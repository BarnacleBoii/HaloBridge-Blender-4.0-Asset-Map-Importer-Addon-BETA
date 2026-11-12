bl_info = {'name':'HaloBridge - Halo Level Importing','author':'HaloBridge contributors','version':(0,10,1),'blender':(4,0,0),'location':'3D View > Sidebar > HaloBridge','description':'Import Halo 3 levels from Editing Kit scenarios, browse Halo 3 and Reach map assets, and prepare custom Halo 3 Sapien levels (Blender 4.0 to 5.2)','category':'Import-Export'}

def register():
    from . import ui
    ui.register()

def unregister():
    from . import ui
    ui.unregister()





