"""Generated collision faces must have finite texture coordinates (Tool rejects NaN UVs).

Blender 5.2 leaves loops added with mesh.loops.add() uninitialized; a Guardian
scenario import produced NaN UVs on box-collision faces and Tool failed with
"mesh definition vertex texcoords invalid".
"""
import math, sys
from pathlib import Path
import bpy
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from halo_bridge import geometry_export

def uvs(mesh):
    values = [0.0] * (len(mesh.uv_layers.active.data) * 2)
    mesh.uv_layers.active.data.foreach_get('uv', values)
    return values

for attempt in range(25):
    mesh = bpy.data.meshes.new('render')
    mesh.from_pydata([(0, 0, 0), (1, 0, 0), (0, 1, 0)], [], [(0, 1, 2)])
    layer = mesh.uv_layers.new(name='UVMap')
    layer.data.foreach_set('uv', [0.25, 0.5] * 3)
    mesh.color_attributes.new('Col', 'FLOAT_COLOR', 'CORNER')
    mesh.materials.append(bpy.data.materials.new('render'))
    mesh.materials.append(bpy.data.materials.new('collision'))
    corners = [(x, y, z) for x in (0, 1) for y in (0, 1) for z in (0, 1)]
    faces = [(0, 1, 3, 2), (4, 6, 7, 5), (0, 4, 5, 1), (2, 3, 7, 6), (0, 2, 6, 4), (1, 5, 7, 3)]
    geometry_export.add_collision_geometry(mesh, 1, corners, faces)
    values = uvs(mesh)
    assert values[:6] == [0.25, 0.5] * 3, 'render UVs changed'
    assert all(v == 0.0 for v in values[6:]), ('collision UVs not zeroed', values[6:12])
    colors = [0.0] * (len(mesh.color_attributes['Col'].data) * 4)
    mesh.color_attributes['Col'].data.foreach_get('color', colors)
    assert all(math.isfinite(c) for c in colors) and all(c == 1.0 for c in colors[12:])
    bpy.data.meshes.remove(mesh)

# The export safety net replaces non-finite UVs on export copies and reports them.
mesh = bpy.data.meshes.new('nan')
mesh.from_pydata([(0, 0, 0), (1, 0, 0), (0, 1, 0)], [], [(0, 1, 2)])
mesh.uv_layers.new(name='UVMap').data.foreach_set('uv', [0.0, float('nan'), 1.0, 0.0, float('inf'), 1.0])
obj = bpy.data.objects.new('nan', mesh)
assert geometry_export.repair_texcoords([obj]) == {'nan': 2}
assert uvs(mesh) == [0.0, 0.0, 1.0, 0.0, 0.0, 1.0]
assert geometry_export.repair_texcoords([obj]) == {}
print('PASS collision faces get zero UVs and white colors; non-finite UVs are repaired before export')
