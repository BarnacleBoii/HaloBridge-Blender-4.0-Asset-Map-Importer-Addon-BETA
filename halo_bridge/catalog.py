"""Filesystem catalogue. No Blender dependency, no changes to source assets."""
import hashlib
import json
import os
import re
from pathlib import Path

VERSION = 1

def read_json(path, default=None):
    p = Path(path)
    return json.loads(p.read_text(encoding='utf-8-sig')) if p.exists() else default

def write_json(path, value):
    p = Path(path); p.parent.mkdir(parents=True, exist_ok=True)
    temporary = p.with_suffix(p.suffix + '.tmp')
    temporary.write_text(json.dumps(value, indent=2), encoding='utf-8')
    os.replace(temporary, p)

def stable_id(*parts):
    return hashlib.sha256('|'.join(str(x) for x in parts).encode()).hexdigest()[:24]

def fingerprint(path):
    p = Path(path); s = p.stat()
    return [str(p.resolve()), s.st_size, s.st_mtime_ns]

def safe_level(name):
    if not re.fullmatch(r'[a-z][a-z0-9_]{2,31}', name):
        raise ValueError('Output level name (above the Prepare button) is '+repr(name)+'. Enter a name such as shrine20, without .map, folders, spaces or capitals. Use 3-32 lowercase letters, digits or underscores, starting with a letter.')
    if name.upper() in {'CON','PRN','AUX','NUL'}|{'COM'+str(i) for i in range(10)}|{'LPT'+str(i) for i in range(10)}:
        raise ValueError('Reserved Windows filename.')
    return name

def category(name):
    n = name.lower()
    if any(w in n for w in ('tree','palm','plant','bush','log','foliage','stump')): return 'Vegetation'
    if any(w in n for w in ('rock','cliff','boulder')): return 'Rocks'
    if any(w in n for w in ('water','river')): return 'Water'
    return 'Structures'

def detect_paths(game="halo3"):
    from .setup import steam_libraries
    home = Path.home(); result = {}
    settings = home/'AppData/Roaming/Osoyoos/Settings.JSON'
    try:profiles=read_json(settings, [])
    except (OSError,ValueError):profiles=[]
    if not isinstance(profiles,list):profiles=[]
    for profile in profiles:
        if not isinstance(profile,dict):continue
        if profile.get('generation') == ('haloreach' if game=='reach' else 'halo3'):
            p = Path(profile.get('tool_path','')).parent
            if (p/'tool.exe').is_file(): result['kit'] = str(p); break
    roots = [p/'steamapps/common' for p in steam_libraries()]
    roots += [Path(f'{d}:/SteamLibrary/steamapps/common') for d in 'ABCDEFGHIJKLMNOPQRSTUVWXYZ']
    roots += [Path(os.environ.get('PROGRAMFILES(X86)', 'C:/Program Files (x86)'))/'Steam/steamapps/common']
    for root in roots:
        kit=root/('HREK' if game=='reach' else 'H3EK')
        if (kit/'tool.exe').is_file(): result.setdefault('kit', str(kit))
        maps = root/'Halo The Master Chief Collection'/('haloreach' if game=='reach' else 'halo3')/'maps'
        if maps.is_dir(): result.setdefault('maps', str(maps))
    result['cache'] = str(home/'Documents/HaloBridge'/('reach' if game=='reach' else ''))
    return result

def scan_library(root):
    root = Path(root); assets = []; counts = {}
    for p in sorted(root.rglob('*')):
        if not p.is_file(): continue
        ext = p.suffix.lower(); counts[ext] = counts.get(ext,0)+1
        if ext not in ('.amf','.jms'): continue
        rel = p.relative_to(root); level = rel.parts[0]
        name = p.parent.name if len(rel.parts)>2 else p.stem
        if name.lower() in ('models','new folder'): name = p.parent.parent.name
        assets.append(dict(id=stable_id('legacy',str(p.resolve()).lower()),name=name,level=level,
            category=category(name),kind='legacy',path=str(p),game='unverified' if 'boneyard' in str(rel).lower() else 'halo3',
            section=-1,tag='',scenery_tag='',status='Needs source mapping',source_fingerprint=fingerprint(p)))
    return {'version':VERSION, 'assets':assets, 'counts':counts}

def merge_assets(catalogue, additions):
    existing = {a['id']:a for a in catalogue.get('assets',[])}
    for a in additions:
        old = existing.get(a['id'], {})
        for key in ('mapping','thumbnail','hidden'):
            if key in old: a[key] = old[key]
        existing[a['id']] = a
    catalogue['assets'] = sorted(existing.values(),key=lambda a:(a['level'],a['name']))
    return catalogue

def indexed_assets(index):
    path = Path(index['map']); result=[]
    for row in index['assets']:
        a = dict(row)
        a.update(id=stable_id(str(path).lower(),a['tag'],a['section'],a.get('scenery_tag','')),map=str(path),
                 level=path.stem,category='Materials' if a['kind']=='material' else category(a['name']),game=index.get('game','halo3'),status='Static geometry; animation and gameplay are not imported' if a['kind']=='model' else 'Ready to extract')
        result.append(a)
    return result

def shader_index(kit):
    root=Path(kit)/'tags'; result={}
    for p in root.rglob('*.shader*'):
        if p.is_file(): result.setdefault(p.stem.lower(),[]).append(str(p.relative_to(root).with_suffix('')).replace('/','\\'))
    return result

def material_name(kit, tag):
    """Resolve through existing collections without changing the shared collection file."""
    tag=tag.replace('/','\\').lower(); root=Path(kit)/'tags'
    matches=[p for p in (root/Path(tag)).parent.glob(Path(tag).name+'.shader*') if p.is_file()]
    if len(matches)!=1: raise ValueError('Missing or ambiguous shader: '+tag)
    choices=[]
    for line in (root/'levels/shader_collections.txt').read_text(errors='replace').splitlines():
        parts=line.split(';')[0].split()
        if len(parts)!=2 or parts[0]=='*': continue
        prefix,folder=parts;folder=folder.lower().rstrip('\\')
        if tag.startswith(folder+'\\'):
            name=prefix+' '+tag.rsplit('\\',1)[-1]
            candidates=list((root/folder).rglob(tag.rsplit('\\',1)[-1]+'.shader*'))
            if len(candidates)==1 and len(name)<=32: choices.append((len(folder),name))
    if not choices: raise ValueError('No unique shader collection mapping for '+tag+'. Choose a shader with an existing collection prefix.')
    return max(choices)[1]
