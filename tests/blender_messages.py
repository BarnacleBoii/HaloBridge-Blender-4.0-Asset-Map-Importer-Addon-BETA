"""Message surfaces and export-collision diagnostics, without game files."""
import sys,tempfile
from pathlib import Path
import bpy
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import halo_bridge
halo_bridge.register()
from halo_bridge import ui,blender_ops

class Layout:
    def __init__(self):self.text=[]
    def label(self,**kwargs):self.text.append(kwargs.get('text',''))
    def operator(self,*args,**kwargs):return self
    def popover(self,**kwargs):self.text.append(kwargs.get('text',''))
    def row(self,**kwargs):return self

ui._message='A long warning with useful instructions. '*20
ui._error='Synthetic collision error'
layout=Layout();ui.draw_messages(layout,bpy.context,popover=True)
assert all(len(line)<=48 for line in layout.text[1:])
assert ' '.join(layout.text[1:])==ui._message.strip()
surface=Layout();surface.layout=surface
ui.draw_message_header(surface,bpy.context)
assert 'HaloBridge Warnings and Messages' in surface.text
assert bpy.types.HB_PT_messages.bl_order<0

with tempfile.TemporaryDirectory() as tmp:
    obj=bpy.data.objects.new('turret_garbage_fixture',bpy.data.meshes.new('fixture'))
    bpy.context.collection.objects.link(obj)
    obj['hb_id']='fixture';obj['hb_kind']='model';obj['hb_cache']=tmp
    assert 'Raw render model' in blender_ops.collision_issue(obj)
    bpy.ops.halo_bridge.select_collision_issues()
    assert obj.select_get() and bpy.context.active_object==obj
    obj['hb_kind']='instance';obj['hb_collision']='original'
    assert 'missing' in blender_ops.collision_issue(obj)
    Path(tmp,'collision.json').write_text('{}')
    assert not blender_ops.collision_issue(obj)
    obj['hb_kind']='scenery';assert not blender_ops.collision_issue(obj)
    obj['hb_kind']='model';obj['hb_ignore']=True
    assert not blender_ops.collision_issue(obj)
halo_bridge.unregister()
halo_bridge.register()
halo_bridge.unregister()
print('PASS: message wrapping/header, panel registration lifecycle, raw model/BSP collision diagnoses and selecting affected assets')
