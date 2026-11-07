# Your first custom test map — HaloBridge v0.9.1

[Home](../README.md) · [Installation](INSTALLATION.md) · [Feature reference](FEATURES.md)

Only importing into Blender? Use the [Blender-only guide](IMPORTING.md) instead; this tutorial requires H3EK with extracted tags.

Start with a floor and a few trees or rocks. A small scene makes it easier to identify setup or material problems before building a large map.

## 1. Find assets

After completing the [H3EK preparation setup](INSTALLATION.md#4-add-halo-3-sapien-preparation), select or type `010_jungle.map` in **Choose .map file** and choose **Index Map Assets**. Indexing creates a searchable list; it does not extract every asset immediately.

Use **Search Assets**, category buttons, and **Level Imported** to narrow the list. Unknown categories are still shown. **All Levels** shows entries from every indexed map.

## 2. Preview and place

Put the 3D cursor where you want to work. Enable **Preview Mode**, then click an asset. Its temporary preview is centered at the cursor. Selecting another asset replaces the preview; switching preview off removes it.

Move or rotate the preview, then choose **Place asset(s)** to keep that transform as a normal placed object. Checked list entries take priority over the highlighted entry; clear checks when you only want one asset. Multiple checked models start together at the cursor.

Duplicate in Object Mode with **Shift+D**, or use copy/paste. **Alt+D** shares mesh data: Object Mode transforms are independent, but Edit Mode mesh edits affect linked copies. If nearby unselected copies move together, turn **Proportional Editing** off with **O** while the pointer is over the viewport. See [troubleshooting](TROUBLESHOOTING.md).

## 3. Make your geometry

Choose **Create starter level shell template**, or build your own floor and walls. The starter shell needs `010_jungle.map` for its ground preview. Save the blend file.

New HaloBridge imports use 100 Blender units per Halo world unit. Export converts back automatically: do not multiply the scene by 100 again. Use consistently scaled assets from the current importer.

To texture authored geometry, load an indexed material with **Place asset(s)**, select your mesh, then use **Apply material to selected object**. Loading a material alone does not assign it. Assign the desired material to faces in Blender as needed. Alternatively, enter an existing Halo shader tag path and choose **Assign existing Halo shader** for the active material. A Blender image alone does not supply a game shader.

You can also greybox with cubes, select several, then use **Swap selected object(s) to selected index asset**. Replacement assets keep position/rotation but use their original scale. Avoid dense terrain subdivisions; visual map size alone does not determine compiler cost.

## 4. Choose the sky and output

Choose **Scan for map skies**, then select **Sky**. Automatic selection uses a single imported map's primary sky, otherwise High Ground. This reads your Editing Kit tags, so the source scenario must be installed.

Enter an **Output Level Name (without .map)** such as `my_first_map`: 3–32 lowercase letters, digits or underscores, starting with a letter, without `.map`. Use a new name for this first test, especially if an older version created an original-map copy.

Move the 3D cursor above the intended starting area. A new scenario receives a test player start above an exposed surface near its XY position. Existing Sapien starts are retained on later exports.

## 5. Prepare and test

Close Sapien. Choose whether to **Generate Test Lighting for Sapien Level**; leaving it off is faster for an initial geometry check. Choose **Prepare current scene for sapien** and read the warning popup. Continue exports the available current meshes, including edits, modifiers and deletions; cancel stops preparation.

The lower **HaloBridge Warnings and Messages** panel sits above **Map Preparation Status**; the top panel remains available too. **ACTION REQUIRED** means you need to inspect the error or confirmation. Open the activity log for detailed progress. Stage percentages are not a total-time estimate.

Compiler errors still stop the job. Read **HaloBridge Warnings and Messages → Open diagnostic report** for all issues found so far. Fix them and retry. A failed normal build restores the previous generated output.

When preparation succeeds, use **Open in Sapien** or the automatic open option. Inspect the geometry and test player placement. Sapien's saved editor camera can be underground even when the player start is above ground. Add gameplay content in Sapien as needed; exporting geometry does not automatically create a complete game mode.

## Starting from an entire map

Use **Import entire .map** to bring in available terrain and static placements at original positions. It does not use the cursor or list filters. Read its import report before editing: missing pieces stay missing unless extraction recovers them.

You can edit or delete those meshes and attempt preparation using the same steps above; full-map imports may require substantial cleanup before Halo Tool accepts them. The original map is not substituted for your edited scene. **Repair incomplete map import** retries missing pieces while preserving existing edits and intentional deletions. Whole campaign maps can be slow and include areas normally streamed separately.


## Original Halo 3 vehicles

To keep an imported Scorpion or another supported Halo 3 vehicle functional instead of exporting it as static terrain:

1. Select its imported model in the **3D View**.
2. Under **Selected Asset > Original Halo 3 Vehicle**, click **Find matching original vehicles**.
3. Click **Use original Halo 3 vehicle** and choose the intended installed tag. Only tags linked to that render model are offered.
4. Prepare the scene normally. Keep a terrain/floor mesh in the scene; a vehicle alone does not form a level.

The original vehicle tag supplies its model, collision, physics and behavior. The Blender object remains an editable placement preview and is omitted from the static geometry export. Position, rotation and positive uniform scale are transferred. Copies receive independent placement identifiers; repeat exports update moved vehicles and remove deleted ones while preserving independent scenario placements.

Mesh reshaping and modifiers cannot be transferred to an existing vehicle tag. Original-pivot changes are recovered when the cached preview still proves the unchanged shape. Blender material edits are not applied to the vehicle tag. Use **Use static mesh instead** to return to mesh export, where the original vertex limit applies. This route requires Halo 3 tags and is not Reach vehicle conversion or automatic campaign reconstruction.

Save and restart Blender after updating before using this feature. Vehicle tag creation was verified with the Scorpion; driving, multiplayer rules, respawn tuning and Project Reclaimer behavior need in-game testing.

Background: [c20 Halo 3 scenario reference](https://c20.reclaimers.net/h3/tags/scenario/) and [Microsoft Halo 3 instance geometry](https://learn.microsoft.com/en-us/halo-master-chief-collection/h3/art/instanceobjects/instanceobjectshome). Original vehicle tags and static instance geometry are different export routes.

For a painted floor, follow [Paint terrain](EDITABLE-MATERIALS.md#paint-terrain) before preparing. Pack the images and save your blend.

## Review materials and collision before testing

Select each important object and check its active material in Materials and Shaders. Assign shader to active material sets its Sapien shader reference. Load the source shader textures when you want the Blender preview refreshed. Use the [editable-material guide](EDITABLE-MATERIALS.md) to export painted terrain or colors.

Leave Object collision on Automatic to try matched original collision. Read the per-object collision routes in the preparation report after exporting. Inspect floors, foliage and barriers in Sapien, especially objects using a fallback. An oversized model may be internally divided into aligned instances. A successful Sapien compile still needs a playtest, followed by separate runtime and multiplayer testing for distribution.

