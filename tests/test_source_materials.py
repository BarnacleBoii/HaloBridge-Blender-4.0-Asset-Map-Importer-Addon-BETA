import unittest
from unittest.mock import patch
from halo_bridge.source_materials import resolve


class SourceMaterialsTests(unittest.TestCase):
    def fixture(self, name='stone'):
        return '7\n"MAX"\n"8"\n"artist"\n"machine"\n1\n"'+name+'"\n"COL biped"\n1\n"BM_FLAGS 0010"\n; geometry unchanged\n123\n'

    def test_exact_reference_and_preserved_geometry_flags(self):
        with patch('halo_bridge.source_materials.material_name', return_value='shr stone') as mapper:
            result, changes = resolve(self.fixture('stone*'), 'kit', ['levels/shrine/stone'])
        mapper.assert_called_once_with('kit', 'levels/shrine/stone')
        self.assertEqual(result,self.fixture('shr stone*'))
        self.assertEqual(len(changes),1)

    def test_ambiguous_and_missing_refs_are_rejected(self):
        for shaders in ([], ['a/stone','b/stone']):
            with self.assertRaisesRegex(RuntimeError,'no unique'):
                resolve(self.fixture(),'kit',shaders)

    def test_special_materials_and_existing_prefix_are_preserved(self):
        for name in ('+portal1','shr stone'):
            self.assertEqual(resolve(self.fixture(name),'kit',[]),(self.fixture(name),[]))

    def test_truncated_material_table_is_rejected(self):
        with self.assertRaises(RuntimeError): resolve('7\n','kit',[])
