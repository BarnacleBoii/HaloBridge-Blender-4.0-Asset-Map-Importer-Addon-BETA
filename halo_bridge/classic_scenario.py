"""Halo: CE and Halo 2 .scenario import.

Their Editing Kits have no ManagedBlam, so the kit's own Tool builds a cache file
from the scenario tag. HaloBridge then reads that .map like an installed one.
The built map is moved into HaloBridge's storage; any map of the same name that
already sat in the kit's output folder is put back afterwards.
"""
import json
import shutil
import time
from pathlib import Path
from .catalog import fingerprint, read_json, stable_id, write_json
from .jobs import run_process

# Tool arguments and the folder Tool writes the built map to, per game.
BUILD = {
    'halo1': dict(args=lambda scenario: ['build-cache-file', scenario, 'remastered'], output='maps'),
    'halo2': dict(args=lambda scenario: ['-batch', 'build-cache-file', scenario, 'win64'], output='h2_maps_win64_dx11'),
}
SCENARIO_FOLDERS = ('levels', 'scenarios')


def supported(game):
    return game in BUILD


def scenarios(kit):
    """Every .scenario in a Halo CE (tags\\levels) or Halo 2 (tags\\scenarios) kit."""
    root = Path(kit) / 'tags'
    found = []
    for folder in SCENARIO_FOLDERS:
        if (root / folder).is_dir():
            found += [str(p.relative_to(root).with_suffix('')).replace('/', '\\') for p in (root / folder).rglob('*.scenario') if p.is_file()]
    # The UI and shared scenarios are not levels.
    found = [f for f in found if not f.lower().startswith(('scenarios\\ui\\', 'scenarios\\shared\\', 'levels\\ui\\'))]
    return sorted(found, key=str.casefold)


def signature(kit, scenario, game):
    """Changes when the scenario or any tag in its folder changes."""
    tag = Path(kit, 'tags', *scenario.split('\\')).with_suffix('.scenario')
    if not tag.is_file():
        raise RuntimeError('Scenario tag not found: ' + str(tag))
    files = sorted(p for p in tag.parent.rglob('*') if p.is_file())
    return {'classic_scenario': 1, 'game': game, 'scenario': scenario.lower(), 'files': [fingerprint(p) for p in files]}


def build_map(config, scenario, cancel=None, progress=None):
    """Build (or reuse) a cache file for a kit scenario; returns the .map path."""
    game = config['game']
    if game not in BUILD:
        raise RuntimeError('Building a map from a .scenario is only used for Halo: CE and Halo 2.')
    kit = Path(config['kit'])
    if not (kit / 'tool.exe').is_file():
        raise RuntimeError('Choose the ' + {'halo1': 'Halo: CE (HCEEK)', 'halo2': 'Halo 2 (H2EK)'}[game] + ' Editing Kit folder; it contains tool.exe.')
    sig = signature(kit, scenario, game)
    name = scenario.rsplit('\\', 1)[-1] + '.map'
    folder = Path(config['cache']) / 'kit_maps' / game / stable_id(str(kit.resolve()).lower(), scenario.lower())
    built = folder / name
    if built.is_file() and read_json(folder / 'stamp.json') == sig:
        return built
    output = kit / BUILD[game]['output']
    target = output / name
    created = not output.exists()
    backup = target.with_name(name + '.halobridge-' + str(time.time_ns()))
    if target.exists():
        target.rename(backup)
    try:
        if progress:
            progress('Building ' + name + ' with the ' + ('Halo: CE' if game == 'halo1' else 'Halo 2') + ' Editing Kit Tool (Halo 2 can take a few minutes)...')
        log = Path(config['cache']) / 'jobs' / ('build_cache_' + str(time.time_ns()) + '.log')
        run_process([kit / 'tool.exe', *BUILD[game]['args'](scenario)], log, cwd=kit, cancel=cancel)
        if not target.is_file():
            raise RuntimeError('Tool did not produce ' + str(target) + '. See ' + str(log))
        folder.mkdir(parents=True, exist_ok=True)
        built.unlink(missing_ok=True)
        shutil.move(str(target), str(built))
        write_json(folder / 'stamp.json', sig)
        write_json(folder / 'source.json', {'kit': str(kit), 'scenario': scenario, 'built': time.time()})
    finally:
        if target.exists() and backup.exists():
            target.unlink()
        if backup.exists():
            backup.rename(target)
        if created and output.is_dir() and not any(output.iterdir()):
            output.rmdir()
    return built


def map_config(config, built):
    """A config whose maps folder is the built map's folder."""
    return dict(config, maps=str(Path(built).parent))


def mark_rows(rows, scenario):
    """Indexed rows from a kit-built map show and filter as .scenario assets."""
    for row in rows:
        row.update(source='scenario', scenario=scenario, level=scenario.rsplit('\\', 1)[-1])
    return rows
