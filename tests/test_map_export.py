import sys,tempfile,unittest,threading
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from halo_bridge import map_export,catalog,jobs

class MapBuildTests(unittest.TestCase):
    def test_repeat_conflict_and_failed_sync_rollback(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);kit=root/'kit';cache=root/'cache';source='levels/test/test'
            src=kit/'tags/levels/test/test.scenario';src.parent.mkdir(parents=True);src.write_bytes(b'original')
            cfg=dict(kit=str(kit),cache=str(cache),level='hb_map',sky_scenario=source)
            plan=dict(source=source,reference_digest='fixture',placements=[],warnings=[],reference_objects=2)
            target=kit/'tags/levels/multi/hb_map/hb_map.scenario';record=cache/'projects/hb_map/map-build.json'
            state={};calls=[]
            def helper(kind,job,*a,**kw):
                calls.append(job['operation'])
                if job['operation']=='copy_level':target.parent.mkdir(parents=True);target.write_bytes(b'base');return {'ok':True}
                if job['operation']=='inspect':return dict(state=state.copy(),spawn_count=1)
                if job['operation']=='sync':target.write_bytes(b'updated');return {}
                return {}
            with patch.object(map_export.build,'ensure_sapien_closed'),patch.object(jobs,'helper',side_effect=helper):
                map_export.prepare(cfg,plan);before=record.read_bytes()
                map_export.prepare(cfg,plan);self.assertEqual(calls.count('copy_level'),1)
                state['hb_changed']='modified-in-Sapien'
                with self.assertRaisesRegex(RuntimeError,'CONFLICT'):map_export.prepare(cfg,plan)
                self.assertEqual(target.read_bytes(),b'updated')
                state.clear();before=record.read_bytes()
                def fail(kind,job,*a,**kw):
                    if job['operation']=='sync':target.write_bytes(b'incomplete');raise jobs.Cancelled('cancelled')
                    return helper(kind,job,*a,**kw)
                with patch.object(jobs,'helper',side_effect=fail),self.assertRaises(jobs.Cancelled):map_export.prepare(cfg,plan)
                self.assertEqual(target.read_bytes(),b'updated');self.assertEqual(record.read_bytes(),before)
                self.assertEqual(src.read_bytes(),b'original')

    def test_unowned_existing_output_is_preserved(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);target=root/'tags/levels/multi/hb_map/hb_map.scenario';target.parent.mkdir(parents=True);target.write_bytes(b'user-level')
            with self.assertRaisesRegex(RuntimeError,'another build'):
                map_export.prepare(dict(kit=str(root),cache=str(root/'cache'),level='hb_map'),dict(source='levels/test/test'))
            self.assertEqual(target.read_bytes(),b'user-level')
