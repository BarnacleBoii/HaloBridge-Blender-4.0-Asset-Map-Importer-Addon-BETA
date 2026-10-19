import importlib.util
import json
import math
import sys
import uuid
from pathlib import Path
import bpy
from mathutils import Matrix, Vector
from .catalog import material_name, read_json, stable_id
from .source_names import leaf,generated_material

def new_id(): return 'hb_'+uuid.uuid4().hex[:24]

def ensure_exporter():
    import addon_utils
    if 'io_scene_halo' not in bpy.context.preferences.addons:
        addon_utils.enable('io_scene_halo',default_set=True)
    if 'io_scene_halo' not in bpy.context.preferences.addons:
        raise RuntimeError('Install and enable Halo Asset Blender Development Toolset for Blender 4.0.')
    import io_scene_halo
    if tuple(io_scene_halo.bl_info['version'])!=(2,364,0):
        raise RuntimeError('This adapter was verified with Halo Asset Blender Development Toolset v364 (2.364.0). Use that version to avoid an incompatible ASS coordinate conversion.')

_material_lookup={}
_material_count=-1

def material(meta, directory):
    global _material_lookup,_material_count
    key='hb_'+stable_id(meta.get('shader'),str(directory),meta['id'])
    if _material_count!=len(bpy.data.materials) or (key in _material_lookup and bpy.data.materials.get(_material_lookup[key]) is None):
        _material_lookup={}
        for item in bpy.data.materials:
            identity=item.get('hb_material_key') or (item.name if generated_material(item.name) else None)
            if identity:_material_lookup.setdefault(identity,item.name)
        _material_count=len(bpy.data.materials)
    m=bpy.data.materials.get(_material_lookup.get(key,key))
    if m:
        m['hb_material_key']=key
        if generated_material(m.name):
            m['hb_conversion_id']=m.get('hb_conversion_id',m.name)
            m.name=leaf(meta.get('name') or meta.get('shader')) or key
        _material_lookup[key]=m.name
        return m
    m=bpy.data.materials.new(leaf(meta.get('name') or meta.get('shader')) or key)
    m['hb_material_key']=key;m['hb_conversion_id']=key
    _material_lookup[key]=m.name;_material_count=len(bpy.data.materials)
    m['hb_shader']=meta.get('shader','');m['hb_label']=meta['name'];m.use_nodes=True
    nodes=m.node_tree.nodes;links=m.node_tree.links;bsdf=nodes.get('Principled BSDF')
    texture_names=read_json(Path(directory)/'texture_names.json',{}).get('textures',{})
    for tm in meta['textures']:
        if tm['usage'] not in ('diffuse','normal','transparency'): continue
        path=Path(directory)/tm['path']
        if not path.is_file():raise RuntimeError('Missing texture: '+str(path))
        image=bpy.data.images.load(str(path),check_existing=True)
        source_name=tm.get('name') or texture_names.get(path.stem.removeprefix('texture_'))
        if source_name:
            image['hb_source_texture']=source_name
            if image.name.startswith('texture_'):image.name=leaf(source_name)
        tex=nodes.new('ShaderNodeTexImage');tex.image=image
        tex.label=leaf(source_name) or (meta['name']+' - '+tm['usage'])
        uv=nodes.new('ShaderNodeTexCoord');mapping=nodes.new('ShaderNodeVectorMath');mapping.operation='MULTIPLY';mapping.inputs[1].default_value=(*tm['tiling'],1)
        links.new(uv.outputs['UV'],mapping.inputs[0]);links.new(mapping.outputs[0],tex.inputs['Vector'])
        if tm['usage']=='diffuse':
            links.new(tex.outputs['Color'],bsdf.inputs['Base Color'])
            if meta['alpha']!='opaque':links.new(tex.outputs['Alpha'],bsdf.inputs['Alpha'])
        elif tm['usage']=='normal':
            image.colorspace_settings.name='Non-Color';normal=nodes.new('ShaderNodeNormalMap');links.new(tex.outputs['Color'],normal.inputs['Color']);links.new(normal.outputs[0],bsdf.inputs['Normal'])
        else:
            channel=tm.get('channels',8)
            if channel==8:links.new(tex.outputs['Alpha'],bsdf.inputs['Alpha'])
            elif channel in (1,2,4):
                separate=nodes.new('ShaderNodeSeparateColor');separate.mode='RGB';links.new(tex.outputs['Color'],separate.inputs[0]);links.new(separate.outputs[{1:0,2:1,4:2}[channel]],bsdf.inputs['Alpha'])
            else:links.new(tex.outputs['Color'],bsdf.inputs['Alpha'])
    if meta['alpha']!='opaque':
        m.blend_method='CLIP' if meta['alpha']=='clip' else 'BLEND';m.use_backface_culling=False
    return m

