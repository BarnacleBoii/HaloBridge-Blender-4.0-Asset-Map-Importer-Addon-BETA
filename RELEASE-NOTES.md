# HaloBridge v0.9 — Beta

Windows x64 • Blender 4.0 • Halo 3 and experimental Halo: Reach importing

## v0.9 interface refresh

- **Choose .map file:** searchable dropdown lists maps from the selected game folder, alongside an editable filename field.
- **Warnings where you need them:** a second HaloBridge Warnings and Messages section sits above Map Preparation Status. The original top panel remains; both show the same errors and action buttons.
- **Preview status:** green ON / red OFF icons, with Place Asset(s) highlighted while previewing. No flashing or global theme changes.
- **One Editing Kit setup:** preparation reuses the Halo 3 path saved under Folders and Setup. The duplicate export-kit path field has been removed.

The v0.9 download assets have been refreshed. Reinstall the updated ZIP and restart Blender to receive these changes.

## What changed since v0.8.9

- **Shared Halo 3/Reach interface.** Reach now has the same material, collision, sky, preparation and activity-log panels. Import game selects the source catalogue; Export to Sapien selects the destination. Prepare Reach or mixed-game scenes for Halo 3 without switching import games. Output level and sky stay selected when switching games.
- **Multi-object swapping for greyboxing.** Select ordinary Blender cubes or existing placed objects and use **Swap selected object(s) to selected index asset**. The replacement keeps world position, rotation and collections, uses the asset's original import scale, and shares mesh data. All replacements are created before originals are removed. An import failure retains the originals.
- **Single-sided terrain and open surfaces.** Removed forced two-sided rendering for every material. Explicit Halo two-sided settings and double-sided alpha previews are retained. Open single-sided meshes use Halo's non-manifold surface flag where appropriate, without adding reverse faces or changing shader opacity. Closed meshes keep their volume behavior.
- **Clearer diagnostics.** Reports open at line 1. Cluster/plane-builder failures identify the main Blender structure object, while explaining that compiler clusters are not Blender object names or exact face selections.
- **Sidebar cleanup.** Asset List is left-aligned above the category buttons, without its divider. Removed the output-name example text.
- **Future game framework.** Central game capability definitions separate source importing from export destinations. Halo CE, Halo 2, ODST and Halo 4 are reserved but not enabled.

## Installation / update

Download **HaloBridge-0.9.0.zip** and install it through Blender 4.0 Preferences → Add-ons → Install. The **-source.zip** is for developers and does not contain the compiled helpers. Save your work and restart Blender after updating. Keep your cache and project records. See the installation and feature guides included in the download.

## Requirements and important limits

- Windows x64, Blender 4.0, the supported Halo Blender toolset and helper runtimes; see [Installation](docs/INSTALLATION.md).
- Supply your own MCC map files. No game maps, models, textures or Microsoft editing-kit libraries are distributed.
- Halo 3 Sapien preparation requires H3EK with extracted tags. Halo 3 is still the only implemented Sapien destination. Reach import does not imply native Reach Sapien export.
- Reach assets use experimental static mesh/material conversion. Reach gameplay, vehicles, animation and original collision tags are not converted into equivalent Halo 3 game objects. The original-vehicle route remains specific to verified Halo 3 tags.
- The starter shell still uses Halo 3 Jungle assets and requires that map. Sky and existing-shader choices use the export destination kit.
- Terrain complexity, collision topology and Halo compiler limits still apply. This release does not automatically simplify or split user geometry, reconstruct full campaign gameplay, or guarantee that every imported map compiles.
- Sapien ownership conflict checks remain conservative; use Resolve Conflict only when you intend Blender to replace its owned placements.

## Validation

Background Blender checks cover shared game menus and export routing, Reach material conversion, warning confirmation, multi-object swapping, import-failure rollback, report positioning, and sidedness/open-surface policy. Isolated Halo compiler tests passed for a Citadel pine and single-sided floor. A separate user-scene test compiled in approximately 95 seconds after a reversible terrain reduction from 32,768 to 8,191 triangles; that reduction is **not** automatically applied by the add-on. The scene retained five nonfatal overlap/duplicate warnings. Lighting and in-game play were not validated in that terrain test.
