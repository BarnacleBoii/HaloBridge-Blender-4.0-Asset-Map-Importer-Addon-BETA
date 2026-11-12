## 0.10.0 — Editing Kit scenario import and Blender 5.2

- **Import level from .scenario.** New Halo 3 route that reads a level from its Editing Kit `.scenario` tag with ManagedBlam: BSP geometry from the ASS source stored in each BSP tag, instance names and transforms, all scenery/crate/machine/control/vehicle placements with variants, weapons/equipment for reference, skies, and the exact shader tag of every surface with its source flags. The matching `.map` is used only for preview textures (looked up by shader path) and as a reported fallback for render models without embedded source.
- **Original scenery placements.** Unedited scenario scenery is prepared as placements of its own scenery tag (keeping its collision, physics and variants); vehicles keep their vehicle tags. Edited objects export as static geometry and are listed in the preparation warnings.
- **Original collision lookup** accepts the scenario's model tag when it differs from the render model path.
- **Blender 4.0 to 5.2.** Handles the removed Auto Smooth setting, EEVEE Next material render methods, brush assets (4.3+), per-mode unified paint settings (5.0+) and registered-property access (5.0+). On Blender 4.1+, the toolset is accepted when it provides the ASS export options and material flags HaloBridge uses (v432 or newer, verified with v432 on 5.2); 4.0 keeps the v364/v432 requirement.
- **Faster mesh signatures** using bulk reads; the digest is unchanged, so existing scenes stay valid.
- **Fixed:** original vehicle and invisible-block placements now use Halo's yaw/pitch/roll order (Blender `ZYX`), matching scenery export and Reclaimer. Objects with pitch or roll were previously rotated incorrectly.
- **Fixed after the first H3EK run (Guardian):** JMS names and material definitions are read as whole lines, so render models use their embedded source instead of the map; material names with lighting parameters (`lm:5.0`) no longer abort the import; shader collections resolve `<folder>\shaders\<name>`; an unbalanced trailing `)` in weapon material names is ignored; the preparation warnings popup no longer crashes background Blender. Cached scenario scenes from earlier 0.10.0 test builds are rebuilt.
- **Fixed after the Outskirts run (6 BSPs):** ASS names containing a quote no longer drop a BSP; `blur)!=`-style and `'name` material names resolve; shaders in collection subfolders resolve; imported vehicles and static objects are no longer rejected for float rounding of their 100x scale. Toolsets that still use v364's frame-locals hack now stop with a clear message on Blender 5.x instead of failing inside the ASS export; v432 is accepted and no longer reported as Blender 4.0-only.
- **Fixed on Blender 5.x:** the sidebar stopped drawing below Preview Mode (Blender 5 renamed the `SEQUENCE_COLOR_*` icons), hiding Prepare for Sapien and every section after it. The Collision material list now uses Blender's `MATERIAL_UL_matslots`. New `tests/blender_icons.py` checks icon and list names against the running Blender.
- **Fixed:** generated box collision left the new faces' UVs uninitialized on Blender 5.2, so a random set of objects exported NaN texture coordinates and Tool rejected the level ("mesh definition vertex texcoords invalid"). Collision faces now get zero UVs and white colors, and any remaining non-finite UVs are set to 0 in the export copy and listed in the preparation report.
- **Sidebar:** every section collapses (Folders and Setup, Indexed Asset List, Selected Asset, Materials and Shaders, Collision, Editable Materials, Sky, Map Preparation); warnings, preparation status and the Prepare button stay visible. Each terrain shader layer (up to four) is its own collapsed section with its Paint button in the header. **Import level from .scenario (Recommended)** is followed directly by **Import entire .map**. Removed **Repair incomplete map import**. New **Remove Grey Blender Fog (View Distance)** sets Clip Start 0.1 / Clip End 999999.
- **Starter template:** a paintable Jungle terrain plane, a see-through SkyBoundary wall (+sky faces are dropped in preparation, which builds its own sky boundary) and Master Chief for scale (not exported), extracted from `010_jungle.map`.
- **Halo 3: ODST** is a full game: index and import `.map` files, **Import level from .scenario** from the H3ODSTEK, and Sapien preparation into the ODST Editing Kit (original scenery, vehicles, sky and test spawn). Selecting a game whose kit supports Sapien also sets **Export to Sapien** to it.
- **Halo: CE and Halo 2 importing** from MCC `.map` files: Index .map Assets (shaders, models, scenery, Halo 2 instanced geometry), preview/placement and Import entire .map (all BSPs, skies and object placements; tested on Blood Gulch, a10 9/9 BSPs, Ascension and Old Mombasa 4/4 BSPs).
- **Every game in a Halo 3 level.** Material conversion, previously Reach-only, now covers any asset whose shader is not from the Sapien destination (ODST, Reach, Halo CE, Halo 2; Halo 3 assets in an ODST level). Layered/detail previews fall back to the textures recorded at import; ODST shaders that exist in H3EK are reused. Original collision is read from each asset's own kit.
- **Sidebar:** the per-material **Collision** control is removed (settings saved by older versions are ignored; the toolset's **Render Only** material flag still works); Object collision's first choice reads **(Default) Automatic**; the output level name starts as **levelname123**; **Import game** lists **Halo: Reach** without "(Experimental)".
- **Folder detection on other PCs:** **Detect folders** also finds MCC installed through the Xbox app / PC Game Pass (`XboxGames`), checks only local fixed drives (no stalls on card readers or network drives), reads Foundry settings from `%APPDATA%`, and only accepts a maps folder that contains `.map` files. New storage goes in the real Windows Documents folder, including one redirected by OneDrive; an existing `Documents\HaloBridge` keeps being used.
- **Documentation rewritten:** new installation guide with a per-task requirements table, importing guide, first-map tutorial, a sidebar reference covering every control, a new supported-games page, and refreshed troubleshooting, limits, editable materials, Reach and how-it-works pages.
- **Fixed: Remove Grey Blender Fog** set Clip Start/End in Blender units, so with HaloBridge's 0.03048 unit scale they read 0.003048 m and 30480 m. They are now set in the scene's displayed units: 0.1 m and 999999 m.
- **Halo: CE and Halo 2 .scenario import.** The kit's own Tool builds a map from the scenario (`build-cache-file`), which is then imported or indexed like an installed map; the built map is cached until the scenario's tags change, and a map of the same name in the kit's output folder is restored. Tested with Blood Gulch (HCEEK) and Ascension (H2EK).
- **Skies from any game.** **Sapien Sky** now has a **Game** choice. The destination game keeps its Editing Kit sky list; for any other game a sky model from its asset list is placed in a **Sapien Sky** collection and, on preparation, converted (self-lit textures, `render-sky` render model, model and scenery tags) and set as the level's sky. Test lighting is baked with the destination kit's sky first, since converted skies carry no sky lighting. Tested with Halo: CE's "mp clear afternoon" in a Halo 3 Blood Gulch level and Halo 2's Ascension sky in a Halo 3 Ascension level. Halo: CE and Halo 2 sky layers use additive blending.
- **Fixed: white Halo: CE and Halo 2 textures.** Halo 2 shaders whose template Reclaimer does not recognise (skies, many effects) lost their bitmaps or kept them only as transparency, and Halo: CE `shader_transparent_generic` shaders had no textures at all (and were missing from the index). Such shaders now use their own bitmap as the base texture, skipping Halo 2's `default_bitmaps` placeholders. Halo: CE / Halo 2 assets and whole-map imports are re-extracted once.
- **Tool collision rejections are retried automatically:** objects whose collision Tool reports as ambiguous or degenerate are recompiled with a simple box, then without collision (up to three compiles), and listed in the report. Collision with welded overlapping pieces is detected before export. Fixed a Blender crash (access violation) when adding collision to meshes with converted materials.
- Sky models placed from an index are omitted like imported skies; objects beyond Halo 3's 10,000 world-unit limit are reported before Tool runs.
- **Halo: Reach .scenario import:** placements come from the HREK scenario tags. The Reach kit ships no source models or BSP sources, so geometry comes from the matching `.map` and this is stated in the import report. Reach Sapien preparation is still unavailable: the Halo toolset's ASS exporter only targets Halo 2/3.
- **Index .scenario Assets:** lists every distinct object, instanced mesh and shader in a scenario in the Indexed Asset List, next to **Index .map Assets**. A new source filter (All Sources / .map Assets / .scenario Assets) shows a one-line summary of what each source is best for.
- **Apply material to selected object** adds the material as a new slot and assigns it (only the selected faces in Edit Mode) instead of replacing the existing material. Unused slots are ignored at export.
- **Sidebar:** each section has its own box; Imported/Hidden Assets sit side by side; **Materials and Shaders** is now **Shaders** without the level filter and shader count; **Remove Grey Blender Fog** uses Clip End 999999; the output level name starts as the placeholder **Level_Name_Here**, which Prepare asks you to replace.
- **Helpers:** new `scenario_scene` tag-helper operation and `materials` extractor operation; ODST maps; Reach shader previews for scenario imports; Reach object names (string IDs) and the ODST spawn block. Rebuild both helpers (`source\Build.ps1`).
- Add-on renamed to **HaloBridge - Halo Level Importing**.

## 0.9.1 — collision, materials and shader workflow

- **Original collision first.** Automatic collision tries verified source collision geometry for eligible imported models and BSP instances. Edited or unmatched objects use the available box or surface fallback. Preparation reports list the collision route for each exported static object.
- **Large static models.** Oversized instances can export as several aligned Halo instances while staying one editable Blender object. This addresses the Reach Elite render-index overflow while retaining its visible triangles.
- **Paintable terrain.** Supported layered terrain starts with the original blended appearance. Numbered shader-layer buttons paint an overlay, and Paint original blend restores the source mixture. Texture resolution has 512, 1024, 2048 and 4096 options. Repeat controls start collapsed.
- **Original vehicle paint.** Editable colors can generate level-local vehicle/model/render-model copies for matched Halo 3 vehicles, with the original gameplay and physics references retained.
- **Snowbound materials.** Halo 3 previews now support default, detail blend, two-detail and two-detail-overlay albedo operations when their parameters are available. The missing second detail texture is extracted, restoring Snowbound's purple icy-metal layer.
- **Paired transparent faces.** Imported meshes whose transparent triangles all have opposite-facing mates get a local material with backface culling, reducing overlapping front/back rendering. This preserves the mesh faces.
- **Shader controls.** Materials and Shaders identifies the active object/material. Assign shader to active material explains its Sapien effect. The picker captures its chosen category, shows the matching count, and keeps manual path entry. Collision controls have their own section.
- **Texture-loading label.** The button is now Load Halo Shader Textures/Masks for Currently selected Material.
- **Neutral normal fallback.** The known unreadable default_vector placeholder can use a flat normal instead of interrupting extraction for that specific decode error.

## 0.9 — shared game workflow and documentation refresh

## v0.9 public early release refresh

Added selectable and separable model variants, terrain painting, static color masks and support for toolset v432. Updated source-map lookup, wrapped color UV validation and reporting of recoverable instance collision diagnostics.


- Shared Halo 3/Reach panels with independent Halo 3 export routing and one saved kit path.
- Multi-object greybox swapping using original asset scale; map picker with manual filename entry.
- Single-sided and open-surface handling, structure-source diagnostics, reports opening at line 1.
- Mirrored warnings panels, preview status icons and placement highlighting.
- Workflow-specific installation requirements, Blender-only import guide and updated user documentation.
- Earlier 0.8.6–0.8.9 work included original Halo 3 vehicle placement, foliage collision policy and live preparation logs; see TESTING.md and release history for scope.

## 0.8.5 — preparation fixes and searchable material/sky pickers

- **Skip objects with export problems:** optional partial preparation lists each excluded object and reason before confirmation. Objects stay in Blender. Compiler failures still stop preparation; at least one valid mesh is required.
- **Material validation:** uses materials assigned to evaluated faces. Unused material slots no longer prevent export. Highlighting an Asset List material still does not assign it.
- **Preparation warnings:** Continue/Cancel remain visible above Prepare. Warnings are no longer saved as failed builds, and underlying error lists are no longer overwritten by a generic confirmation error.
- **Existing shader picker:** shaders are grouped by level/shared category and selected through a searchable popup. Use Scan existing shaders first. Manual path entry remains available.
- **Sky picker:** searchable selection, visible selected scenario path, and selection stored independently of the scanned list. Use Find map skies first.
- **Level Imported:** normalized map-name matching and retained dropdown entries improve selection stability. The exact reported disappearance was not reproduced locally.
- **Static model:** replaces the confusing Source check label.
- **Export target:** Halo 3 supported; Reach Sapien is explicitly unavailable. Reach assets can still be converted to static Halo 3 geometry.


## 0.8.4

- Display original Halo material and bitmap names while preserving cache IDs, shader paths and image filenames.
- Upgrade old hashed material and numeric image names on scene load; recover missing bitmap names from the source map metadata. Preserve custom names and distinguish duplicate names with Blender suffixes.
- Keep Reach conversion IDs stable across display-name migration.

## 0.8.3

- Show current asset names and counts during material checks, mesh preparation and player-start checks.
- Show 16 numbered lighting stages, elapsed tool time, last output and time since output; no estimated percentage.
- Rename Folders and Setup and Halo 3 .map Files.

## 0.8.2

- Fix lightmapping scenes exported entirely as instances: export one existing renderable mesh as main structure, preferring authored geometry; retain other meshes as instances.
- Include the chosen structure object in the preparation report. Reject scenes containing no renderable surfaces before compilation.

## 0.8.1

- Clarify experimental Sapien preparation, shader, sky and repair labels.
- Add a separate preparation status box and loading button text, resetting after completion, cancellation or errors.

## 0.8.0

- Convert imported Reach meshes and preview textures into static Halo 3 level geometry, bitmap/shader tags and generated collision.
- Keep source meshes/materials/UVs intact; retain explicit Halo 3 shader overrides.
- Ignore unavailable Reach scenario skies when choosing an automatic Halo 3 sky.
- Rename the game selector to Import game and document the mixed-game workflow.

# 0.7.1

- Separate material loading from explicit assignment; identify material-only rows.
- Commit extracted placements inside an undo operator and discard pending results before undo/redo.
- Explicit material assignment isolates shared meshes.

# 0.7.0 - Reach importing and native scene origins

- Add Halo game selector with remembered folders, storage and catalogues.
- Add Reach indexing, resource-resolved BSP instances, material previews and static map extraction.
- Keep Reach previews separate from Halo 3 collision tools and retain source-game identity. Reach export is not implemented.
- Use native Origin to Geometry (Median Center) on all scene meshes, including previously centered meshes.
- Convert only diffuse, normal and transparency textures used in Blender previews, skipping unrelated lookup textures.

# 0.6.7 - Early public release

- Public name: HaloBridge - Blender 4.0 Importing.
- Add installation, first-map, feature, troubleshooting, architecture and limitations guides, release notes and contribution templates.
- Correct obsolete original-map collision/lighting descriptions; keep the draft-lighting option visible for imported scenes. Extraction and geometry-export algorithms are unchanged.

# 0.6.6

- Make pasted HaloBridge assets active instead of leaving the original object active. Deselect the temporary preview when its copy is selected, so moving the copy leaves the original in place.
- Give pasted ordinary assets distinct placement IDs when correcting stale paste selection.

# 0.6.5

- Track the actual temporary preview object separately from copied custom properties. Preview cleanup never deletes pasted or duplicated copies.
- Convert copies of previews to normal visible, exportable assets with independent placement identities, preserving their transforms and selection.
- Handle Blender retaining an unselected original preview as the active object after native paste.
- Check for copied preview flags on object-count/selection changes, without repeatedly scanning an unchanged scene.

# 0.6.4

- Choose the exposed upper surface at the 3D cursor for the initial test spawn, avoiding large underground terrain skirts. Existing Sapien starts remain untouched.
- Verified full saved Shrine geometry loading and player simulation in Sapien.

# 0.6.3

- Prepare now compiles current evaluated Blender meshes instead of cloning an original map base. Mesh edits, deletions, modifiers and transforms reach the static geometry export.
- Generate surface collision, an invisible sky boundary and an initial test player start. Original gameplay and animated object behavior are not reconstructed.
- Continue/Cancel popup explains incomplete-import and static-geometry limitations. Compiler errors remain fatal and roll back generated tags.
- Stage uniquely named shader tags locally; automatically select the imported map sky.
- Read map/category filters once per asset-list pass.
- Center disposable previews at the cursor without modifying cached or placed meshes; preserve the centered preview when placing.
- Fix float precision in legacy reference validation and add incomplete-import repair preserving existing edits/deletions.

## 0.6.2

- Highlight Create starter level shell template in blue.
- Report all detected validation issues with a count, keep all missing/deleted-piece details, log individual issues to Blender Info, and save timestamped diagnostic reports in managed storage. Background jobs preserve structured errors.
- Retain compiler errors from anywhere in the log, including errors followed by long progress output.
- Retry incomplete map caches in new folders without replacing files used by existing Blender scenes. Warn immediately after an incomplete map import and include the BSP names and extraction causes during preparation.
- Confirm a fresh Citadel extraction decodes all 16 BSPs. Jungle intro geometry still fails resource decoding; no universal whole-map or edited-map export claim.

## 0.6.1

- Correct the mistaken rendering warning: Shrine renders textured geometry above terrain; green wireframe was the underground camera view.
- Recover embedded BSP ASS source into a private content-addressed cache, verify size and Halo CRC, and reuse verified cached files. Never follow embedded file paths when writing recovered files.
- Keep edited-map export blocked while shader resolution and rebuilt collision/gameplay validation are unfinished. Recovery alone does not mark a map export-ready.

## 0.6.0

- Rename warning surfaces to HaloBridge Warnings and Messages and preparation to Prepare current scene for sapien.
- Add a map-sky picker populated from available Editing Kit scenarios. Preserve BSP sky slots when changing sky references.
- Route validated, unchanged whole-map imports through original editable terrain/collision/gameplay tags under the existing Prepare button. Added scenery is synchronized with persistent ownership.
- Check source BSP instance transforms; protect existing outputs and roll back failed preparation. Preserve original lighting.
- Report unsupported edited/deleted/duplicated original pieces and mixed custom terrain explicitly. Arbitrary edited-map BSP reconstruction remains unimplemented.

## 0.5.9

- Remove the original-map-copy operator/menu and clarify current-scene preparation.
- Always show Folders and setup; highlight Detect folders.
- Identify the Output level name field and show the rejected value in validation errors.
- Expose the sky source scenario instead of always using Deadlock. New full-map imports populate it.
- Stop before any export when visual map-reference objects are present, including mixed shell/map scenes. Previously these could be silently omitted.
- Whole-map round-trip export and skipped scenery extraction remain unresolved; this is not a playable-map reconstruction release.

# Changelog

## 0.5.8 — original-map Sapien copies

- Added Copy original map to Sapien, separate from Blender geometry preparation. It reads the selected map's scenario identity and copies that level's existing H3EK tag folder into a new output namespace.
- Redirects level-local tag references while retaining gameplay blocks, terrain/collision resources, scripts and lighting. External assets remain shared; compiled-map modifications absent from H3EK tags are not reconstructed.
- Verifies original file hashes remain unchanged and checks serialized tag data around reference relocation and scenario block counts. Pre-existing missing references are retained and reported.
- Uses the kit-wide lock and rollback on failure/cancellation. Existing levels and subsequent Sapien edits cannot be overwritten by repeating the copy; geometry builds cannot overwrite the copy project.
- Camera settings unsupported by this ManagedBlam are preserved byte-for-byte when they contain no source-level path requiring relocation.

## 0.5.7 — faster list redraws and verified scenery recovery

- Cached source-map enum options rather than rebuilding them for every row; cached asset icon lookups instead of scanning every scene object for each visible row.
- Kept the 100x working scale. A 1,500-row filtering benchmark (five passes) fell from 1.31 seconds to 0.012 seconds; this measures list filtering, not viewport rendering.
- Prepare for Sapien now resolves placed raw models through actual scenery → model → render/collision tag links. Only a unique match with an existing collision tag is accepted; missing/ambiguous matches report specific failures.
- Verified automatic warehouse-door linking and compilation in a separate H3EK test scenario with correct game-unit placement. No runtime collision or full-map round-trip claim is made.
- Fixed timer handoff between source resolution and level compilation. Full-map reference conversion remains separate work.

## 0.5.6 — 100x working units and source-map filtering

- New placements, map references and starter shells use 100 Blender units per Halo world unit, including map spacing and origins.
- Normalize geometry and scenery transforms on export so working units do not change in-game size. Mixed older/newer export units are rejected explicitly; existing objects are not silently resized.
- Added Level Imported map filtering alongside existing search/category/tab filters.
- Whole-map completion explicitly identifies the result as a visual reference, not Sapien-exportable content. Full-map gameplay/collision reconstruction remains unsupported.

## 0.5.5 — clearer asset search

- Promoted search to a boxed Search Assets bar immediately above the index list, with a magnifying-glass icon and clear button.
- Search updates while typing and filters by asset name, map or kind within the current tab and enabled categories.

## 0.5.4 — centered map origins and Outliner reveal

- Whole-map imports center each mesh's origin at its local bounding-box center and compensate object transforms to preserve world-space geometry and shared mesh data.
- Added Center existing map origins for older imported reference maps, with Blender Undo support; unrelated mesh users are preserved.
- Added Reveal selected asset in Outliner, enabled by default. Active HaloBridge object changes reveal the collection hierarchy in visible View Layer Outliners without changing selection.
- Retains 0.5.2 message controls; the reverted 0.5.3 scroll buttons are not included.

## 0.5.2 — visible messages and clearer export diagnostics

- Added a Warnings/Messages panel above HaloBridge and a fixed 3D View header control with message preview and full-message popover. Sidebar panels still share Blender's scrollbar.
- Removed bottom-of-panel messages; kept cancellation and report actions with messages.
- Marked raw render models as preview-only in the list and explained missing export collision before preparation.
- Replaced the generic source-mapping error with specific raw-model, legacy-model and missing-BSP-collision guidance; added selection of affected placed objects.
- Cached BSP assets with missing collision files now re-extract instead of reusing an incomplete cache. Raw-model gameplay/collision conversion is still unsupported.

## 0.5.1 — asset-list history and faster map assembly

- Added Asset List title and dedicated session Undo/Redo for hide, unhide, delete and indexing (30 changes), restoring list order and check state without touching scene objects.
- Added a centered empty-state hint in Hidden Assets.
- Batch original-map placement in short timer bursts; assemble off-scene and link the completed collection once, retaining cancellation rollback.
- Avoid repeated preview-icon scene searches while a job is running.
- Validated the cached Jungle map: 5,251 placements with preserved world transforms in 73 timer updates, about 6 seconds in background Blender. This excludes extraction and interactive viewport rendering.

## 0.5.0 — original map layout import

- Replaced full asset-library import with scenario-driven static scene reconstruction.
- Preserves original terrain and object world matrices, sharing meshes across repeated placements.
- Added grouped collections, cached scene extraction, per-stage progress, cancellation rollback, and an import report.
- Missing BSPs, textures and approximate variants are reported explicitly; gameplay and collision restoration are outside this visual-reference route.


## 0.4.0 — unified placement and import controls

- Unified Place asset(s) uses checked entries or the highlighted entry; multiple models share the cursor position.
- Added independent category toggle buttons and an always-highlighted Preview Mode control below the list.
- Renamed the swap action as requested.
- Bulk import loads materials without a mesh, reports individual extraction failures, and yields between placements with progress and cancellation.
- Added Import entire .map for the full indexed asset library at the cursor, not original level reconstruction.
- Starter shell now extracts ground textures, sets floor UVs, and enables Material Preview.


## 0.3.0 — catalogue organization

- Added checkboxes, filtered Select all/Clear checks, and batch placement with rollback on failure.
- Added Imported Assets / Hidden Assets tabs, per-row eye controls, bulk hide/unhide, and catalogue-only deletion.
- Replaced confusing replacement wording with Replace selected object, actionable guidance, and disabled invalid actions.
- Clarified map filename and Sapien preparation labels; moved Create starter level shell template directly below Detect folders.
- Hidden entries retain their original order and survive re-indexing.


## 0.2.0 — public alpha

- Public source and add-on archives exclude local demos, caches, game content, debug symbols, and machine-specific build paths.
- Steam library discovery supports custom library locations; missing requirements are explained by Check setup.
- Storage is automatic, with an optional Advanced storage control that preserves existing settings.
- Live selection previews, preview on/off, and placement preserving position, rotation and scale.
- Descriptive control tooltips and simplified setup.
- Includes source build scripts, synthetic tests, dependency notices, and release packaging checks.

Earlier 0.1.x packages were local development builds and are not intended as public releases.