def mesh_from_preview(preview, asset_id):
    directory=Path(preview).parent;data=read_json(preview)
    mats={m['id']:material(m,directory) for m in data['materials']}
    vertices=[];faces=[];uvs=[];normals=[];face_mats=[];order=list(mats)
    for part in data['meshes']:
        offset=len(vertices);vertices+=part['positions'];uvs+=part['uv'] or [[0,0]]*len(part['positions']);normals+=part['normals'] or [[0,0,1]]*len(part['positions'])
        for seg in part['segments']:
            for i in range(0,len(seg['indices']),3):
                faces.append([offset+v for v in seg['indices'][i:i+3]]);face_mats.append(order.index(seg['material']) if seg['material'] in order else 0)
    mesh=bpy.data.meshes.new('hb_mesh_'+asset_id);mesh.from_pydata(vertices,[],faces);mesh.update()
    for mid in order:mesh.materials.append(mats[mid])
    for poly,mi in zip(mesh.polygons,face_mats):poly.material_index=mi;poly.use_smooth=True
    uv=mesh.uv_layers.new(name='UVMap')
    for loop in mesh.loops:uv.data[loop.index].uv=uvs[loop.vertex_index]
    mesh.use_auto_smooth=True;mesh.normals_split_custom_set_from_vertices(normals)
    mesh['hb_asset_id']=asset_id;return mesh

def place(asset, path, config, location=None):
    ensure_exporter()
    mapped=asset.get('mapping',asset);key=asset['id']
    mesh=next((m for m in bpy.data.meshes if m.get('hb_asset_id')==key),None)
    if not mesh:
        if Path(path).suffix.lower()=='.json':mesh=mesh_from_preview(path,key)
        else:mesh=import_legacy(path,key)
    obj=bpy.data.objects.new(asset['name'],mesh);bpy.context.collection.objects.link(obj)
    obj.location=location if location is not None else bpy.context.scene.cursor.location
    obj.scale=(100,100,100);obj['hb_working_units']=100
    bpy.context.scene['hb_working_units']=100
    bpy.context.scene.unit_settings.system='METRIC';bpy.context.scene.unit_settings.scale_length=.03048
    obj['hb_game']=mapped.get('game','halo3');obj['hb_id']=new_id();obj['hb_asset_id']=key;obj['hb_kind']=mapped['kind'];obj['hb_scenery_tag']=mapped.get('scenery_tag','');obj['hb_cache']=str(Path(path).parent)
    obj['hb_collision']='tag' if mapped['kind']=='scenery' else ('original' if (Path(path).parent/'collision.json').exists() else 'missing')
    obj['hb_source_tag']=mapped.get('tag','');obj['hb_section']=mapped.get('section',-1)
    obj['hb_mesh_signature']=mesh_signature(mesh)
    bpy.ops.object.select_all(action='DESELECT');obj.select_set(True);bpy.context.view_layer.objects.active=obj
    return obj

