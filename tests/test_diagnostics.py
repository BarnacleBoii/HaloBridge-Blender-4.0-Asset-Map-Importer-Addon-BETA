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

    def test_test_lighting_shader_assertion_is_recognised(self):
        from halo_bridge import build
        issues=['-FATAL-','-FATAL- ### ASSERTION FAILED:  at c:\\mcc\\release\\h3\\source\\tool\\faux\\faux_material.cpp,#1170','-FATAL-   parameter_success']
        self.assertTrue(build.faux_shader_failure(issues))
        self.assertFalse(build.faux_shader_failure(['-ERROR- plane builder unable to converge']))
        config={'shader_aliases':{r'levels\solo\070_waste\sky\waterfall\shaders\waterfall':{'name':'hb_a','source':r'X:\kit\tags\levels\solo\070_waste\sky\waterfall\shaders\waterfall.shader_custom'},
                                  r'levels\shared\shaders\rock':{'name':'hb_b','source':r'X:\kit\tags\levels\shared\shaders\rock.shader'}}}
        self.assertEqual(build.lighting_suspects(config),[r'levels\solo\070_waste\sky\waterfall\shaders\waterfall'])
