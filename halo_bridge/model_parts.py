"""Editable region/permutation selection, without moving model-space vertices."""
import json
from pathlib import Path
import bpy
from mathutils import Matrix, Vector
from . import blender_ops
from .catalog import read_json

_cache = {}

def data(obj):
    path = obj.get('hb_parts_path', '') if obj else ''
    if not path:
        return None
    if path not in _cache:
        _cache[path] = read_json(path)
    return _cache[path]

def choices(obj):
    result = {}
    for part in (data(obj) or {}).get('meshes', []):
        result.setdefault(part['choice'], (part['region'], part['permutation']))
    return result

def enabled(obj):
    return set(json.loads(obj.get('hb_parts_enabled', '[]')))

def check_editable(obj):
    if obj.modifiers or blender_ops.mesh_signature(obj.data) != obj.get('hb_parts_signature'):
        raise RuntimeError('This model mesh was edited. Place a fresh copy to change variants without losing your edits.')
    if obj.get('hb_vehicle_tag'):
        raise RuntimeError('Use static mesh instead before changing parts; an original vehicle tag controls its own variants.')

def build_mesh(obj, selected, key):
    source = data(obj)
    parts = [p for p in source['meshes'] if p['choice'] in selected]
    # A shared mesh can be referenced by multiple permutation names. Do not
    # duplicate the same surfaces when both aliases are selected.
    unique = {p['source_mesh']: p for p in parts}
    payload = dict(source, meshes=list(unique.values()))
    mesh = blender_ops.mesh_from_preview(obj['hb_parts_path'], key, payload)
    custom={m.get('hb_source_shader'):m for m in obj.data.materials if m and m.get('hb_custom_shader') and m.get('hb_source_shader')}
    for index,mat in enumerate(mesh.materials):
        if mat and mat.get('hb_shader') in custom:mesh.materials[index]=custom[mat['hb_shader']]
    offset = Vector(obj.data.get('hb_origin_center', (0, 0, 0)))
    mesh.transform(Matrix.Translation(-offset))
    mesh['hb_origin_center'] = list(offset)
    return mesh

def apply(obj, selected):
    check_editable(obj)
    selected = set(selected)
    if not selected <= choices(obj).keys():
        raise RuntimeError('The part selection is no longer available. Reimport the model.')
    mesh = build_mesh(obj, selected, 'parts_' + blender_ops.new_id())
    old = obj.data; obj.data = mesh
    obj['hb_parts_enabled'] = json.dumps(sorted(selected))
    obj['hb_parts_signature'] = blender_ops.mesh_signature(mesh)
    obj['hb_mesh_signature'] = obj['hb_parts_signature']
    if old.users == 0:
        bpy.data.meshes.remove(old)

def separate(context, obj, all_variants=False):
    check_editable(obj)
    if obj.get('hb_preview'):
        raise RuntimeError('Place the model first, then separate its parts.')
    groups = choices(obj); selected = set(groups) if all_variants else enabled(obj)
    if not selected:
        raise RuntimeError('Enable at least one part first.')
    if obj.children:
        raise RuntimeError('Unparent attached child objects before separating this model.')
    created = []
    try:
        for choice in sorted(selected):
            mesh = build_mesh(obj, {choice}, 'part_' + blender_ops.new_id())
            region, permutation = groups[choice]
            part = bpy.data.objects.new(obj.name + ' / ' + region + ' / ' + permutation, mesh)
            created.append(part)
            for collection in obj.users_collection:
                collection.objects.link(part)
            part.parent = obj.parent; part.matrix_world = obj.matrix_world.copy()
            for key in ('hb_game', 'hb_working_units', 'hb_source_tag', 'hb_cache'):
                if key in obj: part[key] = obj[key]
            part['hb_id'] = blender_ops.new_id(); part['hb_kind'] = 'model'
            part['hb_model_part'] = True; part['hb_region'] = region
            part['hb_permutation'] = permutation
        bpy.ops.object.select_all(action='DESELECT')
        created[0].select_set(True)
        context.view_layer.objects.active = created[0]
        old = obj.data; bpy.data.objects.remove(obj, do_unlink=True)
        if old.users == 0: bpy.data.meshes.remove(old)
    except Exception:
        for part in created:
            mesh = part.data; bpy.data.objects.remove(part, do_unlink=True)
            if mesh.users == 0: bpy.data.meshes.remove(mesh)
        raise
    return created
