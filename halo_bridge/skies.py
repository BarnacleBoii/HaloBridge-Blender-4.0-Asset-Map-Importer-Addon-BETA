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

GAME_ITEMS=[(key,value['label'],'Choose a sky from '+value['label']) for key,value in games.GAMES.items() if value['import_enabled']]


def sky_game(settings):
    """The game the sky comes from; scenes that never chose one use the Sapien destination."""
    chosen=settings.get('sky_game') if hasattr(settings,'get') else None
    return settings.sky_game if chosen is not None else games.destination(settings).game


def kit_sky(settings):
    """True when the chosen sky comes from the destination Editing Kit's own maps."""
    return sky_game(settings)==games.destination(settings).game


def catalogue_skies(settings,game):
    """Sky models indexed from a game's .map or .scenario files, from that game's asset list."""
    from . import sky_export
    folder=games.profile(settings,game)['cache']
    path=Path(bpy.path.abspath(folder))/'catalogue.json' if folder else None
    if not path or not path.is_file():return []
    data=read_json(path,{})
    seen={};rows=[]
    for asset in data.get('assets',[]) if isinstance(data,dict) else []:
        if asset.get('hidden') or not sky_export.is_sky_asset(asset) or asset.get('game',game)!=game:continue
        key=asset['tag'].lower()
        if key in seen:continue
        seen[key]=True;rows.append(asset)
    return rows


def foreign_items(settings,context):
    game=sky_game(settings)
    folder=games.profile(settings,game)['cache']
    path=Path(bpy.path.abspath(folder))/'catalogue.json' if folder else None
    stamp=path.stat().st_mtime_ns if path and path.is_file() else 0
    key=('foreign',game,normalized_path(folder),stamp)
    if key not in _cache:
        entries=[('NONE','Choose a sky...','No sky chosen from this game',0)]
        for asset in catalogue_skies(settings,game):
            entries.append((asset['id'],asset['name']+' ('+asset.get('level','')+')',asset['tag'],(zlib.crc32(asset['id'].encode())&0x3fffffff)+1))
        _cache[key]=entries
    return _cache[key]


def invalidate():
    # Blender retains references to enum strings across redraws.
    _retired.extend(_cache.values());_cache.clear()
