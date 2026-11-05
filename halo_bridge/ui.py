import json
import copy
import time
import textwrap
import subprocess
import threading
import traceback
from pathlib import Path
import bpy
from bpy.app.handlers import persistent
from bpy.props import StringProperty, BoolProperty, IntProperty, CollectionProperty, PointerProperty, EnumProperty
from .catalog import detect_paths,read_json,write_json,scan_library,merge_assets,indexed_assets,safe_level
from . import jobs, build, blender_ops, setup, map_scene, navigation, map_export, skies, geometry_export
from .diagnostics import ValidationError
from . import source_names,export_review,shader_choices,vehicles
from .progress import PreparationActivity
from . import games

def record_failure(error, details=None):
    global _error,_message,_reported_issues
    issues=getattr(error,'issues',None) or [str(error).strip() or type(error).__name__]
    _reported_issues=issues
    _message=(str(len(issues))+' issue(s) detected. Open diagnostic report for the complete list.')
    _error='\n\n'.join(str(i+1)+'. '+item for i,item in enumerate(issues))
    _error+='\n\nChecks stop when a dependent stage cannot run; this is every issue detected so far, not a guarantee that later compilation will pass.'
    if details:_error+='\n\nTechnical details:\n'+details
    text=bpy.data.texts.get('HaloBridge diagnostics') or bpy.data.texts.new('HaloBridge diagnostics');text.clear();text.write(_error)
    try:
        folder=Path(config(bpy.context)['cache'])/'diagnostics';folder.mkdir(parents=True,exist_ok=True)
        report=folder/('failure-'+str(time.time_ns())+'.txt');report.write_text(_error,encoding='utf-8')
        text.write('\n\nSaved report: '+str(report))
    except Exception:pass # Reporting must not hide the original failure.
    return issues

_catalogue={'version':1,'assets':[]}
_catalogue_path=None
_list_undo=[]
_list_redo=[]

def list_snapshot(context):
    s=context.scene.halo_bridge
    return dict(data=copy.deepcopy(_catalogue),path=_catalogue_path,
                checked=[a.asset_id for a in s.assets if a.checked],
                active=s.assets[s.active_index].asset_id if 0<=s.active_index<len(s.assets) else None)

def remember_list(context,before):
    after=list_snapshot(context)
    if before['data']==after['data']:return
    if _list_undo and (_list_undo[-1][1]['data']!=before['data'] or _list_undo[-1][1]['path']!=before['path']):_list_undo.clear()
    _list_undo.append((before,after));del _list_undo[:-30];_list_redo.clear()

def history_available(redo=False):
    stack=_list_redo if redo else _list_undo
    if not stack:return False
    expected=stack[-1][0 if redo else 1]
    return expected['path']==_catalogue_path and expected['data']==_catalogue
_task=None
_preview_generation=0
_preview_pending=None
_error=''
_message='Connect your folders, then index a map to browse its assets.'

class HBAsset(bpy.types.PropertyGroup):
    asset_id:StringProperty()
    level:StringProperty()
    category:StringProperty()
    kind:StringProperty()
    checked:BoolProperty(name='Select asset',description='Include this asset in actions for checked entries in the current list')
    hidden:BoolProperty(default=False)

def visibility_predicate(settings):
    query=settings.search.lower();level=settings.filter_level;hidden=settings.asset_tab=='HIDDEN'
    # Resolve the stored enum number against retained entries. Normalize old
    # catalogues that used paths, .map extensions or inconsistent casing.
    raw=settings.get('filter_level')
    if isinstance(raw,int):level=next((row[0] for row in level_items(settings,None) if row[3]==raw),'__ALL__')
    level=level_key(level)
    categories={name:getattr(settings,'show_'+name,True) for name in ('vegetation','structures','materials','rocks','water')}
    return lambda item: (item.hidden==hidden and (level=='__ALL__' or level_key(item.level)==level)
                        and (not query or query in (item.name+' '+item.level+' '+item.kind).lower())
                        and categories.get(item.category.lower(),True))

def row_visible(settings,item):
    return visibility_predicate(settings)(item)

_level_items=[]
_retired_level_items=[]
_level_items_token=None
def level_key(value):
    if value=='__ALL__':return value
    return str(value).strip().replace('\\','/').rsplit('/',1)[-1].removesuffix('.map').lower()
def level_items(settings,context):
    global _level_items,_level_items_token
    token=(settings.id_data.as_pointer(),len(settings.assets))
    if token==_level_items_token:return _level_items
    levels=sorted({level_key(a.level) for a in settings.assets})
    # Keep strings alive for Blender's dynamic enum callback.
    if [entry[0] for entry in _level_items[1:]]!=levels or not _level_items:
        _retired_level_items.append(_level_items)
        _level_items=[('__ALL__','All Levels','Show assets from every indexed map',0)]+[(level,level,'Show assets indexed from '+level,1+(__import__('zlib').crc32(level.encode())&0x3fffffff)) for level in levels]
    _level_items_token=token
    return _level_items

def browsing_changed(settings,context):
    visible=visibility_predicate(settings)
    settings.active_index=next((i for i,item in enumerate(settings.assets) if visible(item)),-1)

def selection_changed(settings,context):
    global _preview_generation,_preview_pending
    if not settings.preview_enabled:return
    _preview_generation+=1
    _preview_pending=(settings.id_data.as_pointer(),_preview_generation)
    if not bpy.app.timers.is_registered(preview_tick):
        bpy.app.timers.register(preview_tick,first_interval=.05)

def preview_tick():
    global _preview_pending,_error,_message
    if _preview_pending is None:return None
    context=bpy.context
    if _preview_pending[0]!=context.scene.as_pointer() or not context.scene.halo_bridge.preview_enabled:
        _preview_pending=None;return None
    # Hide the previous asset immediately, even while an extraction finishes.
    clear_previews(context)
    if _task:return .05
    _preview_pending=None
    s=context.scene.halo_bridge
    if not 0<=s.active_index<len(s.assets) or not row_visible(s,s.assets[s.active_index]):return None
    try:bpy.ops.halo_bridge.place(preview_only=True)
    except Exception as e:
        _error=traceback.format_exc();_message=str(e).strip() or type(e).__name__
    return None

def stop_preview(context):
    global _preview_generation,_preview_pending
    context.scene.halo_bridge.preview_enabled=False
    _preview_generation+=1;_preview_pending=None
    if _task and getattr(_task,'preview_generation',None) is not None:_task.cancel.set()
    clear_previews(context)

def game_changed(settings,context):
    global _catalogue,_catalogue_path,_level_items_token
    if not context:return
    stop_preview(context)
    profiles=json.loads(settings.game_profiles or '{}')
    keys=('kit','maps','cache','map_name')
    profiles[settings.previous_game]={k:getattr(settings,k) for k in keys}
    chosen=profiles.get(settings.game) or dict(detect_paths(settings.game),map_name=games.GAMES[settings.game]['map_name'])
    for key in keys:setattr(settings,key,chosen.get(key,''))
    settings.shader_choice='NONE';settings.shader_level='ALL';settings.game_profiles=json.dumps(profiles);settings.previous_game=settings.game
    _catalogue_path=None;_level_items_token=None
    _catalogue=read_json(Path(bpy.path.abspath(settings.cache))/'catalogue.json',{'version':1,'assets':[]})
    refresh(context,persist=False)


class HBSettings(bpy.types.PropertyGroup):
    game:EnumProperty(name='Import game',items=games.IMPORT_ITEMS,default='halo3',update=game_changed)
    previous_game:StringProperty(default='halo3')
    game_profiles:StringProperty(default='{}')
    kit:StringProperty(name='Halo 3 Editing Kit',subtype='DIR_PATH',description='Editing Kit folder containing tool.exe, sapien.exe, and your editable tags')
    maps:StringProperty(name='Halo 3 .map Files',subtype='DIR_PATH',description='Your installed MCC maps folder for the selected Halo game')
    library:StringProperty(name='Extracted library',subtype='DIR_PATH')
    cache:StringProperty(name='Project and cache folder',subtype='DIR_PATH',description='Stores automatically extracted assets, project records, backups, and job logs for reuse')
    map_name:StringProperty(name='Choose .map file',default='010_jungle.map',description='Type a map filename, or use the adjacent dropdown to search maps in the selected game folder')
    level:StringProperty(name='Output Level Name (without .map)',default='hb_jungle_map',description='Name for your generated level; use 3–32 lowercase letters, digits, or underscores, starting with a letter')
    export_target:EnumProperty(name='Export to Sapien',items=[('halo3','Halo 3','Prepare using the Halo 3 Editing Kit'),('reach','Halo: Reach — not available yet','Reach importing is supported, but Reach Sapien compilation and tag writing are not implemented')],default='halo3')
    skip_invalid:BoolProperty(name='Skip objects with export problems',default=False,description='After review, omit entire objects with detected mesh or material problems. Objects stay in Blender. Compiler errors still stop the build')
    sky_choice:EnumProperty(name='(Experimental) Sky From Map',description='Choose the primary sky from any scanned Editing Kit map. Existing lightmaps and weather are not converted',items=skies.items)
    sky_selected:StringProperty(default='AUTO',description='Selected source scenario, stored independently of the scanned list')
    sky_scenario:StringProperty(name='Sky source scenario',default='levels\\multi\\deadlock\\deadlock',description='Existing Editing Kit scenario whose sky references are used; no .scenario extension. Whole-map imports fill this from their source. This does not copy terrain or gameplay')
    lighting:BoolProperty(name='Generate Test Lighting for Sapien Level',default=True,description='Generate quick test lighting during Sapien preparation; turn off for faster geometry iterations')
    open_sapien:BoolProperty(name='Open Sapien when ready',default=False,description='Launch the prepared scenario in Sapien automatically after a successful build')
    search:StringProperty(name='Search Assets',description='Filter assets as you type by name, source map, or asset type; applies within the active tab and enabled categories',options={'TEXTEDIT_UPDATE'},update=browsing_changed)
    filter_level:EnumProperty(name='Level Imported',description='Show assets from one indexed map or all maps',items=level_items,update=browsing_changed)
    filter_category:EnumProperty(name='Category',items=[(n,n,'') for n in ('All','Vegetation','Rocks','Structures','Water','Materials')],update=browsing_changed)
    show_vegetation:BoolProperty(name='Vegetation',default=True,update=browsing_changed)
    show_rocks:BoolProperty(name='Rocks',default=True,update=browsing_changed)
    show_structures:BoolProperty(name='Structures',default=True,update=browsing_changed)
    show_water:BoolProperty(name='Water',default=True,update=browsing_changed)
    show_materials:BoolProperty(name='Materials',default=True,update=browsing_changed)
    asset_tab:EnumProperty(name='Asset list',items=[('IMPORTED','Imported Assets','Available indexed assets; extraction happens on first use'),('HIDDEN','Hidden Assets','Hidden catalogue entries; restore them at any time')],update=browsing_changed)
    assets:CollectionProperty(type=HBAsset)
    active_index:IntProperty(default=0,update=selection_changed)
    preview_enabled:BoolProperty(default=False)
    follow_outliner:BoolProperty(name='Reveal selected asset in Outliner',default=True,description='Expand collections and scroll to the newly selected HaloBridge object in visible View Layer Outliners')
    shader_path:StringProperty(name='(Experimental) Shader Tag Path',description='Existing shader path relative to the Editing Kit tags folder, without its file extension')
    shader_choice:EnumProperty(name='Existing Halo shader',items=shader_choices.items,description='Choose an installed shader for the active Blender material; does not create a shader or change preview textures')
    shader_level:EnumProperty(name='Shader level / category',items=shader_choices.level_items,update=shader_choices.level_changed,description='Limit the shader search to a source level or shared asset category')
    shader_manual:BoolProperty(name='Enter shader path manually',default=False)
    setup:BoolProperty(name='Folders and Setup',default=True,description='Show or hide installation folders and map indexing controls')
    preview_previous_object:PointerProperty(type=bpy.types.Object)
    preview_object:PointerProperty(type=bpy.types.Object)
    advanced:BoolProperty(name='Advanced storage',default=False,description='Choose where cached assets and project records are stored; keep the existing folder when continuing a level')

