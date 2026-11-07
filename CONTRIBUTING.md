# Contributing

Keep changes focused and explain the problem, resulting behavior, and validation. Do not commit game data, extracted assets, private paths, diagnostics, or project caches. The repository's public tests generate synthetic fixtures.

## Build on Windows x64

Install .NET SDK 10, .NET Framework 4.8 (including its C# compiler), and the Halo 3 Editing Kit. Use your own kit path:

```powershell
.\source\Build.ps1 -EditingKit 'D:\Games\H3EK'
python .\scripts\package.py
```

The build reads `bin/ManagedBlam.dll` from the kit as a reference but does not copy it. Release helpers go into `halo_bridge/bin`. The source tree includes the modified Reclaimer sources; no separate checkout is required. NuGet restore requires network access unless packages are already cached.

The packager emits the Blender add-on ZIP and matching source ZIP in `dist/`. It only packages approved helper files and rejects game data and personal build paths. Always distribute both ZIPs together. Never package the repository's parent directory or a local demo project.

## Tests

```powershell
python -m unittest discover -s tests -p 'test_*.py' -v
blender --background --factory-startup --python-exit-code 1 --python tests/blender_smoke.py
blender --background --factory-startup --python-exit-code 1 --python tests/blender_catalogue.py
blender --background --factory-startup --python-exit-code 1 --python tests/blender_map_scene.py
```

The Blender smoke test uses a synthetic triangle and material; it replaces the external extractor/exporter checks for this UI-only test. It does not validate ASS output or the game toolchain. Perform a separate local compile and Sapien check with your own game files when changing export or scenario logic.

Do not submit game-derived fixtures. Record tool versions and a short result summary instead. See TESTING.md for the current release's verification scope.

## v0.9 shared game framework

`halo_bridge/games.py` is the capability registry and destination resolver. Keep import profiles separate from export settings; don't duplicate the sidebar for new games. Adding a registry label is not game support: implement and validate extraction/material/conversion adapters first. Preserve explicit failure reporting for unavailable destinations.

Run `tests/blender_shared_games.py`, `tests/blender_multi_swap.py`, `tests/blender_cross_game.py`, and `tests/blender_current_geometry.py` for changes in those areas. Tests requiring game tools are separate from UI/synthetic tests. Keep documentation's requirements matrix aligned with actual helper calls and setup-check behavior.

## v0.9.1 regression areas

Run tests/blender_shader_choices.py for filtered shader search and active-material assignment, and tests/blender_activity_ui.py for panel drawing. Changes to original collision, temporary instance partitioning and editable materials should cover source identity, transforms, shared materials and preservation of scene geometry. Game-derived fixtures stay local and must be excluded from commits and packages.
