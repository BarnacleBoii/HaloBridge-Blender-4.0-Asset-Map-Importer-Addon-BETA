"""Keep scenery imported from an Editing Kit scenario as original scenery placements.

The scenario names each object's scenery tag, so no matching is needed: an
unedited object is written back as a placement of that exact tag, keeping its
model, collision, physics and variants. Edited objects export as static
geometry instead, like any other mesh.
"""
import math
import re
from pathlib import Path
from mathutils import Matrix
from . import blender_ops, games, invisible_blocks
from .diagnostics import ValidationError

_signatures = {}


def reset_cache():
    _signatures.clear()


def unchanged(obj):
    if obj.modifiers or not obj.get('hb_mesh_signature'):
        return False
    key = (obj.data.as_pointer(), len(obj.data.vertices), len(obj.data.polygons), obj.data.is_editmode)
    if key not in _signatures:
        _signatures[key] = blender_ops.mesh_signature(obj.data)
    return _signatures[key] == obj['hb_mesh_signature']


def candidate(obj):
    return (obj.type == 'MESH' and obj.get('hb_scenario_kind') == 'Scenery' and bool(obj.get('hb_scenery_tag'))
            and games.native(obj) and not obj.get('hb_preview')
            and (obj.get('hb_map_reference') or not obj.get('hb_ignore'))
            and not invisible_blocks.selected(obj))


def selected(obj):
    """True when this object is written as its original scenery tag."""
    return candidate(obj) and unchanged(obj)


def edited(scene):
    return [obj for obj in scene.objects if candidate(obj) and not unchanged(obj)]


def plan(scene, config):
    placements, issues, ids = [], [], set()
    root = Path(config['kit']) / 'tags'
    for obj in scene.objects:
        if not selected(obj):
            continue
        try:
            tag = obj['hb_scenery_tag'].replace('/', '\\')
            path = root / (tag + '.scenery')
            if not path.resolve().is_relative_to(root.resolve()) or not path.is_file():
                raise ValueError('Original scenery tag is missing: ' + tag)
            units = float(obj.get('hb_working_units', 100))
            if not math.isfinite(units) or units <= 0 or any(not math.isfinite(v) for row in obj.matrix_world for v in row):
                raise ValueError('Invalid transform.')
            loc, rot, scale = obj.matrix_world.decompose()
            if min(scale) <= 0 or max(scale) - min(scale) > 1e-4 * max(scale):
                raise ValueError('Original scenery requires positive uniform scale. Apply the scale or edit the mesh instead.')
            rebuilt = Matrix.LocRotScale(loc, rot, scale)
            if max(abs(obj.matrix_world[r][c] - rebuilt[r][c]) for r in range(4) for c in range(4)) > 1e-3:
                raise ValueError('Remove transform shear from this object.')
            identity = obj.get('hb_id', '')
            if not re.fullmatch(r'hb_[0-9a-f]{24}', identity) or identity in ids:
                identity = blender_ops.new_id(); obj['hb_id'] = identity
            ids.add(identity)
            euler = rot.to_euler('ZYX')
            placements.append(dict(id=identity, tag=tag, position=list(loc / units),
                                   rotation=[math.degrees(euler.z), -math.degrees(euler.y), math.degrees(euler.x)],
                                   scale=float(scale.x) / units))
        except (ValueError, KeyError, TypeError, OSError) as error:
            issues.append(obj.name + ': ' + str(error))
    if issues:
        raise ValidationError(issues, 'Original scenery validation')
    return placements