def config(context):
    s=context.scene.halo_bridge
    # Keep saved project locations; new scenes use managed storage automatically.
    if not s.cache:s.cache=str(Path.home()/'Documents/HaloBridge')
    result={n:getattr(s,n) for n in ('game','kit','maps','library','cache','level','lighting','sky_scenario')}
    for n in ('kit','maps','library','cache'):result[n]=bpy.path.abspath(result[n])
    result['skip_invalid']=s.skip_invalid;result['export_target']=s.export_target
    if s.sky_selected!='AUTO':result['sky_scenario']=s.sky_selected
    elif s.sky_choice and s.sky_choice!='AUTO':result['sky_scenario']=s.sky_choice
    return result

def export_config(context):
    result=config(context);target=games.destination(context.scene.halo_bridge)
    if not games.GAMES[target.game]['sapien_enabled']:
        raise RuntimeError('Sapien export for '+games.GAMES[target.game]['label']+' is not implemented. Choose Halo 3 to prepare mixed-game assets.')
    result.update(game=target.game,kit=bpy.path.abspath(target.kit),maps=bpy.path.abspath(target.maps),cache=bpy.path.abspath(target.cache))
    return result


def ensure_catalogue(context,force=False):
    global _catalogue,_catalogue_path
    folder=context.scene.halo_bridge.cache
    path=str(Path(bpy.path.abspath(folder)).resolve()/'catalogue.json') if folder else None
    if force or path!=_catalogue_path or not _catalogue.get('assets'):
        data=read_json(path) if path else None
        if not isinstance(data,dict) or not isinstance(data.get('assets'),list):
            raise RuntimeError('The saved asset catalogue is missing. Click Detect folders, then Index map. Expected catalogue: '+str(path))
        _catalogue=data;_catalogue_path=path
    return _catalogue

def selected(context):
    s=context.scene.halo_bridge
    if not 0<=s.active_index<len(s.assets):raise RuntimeError('Select an asset first.')
    if not row_visible(s,s.assets[s.active_index]):raise RuntimeError('Select an asset in the current list first.')
    asset_id=s.assets[s.active_index].asset_id
    for force in (False,True):
        data=ensure_catalogue(context,force)
        asset=next((a for a in data['assets'] if a.get('id')==asset_id),None)
        if asset:return asset
    raise RuntimeError('This asset is no longer in the catalogue. Click Detect folders to reload the list, then select the asset again.')

def refresh(context,persist=True):
    global _catalogue_path,_level_items_token
    s=context.scene.halo_bridge
    previous_level=s.filter_level
    previous=s.assets[s.active_index].asset_id if 0<=s.active_index<len(s.assets) else None
    checked={a.asset_id for a in s.assets if a.checked}
    s.assets.clear()
    for a in _catalogue['assets']:
        row=s.assets.add();row.name=a['name'];row.asset_id=a['id'];row.level=a['level'];row.category=a['category'];row.kind=a['kind']
        row.hidden=bool(a.get('hidden',False));row.checked=a['id'] in checked
    _level_items_token=None
    if previous_level!='__ALL__' and level_key(previous_level) not in {level_key(a.level) for a in s.assets}:s.filter_level='__ALL__'
    predicate=visibility_predicate(s)
    visible=[i for i,a in enumerate(s.assets) if predicate(a)]
    s.active_index=next((i for i in visible if s.assets[i].asset_id==previous),visible[0] if visible else -1)
    _catalogue_path=str(Path(bpy.path.abspath(s.cache)).resolve()/'catalogue.json') if s.cache else None
    if persist and _catalogue_path:write_json(_catalogue_path,_catalogue)

def reconcile_preview_copies(context):
    """A copied flag does not make a pasted object our disposable preview."""
    owners={s.halo_bridge.preview_object for s in bpy.data.scenes if s.halo_bridge.preview_object}
    selected_copies=[]
    for obj in context.scene.objects:
        if obj.get('hb_preview') and obj not in owners:
            del obj['hb_preview']
            obj['hb_ignore']=False;obj.hide_render=False
            obj['hb_id']=blender_ops.new_id()
            if obj.name.startswith('[Preview] '):obj.name=obj.name[len('[Preview] '):]
            if obj.select_get():selected_copies.append(obj)
    if selected_copies:
        for owner in owners:
            if owner.name in context.view_layer.objects:owner.select_set(False)
        context.view_layer.objects.active=selected_copies[-1]
    repair_paste_active(context)


def repair_paste_active(context):
    """Native paste can leave an unselected source active (including its gizmo)."""
    active=context.active_object
    if not active or active.select_get() or not active.get('hb_id'):return
    copies=[obj for obj in context.selected_objects
            if obj!=active and obj.get('hb_id')==active.get('hb_id')]
    if copies:
        context.view_layer.objects.active=copies[-1]
        for obj in copies:obj['hb_id']=blender_ops.new_id()


@persistent
def paste_selection_updated(scene,depsgraph):
    # Selection-only fix is cheap and runs before the next interactive transform.
    # Do not change an intentional multi-selection or scan all scene geometry.
    if bpy.context.scene==scene:repair_paste_active(bpy.context)


_preview_check_token=None
def check_preview_copies():
    global _preview_check_token
    context=bpy.context
    if not context.scene or not hasattr(context.scene,'halo_bridge'):return .25
    active=context.active_object;owner=context.scene.halo_bridge.preview_object
    token=(context.scene.as_pointer(),len(context.scene.objects),active.as_pointer() if active else 0,owner.as_pointer() if owner else 0)
    if token!=_preview_check_token:
        reconcile_preview_copies(context);_preview_check_token=token
    return .25


def clear_previews(context,keep=None):
    s=context.scene.halo_bridge
    reconcile_preview_copies(context)
    obj=s.preview_object
    restore=bool(obj and context.active_object==obj and obj!=keep)
    if obj and obj!=keep:
        s.preview_object=None
        mesh=obj.data;bpy.data.objects.remove(obj,do_unlink=True)
        if mesh.users==0:bpy.data.meshes.remove(mesh)
    if keep is None:
        previous=s.preview_previous_object
        if restore and previous and previous.name in context.view_layer.objects:
            previous.select_set(True)
            context.view_layer.objects.active=previous
        s.preview_previous_object=None

def preview_active(context):
    return any(obj.get('hb_preview') for obj in context.scene.objects)

def show_preview(context,obj,name):
    clear_previews(context,keep=obj)
    context.scene.halo_bridge.preview_object=obj
    obj['hb_preview']=True;obj['hb_ignore']=True;obj.hide_render=True
    # Center only the disposable preview mesh; cached and placed meshes stay unchanged.
    original_mesh=obj.data;obj.data=original_mesh.copy()
    obj.data.use_fake_user=False
    if original_mesh.users==0:bpy.data.meshes.remove(original_mesh)
    map_scene.center_mesh_origin(obj.data)
    obj.matrix_world.translation=context.scene.cursor.location
    obj.name='[Preview] '+name

class HBTask:
    def __init__(self,fn,done):
        self.done_callback=done;self.cancel=threading.Event();self.result=None;self.error=None;self.finished=False
        self.scene=bpy.context.scene.as_pointer()
        def run():
            try:self.result=fn(self.cancel)
            except Exception as error:self.error=error;self.traceback=traceback.format_exc()
            finally:self.finished=True
        self.thread=threading.Thread(target=run,daemon=True);self.thread.start()

def start(context,fn,done,message,undo=False):
    global _task,_message,_error
    if _task:raise RuntimeError('Wait for the current job or cancel it.')
    _error='';_message=message;_task=HBTask(fn,done);_task.undo=undo
    if not bpy.app.timers.is_registered(poll):bpy.app.timers.register(poll,first_interval=.2)

def poll():
    global _task,_error,_message
    if not _task:return None
    sync_activity_texts()
    if bpy.context.scene.as_pointer()!=_task.scene:_task.cancel.set()
    if _task.finished:
        task=_task;_task=None
        try:
            generation=getattr(task,'preview_generation',None)
            if generation is not None and (generation!=_preview_generation or not bpy.context.scene.halo_bridge.preview_enabled):
                return None
            if task.error:raise task.error
            if task.cancel.is_set():raise jobs.Cancelled('Job cancelled; no new placements were applied.')
            if bpy.context.scene.as_pointer()!=task.scene:raise RuntimeError('The active scene changed during the job. Its result was not applied to this scene.')
            if getattr(task,'undo',False):
                global _apply_task
                _apply_task=task
                try:bpy.ops.halo_bridge.apply_extracted('EXEC_DEFAULT',True)
                finally:_apply_task=None
                return None
            if not hasattr(task,'application'):
                result=task.done_callback(task.result)
                if hasattr(result,'__next__'):task.application=result
            if hasattr(task,'application'):
                next(task.application)
                deadline=time.perf_counter()+getattr(task,'application_budget',0)
                while getattr(task,'application_budget',0) and time.perf_counter()<deadline:
                    if task.cancel.is_set():raise jobs.Cancelled('Import cancelled.')
                    next(task.application)
                _task=task
                for area in bpy.context.screen.areas if bpy.context.screen else []:area.tag_redraw()
                return .01
        except StopIteration:pass
        except Exception as e:
            if getattr(task,'is_prepare',False):prepare_status(('Preparation cancelled.' if isinstance(e,jobs.Cancelled) else 'Preparation failed: '+(str(e).strip() or type(e).__name__).splitlines()[0]))
            if hasattr(task,'application'):task.application.close()
            record_failure(e,getattr(task,'traceback',None) or traceback.format_exc())
            bpy.ops.halo_bridge.report_diagnostics()
        for area in bpy.context.screen.areas if bpy.context.screen else []:area.tag_redraw()
        sync_activity_texts()
        return .2 if _task else None
    for area in bpy.context.screen.areas if bpy.context.screen else []:area.tag_redraw()
    return .2

_apply_task=None

class HBApplyExtracted(bpy.types.Operator):
    bl_idname='halo_bridge.apply_extracted';bl_label='Place HaloBridge assets'
    bl_description='Commit extracted assets as one undoable scene change'
    bl_options={'INTERNAL','UNDO'}
    def execute(self,context):
        task=_apply_task
        if task is None:return {'CANCELLED'}
        result=task.done_callback(task.result)
        if hasattr(result,'__next__'):
            for _ in result:pass
        context.view_layer.update()
        return {'FINISHED'}

@persistent
def cancel_before_history(_=None):
    # Undo replaces RNA datablocks. Never call a closure holding the old objects.
    global _task,_preview_pending,_preview_generation
    _preview_generation+=1;_preview_pending=None
    if _task:
        _task.cancel.set()
        if getattr(_task,'is_prepare',False):prepare_status('Preparation cancelled by Undo/Redo.')
        if hasattr(_task,'application'):_task.application.close()
        _task=None

class Guard:
    def execute(self,context):
        global _error,_message
        try:
            if _task:raise RuntimeError('A HaloBridge job is running. Wait or cancel it first.')
            return self.run(context) or {'FINISHED'}
        except Exception as e:
            if self.bl_idname in {'halo_bridge.prepare','halo_bridge.confirm_prepare'}:prepare_status('Preparation failed: '+(str(e).strip() or type(e).__name__).splitlines()[0])
            issues=record_failure(e,traceback.format_exc())
            for issue in issues:self.report({'WARNING'},issue)
            self.report({'ERROR'},_message);return {'CANCELLED'}

