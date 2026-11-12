"""Editing Kit scenario import: source parsing and manifest building, without Blender."""
import json
import math
import sys
import tempfile
import unittest
import zlib
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from halo_bridge import scenario_scene, source_formats as sf
from halo_bridge.catalog import read_json

ASS = '''7
"MAX"
"8"
"artist"
"machine"
3
"stone"
"COL biped"
2
"BM_FLAGS 1000100000000000000000"
"BM_LMRES 1.0000000000 1 0 0 0 0 0 0 0 0 0"
"shr metal"
""
0
"+portal"
""
0
2
"MESH"
""
""
4
0 0 0
0 0 1
1 1 1
0
1
0 0 0
100 0 0
0 0 1
1 1 1
0
1
1 0 0
100 100 0
0 0 1
1 1 1
0
1
1 1 0
0 100 0
0 0 1
1 1 1
0
1
0 1 0
3
0 0 1 2
2 0 2 3
0 1 1 2 ; degenerate, dropped
"MESH"
""
""
3
0 0 0
0 0 1
1 1 1
1
3 1.0
1
0 0 0
10 0 0
0 0 1
1 1 1
1
3 1.0
1
1 0 0
0 10 0
0 0 1
1 1 1
1
3 1.0
1
0 1 0
1
1 0 1 2
4
-1
"Scene Root"
-1
-1
0
0 0 0 1
0 0 0
1
0 0 0 1
0 0 0
1
0
"level"
1
0
0
0 0 0 1
0 0 0
1
0 0 0 1
0 0 0
1
1
"%rock"
2
0
0
0 0 0.7071068 0.7071068
500 0 0
2
0 0 0 1
0 0 0
1
3
1
"%rock"
3
0
0
0 0 0 1
-500 0 0
1
0 0 0 1
0 0 0
1
3
'''

JMS = '''8213
1
"frame"
-1
0 0 0 1
0 0 0
4
"metal"
"(1) default base"
"glass%"
"(2) damaged base"
"metal"
"(3) L1 default base"
"metal"
"(4) L5 default base"
0
0
0
4
0 0 0
0 0 1
0
1
0 0
0 0 0
100 0 0
0 0 1
0
1
1 0
0 0 0
0 100 0
0 0 1
0
1
0 1
0 0 0
100 100 0
0 0 1
0
1
1 1
0 0 0
4
0 0 1 2
1 1 3 2
2 0 1 3
3 0 3 2
0
0
0
0
0
0
'''


def blob(folder, name, text):
    raw = text.encode()
    (folder / name).write_bytes(zlib.compress(raw))
    return dict(source_path='data\\' + name + ('.ass' if 'bsp' in name else '.jms'), compressed=name,
                size=len(raw), crc32=zlib.crc32(raw) ^ 0xffffffff)


def tags_json(folder):
    bsp = blob(folder, 'bsp_0-0', ASS)
    bsp['source_path'] = 'data\\levels\\multi\\test\\structure\\test.ASS'
    model = blob(folder, 'object_0-0', JMS)
    model['source_path'] = 'data\\objects\\crate\\render\\default.JMS'
    variants = [dict(name='broken', blocks=dict(regions=[dict(name='base', blocks=dict(permutations=[dict(name='damaged', blocks={})]))])),
                dict(name='default', blocks=dict(regions=[dict(name='base', blocks=dict(permutations=[dict(name='default', blocks={})]))]))]
    objects = {'objects\\crate\\crate.scenery': dict(tag='objects\\crate\\crate', model='objects\\crate\\crate', render_model='objects\\crate\\crate',
                                                     collision_model='objects\\crate\\crate', sources=[model],
                                                     shaders=['objects\\crate\\shaders\\metal', 'objects\\crate\\shaders\\glass'], variants=variants),
               'objects\\gun\\gun.weapon': dict(tag='objects\\gun\\gun', model='', render_model='', sources=[], shaders=[], variants=[])}
    placements = [dict(category='Scenery', index=0, name='crate_a', object_tag='objects\\crate\\crate.scenery', variant='',
                       position=[1, 2, 3], rotation=[90, 0, 0], scale=0),
                  dict(category='Scenery', index=1, name='', object_tag='objects\\crate\\crate.scenery', variant='broken',
                       position=[0, 0, 0], rotation=[0, 0, 0], scale=2),
                  dict(category='Weapons', index=0, name='', object_tag='objects\\gun\\gun.weapon', variant='',
                       position=[0, 0, 0], rotation=[0, 0, 0], scale=1)]
    return dict(version=1, kind='halo3_scenario_tags', scenario='levels\\multi\\test\\test',
                bsps=[dict(index=0, tag='levels\\multi\\test\\test', sources=[bsp], shaders=['levels\\multi\\test\\shaders\\stone', 'levels\\shared\\metal'])],
                objects=objects, placements=placements, skies=[], counts=dict(Scenery=2, Weapons=1), warnings=[])


