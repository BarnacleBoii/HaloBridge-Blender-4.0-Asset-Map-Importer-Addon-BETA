"""Vehicle previews become original tag placements, never terrain geometry."""
import sys,tempfile,json,math
from pathlib import Path
import bpy
from mathutils import Matrix
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import halo_bridge
halo_bridge.register()
from halo_bridge import vehicles,blender_ops,geometry_export,ui
from halo_bridge.diagnostics import ValidationError
for obj in list(bpy.context.scene.objects):bpy.data.objects.remove(obj,do_unlink=True)
with tempfile.TemporaryDirectory() as tmp:
 tag=r'objects\vehicles\scorpion\scorpion';p=Path(tmp)/'tags'/(tag+'.vehicle');p.parent.mkdir(parents=True);p.write_bytes(b'fixture')
 bpy.ops.mesh.primitive_cube_add();obj=bpy.context.object;obj.name='scorpion'
 obj['hb_source_tag']=tag;obj['hb_game']='halo3';obj['hb_working_units']=100
 obj['hb_mesh_signature']=blender_ops.mesh_signature(obj.data)
 obj['hb_vehicle_matches']=json.dumps([dict(render=tag,vehicle=tag)])
 assert bpy.ops.halo_bridge.choose_vehicle('EXEC_DEFAULT',choice=tag)=={'FINISHED'}
 obj.scale=(100,)*3;obj.location=(100,200,300);obj.rotation_euler=(.1,.2,.3)
 bpy.context.view_layer.update();cfg={'kit':tmp}
 before=blender_ops.mesh_signature(obj.data)
 row=vehicles.plan(bpy.context.scene,cfg)[0]
 assert row['position']==[1,2,3] and abs(row['scale']-1)<1e-5
 assert max(abs(a-b) for a,b in zip(row['rotation'],[math.degrees(.3),-math.degrees(.2),math.degrees(.1)]))<1e-4
 assert obj not in geometry_export.objects(bpy.context.scene)
 copy=obj.copy();copy.data=obj.data;bpy.context.collection.objects.link(copy)
 rows=vehicles.plan(bpy.context.scene,cfg);assert len({r['id'] for r in rows})==2
 assert copy.data==obj.data and blender_ops.mesh_signature(obj.data)==before
 # Origin-only shifts retain the original vehicle pivot and world placement.
 tri=bpy.data.meshes.new('pivot test');tri.from_pydata([(0,0,0),(1,0,0),(0,1,0)],[],[(0,1,2)])
 pivot=bpy.data.objects.new('pivot',tri);bpy.context.collection.objects.link(pivot)
 for key in ('hb_game','hb_source_tag','hb_working_units','hb_vehicle_tag','hb_vehicle_render'):pivot[key]=obj[key]
 pivot['hb_mesh_signature']=blender_ops.mesh_signature(tri);pivot['hb_cache']=tmp
 Path(tmp,'preview.json').write_text(json.dumps({'meshes':[{'positions':[[0,0,0],[1,0,0],[0,1,0]],'segments':[{'indices':[0,1,2]}]}]}))
 tri.transform(Matrix.Translation((-1,-2,-3)));pivot.matrix_world=Matrix.Translation((100,200,300))@Matrix.Scale(100,4)
 bpy.context.view_layer.update()
 pivot_rows=vehicles.plan(bpy.context.scene,cfg)
 assert next(r for r in pivot_rows if r['id']==pivot['hb_vehicle_id'])['position']==[0,0,0]
 bpy.data.objects.remove(pivot,do_unlink=True);bpy.data.meshes.remove(tri)
 obj.scale.x=80;bpy.context.view_layer.update()
 try:vehicles.plan(bpy.context.scene,cfg)
 except ValidationError as e:assert 'uniform scale' in str(e)
 else:raise AssertionError('Nonuniform vehicle accepted')
 obj.scale=(100,)*3;obj.data.vertices[0].co.x+=.1;bpy.context.view_layer.update()
 try:vehicles.plan(bpy.context.scene,cfg)
 except ValidationError as e:assert 'edited' in str(e)
 else:raise AssertionError('Edited vehicle was silently replaced')
 assert bpy.ops.halo_bridge.vehicle_static()=={'FINISHED'}
 assert obj in geometry_export.objects(bpy.context.scene)
halo_bridge.unregister()
print('PASS original tag picker, geometry exclusion, scale/rotation, duplicate identities, edited-model rejection and static fallback')
