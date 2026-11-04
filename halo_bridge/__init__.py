bl_info = {'name':'HaloBridge - Blender 4.0 Importing','author':'HaloBridge contributors','version':(0,8,9),'blender':(4,0,0),'location':'3D View > Sidebar > HaloBridge','description':'Browse Halo 3 assets and prepare custom levels for Sapien','category':'Import-Export'}

def register():
    from . import ui
    ui.register()

def unregister():
    from . import ui
    ui.unregister()





