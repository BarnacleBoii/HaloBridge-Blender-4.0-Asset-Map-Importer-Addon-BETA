"""Readable datablock names; cache keys, image files and Halo shader paths stay intact."""
import re
from pathlib import Path
from .catalog import read_json,write_json


def leaf(value):return str(value or '').replace('\\','/').rsplit('/',1)[-1]


def generated_material(name):return bool(re.fullmatch(r'hb_[0-9a-f]+(?:\.\d+)?',name))


def source_map(folder):
    folder=Path(folder)
    scene=read_json(folder/'scene.json',{})
    stamp=read_json(folder/'stamp.json',{})
    if scene:
        scenario=leaf(scene.get('scenario',''))
        matches=[Path(row[0]) for row in stamp.get('resources',[]) if Path(row[0]).stem==scenario]
        if len(matches)==1:return matches[0]
    if folder.parent.name=='assets':
        catalogue=read_json(folder.parent.parent/'catalogue.json',{})
        matches={row['map'] for row in catalogue.get('assets',[]) if row.get('id')==folder.name and row.get('map')}
        if len(matches)==1:return Path(next(iter(matches)))
    return None


def fetch_names(folders,jobs_folder,cancel=None):
    from . import jobs
    maps={};unresolved=[]
    for folder in folders:
        folder=Path(folder)
        if (folder/'texture_names.json').is_file():continue
        source=source_map(folder)
        if not source or not source.is_file():unresolved.append(str(folder));continue
        maps.setdefault(str(source),[]).append(folder)
    for source,targets in maps.items():
        if cancel and cancel.is_set():raise jobs.Cancelled('Name lookup cancelled.')
        result=jobs.helper('extractor',dict(operation='texture_names',map=source,output=str(targets[0]/'texture_names.json')),jobs_folder,cancel)
        for target in targets[1:]:write_json(target/'texture_names.json',result)
    return unresolved


def restore():
    import bpy
    changed=0;folders=set();lookups={}
    for mat in bpy.data.materials:
        if mat.library or not mat.get('hb_label'):continue
        if generated_material(mat.name):
            if not mat.get('hb_material_key'):mat['hb_material_key']=mat.name
            if not mat.get('hb_conversion_id'):mat['hb_conversion_id']=mat.name
            mat.name=leaf(mat.get('hb_label') or mat.get('hb_shader')) or mat.name;changed+=1
    for image in bpy.data.images:
        if image.library:continue
        if not re.fullmatch(r'texture_\d+\.png(?:\.\d+)?',image.name):continue
        path=Path(bpy.path.abspath(image.filepath));match=re.fullmatch(r'texture_(\d+)\.png',path.name)
        if not match:continue
        folder=path.parent;folders.add(str(folder))
        if folder not in lookups:lookups[folder]=read_json(folder/'texture_names.json',{}).get('textures',{})
        source=image.get('hb_source_texture') or lookups[folder].get(match[1])
        if source:
            image['hb_source_texture']=source;image.name=leaf(source);changed+=1
    return changed,folders