class HBDetect(Guard,bpy.types.Operator):
    bl_idname='halo_bridge.detect';bl_label='Detect folders'
    bl_description='Find the selected game Editing Kit and MCC maps and reload its saved asset list'
    def run(self,context):
        global _catalogue,_message
        s=context.scene.halo_bridge
        for key,value in detect_paths(s.game).items():
            if key=='library':continue  # Legacy exports are optional, not part of setup.
            if not getattr(s,key):setattr(s,key,value)
        _catalogue=read_json(Path(bpy.path.abspath(s.cache))/'catalogue.json',{'version':1,'assets':[]});refresh(context,persist=False);_message='Folders detected. Index a map to browse its assets.'

class HBCheckSetup(Guard,bpy.types.Operator):
    bl_idname='halo_bridge.check_setup';bl_label='Check setup'
    bl_description='Check Blender, Halo tools, required tags, helper programs and .NET runtimes; show instructions for missing components'
    def run(self,context):
        global _message,_error
        issues=setup.check(config(context),Path(__file__).parent)
        if bpy.app.version[:2]!=(4,0):issues.append('This alpha is tested with Blender 4.0; other versions are not supported yet.')
        try:blender_ops.ensure_exporter()
        except Exception as e:issues.append(str(e))
        text=bpy.data.texts.get('HaloBridge diagnostics') or bpy.data.texts.new('HaloBridge diagnostics')
        text.clear();text.write('\n\n'.join(issues) if issues else 'Setup checks passed. Index a map to begin.')
        _error='\n'.join(issues)
        _message=(str(len(issues))+' setup items need attention. Open the diagnostic report.') if issues else 'Setup checks passed. Index a map to begin.'

class HBScan(Guard,bpy.types.Operator):
    bl_idname='halo_bridge.scan';bl_label='Scan extracted library'
    bl_description='Legacy import: catalogue previously exported AMF and JMS files; unnecessary for direct Halo 3 map browsing'
    def run(self,context):
        cfg=config(context)
        if not Path(cfg['library']).is_dir():raise RuntimeError('Choose your extracted library folder.')
        base=read_json(Path(cfg['cache'])/'catalogue.json',{'version':1,'assets':[]})
        def done(result):
            global _catalogue,_message
            before=list_snapshot(context);before['data']=copy.deepcopy(base);before['path']=str((Path(cfg['cache'])/'catalogue.json').resolve())
            _catalogue=merge_assets(base,result['assets']);refresh(context);remember_list(context,before);_message=f"Found {len(result['assets'])} extracted models."
        start(context,lambda cancel:scan_library(cfg['library']),done,'Scanning existing models and textures…')

_map_file_items=[]
_map_file_retired=[]


def refresh_map_files(context):
    global _map_file_items
    folder=Path(bpy.path.abspath(context.scene.halo_bridge.maps))
    if not context.scene.halo_bridge.maps or not folder.is_dir():
        raise RuntimeError('Choose the selected game .map Files folder first, or type a filename manually.')
    names=sorted((p.name for p in folder.iterdir() if p.is_file() and p.suffix.lower()=='.map'),key=str.casefold)
    if not names:raise RuntimeError('No .map files found in '+str(folder)+'. Check the folder or type a filename manually.')
    _map_file_retired.append(_map_file_items)
    _map_file_items=[(name,name,'Use '+name,index) for index,name in enumerate(names)]
    return _map_file_items


class HBChooseMap(bpy.types.Operator):
    bl_idname='halo_bridge.choose_map';bl_label='Choose .map file'
    bl_description='Search .map files in the selected game folder; choosing one fills the editable filename without importing'
    bl_property='choice'
    choice:EnumProperty(items=lambda self,context:_map_file_items)
    @classmethod
    def poll(cls,context):return _task is None
    def invoke(self,context,event):
        try:refresh_map_files(context)
        except (OSError,RuntimeError) as error:
            self.report({'WARNING'},str(error));return {'CANCELLED'}
        context.window_manager.invoke_search_popup(self)
        return {'RUNNING_MODAL'}
    def execute(self,context):
        if self.choice not in {item[0] for item in _map_file_items}:return {'CANCELLED'}
        context.scene.halo_bridge.map_name=self.choice
        return {'FINISHED'}


class HBIndex(Guard,bpy.types.Operator):
    bl_idname='halo_bridge.index';bl_label='Import Map Assets'
    bl_description='List assets in the selected game map for browsing; models and textures are extracted and cached when first used'
    def run(self,context):
        cfg=config(context);s=context.scene.halo_bridge;mp=Path(cfg['maps'])/s.map_name
        if not mp.is_file():raise RuntimeError('Choose an existing .map file for the selected game.')
        base=read_json(Path(cfg['cache'])/'catalogue.json',{'version':1,'assets':[]})
        out=Path(cfg['cache'])/'indexes'/(mp.stem+'.json');out.parent.mkdir(parents=True,exist_ok=True)
        def done(result):
            global _catalogue,_message
            before=list_snapshot(context);before['data']=copy.deepcopy(base);before['path']=str((Path(cfg['cache'])/'catalogue.json').resolve())
            _catalogue=merge_assets(base,indexed_assets(result));refresh(context);remember_list(context,before);_message=f"Indexed {len(result['assets'])} assets from {mp.stem}."
            if result.get('warnings'):
                report=bpy.data.texts.get('HaloBridge index report') or bpy.data.texts.new('HaloBridge index report')
                report.clear();report.write('\n'.join(result['warnings']))
                _message+=f" {len(result['warnings'])} omissions; see HaloBridge index report in the Text Editor."
        start(context,lambda cancel:jobs.helper('extractor',dict(operation='index',game=cfg['game'],map=str(mp),output=str(out)),Path(cfg['cache'])/'jobs',cancel),done,'Reading map asset index…')

def replacement_target(context,asset):
    targets=[o for o in context.selected_objects if not o.get('hb_preview')]
    if not targets and context.active_object and context.active_object.get('hb_preview'):
        previous=context.scene.halo_bridge.preview_previous_object
        if previous and not previous.get('hb_preview'):targets=[previous]
    if not targets:return [],'Select one or more objects in the 3D View first.'
    if context.mode!='OBJECT':return [],'Switch to Object Mode before swapping objects.'
    if any(o.library or o.override_library for o in targets):return [],'Selected objects must be editable; make linked objects local first.'
    if asset['kind'] not in ('instance','scenery','model','legacy'):
        return [],'Choose a geometry asset; materials cannot replace objects.'
    return targets,''


def swap_objects(context,targets,asset,path,cfg):
    # Build every replacement before removing any original, so import errors
    # leave the greybox intact. Snapshot transforms before parenting changes.
    from mathutils import Matrix
    snapshots=[(o,o.matrix_world.copy(),list(o.users_collection),o.parent,
                [(child,child.matrix_world.copy()) for child in o.children]) for o in targets]
    before=set(bpy.data.objects);created={};active=context.active_object
    try:
        for old,matrix,collections,parent,children in snapshots:
            obj=blender_ops.place(asset,path,cfg);created[old]=obj;obj.asset_mark()
            location,rotation,_=matrix.decompose()
            obj.matrix_world=Matrix.LocRotScale(location,rotation,obj.scale.copy())
            if old.get('hb_id'):obj['hb_id']=old['hb_id']
            for col in collections:
                if obj.name not in col.objects:col.objects.link(obj)
            for col in list(obj.users_collection):
                if col not in collections:col.objects.unlink(obj)
    except Exception:
        for obj in set(bpy.data.objects)-before:bpy.data.objects.remove(obj,do_unlink=True)
        for old in targets:old.select_set(True)
        context.view_layer.objects.active=active
        raise
    for old,matrix,collections,parent,children in snapshots:
        obj=created[old];world=obj.matrix_world.copy()
        obj.parent=created.get(parent,parent);obj.matrix_world=world
        for child,world in children:
            if child not in created:child.parent=obj;child.matrix_world=world
        for entry in _catalogue['assets']:
            if entry['id']==old.get('hb_asset_id') and entry['kind']=='legacy':entry['mapping']=dict(asset)
    for old in targets:bpy.data.objects.remove(old,do_unlink=True)
    for obj in context.selected_objects:obj.select_set(False)
    for obj in created.values():obj.select_set(True)
    context.view_layer.objects.active=created.get(active,next(iter(created.values())))
    refresh(context)
    return list(created.values())

class HBPlace(Guard,bpy.types.Operator):
    bl_idname='halo_bridge.place';bl_label='Place asset(s)'
    bl_description='Place the selected asset, keeping its preview position, rotation and scale; materials are loaded separately without changing existing objects'
    apply_material:BoolProperty(default=False)
    preview_only:BoolProperty(default=False)
    replace_selected:BoolProperty(default=False)
    @classmethod
    def description(cls,context,properties):
        if properties.replace_selected:
            return 'Swap all selected 3D View objects, including greybox cubes, for the highlighted asset; keep positions, rotations and collections, using the original asset import scale. Mesh edits and modifiers are replaced'
        if properties.preview_only:
            return 'Show a temporary preview of this asset; previews are excluded from level export'
        return cls.bl_description+'; checked entries take priority, otherwise uses the highlighted entry; turns Preview Mode off'
    def run(self,context):
        if not self.preview_only and not self.replace_selected and not self.apply_material and checked_ids(context):
            return bpy.ops.halo_bridge.place_checked()
        asset=selected(context);cfg=config(context)
        # Blender frees the operator RNA after execute returns; worker callbacks
        # must retain plain values, never properties on self.
        preview_only=bool(self.preview_only);apply_material=bool(self.apply_material)
        if asset['game']!=cfg['game']:raise RuntimeError('Choose an asset indexed for the selected Halo game.')
        targets=[]
        if self.replace_selected:
            targets,reason=replacement_target(context,asset)
            if reason:raise RuntimeError(reason)
        preview_matrix=None
        if not preview_only and not self.replace_selected and asset['kind']!='material':
            preview=next((obj for obj in context.scene.objects
                          if obj.get('hb_preview') and obj.get('hb_asset_id')==asset['id']),None)
            if preview:
                # Retain a value copy before stop_preview removes its object.
                context.view_layer.update()
                preview_matrix=preview.matrix_world.copy()
        if preview_only:
            context.scene.halo_bridge.preview_enabled=True
            active=context.active_object
            if not preview_active(context) or (active and not active.get('hb_preview')):
                context.scene.halo_bridge.preview_previous_object=active
        else:
            stop_preview(context)
        target=context.active_object
        if asset['kind']=='material' and apply_material and (not target or target.type!='MESH'):
            raise RuntimeError('Select a mesh to apply this material to, or click Preview.')
        if asset['kind']=='material' and apply_material and target.get('hb_preview'):
            raise RuntimeError('Select the level object that should receive this material; the preview sphere is not exported.')
        def done(path):
            global _message
            if asset['kind']=='material':
                data=read_json(path);mat=blender_ops.material(data['materials'][0],Path(path).parent);mat['hb_game']=asset['game']
                mat['hb_game']=asset['game'];mat['hb_asset_id']=asset['id'];mat.use_fake_user=True;mat.asset_mark()
                if apply_material:
                    if target.data.users>1:target.data=target.data.copy()
                    if target.data.materials:target.data.materials[target.active_material_index]=mat
                    else:target.data.materials.append(mat)
                    clear_previews(context)
                elif preview_only:
                    bpy.ops.mesh.primitive_uv_sphere_add(segments=24,ring_count=16,location=context.scene.cursor.location)
                    sphere=bpy.context.object;sphere.data.materials.append(mat)
                    show_preview(context,sphere,asset['name'])
                _message='Material preview shown in viewport (excluded from export).' if preview_only else ('Applied ' if apply_material else 'Loaded material (no object changed): ')+asset['name']
                return
            if targets:
                swapped=swap_objects(context,targets,asset,path,cfg)
                _message=f'Swapped {len(swapped)} object(s) to '+asset['name']+'.'
                return
            obj=blender_ops.place(asset,path,cfg)
            if preview_matrix is not None:
                obj.data=obj.data.copy();map_scene.center_mesh_origin(obj.data);obj.matrix_world=preview_matrix
            obj.asset_mark()
            if preview_only:
                # Native asset_generate_preview starts an asynchronous renderer.
                # Unlinking its object immediately afterwards can crash Blender 4.0.
                # Keep a visible, explicitly non-exported preview instead.
                show_preview(context,obj,asset['name'])
                _message='Preview shown in viewport (excluded from export). Place asset adds the level object.'
            else:
                clear_previews(context)
                _message='Placed '+asset['name']+'. Duplicate with Alt+D to share mesh data.'
        start(context,lambda cancel:jobs.extract(asset,cfg,cancel),done,'Preparing '+asset['name']+'…',undo=not preview_only)
        if preview_only:_task.preview_generation=_preview_generation

