import json,sys,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from halo_bridge import copy_level,jobs

class OriginalCopyTests(unittest.TestCase):
    def test_copy_rollback_and_repeat_protection(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);kit=root/'kit';kit.mkdir();maps=root/'maps';maps.mkdir();(maps/'test.map').write_bytes(b'fixture')
            cfg=dict(kit=str(kit),maps=str(maps),cache=str(root/'cache'),level='hb_copy')
            target=kit/'tags/levels/multi/hb_copy';scenario=target/'hb_copy.scenario'
            def process(args,log,**kwargs):
                job=json.loads(Path(args[1]).read_text());target.mkdir(parents=True);scenario.write_bytes(b'copied')
                Path(job['output']).write_text(json.dumps(dict(version=1,ok=True,scenario=job['scenario'])))
            with patch.object(copy_level.build,'ensure_sapien_closed'),patch.object(jobs,'helper',return_value={'scenario':'levels/test/test'}):
                def fail(*args,**kwargs):
                    target.mkdir(parents=True);scenario.write_bytes(b'incomplete');raise jobs.Cancelled('cancel')
                with patch.object(jobs,'run_process',side_effect=fail),self.assertRaises(jobs.Cancelled):copy_level.copy_original(cfg,'test.map')
                self.assertFalse(target.exists());self.assertFalse((kit/'halo_bridge.build.lock').exists())
                with patch.object(jobs,'run_process',side_effect=process):
                    path,result=copy_level.copy_original(cfg,'test.map')
                self.assertTrue(Path(path).exists());scenario.write_bytes(b'Sapien edits')
                with self.assertRaisesRegex(RuntimeError,'already exists'):copy_level.copy_original(cfg,'test.map')
                self.assertEqual(scenario.read_bytes(),b'Sapien edits')
                manifest=json.loads((root/'cache/projects/hb_copy/original-copy.json').read_text())
                self.assertEqual(manifest['mode'],'original_copy')
                with self.assertRaisesRegex(RuntimeError,'filename'):copy_level.copy_original(dict(cfg,level='hb_other'),'../test.map')

if __name__=='__main__':unittest.main()
