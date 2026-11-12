"""Blender API differences between 4.0 and 5.2, kept in one place.

- Mesh.use_auto_smooth was removed in 4.1; custom normals work without it.
- EEVEE Next (4.2) replaced Material.blend_method with surface_render_method.
- Brushes became assets in 4.3, so Paint.brush can no longer be assigned and
  the texture-paint draw tool id changed.
- Unified paint settings became per paint mode in 5.0.
"""
import sys
import bpy

ALPHA_MODES = ('opaque', 'clip', 'blend')


def enable_nodes(material):
    """Material node trees are always on in newer Blender; older versions need use_nodes."""
    if hasattr(material, 'use_nodes') and not material.use_nodes:
        try:
            material.use_nodes = True
        except (AttributeError, TypeError):
            pass
    return material.node_tree


def nodes_enabled(material):
    return material is not None and material.node_tree is not None and getattr(material, 'use_nodes', True)


def set_alpha(material, mode):
    """Record HaloBridge's alpha intent and apply the closest viewport setting."""
    if mode not in ALPHA_MODES:
        mode = 'opaque'
    material['hb_alpha_mode'] = mode
    if hasattr(material, 'surface_render_method'):
        material.surface_render_method = 'BLENDED' if mode == 'blend' else 'DITHERED'
    if hasattr(material, 'blend_method'):
        try:
            material.blend_method = {'opaque': 'OPAQUE', 'clip': 'CLIP', 'blend': 'BLEND'}[mode]
        except (AttributeError, TypeError, ValueError):
            pass


def alpha_mode(material):
    if material is None:
        return 'opaque'
    stored = material.get('hb_alpha_mode')
    if stored in ALPHA_MODES:
        return stored
    if not hasattr(material, 'surface_render_method'):
        # Blender 4.0/4.1: the blend mode is authoritative.
        method = getattr(material, 'blend_method', 'OPAQUE')
        return 'clip' if method in ('CLIP', 'HASHED') else 'blend' if method == 'BLEND' else 'opaque'
    # 4.2+: blend_method is only a compatibility alias (dithered reads as hashed),
    # so use the render method and whether the alpha input is actually used.
    if material.surface_render_method == 'BLENDED':
        return 'blend'
    tree = material.node_tree
    bsdf = next((n for n in tree.nodes if n.type == 'BSDF_PRINCIPLED'), None) if tree else None
    if bsdf is not None and 'Alpha' in bsdf.inputs and (bsdf.inputs['Alpha'].is_linked or bsdf.inputs['Alpha'].default_value < 1):
        return 'clip'
    return 'opaque'


def is_transparent(material):
    return alpha_mode(material) != 'opaque'


def custom_normals(mesh, normals):
    if hasattr(mesh, 'use_auto_smooth'):
        mesh.use_auto_smooth = True
    mesh.normals_split_custom_set_from_vertices(normals)


def unified_paint(context, paint):
    return getattr(paint, 'unified_paint_settings', None) or getattr(context.tool_settings, 'unified_paint_settings', None)


def texture_paint_brush(context, paint, name):
    """A mix-blend draw brush for texture painting, on every supported Blender."""
    try:
        brush = bpy.data.brushes.get(name) or bpy.data.brushes.new(name, mode='TEXTURE_PAINT')
        paint.brush = brush
        brush.blend = 'MIX'
        return brush
    except (AttributeError, TypeError, RuntimeError, ValueError):
        pass
    # 4.3+: activate the bundled draw brush asset; fall back to whatever is active.
    try:
        bpy.ops.brush.asset_activate(asset_library_type='ESSENTIALS', asset_library_identifier='',
                                     relative_asset_identifier='brushes/essentials_brushes-mesh_texture.blend/Brush/Paint Hard')
    except (AttributeError, RuntimeError, TypeError):
        pass
    return getattr(paint, 'brush', None)


def set_paint_color(context, paint, brush, color):
    unified = unified_paint(context, paint)
    if unified is not None and hasattr(unified, 'use_unified_color'):
        unified.use_unified_color = True
        unified.color = color
    if brush is not None and not getattr(brush, 'library', None):
        try:
            brush.color = color
        except (AttributeError, TypeError):
            pass


def draw_tool(context, area):
    with context.temp_override(area=area):
        for tool in ('builtin.brush', 'builtin_brush.Draw'):
            try:
                if bpy.ops.wm.tool_set_by_id(name=tool) == {'FINISHED'}:
                    return
            except (RuntimeError, TypeError):
                continue


def toolset_module():
    """The Halo Asset Blender Development Toolset module, installed as add-on or extension."""
    for name, module in list(sys.modules.items()):
        if (name == 'io_scene_halo' or name.endswith('.io_scene_halo')) and hasattr(module, 'bl_info'):
            return module
    return None


def section(layout, idname, title, icon='NONE', default_closed=False):
    """A collapsible sidebar section; returns (header, body), body None while collapsed.

    Each section sits in its own box, so its background and border separate it
    from its neighbours. Blender 4.1+ draws a native layout panel inside the box
    that remembers its open state. Older versions and test layouts get an
    always-open box with the title.
    """
    box = layout.box()
    if hasattr(box, 'panel'):
        header, body = box.panel(idname, default_closed=default_closed)
        header.label(text=title, icon=icon)
        return header, body
    box.label(text=title, icon=icon)
    return box, box


def clear_view_fog(screens, start=0.1, end=999999.0, unit_scale=1.0):
    """Push every 3D View's clip range out so large levels are not cut off or greyed.

    start/end are in the scene's displayed units: clip values are stored in Blender
    units, and HaloBridge scenes use a unit scale of 0.03048, so they are divided by it
    (Clip Start then reads 0.1 m, not 0.003048 m).
    """
    unit_scale = unit_scale if unit_scale and unit_scale > 0 else 1.0
    start, end = start / unit_scale, end / unit_scale
    count = 0
    for screen in screens:
        for area in screen.areas:
            if area.type == 'VIEW_3D':
                for space in area.spaces:
                    if space.type == 'VIEW_3D':
                        space.clip_start = start
                        space.clip_end = end
                        count += 1
    return count


_icons = None


def icon(*names):
    """First icon name this Blender knows; SEQUENCE_COLOR_* became STRIP_COLOR_* in 5.x.

    An unknown icon raises inside Panel.draw and Blender stops drawing the rest of the panel.
    """
    global _icons
    if _icons is None:
        _icons = {item.identifier for item in bpy.types.UILayout.bl_rna.functions['label'].parameters['icon'].enum_items}
    return next((name for name in names if name in _icons), 'NONE')


def toolset_frame_hack():
    """True when the toolset's run_code still writes results through caller frame
    locals (v364), which Python 3.13 (Blender 5.x) breaks. v432 copies them instead."""
    import inspect
    module = toolset_module()
    if module is None:
        return False
    functions = sys.modules.get(module.__name__ + '.global_functions.global_functions')
    run_code = getattr(functions, 'run_code', None)
    try:
        return run_code is not None and '__this_is_a_horrible_hack' in inspect.getsource(run_code)
    except (OSError, TypeError):
        return False


def toolset_addon_name():
    for name in bpy.context.preferences.addons.keys():
        if name == 'io_scene_halo' or name.endswith('.io_scene_halo'):
            return name
    return None
