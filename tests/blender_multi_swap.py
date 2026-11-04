import sys
from pathlib import Path
import bpy
from mathutils import Matrix
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import halo_bridge
halo_bridge.register()
from halo_bridge import ui,blender_ops
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
bpy.ops.mesh.primitive_cube_add(location=(3,7,9));a=bpy.context.object;a.rotation_euler=(.2,.3,.4);a.scale=(2,3,4)
bpy.ops.mesh.primitive_cube_add(location=(-4,8,2));b=bpy.context.object;b.scale=(100,100,100);b['hb_working_units']=100;b['hb_id']='keep-me'
a.select_set(True);bpy.context.view_layer.update()
expected=[Matrix.LocRotScale(o.matrix_world.translation,o.matrix_world.to_quaternion(),(100,100,100)) for o in [a,b]]
mesh=bpy.data.meshes.new('cached');mesh.from_pydata([(0,0,0),(1,0,0),(0,1,0)],[],[(0,1,2)])
def place(*args):
    obj=bpy.data.objects.new('replacement',mesh);bpy.context.collection.objects.link(obj);obj['hb_working_units']=100;obj.scale=(100,100,100)
    return obj
blender_ops.place=place;ui.refresh=lambda ctx:None;ui._catalogue={'assets':[]}
asset={'kind':'model','name':'tree'}
targets,reason=ui.replacement_target(bpy.context,asset);assert len(targets)==2 and not reason
result=ui.swap_objects(bpy.context,[a,b],asset,None,{})
for obj,matrix in zip(result,expected):
    assert max(abs(obj.matrix_world[r][c]-matrix[r][c]) for r in range(4) for c in range(4))<.001
assert result[0].data==result[1].data and result[1]['hb_id']=='keep-me'
assert len(bpy.context.selected_objects)==2
before=set(bpy.data.objects);count=0
def broken(*args):
    global count
    obj=place();count+=1
    if count==2:raise RuntimeError('fail')
    return obj
blender_ops.place=broken
try:ui.swap_objects(bpy.context,result,asset,None,{})
except RuntimeError:pass
else:raise AssertionError('Expected failure')
assert set(bpy.data.objects)==before
text=bpy.data.texts.new('report-test');text.write('\n'.join(str(i) for i in range(100)))
with bpy.context.temp_override(area=bpy.context.screen.areas[0]):
    bpy.ops.halo_bridge.diagnostics(text_name='report-test')
assert text.current_line_index==0
print('PASS: multi-object greybox swap, transforms, shared mesh, identity, rollback, report top')
