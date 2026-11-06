# Use HaloBridge v0.9 for Blender-only importing

[Home](../README.md) · [Installation](INSTALLATION.md) · [First map](FIRST-MAP.md) · [Features](FEATURES.md) · [Troubleshooting](TROUBLESHOOTING.md)

You can use HaloBridge to browse assets, assemble a scene, or inspect an original map without preparing a Sapien level. Preview geometry and textures come from your local MCC maps. Read the [requirements matrix](INSTALLATION.md#requirements): individual Halo 3 BSP-instance placement still calls H3EK for collision data, while the visual whole-map extraction route does not.

## Browse and place individual assets

1. Select the import game and set its maps folder under **Folders and Setup**.
2. Use **Choose .map file** to search filenames or type one. The picker only sets the filename; it does not start extraction.
3. Click **Index Map Assets**. This builds the catalogue, not a scene containing every asset.
4. Use **Search Assets**, category toggles and **Level Imported** to find entries. Indexed entries are not necessarily extracted yet. Keep other categories enabled if filtering would hide the item you need.
5. Enable **Preview Mode** and click an entry. First use extracts its geometry/textures and caches them. ON has a green status icon; OFF has a red icon. Colors follow Blender's theme. These are icons, not custom green/red button backgrounds.
6. Move/rotate/scale a preview if desired, then click **Place asset(s)**. Single-asset placement retains the matching preview transform. Preview turns off after placement. With checked entries, bulk placement takes priority and models are placed at the 3D cursor; clear checks for single-preview placement.
7. Switch the viewport to **Material Preview** to see textures. Save your blend and retain its cached image files.

Materials are separate entries. **Place asset(s)** loads a selected material into Blender without applying it to the previously selected object. To assign it intentionally, select a mesh and use **Apply material to selected object**. Selecting an asset-list row alone does not change a scene object's material.

## Import an entire map

Choose **Import entire .map** for the selected filename. It ignores the cursor and list filters, and imports available terrain and static placements at source positions into grouped collections. Indexing first is unnecessary. Read **Open map import report** afterward: missing BSPs, approximate variants and unsupported elements are listed.

This is a static visual reference, not the original playable mission. AI, scripts, gameplay rules, animated states, original collision and baked lighting are not reconstructed. Some render models may be present even though their original interactive behavior is absent. Large campaign maps include areas normally streamed separately and can be expensive to load.

## Greybox with cubes, then swap

Select one or more editable scene objects in Object Mode, highlight one geometry asset in the list, and choose **Swap selected object(s) to selected index asset**. It uses the replacement asset's original import scale and each selected object's world position/rotation. Collections are retained. Meshes and modifiers are replaced, not transferred. Materials cannot replace geometry. Replacement meshes share data; editing shared mesh vertices affects linked copies.

## Organize without deleting your scene

**Hide** and the eye icons move catalogue entries to Hidden Assets. **Unhide** restores them. **Delete checked from list** removes catalogue entries, not placed objects or cached/game files. List Undo/Redo restores supported catalogue actions during the current session; it is separate from Blender scene undo.

Use **Shift+D** for normal duplicates or **Alt+D** for linked mesh duplicates. Object transforms are independent. If moving one object moves nearby objects, check selection, parenting, constraints and Proportional Editing before assuming it is a shared-mesh issue.

## Do I need the preparation controls?

No. Materials/shader-tag, sky and Sapien preparation settings are for game export. Leave them alone if you only need Blender assets. A Halo shader tag path is not the path to the preview image. No standalone Reclaimer application or manually exported asset library is needed.

For game testing later, install/configure H3EK and follow [First Map](FIRST-MAP.md). Reach importing remains experimental; see [Reach](REACH.md) for conversion limits.

After placement, select a supported model to choose visible regions or separate all variants. See [Model parts and variants](FEATURES.md#model-parts-and-variants).
