"""Verified-source linking and the asynchronous preparation handoff."""
import sys,tempfile,time
from pathlib import Path
import bpy
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import halo_bridge
halo_bridge.register()
from halo_bridge import ui,blender_ops
for obj in list(bpy.context.scene.objects):bpy.data.objects.remove(obj,do_unlink=True)
obj=bpy.data.objects.new('Door',bpy.data.meshes.new('Door'));bpy.context.collection.objects.link(obj)
obj['hb_id']='hb_fixture';obj['hb_kind']='model';obj['hb_source_tag']='fixture/render';obj['hb_collision']='missing'
match=dict(render='fixture/render',scenery='fixture/scenery',collision='fixture/collision')
for result in ({'matches':[]},{'matches':[match,dict(match,scenery='fixture/alternative')]}):
    try:blender_ops.link_verified_scenery([obj],result)
    except RuntimeError:pass
    else:raise AssertionError('Missing/ambiguous source accepted')
    assert obj['hb_kind']=='model'
with tempfile.TemporaryDirectory() as tmp:
    s=bpy.context.scene.halo_bridge;s.cache=tmp;s.kit=tmp;s.level='hb_fixture'
    ui.build.ensure_sapien_closed=lambda:None
    ui.jobs.helper=lambda *args:{'matches':[match]}
    compiled=[]
    def export(cfg,path):
        assert obj['hb_kind']=='scenery' and obj['hb_collision']=='tag'
        return [dict(tag=obj['hb_scenery_tag'])]
    ui.blender_ops.export_scene=export
    def build(cfg,path,placements,cancel,progress):
        compiled.extend(placements);return 'fixture.scenario'
    ui.build.prepare=build
    bpy.ops.halo_bridge.prepare()
    deadline=time.monotonic()+5
    while ui._task and time.monotonic()<deadline:
        delay=ui.poll()
        if ui._task:assert delay is not None,'Chained preparation lost its timer'
        time.sleep(.01)
    assert not ui._task and not ui._error,ui._error
    assert compiled==[{'tag':'fixture/scenery'}] and ui._message=='Ready: fixture.scenario'
print('PASS: missing/ambiguous routes rejected, verified scenery linkage, preparation continues after source resolution')
