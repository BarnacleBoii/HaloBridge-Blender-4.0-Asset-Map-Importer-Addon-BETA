# Contributing

Thanks for helping. Keep changes focused, and in your pull request explain the problem, what changes, and how you tested it. See [How HaloBridge works](docs/HOW-IT-WORKS.md) for an overview of the code.

**Never commit game content:** maps, tags, extracted meshes or textures, caches, `.blend` files with game data, diagnostic logs, or anything containing your personal folder paths. Tests use synthetic data only.

## Build on Windows x64

You need the .NET 10 SDK, .NET Framework 4.8 (which includes its C# compiler), and a Halo 3 Editing Kit. Use your own kit path:

```powershell
.\source\Build.ps1 -EditingKit 'D:\Games\H3EK'
python .\scripts\package.py
```

- `Build.ps1` builds the extraction helper with `dotnet build` and the tag helper with the .NET Framework `csc.exe`. It references the kit's `bin\ManagedBlam.dll` but never copies it. Both helpers go into `halo_bridge\bin`.
- The source tree includes the modified Reclaimer sources; no separate checkout is needed. NuGet restore needs network access unless packages are cached.
- Builds are deterministic and strip local paths (`source\Directory.Build.props`).
- `package.py` writes the add-on ZIP and the matching source ZIP to `dist\`. It only includes approved helper files and refuses game data and files containing your home folder path. Always publish both ZIPs together.

The tag helper is compiled by the .NET Framework `csc.exe`, which only accepts C# 5: no `?.`, `$""` strings, `out var` or expression-bodied members in `source/TagBridge/Program.cs`.

## Tests

```powershell
python -m unittest discover -s tests -p "test_*.py"
blender --background --factory-startup --python-exit-code 1 --python tests\blender_smoke.py
```

Run every `tests\blender_*.py` file the same way, on both the oldest (4.0) and newest (5.2) supported Blender. Each prints `PASS` when it succeeds. Put Blender version differences in `halo_bridge/compat.py`.

The Blender tests use synthetic meshes and materials and stub out the helpers, so they don't validate ASS output or the game toolchain. When you change export, collision or scenario logic, also do a real local build with your own game files and open the result in Sapien. Record tool versions and a short result in your pull request; don't attach game-derived files.

Useful tests by area:

| Area | Tests |
| --- | --- |
| Games, profiles, mixed-game export | `blender_all_games.py`, `blender_shared_games.py`, `blender_cross_game.py`, `blender_multi_swap.py` |
| `.scenario` import | `blender_scenario_scene.py`, `test_scenario_scene.py` |
| Whole-map import | `blender_map_scene.py`, `blender_map_prepare.py` |
| Sidebar | `blender_activity_ui.py`, `blender_menu_changes.py`, `blender_icons.py` |
| Shaders and materials | `blender_shader_choices.py`, `blender_editable_materials.py`, `blender_editable_layers.py` |
| Collision | `test_collision_policy.py`, `blender_collision_uvs.py` |
| Folder detection, packaging | `test_public.py` |

## Adding a game

`halo_bridge/games.py` is the list of games and what each supports. Import settings (which maps and kit to read) are kept separate from export settings (which kit to build into); don't duplicate the sidebar for a new game. Adding an entry isn't game support: implement and test extraction, material and conversion first, and keep clear error messages for anything not available. Keep the requirements table in [Installation](docs/INSTALLATION.md#what-each-task-needs) in line with what the code actually calls.
