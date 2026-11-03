# Feature guide

## Halo 3 and Halo: Reach

Use **Import game**, above **Folders and Setup**, to select **Halo 3** or **Halo: Reach**. Each game remembers its folders, map filename, storage and catalogue. Save the blend file to retain these settings. Switching does not delete scene objects. Reach assets can share a scene with Halo 3 assets. Switch **Import game** back to **Halo 3**, verify H3EK, then use **Prepare current scene for sapien**. Reach meshes are converted to static Halo 3 geometry with generated collision and converted preview textures. Existing Reach objects do not need reimporting. See [Reach conversion](REACH.md).

**Origin to Geometry - all scene meshes** uses Blender's native median geometry center on every mesh, including authored, hidden and previously centered objects, preserving visible geometry and selection. Use Object Mode; Blender Undo is available. Linked library meshes must be made local first.

Browse MCC Halo 3 assets in Blender, position them in your map, and prepare a scenario for Sapien.

**0.8.5 beta preview — Windows x64 and Blender 4.0.** This is an independent community project, not an official Microsoft, Bungie, or 343 Industries tool. Other Blender versions, console maps, games beyond Halo 3 and experimental Halo: Reach, and giant-map performance are not supported by this release.

## What it does

- Index assets directly from your installed MCC Halo 3 maps.
- Preview geometry and materials as you click through the asset list.
- Keep a preview's position, rotation, and scale when placing it.
- Reuse cached meshes and textures for repeated placements.
- Export current meshes as static level geometry with generated collision.
- Compile and build optional draft lighting, then launch Sapien.
- Back up generated level files during compilation; a failed build restores the previous output.

## Requirements

