"""Asset-free UI smoke test. No game files, exporter, or helper processes required."""
import sys
import tempfile
import threading
import time
from pathlib import Path
import bpy

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import halo_bridge
halo_bridge.register()
from halo_bridge import ui,catalog,blender_ops

def wait():
    deadline=time.monotonic()+10
    while (ui._task or ui._preview_pending) and time.monotonic()<deadline:
        ui.preview_tick();ui.poll();time.sleep(.01)
    assert not ui._task and not ui._preview_pending and not ui._error,ui._error

with tempfile.TemporaryDirectory() as tmp:
    s=bpy.context.scene.halo_bridge;s.cache=tmp
    assets=[dict(id=str(i),name='Synthetic '+str(i),level='fixture',category='Structures',kind='instance',game='halo3',tag='fixture',section=i) for i in range(2)]
    catalog.write_json(Path(tmp)/'catalogue.json',dict(version=1,assets=assets))
    preview=Path(tmp)/'preview.json'
    catalog.write_json(preview,dict(materials=[],meshes=[dict(positions=[[0,0,0],[1,0,0],[0,1,0]],uv=[],normals=[],segments=[dict(indices=[0,1,2],material=0)])]))
    ui.load_catalogue()
    blender_ops.ensure_exporter=lambda:None
    ui.jobs.extract=lambda asset,cfg,cancel:preview
    bpy.ops.halo_bridge.toggle_preview();wait()
    assert bpy.context.object.get('hb_asset_id')=='0'
    s.active_index=1;wait()
    assert bpy.context.object.get('hb_asset_id')=='1'
    bpy.context.object.location=(8,3,-2)
    bpy.context.object.rotation_euler=(.2,.4,.7)
    bpy.context.object.scale=(1.5,)*3
    bpy.context.view_layer.update();matrix=bpy.context.object.matrix_world.copy()
    bpy.context.scene.cursor.location=(-20,0,0)
    bpy.ops.halo_bridge.place();wait()
    placed=bpy.context.object
    assert not placed.get('hb_ignore') and not s.preview_enabled
    assert all(abs(placed.matrix_world[r][c]-matrix[r][c])<1e-5 for r in range(4) for c in range(4))
    bpy.ops.halo_bridge.toggle_preview();wait()
    bpy.ops.halo_bridge.toggle_preview()
    assert bpy.context.object==placed and not ui.preview_active(bpy.context)
    gate=threading.Event()
    def delayed(asset,cfg,cancel):
        assert gate.wait(5)
        return preview
    ui.jobs.extract=delayed
    bpy.ops.halo_bridge.toggle_preview();ui.preview_tick()
    bpy.ops.halo_bridge.toggle_preview();gate.set();wait()
    assert not ui.preview_active(bpy.context)
    s.active_index=0;wait();assert not ui.preview_active(bpy.context)
    assert ui.config(bpy.context)['cache']==tmp
    s.cache='';assert ui.config(bpy.context)['cache']==str(catalog.default_storage())
    for cls in ui.classes:
        if issubclass(cls,bpy.types.Operator):
            assert getattr(bpy.ops.halo_bridge,cls.bl_idname.split('.')[1]).get_rna_type().description
print('PASS: synthetic live previews, placement transform, off while loading, selection restoration, storage and tooltips')
