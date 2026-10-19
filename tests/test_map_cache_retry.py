import tempfile,unittest
from pathlib import Path
from unittest.mock import patch
from halo_bridge import jobs,catalog

class MapCacheRetryTests(unittest.TestCase):
    def test_incomplete_cache_retries_without_overwriting_then_reuses(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);maps=root/'maps';maps.mkdir();(maps/'test.map').write_bytes(b'map')
            cfg=dict(cache=str(root/'cache'),maps=str(maps))
            calls=[]
            def extract(args,*a,**kw):
                job=catalog.read_json(args[1]);out=Path(job['output']);calls.append(out)
                catalog.write_json(out/'texture_names.json',dict(version=1,textures={}))
                catalog.write_json(out/'scene.json',dict(expected_bsps=2,decoded_bsps=1 if len(calls)==1 else 2))
            with patch.object(jobs,'run_process',side_effect=extract):
                first=jobs.extract_map_scene(cfg,'test.map');before=first.read_bytes()
                second=jobs.extract_map_scene(cfg,'test.map')
                self.assertNotEqual(first,second);self.assertEqual(first.read_bytes(),before)
                self.assertEqual(jobs.extract_map_scene(cfg,'test.map'),second)
                self.assertEqual(len(calls),2)
