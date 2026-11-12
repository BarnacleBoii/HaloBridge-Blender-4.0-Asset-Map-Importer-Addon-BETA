"""Current-scene preparation must never silently drop imported map geometry."""
import sys
from pathlib import Path
from unittest.mock import patch
import bpy
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import halo_bridge
halo_bridge.register()
from halo_bridge import ui,blender_ops,catalog
assert not hasattr(ui,'HBCopyOriginal')
assert ui.HBPrepare.bl_label=='Prepare current scene for sapien'
assert catalog.safe_level('shrine20')=='shrine20'
try:catalog.safe_level('shrine20.map')
except ValueError as e:assert 'above the Prepare button' in str(e) and 'shrine20.map' in str(e)
else:raise AssertionError('Extension accepted')
# The default cube is an authored mesh. A reference map alongside it must still block export.
obj=bpy.data.objects.new('map terrain',bpy.data.meshes.new('map terrain'))
bpy.context.collection.objects.link(obj);obj['hb_map_reference']=True;obj['hb_ignore']=True
with patch.object(blender_ops,'ensure_exporter',side_effect=AssertionError('Exporter should not run')):
    try:blender_ops.export_scene({},'unused.ASS')
    except RuntimeError as e:assert 'silently exporting only the starter shell' in str(e)
    else:raise AssertionError('Map silently omitted')
bpy.data.objects.remove(obj,do_unlink=True)
blender_ops.validate_map_export(bpy.context.scene)
class Layout:
    def __init__(self):self.labels=[];self.ops=[]
    def label(self,**kw):self.labels.append(kw.get('text',''))
    def operator(self,name,**kw):self.ops.append((name,kw));return self
    def operator_menu_enum(self,name,property,**kw):return self.operator(name,**kw)
    def prop(self,*a,**k):pass
    def box(self):return self
    def row(self,**k):return self
    def column(self,**k):return self
    def grid_flow(self,**k):return self
    def template_list(self,*a,**k):pass
    def separator(self,*a,**k):pass
layout=Layout();layout.layout=layout
bpy.context.scene.halo_bridge.setup=False
# Background mode has no UI region; the panel wraps text to the region width.
from types import SimpleNamespace
context=SimpleNamespace(**{k:getattr(bpy.context,k) for k in ('scene','active_object','object','selected_objects','view_layer','window_manager','tool_settings','screen')},region=SimpleNamespace(width=340))
ui.HBPanel.draw(layout,context)
assert 'Folders and Setup' in layout.labels
assert any(n=='halo_bridge.detect' and k.get('depress') for n,k in layout.ops)
assert not any(n=='halo_bridge.copy_original' for n,k in layout.ops)
assert 'Output Level Name (without .map)' in layout.labels
print('PASS: labels, removed copy UI, always-visible setup, and mixed-scene omission guard')
