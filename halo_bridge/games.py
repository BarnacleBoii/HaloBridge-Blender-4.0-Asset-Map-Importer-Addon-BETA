"""Game capabilities shared by the UI and export destination routing.

Add a validated adapter before enabling another import game or Sapien target.
Import game and export target are intentionally independent.

kit / mcc / generation name the Editing Kit folder, the MCC maps subfolder and
the Osoyoos (Foundry) profile generation used by folder detection.
"""
import json
from functools import lru_cache
from types import SimpleNamespace
from .catalog import detect_paths

GAMES={
    'halo3':dict(label='Halo 3',import_label='Halo 3',map_name='010_jungle.map',import_enabled=True,sapien_enabled=True,scenario_enabled=True,
                 kit='H3EK',mcc='halo3',generation='halo3',scenario='levels\\multi\\guardian\\guardian',sky='levels\\multi\\deadlock\\deadlock'),
    'odst':dict(label='Halo 3: ODST',import_label='Halo 3: ODST',map_name='h100.map',import_enabled=True,sapien_enabled=True,scenario_enabled=True,
                kit='H3ODSTEK',mcc='halo3odst',generation='halo3odst',scenario='levels\\atlas\\h100\\h100',sky='levels\\atlas\\h100\\h100'),
    'reach':dict(label='Halo: Reach',import_label='Halo: Reach',map_name='70_boneyard.map',import_enabled=True,sapien_enabled=False,scenario_enabled=True,
                 kit='HREK',mcc='haloreach',generation='haloreach',scenario='levels\\multi\\70_boneyard\\70_boneyard',sky=''),
    # Halo CE / Halo 2: their kits have no ManagedBlam. Kit scenarios are imported by
    # having the kit's own Tool build a cache file (classic_scenario); Sapien
    # preparation targets Halo 3/ODST.
    'halo1':dict(label='Halo: CE',import_label='Halo: CE',map_name='bloodgulch.map',import_enabled=True,sapien_enabled=False,scenario_enabled=True,classic=True,
                 kit='HCEEK',mcc='halo1',generation='halo1',scenario='levels\\test\\bloodgulch\\bloodgulch',sky=''),
    'halo2':dict(label='Halo 2',import_label='Halo 2',map_name='ascension.map',import_enabled=True,sapien_enabled=False,scenario_enabled=True,classic=True,
                 kit='H2EK',mcc='halo2',generation='halo2',scenario='scenarios\\multi\\ascension\\ascension',sky=''),
    'halo4':dict(label='Halo 4',import_enabled=False,sapien_enabled=False,scenario_enabled=False),
}
IMPORT_ITEMS=[(key,value['import_label'],'Import assets and maps; preparation uses the separately selected Sapien destination') for key,value in GAMES.items() if value['import_enabled']]
SAPIEN_ITEMS=[(key,value['label'],'Prepare using the '+value['label']+' Editing Kit') for key,value in GAMES.items() if value['sapien_enabled']]
SAPIEN_ITEMS+=[('reach','Halo: Reach — not available yet','Reach importing is supported, but Reach Sapien compilation and tag writing are not implemented')]

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

def profile(settings,game):
    """Kit, cache and maps folders for any import game (the current one or its saved profile)."""
    if game==settings.game:
        return dict(kit=settings.kit,cache=settings.cache,maps=settings.maps,game=game)
    profiles=json.loads(getattr(settings,'game_profiles','') or '{}')
    chosen=profiles.get(game) or detected(game)
    return dict(kit=chosen.get('kit',''),cache=chosen.get('cache',''),maps=chosen.get('maps',''),game=game)

def target_game():
    """The Sapien destination of the current scene (Halo 3 outside Blender)."""
    try:
        import bpy
        return bpy.context.scene.halo_bridge.export_target or 'halo3'
    except Exception:
        return 'halo3'

def native(obj):
    """True when an object's original tags live in the destination Editing Kit."""
    return obj.get('hb_game','halo3')==target_game()

# Games built on the same engine generation can reuse each other's tag paths when
# the destination kit already contains that exact tag.
SHARED_TAGS=({'halo3','odst'},)

def shares_tags(source,target):
    return source==target or any(source in group and target in group for group in SHARED_TAGS)

def material_game(obj,mat,target=None):
    """The game a material's shader belongs to.

    An explicitly assigned kit shader wins; then the material's own source
    (material assets); then the object's import game. Hand-made materials
    count as the destination game.
    """
    target=target or target_game()
    return mat.get('hb_shader_game') or mat.get('hb_game') or obj.get('hb_game') or target

def needs_conversion(obj,mat,target=None):
    """True when a material's original shader is not from the Sapien destination game."""
    target=target or target_game()
    return material_game(obj,mat,target)!=target

def source_kits(settings):
    """Every configured import game's Editing Kit path, for reading original collision."""
    profiles=json.loads(getattr(settings,'game_profiles','') or '{}')
    result={}
    for key,value in GAMES.items():
        if not value['import_enabled']:continue
        kit=settings.kit if key==settings.game else (profiles.get(key,{}).get('kit') or detected(key).get('kit',''))
        if kit:result[key]=kit
    return result
