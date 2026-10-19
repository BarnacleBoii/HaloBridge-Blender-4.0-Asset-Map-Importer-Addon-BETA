"""Background errors keep all issues and persist a report after async completion."""
import sys,tempfile,time
from pathlib import Path
from unittest.mock import patch
import bpy
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import halo_bridge
halo_bridge.register()
from halo_bridge import ui
from halo_bridge.diagnostics import ValidationError
with tempfile.TemporaryDirectory() as folder:
    issues=['fixture asset '+str(i)+': missing dependency' for i in range(35)]
    def failure(cancel):raise ValidationError(issues)
    with patch.object(ui,'config',return_value={'cache':folder}):
        ui.start(bpy.context,failure,lambda result:None,'Checking fixture')
        deadline=time.monotonic()+5
        while ui._task and time.monotonic()<deadline:
            ui.poll();time.sleep(.01)
        assert ui._task is None
        assert '35 issue(s)' in ui._message
        report=bpy.data.texts['HaloBridge diagnostics'].as_string()
        assert all(item in report for item in issues)
        files=list((Path(folder)/'diagnostics').glob('*.txt'))
        assert len(files)==1 and all(item in files[0].read_text() for item in issues)
        assert ui._reported_issues==issues
print('PASS all 35 async validation issues reach diagnostics and persistent report')
