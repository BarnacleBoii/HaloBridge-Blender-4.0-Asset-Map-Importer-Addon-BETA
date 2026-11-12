# v0.10.0 verification

## Windows run (Windows 11 x64, Blender 5.2.3, H3EK, .NET SDK 10.0.401, .NET Framework csc)

- `source\Build.ps1` built both helpers. The tag helper compiled with the C# 5 `csc.exe` unchanged (only CS0649 warnings on JSON fields).
- 41 Python unit tests passed (including the 4 that failed on Linux and the Windows-only test).
- All 29 `tests/blender_*.py` passed in background mode on Blender 5.2 with toolset v364 loaded. Several older tests had stale fixtures (UI labels, sky menu mock, shader-validated fixtures, prepare-time source linking) and were updated; `blender_vehicles.py` now checks the ZYX round trip instead of the pre-fix XYZ angles.
- Real Guardian import (`levels\multi\guardian\guardian`): 1/1 BSP from embedded ASS, 1023 objects (56 structure, 479 BSP instances, 296 special surfaces, 76 scenery, 83 crates, 20 weapons, 12 equipment, 1 sky), all 67 object render models from embedded JMS, 4 genuine warnings. Field names read as expected: `structure bsps`, the seven `<category>`/`<category> palette` blocks, `object data` position/rotation/scale (191/191), `variant name` (none set on Guardian), `default model variant` (10 objects).
- Rotations: all 191 placements match the scenario yaw/pitch/roll to float precision, including 38 pitched or rolled ones; the export formula round-trips all of them (max matrix error 2e-5, near ±90° pitch). The pre-0.10 XYZ formula gave wrong orientations for 37 of the 38.
- Fixed by this run: JMS names/material definitions are whole lines (all render models previously fell back to the map), lighting parameters such as `lm:5.0` in material names aborted the import, `<collection>\shaders\<name>` shader lookup, unbalanced trailing `)` in shipped weapon material names, a Blender crash showing the warnings popup in background mode, and an unregistered-property error in editable materials. The scenario cache version was bumped so 0.10.0 test caches rebuild.
- Multi-BSP campaign import (`levels\solo\030_outskirts\030_outskirts`): 6/6 BSPs, 6298 objects including 11 vehicles, machines and controls, `variant name` read on 45 placements (368 objects carry a variant). 1012 placements (646 pitched or rolled) match the scenario rotation; 183 scenery and vehicle placements round-trip through the export planners. Remaining warnings are data issues (pathfinding and cinematic-anchor objects without render models, two empty palette slots, five materials without a matching shader in their tag).
- Fixed by the Outskirts run: ASS strings with an embedded quote (`"%"-?bridge_cliffsupp05"`) stopped a BSP from loading; material names with `)` before their symbols (`blur)!=`) or a leading apostrophe; ambiguous shader leaves now prefer the named collection's folder; vehicle and static-export scale/shear checks use relative tolerances (float32 rounding at 100x working scale rejected 4 of 11 vehicles).
- Toolset v364 cannot export on Blender 5.2: its operators read caller locals through a frame hack that Python 3.13 breaks. HaloBridge now detects that hack and stops before exporting with a clear message. The current release, v432 (`master-432`), copies the locals instead and works; it is no longer reported as Blender 4.0-only.
- With toolset v432 on Blender 5.2: 41 unit tests and all 29 Blender tests passed, and Sapien preparation of the Guardian scenario import completed in 144 s (lighting off) to `levels\multi\hb_guardian_test`: structure BSP, lighting info, generated shaders, sky and 76 original scenery placements. Read back through the tag helper, all 76 placements match the source scenario (position 2e-6, rotation 4e-7, scale 2e-7). Tool reported 12 geometry warnings (overlapping surfaces on 10 instances, 2 partially untextured pieces).
- `scripts\package.py` produced both audited ZIPs; the add-on ZIP installs and enables in a clean Blender 5.2 profile.

