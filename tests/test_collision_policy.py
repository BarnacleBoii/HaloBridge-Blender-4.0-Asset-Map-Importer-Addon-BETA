import sys,unittest
from pathlib import Path
from types import SimpleNamespace
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from halo_bridge import collision_policy
from halo_bridge.diagnostics import geometry_warnings

class CollisionPolicyTests(unittest.TestCase):
    def test_foliage_and_explicit_choices(self):
        mat=SimpleNamespace(hb_collision_mode='AUTO',ass_jms=SimpleNamespace(render_only=False))
        self.assertTrue(collision_policy.render_only(mat,'leaves.shader_foliage'))
        self.assertFalse(collision_policy.render_only(mat,'glass.shader'))
        self.assertFalse(collision_policy.render_only(mat,'tree_leafc.shader'))
        self.assertTrue(collision_policy.render_only(mat,'cit_tree_leafc.shader',r'levels\solo\100_citadel\shaders\cit_tree_leafc'))
        # Per-material collision settings from older versions no longer change anything.
        mat.hb_collision_mode='SOLID';self.assertTrue(collision_policy.render_only(mat,'leaves.shader_foliage'))
        mat.hb_collision_mode='RENDER_ONLY';self.assertFalse(collision_policy.render_only(mat,'tree_leafc.shader'))
        mat.hb_collision_mode='AUTO';mat.ass_jms.render_only=True
        self.assertTrue(collision_policy.render_only(mat,'anything.shader'))

    def test_warning_names_and_deduplication(self):
        text='WARNING (poop hb_0.001) overlapping surfaces\rWARNING (poop hb_0.001) overlapping surfaces\nWARNING rasterizer: leaking textures\nWARNING (poop hb_1) duplicate triangle'
        self.assertEqual(geometry_warnings(text,{'hb_0':'pine','hb_1':'rock'}),['WARNING (object pine) overlapping surfaces','WARNING (object rock) duplicate triangle'])

if __name__=='__main__':unittest.main()