def import_legacy(path,key):
    before=set(bpy.data.objects)
    if Path(path).suffix.lower()=='.amf':
        script=Path(__file__).parent/'vendor/amf.py'
        spec=importlib.util.spec_from_file_location('hb_amf',script);mod=importlib.util.module_from_spec(spec);sys.modules['hb_amf']=mod;spec.loader.exec_module(mod)
        options=mod.ImportOptions();options.MODE_SCALE='HALO';options.IMPORT_BONES=False;options.IMPORT_MARKERS=False
        mod.main(bpy.context,str(path),options)
    else:
        # Reclaimer's legacy JMS exports can refer to node zero with an empty
        # node table. The static environment route needs no skeleton.
        from io_scene_halo.file_jms.format import JMSAsset
        from io_scene_halo.file_jms.process_file_retail import process_file_retail
        data=process_file_retail(JMSAsset(str(path)),'halo3','JMS',tuple(range(8197,8214)),'default','default')
        mesh=bpy.data.meshes.new(Path(path).stem)
        mesh.from_pydata([v.translation*.01 for v in data.vertices],[],[(t.v0,t.v1,t.v2) for t in data.triangles]);mesh.update()
        used=sorted(set(t.material_index for t in data.triangles))
        for index in used:
            if index<0 or index>=len(data.materials):raise RuntimeError('JMS contains an invalid material index.')
            mat=bpy.data.materials.new(data.materials[index].name);mesh.materials.append(mat)
        for face,triangle in zip(mesh.polygons,data.triangles):face.material_index=used.index(triangle.material_index)
        uv=mesh.uv_layers.new(name='UVMap')
        for loop in mesh.loops:
            vertex=data.vertices[loop.vertex_index]
            if vertex.uv_set:uv.data[loop.index].uv=vertex.uv_set[0][:2]
        obj=bpy.data.objects.new(Path(path).stem,mesh);bpy.context.collection.objects.link(obj)
    imported=[o for o in bpy.data.objects if o not in before];meshes=[o for o in imported if o.type=='MESH']
    if not meshes:raise RuntimeError('No mesh imported from '+str(path))
    bpy.ops.object.select_all(action='DESELECT')
    names=[o.name for o in imported]
    for o in meshes:o.select_set(True)
    bpy.context.view_layer.objects.active=meshes[0];bpy.ops.object.join()
    obj=bpy.context.object
    # AMF instance transforms are map coordinates; retain shape/orientation but
    # place a reusable object at its own origin.
    obj.location=(0,0,0);bpy.ops.object.transform_apply(location=False,rotation=True,scale=True)
    mesh=obj.data;mesh.use_fake_user=True;mesh['hb_asset_id']=key
    for name in names:
        obj=bpy.data.objects.get(name)
        if obj:bpy.data.objects.remove(obj,do_unlink=True)
    return mesh

def mesh_signature(mesh):
    import hashlib,struct
    h=hashlib.sha256()
    for v in mesh.vertices:h.update(struct.pack('<fff',*v.co))
    for p in mesh.polygons:h.update(struct.pack('<'+'I'*len(p.vertices),*p.vertices))
    return h.hexdigest()

def collision_issue(obj):
    if not obj.get('hb_id') or obj.get('hb_ignore') or obj.get('hb_kind')=='scenery':return ''
    kind=obj.get('hb_kind')
    if kind=='model':
        return 'Raw render model: its game-object tag and collision are not linked. Choose a matching scenery or BSP instance in the Asset List and use Swap selected object, or remove this object from the export scene. A shader assignment cannot recover collision.'
    if kind=='legacy':
        return 'Legacy extracted model has no source collision. Choose its original scenery or BSP instance in the Asset List and use Swap selected object.'
    if obj.get('hb_collision')!='original' or not (Path(obj.get('hb_cache',''))/'collision.json').is_file():
        return 'Original BSP collision is missing. Re-extract and replace this instance using the matching Editing Kit tags; check the diagnostic report if extraction fails.'
    return ''

def link_verified_scenery(objects,result):
    routes={}
    for match in result.get('matches',[]):
        routes.setdefault(match['render'].lower(),{})[match['scenery']]=match
    plan=[];issues=[]
    for obj in objects:
        candidates=routes.get(obj.get('hb_source_tag','').lower(),{})
        if len(candidates)!=1:
            issues.append(obj.name+(': multiple scenery tags use this model; select the intended scenery entry and swap it.' if candidates else ': no existing scenery tag with a verified model/collision link was found. A collision file alone does not identify the game-object placement type.'))
        else:plan.append((obj,next(iter(candidates.values()))))
    if issues:raise RuntimeError('\n'.join(issues))
    for obj,match in plan:
        obj['hb_kind']='scenery';obj['hb_scenery_tag']=match['scenery'];obj['hb_collision']='tag'
        obj['hb_verified_collision_tag']=match['collision']
    return len(plan)

