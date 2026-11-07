# Feature guide

Choose a feature to jump to its instructions. New users can start with [Installation](INSTALLATION.md) or [First map](FIRST-MAP.md).

| Feature | What it does |
| --- | --- |
| [Game and folder setup](#game-and-folder-setup) | Connect your installed game maps and editing tools. |
| [Index map assets](#index-map-assets) | Browse a map before extracting anything into the scene. |
| [Search and filter](#search-and-filter) | Narrow the index by category, source level and asset name. |
| [Checks and hidden assets](#checks-and-hidden-assets) | Organize batches and hide entries you want to keep for later. |
| [Preview and place](#preview-and-place) | See the highlighted model at the cursor and keep its transform when placing it. |
| [Greybox swaps](#greybox-swaps) | Replace selected meshes or blockout cubes with the highlighted asset. |
| [Whole map import and repair](#whole-map-import-and-repair) | Load the available visual layout at its original placements. |
| [Origins and Outliner](#origins-and-outliner) | Center mesh pivots or follow an active object in the Outliner. |
| [Model parts and variants](#model-parts-and-variants) | Choose the visible head, armor, hull or damage pieces of a supported model. |
| [Apply materials and shaders](#apply-materials-and-shaders) | Assign a browsed material or link a mesh material to an installed Halo shader. |
| [Paint terrain and edit colors](#paint-terrain-and-edit-colors) | Paint numbered terrain layers or recolor models and matched vehicles using a mask. |
| [Collision and original vehicles](#collision-and-original-vehicles) | Choose which static surfaces collide or place a supported original Halo 3 vehicle. |
| [Starter shell and sky](#starter-shell-and-sky) | Give a test level a floor and choose its Sapien sky. |
| [Prepare and open in Sapien](#prepare-and-open-in-sapien) | Compile the current Blender scene as a Halo 3 test level. |
| [Progress, warnings and conflict resolution](#progress-warnings-and-conflict-resolution) | See current preparation activity and decide how to handle reported problems. |
| [Large models during preparation](#large-models-during-preparation) | Export oversized instances as aligned pieces while keeping one Blender object. |
| [Storage and repeat builds](#storage-and-repeat-builds) | Reuse cached extractions and preserve the ownership records used for repeat exports. |

## Game and folder setup

Press **N** in the 3D View and open **HaloBridge**. Choose Halo 3 or experimental Reach under **Import game**, then click **Detect folders**. Verify the maps folder contains the level and shared resource files. For Sapien, configure the Halo 3 Editing Kit root under the Halo 3 setup. **Check setup** checks the full workflow. [Compare requirements by task](INSTALLATION.md#requirements).

## Index map assets

Pick a level or type its filename in **Choose .map file**, then click **Index Map Assets**. Index another map to extend the catalogue. Indexing creates entries you can select later. Geometry and textures are extracted on first use and cached.

## Search and filter

In **Indexed Asset List**, toggle categories, choose a map in **Level Imported**, then type in **Search Assets**. Choose **All Levels** and clear the search to see more entries. Two maps can legitimately contain assets with the same name.

## Checks and hidden assets

Check rows for bulk actions. Use the eye or **Hide** to move entries to **Hidden Assets**, then unhide them there. Delete checked entries to remove them from the index. Use the list’s **Undo** or **Redo** to recover catalogue actions. Scene objects are managed separately in the Outliner.

## Preview and place

Turn **Preview Mode** on and click different model rows. Move, rotate or uniformly scale the preview, then click **Place Asset(s)** to commit it. Turn preview off to clear the temporary display. Check several assets to place a batch at the cursor. Use Blender selection to move individual placements afterward.

## Greybox swaps

Highlight a replacement model in the index, then select the objects to replace in the 3D View. Under **Selected Asset**, use **Swap selected object(s) to selected index asset**. Replacements keep placement position and rotation and use the imported asset scale.

## Whole map import and repair

Choose the map and click **Import entire .map**. Read **Open map import report** for missing BSPs and approximated model variants. Use **Repair incomplete map import** for a partial extraction. Campaign maps can load several normally streamed areas at once. AI, scripts and the complete playable mission require separate authoring.

## Origins and Outliner

In Object Mode, use **Origin to Geometry - all scene meshes** to center mesh origins throughout the scene. Use Blender Undo if needed. Enable **Reveal selected asset in Outliner**, then select a placed asset. An open View Layer Outliner can expand to its collection.

## Model parts and variants

Select a placed model with part metadata. In **Model Parts and Variants**, expand a region with the arrow and toggle choices with the checkboxes. For independently movable meshes, use **Separate all parts and variants into objects**. This includes disabled alternatives, so some newly separate pieces can occupy the same location. Choose one in the Outliner before moving it.

## Apply materials and shaders

Select a material entry in Indexed Asset List and a target mesh, then click **Apply material to selected object**.

To choose an existing game shader, select the object and its active material slot. **Materials and Shaders** displays both names. Click **Scan existing shaders**, choose **Filter by level / category**, and check the shader count. **Choose an existing shader** searches that category. Choose **All levels / shared shaders** to search the complete catalogue. Manual path entry is available through its checkbox.

Click **Assign shader to active material** to set the shader used in Sapien. Shared materials affect all their users. To refresh the Blender textures, use **Load Halo Shader Textures/Masks for Currently selected Material** under Editable Materials with the matching import game and a source map containing the shader. A shader selection alone updates the game reference.

Supported Halo 3 regular shaders now include detail texture blending, including Snowbound's icy purple metal. Halo lighting, reflections and other shader effects can still differ from the Blender preview.

## Paint terrain and edit colors

Select the placed mesh and its material slot. Under **Editable Materials**, load the source shader textures, then choose **Create paintable terrain** or **Create editable colors**. Paint the terrain mask or adjust the color channels, pack your edits and save the blend. Preparation bakes local textures for Halo 3. [Painting, masks, resolution and UV guide](EDITABLE-MATERIALS.md).

## Collision and original vehicles

In **Collision**, Object collision controls the static mesh route. Automatic first tries verified original collision geometry when the imported mesh and source identity match. If that lookup fails, eligible characters/shields use a simple box and other meshes use current surfaces. Material collision settings can explicitly request solid or render-only behavior. Check each object's route in the preparation report.

Changed geometry, modifiers or unsupported part selections can prevent original collision reuse. Source collision geometry is recompiled for Halo 3 static instances, so original animated collision, physics constraints and damage behavior require their own game-object route.

For a matching Halo 3 vehicle, use **Find matching original vehicles**, then **Use original Halo 3 vehicle**. Keep a floor in the scene. Use **Create editable colors** on its exterior material to create fixed custom paint while retaining the matched vehicle route. Preparation creates level-local tag copies. Reach vehicles can be exported as static geometry. [Editable materials](EDITABLE-MATERIALS.md) explains the paint workflow.

## Starter shell and sky

Use **Create starter level shell template** for a simple starting surface. The jungle floor preview uses 010_jungle.map. In **Sapien Sky (Experimental)** click **Scan for map skies**, choose a map and check the selected scenario path. The sky must exist in your Halo 3 kit.

## Prepare and open in Sapien

Enter a unique **Output Level Name (without .map)**. Save and close Sapien, then click **Prepare current scene for sapien**. Review exclusions before continuing. Enable **Generate Test Lighting for Sapien Level** if you want a draft lighting pass. Use **Open in Sapien** after success and test the floor, spawn and collision. [First map walkthrough](FIRST-MAP.md).

## Progress, warnings and conflict resolution

Check **Map Preparation Status**, the activity log and the warning panel near the build controls. Open the diagnostic report for object names and reasons. **Skip objects with export problems** offers a review of eligible preflight exclusions. For a placement conflict, review edits before choosing to use Blender’s placements. A successful structure import can still report collision edges to check in Sapien.

## Storage and repeat builds

Use **Advanced storage** to select an existing cache. Save the blend after changing paths. Keep project manifests and backups with the project. Use the same output name for revisions to one level and a fresh name for another project. [Preparation and backup workflow](HOW-IT-WORKS.md).

## Large models during preparation

Halo Tool limits the render indices in a single instance. HaloBridge can partition oversized static instances internally into aligned pieces. The original Blender object stays editable as one object and its visible triangles are retained. This addresses individual instance limits. Terrain clusters, overall map size and compilation performance still have independent limits.

