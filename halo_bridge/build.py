"""Transactional level compilation. Only the explicitly selected project namespace is replaced."""
import contextlib
import os
import shutil
import subprocess
import time
import re
from pathlib import Path
from .catalog import read_json, write_json, safe_level
from .jobs import helper, run_process, Cancelled
from .diagnostics import ValidationError,geometry_warnings
from .progress import ToolProgress,tool_label

def ensure_sapien_closed():
    if os.name!='nt': return
    r=subprocess.run(['tasklist','/FO','CSV','/NH'],capture_output=True,text=True,creationflags=subprocess.CREATE_NO_WINDOW)
    if r.returncode: raise RuntimeError('Cannot check whether Sapien is running. Close Sapien and retry.')
    if any('"'+name+'"' in r.stdout.lower() for name in ('sapien.exe','sapien_play.exe')):
        raise RuntimeError('Save and close Sapien before preparing the level. This prevents overwriting unsaved editor changes.')

def faux_shader_failure(issues):
    """True for Tool's test-lighting assertion on a shader it cannot evaluate (faux_material.cpp)."""
    text='\n'.join(str(i) for i in issues).lower()
    return 'faux_material.cpp' in text or ('faux' in text and 'parameter_success' in text)

# Shader types whose animated parameters Tool's test lighting cannot evaluate.
FAUX_RISKY_SUFFIXES=('.shader_custom',)

def lighting_suspects(config):
    """Original shader tags in this level that Tool's test lighting is known to reject."""
    return sorted(tag for tag,alias in config.get('shader_aliases',{}).items()
                  if Path(alias.get('source','')).suffix.lower() in FAUX_RISKY_SUFFIXES)

@contextlib.contextmanager
def project_transaction(kit, level, cache):
    safe_level(level);kit=Path(kit).resolve();cache=Path(cache)
    # The lock is shared by every project/cache using this editing kit.
    lock=kit/'halo_bridge.build.lock'
    fd=os.open(lock,os.O_CREAT|os.O_EXCL|os.O_WRONLY)
    os.write(fd,str(os.getpid()).encode());os.close(fd)
    backup=cache/'backups'/str(time.time_ns());backup.mkdir(parents=True)
    targets=[]
    try:
        for kind in ('data','tags'):
            target=kit/kind/'levels/multi'/level
            if target.resolve().parent != (kit/kind/'levels/multi').resolve(): raise ValueError('Unsafe output directory')
            existed=target.exists();targets.append((kind,target,existed))
            if existed: shutil.copytree(target,backup/kind)
        write_json(backup/'transaction.json',{'kit':str(kit),'level':level,'state':'running'})
        try:
            yield backup
        except BaseException:
            for kind,target,existed in targets:
                if target.exists(): shutil.rmtree(target)
                if existed: shutil.copytree(backup/kind,target)
            write_json(backup/'transaction.json',{'kit':str(kit),'level':level,'state':'rolled_back'})
            raise
        write_json(backup/'transaction.json',{'kit':str(kit),'level':level,'state':'committed'})
    finally:
        lock.unlink(missing_ok=True)

