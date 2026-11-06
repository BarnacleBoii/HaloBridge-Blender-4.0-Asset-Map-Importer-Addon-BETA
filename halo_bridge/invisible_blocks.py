"""Preserve the verified Floodship invisible blocker as original scenery.

This is deliberately an exact source identity, not a name-based barrier guess.
"""
import math
import re
from pathlib import Path
from mathutils import Matrix, Vector
from . import blender_ops, jobs
from .catalog import read_json
from .diagnostics import ValidationError

TAG = r'objects\levels\solo\060_floodship\inviso_block\inviso_block'
_verified = set()


def selected(obj):
    return (obj.type == 'MESH' and obj.get('hb_game', 'halo3') == 'halo3'
            and obj.get('hb_source_tag', '').replace('/', '\\').lower() == TAG
            and not obj.get('hb_preview')
            and (obj.get('hb_map_reference') or not obj.get('hb_ignore')))


def plan(scene, config):
    objects = [obj for obj in scene.objects if selected(obj)]
    if not objects:
        return []
    directory = Path(config['cache']) / 'jobs'
    signature = tuple((str(path.resolve()), path.stat().st_mtime_ns, path.stat().st_size)
                      for extension in ('.scenery', '.model', '.render_model', '.collision_model')
                      for path in [Path(config['kit']) / 'tags' / (TAG + extension)] if path.is_file())
    if len(signature) != 4:
        raise ValidationError(['Invisible block: original scenery/model/collision tags are missing. Extract the Halo 3 Editing Kit tags.'])
    if signature not in _verified:
        result = jobs.helper('tags', dict(operation='resolve_scenery', kit=config['kit'],
                            sources=[TAG], output=str(directory / 'invisible-block-match.json')), directory)
        if not any(row['scenery'] == TAG and row['render'] == TAG for row in result.get('matches', [])):
            raise ValidationError(['Invisible block: its original scenery/render/collision tag chain could not be verified. Extract the Halo 3 Editing Kit tags.'])
        _verified.add(signature)
    placements, issues, ids = [], [], set()
    for obj in objects:
        try:
            if obj.modifiers:
                raise ValueError('Remove modifiers; original blocker collision cannot reproduce mesh edits.')
            if obj.get('hb_map_reference'):
                manifest = Path(obj['hb_map_manifest']); data = read_json(manifest)
                row = data['placements'][obj['hb_map_placement_index']]
                if row['source_tag'] != TAG or row['group'] != 'Scenery':
                    raise ValueError('Original scenery identity does not match.')
                preview = read_json(manifest.parent / data['meshes'][row['mesh']])
            else:
                preview = read_json(Path(obj['hb_cache']) / 'preview.json')
            positions, faces = [], []
            for mesh in preview['meshes']:
                start = len(positions); positions.extend(mesh['positions'])
                for segment in mesh['segments']:
                    faces.extend(tuple(start + v for v in segment['indices'][i:i+3])
                                 for i in range(0, len(segment['indices']), 3))
            if not positions or len(positions) != len(obj.data.vertices) or len(faces) != len(obj.data.polygons):
                raise ValueError('Blocker geometry was edited; restore its original mesh to reuse original collision.')
            offset = Vector(positions[0]) - obj.data.vertices[0].co
            if (any((Vector(p) - v.co - offset).length > 1e-5 for p, v in zip(positions, obj.data.vertices))
                    or any(tuple(p.vertices) != f for p, f in zip(obj.data.polygons, faces))):
                raise ValueError('Blocker geometry was edited; restore its original mesh to reuse original collision.')
            units = float(obj.get('hb_working_units', 100))
            matrix = obj.matrix_world @ Matrix.Translation(-offset)
            loc, rot, scale = matrix.decompose()
            if not math.isfinite(units) or units <= 0 or any(not math.isfinite(v) for row in matrix for v in row):
                raise ValueError('Invalid blocker transform.')
            if min(scale) <= 0 or max(scale) - min(scale) > 1e-4:
                raise ValueError('Original blocker collision requires positive uniform scale.')
            rebuilt = Matrix.LocRotScale(loc, rot, scale)
            if max(abs(matrix[r][c] - rebuilt[r][c]) for r in range(4) for c in range(4)) > 1e-4:
                raise ValueError('Remove transform shear from this blocker.')
            identity = obj.get('hb_blocker_id', '')
            if not re.fullmatch(r'hb_[0-9a-f]{24}', identity) or identity in ids:
                identity = blender_ops.new_id(); obj['hb_blocker_id'] = identity
            ids.add(identity); euler = rot.to_euler('XYZ')
            placements.append(dict(id=identity, tag=TAG, position=list(loc / units),
                                   rotation=[math.degrees(euler.z), -math.degrees(euler.y), math.degrees(euler.x)],
                                   scale=float(scale.x) / units))
        except (ValueError, KeyError, IndexError, TypeError, OSError) as error:
            issues.append(obj.name + ': ' + str(error))
    if issues:
        raise ValidationError(issues, 'Original invisible-block validation')
    return placements
