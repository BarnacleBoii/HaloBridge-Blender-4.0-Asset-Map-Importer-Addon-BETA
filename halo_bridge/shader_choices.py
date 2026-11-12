"""Existing shader dropdown, populated explicitly rather than during redraw."""
from pathlib import Path
import zlib
from . import games
_cache={}
_retired=[]
_empty=[('NONE','Scan existing shaders first','Scan the Editing Kit to choose an existing shader',0)]
_empty_levels=[('ALL','Scan existing shaders first','No shader catalogue loaded',0)]

def group(path):
    parts=path.replace('\\','/').split('/')
    for i,part in enumerate(parts[:-2]):
        if part=='levels' and parts[i+1] in ('solo','multi','dlc'):
            return parts[i+1]+'/'+parts[i+2]
    return 'Shared/'+('/'.join(parts[:2]) if parts[0]=='objects' else parts[0])

def level_items(settings,context):
    return _cache.get(games.destination(settings).kit,{}).get('levels',_empty_levels)
def items(settings,context):
    # The sidebar no longer filters by level; the search popup covers every shader.
    return filtered_items(games.destination(settings).kit,'ALL')

def filtered_items(kit,category):
    data=_cache.get(kit)
    if not data:return _empty
    return data['groups'].get(category,_empty)

def search_items(operator,context):
    return filtered_items(operator.shader_kit,operator.shader_category)

def level_changed(settings,context):
    settings.shader_choice='NONE'
def scan(kit):
    root=Path(kit)/'tags'
    if not root.is_dir():raise RuntimeError('Choose an Editing Kit with extracted tags first.')
    paths=sorted({str(p.relative_to(root).with_suffix('')) for p in root.rglob('*.shader')})
    initial=('NONE','Choose an existing shader','Assign an existing game shader; this does not create a new shader',0)
    groups={'ALL':[initial]}
    used={0}
    for path in paths:
        number=1+(zlib.crc32(path.encode())&0x3fffffff)
        while number in used:number+=1
        used.add(number)
        parts=path.replace('\\','/').split('/')
        label=parts[-1]+(' ('+parts[-2]+')' if len(parts)>1 else '')
        entry=(path,label,path,number)
        groups['ALL'].append(entry);groups.setdefault(group(path),[initial]).append(entry)
    levels=[('ALL','All levels / shared shaders','Search every installed shader',0)]
    numbers={0}
    for key in sorted(k for k in groups if k!='ALL'):
        number=1+(zlib.crc32(key.encode())&0x3fffffff)
        while number in numbers:number+=1
        numbers.add(number)
        label=key.replace('/',' / ')
        levels.append((key,label+' ('+str(len(groups[key])-1)+')','Shaders from '+key,number))
    if kit in _cache:_retired.append(_cache[kit])
    _cache[kit]={'levels':levels,'groups':groups}
    return len(paths)