def prepare(config, ass_file, placements, cancel=None, progress=None):
    progress=progress or (lambda message:None)
    def stage(number,name):
        if hasattr(progress,'stage'):progress.stage(number,name)
        else:progress(f'Stage {number}/5: '+name)
    level=safe_level(config['level']);kit=Path(config['kit']);cache=Path(config['cache'])
    scenario='levels\\multi\\'+level+'\\'+level
    manifest=cache/'projects'/level/'manifest.json';previous=read_json(manifest,{})
    target=kit/'tags'/(scenario+'.scenario')
    if (cache/'projects'/level/'map-build.json').exists():
        raise RuntimeError('This output was created using the older original-map mode. Choose a new Output level name to compile your edited Blender geometry and preserve that previous level.')
    if (cache/'projects'/level/'original-copy.json').exists():
        raise RuntimeError('This level is an original-map copy. Choose a new output level name for Blender geometry exports to protect its gameplay and Sapien edits.')
    if target.exists() and not previous:
        raise RuntimeError('This level already exists and is not owned by HaloBridge. Choose a new level name.')
    if previous and previous.get('kit')!=str(kit.resolve()): raise RuntimeError('Manifest belongs to a different editing kit.')
    sky_object=config.get('sky_object')
    sky=config.get('sky_scenario',r'levels\multi\deadlock\deadlock').replace('/', '\\')
    sky_parts=sky.split('\\')
    if sky_object:
        # Converted skies carry no sky lighting. Test lighting is baked with a kit sky
        # (the one chosen for this game, or its default) and the converted sky is set after.
        light_sky=sky if sky and ':' not in sky and (kit/'tags'/(sky+'.scenario')).is_file() else config.get('default_sky','')
        if not light_sky or not (kit/'tags'/(light_sky+'.scenario')).is_file():light_sky=''
        sky='converted:'+sky_object['name']
    elif not sky or any(p in ('','.','..') or ':' in p for p in sky_parts) or not (kit/'tags'/(sky+'.scenario')).is_file():
        raise RuntimeError('Sky source scenario must name an existing Editing Kit scenario without its extension, for example levels\\multi\\shrine\\shrine.')
    ensure_sapien_closed()
    jobs=cache/'jobs';jobs.mkdir(parents=True,exist_ok=True)
    def tag_job(operation,**kw):
        progress({'inspect':'Checking scenario state','environment':'Applying the selected sky','sync':'Updating scenario placements','sync_vehicles':'Updating original vehicle placements','ensure_spawn':'Checking the player start','prepare_bitmaps':'Configuring converted textures','import_shaders':'Creating converted Halo 3 shaders'}.get(operation,operation))
        ensure_sapien_closed()
        return helper('tags',dict(operation=operation,kit=str(kit),scenario=scenario,output=str(jobs/'tag-result.json'),**kw),jobs,cancel)
    def tool(*args):
        ensure_sapien_closed();progress(tool_label(args[0]))
        if cancel and cancel.is_set():raise Cancelled('Cancelled')
        try:
            log=jobs/(str(time.time_ns())+'.log')
            return run_process([kit/'tool.exe',*args],log,cwd=kit,cancel=cancel,status=ToolProgress(args[0],log,progress),
                               structure=scenario if args[0]=='structure' else None)
        except ValidationError as error:
            names=config.get('geometry_names',{})
            def friendly(match):
                return '(object '+names[match[1]]+')' if match[1] in names else match[0]
            issues=[re.sub(r'\(poop (hb_\d+)(?:\.\d+)?\)',friendly,issue) for issue in error.issues]
            source=config.get('structure_source')
            if source and any("section 'cluster " in issue or 'plane builder unable to converge' in issue for issue in issues):
                issues.append('Structure geometry context: Blender object "'+source+'" was exported as the main level structure. '
                              'Cluster numbers name regions generated by Halo Tool, not Blender objects; this is the structure source, not an exact failed-face selection. '
                              'Find this object by name in the Outliner and inspect its evaluated geometry and subdivision modifiers. '
                              'Strip segment limits require less complex geometry or a properly designed cluster/portal layout; retrying unchanged geometry will not fix a limit error.')
            raise ValidationError(issues,error.stage) from error
    progress('Backing up the previous level before compilation...')
    with project_transaction(kit,level,cache):
        if previous:
            state=tag_job('inspect')['state']
            if state!=previous['state']:raise RuntimeError('CONFLICT: Sapien changed Blender-owned placements. Restore those edits or explicitly choose Resolve conflict: use Blender.')
        relative='levels\\multi\\'+level+'\\structure\\'+level+'.ASS'
        destination=kit/'data'/relative;destination.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(ass_file,destination)
        aliases=list(config.get('shader_aliases',{}).values())
        stage(2,'Prepare Halo materials')
        for index,alias in enumerate(aliases,1):
            progress(f'Preparing Halo materials {index}/{len(aliases)}: '+Path(alias.get('source',alias['name'])).stem)
            if alias.get('generated'):continue
            source=Path(alias['source']);destination_shader=kit/'tags/levels/multi'/level/'shaders'/(alias['name']+source.suffix)
            destination_shader.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(source,destination_shader)
        converted=config.get('converted_shaders',[])
        if converted:
            bitmap_root='levels\\multi\\'+level+'\\bitmaps\\reach'
            shader_root='levels\\multi\\'+level+'\\shaders'
            bitmap_dir=kit/'data'/bitmap_root;bitmap_dir.mkdir(parents=True,exist_ok=True)
            shaders=[]
            sky_shader_root='levels\\multi\\'+level+'\\sky\\shaders'
            for index,entry in enumerate(converted,1):
                progress(f'Copying converted material {index}/{len(converted)}: '+entry['name'])
                # Tool's render-sky finds a sky's shaders in the sky folder's own shaders folder.
                item=dict(path=(sky_shader_root if entry.get('folder')=='sky' else shader_root)+'\\'+entry['name'],sky=entry.get('folder')=='sky',additive=bool(entry.get('additive')))
                for usage,source in entry['maps'].items():
                    source=Path(source);shutil.copy2(source,bitmap_dir/source.name)
                    item[usage]=bitmap_root+'\\'+source.stem
                shaders.append(item)
            tag_job('prepare_bitmaps',shaders=shaders)
            tool('bitmaps',bitmap_root)
            tag_job('import_shaders',shaders=shaders)
        stage(3,'Compile geometry and collision')
        text=tool('structure',relative)
        config['compiler_warnings']=geometry_warnings(text,config.get('geometry_names',{}))
        if config['compiler_warnings']:
            warning_report=jobs/('geometry-warnings-'+str(time.time_ns())+'.txt')
            warning_report.write_text('\n'.join(config['compiler_warnings']),encoding='utf-8')
            progress(str(len(config['compiler_warnings']))+' geometry warning(s). These may appear as red debug geometry in Sapien. Report: '+str(warning_report))
        if f"=== imported structure '{scenario}' in " not in text or not target.is_file() or not target.with_suffix('.scenario_structure_bsp').is_file():
            raise RuntimeError('Halo did not confirm the level structure import or produce its scenario and BSP tags.')
        stage(4,'Apply sky and scenario settings')
        if sky_object:
            # A sky converted from another game: build its render model, then its model,
            # scenery and the scenario's sky reference.
            sky_root='levels\\multi\\'+level+'\\sky'
            render=kit/'data'/sky_root/'render';render.mkdir(parents=True,exist_ok=True)
            shutil.copy2(sky_object['jms'],render/'sky.JMS')
            progress('Building the converted sky: '+sky_object['name'])
            tool('render-sky',sky_root)
            tag_job('sky_object',template=sky_root+'\\sky',radius=float(sky_object.get('radius',0)))
            if config.get('lighting',True) and light_sky:tag_job('environment',template=light_sky)
        elif not previous or previous.get('sky_scenario',r'levels\multi\deadlock\deadlock')!=sky: tag_job('environment',template=sky)
        # Compilation may legitimately update derived placement fields. User edits
        # were checked above, before running Tool with Sapien closed.
        after_compile=tag_job('inspect')['state']
        tag_job('sync',placements=placements,previous=after_compile)
        if config.get('vehicle_placements') or any(key.startswith('vehicle:') for key in after_compile):
            progress('Placing original vehicles (using existing vehicle tags)')
            tag_job('sync_vehicles',placements=config.get('vehicle_placements',[]),previous=after_compile)
        if config.get('spawn_position'):tag_job('ensure_spawn',position=config['spawn_position'])
        lit=False
        if config.get('lighting',True):
            stage(5,'Generate test lighting and finalize')
            progress('Starting test lighting: 16 tool stages. Each stage can take several minutes.')
            blob=str(100000000+time.time_ns()%900000000);blobdir='faux\\'+blob
            try:
                tool('faux_data_sync',scenario,level)
                tool('faux_farm_begin',scenario,level,'all','draft',blob)
                for stage in ('dillum','pcast','radest','extillum','fgather'):
                    tool('faux_farm_'+stage,blobdir,'0','1')
                    tool('faux_farm_'+stage+'_merge',blobdir,'1')
                tool('faux_farm_finish',blobdir)
                tool('faux-build-linear-textures-with-intensity-from-quadratic',scenario,level)
                tool('faux-compress-scenario-bitmaps-dxt5',scenario,level)
                tool('faux-farm-compression-merge',scenario,level)
                lit=True
            except ValidationError as error:
                if not faux_shader_failure(error.issues):raise
                # Tool's test lighting (faux) asserts on some animated shaders (for example
                # 070_waste's waterfall.shader_custom). The compiled level is still valid,
                # so it is kept without test lighting instead of rolling everything back.
                suspects=lighting_suspects(config)
                config['lighting_skipped_shaders']=suspects
                note=('Test lighting was skipped: Halo Tool\'s test lighting cannot process '
                      +(('the animated shader(s) '+', '.join(suspects)) if suspects else 'one of this level\'s shaders')
                      +'. The level was prepared without test lighting. To light it, give those objects a different shader or remove them, '
                      'or turn off Generate Test Lighting. Tool log: '+str(error.stage))
                config.setdefault('compiler_warnings',[]).append(note)
                progress(note)
        else:stage(5,'Finalize (test lighting disabled)')
        if sky_object and light_sky and config.get('lighting',True):
            progress('Setting the converted sky'+(' (lighting was baked with '+light_sky.rsplit('\\',1)[-1]+')' if lit else ''))
            tag_job('sky_object',template='levels\\multi\\'+level+'\\sky\\sky',radius=float(sky_object.get('radius',0)))
        final=tag_job('inspect')
        write_json(manifest,dict(version=1,kit=str(kit.resolve()),scenario=scenario,state=final['state'],placements=placements,completed=time.time(),lighting=lit,sky_scenario=sky))
    progress('Ready in Sapien')
    return str(target)

