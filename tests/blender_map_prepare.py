"""Current-scene dispatch, optional warning confirmation and sky selection."""
import sys,tempfile,time
from pathlib import Path
from unittest.mock import patch
import bpy
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import halo_bridge
halo_bridge.register()
from halo_bridge import ui,catalog
with tempfile.TemporaryDirectory() as tmp:
    s=bpy.context.scene.halo_bridge;s.kit=tmp;s.cache=tmp;s.level='hb_test';s.open_sapien=False
    sky=Path(tmp)/'tags/levels/multi/shrine/shrine.scenario';sky.parent.mkdir(parents=True);sky.touch()
    manifest=Path(tmp)/'scene.json';catalog.write_json(manifest,{'scenario':r'levels\multi\shrine\shrine'})
    obj=bpy.context.object;obj['hb_map_reference']=True;obj['hb_map_manifest']=str(manifest)
    # Preparation validates shaders first; give the cube a fixture Halo shader tag.
    shader=Path(tmp)/'tags/fixture/test.shader';shader.parent.mkdir(parents=True);shader.write_bytes(b'fixture')
    obj.data.materials.clear();mat=bpy.data.materials.new('fixture');mat['hb_shader']=r'fixture\test';obj.data.materials.append(mat)
    def export(cfg,path,progress=None):
        assert cfg['sky_scenario']==r'levels\multi\shrine\shrine'
        return []
    def wait():
        deadline=time.monotonic()+5
        while ui._task and time.monotonic()<deadline:ui.poll();time.sleep(.01)
        assert not ui._task and not ui._error,ui._error
    with patch.object(ui.build,'ensure_sapien_closed'),patch.object(ui.geometry_export,'export',side_effect=export) as exp,patch.object(ui.build,'prepare',return_value='test.scenario') as build,patch.object(ui.map_export,'prepare',side_effect=AssertionError('Original base must never be used')),patch.object(ui,'confirm_map_warnings') as popup:
        bpy.ops.halo_bridge.prepare();assert popup.call_count==1;assert not exp.called and not build.called
        bpy.ops.halo_bridge.prepare(warnings_accepted=True)
        assert ui._prepare_running and ui.prepare_button_text().startswith('(LOADING...PLEASE WAIT)')
        wait();assert exp.call_count==build.call_count==1
        assert not ui._prepare_running and ui.prepare_button_text()=='Prepare current scene for sapien'
        assert ui._prepare_status.startswith('Finished.')
        assert 'Edits, transforms, modifiers and deletions' in bpy.data.texts['HaloBridge preparation report'].as_string()
    with patch.object(ui.build,'ensure_sapien_closed'),patch.object(ui.geometry_export,'export',return_value=[]),patch.object(ui.build,'prepare',side_effect=RuntimeError('Compiler fixture failure')):
        bpy.ops.halo_bridge.prepare(warnings_accepted=True)
        while ui._task:ui.poll();time.sleep(.01)
        assert not ui._prepare_running and 'Compiler fixture failure' in ui._prepare_status
print('PASS current mesh dispatch, warning-before-build and automatic source sky')
