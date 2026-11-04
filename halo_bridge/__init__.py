bl_info = {'name':'HaloBridge - Blender 4.0 Importing','author':'HaloBridge contributors','version':(0,9,0),'blender':(4,0,0),'location':'3D View > Sidebar > HaloBridge','description':'Browse Halo 3 and Reach assets with shared tools and prepare custom Halo 3 Sapien levels','category':'Import-Export'}

def register():
    from . import ui
    ui.register()

def unregister():
    from . import ui
    ui.unregister()





