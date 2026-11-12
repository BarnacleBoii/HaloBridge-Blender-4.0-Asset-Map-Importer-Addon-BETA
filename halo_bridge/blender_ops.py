import importlib.util
import json
import math
import sys
import uuid
from pathlib import Path
import bpy
from mathutils import Matrix, Vector
from .catalog import material_name, read_json, stable_id
from . import compat
from .source_names import leaf,generated_material

def new_id(): return 'hb_'+uuid.uuid4().hex[:24]

# Exporter options and material flags this adapter relies on. Builds that
# still provide them export compatible ASS files (vertices scaled, instance
# translations unscaled), which the export transforms below compensate for.
EXPORT_OPTIONS=('game_title','scale_enum','hidden_geo','nonrender_geo','apply_modifiers','triangulate_faces','edge_split','clean_normalize_weights')
MATERIAL_FLAGS=('name_override','is_bm','render_only','collision_only','two_sided','transparent_1_sided','transparent_2_sided','precise')
LEGACY_TOOLSETS=((2,364,0),(2,432,0))

def ensure_exporter():
    import addon_utils
    if not compat.toolset_addon_name():
        addon_utils.enable('io_scene_halo',default_set=True)
    if not compat.toolset_addon_name():
        raise RuntimeError('Install and enable the Halo Asset Blender Development Toolset (General-101). Use v432 or newer (Blender 4.0 can also use v364).')
    module=compat.toolset_module()
    version=tuple(module.bl_info.get('version',())) if module else ()
    if bpy.app.version<(4,1,0):
        if version not in LEGACY_TOOLSETS:
            raise RuntimeError('On Blender 4.0, use Halo Asset Blender Development Toolset v364 (2.364.0) or v432 (2.432.0).')
        return
    # Newer Blender: check the interface this adapter uses instead of a version number.
    try:
        options=set(bpy.ops.export_scene.ass.get_rna_type().properties.keys())
    except (AttributeError,KeyError,RuntimeError):
        options=set()
    missing=[name for name in EXPORT_OPTIONS if name not in options]
    group=getattr(bpy.types.Material,'bl_rna',None)
    material_props=bpy.types.Material.bl_rna.properties.get('ass_jms') if group else None
    if material_props is not None:
        flags=set(material_props.fixed_type.properties.keys())
        missing+=[name for name in MATERIAL_FLAGS if name not in flags]
    else:missing.append('material ass_jms properties')
    if missing:
        raise RuntimeError('The installed Halo toolset does not provide the ASS export options HaloBridge uses ('+', '.join(missing)+'). Install the current General-101 toolset release.')

def legacy_toolset_check():
    """Older toolsets (v364) run operators through a frame-locals hack that Python 3.13
    (Blender 5.x) no longer supports: the ASS export fails with a KeyError. v432 fixed it."""
    if compat.toolset_frame_hack() and sys.version_info>=(3,13):
        module=compat.toolset_module()
        version='.'.join(map(str,module.bl_info.get('version',()))) if module else ''
        raise RuntimeError('Halo Asset Blender Development Toolset '+version+' cannot export on Blender '
                           +'.'.join(map(str,bpy.app.version[:2]))+' (Python 3.13). Install the current General-101 toolset release (v432 or newer) and prepare again.')

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
    m['hb_texture_sources']=json.dumps(meta.get('textures',[]));m['hb_texture_directory']=str(directory)
    m['hb_shader']=meta.get('shader','');m['hb_label']=meta['name'];compat.enable_nodes(m)
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
    for tm in meta['textures']:
        if tm['usage']=='color_change':
            mask=bpy.data.images.load(str(Path(directory)/tm['path']),check_existing=True)
            mask.colorspace_settings.name='Non-Color';m['hb_change_mask_image']=mask.name
    from . import layered_preview
    layered_preview.apply(m,meta,directory)
    from . import regular_preview
    regular_preview.apply(m,meta,directory)
    if meta['alpha']!='opaque':
        compat.set_alpha(m,'clip' if meta['alpha']=='clip' else 'blend');m.use_backface_culling=False
    return m

def add_material(obj, mat):
    """Add mat as a new slot (or reuse its slot) and assign it, keeping every existing material.

    In Edit Mode only the selected faces are assigned; otherwise the whole object is.
    """
    if obj.data.users>1:obj.data=obj.data.copy()
    mesh=obj.data
    index=next((i for i,m in enumerate(mesh.materials) if m==mat),None)
    if index is None:
        mesh.materials.append(mat);index=len(mesh.materials)-1
    if obj.mode=='EDIT':
        import bmesh
        bm=bmesh.from_edit_mesh(mesh)
        faces=[f for f in bm.faces if f.select] or list(bm.faces)
        for face in faces:face.material_index=index
        bmesh.update_edit_mesh(mesh)
    else:
        for poly in mesh.polygons:poly.material_index=index
    obj.active_material_index=index
    return index

