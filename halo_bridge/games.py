"""Game capabilities shared by the UI and export destination routing.

Add a validated adapter before enabling another import game or Sapien target.
Import game and export target are intentionally independent.
"""
import json
from functools import lru_cache
from types import SimpleNamespace
from .catalog import detect_paths

GAMES={
    'halo3':dict(label='Halo 3',import_label='Halo 3',map_name='010_jungle.map',import_enabled=True,sapien_enabled=True),
    'reach':dict(label='Halo: Reach',import_label='(Experimental) Halo Reach',map_name='70_boneyard.map',import_enabled=True,sapien_enabled=False),
    'halo1':dict(label='Halo: CE',import_enabled=False,sapien_enabled=False),
    'halo2':dict(label='Halo 2',import_enabled=False,sapien_enabled=False),
    'odst':dict(label='Halo 3: ODST',import_enabled=False,sapien_enabled=False),
    'halo4':dict(label='Halo 4',import_enabled=False,sapien_enabled=False),
}
IMPORT_ITEMS=[(key,value['import_label'],'Import assets and maps; preparation uses the separately selected Sapien destination') for key,value in GAMES.items() if value['import_enabled']]

@lru_cache(maxsize=None)
def detected(game):
    return detect_paths(game)

def destination(settings):
    if not hasattr(settings,'export_target'):return settings
    game=settings.export_target
    if game==settings.game:
        return SimpleNamespace(kit=settings.kit,cache=settings.cache,maps=settings.maps,game=game)
    profiles=json.loads(settings.game_profiles or '{}')
    profile=profiles.get(game) or detected(game)
    kit=profile.get('kit','')
    return SimpleNamespace(kit=kit,cache=profile.get('cache',''),maps=profile.get('maps',''),game=game)
