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
    if name == 'Level_Name_Here':
        raise ValueError('Name your level first: replace Level_Name_Here in Output Level Name (above the Prepare button) with a name such as shrine20, using lowercase letters, digits or underscores.')
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

# Editing Kit folder, MCC maps subfolder and Osoyoos generation per game.
GAME_FOLDERS = {'halo3': ('H3EK', 'halo3', 'halo3'), 'odst': ('H3ODSTEK', 'halo3odst', 'halo3odst'),
                'reach': ('HREK', 'haloreach', 'haloreach'),
                'halo1': ('HCEEK', 'halo1', 'halo1'), 'halo2': ('H2EK', 'halo2', 'halo2')}
# MCC map folders that are not <game>/maps.
MAP_FOLDERS = {'halo2': 'halo2/h2_maps_win64_dx11'}

def fixed_drives():
    """Local fixed drive roots (C:/, D:/ ...); skips empty card readers and network drives."""
    if os.name != 'nt': return []
    try:
        import ctypes
        mask = ctypes.windll.kernel32.GetLogicalDrives(); drives = []
        for i, letter in enumerate('ABCDEFGHIJKLMNOPQRSTUVWXYZ'):
            if mask >> i & 1 and ctypes.windll.kernel32.GetDriveTypeW(letter+':\\') == 3:
                drives.append(Path(letter+':/'))
        return drives
    except Exception:
        return [Path(d+':/') for d in 'CDEFGH']

def documents_folder():
    """The user's Documents folder, including OneDrive or other redirected locations."""
    home = Path.home()
    if os.name == 'nt':
        try:
            import ctypes, uuid
            from ctypes import wintypes
            guid = uuid.UUID('{FDD39AD0-238F-46AF-ADB4-6C85480369C7}')  # FOLDERID_Documents
            buffer = ctypes.c_wchar_p()
            fid = (ctypes.c_ubyte*16).from_buffer_copy(guid.bytes_le)
            if ctypes.windll.shell32.SHGetKnownFolderPath(ctypes.byref(fid), 0, None, ctypes.byref(buffer)) == 0:
                try: return Path(buffer.value)
                finally: ctypes.windll.ole32.CoTaskMemFree(buffer)
        except Exception:
            pass
    return home/'Documents'

def default_storage(game='halo3'):
    """Default HaloBridge storage. An existing ~/Documents/HaloBridge keeps being used."""
    legacy = Path.home()/'Documents/HaloBridge'
    root = legacy if legacy.is_dir() else documents_folder()/'HaloBridge'
    # Halo 3 keeps the original storage root so existing projects keep their records.
    return root if game == 'halo3' else root/game

def appdata_folder():
    value = os.environ.get('APPDATA')
    return Path(value) if value else Path.home()/'AppData/Roaming'

MCC_FOLDER = 'Halo The Master Chief Collection'

def mcc_roots(steam_roots):
    """Steam library MCC folders, then Xbox app / Game Pass installs."""
    roots = [root/MCC_FOLDER for root in steam_roots]
    for drive in fixed_drives():
        for parent in (drive/'XboxGames', drive/'Program Files/ModifiableWindowsApps'):
            try:
                if not parent.is_dir(): continue
                for folder in sorted(parent.iterdir()):
                    name = folder.name.lower()
                    if 'master chief' in name or name.startswith('halomcc'):
                        roots += [folder/'Content', folder]
            except OSError:
                pass
    return roots

def detect_paths(game="halo3"):
    from .setup import steam_libraries
    result = {}
    kit_name, mcc, generation = GAME_FOLDERS.get(game, GAME_FOLDERS['halo3'])
    settings = appdata_folder()/'Osoyoos/Settings.JSON'
    try:profiles=read_json(settings, [])
    except (OSError,ValueError):profiles=[]
    if not isinstance(profiles,list):profiles=[]
    for profile in profiles:
        if not isinstance(profile,dict):continue
        if profile.get('generation') == generation:
            p = Path(profile.get('tool_path','')).parent
            if (p/'tool.exe').is_file(): result['kit'] = str(p); break
    roots = [p/'steamapps/common' for p in steam_libraries()]
    roots += [d/'SteamLibrary/steamapps/common' for d in fixed_drives()]
    roots += [Path(os.environ.get('PROGRAMFILES(X86)', 'C:/Program Files (x86)'))/'Steam/steamapps/common']
    roots = list(dict.fromkeys(roots))
    for root in roots:
        try:
            kit=root/kit_name
            if (kit/'tool.exe').is_file(): result.setdefault('kit', str(kit))
        except OSError:
            pass
    for root in mcc_roots(roots):
        try:
            maps = root/MAP_FOLDERS.get(game, mcc+'/maps')
            if maps.is_dir() and any(maps.glob('*.map')): result.setdefault('maps', str(maps))
        except OSError:
            pass
    result['cache'] = str(default_storage(game))
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
