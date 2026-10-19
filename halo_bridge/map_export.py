"""Validated whole-map base preparation, using original editable collision/gameplay."""
import hashlib
import time
from pathlib import Path
from .catalog import safe_level,read_json,write_json
from . import jobs,build


def prepare(config,plan,cancel=None,progress=None):
    progress=progress or (lambda message:None)
    level=safe_level(config['level']);kit=Path(config['kit']).resolve();cache=Path(config['cache'])
    scenario='levels\\multi\\'+level+'\\'+level
    target=kit/'tags'/(scenario+'.scenario');record=cache/'projects'/level/'map-build.json'
    previous=read_json(record)
    if previous and (previous['kit']!=str(kit) or previous['source']!=plan['source']):
        raise RuntimeError('This output belongs to another map or Editing Kit. Choose a new Output level name.')
    if target.exists() and not previous:
        raise RuntimeError('Output level name '+level+' already belongs to another build. Choose a new name, such as '+level+'_scene, to preserve that level.')
    if previous and not target.exists():raise RuntimeError('The previously prepared scenario is missing. Restore it or choose a new Output level name.')
    source=plan['source'];sky=config.get('sky_scenario') or source
    for name in (source,sky):
        parts=name.replace('/', '\\').split('\\')
        if any(p in ('','.','..') or ':' in p for p in parts) or not (kit/'tags'/(name+'.scenario')).is_file():
            raise RuntimeError('Required Editing Kit scenario is missing: '+name+'. Extract its Editing Kit tags first.')
    if previous and previous['reference_digest']!=plan['reference_digest']:
        raise RuntimeError('The imported map cache differs from this project. Choose a new Output level name.')
    build.ensure_sapien_closed();directory=cache/'jobs';directory.mkdir(parents=True,exist_ok=True)
    nonce=str(time.time_ns())
    def helper(op,**kw):
        build.ensure_sapien_closed()
        return jobs.helper('tags',dict(operation=op,kit=str(kit),scenario=scenario,output=str(directory/(op+'-'+nonce+'.json')),**kw),directory,cancel)
    progress('Checking imported BSP transforms against original collision tags...')
    for number,(bsp,expected) in enumerate(plan.get('bsps',{}).items()):
        state=jobs.helper('tags',dict(operation='inspect_bsp',kit=str(kit),scenario=bsp,output=str(directory/('base-bsp-'+nonce+'-'+str(number)+'.json'))),directory,cancel)
        by_name={}
        for item in state['instances']:by_name.setdefault(item['name'],[]).append(item)
        for item in expected:
            candidates=by_name.get(item['name'],[])
            def matches(other):
                vectors=other['vectors'];rows=[vectors[n] for n in ('forward','left','up')]
                rows=[[v*other['scale'] for v in row] for row in rows]+[other['position']]
                return all(abs(rows[r][c]-item['matrix'][r][c])<.001 for r in range(4) for c in range(3))
            if len([candidate for candidate in candidates if matches(candidate)])!=1:
                raise RuntimeError('The compiled map and Editing Kit BSP do not match: '+bsp+' / '+item['name']+'. A modded map cannot use a different stock collision base.')
    with build.project_transaction(kit,level,cache):
        if not previous:
            if target.exists():raise RuntimeError('Another process created the output. Choose another name.')
            progress('Preparing original terrain, collision, lighting and gameplay tags...')
            # This helper verifies source hashes and copied scenario data.
            copied=helper('copy_level',template=source)
        else:
            copied=previous['copy_result']
            state=helper('inspect')['state']
            if state!=previous['state']:raise RuntimeError('CONFLICT: Sapien changed Blender-owned scenery. The previous level was retained.')
        if (previous and previous['sky']!=sky) or (not previous and sky!=source):
            progress('Applying selected sky...');helper('environment',template=sky)
        progress('Updating added Blender scenery...')
        state=helper('inspect')['state']
        helper('sync',placements=plan['placements'],previous=state)
        final=helper('inspect')
        if cancel and cancel.is_set():raise jobs.Cancelled('Cancelled; the previous successful level is retained.')
        result=dict(version=1,mode='map_base',kit=str(kit),source=source,scenario=scenario,sky=sky,
                    reference_digest=plan['reference_digest'],copy_result=copied,state=final['state'],
                    placements=plan['placements'],completed=time.time(),reference_objects=plan['reference_objects'],
                    import_warnings=plan['warnings'],fallback_issues=plan.get('fallback_issues',[]),spawn_count=final['spawn_count'])
        write_json(record,result)
    return str(target),result