def checked_ids(context):
    s=context.scene.halo_bridge
    visible=visibility_predicate(s)
    return [a.asset_id for a in s.assets if a.checked and visible(a)]

class HBClearSearch(bpy.types.Operator):
    bl_idname='halo_bridge.clear_search';bl_label='Clear asset search'
    bl_description='Clear the search text to show all assets allowed by the current tab and category filters'
    def execute(self,context):
        context.scene.halo_bridge.search=''
        return {'FINISHED'}

class HBCheckAssets(bpy.types.Operator):
    bl_idname='halo_bridge.check_assets';bl_label='Select all listed'
    bl_description='Check or uncheck all entries currently shown by this tab and its search/category filters'
    check:BoolProperty(default=True)
    def execute(self,context):
        s=context.scene.halo_bridge
        visible=visibility_predicate(s)
        for a in s.assets:
            if visible(a):a.checked=self.check
        return {'FINISHED'}

class HBListHistory(Guard,bpy.types.Operator):
    bl_idname='halo_bridge.list_history';bl_label='Undo / Redo asset list'
    bl_description='Undo or redo the last hide, unhide, delete or index change in this session (up to 30 changes); scene objects and cached files are kept'
    redo:BoolProperty(default=False)
    def run(self,context):
        global _catalogue,_message
        if not history_available(self.redo):raise RuntimeError('No matching asset-list history is available.')
        source=_list_redo if self.redo else _list_undo
        destination=_list_undo if self.redo else _list_redo
        entry=source[-1];state=entry[1 if self.redo else 0]
        expected=entry[0 if self.redo else 1]
        if read_json(_catalogue_path)!=expected['data']:
            raise RuntimeError('The catalogue changed outside this list. Reload it before making further changes.')
        write_json(_catalogue_path,state['data'])
        _catalogue=copy.deepcopy(state['data']);refresh(context,persist=False)
        s=context.scene.halo_bridge
        for row in s.assets:row.checked=row.asset_id in state['checked']
        for i,row in enumerate(s.assets):
            if row.asset_id==state['active'] and row_visible(s,row):s.active_index=i;break
        source.pop();destination.append(entry)
        _message=('Redid' if self.redo else 'Undid')+' asset-list change.'

class HBListAction(Guard,bpy.types.Operator):
    bl_idname='halo_bridge.list_action';bl_label='Manage checked assets'
    bl_description='Hide, unhide, or delete checked catalogue entries; placed objects, original maps and cached files are kept'
    action:EnumProperty(items=[('HIDE','Hide',''),('UNHIDE','Unhide',''),('DELETE','Delete from list','')])
    asset_id:StringProperty()
    @classmethod
    def description(cls,context,properties):
        if properties.action=='HIDE':return 'Move these catalogue entries to Hidden Assets; placed objects remain visible and the original list order is preserved'
        if properties.action=='UNHIDE':return 'Return these entries to Imported Assets at their original positions'
        return 'Delete checked entries from this catalogue only; placed objects and files are kept. Re-index the map to restore deleted entries'
    def run(self,context):
        global _message
        data=ensure_catalogue(context)
        ids={self.asset_id} if self.asset_id else set(checked_ids(context))
        matches=[a for a in data['assets'] if a['id'] in ids]
        if not matches:raise RuntimeError('Check at least one asset in this tab first.')
        before=list_snapshot(context)
        path=Path(config(context)['cache'])/'catalogue.json'
        write_json(path.with_name('catalogue.before-list-edit.json'),data)
        # Preserve ordering by marking hidden entries in place, never moving rows.
        if self.action=='DELETE':data['assets']=[a for a in data['assets'] if a['id'] not in ids]
        else:
            for a in matches:a['hidden']=self.action=='HIDE'
        for a in context.scene.halo_bridge.assets:
            if a.asset_id in ids:a.checked=False
        refresh(context)
        remember_list(context,before)
        verb={'DELETE':'Deleted from list','HIDE':'Hidden','UNHIDE':'Restored'}[self.action]
        _message=verb+': '+str(len(matches))+' asset(s). Placed objects are unchanged.'

class HBPlaceChecked(Guard,bpy.types.Operator):
    bl_idname='halo_bridge.place_checked';bl_label='Place checked assets'
    bl_description='Place checked models together at the 3D cursor; load checked materials without changing existing objects. Failed extractions are listed in the report'
    entire_map:BoolProperty(default=False)
    @classmethod
    def description(cls,context,properties):
        if properties.entire_map:return 'Import the named map terrain and static placements at their original world coordinates'
        return cls.bl_description
    def run(self,context):
        if self.entire_map:return bpy.ops.halo_bridge.import_map_scene()
        cfg=config(context)
        data=ensure_catalogue(context)
        ids=set(checked_ids(context))
        assets=[dict(a) for a in data['assets'] if a['id'] in ids]
        if not assets:raise RuntimeError('Check at least one asset in this tab first.')
        if any(a['game']!=cfg['game'] for a in assets):raise RuntimeError('Uncheck assets from a different or unverified game.')
        target=context.active_object
        if target and target.get('hb_preview'):target=context.scene.halo_bridge.preview_previous_object
        materials=any(a['kind']=='material' for a in assets)
        if not target or target.type!='MESH':target=None
        context.view_layer.update()
        preview_matrix=next((o.matrix_world.copy() for o in context.scene.objects if o.get('hb_preview') and len(assets)==1 and o.get('hb_asset_id')==assets[0]['id']),None)
        origin=context.scene.cursor.location.copy()
        stop_preview(context)
        def extract_all(cancel):
            global _message
            paths=[];failures=[]
            for index,asset in enumerate(assets):
                if cancel.is_set():raise jobs.Cancelled('Batch placement cancelled before creating objects.')
                _message='Extracting '+str(index+1)+'/'+str(len(assets))+': '+asset['name']
                try:paths.append((asset,jobs.extract(asset,cfg,cancel)))
                except jobs.Cancelled:raise
                except Exception as e:failures.append(asset['name']+' ('+asset['id']+'): '+str(e))
            return paths,failures
        def done(result):
            global _message,_error
            paths,failures=result
            created=[]
            old_materials=list(target.data.materials) if materials and target else []
            old_slot=target.active_material_index if materials and target else 0
            loaded_materials=0
            previous_selection=list(context.selected_objects);previous_active=context.active_object
            try:
                for index,(asset,path) in enumerate(paths):
                    _message='Placing '+str(index+1)+'/'+str(len(paths))+': '+asset['name']
                    if asset['kind']=='material':
                        meta=read_json(path);mat=blender_ops.material(meta['materials'][0],Path(path).parent)
                        mat['hb_game']=asset['game'];mat['hb_asset_id']=asset['id'];mat.use_fake_user=True;mat.asset_mark()
                        # Loading a material never changes an already placed object.
                        loaded_materials+=1
                    else:
                        # Include objects created by an importer even if it fails midway.
                        before=set(context.scene.objects)
                        try:obj=blender_ops.place(asset,path,cfg,location=origin)
                        finally:created.extend(o for o in context.scene.objects if o not in before)
                        if preview_matrix is not None:
                            obj.data=obj.data.copy();map_scene.center_mesh_origin(obj.data);obj.matrix_world=preview_matrix
                        obj.asset_mark();context.view_layer.update()
                    yield
                bpy.ops.object.select_all(action='DESELECT')
                for obj in created:obj.select_set(True)
                if created:context.view_layer.objects.active=created[-1]
                elif target:target.select_set(True);context.view_layer.objects.active=target
            except BaseException:
                for obj in created:
                    if obj.name in bpy.data.objects:bpy.data.objects.remove(obj,do_unlink=True)
                if materials and target:
                    target.data.materials.clear()
                    for mat in old_materials:target.data.materials.append(mat)
                    target.active_material_index=old_slot
                for obj in previous_selection:
                    if obj.name in context.view_layer.objects:obj.select_set(True)
                if previous_active and previous_active.name in context.view_layer.objects:context.view_layer.objects.active=previous_active
                raise
            _message='Placed '+str(len(created))+' object(s); loaded '+str(loaded_materials)+' material(s).'
            if failures:
                _error='Skipped '+str(len(failures))+' asset(s):\n\n'+'\n\n'.join(failures)
                text=bpy.data.texts.get('HaloBridge diagnostics') or bpy.data.texts.new('HaloBridge diagnostics');text.clear();text.write(_error)
                _message+=' Skipped '+str(len(failures))+'. Open report for details.'
        start(context,extract_all,done,'Preparing '+str(len(assets))+' checked asset(s)…',undo=True)

class HBImportMapScene(Guard,bpy.types.Operator):
    bl_idname='halo_bridge.import_map_scene';bl_label='Import entire .map'
    bl_description='Reconstruct the map terrain and static object placements at original positions, rotations and scales in a separate collection. Prepare exports the current meshes as static geometry with generated collision; original gameplay is not reconstructed'
    def run(self,context):
        cfg=config(context);name=context.scene.halo_bridge.map_name
        stop_preview(context)
        def progress(message):
            global _message
            _message=message
        def done(manifest):
            global _message,_error
            data=read_json(manifest)
            yield from map_scene.import_scene(context,manifest,progress)
            context.scene.halo_bridge.sky_scenario=data['scenario']
            warnings=data.get('warnings',[])
            report='Original map layout: '+data['scenario']+'\n\n'
            report+='Terrain BSPs: '+str(data['decoded_bsps'])+'/'+str(data['expected_bsps'])+'\n'
            report+='\n'.join(k+': '+str(v) for k,v in data.get('counts',{}).items())
            report+='\n\nImport scope:\n'+'\n'.join(data.get('limitations',[]))
            if warnings:report+='\n\nMissing or approximated elements:\n'+'\n'.join(warnings)
            text=bpy.data.texts.get('HaloBridge map import report') or bpy.data.texts.new('HaloBridge map import report');text.clear();text.write(report)
            _message='Imported original map base: '+str(len(data['placements']))+' mesh placements; terrain BSPs '+str(data['decoded_bsps'])+'/'+str(data['expected_bsps'])+'. '+str(len(warnings))+' warnings. See map import report.'
            if data['decoded_bsps']!=data['expected_bsps']:
                issues=['Incomplete import: '+str(data['decoded_bsps'])+'/'+str(data['expected_bsps'])+' terrain BSPs. This scene is not ready for Sapien preparation.']
                issues.extend(w for w in warnings if w.startswith('BSP '))
                record_failure(ValidationError(issues,'Map extraction'))
                bpy.ops.halo_bridge.report_diagnostics()
        start(context,lambda cancel:jobs.extract_map_scene(cfg,name,cancel,progress),done,'Reading original map layout…')
        _task.application_budget=.05

