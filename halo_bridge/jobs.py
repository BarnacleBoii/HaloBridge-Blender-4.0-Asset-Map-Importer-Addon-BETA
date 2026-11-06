"""Cancelable external jobs with readable logs and content-aware extraction caching."""
import json
import os
import subprocess
import threading
import time
from pathlib import Path
from .catalog import read_json, write_json, fingerprint, stable_id
from .diagnostics import ValidationError, compiler_errors

BIN=Path(__file__).parent/'bin'

class Cancelled(RuntimeError): pass

def process_activity(process):
    """CPU seconds and resident bytes from our own child process handle."""
    if os.name!='nt':return None
    import ctypes
    from ctypes import wintypes
    class Counters(ctypes.Structure):
        _fields_=[('cb',wintypes.DWORD),('PageFaultCount',wintypes.DWORD)]+[(n,ctypes.c_size_t) for n in ('PeakWorkingSetSize','WorkingSetSize','QuotaPeakPagedPoolUsage','QuotaPagedPoolUsage','QuotaPeakNonPagedPoolUsage','QuotaNonPagedPoolUsage','PagefileUsage','PeakPagefileUsage')]
    handle=wintypes.HANDLE(int(process._handle));times=[wintypes.FILETIME() for _ in range(4)]
    if not ctypes.windll.kernel32.GetProcessTimes(handle,*[ctypes.byref(t) for t in times]):return None
    counters=Counters();counters.cb=ctypes.sizeof(counters)
    if not ctypes.windll.psapi.GetProcessMemoryInfo(handle,ctypes.byref(counters),counters.cb):return None
    cpu=sum((t.dwHighDateTime<<32)|t.dwLowDateTime for t in times[2:])/10000000
    return cpu,counters.WorkingSetSize

def _peak_memory(process):
    if os.name!='nt':return 0
    import ctypes
    from ctypes import wintypes
    class Counters(ctypes.Structure):
        _fields_=[('cb',wintypes.DWORD),('PageFaultCount',wintypes.DWORD)]+[(n,ctypes.c_size_t) for n in ('PeakWorkingSetSize','WorkingSetSize','QuotaPeakPagedPoolUsage','QuotaPagedPoolUsage','QuotaPeakNonPagedPoolUsage','QuotaNonPagedPoolUsage','PagefileUsage','PeakPagefileUsage')]
    c=Counters();c.cb=ctypes.sizeof(c)
    ok=ctypes.windll.psapi.GetProcessMemoryInfo(wintypes.HANDLE(int(process._handle)),ctypes.byref(c),c.cb)
    return c.PeakWorkingSetSize if ok else 0

def run_process(args, log, cwd=None, cancel=None, status=None, structure=None):
    log=Path(log);log.parent.mkdir(parents=True,exist_ok=True)
    flags=getattr(subprocess,'CREATE_NO_WINDOW',0)
    with log.open('w',encoding='utf-8') as stream:
        p=subprocess.Popen([str(a) for a in args],cwd=cwd,stdout=stream,stderr=subprocess.STDOUT,creationflags=flags)
        if hasattr(status,'bind_process'):status.bind_process(p,process_activity)
        started=time.perf_counter();peak=0
        try:
            while p.poll() is None:
                if status:status()
                peak=max(peak,_peak_memory(p))
                if cancel and cancel.is_set():
                    subprocess.run(['taskkill','/PID',str(p.pid),'/T','/F'],capture_output=True,creationflags=flags)
                    if p.poll() is None:p.kill()
                    p.wait();raise Cancelled('Cancelled; the previous successful level is retained.')
                time.sleep(.1)
            if status:
                if hasattr(status,'last_update'):status.last_update=-float('inf')
                status()
        finally:
            if p.poll() is None: p.kill();p.wait()
            write_json(log.with_suffix('.metrics.json'),dict(seconds=time.perf_counter()-started,peak_working_set_bytes=peak,exit_code=p.returncode))
    text=log.read_text(encoding='utf-8',errors='replace')
    errors=compiler_errors(text, structure if p.returncode == 0 else None)
    if p.returncode or errors:
        raise ValidationError(errors or ['Process exited with code '+str(p.returncode)+'.\n'+text],
                              'External job failed; full log: '+str(log))
    return text

def helper(kind, job, directory, cancel=None):
    directory=Path(directory); directory.mkdir(parents=True,exist_ok=True)
    nonce=str(time.time_ns());file=directory/(kind+'_'+nonce+'.json');write_json(file,dict(version=1,**job))
    exe=BIN/('extractor/HaloBridge.Extractor.exe' if kind=='extractor' else 'tags/HaloBridge.Tags.exe')
    if not exe.is_file():raise RuntimeError('HaloBridge helper is missing. Install the release add-on ZIP, or build helpers from source. Use Check setup for details.')
    run_process([exe,file], file.with_suffix('.log'), cancel=cancel)
    return read_json(job['output']) if Path(job['output']).is_file() else None

