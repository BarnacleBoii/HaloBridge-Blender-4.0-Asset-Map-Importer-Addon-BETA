"""Original-coordinate visual map import; intentionally separate from map authoring."""
from pathlib import Path
import bpy
from mathutils import Matrix,Vector
from .catalog import read_json,stable_id
from .blender_ops import mesh_from_preview
from .diagnostics import ValidationError


def center_mesh_origin(mesh):
    """Move a mesh's bounding-box center to zero; return the compensating offset."""
    if not mesh.vertices:return Vector((0,0,0))
    center=Vector(tuple((min(v.co[i] for v in mesh.vertices)+max(v.co[i] for v in mesh.vertices))/2 for i in range(3)))
    mesh.transform(Matrix.Translation(-center));mesh.update()
    mesh['hb_origin_center']=list(center)
    return center

def center_existing_origins(context):
    """Blender Origin to Geometry, including previously centered and authored meshes."""
    objects=[o for o in context.scene.objects if o.type=='MESH']
    if not objects:return 0
    if any(o.library or o.data.library for o in objects):
        raise RuntimeError('Make linked library meshes local before centering all scene origins.')
    tracked={o.data:(o.data.vertices[0].co.copy(),Vector(o.data['hb_origin_center']))
             for o in objects if o.data.vertices and 'hb_origin_center' in o.data}
    # Native operator uses this context collection, including hidden scene meshes.
    # Keep the user's selection and active object unchanged.
    with context.temp_override(selected_editable_objects=objects,selected_objects=objects,active_object=objects[0],object=objects[0]):
        result=bpy.ops.object.origin_set(type='ORIGIN_GEOMETRY',center='MEDIAN')
    if result!={'FINISHED'}:raise RuntimeError('Blender could not center the scene origins.')
    # Future cached map imports need the new compensation, not the old bbox center.
    for mesh,(before,center) in tracked.items():
        mesh['hb_origin_center']=list(center+before-mesh.vertices[0].co)
    return len(objects)


def import_scene(context,manifest,progress=None,indices=None):
    manifest=Path(manifest);data=read_json(manifest)
    if data.get('kind')!='halo3_map_scene' or data.get('matrix_convention')!='row_vector':
        raise RuntimeError('Unsupported original-map scene manifest.')
    if not data.get('placements'):raise RuntimeError('The map has no decoded visual placements.')
    progress=progress or (lambda message:None)
    collection=bpy.data.collections.new('Map: '+data['scenario'].replace('\\','/').split('/')[-1]+' (original layout)')
    # Build off-scene so every timer yield does not re-evaluate a growing map.
    # Publish the complete collection only after all placements succeed.
    collection['hb_map_reference']=True
    groups={};objects=[];new_meshes=[];cache={}
    old_selection=list(context.selected_objects);old_active=context.active_object
    try:
        for index,item in enumerate(data['placements']):
            if indices is not None and index not in indices:continue
            progress('Importing original layout '+str(index+1)+'/'+str(len(data['placements']))+': '+item['group'])
            key=item['mesh']
            if key not in cache:
                asset_id='map_centered_v1_'+stable_id(str(manifest.resolve()),key)
                mesh=next((m for m in bpy.data.meshes if m.get('hb_asset_id')==asset_id),None)
                if mesh is None:
                    path=(manifest.parent/data['meshes'][key]).resolve()
                    if path.parent!=manifest.parent.resolve():raise RuntimeError('Invalid map mesh path.')
                    mesh=mesh_from_preview(path,asset_id);new_meshes.append(mesh)
                    center_mesh_origin(mesh)
                cache[key]=mesh
            if item['group'] not in groups:
                child=bpy.data.collections.new(item['group']);collection.children.link(child);groups[item['group']]=child
            obj=bpy.data.objects.new(item['name'],cache[key]);groups[item['group']].objects.link(obj);objects.append(obj)
            obj.matrix_world=Matrix.Scale(100,4)@Matrix(item['matrix']).transposed()@Matrix.Translation(Vector(cache[key].get('hb_origin_center',(0,0,0))))
            obj['hb_game']=data.get('game','halo3');obj['hb_working_units']=100
            obj['hb_map_reference']=True;obj['hb_ignore']=True
            obj['hb_source_tag']=item.get('source_tag','')
            obj['hb_map_placement_index']=index;obj['hb_map_manifest']=str(manifest)
            yield
        context.scene.collection.children.link(collection)
        context.scene['hb_working_units']=100
        context.scene.unit_settings.system='METRIC';context.scene.unit_settings.scale_length=.03048
        for screen in bpy.data.screens:
            for area in screen.areas:
                if area.type=='VIEW_3D':area.spaces.active.shading.type='MATERIAL'
        # Keep the user's current selection; a whole-map import can contain
        # thousands of objects and should not make accidental mass edits easy.
    except BaseException:
        for obj in objects:bpy.data.objects.remove(obj,do_unlink=True)
        for child in groups.values():bpy.data.collections.remove(child)
        bpy.data.collections.remove(collection)
        for mesh in new_meshes:
            if mesh.users==0:bpy.data.meshes.remove(mesh)
        for obj in old_selection:
            if obj.name in context.view_layer.objects:obj.select_set(True)
        if old_active and old_active.name in context.view_layer.objects:context.view_layer.objects.active=old_active
        raise