class HBPreviewToggle(Guard,bpy.types.Operator):
    bl_idname='halo_bridge.toggle_preview';bl_label='Preview On / Off';bl_options={'REGISTER','UNDO'}
    bl_description='Turn live previews on or off: selecting another asset updates the preview; turning off removes it, even while loading'
    def execute(self,context):
        global _message
        if context.scene.halo_bridge.preview_enabled or preview_active(context):
            stop_preview(context)
            _message='Preview off. Ready to place assets.'
            return {'FINISHED'}
        return Guard.execute(self,context)
    def run(self,context):
        context.scene.halo_bridge.preview_enabled=True
        selection_changed(context.scene.halo_bridge,context)

class HBRepairMap(Guard,bpy.types.Operator):
    bl_idname='halo_bridge.repair_map';bl_label='(Experimental) Repair incomplete map import'
    bl_description='Retry the selected map extraction and add newly recovered pieces, preserving existing edits and intentional deletions'
    def run(self,context):
        cfg=config(context);name=context.scene.halo_bridge.map_name
        if not any(o.get('hb_map_reference') for o in context.scene.objects):raise RuntimeError('Import a map first.')
        def progress(message):
            global _message
            _message=message
        def done(manifest):
            yield from map_scene.repair_scene(context,manifest,progress)
        start(context,lambda cancel:jobs.extract_map_scene(cfg,name,cancel,progress),done,'Retrying incomplete map extraction...')

class HBGround(Guard,bpy.types.Operator):
    bl_idname='halo_bridge.ground';bl_label='Create starter level shell template';bl_options={'REGISTER','UNDO'}
    bl_description='Add a closed test-level shell with a ground surface and sky boundaries as a starting point for your map'
    def run(self,context):
        cfg=export_config(context)
        mp=Path(cfg['maps'])/'010_jungle.map'
        if not mp.is_file():raise RuntimeError('The textured starter template needs 010_jungle.map. Check the Halo 3 maps folder.')
        asset=indexed_assets(dict(map=str(mp),assets=[dict(name='Jungle ground',tag='levels\\solo\\010_jungle\\shaders\\terrain\\terrain_000',kind='material',section=-1)]))[0]
        def done(path):
            global _message
            blender_ops.starter_ground(cfg,path)
            _message='Created textured starter shell. Material Preview is enabled.'
        start(context,lambda cancel:jobs.extract(asset,cfg,cancel),done,'Loading starter shell ground texture…')

class HBScanShaders(Guard,bpy.types.Operator):
    bl_idname='halo_bridge.scan_shaders';bl_label='Scan existing shaders'
    bl_description='List existing .shader tags from the selected Editing Kit; no new shaders are created'
    def run(self,context):
        global _message
        _message='Found '+str(shader_choices.scan(games.destination(context.scene.halo_bridge).kit))+' existing shaders.'
        context.scene.halo_bridge.shader_level='ALL'
        context.scene.halo_bridge.shader_choice='NONE'

class HBChooseShader(bpy.types.Operator):
    bl_idname='halo_bridge.choose_shader';bl_label='Search existing shaders'
    bl_description='Search shaders in the selected level or category; then click Assign existing Halo shader to apply your choice'
    bl_property='choice'
    choice:EnumProperty(items=shader_choices.search_items)
    def invoke(self,context,event):
        context.window_manager.invoke_search_popup(self)
        return {'RUNNING_MODAL'}
    def execute(self,context):
        context.scene.halo_bridge.shader_choice=self.choice
        return {'FINISHED'}

class HBShader(Guard,bpy.types.Operator):
    bl_idname='halo_bridge.shader';bl_label='Assign existing Halo shader';bl_options={'REGISTER','UNDO'}
    bl_description='Link the active material to the existing Halo shader tag entered above so the level uses that shader in game'
    def run(self,context):
        from .catalog import material_name
        obj=context.active_object
        if not obj or not obj.active_material:raise RuntimeError('Select an object with an active material.')
        settings=context.scene.halo_bridge
        tag=(settings.shader_path if settings.shader_manual else settings.shader_choice).replace('/','\\')
        if tag=='NONE':raise RuntimeError('Scan existing shaders and choose one first.')
        export_review.shader_file(games.destination(settings).kit,tag);obj.active_material['hb_shader']=tag
        obj.active_material['hb_shader_game']=settings.export_target

_vehicle_items_cache={}

def vehicle_items(operator,context):
    obj=context.active_object if context else None
    raw=obj.get('hb_vehicle_matches','[]') if obj else '[]'
    if raw not in _vehicle_items_cache:
        rows=json.loads(raw)
        _vehicle_items_cache[raw]=[(r['vehicle'],r['vehicle'].rsplit('\\',1)[-1],r['vehicle'],i) for i,r in enumerate(rows)]
    return _vehicle_items_cache[raw]

class HBFindVehicle(Guard,bpy.types.Operator):
    bl_idname='halo_bridge.find_vehicle';bl_label='Find matching original vehicles'
    bl_description='Find installed Halo 3 vehicle tags whose render model matches the selected imported object; select a variant afterward'
    def run(self,context):
        obj=context.active_object
        if not obj or obj.type!='MESH':raise RuntimeError('Select the imported vehicle model in the 3D View first.')
        vehicles.validate_preview(obj);cfg=export_config(context)
        name=obj.name;source=obj['hb_source_tag'];directory=Path(cfg['cache'])/'jobs';out=directory/('vehicle-matches-'+str(time.time_ns())+'.json')
        def done(result):
            global _message
            target=bpy.data.objects.get(name)
            if target!=obj or target.get('hb_source_tag')!=source:raise RuntimeError('The selected object changed; find matching vehicles again.')
            matches=result.get('matches',[]);target['hb_vehicle_matches']=json.dumps(matches)
            if not matches:raise RuntimeError('No installed Halo 3 vehicle tag references this model. Check that the Editing Kit tags are extracted.')
            _message='Found '+str(len(matches))+' matching vehicle tag(s). Choose the original vehicle variant under Selected Asset.'
        start(context,lambda cancel:jobs.helper('tags',dict(operation='resolve_vehicles',kit=cfg['kit'],sources=[source],output=str(out)),directory,cancel),done,'Finding matching Halo 3 vehicle tags...')

class HBChooseVehicle(Guard,bpy.types.Operator):
    bl_idname='halo_bridge.choose_vehicle';bl_label='Use original Halo 3 vehicle'
    bl_description='Export the selected object as an original Halo 3 vehicle placement, keeping its game collision and behavior instead of static mesh geometry'
    bl_property='choice';bl_options={'REGISTER','UNDO'}
    choice:EnumProperty(items=vehicle_items)
    target_name:StringProperty(options={'HIDDEN','SKIP_SAVE'})
    def invoke(self,context,event):
        if not context.active_object:return {'CANCELLED'}
        self.target_name=context.active_object.name
        context.window_manager.invoke_search_popup(self);return {'RUNNING_MODAL'}
    def run(self,context):
        global _message
        obj=context.active_object
        if not obj or (self.target_name and obj.name!=self.target_name):raise RuntimeError('Select the same object and choose its vehicle again.')
        vehicles.validate_preview(obj)
        rows=json.loads(obj.get('hb_vehicle_matches','[]'))
        if not any(r['vehicle']==self.choice and r['render']==obj['hb_source_tag'] for r in rows):raise RuntimeError('Find matching vehicles for this model first.')
        obj['hb_vehicle_tag']=self.choice;obj['hb_vehicle_render']=obj['hb_source_tag']
        if not obj.get('hb_vehicle_id'):obj['hb_vehicle_id']=blender_ops.new_id()
        _message=obj.name+' will export as an original Halo 3 vehicle: '+self.choice

class HBVehicleStatic(bpy.types.Operator):
    bl_idname='halo_bridge.vehicle_static';bl_label='Use static mesh instead';bl_options={'REGISTER','UNDO'}
    bl_description='Export the selected object as static geometry again; vertex limits apply and vehicle behavior is not included'
    def execute(self,context):
        obj=context.active_object
        if obj and 'hb_vehicle_tag' in obj:del obj['hb_vehicle_tag']
        return {'FINISHED'}

class HBChooseSky(bpy.types.Operator):
    bl_idname='halo_bridge.choose_sky';bl_label='Choose sky from map'
    bl_description='Search installed map skies; the selected scenario is shown below and saved with the scene'
    bl_property='choice'
    choice:EnumProperty(items=lambda self,context:skies.items(context.scene.halo_bridge,context) if context else [])
    def invoke(self,context,event):
        context.window_manager.invoke_search_popup(self)
        return {'RUNNING_MODAL'}
    def execute(self,context):
        s=context.scene.halo_bridge
        s.sky_choice=self.choice;s.sky_selected=self.choice
        s.sky_scenario=self.choice if self.choice!='AUTO' else 'levels\\multi\\deadlock\\deadlock'
        return {'FINISHED'}

class HBRefreshSkies(Guard,bpy.types.Operator):
    bl_idname='halo_bridge.refresh_skies';bl_label='Find map skies'
    bl_description='Scan installed Editing Kit scenarios for usable sky references; includes maps beyond the current asset index'
    def run(self,context):
        cfg=export_config(context);directory=Path(cfg['cache'])/'jobs';out=directory/('skies-'+str(time.time_ns())+'.json')
        def done(result):
            global _message
            result['kit']=cfg['kit']
            write_json(Path(cfg['cache'])/'sky-catalogue.json',result);skies.invalidate()
            _message='Found skies from '+str(len(result['items']))+' maps. Select one in Sky from map. Use Generate Test Lighting for Sapien Level during preparation.'
        start(context,lambda cancel:jobs.helper('tags',dict(operation='list_skies',kit=cfg['kit'],output=str(out)),directory,cancel),done,'Finding skies in Editing Kit maps...')

_prepare_running=False
_prepare_status='Ready to prepare the current scene.'
_prepare_activity=None
_activity_text_stamps={}


def sync_activity_texts(force=False):
    if not _prepare_activity:return
    visible={area.spaces.active.text.name for screen in bpy.data.screens for area in screen.areas
             if area.type=='TEXT_EDITOR' and area.spaces.active.text}
    for name,path in (('HaloBridge preparation activity',str(_prepare_activity.path)),
                      ('HaloBridge compiler output',_prepare_activity.current_log)):
        if not path or (not force and name not in visible):continue
        try:
            source=Path(path);stamp=(path,source.stat().st_mtime_ns,source.stat().st_size)
            if _activity_text_stamps.get(name)==stamp:continue
            with source.open('rb') as stream:
                stream.seek(max(0,stamp[2]-1048576));data=stream.read().decode('utf-8',errors='replace')
            text=bpy.data.texts.get(name) or bpy.data.texts.new(name)
            text.clear();text.write('Live log (refreshes while preparing). Full file: '+path+'\n\n'+data)
            _activity_text_stamps[name]=stamp
        except OSError:pass


class HBActivityLog(bpy.types.Operator):
    bl_idname='halo_bridge.activity_log';bl_label='Open preparation activity log'
    bl_description='Show timestamped preparation events or raw compiler output in a live Text Editor; full logs are also saved in the HaloBridge jobs folder'
    raw:BoolProperty(default=False)
    def execute(self,context):
        if not _prepare_activity:return {'CANCELLED'}
        sync_activity_texts(force=True)
        name='HaloBridge compiler output' if self.raw else 'HaloBridge preparation activity'
        text=bpy.data.texts.get(name)
        if not text:return {'CANCELLED'}
        context.area.type='TEXT_EDITOR';context.area.spaces.active.text=text
        return {'FINISHED'}