- Windowed Blender 5.2 (not background): the sidebar threw on the Preview Mode icon (`SEQUENCE_COLOR_*` is `STRIP_COLOR_*` in Blender 5), so nothing below it was drawn, including Prepare for Sapien; the Collision list named a nonexistent UIList. Both fixed; the full panel now draws with and without a scenario import. Background tests use mock layouts and could not catch this; `tests/blender_icons.py` now checks names against the real Blender.

- A user's Guardian scene failed in Tool with NaN texture coordinates. The source meshes were clean; `add_collision_geometry` added loops whose UVs Blender 5.2 leaves uninitialized, so the affected objects changed between runs. After the fix, two exports of that scene had no non-finite values and Tool compiled it in 97 s. `tests/blender_collision_uvs.py` covers it.

- Multi-game round (Blender 5.2.3, H3EK, H3ODSTEK, HREK, rebuilt helpers):
  - **ODST:** `h100.map` indexes 4,571 assets; scenery, instance, model and material extraction work; whole-map import of `h100` decodes 11/11 BSPs (16,302 placements). Scenario import of `levels\atlas\sc100\sc100`: 4/4 BSPs from embedded ASS, 5,271 objects, 397 of 471 materials textured from `sc100.map`; Index .scenario Assets lists 1,134 rows and placing one of each kind works. 4 BSP objects in Bungie's source have no material assigned (index -1) and are skipped with a note.
  - **ODST Sapien:** preparation of 40 scenario scenery, 3 vehicles and a floor using an indexed ODST shader completed in 10 s (lighting off) to `levels\multi\hb_odst_test` in H3ODSTEK. Read back: 40 scenery, 3 vehicles, 1 player start, 1 sky, 1 BSP. Fixed by this run: ODST's player start block has no `bsp index` field.
  - **Reach:** scenario import of `levels\multi\70_boneyard\70_boneyard` places 8,471 objects. HREK ships no source models or BSP sources, so 2 BSPs and 57 object models come from `70_boneyard.map`; the developer "hidden" BSP fails to decode, as it does in whole-map import. Index .scenario Assets lists 1,170 rows. Fixed by this run: Reach object names are string IDs.
  - **Halo 3 regression:** Guardian scenario import unchanged (1/1 BSP, 1,023 objects, 389 index rows); the starter template still prepares in 10 s.
  - 41 unit tests and 33 Blender tests pass (new `tests/blender_menu_changes.py`). The windowed sidebar draws with every section open; screenshots checked the boxed sections, the side-by-side tabs and the source filter.

**Still not verified:** opening the prepared level in Sapien and comparing it visually, Sapien preparation of a multi-BSP campaign scenario, and preparation with lighting enabled. Blender 4.x is no longer a test target.

## Linux run

Run on Linux without Windows, Blender, H3EK or game files:

- 39 Python unit tests ran: 34 passed, 1 skipped (Windows-only) and 4 failed. The 4 failures (`test_copy_level`, two `test_map_export` and `test_progress`) also fail on unchanged v0.9.1 code there: they depend on Windows path and process behavior.
- New `tests/test_scenario_scene.py` (11 tests): ASS/JMS parsing, instance transform composition, BM_FLAGS and name-symbol flags, variant and LOD selection, Halo yaw/pitch/roll against Reclaimer's quaternion order, checksum rejection, shader resolution through BSP references and shader collections, and the full extract → manifest → texture merge → cache reuse flow with a mocked helper.

**Not yet verified, needs a Windows run before release:**

- The C# helpers were not compiled here. Build them with `source\Build.ps1` (the tag helper uses the .NET Framework C# 5 compiler).
- `tests/blender_scenario_scene.py` and the existing Blender tests have not been run on Blender 4.0 or 5.2.
- No real H3EK scenario has been imported yet. First check: Guardian or High Ground, then a campaign level with several BSPs. Confirm the scenario field names (`structure bsps`, palettes, `object data`, `variant name`, `default model variant`) read as expected, and that placement rotations match Sapien.
- Sapien preparation with original scenery placements from a scenario import.