class SourceFormatTests(unittest.TestCase):
    def test_ass_instances_share_objects_and_compose_transforms(self):
        ass = sf.parse_ass(ASS)
        self.assertEqual(ass['version'], 7)
        self.assertEqual([m['name'] for m in ass['materials']], ['stone', 'shr metal', '+portal'])
        self.assertEqual(len(ass['objects'][0]['triangles']), 3)
        self.assertEqual(ass['objects'][1]['nodes'], [3])
        matrices = sf.ass_world_matrices(ass)
        rotated = matrices[2]
        point = [sum(rotated[r][c] * v for c, v in enumerate((10, 0, 0, 1))) for r in range(3)]
        # Quarter turn about Z, scale 2, then moved 500 along X.
        for got, want in zip(point, (500, 20, 0)):
            self.assertAlmostEqual(got, want, places=3)

    def test_material_flags_from_names_and_bm_flags(self):
        self.assertEqual(sf.split_material_name('stone%!'), ('stone', '%!'))
        self.assertEqual(sf.split_material_name('+portal'), ('+portal', ''))
        # Halo 3 lighting parameters trail the shader name (real Guardian names).
        self.assertEqual(sf.split_material_name('guardian guardian_floor_a lm:5.0'), ('guardian guardian_floor_a', ''))
        self.assertEqual(sf.split_material_name('guardian guardian_tree_a_blend% lm:0.005 lp:2'), ('guardian guardian_tree_a_blend', '%'))
        self.assertIn('two_sided', sf.material_flags('guardian guardian_tree_a_blend% lm:0.005'))
        # Unbalanced trailing ")" in shipped weapon JMS names is not part of the shader name.
        self.assertEqual(sf.split_material_name('display=?)'), ('display', '=?'))
        self.assertEqual(sf.split_material_name('assault_rifle)'), ('assault_rifle', ''))
        self.assertEqual(sf.split_material_name('panel (old)'), ('panel (old)', ''))
        self.assertEqual(sf.split_material_name('blur)!='), ('blur', '!='))
        self.assertEqual(sf.split_material_name("'water_030"), ('water_030', ''))
        self.assertEqual(sf.split_material_name('voi rubber_wire !'), ('voi rubber_wire', '!'))
        # ASS names are whole quoted lines, even with an embedded quote.
        self.assertEqual(sf.Reader('"%"-?bridge"\n7\n').line(), '%"-?bridge')
        flags = sf.material_flags('stone', ['BM_FLAGS 1000100000000000000000'])
        self.assertEqual(flags, ['collision_only', 'two_sided'])
        self.assertIn('render_only', sf.material_flags('leaf!'))

    def test_jms_variant_and_lod_selection(self):
        jms = sf.parse_jms(JMS, default_permutation='default')
        self.assertEqual([(m['lod'], m['permutation'], m['region']) for m in jms['materials']],
                         [('', 'default', 'base'), ('', 'damaged', 'base'), ('l1', 'default', 'base'), ('l5', 'default', 'base')])
        default, report = sf.select_render_triangles(jms, {})
        self.assertEqual([t[0] for t in default], [0, 3])
        self.assertEqual(report[0]['selected'], ['default'])
        damaged, _ = sf.select_render_triangles(jms, {'BASE': 'Damaged'})
        self.assertEqual([t[0] for t in damaged], [1])
        # Faces with no material (-1), as in 070_waste's sky source, are skipped, not fatal.
        unassigned = dict(jms, triangles=jms['triangles'] + [(-1, 0, 1, 2), (99, 0, 1, 2)])
        self.assertEqual(sf.unassigned_triangles(unassigned), 2)
        kept, _ = sf.select_render_triangles(unassigned, {})
        self.assertEqual([t[0] for t in kept], [0, 3])

    def test_jms_unquoted_names_with_spaces(self):
        # Tool writes JMS strings as whole unquoted lines; names and definitions contain spaces.
        text = '\n'.join([
            ';### VERSION ###', '8213', ';### NODES ###', '1', ';NODE 0', 'frame my box', '-1',
            '0 0 0 1', '0 0 0', ';### MATERIALS ###', '2', ';MATERIAL 0', 'panel metal%', '(1) L1 broken base',
            ';MATERIAL 1', 'panel metal%', '(2) default base', ';### MARKERS ###', '1', 'hinge top', '0', '0 0 0 1', '0 0 0', '1',
            ';### INSTANCE XREF PATHS ###', '0', ';### INSTANCE MARKERS ###', '0', ';### VERTICES ###', '3'] +
            sum([[p, '0 0 1', '1', '0', '1', '1', '0 0', '0 0 0'] for p in ('0 0 0', '1 0 0', '0 1 0')], []) +
            [';### TRIANGLES ###', '2', '0', '0 1 2', '1', '0 2 1'])
        jms = sf.parse_jms(text)
        self.assertEqual(jms['nodes'][0]['name'], 'frame my box')
        self.assertEqual([m['name'] for m in jms['materials']], ['panel metal%', 'panel metal%'])
        self.assertEqual([(m['lod'], m['permutation'], m['region']) for m in jms['materials']],
                         [('l1', 'broken', 'base'), ('', 'default', 'base')])
        self.assertEqual(len(jms['positions']), 3)
        self.assertEqual(jms['triangles'], [(0, 0, 1, 2), (1, 0, 2, 1)])

    def test_euler_matches_reclaimer_order(self):
        # Reclaimer: q = Rx(roll) * R(-Y)(pitch) * Rz(yaw), applied to column vectors.
        yaw, pitch, roll = 30, 20, 10
        m = sf.euler_matrix(yaw, pitch, roll, (0, 0, 0), 1)
        def axis(ax, angle):
            a = math.radians(angle) / 2
            return (math.cos(a), *(math.sin(a) * v for v in ax))
        def qmul(a, b):
            w1, x1, y1, z1 = a; w2, x2, y2, z2 = b
            return (w1*w2 - x1*x2 - y1*y2 - z1*z2, w1*x2 + x1*w2 + y1*z2 - z1*y2,
                    w1*y2 - x1*z2 + y1*w2 + z1*x2, w1*z2 + x1*y2 - y1*x2 + z1*w2)
        q = qmul(qmul(axis((1, 0, 0), roll), axis((0, -1, 0), pitch)), axis((0, 0, 1), yaw))
        expected = sf.compose((q[1], q[2], q[3], q[0]), (0, 0, 0), 1)
        for r in range(3):
            for c in range(3):
                self.assertAlmostEqual(m[r][c], expected[r][c], places=6)

    def test_mesh_record_drops_degenerates_and_converts_units(self):
        ass = sf.parse_ass(ASS)
        item = ass['objects'][0]
        record, dropped = sf.mesh_record(item['positions'], item['normals'], item['uvs'], item['triangles'], [7, 8, 9])
        self.assertEqual(dropped, 1)
        self.assertEqual(record['positions'][1], [1.0, 0.0, 0.0])
        self.assertEqual({s['material'] for s in record['segments']}, {7, 9})

    def test_truncated_and_unsupported_sources_are_rejected(self):
        with self.assertRaises(sf.SourceError):
            sf.parse_ass('7\n"MAX"\n')
        with self.assertRaises(sf.SourceError):
            sf.parse_jms('8200\n')


class ScenarioBuildTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.kit = self.root / 'kit'
        (self.kit / 'tags/levels/multi/test').mkdir(parents=True)
        (self.kit / 'tags/levels/multi/test/test.scenario').write_bytes(b'tag')
        (self.kit / 'tags/levels/shader_collections.txt').write_text('shr levels\\shared\n')
        self.config = dict(kit=str(self.kit), cache=str(self.root / 'cache'), maps='')

    def tearDown(self):
        self.tmp.cleanup()

    def test_shader_collection_shaders_subfolder(self):
        # H3EK level collections keep shaders in <folder>\shaders (guardian -> levels\multi\guardian\shaders).
        (self.kit / 'tags/levels/shader_collections.txt').write_text('shr levels\\shared\nlvl levels\\multi\\test\n')
        shader = self.kit / 'tags/levels/multi/test/shaders/floor_a.shader'
        shader.parent.mkdir(parents=True); shader.write_bytes(b'tag')
        materials = scenario_scene.Materials(self.config['kit'])
        on_disk = materials.get('lvl floor_a lm:5.0', [])
        referenced = materials.get('lvl wall_b', ['levels\\multi\\test\\shaders\\wall_b'])
        metas = {m['id']: m for m in materials.metas()}
        self.assertEqual(metas[on_disk]['shader'], 'levels\\multi\\test\\shaders\\floor_a')
        self.assertEqual(metas[referenced]['shader'], 'levels\\multi\\test\\shaders\\wall_b')
        self.assertFalse(materials.unresolved)
        # Ambiguous leaf names resolve to the copy inside the named collection.
        (self.kit / 'tags/levels/shader_collections.txt').write_text('voi levels\\solo\\040_voi\n')
        materials = scenario_scene.Materials(self.config['kit'])
        wire = materials.get('voi rubber_wire !', ['levels\\solo\\020_base\\shaders\\rubber_wire', 'levels\\solo\\040_voi\\shaders\\plastic\\rubber_wire'])
        self.assertEqual(materials.metas()[wire]['shader'], 'levels\\solo\\040_voi\\shaders\\plastic\\rubber_wire')

    def test_build_layout_materials_and_variants(self):
        folder = self.root / 'work'; folder.mkdir()
        data = tags_json(folder)
        result = scenario_scene.build(self.config, data['scenario'], data, folder)
        self.assertEqual(result['decoded'], 1)
        groups = [p['group'] for p in result['placements']]
        self.assertEqual(groups.count('Structure'), 1)
        self.assertEqual(groups.count('BSP instances'), 2)
        self.assertEqual(groups.count('Special surfaces'), 1)
        self.assertEqual(groups.count('Scenery'), 2)
        rocks = [p for p in result['placements'] if p['group'] == 'BSP instances']
        self.assertEqual(rocks[0]['mesh'], rocks[1]['mesh'])
        metas = {m['source_name']: m for m in result['materials'].metas()}
        self.assertEqual(metas['stone']['shader'], 'levels\\multi\\test\\shaders\\stone')
        self.assertEqual(metas['shr metal']['shader'], 'levels\\shared\\metal')
        self.assertTrue(metas['+portal']['special'])
        self.assertIn('collision_only', metas['stone']['flags'])
        crates = [p for p in result['placements'] if p['group'] == 'Scenery']
        self.assertNotEqual(crates[0]['mesh'], crates[1]['mesh'])
        self.assertEqual(crates[1]['variant'], 'broken')
        self.assertEqual(crates[1]['selection'][0]['selected'], ['damaged'])
        # Position is converted to 100x working units; zero scale means 1.
        self.assertAlmostEqual(crates[0]['matrix'][0][3], 100)
        self.assertAlmostEqual(crates[0]['matrix'][2][3], 300)
        self.assertAlmostEqual(crates[0]['matrix'][1][0], 1, places=6)
        self.assertTrue(any('gun' in w for w in result['warnings']))
        mesh = read_json(folder / result['meshes'][crates[0]['mesh']])
        self.assertEqual(mesh['materials'][0]['shader'], 'objects\\crate\\shaders\\metal')

    def test_extract_end_to_end_with_textures_and_cache(self):
        maps = self.root / 'maps'; maps.mkdir()
        (maps / 'test.map').write_bytes(b'map')
        self.config['maps'] = str(maps)
        calls = []

        def helper(kind, job, directory, cancel=None):
            calls.append((kind, job['operation']))
            out = Path(job['output'])
            if job['operation'] == 'scenario_scene':
                (out.parent / 'tags.json').write_text(json.dumps(tags_json(out.parent)))
            elif job['operation'] == 'materials':
                self.assertIn('levels\\multi\\test\\shaders\\stone', job['tags'])
                (out / 'texture_1.png').write_bytes(b'png')
                (out / 'materials.json').write_text(json.dumps(dict(materials={'LEVELS\\multi\\test\\shaders\\stone': dict(
                    textures=[dict(usage='diffuse', path='texture_1.png', tiling=[1, 1])], alpha='opaque', source_game='halo3')})))
            return None

        with patch('halo_bridge.scenario_scene.jobs.helper', side_effect=helper):
            manifest = scenario_scene.extract(self.config, 'levels/multi/test/test')
            data = read_json(manifest)
            self.assertEqual(data['kind'], scenario_scene.KIND)
            self.assertEqual(data['decoded_bsps'], data['expected_bsps'])
            stone = [m for f in data['meshes'].values() for m in read_json(manifest.parent / f)['materials'] if m['source_name'] == 'stone']
            self.assertTrue(stone and all(m['textures'] for m in stone))
            self.assertFalse(list(manifest.parent.glob('*.zlib')))
            self.assertIn('Editing Kit scenario', scenario_scene.report(data))
            # Unchanged tags reuse the cached manifest without running helpers.
            before = len(calls)
            self.assertEqual(scenario_scene.extract(self.config, 'levels\\multi\\test\\test'), manifest)
            self.assertEqual(len(calls), before)
        self.assertEqual(calls[0], ('tags', 'scenario_scene'))

    def test_bad_checksum_is_reported_not_accepted(self):
        folder = self.root / 'work'; folder.mkdir()
        data = tags_json(folder)
        data['bsps'][0]['sources'][0]['crc32'] ^= 1
        result = scenario_scene.build(self.config, data['scenario'], data, folder)
        self.assertEqual(result['decoded'], 0)
        self.assertTrue(any('checksum' in w for w in result['warnings']))

    def test_unsafe_scenario_paths_are_rejected(self):
        for value in ('', '..\\x', 'C:\\x', 'a\\\\b'):
            with self.assertRaises(RuntimeError):
                scenario_scene.safe_tag(value)
        self.assertEqual(scenario_scene.safe_tag('levels/multi/a/a.scenario'), 'levels\\multi\\a\\a')

    def test_scenarios_lists_kit_levels(self):
        self.assertEqual(scenario_scene.scenarios(self.kit), ['levels\\multi\\test\\test'])


if __name__ == '__main__':
    unittest.main()
