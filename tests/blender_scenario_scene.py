"""Editing Kit scenario import inside Blender (synthetic tags; no game data).

Run: blender -b --factory-startup --python tests/blender_scenario_scene.py
"""
import json, math, sys, tempfile
from pathlib import Path
from unittest.mock import patch
import bpy
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from halo_bridge import scenario_scene, original_scenery, geometry_export
from test_scenario_scene import tags_json

for obj in list(bpy.context.scene.objects):
    bpy.data.objects.remove(obj, do_unlink=True)
with tempfile.TemporaryDirectory() as tmp:
    root = Path(tmp); kit = root / 'kit'
    (kit / 'tags/levels/multi/test').mkdir(parents=True)
    (kit / 'tags/levels/multi/test/test.scenario').write_bytes(b'tag')
    (kit / 'tags/objects/crate').mkdir(parents=True)
    (kit / 'tags/objects/crate/crate.scenery').write_bytes(b'tag')
    config = dict(kit=str(kit), cache=str(root / 'cache'), maps='')

    def helper(kind, job, directory, cancel=None):
        out = Path(job['output'])
        (out.parent / 'tags.json').write_text(json.dumps(tags_json(out.parent)))

    with patch('halo_bridge.scenario_scene.jobs.helper', side_effect=helper):
        manifest = scenario_scene.extract(config, 'levels\\multi\\test\\test')
    for _ in scenario_scene.import_scene(bpy.context, manifest):
        pass
    objects = [o for o in bpy.context.scene.objects if o.get('hb_scenario_manifest')]
    names = {o.name for o in objects}
    assert 'test / level' in names and len([o for o in objects if o.name.startswith('test / %rock')]) == 2
    rocks = [o for o in objects if o.name.startswith('test / %rock')]
    assert rocks[0].data == rocks[1].data, 'instanced geometry shares one mesh'
    # (10, 0, 0) source units, rotated 90 degrees, scale 2, moved 500 along X.
    rock = next(o for o in rocks if abs(o.matrix_world.translation.x - 500) < 1e-3)
    point = rock.matrix_world @ rock.data.vertices[1].co
    assert (point - __import__('mathutils').Vector((500, 20, 0))).length < 1e-3, point
    crate = next(o for o in objects if o.get('hb_scenario_kind') == 'Scenery' and o.name.startswith('crate_a'))
    assert abs(crate.matrix_world.translation.z - 300) < 1e-3 and abs(crate.matrix_world.to_scale().x - 100) < 1e-3
    special = next(o for o in objects if o.users_collection[0].name.startswith('Special surfaces'))
    assert special.get('hb_ignore') and not special.get('hb_map_reference')
    assert special not in geometry_export.objects(bpy.context.scene)
    stone = next(m for m in bpy.data.materials if m.get('hb_source_material') == 'stone')
    assert 'collision_only' in scenario_scene.material_flags(stone)
    # Unedited scenery stays scenery; editing the mesh turns it into static geometry.
    original_scenery.reset_cache()
    plan = original_scenery.plan(bpy.context.scene, config)
    first = next(p for p in plan if abs(p['position'][2] - 3) < 1e-4)
    assert abs(first['position'][0] - 1) < 1e-4 and abs(first['rotation'][0] - 90) < 1e-3 and abs(first['scale'] - 1) < 1e-4, first
    assert crate not in geometry_export.objects(bpy.context.scene)
    crate.data = crate.data.copy(); crate.data.vertices[0].co.x += 1
    original_scenery.reset_cache()
    assert crate in geometry_export.objects(bpy.context.scene)
    assert crate in original_scenery.edited(bpy.context.scene)
print('PASS scenario import layout, shared instances, special surfaces and original scenery routing')
