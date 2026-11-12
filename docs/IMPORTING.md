# Importing Halo levels and assets into Blender

[Home](../README.md) · [Installation](INSTALLATION.md) · [First map](FIRST-MAP.md) · [Sidebar reference](FEATURES.md) · [Troubleshooting](TROUBLESHOOTING.md)

HaloBridge has three ways to bring Halo content into Blender. You don't need to prepare a Sapien level to use any of them; importing on its own is fine.

| Route | Button | Best for | Source |
| --- | --- | --- | --- |
| [**Level from .scenario**](#1-import-a-level-from-its-scenario-recommended) | **Import level from .scenario (Recommended)** | Editing an original level and sending it back to Sapien | Editing Kit tags (textures from the `.map`) |
| [**Entire .map**](#2-import-an-entire-map) | **Import entire .map** | Any level in MCC, including ones without kit tags | MCC `.map` file |
| [**Asset list**](#3-browse-and-place-individual-assets) | **Index .map Assets** / **Index .scenario Assets** | Picking individual models, scenery and materials | Either |

Before you start, finish [Installation](INSTALLATION.md) and set the folders for the game you want under **Folders and Setup**.

## 1. Import a level from its .scenario (recommended)

A `.scenario` is the master tag of a level in the Editing Kit. It lists the level's BSPs (terrain and structure), every placed object, the skies and more. Importing from the scenario gives you the level as its designers authored it, rather than a reconstruction of the compiled game file.

**Steps**

1. Choose the **Import game** and make sure its **Editing Kit** folder is set.
2. In **Folders and Setup → Import level from .scenario (Recommended)**, click the **⌄** arrow next to the scenario field. A searchable list of every scenario in the kit opens; type part of a name (for example `guardian`) and pick one. You can also type the path yourself, without the `.scenario` extension: `levels\multi\guardian\guardian`.
3. Click **Import level from .scenario (Recommended)**. Progress shows at the bottom of the sidebar. A large level can take a few minutes the first time; later imports of the same level reuse the cache.
4. When it finishes, read the **HaloBridge scenario import report** in Blender's Text Editor. It lists anything that couldn't be imported.
5. Switch the viewport to **Material Preview** (the third sphere icon at the top right of the 3D View) to see textures.

The new objects go into a collection named after the level, split into sub-collections (BSPs, Scenery, Crates, Machines, Vehicles and so on).

### What you get (Halo 3 and ODST)

- **BSP geometry from the source files stored inside each BSP tag**, with the original instance names (`%name`) and transforms. Instanced geometry shares one mesh, as in the original level: editing one copy in Edit Mode edits all of them.
- **Every scenery, crate, machine, control and vehicle placement** with its position, rotation, scale and variant. Object meshes come from the source stored in each render model tag, using the pieces that the placement's variant selects.
- **Weapons and equipment** in their own collections, for reference only. They aren't exported.
- **Materials named after the exact shader tag** each surface uses, including source flags such as two-sided, render-only and collision-only. These names are what Sapien preparation uses, so original surfaces keep their original shaders.
- **Preview textures** from the matching `.map` (for example `guardian.map` for Guardian), looked up by exact shader path. Without the map, the geometry and shader assignments still import; materials are just untextured.
- **Special surfaces** (portals, `+sky` faces, seam sealers, weather polygons) go into a hidden **Special surfaces** collection. They are never exported.

If a tag has no stored source file, the report says so. A render model without one falls back to the mesh from the `.map`. A BSP without one is skipped; use **Import entire .map** for that level instead.

**Original objects stay original.** When you prepare this scene for Sapien, unedited scenery is written as placements of its own scenery tag, keeping its real collision, physics and variants, and vehicles keep their vehicle tags. If you edit a scenery mesh, it's exported as static geometry instead, and the preparation warnings say which objects changed.

### Halo: Reach

The Reach Editing Kit (HREK) has the scenario and placements but no source models or BSP source files. HaloBridge takes placements from HREK and geometry from the matching `.map`, so set both folders. The report says which parts came from the map. See [Halo: Reach](REACH.md).

### Halo: CE and Halo 2

The Halo: CE (HCEEK) and Halo 2 (H2EK) kits have no ManagedBlam, so HaloBridge can't read their tags directly. Instead it asks the kit's own **Tool** to build a map from the scenario, then imports that map exactly like **Import entire .map**.

- Halo: CE scenarios are under `levels\` (for example `levels\test\bloodgulch\bloodgulch`); Halo 2 scenarios are under `scenarios\` (for example `scenarios\multi\ascension\ascension`).
- Building takes about 10 seconds for Blood Gulch and one to two minutes for a Halo 2 level.
- The built map is kept in HaloBridge's storage (`kit_maps`) and reused until a tag in that scenario's folder changes.
- Tool writes into the kit's own maps folder while building. If a map of the same name was already there, HaloBridge puts it back afterwards.
- Because the geometry comes from a built map, instance names and material flags are those of the map, not of the original source files.

## 2. Import an entire .map

Use this for any level in MCC, including levels with no Editing Kit tags, DLC maps, and campaign missions.

1. Choose the **Import game** and set its **.map Files** folder.
2. Under **Import entire .map**, click the **⌄** arrow below **Choose .map file** to pick from the maps in that folder, or type a filename including `.map` (for example `guardian.map`).
3. Click **Import entire .map**. You don't need to index the map first, and the 3D cursor and list filters are ignored: everything goes at its original position.
4. Read **Open map import report** (in **HaloBridge Warnings and Messages**). It lists BSPs that couldn't be decoded, objects whose variant had to be approximated, and anything unsupported.

You get the level's BSPs (terrain and structure), instanced geometry, scenery and other static objects, and the skies, grouped into collections, all with preview textures.

What you don't get: AI, scripts, game types, animations, doors that open, original collision and baked lighting. The result is a visual layout to build on, not the playable mission. Campaign maps contain areas the game normally streams in one at a time, so they can be heavy; give Blender time and watch the progress line.

## 3. Browse and place individual assets

The asset list (**Indexed Asset List**) is a catalogue of every model, piece of scenery, instanced mesh and material in a level. Indexing only reads the list; an asset's mesh and textures are extracted the first time you use it and cached after that.

### Index a level

- **Index .map Assets** (under **Import entire .map**): everything the compiled map loads, including shared objects such as characters, weapons and vehicles. Best for browsing and kitbashing.
- **Index .scenario Assets** (under **Import level from .scenario**): only the level's own objects, instanced meshes and shaders, built from the kit's source files with exact shader names. Best for editing and Sapien.

Index as many levels and games as you like; each one adds to that game's list.

### Find assets

In **Indexed Asset List**:

- **Search Assets** filters as you type (try `tree`, `rock`, `scorpion`). The **X** clears it.
- The category toggles (**Vegetation, Rocks, Structures, Water, Materials**) hide or show whole categories.
- **Level Imported** shows one indexed level or **All Levels**.
- **All Sources / .map Assets / .scenario Assets** shows assets from either kind of index.
- **Imported Assets / Hidden Assets** switches between your list and the entries you hid.

The line under the list says how many entries are shown out of the total. If something seems missing, clear the search, choose **All Levels** and **All Sources**, and turn all categories on.

### Preview and place

1. Put the **3D cursor** where you want the asset (Shift + right-click in the viewport).
2. Click **Preview Mode: OFF** to turn it on (it shows **Preview Mode: ON**).
3. Click a row. The asset appears at the cursor as a temporary preview. Click another row to swap it. The first preview of an asset takes a moment while it is extracted.
4. Move, rotate or scale the preview if you like.
5. Click **Place asset(s)**. The preview becomes a normal object with the same transform, and Preview Mode turns off.

To place several at once, tick the checkboxes on their rows (or **Select all**) and click **Place asset(s)**: all ticked assets are placed together at the cursor. Ticks take priority over the highlighted row, so click **Clear checks** when you want just one.

### Materials

Material rows are materials only, with no mesh. To use one:

1. Select the material row in the list.
2. Select a mesh in the 3D View.
3. Click **Selected Asset → Apply material to selected object**.

The material is added as a new slot and assigned to the whole object, or only to the selected faces if you're in Edit Mode. The object's other materials stay. Unused slots are ignored when you prepare.

### Organize the list

- **Hide** (or the eye icon on a row) moves ticked entries to **Hidden Assets**; **Unhide** brings them back.
- **Delete checked from list** removes entries from the list only. It never deletes placed objects or cached files.
- The list's own **Undo / Redo** buttons undo these list actions. They're separate from Blender's Ctrl+Z.

### Greybox with cubes, then swap

Block out a level with simple cubes, then swap them for real assets:

1. Highlight a model in the asset list.
2. Select one or more objects in the 3D View (Object Mode).
3. Click **Selected Asset → Swap selected object(s) to selected index asset**.

Each selected object is replaced by the asset at the same position and rotation, in the same collection. The asset keeps its original size, so scale the results afterwards if needed. All swapped copies share one mesh.

### Model parts and variants

Select a placed model (a Warthog, a Spartan, a crate with damage states) and the **Model Parts and Variants** section appears. Expand a region with its arrow and tick the pieces you want visible. **Separate enabled parts into objects** splits the visible pieces into separate objects; **Separate all parts and variants into objects** splits every alternative, so several pieces can end up in the same spot. Choose one in the Outliner before moving it.

## Use assets from any game in one level

Assets from Halo: CE, Halo 2, Halo 3: ODST and Halo: Reach can sit in the same Halo 3 Sapien level as Halo 3 assets.

1. Switch **Import game** to the game you want, set its folders, and import or place its assets as usual.
2. Switch to another game and keep going. Objects already in the scene remember which game they came from.
3. When you prepare, set **Export to Sapien** to Halo 3 (or ODST).

During preparation, each object's current mesh and position are exported as static geometry. Any material whose shader isn't from the destination game is rebuilt as level-local Halo 3 bitmaps and shaders: base color, normal map, UV tiling and cut-out transparency. ODST shaders that also exist in H3EK reuse the Halo 3 shader instead.

Collision uses the original collision from the source game's Editing Kit when that kit is installed (Halo 3, ODST and Reach); Halo: CE and Halo 2 objects use a box or their mesh surfaces. If Tool rejects an object's collision, HaloBridge recompiles that object with a simple box, then without collision, and the report says so.

Gameplay objects aren't converted: a Reach Warthog from another game becomes a static shape. Sky models placed from an asset list are left out of the level geometry; choose the level's sky under **Sapien Sky** instead.

## Use a sky from another game

Under **Sapien Sky (Experimental)**, choose the **Game** first, then the **Sky**.

**Sky from the destination game** (Halo 3, or ODST for an ODST level): click **Scan for map skies**, then pick a level from the **Sky** drop-down. That level's own sky tags are used as they are, including their lighting.

**Sky from any other game:**

1. Index one of that game's levels first (switch **Import game**, then **Index .map Assets** or **Index .scenario Assets**). The **Sky** drop-down lists sky models from that game's asset list.
2. Choose a sky. It's placed in a **Sapien Sky** collection. It's never exported as level geometry, but you can check its size and position and move or scale it.
   - Halo: CE and Halo 2 draw their skies around the camera, so HaloBridge enlarges these to surround your level: four times the level's radius, between 2,000 and 6,000 world units.
   - Halo 3, ODST and Reach skies keep their original size.
3. Prepare as usual. HaloBridge converts the sky's textures, writes it as a sky render model, builds it with Tool's `render-sky`, and creates the model and scenery tags the scenario uses as its sky.

Things to know about converted skies:

- Sky textures are converted as self-lit (unshaded), so they look like a skybox.
- A converted sky has no sky lighting of its own. If **Generate Test Lighting** is on, the level is lit with the destination kit's sky (the last one you chose for that game, or Deadlock), and then the converted sky is swapped in.
- Halo: CE and Halo 2 skies are stacks of see-through layers, so their converted shaders blend additively and can look bright.
- Halo: CE colours its clouds with shader tints that aren't converted, so its clouds look grey.
- Only the sky's geometry and its base, normal and alpha textures are converted. Fog, atmosphere settings, moving clouds and other animated effects aren't.
- **Remove sky object** deletes the placed sky. If a sky chosen with an older version looks white, choose it again.

## Refresh older material previews

Materials imported with older versions keep their old preview until you reload them. Select the object and its material slot, make sure **Import game** matches the material's game, and click **Editable Materials → Load Halo Shader Textures/Masks for Currently selected Material**.

---

Next: [build your first Sapien map](FIRST-MAP.md), or look up any button in the [sidebar reference](FEATURES.md).
