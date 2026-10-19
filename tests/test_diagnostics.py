import unittest
from halo_bridge.diagnostics import ValidationError, compiler_errors

class DiagnosticTests(unittest.TestCase):
    def test_all_issues_are_kept(self):
        error=ValidationError(['object '+str(i) for i in range(40)])
        self.assertEqual(len(error.issues),40)
        self.assertIn('40. object 39',str(error))

    def test_early_compiler_errors_are_not_lost_in_progress_output(self):
        text='-ERROR- missing terrain\n'+'progress\n'*500+'-ERROR- missing shader\n-ERROR- missing terrain\n'
        self.assertEqual(compiler_errors(text),['-ERROR- missing terrain','-ERROR- missing shader'])
