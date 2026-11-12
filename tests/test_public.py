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
            home=Path(tmp);p=home/'Roaming/Osoyoos/Settings.JSON'
            p.parent.mkdir(parents=True);p.write_text('{broken')
            with patch.object(Path,'home',return_value=home),patch.dict(os.environ,{'APPDATA':str(home/'Roaming')}),\
                 patch.object(catalog,'documents_folder',return_value=home/'OneDrive/Documents'):
                result=catalog.detect_paths()
            # Redirected (OneDrive) Documents folders are used for new storage.
            self.assertEqual(result['cache'],str(home/'OneDrive/Documents/HaloBridge'))
            self.assertNotIn('library',result)

    def test_existing_storage_is_kept(self):
        with tempfile.TemporaryDirectory() as tmp:
            home=Path(tmp);(home/'Documents/HaloBridge').mkdir(parents=True)
            with patch.object(Path,'home',return_value=home),patch.object(catalog,'documents_folder',return_value=home/'OneDrive/Documents'):
                self.assertEqual(catalog.default_storage(),home/'Documents/HaloBridge')
                self.assertEqual(catalog.default_storage('reach'),home/'Documents/HaloBridge/reach')

    def test_documents_folder_resolves(self):
        folder=catalog.documents_folder()
        self.assertTrue(folder.is_absolute())
        if os.name=='nt':self.assertTrue(folder.is_dir())

    def test_kits_and_maps_in_any_library(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);common=root/'Games/steamapps/common'
            (common/'H3EK').mkdir(parents=True);(common/'H3EK/tool.exe').write_bytes(b'')
            maps=common/'Halo The Master Chief Collection/halo3/maps';maps.mkdir(parents=True);(maps/'010_jungle.map').write_bytes(b'')
            h2=common/'Halo The Master Chief Collection/halo2/h2_maps_win64_dx11';h2.mkdir(parents=True);(h2/'ascension.map').write_bytes(b'')
            with patch.object(setup,'steam_libraries',return_value=[root/'Games']),patch.object(catalog,'fixed_drives',return_value=[]),\
                 patch.dict(os.environ,{'APPDATA':tmp}):
                result=catalog.detect_paths('halo3')
                self.assertEqual(result['kit'],str(common/'H3EK'));self.assertEqual(result['maps'],str(maps))
                self.assertEqual(catalog.detect_paths('halo2')['maps'],str(h2))

    def test_xbox_app_mcc_maps(self):
        with tempfile.TemporaryDirectory() as tmp:
            drive=Path(tmp);maps=drive/'XboxGames/Halo The Master Chief Collection/Content/halo3/maps'
            maps.mkdir(parents=True);(maps/'guardian.map').write_bytes(b'')
            with patch.object(setup,'steam_libraries',return_value=[]),patch.object(catalog,'fixed_drives',return_value=[drive]),\
                 patch.dict(os.environ,{'APPDATA':tmp,'PROGRAMFILES(X86)':tmp}):
                self.assertEqual(catalog.detect_paths('halo3')['maps'],str(maps))

if __name__=='__main__':unittest.main()
