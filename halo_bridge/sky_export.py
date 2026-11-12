"""Skies from other games, rebuilt as a Halo 3 / ODST sky object.

A Halo 3 sky is a scenery object whose render model surrounds the level (Deadlock's
is about 5,500 world units across) and uses ordinary shaders. A sky model chosen
from another game's index is placed in Blender in the "Sapien Sky" collection, so
its size and position can be checked and changed. Preparation converts its textures
like other cross-game materials, writes it as a JMS render model and Tool's
render-sky builds it; the tag helper then creates the model and scenery tags and
puts the sky in the scenario.
"""
import json
from pathlib import Path
import bpy
from mathutils import Matrix, Vector
from . import blender_ops, cross_game

PROPERTY = 'hb_sapien_sky'
COLLECTION = 'Sapien Sky'
SKY_FOLDERS = {'sky', 'skies'}
# Halo CE and Halo 2 draw their sky models around the camera at their own small
# scale; Halo 3 places the sky in the world, so those skies are enlarged to
# surround the level. Halo 3, ODST and Reach skies are already world-sized.
CAMERA_SKIES = {'halo1', 'halo2'}
MIN_RADIUS, MAX_RADIUS = 2000.0, 6000.0


def is_sky_asset(asset):
    tag = asset.get('tag', '').lower().replace('/', '\\')
    return asset.get('kind') in ('model', 'scenery') and any(part in SKY_FOLDERS for part in tag.split('\\')[:-1])


def sky_object(scene):
    return next((o for o in scene.objects if o.get(PROPERTY) and o.type == 'MESH'), None)


def collection(scene):
    found = bpy.data.collections.get(COLLECTION)
    if found is None:
        found = bpy.data.collections.new(COLLECTION)
    if found.name not in scene.collection.children:
        scene.collection.children.link(found)
    return found


def world_radius(objects, depsgraph=None):
    """Largest distance from the origin of any bounding-box corner, in world units."""
    radius = 0.0
    for obj in objects:
        units = float(obj.get('hb_working_units', 100))
        for corner in obj.bound_box:
            radius = max(radius, (obj.matrix_world @ Vector(corner)).length / units)
    return radius


def place(context, asset, path, config):
    """Replace any previous Sapien sky with the chosen sky model."""
    scene = context.scene
    for old in [o for o in scene.objects if o.get(PROPERTY)]:
        bpy.data.objects.remove(old, do_unlink=True)
    # Always build the sky from the current extraction, not an older mesh of the same asset.
    for mesh in bpy.data.meshes:
        if mesh.get('hb_asset_id') == asset['id']:
            mesh['hb_asset_id'] = asset['id'] + '_previous'
    obj = blender_ops.place(asset, path, config, location=(0, 0, 0))
    for col in list(obj.users_collection):
        col.objects.unlink(obj)
    collection(scene).objects.link(obj)
    obj[PROPERTY] = True
    obj['hb_ignore'] = True  # never part of the level geometry
    obj.name = 'Sapien sky - ' + asset['name']
    if asset.get('game') in CAMERA_SKIES:
        level = [o for o in scene.objects if o.type == 'MESH' and not o.get(PROPERTY) and not o.get('hb_preview')]
        target = min(MAX_RADIUS, max(MIN_RADIUS, 4 * world_radius(level)))
        current = world_radius([obj])
        if current > 0:
            obj.scale = obj.scale * (target / current)
    obj['hb_sky_game'] = asset.get('game', '')
    obj['hb_sky_asset'] = json.dumps(dict(id=asset['id'], name=asset['name'], tag=asset.get('tag', ''), level=asset.get('level', '')))
    return obj


def export(obj, folder, progress=None):
    """Convert the sky's materials and write sky.JMS; returns the JMS path and shader entries."""
    folder = Path(folder)
    folder.mkdir(parents=True, exist_ok=True)
    materials = {m.as_pointer(): m for m in obj.data.materials if m and not m.name.startswith('+')}
    if not materials:
        raise RuntimeError(obj.name + ': the sky has no materials.')
    converted = cross_game.prepare([obj], folder / 'textures', progress, materials=materials)
    units = float(obj.get('hb_working_units', 100))
    temp = bpy.data.scenes.new('HaloBridge sky export')
    mesh = obj.data.copy()
    made = []
    try:
        for index, mat in enumerate(list(mesh.materials)):
            if mat is None or mat.as_pointer() not in converted:
                continue
            entry = converted[mat.as_pointer()]
            copy = bpy.data.materials.new(entry['name'])
            copy.ass_jms.name_override = entry['name']
            made.append(copy)
            mesh.materials[index] = copy
            u, v = entry['tiling']
            if mesh.uv_layers.active and (u, v) != (1.0, 1.0):
                layer = mesh.uv_layers.active.data
                for face in mesh.polygons:
                    if face.material_index == index:
                        for loop in face.loop_indices:
                            layer[loop].uv.x *= u
                            layer[loop].uv.y *= v
        frame = bpy.data.objects.new('frame root', None)
        temp.collection.objects.link(frame)
        copy_obj = bpy.data.objects.new('sky', mesh)
        temp.collection.objects.link(copy_obj)
        copy_obj.parent = frame
        # JMS at scale "1" writes 100 units per Blender unit, Tool reads 100 per world unit.
        copy_obj.matrix_world = Matrix.Scale(1 / units, 4) @ obj.matrix_world
        from .compat import toolset_module
        import importlib
        toolset = toolset_module()
        if toolset is None:
            raise RuntimeError('Enable the Halo Asset Blender Development Toolset to export the sky.')
        export_jms = importlib.import_module(toolset.__name__ + '.file_jms.export_jms')
        functions = importlib.import_module(toolset.__name__ + '.global_functions.global_functions')
        path = folder / 'sky.JMS'
        path.unlink(missing_ok=True)
        messages = []
        with bpy.context.temp_override(scene=temp, view_layer=temp.view_layers[0]):
            export_jms.write_file(bpy.context, str(path), 'halo3', 8210, '', '', False, 0, False, False, False, False, True, False, False,
                                  True, True, False, False, functions.EdgeSplit(False, True, 0.523599, True), False, False, False,
                                  functions.set_scale('1', 1.0), False, lambda *a: messages.append(a))
        if not path.is_file():
            raise RuntimeError('The sky JMS was not written. ' + ' '.join(str(m) for m in messages))
    finally:
        for o in list(temp.objects):
            bpy.data.objects.remove(o, do_unlink=True)
        bpy.data.scenes.remove(temp)
        bpy.data.meshes.remove(mesh)
        for mat in made:
            bpy.data.materials.remove(mat)
    # Halo CE / Halo 2 skies are stacked layers drawn additively; opaque layers would
    # hide each other behind their black backgrounds.
    additive = obj.get('hb_sky_game') in CAMERA_SKIES
    shaders = [dict(entry, folder='sky', additive=additive) for entry in converted.values()]
    return dict(jms=str(path), shaders=shaders, name=obj.name, radius=world_radius([obj]) * 1.05)