def mesh_from_preview(preview, asset_id, data=None):
    directory=Path(preview).parent;data=read_json(preview) if data is None else data
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
    compat.custom_normals(mesh,normals)
    from . import regular_preview
    regular_preview.paired_transparency(mesh)
    mesh['hb_asset_id']=asset_id;return mesh

def place(asset, path, config, location=None):
    ensure_exporter()
    mapped=asset.get('mapping',asset);key=asset['id']
    policy=read_json(path).get('selection_policy',0) if Path(path).suffix.lower()=='.json' else 0
    mesh=next((m for m in bpy.data.meshes if m.get('hb_asset_id')==key and m.get('hb_selection_policy',0)==policy),None)
    if not mesh:
        if Path(path).suffix.lower()=='.json':mesh=mesh_from_preview(path,key)
        else:mesh=import_legacy(path,key)
        mesh['hb_selection_policy']=policy
    obj=bpy.data.objects.new(asset['name'],mesh);bpy.context.collection.objects.link(obj)
    obj.location=location if location is not None else bpy.context.scene.cursor.location
    obj.scale=(100,100,100);obj['hb_working_units']=100
    bpy.context.scene['hb_working_units']=100
    bpy.context.scene.unit_settings.system='METRIC';bpy.context.scene.unit_settings.scale_length=.03048
    obj['hb_game']=mapped.get('game','halo3');obj['hb_id']=new_id();obj['hb_asset_id']=key;obj['hb_kind']=mapped['kind'];obj['hb_scenery_tag']=mapped.get('scenery_tag','');obj['hb_cache']=str(Path(path).parent)
    obj['hb_collision']='tag' if mapped['kind']=='scenery' else ('original' if (Path(path).parent/'collision.json').exists() else 'missing')
    obj['hb_source_tag']=mapped.get('tag','');obj['hb_section']=mapped.get('section',-1)
    obj['hb_mesh_signature']=mesh_signature(mesh)
    if policy:
        details=read_json(path)
        obj['hb_model_selection']=json.dumps(details.get('selection',[]))
        obj['hb_import_warnings']=json.dumps(details.get('warnings',[]))
        if (Path(path).parent/'parts.json').is_file():
            obj['hb_parts_path']=str(Path(path).parent/'parts.json')
            obj['hb_parts_enabled']=json.dumps(sorted({p['choice'] for p in details['meshes']}))
            obj['hb_parts_signature']=mesh_signature(mesh)
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
        toolset=compat.toolset_module()
        if toolset is None:raise RuntimeError('Enable the Halo Asset Blender Development Toolset to import legacy JMS files.')
        import importlib
        JMSAsset=importlib.import_module(toolset.__name__+'.file_jms.format').JMSAsset
        process_file_retail=importlib.import_module(toolset.__name__+'.file_jms.process_file_retail').process_file_retail
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
    """SHA-256 of vertex positions and face vertex order (unchanged digest, bulk-read)."""
    import hashlib
    h=hashlib.sha256()
    try:
        import numpy as np
        co=np.empty(len(mesh.vertices)*3,dtype='<f4');mesh.vertices.foreach_get('co',co);h.update(co.tobytes())
        # Face corners are stored contiguously in face order, as p.vertices lists them.
        starts=np.empty(len(mesh.polygons),dtype=np.int64);mesh.polygons.foreach_get('loop_start',starts)
        loops=np.empty(len(mesh.loops),dtype='<u4');mesh.loops.foreach_get('vertex_index',loops)
        if len(starts) and (np.any(np.diff(starts)<0) or starts[0]!=0):raise ValueError('non-contiguous faces')
        h.update(loops.tobytes());return h.hexdigest()
    except (ImportError,ValueError,TypeError):
        import struct
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
            # Relative tolerances: at 100x working scale float32 rounding alone is ~1e-5.
            if min(scale)<=0 or max(scale)-min(scale)>1e-4*max(scale):issues.append(obj.name+': use positive uniform scale.')
            reconstructed=Matrix.LocRotScale(loc,rot,scale)
            if max(abs(obj.matrix_world[r][c]-reconstructed[r][c]) for r in range(4) for c in range(4))>1e-5*max(1.0,max(scale)):
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
            # Tool converts ASS units to world units by /100. The v364/v432 ASS
            # exporter scales vertices but leaves instance translations alone.
            new.matrix_world.translation=obj.matrix_world.translation*(100/units)
        temp.unit_settings.scale_length=3.048
        legacy_toolset_check()
        from .geometry_export import repair_texcoords
        repair_texcoords(temp.objects)  # Tool rejects the whole ASS for one NaN texture coordinate.
        bpy.ops.export_scene.ass(filepath=str(path),game_title='halo3',scale_enum='1',hidden_geo=False,nonrender_geo=False,apply_modifiers=True,triangulate_faces=True,edge_split=False,clean_normalize_weights=False)
        if not Path(path).is_file():raise RuntimeError('Exporter did not produce a level file.')
    finally:
        bpy.context.window.scene=old
        for o in list(temp.objects):bpy.data.objects.remove(o,do_unlink=True)
        bpy.data.scenes.remove(temp)
        for mesh in mesh_cache.values():bpy.data.meshes.remove(mesh)
        for mat in mat_cache.values():bpy.data.materials.remove(mat)
    return placements

