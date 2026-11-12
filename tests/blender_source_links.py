"""Verified-source linking and the asynchronous preparation handoff."""
import sys,tempfile,time
from pathlib import Path
import bpy
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import halo_bridge
halo_bridge.register()
from halo_bridge import ui,blender_ops
for obj in list(bpy.context.scene.objects):bpy.data.objects.remove(obj,do_unlink=True)
door=bpy.data.meshes.new('Door');door.from_pydata([(0,0,0),(1,0,0),(0,1,0)],[],[(0,1,2)])
obj=bpy.data.objects.new('Door',door);bpy.context.collection.objects.link(obj)
obj['hb_id']='hb_fixture';obj['hb_kind']='model';obj['hb_source_tag']='fixture/render';obj['hb_collision']='missing'
match=dict(render='fixture/render',scenery='fixture/scenery',collision='fixture/collision')
for result in ({'matches':[]},{'matches':[match,dict(match,scenery='fixture/alternative')]}):
    try:blender_ops.link_verified_scenery([obj],result)
    except RuntimeError:pass
    else:raise AssertionError('Missing/ambiguous source accepted')
    assert obj['hb_kind']=='model'
with tempfile.TemporaryDirectory() as tmp:
    s=bpy.context.scene.halo_bridge;s.cache=tmp;s.kit=tmp;s.level='hb_fixture'
    # Preparation validates shaders first; give the door a fixture Halo shader tag.
    shader=Path(tmp)/'tags/fixture/door.shader';shader.parent.mkdir(parents=True);shader.write_bytes(b'fixture')
    mat=bpy.data.materials.new('fixture');mat['hb_shader']=r'fixture\door';obj.data.materials.append(mat)
    ui.build.ensure_sapien_closed=lambda:None
    # Preparation no longer resolves sources itself; link the single verified match first.
    assert blender_ops.link_verified_scenery([obj],{'matches':[match]})==1
    assert obj['hb_scenery_tag']=='fixture/scenery' and obj['hb_verified_collision_tag']=='fixture/collision'
    compiled=[]
    def export(cfg,path):
        assert obj['hb_kind']=='scenery' and obj['hb_collision']=='tag'
        return [dict(tag=obj['hb_scenery_tag'])]
    ui.blender_ops.export_scene=export
    def build(cfg,path,placements,cancel,progress):
        compiled.extend(placements);return 'fixture.scenario'
    ui.build.prepare=build
    # The collision-policy notice is a reviewable warning; accept it as the sidebar button does.
    bpy.ops.halo_bridge.prepare(warnings_accepted=True)
    deadline=time.monotonic()+5
    while ui._task and time.monotonic()<deadline:
        delay=ui.poll()
        if ui._task:assert delay is not None,'Chained preparation lost its timer'
        time.sleep(.01)
    assert not ui._task and not ui._error,ui._error
    assert compiled==[{'tag':'fixture/scenery'}] and ui._message=='Ready: fixture.scenario'
print('PASS: missing/ambiguous routes rejected, verified scenery linkage, preparation continues after source resolution')