def repair_scene(context,manifest,progress=None):
    """Add newly recovered rows, keeping edited objects and intentional deletions."""
    import json
    refs=[o for o in context.scene.objects if o.get('hb_map_reference')]
    paths={o.get('hb_map_manifest','') for o in refs}
    if len(paths)!=1:raise RuntimeError('Repair one imported map at a time.')
    old_path=Path(next(iter(paths)));new_path=Path(manifest)
    old=read_json(old_path);new=read_json(new_path)
    if old.get('scenario')!=new.get('scenario'):raise RuntimeError('The selected .map is different from the imported scene. Select its original .map filename and retry.')
    if new.get('decoded_bsps')!=new.get('expected_bsps'):
        raise ValidationError(['Retry still has '+str(new.get('decoded_bsps'))+'/'+str(new.get('expected_bsps'))+' terrain BSPs. Existing scene retained.']+[w for w in new.get('warnings',[]) if w.startswith('BSP ')],'Repair incomplete import')
    def identity(row):return json.dumps(row,sort_keys=True,separators=(',',':'))
    lookup={}
    for index,row in enumerate(new['placements']):lookup.setdefault(identity(row),[]).append(index)
    remap={}
    for index,row in enumerate(old['placements']):
        candidates=lookup.get(identity(row),[])
        if len(candidates)!=1:raise RuntimeError('Cannot uniquely match the old import to the recovered map: '+row['name']+'. Existing scene retained.')
        remap[index]=candidates[0]
    for key in old['meshes']:
        before=read_json(old_path.parent/old['meshes'][key]);after=read_json(new_path.parent/new['meshes'][key])
        if before['meshes']!=after['meshes'] or [(m['id'],m.get('shader','')) for m in before['materials']]!=[(m['id'],m.get('shader','')) for m in after['materials']]:
            raise RuntimeError('Recovered source differs from the old geometry or shaders. Import into a separate scene to preserve edits.')
    for obj in refs:
        if obj.get('hb_map_placement_index',-1) not in remap:raise RuntimeError('An object lost its original placement identity. Existing scene retained.')
    additions=set(range(len(new['placements'])))-set(remap.values())
    if additions:yield from import_scene(context,new_path,progress,indices=additions)
    for obj in refs:
        obj['hb_map_placement_index']=remap[obj['hb_map_placement_index']]
        obj['hb_map_manifest']=str(new_path)
    if progress:progress('Recovered '+str(len(additions))+' missing placements. Existing edits and deletions retained.')

