"""Export current evaluated meshes as static test geometry, never a donor BSP."""
import hashlib
from collections import Counter
from pathlib import Path
import bpy
from mathutils import Vector, Matrix
from . import blender_ops, cross_game, export_review, vehicles, collision_policy, invisible_blocks
from .catalog import read_json
from .diagnostics import ValidationError


def objects(scene):
    return [o for o in scene.objects if o.type=='MESH' and not o.get('hb_preview') and not vehicles.selected_vehicle(o) and not invisible_blocks.selected(o)
            and (o.get('hb_map_reference') or not o.get('hb_ignore'))]


def is_sky(obj):
    return obj.get('hb_map_reference') and any(c.name.split('.')[0]=='Skies' for c in obj.users_collection)


def warnings(scene):
    result=[]
    if any(o.get('hb_map_reference') or o.get('hb_id') for o in objects(scene)):
        result.append('Automatic collision first tries the verified original source-game collision geometry. Unmatched or edited static meshes use the available box or surface fallback. Render-only foliage has no generated collision. Original vehicle placements use their game tags instead.')
    if any(m and m.name.startswith('+sky') for o in objects(scene) for m in o.data.materials):
        result.append('Sky-only faces are replaced by an enclosing sky boundary; solid ground and other mesh surfaces are retained.')
    if any(simple_collision(o) for o in objects(scene)):
        result.append("Simple box fallback encloses eligible character and shield surfaces when original collision is unavailable. Set Static collision to Mesh surfaces for detailed contact or openings.")
    if any(is_sky(o) for o in objects(scene)):
        result.append('Imported sky meshes are omitted from solid geometry. The selected Sky from map supplies the game sky.')
    for manifest in sorted({o.get('hb_map_manifest') for o in objects(scene) if o.get('hb_map_manifest')}):
        data=read_json(manifest,{})
        if data.get('decoded_bsps',0)<data.get('expected_bsps',0):
            result.append('The import is incomplete: only geometry currently present in Blender will be exported. Missing terrain will remain missing.')
    if any(m and m.get('hb_custom_shader') for o in objects(scene) for m in o.data.materials):
        result.append('Editable materials are baked into level-local textures and shaders. Save your painted images in the blend. Dynamic Halo color changes, reflections and layered shader behavior are not preserved in this baked result.')
    if any(not m.get('hb_custom_shader') for m in cross_game.reach_materials(objects(scene)).values()):
        result.append("Reach assets use converted textures on static Halo 3 geometry. Layered shaders, water, glow and animated behavior are approximated; transparency uses cutout alpha.")
    return result


def simple_collision(obj):
    mode = getattr(obj, 'hb_static_collision', 'AUTO')
    if mode != 'AUTO':
        return mode == 'BOX'
    tag = obj.get('hb_source_tag', '').lower().replace(chr(92), '/')
    return tag.startswith('objects/characters/') or tag.endswith('/cov_portable_shield/cov_portable_shield')


def add_collision_geometry(mesh, slot, corners, faces):
    # Append only to the temporary export mesh, keeping all render loops and UVs.
    start, loop_start, face_start = len(mesh.vertices), len(mesh.loops), len(mesh.polygons)
    mesh.vertices.add(len(corners))
    for index, co in enumerate(corners):
        mesh.vertices[start + index].co = co
    mesh.loops.add(sum(map(len,faces)))
    mesh.polygons.add(len(faces))
    first=loop_start
    for index, vertices in enumerate(faces):
        polygon = mesh.polygons[face_start + index]
        polygon.loop_start = first
        polygon.material_index = slot
        for offset, vertex in enumerate(vertices):
            mesh.loops[first + offset].vertex_index = start + vertex
        first+=len(vertices)
    mesh.update(calc_edges=True)


