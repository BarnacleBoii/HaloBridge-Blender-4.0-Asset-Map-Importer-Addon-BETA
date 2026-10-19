import sys,tempfile,threading,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from halo_bridge import catalog,build,jobs

class SafetyTests(unittest.TestCase):
    def test_reject_unsafe_names(self):
        for name in ('../stock','a/b','C:\\stock','con','ab','Upper','a'*33):
            with self.assertRaises(ValueError):catalog.safe_level(name)

    def test_mapping_survives_rescan(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/'Jungle/tree/model.amf';p.parent.mkdir(parents=True);p.write_bytes(b'fixture')
            c=catalog.scan_library(tmp);c['assets'][0]['mapping']={'id':'explicit'}
            merged=catalog.merge_assets(c,catalog.scan_library(tmp)['assets'])
            self.assertEqual(merged['assets'][0]['mapping']['id'],'explicit')

    def test_rollback_and_namespace(self):
        with tempfile.TemporaryDirectory() as tmp:
            kit=Path(tmp)/'kit';cache=Path(tmp)/'cache';p=kit/'tags/levels/multi/hb_test/saved.tag'
            p.parent.mkdir(parents=True);p.write_bytes(b'previous');stock=kit/'tags/stock.tag';stock.write_bytes(b'stock')
            with self.assertRaises(RuntimeError):
                with build.project_transaction(kit,'hb_test',cache):
                    p.write_bytes(b'bad');(p.parent/'new.tag').write_bytes(b'new');raise RuntimeError('compiler failure')
            self.assertEqual(p.read_bytes(),b'previous');self.assertEqual(stock.read_bytes(),b'stock')
            self.assertFalse((p.parent/'new.tag').exists());self.assertFalse((kit/'halo_bridge.build.lock').exists())

    @unittest.skipUnless(sys.platform=='win32','Windows process cancellation')
    def test_cancellation(self):
        with tempfile.TemporaryDirectory() as tmp:
            cancel=threading.Event();cancel.set()
            with self.assertRaises(jobs.Cancelled):jobs.run_process([sys.executable,'-c','import time;time.sleep(10)'],Path(tmp)/'log',cancel=cancel)

    def test_error_even_with_zero_exit(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(RuntimeError):jobs.run_process([sys.executable,'-c','print("-ERROR- test failure")'],Path(tmp)/'log')

    def test_index_routes_and_identity(self):
        rows=[dict(name='tree',tag='levels\\bsp',section=4,kind='instance'),dict(name='tree',tag='levels\\bsp',section=5,kind='instance'),dict(name='ground',tag='shaders\\ground',section=-1,kind='material')]
        assets=catalog.indexed_assets(dict(map='010_jungle.map',assets=rows))
        self.assertEqual(len(set(a['id'] for a in assets)),3)
        self.assertEqual(assets[-1]['category'],'Materials')

if __name__=='__main__':unittest.main()