def prepare_status(message,running=False):
    global _prepare_status,_prepare_running
    _prepare_status=message;_prepare_running=running
    if _prepare_activity:
        _prepare_activity.ended=None if running else time.monotonic()
        if not running:_prepare_activity.event(message)


def prepare_button_text():
    return '(LOADING...PLEASE WAIT) Preparing current scene for sapien' if _prepare_running else 'Prepare current scene for sapien'


_pending_prepare_warning=None

def preparation_warnings(context,cfg):
    vehicle_placements=vehicles.plan(context.scene,cfg)
    warnings=geometry_export.warnings(context.scene)
    if vehicle_placements:warnings.append(str(len(vehicle_placements))+' original Halo 3 vehicle(s) will be placed using their game tags. Their original appearance, physics and behavior replace the Blender preview; Blender material changes are not exported for these vehicles.')
    selected=[o for o in geometry_export.objects(context.scene) if not geometry_export.is_sky(o)]
    issues,_,_=export_review.inspect(selected,cfg)
    if issues:
        lines=export_review.messages(issues)
        report=bpy.data.texts.get('HaloBridge export exclusions') or bpy.data.texts.new('HaloBridge export exclusions')
        report.clear();report.write('Objects with export problems (entire objects omitted only if skipping is enabled):\n\n'+'\n\n'.join(lines))
        if not cfg.get('skip_invalid'):
            raise ValidationError(lines+['Fix these objects, or enable Skip objects with export problems and prepare again to review the exclusions.'])
        if len(issues)==len(selected):raise ValidationError(lines+['No exportable objects remain. At least one valid mesh is required.'])
        warnings.extend('WILL NOT EXPORT — '+line for line in lines)
    return warnings

def draw_review_actions(layout,token,enabled=True):
    # Blender's native operator buttons expose alert/pressed states, not RGB fills.
    # Keep the affirmative action distinct without changing the user's global theme.
    row=layout.row();row.enabled=enabled;row.alert=False;row.scale_y=1.3
    op=row.operator('halo_bridge.confirm_prepare',text='Continue with warnings',icon='CHECKMARK',depress=True)
    op.token=token;op.accept=True
    row=layout.row();row.enabled=enabled;row.alert=True;row.scale_y=1.15
    op=row.operator('halo_bridge.confirm_prepare',text='Cancel',icon='CANCEL')
    op.token=token;op.accept=False


def confirm_map_warnings(context,cfg,error):
    global _pending_prepare_warning,_error,_message,_reported_issues
    # Reviewable limitations are not failed builds. Keep the decision available
    # in the sidebar even when Blender dismisses the transient popup.
    _error=''
    _reported_issues=[]
    _message='Preparation needs confirmation. Choose Continue with warnings or Cancel above the Prepare button.'
    token=str(time.time_ns())
    _pending_prepare_warning=dict(token=token,scene=context.scene.as_pointer(),config=dict(cfg),issues=list(error.issues))
    def draw(menu,ctx):
        layout=menu.layout
        layout.label(text=str(len(error.issues))+' warning(s) found. Continue exporting current geometry?',icon='ERROR')
        layout.label(text='Edits and deletions are exported. Original map geometry is never substituted.')
        layout.label(text='Required-file and compiler errors may still prevent completion.')
        layout.separator()
        for issue in error.issues[:8]:
            for line in textwrap.wrap(issue,width=95):layout.label(text=line)
        if len(error.issues)>8:layout.label(text='All '+str(len(error.issues))+' warnings are above the Prepare button.')
        layout.separator()
        draw_review_actions(layout,token)
    context.window_manager.popup_menu(draw,title='Prepare for Sapien: review warnings',icon='ERROR')

class HBConfirmPrepare(Guard,bpy.types.Operator):
    bl_idname='halo_bridge.confirm_prepare';bl_label='Continue with warnings'
    bl_description='Continue exporting current meshes after reviewing limitations, or cancel without preparing'
    bl_options={'INTERNAL'}
    token:StringProperty(options={'HIDDEN','SKIP_SAVE'})
    accept:BoolProperty(default=False,options={'HIDDEN','SKIP_SAVE'})
    def run(self,context):
        global _pending_prepare_warning,_message
        pending=_pending_prepare_warning
        if not pending or pending['token']!=self.token:raise RuntimeError('This confirmation expired. Prepare again.')
        _pending_prepare_warning=None
        if not self.accept:
            _message='Preparation cancelled. No level files were written.';prepare_status(_message);return {'CANCELLED'}
        if pending['scene']!=context.scene.as_pointer() or pending['config']!=export_config(context):
            raise RuntimeError('The scene or setup changed. Prepare again to review current warnings.')
        current=preparation_warnings(context,pending['config'])
        if current!=pending['issues']:
            raise RuntimeError('The detected issues changed. Prepare again to review the current list.')
        # One error boundary: nested bpy operators turn the detailed validation
        # error into a generic RuntimeError and overwrite its diagnostic report.
        return HBPrepare.run(self,context,warnings_accepted=True)

class HBPrepare(Guard,bpy.types.Operator):
    bl_idname='halo_bridge.prepare';bl_label='Prepare current scene for sapien'
    bl_description='Compile current meshes, edits and modifiers as static geometry with generated surface collision; optionally build draft lighting, then test in Sapien'
    warnings_accepted:BoolProperty(default=False,options={'HIDDEN','SKIP_SAVE'})
    def invoke(self,context,event):
        if _task or _prepare_running:return {'CANCELLED'}
        prepare_status('Starting scene preparation...',True)
        scene=context.scene.as_pointer()
        for area in context.screen.areas:area.tag_redraw()
        def begin():
            if bpy.context.scene.as_pointer()!=scene:
                prepare_status('Preparation cancelled: active scene changed.');return
            bpy.ops.halo_bridge.prepare('EXEC_DEFAULT')
        bpy.app.timers.register(begin,first_interval=.15)
        return {'FINISHED'}
    def run(self,context,warnings_accepted=None):
        if warnings_accepted is None:warnings_accepted=self.warnings_accepted
        prepare_status('Validating current scene...',True)
        reconcile_preview_copies(context)
        cfg=export_config(context)
        safe_level(cfg['level']);build.ensure_sapien_closed()
        out=Path(cfg['cache'])/'projects'/cfg['level']/'export'/('level_'+str(__import__('time').time_ns())+'.ASS');out.parent.mkdir(parents=True,exist_ok=True)
        last_redraw=[0.0]
        source_scene=context.scene.as_pointer()
        def report_progress(message):
            global _message
            _message=message;prepare_status(message,True)
            # Background compiler callbacks only update plain strings. Blender RNA
            # and redraw requests are restricted to main-thread scene conversion.
            if threading.current_thread() is threading.main_thread() and not bpy.app.background:
                now=time.monotonic()
                if now-last_redraw[0]>.25 and bpy.context.scene.as_pointer()==source_scene:
                    last_redraw[0]=now
                    for area in context.screen.areas:area.tag_redraw()
                    if bpy.ops.wm.redraw_timer.poll():bpy.ops.wm.redraw_timer(type='DRAW_WIN_SWAP',iterations=1)
        def done(path):
            global _message
            _message='Ready: '+path;prepare_status('Finished. Level prepared for Sapien.')
            issues=cfg.get('compiler_warnings',[])
            if issues:
                _message+='\nPrepared with '+str(len(issues))+' geometry warning(s). Open the preparation report for affected objects.'
                prepare_status('Finished with '+str(len(issues))+' geometry warning(s). Review the preparation report before playtesting.')
                report=bpy.data.texts.get('HaloBridge preparation report')
                if report:report.write('\n\nCompiler geometry warnings (level built, but these surfaces need attention):\n'+'\n'.join(issues))
            if context.scene.halo_bridge.open_sapien:open_sapien(cfg)
        warnings=preparation_warnings(context,cfg)
        if warnings and not warnings_accepted:
            prepare_status('Waiting for confirmation: review preparation warnings.')
            confirm_map_warnings(context,cfg,ValidationError(warnings,'Geometry export warnings'));return
        if context.scene.halo_bridge.sky_selected=='AUTO' and context.scene.halo_bridge.sky_choice in ('AUTO',''):
            manifests={o.get('hb_map_manifest') for o in geometry_export.objects(context.scene) if o.get('hb_map_manifest')}
            sources={read_json(p,{}).get('scenario','') for p in manifests}
            if len(sources)==1:
                candidate=next(iter(sources))
                if candidate and (Path(cfg['kit'])/'tags'/(candidate+'.scenario')).is_file():cfg['sky_scenario']=candidate
        global _prepare_activity
        _prepare_activity=PreparationActivity(Path(cfg['cache'])/'jobs'/('preparation-'+str(time.time_ns())+'.log'),report_progress)
        progress=_prepare_activity
        progress.stage(1,'Export current scene meshes')
        placements=geometry_export.export(cfg,out,progress=progress)
        report=bpy.data.texts.get('HaloBridge preparation report') or bpy.data.texts.new('HaloBridge preparation report')
        report.clear();report.write('Current Blender meshes exported. Edits, transforms, modifiers and deletions are included. Collision is generated from current surfaces.\nStructure geometry: '+cfg.get('structure_source','current scene')+'\nSky: '+cfg.get('sky_scenario','default')+'\n\n'+'\n'.join(warnings))
        start(context,lambda cancel:build.prepare(cfg,out,placements,cancel,progress),done,'Compiling current scene geometry...')

        _task.is_prepare=True


def open_sapien(cfg):
    build.ensure_sapien_closed()
    level=safe_level(cfg['level']);tag=Path(cfg['kit'])/'tags/levels/multi'/level/(level+'.scenario')
    if not tag.is_file():raise RuntimeError('Prepare this level successfully before opening Sapien.')
    process=subprocess.Popen([str(Path(cfg['kit'])/'sapien.exe'),str(tag)],cwd=cfg['kit'])
    def verify_launch():
        global _message,_error
        code=process.poll()
        if code is not None:
            _message='Sapien closed during startup. The prepared level is saved.'
            _error='Sapien exited with code '+str(code)+'. Open '+str(tag)+' from Sapien, started in '+cfg['kit']+'.'
            text=bpy.data.texts.get('HaloBridge diagnostics') or bpy.data.texts.new('HaloBridge diagnostics');text.clear();text.write(_error)
        return None
    bpy.app.timers.register(verify_launch,first_interval=5)

class HBOpen(Guard,bpy.types.Operator):
    bl_idname='halo_bridge.open';bl_label='Open in Sapien'
    bl_description='Launch Sapien with the successfully prepared scenario for this output level; prepare the level first'
    def run(self,context):open_sapien(export_config(context))

class HBResolve(Guard,bpy.types.Operator):
    bl_idname='halo_bridge.resolve';bl_label='Resolve conflict: use Blender'
    bl_description='Confirm that the next export may replace conflicting Sapien edits to Blender-owned placements; independently added Sapien content is kept'
    def invoke(self,context,event):return context.window_manager.invoke_props_dialog(self,width=440)
    def draw(self,context):
        self.layout.label(text='Next export will replace Sapien edits to Blender-owned placements.')
        self.layout.label(text='Sapien-owned objects and gameplay settings will be kept.')
    def run(self,context):
        cfg=export_config(context);build.ensure_sapien_closed();safe_level(cfg['level'])
        path=Path(cfg['cache'])/'projects'/cfg['level']/'manifest.json';manifest=read_json(path)
        if not manifest:raise RuntimeError('No previously successful export for this level.')
        def done(result):
            global _message
            write_json(path.with_suffix('.before-resolution.json'),manifest)
            manifest['state']=result['state'];write_json(path,manifest)
            _message='Conflict resolved explicitly. Prepare for Sapien to use Blender placements.'
        start(context,lambda cancel:jobs.helper('tags',dict(operation='inspect',kit=cfg['kit'],scenario=manifest['scenario'],output=str(Path(cfg['cache'])/'jobs/resolve.json')),Path(cfg['cache'])/'jobs',cancel),done,'Reading current placement state…')