def validate_map_export(scene):
    references=[o for o in scene.objects if o.get('hb_map_reference')]
    if references:
        raise RuntimeError('Cannot prepare the complete scene: '+str(len(references))+' whole-map reference objects are not export-ready. Their original terrain collision, object types and source identities must be linked before export. Preparation stopped before writing files, instead of silently exporting only the starter shell. This version does not yet support whole-map round-trip export.')

def export_scene(config,path):
    def shader_name(tag):
        alias=config.get("shader_aliases",{}).get(tag)
        return alias["name"] if alias else material_name(config["kit"],tag)
    validate_map_export(bpy.context.scene)
    ensure_exporter();bpy.context.view_layer.update();source=bpy.context.scene;objects=[o for o in source.objects if o.type=='MESH' and not o.get('hb_ignore')]
    if not objects:
        if any(o.get('hb_map_reference') for o in source.objects):
            raise RuntimeError('The original-layout collection is a visual map reference, not export-ready level geometry. Original collision and gameplay are not reconstructed. Create authored level geometry before Prepare for Sapien.')
        raise RuntimeError('The scene has no level geometry.')
    issues=[];placements=[];seen=set()
    units={float(o.get('hb_working_units',1 if o.get('hb_id') else source.get('hb_working_units',1))) for o in objects}
    if len(units)>1:raise RuntimeError('This scene mixes older 1x imports with new 100x imports. Keep them in separate scenes or replace the older imports before preparing for Sapien; automatic conversion would change your existing layout.')
    for obj in objects:
        if obj.get('hb_id'):
            if obj['hb_id'] in seen:obj['hb_id']=new_id()
            seen.add(obj['hb_id'])
            loc,rot,scale=obj.matrix_world.decompose()
            if min(scale)<=0 or max(scale)-min(scale)>1e-5:issues.append(obj.name+': use positive uniform scale.')
            reconstructed=Matrix.LocRotScale(loc,rot,scale)
            if max(abs(obj.matrix_world[r][c]-reconstructed[r][c]) for r in range(4) for c in range(4))>1e-5:
                issues.append(obj.name+': parent transforms introduce shear; clear the shear before export.')
            if obj.modifiers or mesh_signature(obj.data)!=obj.get('hb_mesh_signature'):issues.append(obj.name+': mesh edits are outside version-one support.')
            if obj.get('hb_kind')=='scenery':
                euler=rot.to_euler('ZYX')
                units=float(obj.get('hb_working_units',1))
                placements.append(dict(id=obj['hb_id'],tag=obj['hb_scenery_tag'],position=list(loc/units),rotation=[math.degrees(euler.z),-math.degrees(euler.y),math.degrees(euler.x)],scale=float(scale.x)/units))
                continue
            issue=collision_issue(obj)
            if issue:issues.append(obj.name+': '+issue)
        if not obj.data.materials:issues.append(obj.name+': assign a Halo shader before exporting.')
        for mat in obj.data.materials:
            if not mat:issues.append(obj.name+': empty material slot.');continue
            if mat.name.startswith('+'):continue
            try:shader_name(mat.get('hb_shader',''))
            except (ValueError,OSError) as e:issues.append(obj.name+': '+str(e))
    if issues:
        from .diagnostics import ValidationError
        raise ValidationError(issues)
    temp=bpy.data.scenes.new('HaloBridge export');old=bpy.context.window.scene;mesh_cache={};mat_cache={}
    try:
        bpy.context.window.scene=temp
        for obj in objects:
            if obj.get('hb_kind')=='scenery':continue
            key=obj.data.as_pointer()
            if key not in mesh_cache:
                mesh=obj.data.copy();mesh_cache[key]=mesh
                for i,m in enumerate(list(mesh.materials)):
                    mk=(m.as_pointer(),bool(obj.get('hb_id')))
                    if mk not in mat_cache:
                        c=m.copy();c.ass_jms.name_override=('+sky' if m.name.startswith('+sky') else m.name) if m.name.startswith('+') else shader_name(m['hb_shader']);c.ass_jms.is_bm=True
                        if obj.get('hb_id'):c.ass_jms.render_only=True
                        mat_cache[mk]=c
                    mesh.materials[i]=mat_cache[mk]
                if obj.get('hb_collision')=='original':
                    collision=read_json(Path(obj['hb_cache'])/'collision.json')['meshes'][0]
                    import bmesh
                    bm=bmesh.new();bm.from_mesh(mesh)
                    cm=bpy.data.materials.new('hb_collision');cm.ass_jms.is_bm=True;cm.ass_jms.collision_only=True
                    cm.ass_jms.name_override=material_name(config['kit'],obj.data.materials[0]['hb_shader']);mesh.materials.append(cm)
                    mat_cache[(key,'collision')]=cm
                    verts=[bm.verts.new(v) for v in collision['positions']]
                    for f in collision['faces']:
                        face=bm.faces.new([verts[i] for i in f]);face.material_index=len(mesh.materials)-1
                    bm.to_mesh(mesh);bm.free();mesh.update()
            units=float(obj.get('hb_working_units',1 if obj.get('hb_id') else source.get('hb_working_units',1)))
            new=bpy.data.objects.new(('%' if obj.get('hb_id') else '')+obj.name,mesh_cache[key]);temp.collection.objects.link(new);new.matrix_world=Matrix.Scale(1/units,4)@obj.matrix_world
            # Tool converts ASS units to world units by /100. The v364 ASS
            # exporter scales vertices but leaves instance translations alone.
            new.matrix_world.translation=obj.matrix_world.translation*(100/units)
        temp.unit_settings.scale_length=3.048
        bpy.ops.export_scene.ass(filepath=str(path),game_title='halo3',scale_enum='1',hidden_geo=False,nonrender_geo=False,apply_modifiers=True,triangulate_faces=True,edge_split=False,clean_normalize_weights=False)
        if not Path(path).is_file():raise RuntimeError('Exporter did not produce a level file.')
    finally:
        bpy.context.window.scene=old
        for o in list(temp.objects):bpy.data.objects.remove(o,do_unlink=True)
        bpy.data.scenes.remove(temp)
        for mesh in mesh_cache.values():bpy.data.meshes.remove(mesh)
        for mat in mat_cache.values():bpy.data.materials.remove(mat)
    return placements