# Starter template sizes in 100x working units: an 81 m terrain inside a 131 m x 52 m sky wall.
TERRAIN_SCALE=4071.525
SKY_SCALE=218.146
SKY_CENTER_Z=2616.78


def sky_material():
    """A visible, see-through +sky wall. Preparation removes +sky faces, so it never exports."""
    sky=bpy.data.materials.get('+sky') or bpy.data.materials.new('+sky')
    compat.enable_nodes(sky)
    bsdf=next((n for n in sky.node_tree.nodes if n.type=='BSDF_PRINCIPLED'),None)
    if bsdf:
        bsdf.inputs['Base Color'].default_value=(.45,.65,.95,1);bsdf.inputs['Alpha'].default_value=.18
    compat.set_alpha(sky,'blend');sky.use_backface_culling=True;sky.diffuse_color=(.45,.65,.95,.18)
    return sky


def starter_template(context,config,ground_preview,chief_asset=None,chief_preview=None):
    """Paintable terrain plane, a +sky boundary wall and Master Chief for scale (not exported)."""
    ensure_exporter()
    if ground_preview is None:raise RuntimeError('Load the starter ground material before creating the template.')
    from . import editable_materials
    scene=bpy.context.scene;collection=bpy.context.collection
    scene['hb_working_units']=100
    scene.unit_settings.system='METRIC';scene.unit_settings.scale_length=.03048
    if bpy.context.object and bpy.context.object.mode!='OBJECT':bpy.ops.object.mode_set(mode='OBJECT')
    # Terrain: a single quad with 0-1 UVs, so the editable terrain paints one texture tile.
    mesh=bpy.data.meshes.new('Terrain')
    mesh.from_pydata([(-1,-1,0),(1,-1,0),(1,1,0),(-1,1,0)],[],[(0,1,2,3)])
    uv=mesh.uv_layers.new(name='UVMap')
    for loop in mesh.loops:
        co=mesh.vertices[loop.vertex_index].co;uv.data[loop.index].uv=((co.x+1)/2,(co.y+1)/2)
    terrain=bpy.data.objects.new('Terrain',mesh);collection.objects.link(terrain)
    terrain.scale=(TERRAIN_SCALE,)*3;terrain['hb_working_units']=100
    meta=read_json(ground_preview)
    mesh.materials.append(material(meta['materials'][0],Path(ground_preview).parent))
    bpy.ops.object.select_all(action='DESELECT');terrain.select_set(True);bpy.context.view_layer.objects.active=terrain
    try:
        editable_materials.make(bpy.context,'terrain')
    except ValueError as error:
        # The plain shader preview still exports; only painting is unavailable.
        terrain['hb_template_note']='Paintable terrain unavailable: '+str(error)
    # Sky boundary: an inward-facing box; its +sky faces are dropped during preparation.
    box=bpy.data.meshes.new('SkyBoundary')
    v=[(x,y,z) for x in (-30,30) for y in (-30,30) for z in (-12,12)]
    box.from_pydata(v,[],[(0,2,3,1),(4,5,7,6),(0,1,5,4),(2,6,7,3),(0,4,6,2),(1,3,7,5)])
    box.uv_layers.new(name='UVMap');box.materials.append(sky_material())
    sky=bpy.data.objects.new('SkyBoundary',box);collection.objects.link(sky)
    sky.scale=(SKY_SCALE,)*3;sky.location=(0,0,SKY_CENTER_Z);sky['hb_working_units']=100
    chief=None
    if chief_asset and chief_preview:
        chief=place(chief_asset,chief_preview,config,location=(0,0,0))
        chief.name='Master Chief (scale reference)'
        # Scale reference only: never compiled into the level.
        chief['hb_ignore']=True
    for screen in bpy.data.screens:
        for area in screen.areas:
            if area.type=='VIEW_3D':area.spaces.active.shading.type='MATERIAL'
    compat.clear_view_fog(bpy.data.screens)
    bpy.ops.object.select_all(action='DESELECT');terrain.select_set(True);bpy.context.view_layer.objects.active=terrain
    return dict(terrain=terrain,sky=sky,chief=chief)

