"""Native copy/paste and duplication must survive preview cleanup."""
import sys
from pathlib import Path
import bpy
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import halo_bridge
halo_bridge.register()
from halo_bridge import ui,geometry_export
for obj in list(bpy.context.scene.objects):bpy.data.objects.remove(obj,do_unlink=True)
bpy.ops.mesh.primitive_cube_add()
preview=bpy.context.object;preview['hb_id']='preview_identity';preview['hb_asset_id']='fixture'
ui.show_preview(bpy.context,preview,'Fixture')
preview.location=(4,5,6)
bpy.context.view_layer.update()
area=next(a for a in bpy.context.screen.areas if a.type=='VIEW_3D')
with bpy.context.temp_override(area=area):
    assert bpy.ops.view3d.copybuffer()=={'FINISHED'}
    assert bpy.ops.view3d.pastebuffer()=={'FINISHED'}
pasted=next(o for o in bpy.context.scene.objects if o!=preview)
print('PASTE',[(o.name,o.select_get(),bool(o.get('hb_preview'))) for o in bpy.context.scene.objects], 'ACTIVE',bpy.context.active_object.name)
assert pasted!=preview and pasted.get('hb_preview')
# Also cover paste contexts which retain the source selection.
preview.select_set(True)
ui.check_preview_copies()
assert not pasted.get('hb_preview') and not pasted.get('hb_ignore') and not pasted.hide_render
assert pasted['hb_id']!=preview['hb_id'] and tuple(pasted.location)==(4,5,6)
assert pasted in geometry_export.objects(bpy.context.scene)
assert bpy.context.active_object==pasted and not preview.select_get()
before=preview.matrix_world.copy()
with bpy.context.temp_override(area=area):bpy.ops.transform.translate(value=(3,0,0))
bpy.context.view_layer.update()
assert preview.matrix_world==before, 'Moving preview copy moved original'
assert pasted.location.x==7
ui.stop_preview(bpy.context)
assert pasted.name in bpy.context.scene.objects
# Shift-D of a live preview is handled identically, even before the timer fires.
bpy.ops.mesh.primitive_cube_add();preview=bpy.context.object;preview['hb_id']='second_preview'
ui.show_preview(bpy.context,preview,'Second')
bpy.ops.object.duplicate();duplicate=bpy.context.object
ui.stop_preview(bpy.context)
assert duplicate.name in bpy.context.scene.objects and not duplicate.get('hb_preview')
assert not duplicate.hide_render and not duplicate.get('hb_ignore')
# Copy/paste an ordinary placed asset; cleanup must leave both in the scene.
bpy.ops.object.select_all(action='DESELECT');pasted.select_set(True);bpy.context.view_layer.objects.active=pasted
with bpy.context.temp_override(area=area):
    bpy.ops.view3d.copybuffer();bpy.ops.view3d.pastebuffer()
normal_copy=next(o for o in bpy.context.scene.objects if o not in (pasted,duplicate))
before=pasted.matrix_world.copy()
ui.check_preview_copies()
assert bpy.context.active_object==normal_copy and not pasted.select_get()
print('NORMAL ACTIVE',bpy.context.active_object.name,'SELECTED',[o.name for o in bpy.context.selected_objects])
with bpy.context.temp_override(area=area):bpy.ops.transform.translate(value=(3,0,0))
bpy.context.view_layer.update()
assert pasted.matrix_world==before, 'Moving pasted asset also moved original'
assert normal_copy.location.x==pasted.location.x+3
ui.clear_previews(bpy.context)
assert normal_copy!=pasted and normal_copy.name in bpy.context.scene.objects
print('PASS native copy/paste, Shift-D, preserved selection/transforms and export inclusion')
