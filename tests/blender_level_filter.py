import sys,json,tempfile
from pathlib import Path
from types import SimpleNamespace
import bpy
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import halo_bridge
halo_bridge.register()
from halo_bridge import ui
s=bpy.context.scene.halo_bridge
ui._catalogue={'version':1,'assets':[dict(id=str(i),name='Shared tree',level=level,category='Vegetation',kind='model') for i,level in enumerate(('010_jungle','lockout','010_jungle'))]}
ui.refresh(bpy.context,persist=False)
for name,expected in [('lockout',1),('010_jungle',2),('__ALL__',3)]:
 s.filter_level=name
 flags,_=ui.HB_UL_assets.filter_items(SimpleNamespace(bitflag_filter_item=1),bpy.context,s,'assets')
 visible=[r for r,f in zip(s.assets,flags) if f]
 assert len(visible)==expected,(name,len(visible))
 if name!='__ALL__':assert all(ui.level_key(r.level)==name for r in visible)
 assert s.filter_level_selected==name
 print('PASS',name,len(visible))
s.filter_level='lockout';s.search='010_jungle'
assert not any(ui.row_visible(s,r) for r in s.assets)
s.search='';s.asset_tab='HIDDEN'
assert not any(ui.row_visible(s,r) for r in s.assets)
s.asset_tab='IMPORTED'
assert ui.level_key(r'E:\maps\010_Jungle.MAP')=='010_jungle'
temporary=tempfile.TemporaryDirectory();path=str(Path(temporary.name)/'level-filter-test.blend')
bpy.ops.wm.save_as_mainfile(filepath=path)
bpy.ops.wm.open_mainfile(filepath=path,load_ui=False)
s=bpy.context.scene.halo_bridge
assert s.filter_level_selected=='lockout'
assert all(r.level=='lockout' for r in s.assets if ui.row_visible(s,r))
print('PASS search, hidden tab, uppercase paths, save/reopen selection')

temporary.cleanup()
