"""Apply material adds a slot, level-name placeholder, .map/.scenario filter, view distance, game table."""
import json, sys, tempfile
from pathlib import Path
from types import SimpleNamespace
import bpy
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import halo_bridge
halo_bridge.register()
from halo_bridge import ui, compat, games, blender_ops, scenario_scene
from halo_bridge.catalog import safe_level, write_json

# Apply material: a new slot is added and assigned; the old material stays on the object.
bpy.ops.mesh.primitive_cube_add()
cube = bpy.context.active_object
old = bpy.data.materials.new('old'); new = bpy.data.materials.new('new')
cube.data.materials.append(old)
index = blender_ops.add_material(cube, new)
assert [m.name for m in cube.data.materials] == ['old', 'new'] and index == 1
assert all(p.material_index == 1 for p in cube.data.polygons) and cube.active_material_index == 1
assert blender_ops.add_material(cube, new) == 1 and len(cube.data.materials) == 2, 'reuses the existing slot'
# Edit Mode: only the selected faces change.
bpy.ops.object.mode_set(mode='EDIT')
import bmesh
bm = bmesh.from_edit_mesh(cube.data)
for face in bm.faces:
    face.select = face.index == 0
bmesh.update_edit_mesh(cube.data)
third = bpy.data.materials.new('third')
assert blender_ops.add_material(cube, third) == 2
bpy.ops.object.mode_set(mode='OBJECT')
assert [p.material_index for p in cube.data.polygons] == [2, 1, 1, 1, 1, 1]

# Output level name: a valid default; the old placeholder is still refused in older scenes.
s = bpy.context.scene.halo_bridge
assert s.level == 'levelname123' and safe_level(s.level) == 'levelname123'
try:
    safe_level('Level_Name_Here')
    raise AssertionError('old placeholder accepted')
except ValueError as error:
    assert 'Level_Name_Here' in str(error)
assert safe_level('my_level') == 'my_level'

# Collision: Object collision default label; the per-material control is gone.
items = {i.identifier: i.name for i in bpy.types.Object.bl_rna.properties['hb_static_collision'].enum_items}
assert items['AUTO'] == '(Default) Automatic'

# View distance in displayed units: HaloBridge scenes use a unit scale of 0.03048.
assert compat.clear_view_fog(bpy.data.screens, unit_scale=0.03048) >= 0
for screen in bpy.data.screens:
    for area in screen.areas:
        if area.type == 'VIEW_3D':
            space = area.spaces.active
            assert abs(space.clip_start * 0.03048 - 0.1) < 1e-6 and abs(space.clip_end * 0.03048 - 999999.0) < 1.0, (space.clip_start, space.clip_end)
assert compat.clear_view_fog(bpy.data.screens) >= 0
for screen in bpy.data.screens:
    for area in screen.areas:
        if area.type == 'VIEW_3D':
            assert area.spaces.active.clip_end == 999999.0 and abs(area.spaces.active.clip_start - 0.1) < 1e-6
assert dict((k, label) for k, label, _ in games.IMPORT_ITEMS)['reach'] == 'Halo: Reach'

# Games: ODST imports, indexes scenarios and prepares; Reach imports scenarios but cannot prepare.
assert games.GAMES['odst']['import_enabled'] and games.GAMES['odst']['sapien_enabled'] and games.GAMES['odst']['scenario_enabled']
assert games.GAMES['reach']['scenario_enabled'] and not games.GAMES['reach']['sapien_enabled']
assert [k for k, *_ in games.SAPIEN_ITEMS] == ['halo3', 'odst', 'reach']
assert 'odst' in [k for k, *_ in games.IMPORT_ITEMS]