1. **Blender 4.0, Windows x64.** The adapter is tested with 4.0.0.
2. **Halo: The Master Chief Collection with Halo 3 installed.** Retain its complete `halo3/maps` directory, including resource maps.
3. **Halo 3 Editing Kit**, including extracted tag archives. Confirm Tool and Sapien work independently. The High Ground (`deadlock`) scenario is used for starter sky settings; jungle assets also require their corresponding source tags and shaders. See [Microsoft's Editing Kit overview](https://learn.microsoft.com/en-us/halo-master-chief-collection/h3/quickstart/quickstartoverview).
4. **[Halo Asset Blender Development Toolset](https://github.com/General-101/Halo-Asset-Blender-Development-Toolset), version 2.364.0 (v364)**, installed and enabled in Blender. The adapter intentionally rejects unverified exporter versions.
5. **[.NET 10 Desktop Runtime for Windows x64](https://dotnet.microsoft.com/en-us/download/dotnet/10.0)** and **[.NET Framework 4.8 or newer](https://dotnet.microsoft.com/en-us/download/dotnet-framework/net48)**. The SDK is only needed to build from source.

Game files, game tags, textures, ManagedBlam, and the Halo exporter are not included. You supply these from your own installations. No standalone Reclaimer installation or manually extracted asset library is required.

## Install

1. Download **HaloBridge-0.8.5.zip** from the project's release assets. GitHub's automatic “Source code” ZIP is for developers and does not contain built helpers.
2. Save your Blender work. If replacing an older HaloBridge version, disable and remove it in Preferences, then restart Blender.
3. Choose **Edit → Preferences → Add-ons → Install**, select the add-on ZIP without unzipping, and enable **HaloBridge - Blender 4.0 Importing**.
4. Open the 3D View sidebar with **N**, then select **HaloBridge**.
5. Choose **Detect folders**. Check the Editing Kit and Halo 3 maps locations, then choose **Check setup**. Missing requirements appear in the diagnostic report. Detection reads Steam library locations and optionally Osoyoos settings; manual folder selection is supported.

## Make a small test map

### Export the current Blender scene (experimental)

Preparation exports the current evaluated meshes, including edits, modifiers, movement, duplication and deletion. It does not substitute the original Editing Kit map. Imported assets become static, two-sided geometry; Tool builds collision from their current surfaces. Doors, breakable objects, animations and gameplay scripts are not reconstructed.

1. Place assets or import a map, then edit your geometry in Blender.
2. Choose **Find map skies**, then **Sky from map**. Automatic selection uses the single imported map's primary sky; otherwise the default is High Ground. Imported sky meshes are excluded from solid geometry. Weather and fog are not converted.
3. Enter a new **Output Level Name (without .map)**, without `.map`. Outputs previously made with original-map copying require a new name to preserve those levels.
4. Close Sapien and choose **Prepare current scene for sapien**. Review **Continue with warnings** / **Cancel**. Incomplete imports export only meshes actually present; deleted pieces stay deleted.
5. The compiler creates static geometry, generated collision, a sky boundary and a test player start above an exposed surface near the cursor. Existing starts in repeated authored exports are retained. Optional draft lighting runs afterward.

This is a geometry-testing route. Extracted render meshes can contain open surfaces, invalid topology or exceed Halo limits; compiler failures still stop preparation and restore the previous output. Warnings cannot make invalid geometry compile. The sky boundary is invisible and adds no ground. Shader tags are copied into the generated level under unique names, retaining their bitmap references. Source game tags are not modified.

### Author a new Blender level

1. Index `010_jungle.map` or `deadlock.map`. Indexing lists assets without extracting everything.
2. Select an **instance** or **scenery** asset. Turn **Preview Mode** on to browse live previews; first-use extraction may take a moment.
3. Move, rotate, and uniformly scale the preview, then click **Place asset(s)**. Preview turns off and the placed object retains that transform. Use **Alt+D** for linked duplicates.
4. For materials, select your level mesh before previewing a material, then click **Apply material to selected object** to apply it.
5. Choose **Create starter level shell template** under Detect folders, or create closed level geometry with existing Halo shader references. New imports use 100 Blender units per Halo world unit; the scene display scale is 0.03048 metres per Blender unit. Export converts back to game units.
6. Give the output level a unique lowercase name. Save your blend file and close Sapien, then choose **Prepare current scene for sapien**.
7. Open the resulting scenario in Sapien to add gameplay content. Draft lighting is optional for faster geometry iterations.

Hover over controls for explanations. Raw models can be exported as static geometry; they do not require a scenery-tag mapping on this route.

**HaloBridge Warnings and Messages** shows progress and reports. The viewport header control stays accessible while the sidebar scrolls. Preparation lists all detected issues; dependent compiler stages can discover additional errors later. Continue with warnings accepts documented import omissions and static-geometry limitations, but does not override a failed compiler.

## Organize and place multiple assets

The list has **Imported Assets** and **Hidden Assets** tabs. Imported Assets contains entries indexed from map files; extraction still happens on first use.

The **Asset List** header has dedicated **Undo / Redo** buttons for the last 30 hide, unhide, delete and index changes in this Blender session. These restore catalogue entries and their order without changing placed objects or deleting cached files. A new list edit clears redo history. History is not saved across Blender restarts and cannot overwrite a catalogue changed externally. Search, category filters and individual checkbox clicks are browsing controls, not history entries. An empty Hidden Assets tab displays a centered hint until an asset is hidden.

- Tick an entry's checkbox to include it in bulk actions. **Select all** and **Clear checks** affect only entries visible under the current tab, search, and category filter.
- **Place asset(s)** uses checked entries in the current filtered tab when present, otherwise the highlighted entry. Multiple models are placed together at the 3D cursor. Single-asset placement retains its matching preview transform. Materials are loaded into Blender without changing any existing object. Material rows have a material icon and label. Use **Apply material to selected object** for an intentional assignment. Placement commits as one undo step after extraction; large batches may pause briefly during that commit.
- The eye icon beside an entry, or **Hide** for checked entries, moves it to Hidden Assets. **Unhide** returns it to its original position. These actions organize the catalogue; they do not hide placed scene objects. Hidden state survives reopening and re-indexing.
- **Delete checked from list** removes catalogue entries only. Placed objects, cache files, and game files are kept. Re-index the corresponding map to restore deleted entries. The previous catalogue is backed up before each list edit.
- **Swap selected object to the selected index asset** replaces the HaloBridge object selected in the 3D View with the highlighted list entry, preserving its transform and placement identity. Choose an instance or scenery entry; materials and raw models cannot replace objects. The panel explains unmet requirements beside the disabled button.

## Category filters and original map layout import

Category buttons independently include or exclude Vegetation, Rocks, Structures, Water, and Materials. Turn Materials off to see everything else. Preview Mode sits immediately below the index list, remains highlighted in both states, and explicitly reads On or Off. Highlight color follows Blender's theme.

**Level Imported** filters the list by the source map, or shows **All Levels**. It works together with search, category toggles and the Imported/Hidden tabs; it does not limit whole-map imports.

New object imports and starter shells use a **100x working scale**. Whole-map spacing and object origins are scaled together; existing saved objects are not automatically resized. Old and new working conventions must not be mixed in an export scene: replace older imports or use a separate scene. Raw-model swapping from an older object converts its transform to the new convention. For an already imported whole map, reimport into a separate scene to adopt the new scale. The x100 working scale does not enlarge the resulting objects in-game.

**Import entire .map** reads the scenario's terrain BSPs and static placements and reconstructs their original world positions, orientations, and scales. It ignores the 3D cursor and list filters. Each import creates a separate collection, with child collections for Terrain, BSP instances, Scenery, Machines, Controls, Crates, and Skies. Repeated geometry shares mesh data. No need to index or select all assets first.

Map assembly runs in short batches and adds the completed collection to the scene at the end, avoiding a viewport rebuild for every object. Cancel remains available between batches (an individual large mesh can take longer). First extraction and texture conversion can still take minutes; repeat imports reuse the extraction cache.

**Origin to Geometry - all scene meshes** uses Blender's native median geometry center on every mesh, including authored, hidden and previously centered objects, preserving visible geometry and selection. Use Object Mode; Blender Undo is available. Linked library meshes must be made local first.



**Reveal selected asset in Outliner** is enabled by default above Asset List. Selecting a placed HaloBridge object or an imported map object expands its collection hierarchy and scrolls to it in open Outliners using View Layer mode. It follows the active object when several are selected, skips temporary previews, and only reacts to selection changes so it does not repeatedly reset manual scrolling. Disable the toggle to browse the Outliner manually. Filters that hide an object can still prevent it from appearing.

This is a **static visual layout import**, not restoration of a complete playable scenario. AI, player starts, weapons, vehicles, scripts, triggers, animated device states, original collision and baked lighting are not imported. Some model variants are approximated and missing resources are reported. Campaign BSPs are loaded together, including areas normally streamed separately. The completion message gives the decoded terrain count; **Open map import report** lists omissions and approximations.

Prepare includes the current meshes in original-layout collections, including your edits and deletions, and generates static surface collision. It does not load the original map in place of your changes. Existing scenes and previously imported collections are not replaced automatically.

Extraction and placement show progress and support cancellation. Cancelled placement removes only the collection being created. A completed extraction is cached for repeat imports. Ordinary checked-asset placement remains available through Place asset(s), with multiple assets at the cursor; it is separate from original-layout import.

The starter shell now loads the jungle ground texture, creates repeating floor UVs, and enables Material Preview. It requires `010_jungle.map`. This is an approximation of the Halo shader, not a reproduction of every layered rendering effect. Existing shells are not automatically changed.

## Storage and existing projects

Storage defaults to `Documents/HaloBridge` under the current user's home directory. Existing blend files retain their saved folder. **Folders and Setup → Advanced storage** allows another location. It does not move or merge files: select the existing project folder when reopening a level. Save your blend file after changing settings.

Keep the cache's `projects` ownership manifests and `backups`; they are project data, not disposable thumbnails. Deleting them prevents safe repeat exports. Use distinct output level names for distinct maps. Moving a completed project to another computer is not yet automatic: catalogues, manifests, source map references, and placed-object metadata contain local paths. Do not regenerate ownership records to bypass this protection.

## Current limits

- Static Halo 3 environment assets first. Mesh editing is supported on the geometry-test route. Experimental Reach-to-Halo-3 static conversion is available; animation authoring and universal MCC conversion are not supported.
- Collision is rebuilt from source polygons; specialized per-surface physics, breakable surfaces, and collision-material distinctions are not fully preserved.
- Blender materials approximate Halo rendering. Not every shader effect, water effect, or model variant is reproduced.
- Changing Blender-owned objects in Sapien can create conflicts. Resolve these explicitly; independently added Sapien content remains separate.
- Normal compiler errors and cancellation restore previous project output. Forced termination cannot guarantee rollback.
- Large-map limits, final lighting, navigation, multiplayer, and Project Reclaimer packaging require separate testing. A successful small-map compile does not guarantee runtime performance.

See [TESTING.md](../TESTING.md) for what was verified. This beta has not been validated on a second, clean Windows computer.

## Source and contributions

See [CONTRIBUTING.md](../CONTRIBUTING.md) for build and test instructions and [THIRD-PARTY.md](../THIRD-PARTY.md) for dependency notices. HaloBridge is distributed under GPL-3.0; see [LICENSE](../LICENSE). Publish the matching source archive alongside every binary release.

Before attaching diagnostics to an issue, remove personal filesystem paths. Do not upload game maps, extracted textures/models, tags, caches, or blend files containing game assets.

## Material and texture names

Materials and image datablocks use original Halo source names. Full shader/bitmap paths and cache identifiers remain in custom properties; display names do not determine Sapien shader references. Existing generated names upgrade when a saved scene loads. Missing bitmap names are looked up in the original map without extracting geometry again. If source metadata is unavailable, the old texture name stays unchanged. Custom names are retained, and Blender adds numeric suffixes when separate sources share a name.

## Preparation progress

The status directly above **Prepare current scene for sapien** reports the current mesh count and asset name during geometry preparation. Later stages show the compiler or lighting phase, elapsed time and recent tool output. A quiet tool stage is reported as waiting; it does not invent a percentage. The preparation button displays **(LOADING...PLEASE WAIT)** while the job runs. Open the diagnostic report for complete detected errors; later dependent stages may reveal additional issues.

## Export review and shader selection (0.8.5)

An assigned HaloBridge material already carries its game shader reference. Highlighting an Asset List material only selects it for browsing; use Apply material to selected object to assign it. Export checks materials used by evaluated faces, not unused slots.

Enable **Skip objects with export problems** to omit whole objects with detected material/mesh validation problems. Prepare lists every omitted object and reason before **Continue with warnings**. Objects remain in Blender, and exclusions appear in the preparation report. At least one valid object is required. This does not bypass compiler failures or guarantee that all topology will compile.

**Scan existing shaders** populates the **Existing Halo shader** dropdown from installed .shader tags. Assignment links the active Blender material to an existing game shader; it does not create a shader or replace preview textures. Manual path entry remains optional. **Static model** means geometry-only importing; it is not an error.

**Export to Sapien** currently supports Halo 3. Halo: Reach is marked not available yet and cannot start a build. Reach assets may still be converted into a Halo 3 level.
