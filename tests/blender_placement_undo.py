import sys,tempfile,time,threading
from pathlib import Path
import bpy
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import halo_bridge
halo_bridge.register()
from halo_bridge import ui,catalog,blender_ops

def wait():
    while ui._task:
        ui.poll();time.sleep(.01)
    assert not ui._error,ui._error

def count():return len([o for o in bpy.context.scene.objects if o.get('hb_asset_id')])
with tempfile.TemporaryDirectory() as tmp:
    bpy.context.scene.halo_bridge.cache=tmp
    assets=[dict(id=str(i),name='Model '+str(i),level='fixture',category='Structures',kind='instance',game='halo3',tag='fixture',section=i) for i in range(2)]
    assets.append(dict(assets[0],id='mat',name='Material only',kind='material',category='Materials'))
    catalog.write_json(Path(tmp)/'catalogue.json',dict(version=1,assets=assets))
    path=Path(tmp)/'preview.json'
    catalog.write_json(path,dict(materials=[dict(id='0',name='fixture',textures=[],alpha='opaque')],meshes=[dict(positions=[[0,0,0],[1,0,0],[0,1,0]],uv=[],normals=[],segments=[dict(indices=[0,1,2],material=0)])]))
    ui.load_catalogue();blender_ops.ensure_exporter=lambda:None
    ui.jobs.extract=lambda asset,cfg,cancel:path
    bpy.ops.ed.undo_push(message='Baseline')
    bpy.ops.halo_bridge.place();wait()
    bpy.context.scene.halo_bridge.active_index=1
    bpy.ops.halo_bridge.place();wait()
    assert count()==2
    before=[m.name for m in bpy.context.object.data.materials]
    bpy.context.scene.halo_bridge.active_index=2
    bpy.ops.halo_bridge.place();wait()
    assert count()==2 and before==[m.name for m in bpy.context.object.data.materials]
    for _ in range(3):
        bpy.ops.ed.undo();bpy.context.view_layer.update()
        print('UNDO COUNT',count())
    assert count()==0
    for _ in range(3):bpy.ops.ed.redo();bpy.context.view_layer.update()
    assert count()==2
    for _ in range(8):
        bpy.ops.ed.undo();bpy.context.view_layer.update()
        bpy.ops.ed.redo();bpy.context.view_layer.update()
    # Explicit assignment must not change a linked duplicate's material slots.
    first=next(o for o in bpy.context.scene.objects if o.get('hb_asset_id')=='0')
    twin=first.copy();bpy.context.collection.objects.link(twin)
    original_data=twin.data
    bpy.context.view_layer.objects.active=first
    bpy.context.scene.halo_bridge.active_index=2
    bpy.ops.halo_bridge.place(apply_material=True);wait()
    assert first.data!=twin.data and twin.data==original_data
    bpy.ops.ed.undo();bpy.context.view_layer.update()
    # Preview-on placement also remains undoable.
    bpy.context.scene.halo_bridge.active_index=1
    bpy.ops.halo_bridge.toggle_preview()
    while ui._preview_pending or ui._task:
        ui.preview_tick();ui.poll();time.sleep(.01)
    bpy.ops.halo_bridge.place();wait()
    bpy.ops.ed.undo();bpy.context.view_layer.update()
    bpy.ops.ed.redo();bpy.context.view_layer.update()
    gate=threading.Event()
    def delayed(asset,cfg,cancel):gate.wait(5);return path
    ui.jobs.extract=delayed
    bpy.context.scene.halo_bridge.active_index=0
    bpy.ops.halo_bridge.place()
    bpy.ops.ed.undo();gate.set();time.sleep(.1)
    ui.poll()
    assert ui._task is None
print('PASS: separate models, material loading, real undo/redo and pending-job invalidation')