# v0.9.1 verification

Release checks passed for all 28 Python tests, both audited ZIP archives, local documentation links, and shader-picker/panel checks against the extracted installer.

- The painted Halo 3 and Reach Elite fixtures compiled together in an isolated Halo 3 level with original collision geometry. The larger Elite exported as two aligned instances. That compiler run reported no geometry warnings. Contact and multiplayer playtests remain separate.
- The actual Jungle layered shader and editable version produced matching initial color bakes within the test tolerance. The paint operator targeted the mask, and changed mask pixels changed the baked result. This does not claim a manual brush-stroke usability test.
- Snowbound source inspection recovered the missing detail-map parameter and two-detail-overlay options. The corrected material graph baked successfully. Paired-glass inspection found opposite-facing coincident triangles and enabled local backface culling. Interactive flicker confirmation remains pending.
- Blender 4.0 regression checks passed for shader category switching, captured popup items, active-material assignment and panel drawing. These are programmatic checks rather than a complete mouse-driven UI test.

Historical checks below describe their own build versions. They do not imply every old fixture was rerun for v0.9.1.

# v0.9 validation summary

The release passes 28 automated Python checks and targeted background Blender checks for shared game routing, Reach material conversion, multi-object swapping, warning confirmation and sidedness policy. UI-only checks do not prove game behavior. Isolated Halo compiler tests passed for a Citadel pine and single-sided floor. A separate user scene compiled in about 95 seconds after a reversible terrain reduction; lighting/play testing were not included, and five nonfatal warnings remained.

The current minimum-dependency, MCC-only installation has not been validated on a clean second machine. Requirements distinguish code paths from setup-checker policy; do not describe all placement as kit-free. Native Reach Sapien and future games remain unavailable.

The sections below retain historical verification details; older two-sided tests describe those builds, not the current default export policy.

# 0.7.0 checks

22 Python regression tests and five Blender suites passed: origins/game profiles, map layout, previews, catalogue and Halo 3 preparation dispatch. Origin tests cover authored, shared, hidden and previously marked meshes, unchanged world geometry and median centers. Game profiles restore saved settings.

Real Reach Boneyard: 2,037 indexed assets; 8,474 extracted placements (29 terrain, 7,700 BSP instances, 505 scenery, 28 machines, 6 controls, 200 crates, 6 skies). Decoded 2 of 3 BSPs; the hidden BSP failed and is reported. A representative 21-placement Blender import covered all groups and matched source matrices. Instance/scenery/material extraction and repeat-cache reuse passed. This does not validate every Reach map or placement, or Reach Sapien export.

# Verification history

## 0.6.7 early public release

All 22 Python unit tests and the Blender 4.0 synthetic UI smoke test passed for the public-name and documentation update. Extraction and current-mesh export algorithms are unchanged from 0.6.6. Earlier Sapien checks below are historical results, not a new end-to-end run for this documentation release. Proportional Editing was found enabled during live troubleshooting of overlapping copies; switching it off resolved the setting responsible for moving nearby unselected objects.

## 0.6.6 paste movement

Blender 4.0 native clipboard tests verify that translating pasted previews and ordinary assets leaves the original transform unchanged. Includes retained preview selection, active object correction, Shift+D and preview cleanup. Tests use an isolated clipboard directory.

## 0.6.5 preview copying

Blender 4.0 native copybuffer/pastebuffer and object.duplicate tests passed in an isolated temporary clipboard directory. Pasted previews retain transforms, become render-visible/exportable assets with fresh IDs, and survive switching Preview Mode off. Ordinary asset paste also survives cleanup. Live preview, catalogue and preparation dispatch regression scripts passed. Tests did not use the user's open scenes or Blender clipboard.

## 0.6.4 runtime follow-up