# .scenario index rows from a small manifest, and the source filter.
with tempfile.TemporaryDirectory() as folder:
    root = Path(folder) / 'scenario_scenes' / 'x' / 'scene_1'
    root.mkdir(parents=True)
    meta = dict(id=0, name='rock', shader='levels\\test\\shaders\\rock', alpha='opaque', textures=[], flags=[])
    for name in ('object_a.json', 'bsp0_0_1_geometry.json'):
        write_json(root / name, dict(version=1, materials=[meta], meshes=[]))
    write_json(root / 'scene.json', dict(version=scenario_scene.VERSION, kind=scenario_scene.KIND, game='odst',
                                         scenario='levels\\test\\test', meshes={'object_a': 'object_a.json', 'bsp0_0_1_geometry': 'bsp0_0_1_geometry.json'},
                                         placements=[
                                             dict(name='rock #0', mesh='object_a', group='Scenery', object_tag='objects\\rock\\rock.scenery', variant=''),
                                             dict(name='rock #1', mesh='object_a', group='Scenery', object_tag='objects\\rock\\rock.scenery', variant=''),
                                             dict(name='test / %boulder', mesh='bsp0_0_1_geometry', group='BSP instances', source_tag='levels\\test\\test'),
                                             dict(name='test / floor', mesh='bsp0_0_1_geometry', group='Structure', source_tag='levels\\test\\test')]))
    rows = scenario_scene.index_assets(root / 'scene.json', dict(kit=folder, game='odst'))
    kinds = sorted(r['kind'] for r in rows)
    assert kinds == ['instance', 'material', 'scenery'], kinds
    scenery = next(r for r in rows if r['kind'] == 'scenery')
    assert scenery['scenery_tag'] == 'objects\\rock\\rock' and scenery['game'] == 'odst' and scenery['source'] == 'scenario'
    assert next(r for r in rows if r['kind'] == 'instance')['name'] == 'boulder'
    material = next(r for r in rows if r['kind'] == 'material')
    assert Path(material['path']).is_file() and json.loads(Path(material['path']).read_text())['materials'][0]['shader'] == meta['shader']
    assert scenario_scene.asset_path(scenery, dict(kit=folder)) == Path(scenery['path'])

    ui._catalogue = {'version': 1, 'assets': [dict(id='m1', name='tree', level='test', category='Vegetation', kind='scenery'),
                                             dict(rows[0], id='s1')]}
    s.cache = folder
    ui.refresh(bpy.context, persist=False)
    def shown():
        return sorted(a.asset_id for a in s.assets if ui.visibility_predicate(s)(a))
    s.filter_source = 'ALL'; assert shown() == ['m1', 's1']
    s.filter_source = 'MAP'; assert shown() == ['m1']
    s.filter_source = 'SCENARIO'; assert shown() == ['s1']
    s.filter_source = 'ALL'

# Panel: section names and the summaries draw.
drawn = []
class Layout:
    def __getattr__(self, name):
        return lambda *a, **kw: self
    def label(self, **kw): drawn.append(kw.get('text'))
    def operator(self, name, **kw): drawn.append(name); return SimpleNamespace()
compat.section = lambda layout, idname, title, icon='NONE', default_closed=False: (layout, layout if drawn.append(title) is None else None)
s.game = 'odst'
assert s.export_target == 'odst' and s.scenario_path == games.GAMES['odst']['scenario']
ui.HBPanel.draw(SimpleNamespace(layout=Layout()), SimpleNamespace(scene=bpy.context.scene, region=SimpleNamespace(width=340), active_object=cube))
assert 'Shaders' in drawn and 'Materials and Shaders' not in drawn
assert 'halo_bridge.index_scenario' in drawn and 'halo_bridge.index' in drawn
assert drawn.index('halo_bridge.import_scenario') < drawn.index('halo_bridge.import_map_scene')
assert any(t and t.startswith('.map assets:') for t in drawn) and any(t and t.startswith('.scenario assets:') for t in drawn)
assert 'Shared materials affect all objects using them.' not in drawn
assert 'Filter by level / category' not in drawn and not any(t and 'in this category' in t for t in drawn)
halo_bridge.unregister()
print('PASS apply material adds a slot, level placeholder, view distance 999999, ODST/Reach game table, .scenario index rows and source filter, panel labels')