def extract(asset, config, cancel=None):
    if asset['kind']=='legacy':
        mapped=asset.get('mapping')
        if not mapped: return Path(asset['path'])
        asset=mapped
    cache=Path(config['cache'])/'assets'/asset['id']
    if asset['kind'] in ('model','scenery'):cache=cache/'model_parts_v2'
    stamp=cache/'stamp.json'
    # Resource cache updates can change an asset even if the selected map does not.
    resources=sorted(Path(asset['map']).parent.glob('*.map'))
    signature={'extractor':4,'files':[fingerprint(p) for p in resources], 'tag':asset['tag'],'section':asset['section']}
    if asset['kind']=='instance' and asset.get('game','halo3')=='halo3':
        signature['source_bsp']=fingerprint(Path(config['kit'])/'tags'/(asset['tag']+'.scenario_structure_bsp'))
    if (read_json(stamp)==signature and (cache/'preview.json').is_file()
            and (asset['kind']!='instance' or asset.get('game')=='reach' or (cache/'collision.json').is_file())): return cache/'preview.json'
    cache.mkdir(parents=True,exist_ok=True)
    stamp.unlink(missing_ok=True)
    # Re-extraction must not retain textures from an older resource cache.
    for texture in cache.glob('texture_*.*'):texture.unlink()
    helper('extractor',dict(operation='material' if asset['kind']=='material' else 'extract',game=asset.get('game','halo3'),map=asset['map'],tag=asset['tag'],section=asset['section'],output=str(cache)),Path(config['cache'])/'jobs',cancel)
    if asset['kind']=='instance' and asset.get('game','halo3')=='halo3':
        helper('tags',dict(operation='collision',kit=config['kit'],scenario=asset['tag'],section=asset['section'],asset_name=asset['name'],output=str(cache/'collision.json')),Path(config['cache'])/'jobs',cancel)
    write_json(stamp,signature)
    return cache/'preview.json'

def extract_map_scene(config,map_name,cancel=None,progress=None):
    mp=Path(config['maps'])/map_name
    if not mp.is_file():raise RuntimeError('Choose an existing MCC .map filename for the selected game.')
    signature={'map_scene':1,'game':config.get('game','halo3'),'resources':[fingerprint(p) for p in sorted(mp.parent.glob('*.map'))]}
    # Content-addressed generation keeps a prior completed map cache intact.
    folder=Path(config['cache'])/'map_scenes'/stable_id(str(mp.resolve()),json.dumps(signature,sort_keys=True))
    # A failed BSP extraction must not become a permanently reusable cache.
    # Fresh attempts use new directories so an open Blender scene retains its
    # existing mesh identities and cached files, including user edits.
    candidates=[folder]+sorted(folder.parent.glob(folder.name+'_retry_*'),reverse=True)
    for candidate in candidates:
        manifest=candidate/'scene.json'
        data=read_json(manifest,{})
        if (read_json(candidate/'stamp.json')==signature and data.get('expected_bsps',0)>0
                and data.get('decoded_bsps')==data['expected_bsps']):
            if not (candidate/'texture_names.json').is_file():
                helper('extractor',dict(operation='texture_names',map=str(mp),output=str(candidate/'texture_names.json')),Path(config['cache'])/'jobs',cancel)
            return manifest
    if folder.exists():folder=folder.with_name(folder.name+'_retry_'+str(time.time_ns()))
    manifest=folder/'scene.json';stamp=folder/'stamp.json'
    folder.mkdir(parents=True,exist_ok=True)
    directory=Path(config['cache'])/'jobs';directory.mkdir(parents=True,exist_ok=True)
    job=directory/('map_scene_'+str(time.time_ns())+'.json')
    write_json(job,dict(version=1,operation='map_scene',game=config.get('game','halo3'),map=str(mp),output=str(folder)))
    def status():
        if progress:
            try:
                data=read_json(folder/'progress.json',{})
                if data.get('message'):progress(data['message'])
            except (OSError,ValueError):pass
    run_process([BIN/'extractor/HaloBridge.Extractor.exe',job],job.with_suffix('.log'),cancel=cancel,status=status)
    if not manifest.is_file():raise RuntimeError('Map extractor did not create a scene manifest.')
    write_json(stamp,signature)
    return manifest
