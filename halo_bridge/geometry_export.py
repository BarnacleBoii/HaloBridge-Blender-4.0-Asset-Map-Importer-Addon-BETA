"""Export current evaluated meshes as static test geometry, never a donor BSP."""
import hashlib
from pathlib import Path
import bpy
from mathutils import Vector, Matrix
from . import blender_ops, cross_game
from .catalog import read_json
from .diagnostics import ValidationError


def objects(scene):
    return [o for o in scene.objects if o.type=='MESH' and not o.get('hb_preview')
            and (o.get('hb_map_reference') or not o.get('hb_ignore'))]


def is_sky(obj):
    return obj.get('hb_map_reference') and any(c.name.split('.')[0]=='Skies' for c in obj.users_collection)


def warnings(scene):
    result=[]
    if any(o.get('hb_map_reference') or o.get('hb_id') for o in objects(scene)):
        result.append('Assets are exported as static, two-sided surfaces with generated collision. Animated doors, breakable objects and gameplay behavior are not recreated.')
    if any(m and m.name.startswith('+sky') for o in objects(scene) for m in o.data.materials):
        result.append('Sky-only faces are replaced by an enclosing sky boundary; solid ground and other mesh surfaces are retained.')
    if any(is_sky(o) for o in objects(scene)):
        result.append('Imported sky meshes are omitted from solid geometry. The selected Sky from map supplies the game sky.')
    for manifest in sorted({o.get('hb_map_manifest') for o in objects(scene) if o.get('hb_map_manifest')}):
        data=read_json(manifest,{})
        if data.get('decoded_bsps',0)<data.get('expected_bsps',0):
            result.append('The import is incomplete: only geometry currently present in Blender will be exported. Missing terrain will remain missing.')
    if cross_game.reach_materials(objects(scene)):
        result.append("Reach assets become static Halo 3 geometry with generated collision and converted preview textures. Layered shaders, water, glow and animated behavior are approximated; transparency uses cutout alpha.")
    return result


def export(config,path,progress=None):
    progress=progress or (lambda message:None)
    source=bpy.context.scene;depsgraph=bpy.context.evaluated_depsgraph_get()
    selected=[o for o in objects(source) if not is_sky(o)]
    if not selected:raise ValidationError(['There are no meshes to export.'])
    blender_ops.ensure_exporter()
    converted=cross_game.prepare(selected,Path(path).parent/"converted_textures",progress=progress)
    config["converted_shaders"]=list(converted.values())
    aliases={entry["name"]:dict(name=entry["name"],generated=True) for entry in converted.values()};issues=[]
    for index,obj in enumerate(selected,1):
        progress(f'Checking materials {index}/{len(selected)} assets: {obj.name}')
        for mat in obj.data.materials:
            if not mat or mat.name.startswith('+') or mat.as_pointer() in converted:continue
            tag=mat.get('hb_shader','').replace('/', '\\')
            if tag in aliases:continue
            root=Path(config['kit'])/'tags';p=root/tag
            if not tag or '..' in tag.split('\\') or not p.resolve().is_relative_to(root.resolve()):
                issues.append(obj.name+': assign an existing Halo shader.');continue
            matches=[f for f in p.parent.glob(p.name+'.shader*') if f.is_file()]
            # Mesh surfaces use the regular shader when a separate decal tag
            # happens to share its name. Decal tags describe projected decals.
            regular=p.with_suffix('.shader')
            if regular in matches:matches=[regular]
            if len(matches)!=1:issues.append(obj.name+': missing or ambiguous shader '+tag);continue
            aliases[tag]=dict(name='hb_'+hashlib.sha256(tag.encode()).hexdigest()[:20],source=str(matches[0]))
    if issues:raise ValidationError(sorted(set(issues)))
    config['shader_aliases']=aliases
    config['geometry_names']={}
    temp=bpy.data.scenes.new('HaloBridge current geometry');meshes=[];materials=[];cache={};material_cache={}
    old=bpy.context.window.scene;bounds=[];spawn=None;spawn_area=0;structure_candidates=[]
    try:
        for index,obj in enumerate(selected,1):
            progress(f'Preparing asset {index}/{len(selected)}: {obj.name}')
            units=float(obj.get('hb_working_units',source.get('hb_working_units',100)))
            if units<=0:raise ValidationError([obj.name+': invalid working scale.'])
            location,rotation,scale=obj.matrix_world.decompose()
            stretch=(rotation.to_matrix().inverted()@obj.matrix_world.to_3x3())*(1/units)
            key=(obj.data.as_pointer(),obj.as_pointer() if obj.modifiers else 0,tuple(v for row in stretch for v in row))
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
                mesh.transform(stretch.to_4x4())
                if stretch.determinant()<0:mesh.flip_normals()
                sky_slots={i for i,m in enumerate(mesh.materials) if m and m.name.startswith('+sky')}
                if sky_slots:
                    import bmesh
                    bm=bmesh.new();bm.from_mesh(mesh)
                    bmesh.ops.delete(bm,geom=[f for f in bm.faces if f.material_index in sky_slots],context='FACES')
                    bm.to_mesh(mesh);bm.free()
                # Preview/render-only flags must not suppress newly generated collision.
                for i,mat in enumerate(list(mesh.materials)):
                    if mat:
                        mk=mat.as_pointer()
                        if mk not in material_cache:
                            copy=mat.copy();materials.append(copy);material_cache[mk]=copy
                            if mk in converted:copy["hb_shader"]=converted[mk]["name"]
                            copy.ass_jms.render_only=False;copy.ass_jms.collision_only=False
                            if not mat.name.startswith('+'):copy.ass_jms.two_sided=True
                        mesh.materials[i]=material_cache[mk]
                        if mk in converted and mesh.uv_layers.active:
                            u,v=converted[mk]["tiling"]
                            for face in mesh.polygons:
                                if face.material_index==i:
                                    for loop in face.loop_indices:
                                        mesh.uv_layers.active.data[loop].uv.x*=u
                                        mesh.uv_layers.active.data[loop].uv.y*=v
            if not cache[key].polygons:continue
            clone=bpy.data.objects.new('%hb_'+str(len(temp.objects)),cache[key]);temp.collection.objects.link(clone)
            config['geometry_names'][clone.name.lstrip('%').split('.')[0]]=obj.name
            clone.matrix_world=Matrix.LocRotScale(location/units,rotation,Vector((1,1,1)))
            clone['hb_working_units']=1
            solid_faces=[f for f in clone.data.polygons if f.material_index<len(clone.data.materials) and clone.data.materials[f.material_index] and not clone.data.materials[f.material_index].name.startswith('+')]
            if solid_faces:
                authored=not obj.get('hb_id') and not obj.get('hb_map_reference')
                area=sum(f.area for f in solid_faces)
                structure_candidates.append((authored,area,clone))
            for face in clone.data.polygons:
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
            if key not in trees:trees[key]=BVHTree.FromPolygons([v.co for v in obj.data.vertices],[p.vertices for p in obj.data.polygons])
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
        return blender_ops.export_scene(config,path)
    finally:
        bpy.context.window.scene=old
        for obj in list(temp.objects):bpy.data.objects.remove(obj,do_unlink=True)
        bpy.data.scenes.remove(temp)
        for mesh in meshes:bpy.data.meshes.remove(mesh)
        for mat in materials:bpy.data.materials.remove(mat)
