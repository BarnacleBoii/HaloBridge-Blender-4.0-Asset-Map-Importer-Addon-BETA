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