class HBCancel(bpy.types.Operator):
    bl_idname='halo_bridge.cancel';bl_label='Cancel job'
    bl_description='Request cancellation of the current background job; preview loading stops and level builds restore the previous successful output'
    def execute(self,context):
        if _task and getattr(_task,'preview_generation',None) is not None:stop_preview(context)
        if _task:_task.cancel.set()
        return {'FINISHED'}

class HBReportDiagnostics(bpy.types.Operator):
    bl_idname='halo_bridge.report_diagnostics';bl_label='Report HaloBridge issues'
    bl_description='Write all detected issues to Blender Info and preserve the full diagnostic report'
    bl_options={'INTERNAL'}
    def execute(self,context):
        for issue in globals().get('_reported_issues',[]):self.report({'WARNING'},issue)
        self.report({'WARNING'},_message)
        return {'FINISHED'}

class HBDiagnostics(bpy.types.Operator):
    bl_idname='halo_bridge.diagnostics';bl_label='Open diagnostic report'
    bl_description='Show the latest HaloBridge error details in this area using Blender\'s Text Editor'
    text_name:StringProperty(default='HaloBridge diagnostics')
    def execute(self,context):
        text=bpy.data.texts.get(self.text_name) or bpy.data.texts.new(self.text_name)
        context.area.type='TEXT_EDITOR';context.area.spaces.active.text=text
        text.cursor_set(0,character=0)
        region=next((r for r in context.area.regions if r.type=='WINDOW'),None)
        if region:
            with context.temp_override(area=context.area,region=region):
                bpy.ops.text.move(type='FILE_TOP')
                bpy.ops.text.scroll(lines=-1000000)
        return {'FINISHED'}

_icon_token=None
_icons={}
def asset_icons():
    global _icon_token,_icons
    if _task:return {}
    token=(len(bpy.data.objects),len(bpy.data.materials))
    if token!=_icon_token:
        _icons={}
        for pool in (bpy.data.objects,bpy.data.materials):
            for obj in pool:
                asset_id=obj.get('hb_asset_id')
                if asset_id and obj.preview:_icons[asset_id]=obj.preview.icon_id
        _icon_token=token
    return _icons

class HB_UL_assets(bpy.types.UIList):
    def draw_item(self,context,layout,data,item,icon,active_data,active_propname,index):
        icon_id=asset_icons().get(item.asset_id,0)
        layout.prop(item,'checked',text='')
        layout.label(text=item.name,icon_value=icon_id,icon='NONE' if icon_id else ('MATERIAL' if item.kind=='material' else 'OUTLINER_OB_MESH'))
        if item.kind=='material':layout.label(text='Material')
        if item.kind=='model':layout.label(text='Static model',icon='INFO')
        row=layout.row();row.enabled=_task is None
        op=row.operator('halo_bridge.list_action',text='',icon='HIDE_ON' if item.hidden else 'HIDE_OFF',emboss=False)
        op.action='UNHIDE' if item.hidden else 'HIDE';op.asset_id=item.asset_id
    def filter_items(self,context,data,propname):
        s=context.scene.halo_bridge;items=getattr(data,propname)
        visible=visibility_predicate(s)
        return [self.bitflag_filter_item if visible(i) else 0 for i in items],[]

class HBSelectCollisionIssues(Guard,bpy.types.Operator):
    bl_idname='halo_bridge.select_collision_issues';bl_label='Select assets missing export collision'
    bl_description='Select placed assets that lack an exportable collision source, so you can replace or remove them; scene geometry is not changed'
    def run(self,context):
        global _message
        objects=[o for o in context.view_layer.objects if o.type=='MESH' and blender_ops.collision_issue(o)]
        if not objects:raise RuntimeError('No placed assets with missing export collision were found.')
        bpy.ops.object.select_all(action='DESELECT')
        selected_objects=[]
        for obj in objects:
            if obj.visible_get() and not obj.hide_select:obj.select_set(True);selected_objects.append(obj)
        if selected_objects:context.view_layer.objects.active=selected_objects[0]
        _message=f'Selected {len(selected_objects)} of {len(objects)} assets missing export collision. Hidden or selection-locked objects remain unselected. Choose a matching scenery or instance and use Swap selected object.'

def draw_messages(layout,context,popover=False):
    width=48 if popover else max(24,min(85,int((context.region.width if context.region else 360)/7)-5))
    notice=layout.box()
    heading=notice.row();heading.alert=bool(_error or _pending_prepare_warning);heading.scale_y=1.3
    heading.label(text='ACTION REQUIRED' if _error else ('REVIEW PREPARATION WARNINGS' if _pending_prepare_warning else 'Working…' if _task else 'Status'),icon='ERROR' if _error or _pending_prepare_warning else 'INFO')
    body=notice.column();body.alert=bool(_error)
    for paragraph in _message.splitlines():
        for line in textwrap.wrap(paragraph,width=width) or ['']:body.label(text=line)
    if _task:
        row=notice.row();row.alert=True;row.operator('halo_bridge.cancel',icon='CANCEL')
    if _error:
        row=notice.row();row.alert=True;row.operator('halo_bridge.diagnostics',icon='ERROR')
        if 'CONFLICT' in _error:
            row=notice.row();row.alert=True;row.scale_y=1.4
            row.operator('halo_bridge.resolve',text='Resolve Conflict: Use Blender',icon='FILE_REFRESH')
    if bpy.data.texts.get('HaloBridge map import report'):
        layout.operator('halo_bridge.diagnostics',text='Open map import report',icon='INFO').text_name='HaloBridge map import report'
    if bpy.data.texts.get('HaloBridge preparation report'):
        layout.operator('halo_bridge.diagnostics',text='Open preparation report',icon='INFO').text_name='HaloBridge preparation report'
    if bpy.data.texts.get('HaloBridge original copy report'):
        layout.operator('halo_bridge.diagnostics',text='Open original copy report',icon='INFO').text_name='HaloBridge original copy report'

class HBMessages(bpy.types.Panel):
    bl_label='HaloBridge Warnings and Messages';bl_idname='HB_PT_messages';bl_space_type='VIEW_3D';bl_region_type='UI';bl_category='HaloBridge';bl_order=-10
    def draw(self,context):draw_messages(self.layout,context)

class HBMessagesPopover(bpy.types.Panel):
    bl_label='HaloBridge Warnings and Messages';bl_idname='HB_PT_messages_popover';bl_space_type='VIEW_3D';bl_region_type='HEADER';bl_ui_units_x=28
    def draw(self,context):draw_messages(self.layout,context,popover=True)

def draw_message_header(self,context):
    row=self.layout.row(align=True)
    row.alert=bool(_error or _pending_prepare_warning)
    row.popover(panel='HB_PT_messages_popover',text='HaloBridge Warnings and Messages',icon='ERROR' if _error else 'INFO')
    row.label(text=textwrap.shorten(_message.replace('\n',' '),width=65,placeholder='…'))

class HBCenterMapOrigins(Guard,bpy.types.Operator):
    bl_idname='halo_bridge.center_map_origins';bl_label='Origin to Geometry - all scene meshes';bl_options={'REGISTER','UNDO'}
    bl_description='Run Blender Origin to Geometry (Median Center) on every mesh in this scene, including authored, hidden and previously centered meshes'
    def run(self,context):
        global _message
        if context.mode!='OBJECT':raise RuntimeError('Switch to Object Mode first.')
        count=map_scene.center_existing_origins(context)
        _message=f'Set Origin to Geometry for {count} scene meshes.'

