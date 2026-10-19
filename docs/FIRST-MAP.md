# Your first custom test map

[Home](../README.md) · [Installation](INSTALLATION.md) · [Feature reference](FEATURES.md)

Start with a floor and a few trees or rocks. A small scene makes it easier to identify setup or material problems before building a large map.

## 1. Find assets

After **Check setup** passes, enter `010_jungle.map` in **.map file name to Index** and choose **Import Map Assets**. Indexing creates a searchable list; it does not extract every asset immediately.

Use **Search Assets**, category buttons, and **Level Imported** to narrow the list. Unknown categories are still shown. **All Levels** shows entries from every indexed map.

## 2. Preview and place

Put the 3D cursor where you want to work. Enable **Preview Mode**, then click an asset. Its temporary preview is centered at the cursor. Selecting another asset replaces the preview; switching preview off removes it.

Move or rotate the preview, then choose **Place asset(s)** to keep that transform as a normal placed object. Checked list entries take priority over the highlighted entry; clear checks when you only want one asset. Multiple checked models start together at the cursor.

Duplicate in Object Mode with **Shift+D**, or use copy/paste. **Alt+D** shares mesh data: Object Mode transforms are independent, but Edit Mode mesh edits affect linked copies. If nearby unselected copies move together, turn **Proportional Editing** off with **O** while the pointer is over the viewport. See [troubleshooting](TROUBLESHOOTING.md).

## 3. Make your geometry

Choose **Create starter level shell template**, or build your own floor and walls. The starter shell needs `010_jungle.map` for its ground preview. Save the blend file.

New HaloBridge imports use 100 Blender units per Halo world unit. Export converts back automatically: do not multiply the scene by 100 again. Use consistently scaled assets from the current importer.

To texture authored geometry, load an indexed material with **Place asset(s)**, select your mesh, then use **Apply material to selected object**. Loading a material alone does not assign it. Assign the desired material to faces in Blender as needed. Alternatively, enter an existing Halo shader tag path and choose **Assign existing Halo shader** for the active material. A Blender image alone does not supply a game shader.

## 4. Choose the sky and output

Choose **Find map skies**, then select **Sky from map**. Automatic selection uses a single imported map's primary sky, otherwise High Ground. This reads your Editing Kit tags, so the source scenario must be installed.

Enter an **Output Level Name (without .map)** such as `my_first_map`: 3–32 lowercase letters, digits or underscores, starting with a letter, without `.map`. Use a new name for this first test, especially if an older version created an original-map copy.

Move the 3D cursor above the intended starting area. A new scenario receives a test player start above an exposed surface near its XY position. Existing Sapien starts are retained on later exports.

## 5. Prepare and test

Close Sapien. Choose whether to **Generate Test Lighting for Sapien Level**; leaving it off is faster for an initial geometry check. Choose **Prepare current scene for sapien** and read the warning popup. Continue exports the available current meshes, including edits, modifiers and deletions; cancel stops preparation.

Compiler errors still stop the job. Read **HaloBridge Warnings and Messages → Open diagnostic report** for all issues found so far. Fix them and retry. A failed normal build restores the previous generated output.

When preparation succeeds, use **Open in Sapien** or the automatic open option. Inspect the geometry and test player placement. Sapien's saved editor camera can be underground even when the player start is above ground. Add gameplay content in Sapien as needed; exporting geometry does not automatically create a complete game mode.

## Starting from an entire map

Use **Import entire .map** to bring in available terrain and static placements at original positions. It does not use the cursor or list filters. Read its import report before editing: missing pieces stay missing unless extraction recovers them.

You can edit or delete those meshes and prepare the result using the same steps above. The original map is not substituted for your edited scene. **Repair incomplete map import** retries missing pieces while preserving existing edits and intentional deletions. Whole campaign maps can be slow and include areas normally streamed separately.
