"""Check category filtering and shader assignment through Blender's RNA properties."""
import sys
import tempfile
from pathlib import Path
from types import SimpleNamespace
import bpy

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import halo_bridge
halo_bridge.register()
from halo_bridge import shader_choices, ui

with tempfile.TemporaryDirectory() as folder:
    paths = ['levels/multi/snowbound/shaders/metal', 'levels/solo/010_jungle/shaders/ground', 'objects/vehicles/warthog/metal']
    for path in paths:
        tag = Path(folder)/'tags'/(path+'.shader')
        tag.parent.mkdir(parents=True, exist_ok=True)
        tag.touch()
    settings = bpy.context.scene.halo_bridge
    settings.game = 'halo3'
    settings.export_target = 'halo3'
    settings.kit = folder
    assert shader_choices.scan(folder) == 3
    # The sidebar no longer filters by level: every shader is listed whatever shader_level holds.
    rows = shader_choices.items(settings, bpy.context)
    assert len(rows) == 4
    for category in ('multi/snowbound', 'solo/010_jungle', 'ALL'):
        settings.shader_level = category
        assert shader_choices.items(settings, bpy.context) == rows
    operator = SimpleNamespace(shader_kit=folder, shader_category='ALL')
    assert shader_choices.search_items(operator, None) == rows
    for expected in paths:
        choice = next(row[0] for row in rows if row[0].replace('\\', '/') == expected)
        result = bpy.ops.halo_bridge.choose_shader('EXEC_DEFAULT', shader_kit=folder, shader_category='ALL', choice=choice)
        assert result == {'FINISHED'}
        assert settings.shader_choice == choice
    assert shader_choices.filtered_items(folder, 'missing') == shader_choices._empty
    settings.shader_choice = next(row[0] for row in rows if row[0].replace('\\', '/') == paths[0])
    obj = bpy.context.active_object
    mat = bpy.data.materials.new('Test material')
    obj.data.materials.clear()
    obj.data.materials.append(mat)
    assert bpy.ops.halo_bridge.shader() == {'FINISHED'}
    assert mat['hb_shader'].replace('\\', '/') == paths[0]
    assert ui.HBReadShaderTextures.bl_label == 'Load Halo Shader Textures/Masks for Currently selected Material'
print('PASS unfiltered shader list, search items, assignment and labels')
