"""Background Blender check for activity views and panel grouping."""
import sys,tempfile
from pathlib import Path
from types import SimpleNamespace
import bpy
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import halo_bridge
halo_bridge.register()
from halo_bridge import ui
from halo_bridge.progress import PreparationActivity

drawn=[]
class Layout:
    def row(self,**kw):return self
    def box(self,**kw):return self
    def column(self,**kw):return self
    def grid_flow(self,**kw):return self
    def separator(self,**kw):pass
    def prop(self,*args,**kw):drawn.append(('prop',args[1],kw))
    def label(self,**kw):drawn.append(('label',kw.get('text'),kw))
    def operator(self,name,**kw):drawn.append(('operator',name,kw));return SimpleNamespace()
    def template_list(self,*args,**kw):drawn.append(('list',args[0],kw))
    def template_icon(self,**kw):pass

with tempfile.TemporaryDirectory() as folder:
    ui._prepare_activity=PreparationActivity(Path(folder)/'activity.log',lambda _:None)
    ui._prepare_activity.stage(3,'Compile geometry and collision')
    ui._prepare_activity.event('Test object 1/2')
    raw=Path(folder)/'compiler.log';raw.write_text('creating initial planes... 1%\n')
    ui._prepare_activity.current_log=str(raw)
    ui.sync_activity_texts(force=True)
    assert 'Test object 1/2' in bpy.data.texts['HaloBridge preparation activity'].as_string()
    assert 'initial planes' in bpy.data.texts['HaloBridge compiler output'].as_string()
    ui._prepare_activity.event('Test object 2/2');ui.sync_activity_texts(force=True)
    assert 'Test object 2/2' in bpy.data.texts['HaloBridge preparation activity'].as_string()
    context=SimpleNamespace(scene=bpy.context.scene,region=SimpleNamespace(width=340),active_object=bpy.context.active_object)
    ui.HBPanel.draw(SimpleNamespace(layout=Layout()),context)
    for name in ('halo_bridge.index','halo_bridge.import_map_scene'):
        assert next(row[2] for row in drawn if row[:2]==('operator',name))['depress']
    labels=[row[1] for row in drawn if row[0]=='label']
    assert labels.index('Materials and Shaders')<labels.index('Sky (Experimental)')<labels.index('(Experimental) Sapien Map Preparation')
    header=next(i for i,row in enumerate(drawn) if row[:2]==('label','Asset List'))
    search=next(i for i,row in enumerate(drawn) if row[:2]==('prop','search'))
    listing=next(i for i,row in enumerate(drawn) if row[0]=='list')
    assert header<search<listing
    assert 'Stage 3/5 — Compile geometry and collision' in labels
    assert any(row[:2]==('operator','halo_bridge.activity_log') for row in drawn)
ui._prepare_activity=None
halo_bridge.unregister()
print('PASS activity log refresh, compiler output, panel groups, import highlights and Asset List heading')
