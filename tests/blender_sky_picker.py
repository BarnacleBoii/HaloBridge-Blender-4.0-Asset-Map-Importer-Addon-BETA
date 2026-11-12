import sys,json,tempfile
from pathlib import Path
import bpy
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import halo_bridge
halo_bridge.register()
from halo_bridge import skies,ui
s=bpy.context.scene.halo_bridge
with tempfile.TemporaryDirectory() as folder:
 s.cache=folder;s.kit='X:/Games/steamapps/common/H3EK/'
 sky=r'levels\multi\lockout\lockout'
 Path(folder,'sky-catalogue.json').write_text(json.dumps(dict(kit=r'x:\games\steamapps\common\h3ek',items=[dict(scenario=sky,name='Lockout',skies=['sky'])])))
 skies.invalidate();rows=skies.items(s,bpy.context)
 assert len(rows)==2,rows
 assert bpy.ops.halo_bridge.choose_sky('INVOKE_DEFAULT',choice=sky)=={'FINISHED'}
 assert s.sky_selected==sky and ui.export_config(bpy.context)['sky_scenario']==sky
 assert bpy.ops.halo_bridge.choose_sky(choice='AUTO')=={'FINISHED'}
 assert s.sky_selected=='AUTO'
 s.kit='F:/different-kit';assert len(skies.items(s,bpy.context))==1
 print('PASS: equivalent folder spellings, sky selection/export configuration, default choice, wrong-kit isolation')
