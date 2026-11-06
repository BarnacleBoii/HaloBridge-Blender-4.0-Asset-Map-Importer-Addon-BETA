"""Sky picker cache. File scanning and ManagedBlam work run only on refresh."""
from pathlib import Path
from .catalog import read_json
import zlib
import os
import bpy
from . import games
_cache={}
_retired=[]

def normalized_path(value):
    return os.path.normcase(os.path.normpath(bpy.path.abspath(value))) if value else ''


def items(settings,context):
    settings=games.destination(settings)
    key=(normalized_path(settings.kit),normalized_path(settings.cache))
    if key not in _cache:
        data=read_json(Path(key[1])/'sky-catalogue.json',{}) if settings.cache else {}
        rows=data.get('items',[]) if normalized_path(data.get('kit',''))==key[0] else []
        entries=[('AUTO','Original map / default sky','Use the imported map sky, or the starter sky for an authored level',0)]
        for row in rows:
            name=row['scenario'];entries.append((name,row['name'],name+' — Primary sky: '+', '.join(row['skies']),(zlib.crc32(name.encode())&0x3fffffff)+1))
        _cache[key]=entries
    return _cache[key]

def invalidate():
    # Blender retains references to enum strings across redraws.
    _retired.extend(_cache.values());_cache.clear()
