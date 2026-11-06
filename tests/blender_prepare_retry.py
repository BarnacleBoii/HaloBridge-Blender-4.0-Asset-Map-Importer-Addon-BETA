from pathlib import Path
import sys,tempfile
from unittest.mock import patch
import bpy
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import halo_bridge
halo_bridge.register()
from halo_bridge import ui
from halo_bridge.diagnostics import ValidationError
with tempfile.TemporaryDirectory() as folder:
 bpy.context.scene.halo_bridge.cache=folder
 cfg={'game':'halo3','export_target':'halo3','level':'fixture','cache':folder,'kit':folder}
 with patch.object(ui,'export_config',return_value=cfg),patch.object(ui.build,'ensure_sapien_closed'),patch.object(ui,'preparation_warnings',side_effect=ValidationError(['Plane: empty material'])):
  try:bpy.ops.halo_bridge.prepare()
  except RuntimeError:pass
 print('IDNAME',ui.HBPrepare.bl_idname,'RUNNING',ui._prepare_running,'STATUS',ui._prepare_status,'TASK',ui._task,flush=True)
 assert not ui._prepare_running,'Preparation left locked after validation error'

# Exercise actual material validation and revalidation after deleting an object.
with tempfile.TemporaryDirectory() as folder:
 s=bpy.context.scene.halo_bridge;s.cache=folder;s.kit=folder;s.level='retry_fixture';s.skip_invalid=False
 shader=Path(folder)/'tags/test/ground.shader';shader.parent.mkdir(parents=True);shader.write_bytes(b'fixture')
 for obj in list(bpy.context.scene.objects):bpy.data.objects.remove(obj,do_unlink=True)
 bpy.ops.mesh.primitive_plane_add();bad=bpy.context.object;bad.name='DeletedPlane'
 bpy.ops.mesh.primitive_cube_add();bpy.context.object.name='inviso_block_fixture'
 bpy.ops.mesh.primitive_plane_add();good=bpy.context.object;good.name='GoodGround'
 mat=bpy.data.materials.new('Ground');mat['hb_shader']='test/ground';good.data.materials.append(mat)
 def attempt():
  with patch.object(ui.build,'ensure_sapien_closed'):
   try:bpy.ops.halo_bridge.prepare()
   except RuntimeError:pass
  assert not ui._prepare_running and ui._task is None
 attempt();assert 'DeletedPlane' in ui._error and 'inviso_block_fixture' in ui._error
 bpy.data.objects.remove(bad,do_unlink=True);bpy.context.view_layer.update()
 attempt();assert 'DeletedPlane' not in ui._error and 'inviso_block_fixture' in ui._error
 s.skip_invalid=True
 with patch.object(ui.build,'ensure_sapien_closed'),patch.object(ui,'confirm_map_warnings') as confirmation:
  bpy.ops.halo_bridge.prepare()
  assert confirmation.called and not ui._prepare_running
  issues=confirmation.call_args.args[2].issues
  assert any('WILL NOT EXPORT' in issue and 'inviso_block_fixture' in issue for issue in issues)
  assert not any('DeletedPlane' in issue for issue in issues)
print('PASS registered validation unlocks retry; deleted meshes disappear; skip mode reviews remaining exclusions')
