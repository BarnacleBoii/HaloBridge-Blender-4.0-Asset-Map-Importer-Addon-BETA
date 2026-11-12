# Sidebar reference

[Home](../README.md) · [Installation](INSTALLATION.md) · [Importing](IMPORTING.md) · [First map](FIRST-MAP.md) · [Troubleshooting](TROUBLESHOOTING.md)

This page goes through the HaloBridge sidebar from top to bottom and explains every control. Open the sidebar by hovering over the 3D View and pressing **N**, then clicking the **HaloBridge** tab.

Every section can be collapsed by clicking its header. The warnings, the preparation status and the Prepare / Open in Sapien buttons at the bottom always stay visible. While a job is running, buttons that would interfere with it are greyed out.

| Section | What it's for |
| --- | --- |
| [Import game](#import-game) | Which game you're importing from |
| [Folders and Setup](#folders-and-setup) | Folders, setup check, starter template, level and map imports |
| [Indexed Asset List](#indexed-asset-list) | Search, preview and place individual assets |
| [Model Parts and Variants](#model-parts-and-variants) | Choose visible pieces of a placed model |
| [Selected Asset](#selected-asset) | Apply materials, swap objects, original vehicles |
| [Shaders](#shaders) | Give a material a Halo shader |
| [Collision](#collision) | How an object collides in game |
| [Editable Materials](#editable-materials-experimental) | Paint terrain, recolor models |
| [Sapien Sky](#sapien-sky-experimental) | The level's sky |
| [Sapien Map Preparation](#experimental-sapien-map-preparation) | Build settings |
| [Warnings, status and Prepare](#warnings-status-and-prepare) | Build, monitor and open in Sapien |

## Import game

The drop-down at the very top: **Halo: CE, Halo 2, Halo 3, Halo 3: ODST, Halo: Reach**. It picks which game's folders, maps, asset list and storage you're working with. Each game keeps its own settings, so switching back and forth is safe and doesn't touch objects already in your scene. Objects remember which game they came from.

The import game is separate from the game you export to (**Export to Sapien**, further down). You can import from Reach and prepare for Halo 3 without switching back. See [Supported games](GAMES.md).

## Folders and Setup

| Control | What it does |
| --- | --- |
| **\<Game> Editing Kit** | The Mod Tools folder for this game, the one containing `tool.exe`. Not its `tags` subfolder. |
| **\<Game> .map Files** | The MCC folder holding this game's `.map` files, e.g. `...\Halo The Master Chief Collection\halo3\maps`. |
| **Detect folders** | Fills empty folder fields automatically by searching every Steam library, `SteamLibrary` folders on local drives, Foundry's settings, and Xbox app / Game Pass installs. It never overwrites a path you entered. It also reloads this game's saved asset list. |
| **Check setup** | Checks everything HaloBridge needs and writes a report (**HaloBridge diagnostics** in the Text Editor) with what to fix. See [Installation → Check setup](INSTALLATION.md#5-check-setup). |
| **Create starter level shell template** | Adds a paintable jungle ground plane, a see-through SkyBoundary guide wall and Master Chief for scale. Neither the wall nor Master Chief is exported. Needs the Halo 3 maps folder (`010_jungle.map`). |
| **Remove Grey Blender Fog (View Distance)** | Sets every 3D View's Clip Start to 0.1 m and Clip End to 999999 m, so large levels aren't cut off or faded. On huge ranges you may see some flickering; narrow the range if so. |

### Import level from .scenario (Recommended)

Shown for games with Editing Kit support.

| Control | What it does |
| --- | --- |
| Scenario field and **⌄** | The scenario tag path, relative to the kit's `tags` folder and without `.scenario`. The arrow opens a searchable list of every scenario in the kit. |
| **Import level from .scenario (Recommended)** | Imports the whole level from its tags. The note underneath says where the data comes from for this game. See [Importing](IMPORTING.md#1-import-a-level-from-its-scenario-recommended). |
| **Index .scenario Assets** | Adds the level's own objects, instanced meshes and shaders to the asset list instead of importing everything. |

### Import entire .map

| Control | What it does |
| --- | --- |
| **Choose .map file** and **⌄** | The map filename (with `.map`). The arrow lists every map in the maps folder. Choosing a map doesn't start anything. |
| **Import entire .map** | Imports the map's terrain, instances, objects and skies at their original positions. See [Importing](IMPORTING.md#2-import-an-entire-map). |
| **Index .map Assets** | Adds every model, piece of scenery, instance and material the map loads to the asset list. Nothing is extracted until you use an asset. |

### Other controls

| Control | What it does |
| --- | --- |
| **Origin to Geometry - all scene meshes** | Moves every mesh's origin (pivot) to the centre of its geometry. Handy after a whole-level import, where many objects share the level's origin. Use Ctrl+Z to undo. |
| **Advanced storage** | Shows **Storage location**, where HaloBridge keeps its cache and project records. Changing it doesn't move existing files; keep the original location for a level you're still working on. |

## Indexed Asset List

| Control | What it does |
| --- | --- |
| **Reveal selected asset in Outliner** | When on, selecting a placed asset expands and scrolls the Outliner to it. |
| **Undo / Redo** | Undo or redo list actions (hide, unhide, delete from list). Separate from Blender's Ctrl+Z. |
| **Imported Assets / Hidden Assets** | Your list, or the entries you've hidden. |
| **Vegetation, Rocks, Structures, Water, Materials** | Category toggles. Categories are guessed from names, so if you can't find something, turn them all on. |
| **Level Imported** | Show one indexed level or **All Levels**. The same asset can appear under several levels. |
| **All Sources / .map Assets / .scenario Assets** | Show assets indexed from `.map` files, from `.scenario` tags, or both. A short note explains what each is best for. |
| **Search Assets** | Filters by name, source level or asset type as you type. **X** clears it. |
| The list | Click a row to highlight it (and preview it, if Preview Mode is on). Tick rows for bulk actions. The line below shows how many entries are visible out of the total. |
| **Preview Mode: ON / OFF** | When on, clicking a row shows that asset at the 3D cursor as a temporary preview. Turning it off removes the preview. |
| **Select all / Clear checks** | Tick or untick every visible row. Shows how many are ticked. |
| **Hide / Unhide** | Move ticked entries to Hidden Assets, or back. |
| **Delete checked from list** | Remove ticked entries from the list only. Placed objects and cached files are untouched. |
| **Place asset(s)** | Place the ticked assets together at the 3D cursor, or, with nothing ticked, the highlighted asset (keeping the preview's position, rotation and scale). Turns Preview Mode off. |

The first use of an asset extracts its mesh and textures, which can take a moment; later uses come from the cache.

## Model Parts and Variants

Appears when you select a placed model that has parts (vehicles, characters, crates with damage states and so on).

- Click the arrow next to a **region** (for example *hull* or *turret*) to list its choices, and tick the ones you want visible. The checkbox next to the region toggles all of its choices. Parts stay where they are.
- **Separate enabled parts into objects** splits the visible parts into separate objects you can move individually.
- **Separate all parts and variants into objects** splits every choice, including hidden ones, so several pieces may overlap. Pick one in the Outliner before moving it.

Place a preview first; a preview can't be separated.

## Selected Asset

| Control | What it does |
| --- | --- |
| **Apply material to selected object** | With a material row highlighted in the list and a mesh selected, adds that material as a new slot and assigns it (to selected faces only in Edit Mode). |
| Asset details | The highlighted asset's status, source level and a thumbnail. |
| **Swap selected object(s) to selected index asset** | Replaces each selected object with the highlighted asset, keeping its position, rotation and collection. The asset keeps its original size. If the button is greyed out, a note below explains why. |

**Original Halo 3 Vehicle** (or ODST) appears for an imported vehicle model:

| Control | What it does |
| --- | --- |
| **Find matching original vehicles** | Looks in your Editing Kit for vehicle tags that use this model. |
| **Use original vehicle tag** | Choose one. The object becomes a placement of the real vehicle: drivable, with its own collision and physics. Mesh edits don't carry over. |
| **Use static mesh instead** | Goes back to exporting the mesh as static geometry. |

## Shaders

Every exported surface needs a Halo shader tag. This section sets one for the **active material** of the **selected object**, both shown at the top. A note warns you if the material is shared by other objects (they'll change too).

| Control | What it does |
| --- | --- |
| **Scan existing shaders** | Reads every shader in the destination Editing Kit. Do this once, and again after adding shaders to the kit. |
| **Choose an existing shader...** | Opens a search box over all scanned shaders. Type part of a name or folder. |
| **Enter shader path manually** | Instead, type a shader path relative to the kit's `tags` folder, without the extension (e.g. `levels\multi\guardian\shaders\guardian_metal`). |
| **Assign shader to active material** | Sets that shader for Sapien. It doesn't change the Blender preview; to refresh the preview use **Load Halo Shader Textures/Masks** under Editable Materials. |

Imported materials already carry their original shader, so you only need this for your own materials or to change one.

## Collision

Appears for a selected mesh (not for an original vehicle placement). **Object collision** has three choices:

| Choice | Behaviour |
| --- | --- |
| **(Default) Automatic** | Uses the object's original collision from its game's Editing Kit when HaloBridge can prove the mesh is unchanged. Otherwise characters and shields get a simple box, and everything else uses its own mesh surfaces. Foliage leaves are walk-through. |
| **Mesh surfaces** | The object's faces are solid. |
| **Simple box** | One solid box around the object, including any gaps inside it. |

To make one material walk-through (e.g. leaves Automatic doesn't recognise), tick the Halo toolset's **Render Only** flag on it in Blender's Material Properties. The preparation report lists which collision route each object used.

## Editable Materials (Experimental)

Turn an imported material into one you can paint or recolor; preparation bakes it into new Halo 3 textures and shaders in your level folder. Full guide: [Editable materials](EDITABLE-MATERIALS.md).

| Control | What it does |
| --- | --- |
| **Load Halo Shader Textures/Masks for Currently selected Material** | Reloads the selected material's original textures, layers and color masks from its `.map`. Also refreshes older previews. |
| **Create paintable terrain** | Converts a terrain material into numbered shader layers you can paint between. |
| **Create editable colors** | Converts a material into a base texture with four mask-driven tint colors. |
| **Texture resolution** | 512, 1024, 2048 or 4096: the size of the baked texture. |
| **Repeat settings** | Shows X/Y/Z tiling for each texture. |
| **Shader 1–4** sections | Each terrain layer, with its texture images and a **Paint** button. |
| **Paint original blend** | Paint back the level's original mix of layers. |
| **Pack texture edits into blend** | Saves painted images inside your `.blend`. Do this before saving. |

## Sapien Sky (Experimental)

| Control | What it does |
| --- | --- |
| **Game** | Which game the sky comes from. Defaults to the Sapien destination game. |
| **Scan for map skies** (destination game) | Reads every scenario in the destination kit and lists the levels that have a sky. |
| **Sky** (destination game) | Choose a level; its sky tags are used as they are, lighting included. **Original map / default sky** uses the imported level's sky, or Deadlock. |
| **Sky** (other games) | Lists sky models in that game's asset list (index one of its levels first). Choosing one places it in a **Sapien Sky** collection; preparation converts it into a Halo 3 sky. |
| **Remove sky object** | Deletes the placed converted sky. |

If you've chosen another game but no sky, a warning says preparation will stop. Details: [Use a sky from another game](IMPORTING.md#use-a-sky-from-another-game).

## (Experimental) Sapien Map Preparation

| Control | What it does |
| --- | --- |
| **Export to Sapien** | **Halo 3** or **Halo 3: ODST**. Reach is listed but not available yet. Assets from any other game are converted. |
| **Skip objects with export problems** | When on, objects with mesh or material problems found before compiling are offered for skipping in the review popup (they stay in Blender). Compiler errors still stop the build. |
| **Output Level Name (without .map)** | Your level's name: 3–32 lowercase letters, digits or underscores, starting with a letter. Starts as `levelname123`; give each level its own name. The level is written to `levels\multi\<name>` in the Editing Kit. |
| **Generate Test Lighting for Sapien Level** | Bakes draft lighting (16 Tool stages, which can take a while). Turn off for quick geometry tests. |
| **Open Sapien when ready** | Starts Sapien with the level when preparation succeeds. |

## Warnings, status and Prepare

| Control | What it does |
| --- | --- |
| **HaloBridge Warnings and Messages** | The latest result or problem. **ACTION REQUIRED** means something needs your attention. Buttons here open the full diagnostic report, the map or scenario import report, or select the objects involved. |
| **Map Preparation Status** | Current stage, total elapsed time, the stages still to run and recent activity. Stages differ a lot in length; there's no reliable time-remaining estimate. |
| **Open live activity log / Open live compiler output** | Open the step-by-step log or Tool's raw output in Blender's Text Editor. They update while preparation runs. |
| **Cancel preparation** | Stops the build and restores the previous successful version of the level. |
| **Review preparation warnings** | Appears when preparation found something to confirm; choose to continue or stop. |
| **Prepare current scene for sapien** | Builds the level. See [First map](FIRST-MAP.md). |
| **Open in Sapien** | Opens the prepared level in Sapien. |
