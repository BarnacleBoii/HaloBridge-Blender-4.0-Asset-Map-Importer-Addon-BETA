import importlib.util
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from halo_bridge import setup,catalog
spec=importlib.util.spec_from_file_location('release_package',ROOT/'scripts/package.py')
package=importlib.util.module_from_spec(spec);spec.loader.exec_module(package)

class PublicTests(unittest.TestCase):
    def test_release_rejects_private_content(self):
        for name in ('example.map','scene.blend','catalogue.json','ManagedBlam.dll','xcompress64.dll'):
            with self.assertRaises(ValueError):package.audit(name,b'fixture')
        with self.assertRaises(ValueError):package.audit('sample.cs',str(Path.home()).encode())
        package.audit('sample.py',b'value=1')

    def test_custom_steam_library(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);steam=root/'Steam';custom=root/'Other Library'
            (steam/'steamapps').mkdir(parents=True)
            encoded=str(custom).replace('\\','\\\\')
            (steam/'steamapps/libraryfolders.vdf').write_text('"libraryfolders" { "1" { "path" "'+encoded+'" } }')
            with patch.dict(os.environ,{'PROGRAMFILES(X86)':tmp}):
                self.assertIn(custom,setup.steam_libraries())

    def test_missing_requirements_are_actionable(self):
        with tempfile.TemporaryDirectory() as tmp,patch.object(setup,'runtime_check',return_value=False):
            issues=setup.check({'kit':tmp,'maps':tmp},Path(tmp))
            self.assertTrue(any('Desktop Runtime' in x for x in issues))
            self.assertTrue(any('release add-on ZIP' in x for x in issues))
            self.assertTrue(any('tag archives' in x for x in issues))

    def test_broken_optional_osoyoos_settings(self):
        with tempfile.TemporaryDirectory() as tmp:
            home=Path(tmp);p=home/'AppData/Roaming/Osoyoos/Settings.JSON'
            p.parent.mkdir(parents=True);p.write_text('{broken')
            with patch.object(Path,'home',return_value=home):
                result=catalog.detect_paths()
            self.assertEqual(result['cache'],str(home/'Documents/HaloBridge'))
            self.assertNotIn('library',result)

if __name__=='__main__':unittest.main()