class HBPanel(bpy.types.Panel):
    bl_label='HaloBridge';bl_idname='HB_PT_main';bl_space_type='VIEW_3D';bl_region_type='UI';bl_category='HaloBridge'
    def draw(self,context):
        l=self.layout;s=context.scene.halo_bridge
        row=l.row();row.enabled=_task is None;row.prop(s,'game')
        l.label(text='Folders and Setup',icon='PREFERENCES')
        box=l.box()
        for n in ('kit','maps'):box.prop(s,n,text=games.GAMES[s.game]['label']+(' Editing Kit' if n=='kit' else ' .map Files'))
        row=box.row();row.operator('halo_bridge.detect',depress=True);row.operator('halo_bridge.check_setup')
        row=box.row();row.enabled=_task is None;row.operator('halo_bridge.ground',depress=True)
        box.label(text='Choose .map file')
        row=box.row(align=True);row.enabled=_task is None
        row.prop(s,'map_name',text='')
        row.operator('halo_bridge.choose_map',text='',icon='DOWNARROW_HLT')
        box.operator('halo_bridge.index',depress=True)
        row=box.row();row.enabled=_task is None
        row.operator('halo_bridge.import_map_scene',depress=True)
        box.operator('halo_bridge.repair_map')
        box.operator('halo_bridge.center_map_origins')
        box.prop(s,'advanced')
        if s.advanced:
            box.prop(s,'cache',text='Storage location')
            box.label(text='Existing projects need their original records.')
        l.prop(s,'follow_outliner')
        row=l.row()
        for redo,icon in ((False,'LOOP_BACK'),(True,'LOOP_FORWARDS')):
            control=row.row();control.enabled=_task is None and history_available(redo)
            control.operator('halo_bridge.list_history',text='Redo' if redo else 'Undo',icon=icon).redo=redo
        l.prop(s,'asset_tab',expand=True)
        l.prop(s,'filter_level')
        l.label(text='Asset List',icon='ASSET_MANAGER')
        grid=l.grid_flow(columns=3,align=True)
        for category in ('vegetation','rocks','structures','water','materials'):grid.prop(s,'show_'+category,toggle=True)
        search=l.box().row(align=True)
        search.prop(s,'search',text='Search Assets',icon='VIEWZOOM')
        clear=search.row(align=True);clear.enabled=bool(s.search)
        clear.operator('halo_bridge.clear_search',text='',icon='X')
        if s.asset_tab=='HIDDEN' and not any(a.hidden for a in s.assets):
            box=l.box();box.separator(factor=2)
            for line in ('Your Hidden Assets will show up','here when you [Hide] them.'):
                row=box.row();row.alignment='CENTER';row.label(text=line)
            box.separator(factor=2)
        else:l.template_list('HB_UL_assets','',s,'assets',s,'active_index',rows=7)
        on=s.preview_enabled
        toggle=l.row();toggle.enabled=on or _task is None
        toggle.operator('halo_bridge.toggle_preview',text='Preview Mode: ON' if on else 'Preview Mode: OFF',depress=on,icon='SEQUENCE_COLOR_04' if on else 'SEQUENCE_COLOR_01')
        count=len(checked_ids(context))
        row=l.row(align=True);row.operator('halo_bridge.check_assets',text='Select all').check=True
        row.operator('halo_bridge.check_assets',text='Clear checks').check=False;row.label(text=str(count)+' checked')
        row=l.row();row.enabled=_task is None and count>0
        op=row.operator('halo_bridge.list_action',text='Unhide' if s.asset_tab=='HIDDEN' else 'Hide',icon='HIDE_ON' if s.asset_tab=='HIDDEN' else 'HIDE_OFF')
        op.action='UNHIDE' if s.asset_tab=='HIDDEN' else 'HIDE'
        row=l.row();row.enabled=_task is None and count>0
        row.operator('halo_bridge.list_action',text='Delete checked from list',icon='TRASH').action='DELETE'
        row=l.row();place=row.row();place.enabled=_task is None;place.operator('halo_bridge.place',depress=on,icon='ADD')
        root=l;l=root.box();l.label(text='Selected Asset',icon='OBJECT_DATA')
        try:
            asset=selected(context)
            if asset['kind']=='material':
                l.label(text='Material only: contains no geometry.',icon='MATERIAL')
                apply=l.row();apply.enabled=_task is None and context.active_object is not None and context.active_object.type=='MESH'
                apply.operator('halo_bridge.place',text='Apply material to selected object').apply_material=True
            status='Exports the current mesh as static geometry with generated collision.' if asset['kind']=='model' else asset.get('status','')
            for line in textwrap.wrap(status,width=44):l.label(text=line)
            l.label(text='Map: '+asset['level'])
            if asset.get('section',-1)>=0:l.label(text=asset['tag'].rsplit('\\',1)[-1]+' / section '+str(asset['section']))
            icon_id=asset_icons().get(asset['id'],0)
            if icon_id:l.template_icon(icon_value=icon_id,scale=6)
        except Exception:pass
        try:_,reason=replacement_target(context,selected(context))
        except Exception:reason='Choose an asset in the list to use as the replacement.'
        row=l.row();row.enabled=_task is None and not reason
        op=row.operator('halo_bridge.place',text='Swap selected object(s) to selected index asset');op.replace_selected=True
        if reason:
            for line in textwrap.wrap(reason,width=max(24,int(context.region.width/7)-6)):l.label(text=line)
        active=context.active_object
        if active and active.type=='MESH' and active.get('hb_game','halo3')=='halo3' and active.get('hb_source_tag'):
            l.separator();l.label(text='Original Halo 3 Vehicle',icon='AUTO')
            for line in textwrap.wrap('3D object: '+active.name,width=max(24,int(context.region.width/7)-6)):l.label(text=line)
            row=l.row();row.enabled=_task is None;row.operator('halo_bridge.find_vehicle')
            if json.loads(active.get('hb_vehicle_matches','[]')):
                row=l.row();row.enabled=_task is None;row.operator('halo_bridge.choose_vehicle',icon='VIEWZOOM')
            if active.get('hb_vehicle_tag'):
                for line in textwrap.wrap('Vehicle: '+active['hb_vehicle_tag'],width=max(24,int(context.region.width/7)-6)):l.label(text=line)
                l.operator('halo_bridge.vehicle_static')
        l=root
        l.separator();l=root.box();l.label(text='Materials and Shaders',icon='MATERIAL')
        l.label(text='Shaders from the export destination.')
        l.label(text='Imported materials already have shaders.')
        l.operator('halo_bridge.scan_shaders',icon='FILE_REFRESH')
        l.label(text='Shader level / category');l.prop(s,'shader_level',text='')
        shader=s.shader_choice
        label=shader.replace('\\','/').rsplit('/',1)[-1] if shader and shader!='NONE' else 'Choose an existing shader...'
        l.operator('halo_bridge.choose_shader',text=label,icon='VIEWZOOM')
        l.prop(s,'shader_manual')
        if s.shader_manual:l.prop(s,'shader_path')
        l.operator('halo_bridge.shader')
        active=context.active_object
        if active and active.type=='MESH' and active.active_material and not vehicles.selected_vehicle(active):
            l.separator();l.label(text='Collision for selected material')
            if len(active.material_slots)>1:
                l.template_list('MATERIAL_UL_mats','hb_collision',active,'material_slots',active,'active_material_index',rows=3)
            l.label(text=active.active_material.name,icon='MATERIAL')
            l.prop(active.active_material,'hb_collision_mode',text='Collision')
            l.label(text='Shared materials affect all objects using them.')
        l=root.box();l.label(text='Sky (Experimental)',icon='WORLD')
        l.label(text='Choose the sky used in Sapien.')
        selected_sky=s.sky_selected if s.sky_selected!='AUTO' else (s.sky_choice or 'AUTO')
        label=selected_sky.replace('\\','/').rsplit('/',1)[-1] if selected_sky!='AUTO' else 'Original map / default sky'
        l.operator('halo_bridge.choose_sky',text=label,icon='WORLD')
        if selected_sky!='AUTO':
            for line in textwrap.wrap('Selected: '+selected_sky,width=max(24,int(context.region.width/7)-6)):l.label(text=line)
        row=l.row();row.enabled=_task is None;row.operator('halo_bridge.refresh_skies',icon='FILE_REFRESH')
        l=root.box();l.label(text='(Experimental) Sapien Map Preparation',icon='SCENE_DATA')
        l.prop(s,'export_target')
        if s.game!=s.export_target:
            l.label(text='Mixed-game meshes convert to the destination.')
        if s.export_target=='reach':
            l.label(text='Reach Sapien export is not available yet.',icon='INFO')
            l.label(text='Choose Halo 3 to prepare this scene.')
            return
        l.prop(s,'skip_invalid')
        l.label(text='Output Level Name (without .map)')
        l.prop(s,'level',text='')
        l.label(text='Current meshes: generated static collision.')
        l.prop(s,'lighting')
        l.prop(s,'open_sapien')
        l=root
        l.label(text='HaloBridge Warnings and Messages',icon='INFO')
        draw_messages(l,context)
        status=l.box();status.label(text='Map Preparation Status',icon='INFO')
        width=max(24,int(context.region.width/7))
        if _prepare_activity:
            status.label(text=_prepare_activity.phase)
            elapsed=int((_prepare_activity.ended or time.monotonic())-_prepare_activity.started)
            status.label(text=f'Total elapsed: {elapsed//60:02}:{elapsed%60:02}')
            status.label(text='Stage counts do not estimate time remaining.')
            upcoming=('Scene export','Materials','Geometry and collision','Sky and scenario','Lighting / final checks')[_prepare_activity.stage_number:]
            if upcoming and _prepare_running:
                for line in textwrap.wrap('Still to run: '+', '.join(upcoming),width=width):status.label(text=line)
        for paragraph in _prepare_status.splitlines():
            for line in textwrap.wrap(paragraph,width=width):status.label(text=line)
        if _prepare_activity:
            status.separator();status.label(text='Recent preparation activity',icon='TIME')
            for entry in _prepare_activity.recent[-3:]:
                for line in textwrap.wrap(entry,width=width):status.label(text=line)
            status.operator('halo_bridge.activity_log',text='Open live activity log',icon='TEXT')
            row=status.row();row.enabled=bool(_prepare_activity.current_log)
            row.operator('halo_bridge.activity_log',text='Open live compiler output',icon='CONSOLE').raw=True
        if _task and getattr(_task,'is_prepare',False):status.operator('halo_bridge.cancel',text='Cancel preparation',icon='CANCEL')
        if _pending_prepare_warning and _pending_prepare_warning['scene']==context.scene.as_pointer():
            review=l.box();heading=review.row();heading.alert=True;heading.scale_y=1.25
            heading.label(text='Review preparation warnings',icon='ERROR')
            for issue in _pending_prepare_warning['issues']:
                for line in textwrap.wrap(issue,width=width):review.label(text=line)
            draw_review_actions(review,_pending_prepare_warning['token'],_task is None and not _prepare_running)
        row=l.row();row.enabled=_task is None and not _prepare_running
        row.scale_y=1.3;row.operator('halo_bridge.prepare',text=prepare_button_text(),icon='EXPORT',depress=True)
        row=l.row();row.enabled=_task is None;row.scale_y=1.2;row.operator('halo_bridge.open',icon='PLAY',depress=True)

classes=(HBChooseMap,HBFindVehicle,HBChooseVehicle,HBVehicleStatic,HBActivityLog,HBApplyExtracted,HBAsset,HBSettings,HBDetect,HBCheckSetup,HBScan,HBIndex,HBPlace,HBClearSearch,HBCheckAssets,HBListHistory,HBListAction,HBPlaceChecked,HBImportMapScene,HBRepairMap,HBPreviewToggle,HBGround,HBScanShaders,HBChooseShader,HBShader,HBChooseSky,HBRefreshSkies,HBPrepare,HBConfirmPrepare,HBOpen,HBResolve,HBCancel,HBDiagnostics,HBReportDiagnostics,HBSelectCollisionIssues,HBCenterMapOrigins,HB_UL_assets,HBMessages,HBMessagesPopover,HBPanel)

@persistent
def load_catalogue(_=None):
    global _catalogue,_message
    s=bpy.context.scene.halo_bridge
    changed,folders=source_names.restore()
    if folders and not _task:
        def done(unresolved):
            global _message
            count,_=source_names.restore()
            _message='Source material and texture names updated.'
            if unresolved:_message+=' Some texture names could not be recovered because their source map or catalogue is unavailable.'
        directory=Path(config(bpy.context)['cache'])/'jobs'
        start(bpy.context,lambda cancel:source_names.fetch_names(folders,directory,cancel),done,'Looking up original Halo texture names...')
    if s.cache:
        try:
            ensure_catalogue(bpy.context,force=True)
            refresh(bpy.context,persist=False)
            if not _task:_message='Catalogue loaded. Search for an asset to place.'
        except Exception as e:_message='Could not load catalogue: '+str(e)

def register():
    for cls in classes:bpy.utils.register_class(cls)
    bpy.types.VIEW3D_HT_header.append(draw_message_header)
    bpy.types.Scene.halo_bridge=PointerProperty(type=HBSettings)
    bpy.types.Material.hb_collision_mode=EnumProperty(name='Export collision',description='Controls collision generated from this material during static scene export',items=[('AUTO','Automatic','Halo foliage shaders and explicit render-only materials do not generate collision; other surfaces remain collidable'),('SOLID','Collidable','Generate collision from these surfaces, including foliage'),('RENDER_ONLY','Render only (no collision)','Keep these surfaces visible but omit them from collision; useful for leaf cards and decorative foliage')],default='AUTO')
    navigation.register()
    bpy.app.handlers.undo_pre.append(cancel_before_history)
    bpy.app.handlers.redo_pre.append(cancel_before_history)
    bpy.app.handlers.load_post.append(load_catalogue)
    bpy.app.handlers.depsgraph_update_post.append(paste_selection_updated)
    bpy.app.timers.register(load_catalogue,first_interval=.1)
    bpy.app.timers.register(check_preview_copies,first_interval=.25,persistent=True)

def unregister():
    navigation.unregister()
    for handlers in (bpy.app.handlers.undo_pre,bpy.app.handlers.redo_pre):
        if cancel_before_history in handlers:handlers.remove(cancel_before_history)
    bpy.types.VIEW3D_HT_header.remove(draw_message_header)
    if _task:_task.cancel.set()
    if bpy.app.timers.is_registered(preview_tick):bpy.app.timers.unregister(preview_tick)
    if bpy.app.timers.is_registered(poll):bpy.app.timers.unregister(poll)
    if bpy.app.timers.is_registered(load_catalogue):bpy.app.timers.unregister(load_catalogue)
    if bpy.app.timers.is_registered(check_preview_copies):bpy.app.timers.unregister(check_preview_copies)
    if load_catalogue in bpy.app.handlers.load_post:bpy.app.handlers.load_post.remove(load_catalogue)
    if paste_selection_updated in bpy.app.handlers.depsgraph_update_post:bpy.app.handlers.depsgraph_update_post.remove(paste_selection_updated)
    del bpy.types.Scene.halo_bridge
    del bpy.types.Material.hb_collision_mode
    for cls in reversed(classes):bpy.utils.unregister_class(cls)

