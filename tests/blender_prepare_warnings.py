"""Run in background Blender: warning dismissal must never block preparation."""
import sys
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch,Mock
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from halo_bridge import ui
from halo_bridge.diagnostics import ValidationError

scene=SimpleNamespace(as_pointer=lambda:123)
context=SimpleNamespace(scene=scene,window_manager=SimpleNamespace(popup_menu=Mock()))
cfg={'level':'testleveldudebro'}
issues=['Assets are exported as static, two-sided surfaces with generated collision.']
with patch.object(ui,'record_failure') as failure:
    ui._error='previous error';ui._reported_issues=['previous error']
    ui.confirm_map_warnings(context,cfg,ValidationError(issues))
    failure.assert_not_called()
    assert not ui._error and not ui._reported_issues
    pending=ui._pending_prepare_warning
    assert pending['issues']==issues and pending['config']==cfg
    # Dismissing the popup does not discard the sidebar confirmation token.
    context.window_manager.popup_menu.assert_called_once()
    assert ui._pending_prepare_warning is pending

operator=SimpleNamespace(token=pending['token'],accept=True)
prepare=Mock(return_value={'FINISHED'})
with patch.object(ui,'config',return_value=cfg),patch.object(ui,'preparation_warnings',return_value=issues),patch.object(ui.HBPrepare,'run',prepare):
    assert ui.HBConfirmPrepare.run(operator,context)=={'FINISHED'}
    prepare.assert_called_once_with(operator,context,warnings_accepted=True)
assert ui._pending_prepare_warning is None

ui.confirm_map_warnings(context,cfg,ValidationError(issues))
operator.token=ui._pending_prepare_warning['token'];operator.accept=False
assert ui.HBConfirmPrepare.run(operator,context)=={'CANCELLED'}
assert ui._pending_prepare_warning is None and not ui._prepare_running

ui.confirm_map_warnings(context,cfg,ValidationError(issues))
operator.token=ui._pending_prepare_warning['token'];operator.accept=True
with patch.object(ui,'config',return_value={'level':'different_level'}):
    try:ui.HBConfirmPrepare.run(operator,context)
    except RuntimeError as e:assert 'scene or setup changed' in str(e)
    else:raise AssertionError('Changed configuration bypassed confirmation')
print('PASS: warnings are not failures; dismissed popup remains actionable; continue, cancel and stale-config checks passed')

# A failed accepted preparation must be recorded once with all original issues.
ui.confirm_map_warnings(context,cfg,ValidationError(issues))
operator.token=ui._pending_prepare_warning['token'];operator.accept=True
operator.bl_idname='halo_bridge.confirm_prepare';operator.report=Mock()
operator.run=lambda ctx:ui.HBConfirmPrepare.run(operator,ctx)
errors=['Plane: assign an existing Halo shader.','Plane.002: assign an existing Halo shader.','Plane.003: assign an existing Halo shader.']
failure=ValidationError(errors)
with patch.object(ui,'config',return_value=cfg),patch.object(ui,'preparation_warnings',return_value=issues),patch.object(ui.HBPrepare,'run',side_effect=failure),patch.object(ui,'record_failure',return_value=errors) as recorder:
    assert ui.Guard.execute(operator,context)=={'CANCELLED'}
    recorder.assert_called_once()
    assert recorder.call_args.args[0] is failure
    assert recorder.call_args.args[0].issues==errors
assert not ui._prepare_running
print('PASS: all three underlying validation issues retained with a single error report')
