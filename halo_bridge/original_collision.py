"""Read matched editing-kit collision for unmodified imported geometry."""
import json
from pathlib import Path
from mathutils import Matrix, Quaternion, Vector
from . import jobs, vehicles
from .catalog import read_json
from .diagnostics import ValidationError

def get(obj, config, progress):
    tag=obj.get('hb_source_tag','')
    if not tag or obj.modifiers or not obj.get('hb_cache'):
        return None
    try:
        offset=vehicles.validate_preview(obj)
    except ValueError:
        return None
    # Model part rebuilds preserve a translated pivot.
    center=Vector(obj.data.get('hb_origin_center',(0,0,0)))
    if center.length and not offset.length:offset=center
    if any(getattr(m,'hb_collision_mode','AUTO')!='AUTO' for m in obj.data.materials if m):return None
    source=Path(obj['hb_cache'])
    if obj.get('hb_kind')=='instance':
        data=read_json(source/'collision.json',{})
        if data.get('source')==tag and data.get('section')==obj.get('hb_section') and data.get('meshes'):
            m=data['meshes'][0]
            return m['positions'],m['faces'],offset
        return None
    if obj.get('hb_kind') not in ('model','scenery'):return None

    if obj.get('hb_parts_enabled'):
        preview=read_json(source/'preview.json',{})
        if set(json.loads(obj['hb_parts_enabled']))!={m.get('choice') for m in preview.get('meshes',[])}:return None
    kit=config.get('reach_collision_kit') if obj.get('hb_game')=='reach' else config['kit']
    if not kit:return None
    tags=Path(kit)/'tags'
    if not (tags/(tag+'.model')).is_file():return None
    cache=config.setdefault('_collision_reads',{})
    key=(kit,tag)
    if key not in cache:
        directory=Path(config['cache'])/'jobs';out=directory/'model-collision.json'
        try:
            cache[key]=jobs.helper('tags',dict(operation='model_collision',kit=kit,scenario=tag,output=str(out)),directory)
        except ValidationError as e:
            progress('Original collision unavailable for '+obj.name+': '+str(e.issues[0]).splitlines()[0])
            cache[key]=None
    data=cache[key]
    if not data:return None
    transforms={};nodes=data['skeleton']
    def transform(i):
        n=nodes[i]
        if i not in transforms:
            x,y,z,w=n['rotation']
            local=Matrix.Translation(Vector(n['translation'])) @ Quaternion((w,x,y,z)).to_matrix().to_4x4()
            transforms[i]=transform(n['parent']) @ local if n['parent']>=0 else local
        return transforms[i]
    by_name={n['name']:transform(i) for i,n in enumerate(nodes)}
    selections={r['region']:r['selected'] for r in json.loads(obj.get('hb_model_selection','[]'))}
    verts=[];faces=[]
    for region in sorted({m['region'] for m in data['meshes']}):
        parts=[m for m in data['meshes'] if m['region']==region]
        choices={m['permutation'] for m in parts}
        match=choices.intersection(selections.get(region,[]))
        if len(choices)>1 and len(match)!=1:return None
        for m in parts:
            if len(choices)>1 and m['permutation'] not in match:continue
            base=len(verts);geom=m['geometry']
            verts.extend(by_name[m['node']] @ Vector(v) for v in geom['positions'])
            faces.extend([base+i for i in face] for face in geom['faces'])
    return (verts,faces,offset) if faces else None
