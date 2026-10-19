"""Sky picker cache. File scanning and ManagedBlam work run only on refresh."""
from pathlib import Path
from .catalog import read_json
import zlib
_cache={}
_retired=[]

def items(settings,context):
    key=(settings.kit,settings.cache)
    if key not in _cache:
        data=read_json(Path(settings.cache)/'sky-catalogue.json',{}) if settings.cache else {}
        rows=data.get('items',[]) if data.get('kit')==settings.kit else []
        entries=[('AUTO','Original map / default sky','Use the imported map sky, or the starter sky for an authored level',0)]
        for row in rows:
            name=row['scenario'];entries.append((name,row['name']+' ('+name.replace('\\','/')+')','Primary sky: '+', '.join(row['skies']),(zlib.crc32(name.encode())&0x3fffffff)+1))
        _cache[key]=entries
    return _cache[key]

def invalidate():
    # Blender retains references to enum strings across redraws.
    _retired.extend(_cache.values());_cache.clear()