The saved 849-object Shrine Blender scene compiled through the current-mesh route. Generated tags contain 932 instances after Tool processing, 724 collision definitions and 267,650 collision surfaces. The scenario references the Shrine sky and has a test player start. Loaded it in Sapien and entered player simulation: textured terrain and structures render, and the player appears above the terrain. No draft lighting was built for this test. Overlapping-surface debug markers and stock tag warnings remain; this is not a complete-map gameplay or traversal acceptance test.

The initial largest-face spawn picked an underground skirt. A new ray test chooses the uppermost exposed surface at the cursor. The regression fixture includes a larger underground plane beneath the intended platform. It passes. Existing Sapien starts are not overwritten; the disposable test scenario's old generated start was relocated separately for this check. Sapien retains its editor camera independently of player starts, so an old camera can remain underground while Tab player simulation uses the correct spawn.

## 0.6.3 current-scene geometry

22 Python tests and seven Blender background regression scripts passed (current geometry, preparation dispatch, previews, catalogue, diagnostics, map import and repair). The geometry test checks an edited vertex, nonuniform scale, evaluated bevel modifier, deletion, and preservation of source meshes/transforms. Repair retains edits and intentional deletions.

A 20,000-row synthetic catalogue filtered a single map in approximately 10 ms (All Levels approximately 17 ms); this measures the filter pass, not the entire viewport redraw.

Real Tool builds passed for an edited closed mesh and an open two-sided plane, with original shader references staged under unique names. Compiled collision was inspected: the moved vertex is at (-3.75,-3,-0.5), instance position (2,3,0), instance scale 1, with 8 collision vertices and 7 surfaces. A test player start and the Shrine sky reference were verified in the generated scenario. Repeated compilation passed. These checks do not constitute live Sapien player-traversal acceptance.

## 0.6.0

13 Python tests passed, including original-map repeat preparation, conflict detection, unowned-output protection and cancellation rollback. Blender background checks passed for messages, controls, import matrices/cache sharing and Prepare dispatch/sky selection. Real Shrine cache: 849 imported pieces validated; modified-piece rejection tested. Prepared a separate Shrine scenario and verified all 330 BSP instance records and 110 collision definitions against the source. Added/moved/removed scenery and sky switching passed. Original gameplay blocks were verified after allowing appended managed name/palette bookkeeping and selected sky changes. Runtime follow-up: Shrine displays textured terrain and structures after moving the camera above ground. The original test camera/player start was at Z -21.5137, underneath the terrain; the above-ground check used Z 0. The test spawn was changed only in the disposable Sapien session, not saved. Player simulation was started, but full gameplay/collision traversal acceptance is still outstanding. Missing audio/object-function and decal warnings remain separate issues.

# Release verification

## 0.5.0 original-coordinate map import

Rebuilt the scene extractor and exercised real MCC High Ground and jungle inputs in Blender 4.0. High Ground imported 1,449 mesh placements sharing 397 meshes (1/1 terrain BSPs decoded). Jungle imported 5,251 mesh placements sharing 802 meshes (12/13 terrain BSPs decoded); its intro BSP returned Data not found. Reports contained 10 and 54 warnings respectively, including missing models and approximate variants. Every imported Blender world matrix was compared with the extracted row-vector transform after transposition; the cursor was deliberately moved away from the origin. Original gameplay, collision, final lighting and complete variant fidelity are not verified or provided.

Synthetic tests passed for known translations, rotations and scales, mesh sharing, collection isolation, cursor independence, report generation, routing of the old full-map action, and cancellation rollback. Existing preview and catalogue tests also passed.


## 0.4.0 controls and batch import

Blender 4.0 tests passed for unified placement, coincident batch positions, independent category filters, material loading without a target mesh, continuing after a synthetic missing-texture failure, full-map asset indexing/import with synthetic fixtures, and cancellation during the main-thread placement phase. The real jungle starter material was loaded and its image pixels, shader nodes, floor UVs, and Material Preview setting verified. Full 1,334-entry import has not been benchmarked or completed as a release test. Original playable-level reconstruction is not implemented.