def chunk_instances(scene, meshes, names, progress):
    """Partition temporary instance faces in local space, keeping shared placements aligned."""
    import bmesh
    shared={}
    for obj in list(scene.objects):
        if not obj.name.startswith('%'):continue
        data=obj.data
        if data not in shared:
            batches=[];start=0;cost=0
            for face in data.polygons:
                flags=data.materials[face.material_index].ass_jms
                triangles=(len(face.vertices)-2)*(2 if flags.two_sided or flags.transparent_2_sided else 1)
                if cost+triangles>16000 and start<face.index:
                    batches.append((start,face.index));start=face.index;cost=0
                cost+=triangles
            if not batches:shared[data]=[];continue
            batches.append((start,len(data.polygons)))
            parts=[]
            for lo,hi in batches:
                bm=bmesh.new()
                try:
                    bm.from_mesh(data)
                    bmesh.ops.delete(bm,geom=[f for f in bm.faces if not lo<=f.index<hi],context='FACES')
                    part=data.copy();meshes.append(part);bm.to_mesh(part);part.update();parts.append(part)
                finally:bm.free()
            shared[data]=parts
        parts=shared[data]
        if not parts:continue
        label=names[obj.name.lstrip('%').split('.')[0]]
        obj.data=parts[0]
        for part in parts[1:]:
            clone=bpy.data.objects.new('%hb_'+str(len(scene.objects)),part);scene.collection.objects.link(clone)
            clone.matrix_world=obj.matrix_world.copy();clone['hb_working_units']=1
            names[clone.name.lstrip('%').split('.')[0]]=label
        progress(f'{label}: exporting {len(parts)} aligned instances to fit Halo render index limits.')


