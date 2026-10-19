"""Reveal newly selected HaloBridge objects without changing the selection."""
import bpy

_last={}

def reveal_active(window):
    for area in window.screen.areas:
        if area.type!='OUTLINER' or area.spaces.active.display_mode!='VIEW_LAYER':continue
        region=next((r for r in area.regions if r.type=='WINDOW'),None)
        if region:
            with bpy.context.temp_override(window=window,area=area,region=region):
                bpy.ops.outliner.show_active()

def follow_selection():
    from . import ui
    if ui._task:return .2
    alive=set()
    for window in bpy.context.window_manager.windows:
        key=window.as_pointer();alive.add(key)
        settings=getattr(window.scene,'halo_bridge',None)
        obj=window.view_layer.objects.active
        identity=(window.scene.as_pointer(),window.view_layer.as_pointer(),obj.as_pointer() if obj else 0)
        if not settings or not settings.follow_outliner:
            _last.pop(key,None);continue
        if _last.get(key)==identity:continue
        _last[key]=identity
        if obj and obj.select_get(view_layer=window.view_layer) and not obj.get('hb_preview') and (obj.get('hb_map_reference') or obj.get('hb_id')):
            try:reveal_active(window)
            except RuntimeError:pass  # Outliner may be switching modes or being closed.
    for key in set(_last)-alive:_last.pop(key,None)
    return .2

def register():
    _last.clear()
    if not bpy.app.timers.is_registered(follow_selection):bpy.app.timers.register(follow_selection,first_interval=.2,persistent=True)

def unregister():
    if bpy.app.timers.is_registered(follow_selection):bpy.app.timers.unregister(follow_selection)
    _last.clear()