## 0.3.0 catalogue update

Blender 4.0 synthetic smoke and catalogue tests passed: filtered checkbox selection; hide/unhide ordering and persisted state; model and material batch placement; replacement identity/transform preservation; catalogue-only deletion; rollback after a partially created batch; cancellation; empty-tab preview handling. These tests use no game-derived fixtures. The C# helpers and compilation pipeline are unchanged from 0.2.0.


## 0.2.0 public alpha

Verified locally on Windows x64 with Blender 4.0.0 and Halo Asset Blender Development Toolset 2.364.0:

- Both helpers rebuilt successfully from the public source tree using .NET SDK 10 and the installed Editing Kit reference.
- Ten Python tests passed: unsafe output names, mapping preservation, transactional rollback, cancellation, zero-exit compiler errors, asset identity, custom Steam libraries, broken optional Osoyoos settings, actionable missing requirements, and package rejection of private content.
- Asset-free Blender smoke test passed: live selection previews, transform-preserving placement, off during loading, selection restoration, automatic storage, and registered tooltips.
- Setup checks passed against an actual local installation.
- Fresh extraction of an MCC jungle tree, its collision, and a terrain material passed using the public helper build without native xcompress DLLs. Repeat requests reused cached output.
- Release archives are checked for game-file extensions, private project metadata, debug symbols, native xcompress binaries, and the packaging user's home path in both text and binary data. Source Python files are syntax-checked.
- The packaged add-on ZIP passed the synthetic Blender smoke test after extraction to an isolated folder. Both helpers also rebuilt successfully from the packaged source ZIP.

Earlier local 0.1 builds compiled and lit a small jungle level, loaded it in Sapien, verified source collision and transforms, and exercised repeat exports preserving independent scenery and player starts. Those game-derived fixtures and local reports are deliberately excluded from this repository. The complete compile-and-Sapien demonstration was not repeated for 0.2.0; the export/scenario algorithms are unchanged.

Not yet verified: a second clean Windows computer, other Blender/exporter versions, arbitrary MCC map revisions, multiplayer packaging, giant-map performance, and automatic migration of existing projects between machines. Report this release as an alpha, not a universal or fully validated converter.

0.6.1: 19 Python tests pass, along with the Blender preparation/sky/report check. Source recovery checks cover CRC, truncated streams, excessive expansion and trailing data. Real Shrine ASS recovery matches Halo Tool byte-for-byte (10,933,733 bytes), and repeated recovery reuses the cache. Source material matching identifies 39 slots from the original BSP references, but this installed Tool still rejected the collection-prefixed experiment. Preserving the original level-local shader folder resolved missing shader errors in the subsequent isolated source rebuild. Compiler completion alone is not export acceptance. Source recovery is backend groundwork and is not yet wired into edited-map preparation.

0.6.2: 22 Python tests passed, including all-error retention and retrying incomplete map caches without overwriting previous files. Blender async diagnostics preserved all 35 fixture errors in the report and persistent file; map preparation/sky/report regression passed. A fresh complete Citadel extraction decoded 16/16 BSPs. Targeted Jungle intro decoding still fails with Data not found despite 17 clusters and 237 instance records. Those records alone do not establish recoverable geometry or export readiness.


## 0.8.7 original vehicle route

Blender checks cover model-to-tag selection, exclusion from static export, transforms, duplicate placement IDs, cached-origin correction and rejection of reshaped models. Real ManagedBlam checks cover add/move/delete, duplicate prevention, existing vehicle preservation, unchanged source tags and conflict rejection before saving. A separate test level compiled with a cached Halo 3 Scorpion preview excluded from its ASS; the resulting scenario references the original Scorpion vehicle tag. Test lighting was disabled for that isolated test. No driving or multiplayer playtest is claimed. No mesh-splitting implementation is shipped.