def export(config,path,progress=None):
    progress=progress or (lambda message:None)
    source=bpy.context.scene;depsgraph=bpy.context.evaluated_depsgraph_get()
    blockers=invisible_blocks.plan(source,config)
    config['vehicle_placements']=vehicles.plan(source,config)
    for placement in config['vehicle_placements']:progress('Original vehicle placement: '+placement['tag']+' (excluded from static geometry)')
    selected=[o for o in objects(source) if not is_sky(o)]
    if not selected:raise ValidationError(['There are no meshes to export.'])
    blender_ops.ensure_exporter()
    issues,used,reach=export_review.inspect(selected,config)
    if issues and not config.get('skip_invalid'):
        raise ValidationError(export_review.messages(issues)+['To omit these entire objects, enable Skip objects with export problems and prepare again.'])
    selected=[obj for obj in selected if obj.name not in issues]
    config['skipped_objects']=issues
    if not selected:raise ValidationError(['No exportable objects remain. Fix at least one object before preparing.'])
    paints = {}
    managed_ids = {p['id'] for p in config['vehicle_placements']}
    for obj in source.objects:
        if not vehicles.selected_vehicle(obj) or obj.get('hb_vehicle_id') not in managed_ids or obj.get('hb_preview') or obj.get('hb_ignore') and not obj.get('hb_map_reference'):
            continue
        slots = {}
        for material_slot in obj.material_slots:
            mat = material_slot.material
            if not mat or not mat.get('hb_custom_shader'):
                continue
            original = mat.get('hb_source_shader')
            if not original or mat.get('hb_custom_shader') != 'colors':
                raise ValidationError([obj.name + ': select an original vehicle material and create editable colors from it.'])
            if original in slots and slots[original] != mat.as_pointer():
                raise ValidationError([obj.name + ': two paint materials replace the same original shader: ' + original])
            from . import editable_materials
            editable_materials.validate(mat)
            if not editable_materials.repeats_on_uv_tiles(mat):
                raise ValidationError([obj.name + ': original vehicle paint requires repeating images and whole-number UV tiling.'])
            slots[original] = mat.as_pointer()
            reach[mat.as_pointer()] = mat
        if slots:
            paints[obj['hb_vehicle_id']] = slots
    converted=cross_game.prepare(selected,Path(path).parent/"converted_textures",progress,materials=reach)
    for placement in config['vehicle_placements']:
        slots = paints.get(placement['id'], {})
        if slots:
            placement['paint'] = {tag: converted[key]['name'] for tag, key in slots.items()}
    config["converted_shaders"]=list(converted.values())
    aliases={entry["name"]:dict(name=entry["name"],generated=True) for entry in converted.values()}
    for obj in selected:
        for mat in used[obj.name]:
            if mat.name.startswith('+') or mat.as_pointer() in converted:continue
            tag=mat.get('hb_shader','').replace('/','\\')
            aliases[tag]=dict(name='hb_'+hashlib.sha256(tag.encode()).hexdigest()[:20],source=str(export_review.shader_file(config['kit'],tag)))
    config['shader_aliases']=aliases
    config['geometry_names']={}
    config['collision_routes']={};routes={}
    temp=bpy.data.scenes.new('HaloBridge current geometry');meshes=[];materials=[];cache={};material_cache={}
    old=bpy.context.window.scene;bounds=[];spawn=None;spawn_area=0;structure_candidates=[]
    try:
        for index,obj in enumerate(selected,1):
            progress(f'Preparing asset {index}/{len(selected)}: {obj.name}')
            units=float(obj.get('hb_working_units',source.get('hb_working_units',100)))
            if units<=0:raise ValidationError([obj.name+': invalid working scale.'])
            location,rotation,scale=obj.matrix_world.decompose()
            stretch=(rotation.to_matrix().inverted()@obj.matrix_world.to_3x3())*(1/units)
            original_key=(obj.get('hb_game',''),obj.get('hb_section'),obj.get('hb_source_tag',''),obj.get('hb_cache',''),obj.get('hb_parts_enabled',''),getattr(obj,'hb_static_collision','AUTO'),obj.get('hb_mesh_signature',''))
            proxy=simple_collision(obj)
            precise=bool(obj.get("hb_id") or obj.get("hb_map_reference"))
            key=(original_key,proxy,precise,obj.data.as_pointer(),obj.as_pointer() if obj.modifiers else 0,tuple(v for row in stretch for v in row))
            if key not in cache:
                mesh=bpy.data.meshes.new_from_object(obj.evaluated_get(depsgraph),preserve_all_data_layers=True,depsgraph=depsgraph)
                meshes.append(mesh);cache[key]=mesh
                if any(m and m.as_pointer() in converted for m in mesh.materials):
                    # Blender 4 can share evaluated UV buffers; recreate layers before writes.
                    layers=[(layer.name,[tuple(loop.uv) for loop in layer.data]) for layer in mesh.uv_layers]
                    active=mesh.uv_layers.active_index
                    for layer in list(mesh.uv_layers):mesh.uv_layers.remove(layer)
                    for name,values in layers:
                        layer=mesh.uv_layers.new(name=name)
                        layer.data.foreach_set('uv',[value for pair in values for value in pair])
                    if layers:mesh.uv_layers.active_index=active
                # Unused legacy slots must not reach the ASS material validator.
                slot_ids=sorted({face.material_index for face in mesh.polygons})
                slots=[mesh.materials[i] for i in slot_ids]
                indices=[slot_ids.index(face.material_index) for face in mesh.polygons]
                mesh.materials.clear()
                for mat in slots:mesh.materials.append(mat)
                for face,index in zip(mesh.polygons,indices):face.material_index=index
                mesh.transform(stretch.to_4x4())
                if stretch.determinant()<0:mesh.flip_normals()
                sky_slots={i for i,m in enumerate(mesh.materials) if m and m.name.startswith('+sky')}
                if sky_slots:
                    import bmesh
                    bm=bmesh.new();bm.from_mesh(mesh)
                    bmesh.ops.delete(bm,geom=[f for f in bm.faces if f.material_index in sky_slots],context='FACES')
                    bm.to_mesh(mesh);bm.free()
                # Open imported render meshes are surfaces, not sealed volumes.
                # Halo's one-sided transparent geometry flag permits open collision
                # edges without duplicating render faces or changing shader alpha.
                edge_uses=Counter(edge for face in mesh.polygons for edge in face.edge_keys)
                open_surface=any(count!=2 for count in edge_uses.values())
                # Leaf cards must not become solid collision solely because they render.
                from . import original_collision
                original=original_collision.get(obj, config, progress) if getattr(obj,'hb_static_collision','AUTO')=='AUTO' else None
                proxy=bool(original) or proxy
                proxy_slots = set()
                if proxy:
                    for i, mat in enumerate(mesh.materials):
                        tag = mat.get('hb_shader', '')
                        shader = aliases.get(tag, {}).get('source')
                        if not mat.name.startswith('+') and not collision_policy.render_only(mat, shader, tag):
                            proxy_slots.add(i)
                points = [mesh.vertices[v].co for f in mesh.polygons if f.material_index in proxy_slots for v in f.vertices]
                corners = []
                proxy_faces=[(0,1,3,2),(4,6,7,5),(0,4,5,1),(2,3,7,6),(0,2,6,4),(1,5,7,3)]
                if original and proxy_slots:
                    vertices,proxy_faces,offset=original
                    corners=[stretch @ (Vector(v)-offset) for v in vertices]
                    if stretch.determinant()<0:proxy_faces=[face[::-1] for face in proxy_faces]
                elif points:
                    limits = [(min(p[a] for p in points), max(p[a] for p in points)) for a in range(3)]
                    if all(hi-lo > 0.0001 for lo,hi in limits):
                        corners = [(x,y,z) for x in limits[0] for y in limits[1] for z in limits[2]]
                for i,mat in enumerate(list(mesh.materials)):
                    if mat:
                        mk=mat.as_pointer();material_key=(mk,open_surface,precise,bool(corners) and i in proxy_slots)
                        if material_key not in material_cache:
                            copy=mat.copy();materials.append(copy);material_cache[material_key]=copy
                            if mk in converted:copy["hb_shader"]=converted[mk]["name"]
                            shader=aliases.get(mat.get('hb_shader','').replace('/','\\'),{}).get('source')
                            if precise:copy.ass_jms.precise=True
                            copy.ass_jms.render_only=(bool(corners) and i in proxy_slots) or collision_policy.render_only(mat,shader,mat.get('hb_shader',''))
                            copy.ass_jms.collision_only=False
                            if copy.ass_jms.render_only:progress('Render-only material (no generated collision): '+mat.name)
                            # Preserve explicit Halo sidedness. Imported alpha cards
                            # already display both sides when backface culling is off.
                            # Opaque viewport defaults alone do not request duplication.
                            if not mat.name.startswith('+'):
                                copy.ass_jms.two_sided=bool(mat.ass_jms.two_sided or
                                    (mat.blend_method!='OPAQUE' and not mat.use_backface_culling))
                                if open_surface and not copy.ass_jms.two_sided and not copy.ass_jms.transparent_2_sided and not copy.ass_jms.render_only:
                                    copy.ass_jms.transparent_1_sided=True
                        mesh.materials[i]=material_cache[material_key]
                        if mk in converted and mesh.uv_layers.active:
                            u,v=converted[mk]["tiling"]
                            for face in mesh.polygons:
                                if face.material_index==i:
                                    for loop in face.loop_indices:
                                        mesh.uv_layers.active.data[loop].uv.x*=u
                                        mesh.uv_layers.active.data[loop].uv.y*=v
                if corners:
                    cm = mesh.materials[min(proxy_slots)].copy()
                    materials.append(cm)
                    cm.ass_jms.render_only = False
                    cm.ass_jms.collision_only = True
                    cm.ass_jms.two_sided = False
                    cm.ass_jms.transparent_1_sided = False
                    cm.ass_jms.transparent_2_sided = False
                    mesh.materials.append(cm)
                    add_collision_geometry(mesh, len(mesh.materials)-1, corners, proxy_faces)
                    progress(('Original Halo collision: ' if original else 'Simple box collision: ')+obj.name)
                routes[key]=('Original Halo collision' if original else 'Simple box') if corners else ('Mesh surfaces' if any(m and not m.ass_jms.render_only for m in mesh.materials) else 'Render only')
            config['collision_routes'][obj.name]=routes[key]
            if not cache[key].polygons:continue
            clone=bpy.data.objects.new('%hb_'+str(len(temp.objects)),cache[key]);temp.collection.objects.link(clone)
            config['geometry_names'][clone.name.lstrip('%').split('.')[0]]=obj.name
            clone.matrix_world=Matrix.LocRotScale(location/units,rotation,Vector((1,1,1)))
            clone['hb_working_units']=1
            solid_faces=[f for f in clone.data.polygons if f.material_index<len(clone.data.materials) and clone.data.materials[f.material_index] and not clone.data.materials[f.material_index].name.startswith('+') and not clone.data.materials[f.material_index].ass_jms.render_only]
            if solid_faces:
                authored=not obj.get('hb_id') and not obj.get('hb_map_reference')
                area=sum(f.area for f in solid_faces)
                structure_candidates.append((authored,area,clone))
            for face in clone.data.polygons:
                if clone.data.materials[face.material_index].ass_jms.render_only:continue
                area=face.area
                if area>spawn_area and (rotation@face.normal).z>.5:
                    spawn_area=area;spawn=(clone.matrix_world@face.center)+Vector((0,0,1))
            for corner in obj.bound_box:bounds.append((obj.matrix_world@Vector(corner))/units)
        progress(f'{len(selected)}/{len(selected)} assets processed. Building the level boundary and player start...')
        # Lightmapping requires a renderable structure mesh, not just % instances.
        # Reuse actual scene geometry; never inject a hidden floor or duplicate it.
        if not structure_candidates:raise ValidationError(['No renderable surfaces remain. Add solid geometry with a Halo material before preparing.'])
        base=max(structure_candidates,key=lambda item:(item[0],item[1]))[2]
        base.name=base.name.lstrip('%')
        config['structure_source']=config['geometry_names'][base.name.split('.')[0]]
        chunk_instances(temp,meshes,config['geometry_names'],progress)
        temp.view_layers[0].update()
        triangles=sum(max(0,len(face.vertices)-2) for face in base.data.polygons)
        progress(f'Main structure: {config["structure_source"]} — {len(base.data.vertices):,} vertices, {triangles:,} triangles. Halo compiles these surfaces into the level BSP.')
        if triangles>20000:
            progress('Complex structure warning: the main structure exceeds 20,000 triangles. This is a performance advisory, not a Halo limit; dense or heavily subdivided terrain can make plane generation very slow. Geometry has not been simplified.')
        # A closed sky hull supplies a valid exterior for extracted render clusters.
        if not bounds:raise ValidationError(['The scene contains only sky faces; add solid geometry.'])
        lo=Vector(tuple(min(v[i] for v in bounds)-10 for i in range(3)))
        hi=Vector(tuple(max(v[i] for v in bounds)+10 for i in range(3)))
        # Largest-area faces can be underground terrain skirts. Prefer the
        # uppermost exposed surface at the cursor instead of spawning below it.
        from mathutils.bvhtree import BVHTree
        cursor=source.cursor.location/float(source.get('hb_working_units',100))
        ray_origin=Vector((cursor.x,cursor.y,hi.z));top=None;trees={}
        for index,obj in enumerate(temp.objects,1):
            progress(f'Checking player start {index}/{len(temp.objects)} assets: '+config['geometry_names'].get(obj.name.lstrip('%').split('.')[0],obj.name))
            corners=[obj.matrix_world@Vector(c) for c in obj.bound_box]
            if not all(min(c[i] for c in corners)-.0001<=cursor[i]<=max(c[i] for c in corners)+.0001 for i in (0,1)):continue
            key=obj.data.as_pointer()
            if key not in trees:
                faces=[p.vertices for p in obj.data.polygons if not obj.data.materials[p.material_index].ass_jms.render_only]
                trees[key]=BVHTree.FromPolygons([v.co for v in obj.data.vertices],faces) if faces else None
            if trees[key] is None:continue
            inv=obj.matrix_world.inverted()
            hit,normal,_,_=trees[key].ray_cast(inv@ray_origin,inv.to_3x3()@Vector((0,0,-1)))
            if hit is not None and (obj.matrix_world.to_3x3()@normal).z>.5:
                point=obj.matrix_world@hit
                if top is None or point.z>top.z:top=point
        if top is not None:spawn=top+Vector((0,0,1))
        config['spawn_position']=list(spawn if spawn is not None else Vector(((lo.x+hi.x)/2,(lo.y+hi.y)/2,hi.z-9)))
        verts=[(x,y,z) for x in (lo.x,hi.x) for y in (lo.y,hi.y) for z in (lo.z,hi.z)]
        mesh=bpy.data.meshes.new('Sky boundary');meshes.append(mesh)
        mesh.from_pydata(verts,[],[(0,2,3,1),(4,5,7,6),(0,1,5,4),(2,6,7,3),(0,4,6,2),(1,3,7,5)])
        sky=bpy.data.materials.new('+sky');materials.append(sky);mesh.materials.append(sky)
        hull=bpy.data.objects.new('Sky boundary',mesh);temp.collection.objects.link(hull);hull['hb_working_units']=1
        # Normalize working units before passing to the established ASS adapter.
        for obj in temp.objects:
            units=obj['hb_working_units'];obj.matrix_world=Matrix.Scale(1/units,4)@obj.matrix_world;obj['hb_working_units']=1
        progress(f'{len(selected)}/{len(selected)} assets processed. Writing geometry file; waiting for the Blender exporter...')
        bpy.context.window.scene=temp
        return blender_ops.export_scene(config,path)+blockers
    finally:
        config.pop('_collision_reads',None)
        bpy.context.window.scene=old
        for obj in list(temp.objects):bpy.data.objects.remove(obj,do_unlink=True)
        bpy.data.scenes.remove(temp)
        for mesh in meshes:bpy.data.meshes.remove(mesh)
        for mat in materials:bpy.data.materials.remove(mat)