def starter_ground(config,preview=None):
    ensure_exporter()
    if preview is None:raise RuntimeError('Load the starter ground material before creating its shell.')
    meta=read_json(preview)
    ground=material(meta['materials'][0],Path(preview).parent)
    bpy.ops.mesh.primitive_cube_add(size=2,location=(0,0,12))
    obj=bpy.context.object;obj.name='HaloBridge level shell';obj.scale=(30,30,12)
    bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    bpy.ops.object.mode_set(mode='EDIT');bpy.ops.mesh.select_all(action='SELECT');bpy.ops.mesh.flip_normals();bpy.ops.object.mode_set(mode='OBJECT')
    sky=bpy.data.materials.new('+sky');sky.use_nodes=True;sky.node_tree.nodes.get('Principled BSDF').inputs['Alpha'].default_value=0
    sky.blend_method='CLIP';sky.use_backface_culling=True
    obj.data.materials.append(ground);obj.data.materials.append(sky)
    for poly in obj.data.polygons:
        if poly.center.z>0 or abs(poly.normal.z)<.5:poly.material_index=1
        else:
            for index in poly.loop_indices:
                vertex=obj.data.vertices[obj.data.loops[index].vertex_index]
                obj.data.uv_layers.active.data[index].uv=(vertex.co.x/4,vertex.co.y/4)
    obj.matrix_world=Matrix.Scale(100,4)@obj.matrix_world;obj['hb_working_units']=100
    bpy.context.scene['hb_working_units']=100
    bpy.context.scene.unit_settings.system='METRIC';bpy.context.scene.unit_settings.scale_length=.03048
    for screen in bpy.data.screens:
        for area in screen.areas:
            if area.type=='VIEW_3D':area.spaces.active.shading.type='MATERIAL'
    return obj

