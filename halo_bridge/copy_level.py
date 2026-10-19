"""Copy original editable level tags, independently of Blender geometry export."""
import time
from pathlib import Path
from . import jobs,build
from .catalog import safe_level,read_json,write_json

def copy_original(config,map_name,cancel=None,progress=None):
    progress=progress or (lambda message:None)
    level=safe_level(config['level']);kit=Path(config['kit']).resolve();cache=Path(config['cache'])
    if Path(map_name).name!=map_name or not map_name.lower().endswith('.map'):raise RuntimeError('Choose a .map filename from your maps folder.')
    source_map=Path(config['maps'])/map_name
    if not source_map.is_file():raise RuntimeError('The selected original .map file was not found.')
    target=kit/'tags/levels/multi'/level
    manifest=cache/'projects'/level/'original-copy.json'
    if target.exists() or manifest.exists():raise RuntimeError('That output level already exists. Choose a new output level name; existing Sapien edits will not be overwritten.')
    build.ensure_sapien_closed();directory=cache/'jobs';directory.mkdir(parents=True,exist_ok=True)
    nonce=str(time.time_ns())
    progress('Reading the original scenario identity…')
    info=jobs.helper('extractor',dict(operation='scenario_info',map=str(source_map),output=str(directory/('copy-source-'+nonce+'.json'))),directory,cancel)
    scenario='levels\\multi\\'+level+'\\'+level
    result_file=directory/('copy-result-'+nonce+'.json')
    job_file=directory/('copy-job-'+nonce+'.json')
    write_json(job_file,dict(version=1,operation='copy_level',kit=str(kit),template=info['scenario'],scenario=scenario,output=str(result_file)))
    def status():
        try:
            message=read_json(str(result_file)+'.progress.json',{}).get('message')
            if message:progress(message)
        except (OSError,ValueError):pass
    with build.project_transaction(kit,level,cache):
        # Check again under the kit lock, before any destination file is written.
        if target.exists():raise RuntimeError('The output level was created by another process. Choose a different name.')
        build.ensure_sapien_closed();progress('Copying original level tags and retaining gameplay/collision…')
        jobs.run_process([jobs.BIN/'tags/HaloBridge.Tags.exe',job_file],job_file.with_suffix('.log'),cancel=cancel,status=status)
        if cancel and cancel.is_set():raise jobs.Cancelled('Copy cancelled.')
        result=read_json(result_file)
        if not result or not result.get('ok') or result.get('scenario')!=scenario:raise RuntimeError('Copied scenario verification did not complete.')
        path=kit/'tags'/(scenario+'.scenario')
        if not path.is_file():raise RuntimeError('The copied scenario file is missing.')
        write_json(manifest,{**result,'version':1,'mode':'original_copy','kit':str(kit),'source_map':str(source_map),'completed':time.time()})
    progress('Original map copy is ready for Sapien.')
    return str(path),result