def export_plan(context):
    """Validate the imported base before reusing its original collision tags.

    Original terrain/placements must remain unchanged. Newly placed scenery
    has separate persistent ownership and can move, duplicate or be removed.
    """
    import hashlib,json,math
    from . import blender_ops
    context.view_layer.update()
    refs=[o for o in context.scene.objects if o.get('hb_map_reference')]
    manifests={o.get('hb_map_manifest','') for o in refs}
    if len(manifests)!=1 or not next(iter(manifests)):
        raise RuntimeError('Prepare one imported map per scene. Multiple map imports cannot share an original collision base.')
    manifest=Path(next(iter(manifests)));data=read_json(manifest)
    if not data or data.get('kind')!='halo3_map_scene':raise RuntimeError('Original map cache is missing. Reimport the map before preparation.')
    source=data['scenario'];rows=data['placements'];by_index={};issues=[];checked={}
    if data['decoded_bsps']!=data['expected_bsps']:
        issues.append('Incomplete map extraction: '+source+' has '+str(data['decoded_bsps'])+' of '+str(data['expected_bsps'])+' terrain BSPs. Reimport after resolving the extraction errors below; editing geometry did not cause this count mismatch.')
        issues.extend(w for w in data.get('warnings',[]) if w.startswith('BSP '))
    for obj in refs:
        index=obj.get('hb_map_placement_index',-1)
        if index<0 or index>=len(rows):issues.append(obj.name+': missing original placement identity.');continue
        row=rows[index]
        if row['group']=='Skies':continue # Sky selection comes from scenario tags.
        if index in by_index:issues.append(obj.name+': duplicated original map piece; use Place asset(s) for new scenery.');continue
        by_index[index]=obj
        units=float(obj.get('hb_working_units',1));center=Vector(obj.data.get('hb_origin_center',(0,0,0)))
        expected=Matrix.Scale(units,4)@Matrix(row['matrix']).transposed()@Matrix.Translation(center)
        if max(abs(obj.matrix_world[r][c]-expected[r][c]) for r in range(4) for c in range(4))>.02:
            issues.append(obj.name+': original-map piece moved or resized. Restore its imported transform; moving original base pieces is not supported yet.')
        if obj.modifiers:issues.append(obj.name+': original-map modifiers cannot be transferred.')
        key=(obj.data.as_pointer(),row['mesh'])
        if key not in checked:
            path=(manifest.parent/data['meshes'][row['mesh']]).resolve()
            if path.parent!=manifest.parent.resolve():raise RuntimeError('Unsafe cached mesh path.')
            meta=read_json(path);points=[];faces=[];material_ids=[];uvs=[]
            for part in meta['meshes']:
                offset=len(points);points.extend(part['positions']);uvs.extend(part.get('uv') or [[0,0]]*len(part['positions']))
                for segment in part['segments']:
                    indices=segment['indices']
                    for i in range(0,len(indices),3):faces.append(tuple(offset+n for n in indices[i:i+3]));material_ids.append(segment['material'])
            mesh=obj.data;good=len(points)==len(mesh.vertices) and len(faces)==len(mesh.polygons)
            # Reproduce Blender's float32 import and origin-centering arithmetic.
            # Adding the center back and comparing to JSON doubles falsely
            # marked distant, untouched geometry as edited (High Charity).
            if good:good=all(max(abs(v.co[i]-(Vector(p)-center)[i]) for i in range(3))<.0002 for v,p in zip(mesh.vertices,points))
            if good:good=all(tuple(p.vertices)==f for p,f in zip(mesh.polygons,faces))
            materials=meta['materials'];order=[m['id'] for m in materials]
            if good:good=len(mesh.materials)==len(materials) and all(m and m.get('hb_shader','')==old.get('shader','') for m,old in zip(mesh.materials,materials))
            if good:good=all(p.material_index==(order.index(mid) if mid in order else 0) for p,mid in zip(mesh.polygons,material_ids))
            if good and mesh.uv_layers.active:good=all(max(abs(mesh.uv_layers.active.data[loop.index].uv[i]-uvs[loop.vertex_index][i]) for i in (0,1))<.0002 for loop in mesh.loops)
            checked[key]=good
        if not checked[key]:issues.append(obj.name+': original geometry or Halo materials were edited; restore or reimport this piece.')
    missing=[row['name'] for i,row in enumerate(rows) if row['group']!='Skies' and i not in by_index]
    for name in missing:issues.append('Deleted original map piece: '+name+'. Rebuilding deletions is not supported yet.')
    placements=[];ids=set()
    for obj in context.scene.objects:
        if obj.get('hb_map_reference') or obj.get('hb_ignore') or obj.type!='MESH':continue
        if obj.get('hb_kind')!='scenery' or not obj.get('hb_id'):
            issues.append(obj.name+': this route supports the original map plus added scenery tags. Move custom terrain/the starter shell to another scene; additional BSP instances are not supported yet.');continue
        loc,rot,scale=obj.matrix_world.decompose();units=float(obj.get('hb_working_units',1))
        if min(scale)<=0 or max(scale)-min(scale)>1e-5:issues.append(obj.name+': use positive uniform scale.');continue
        rebuilt=Matrix.LocRotScale(loc,rot,scale)
        if max(abs(obj.matrix_world[r][c]-rebuilt[r][c]) for r in range(4) for c in range(4))>1e-4:issues.append(obj.name+': clear parent shear.');continue
        if obj.modifiers or blender_ops.mesh_signature(obj.data)!=obj.get('hb_mesh_signature'):issues.append(obj.name+': added scenery mesh was edited.');continue
        if obj['hb_id'] in ids:obj['hb_id']=blender_ops.new_id()
        ids.add(obj['hb_id']);euler=rot.to_euler('ZYX')
        placements.append(dict(id=obj['hb_id'],tag=obj['hb_scenery_tag'],position=list(loc/units),rotation=[math.degrees(euler.z),-math.degrees(euler.y),math.degrees(euler.x)],scale=float(scale.x)/units))
    if issues:raise ValidationError(issues,'Imported map validation')
    return dict(source=source,reference_digest=hashlib.sha256(manifest.read_bytes()).hexdigest(),reference_objects=len(refs),placements=placements,warnings=data.get('warnings',[]),bsps={tag:[dict(name=row['name'].rsplit(' / ',1)[-1],matrix=row['matrix']) for row in rows if row['group']=='BSP instances' and row['source_tag']==tag] for tag in sorted({row['source_tag'] for row in rows if row['group']=='Terrain'})})
