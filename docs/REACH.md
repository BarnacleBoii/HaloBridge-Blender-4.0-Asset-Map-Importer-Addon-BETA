# Halo: Reach

[Home](../README.md) · [Supported games](GAMES.md) · [Importing](IMPORTING.md)

Reach content imports into Blender like any other game, and Reach assets can be built into a Halo 3 (or ODST) Sapien level as static geometry with converted materials. A native Reach Sapien level can't be prepared yet.

## Setup

1. Make sure **Halo: Reach** is installed in MCC (its maps are in `haloreach\maps`).
2. Optional: install **Halo: Reach Mod Tools - MCC** (HREK) and extract its tags. You need it for Reach `.scenario` import, and for reusing Reach models' original collision in a Halo 3 level.
3. For Sapien, install H3EK as described in [Installation](INSTALLATION.md).
4. In the sidebar, set **Import game** to **Halo: Reach**, open **Folders and Setup** and click **Detect folders**. Check **Halo: Reach Editing Kit** (ends in `HREK`) and **Halo: Reach .map Files** (ends in `haloreach\maps`).

## Importing

- **Import entire .map:** choose a map such as `70_boneyard.map` and click **Import entire .map**.
- **Import level from .scenario:** choose a scenario such as `levels\multi\70_boneyard\70_boneyard`. HREK has the scenario and placements but no source models or BSP sources, so placements come from HREK and geometry from the `.map`. Set both folders.
- **Asset list:** **Index .map Assets** or **Index .scenario Assets**, then search, preview and place as described in [Importing](IMPORTING.md#3-browse-and-place-individual-assets).

Reach indexing works out BSP instances from the map's resource data, so it can take longer than Halo 3. Warnings go to the **HaloBridge index report** in Blender's Text Editor. Reach's developer-only BSPs don't decode and are reported.

## Using Reach assets in a Halo 3 level

1. Import or place Reach assets as usual. You can keep **Import game** on Reach.
2. Set **Export to Sapien** to **Halo 3**. HaloBridge uses the H3EK folder you saved with Halo 3 selected; there's no second path to enter.
3. Choose a Halo 3 sky (or convert a Reach sky; see [Use a sky from another game](IMPORTING.md#use-a-sky-from-another-game)), set the level name, and click **Prepare current scene for sapien**.

What happens to Reach objects:

- Their current meshes and positions are exported as static geometry, including your edits and modifiers.
- Materials become new Halo 3 bitmaps and shaders in your level folder: base color, normal map, UV tiling, and cut-out transparency. If you assign a Halo 3 shader yourself, that's used instead.
- Collision uses the original model collision from HREK when it's installed and the mesh is unchanged; otherwise a box or the mesh's surfaces.
- Vehicles, weapons, machines and characters become static shapes, not working game objects.

Things that are approximated: layered terrain shaders, water, glow and blended transparency (it becomes cut-out). Textures with different tiling are resampled to the base texture's tiling, which can lose some detail. Converted bitmaps are uncompressed, so large scenes need more disk space.

## Recoloring Reach characters and shields

Select the material slot and use [editable colors](EDITABLE-MATERIALS.md#recolor-models-and-vehicles). Glow and other effects stay approximate.

## Why there's no Reach Sapien preparation

HaloBridge exports geometry with the Halo toolset's ASS exporter, which only writes Halo 2 / Halo 3 format. Reach's tools expect a different pipeline. Reach in the **Export to Sapien** list is marked "not available yet".
