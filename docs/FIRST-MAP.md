# Your first Sapien test map

[Home](../README.md) · [Installation](INSTALLATION.md) · [Importing](IMPORTING.md) · [Sidebar reference](FEATURES.md) · [Troubleshooting](TROUBLESHOOTING.md)

This tutorial builds a small Halo 3 level in Blender, compiles it with one button and opens it in Sapien. It takes about 20 minutes. Start small: a floor and a few trees and rocks make problems much easier to spot than a full map.

**Before you start:** complete [Installation](INSTALLATION.md), including H3EK with its tags extracted. Set **Import game** to Halo 3 and confirm **Check setup** passes.

## How preparation works

When you click **Prepare current scene for sapien**, HaloBridge:

1. copies every visible mesh in your scene into a temporary export scene, with your edits and modifiers applied (your scene is never changed),
2. matches each material to a Halo shader, or converts it if it came from another game,
3. writes the geometry with the Halo toolset's ASS exporter and compiles it with H3EK's **Tool**, building collision as it goes,
4. creates the scenario, sets the sky, adds a test player start, and writes original scenery and vehicles as placements,
5. optionally bakes draft test lighting, then can open the level in **Sapien**.

The output goes to `H3EK\tags\levels\multi\<your level name>\`. If anything fails, the previous successful version of that level is restored.

## 1. Start a scene

1. Open a new Blender file (**File → New → General**) and delete the default cube, camera and light.
2. In **Folders and Setup**, click **Create starter level shell template**. It adds:
   - a paintable **Jungle ground** plane with the original jungle terrain textures from the campaign level Sierra 117,
   - a see-through **SkyBoundary** wall that shows roughly where the level's edge is (it's a guide only; preparation builds its own sky boundary),
   - **Master Chief** for scale. He's never exported.

   The template's assets come from `010_jungle.map`, so the Halo 3 maps folder must be set.
3. If the far side of the ground looks grey or is cut off, click **Remove Grey Blender Fog (View Distance)**. It sets the viewport's Clip Start to 0.1 m and Clip End to 999999 m.
4. Save the file (**Ctrl+S**).

You can build your own floor instead. Any mesh works: a subdivided plane, a sculpted terrain, or a level imported with **Import level from .scenario** or **Import entire .map**.

> **Scale:** HaloBridge works at 100 Blender units per Halo world unit (1 world unit = 3.048 m), and the scene's units are set so that sizes read correctly in metres. Preparation converts back automatically. Don't scale your scene by 100 yourself.

## 2. Add some assets

1. In **Folders and Setup → Import entire .map**, choose `010_jungle.map` (Sierra 117) with the arrow under **Choose .map file**, then click **Index .map Assets**. Indexing takes a few seconds and fills the **Indexed Asset List**; nothing is extracted yet.
2. In **Indexed Asset List**, type `tree` in **Search Assets**.
3. Shift + right-click on the ground to put the **3D cursor** where you want a tree.
4. Turn on **Preview Mode**, then click a tree row. The tree appears at the cursor. Click other rows to compare them.
5. Rotate or move the preview if you like, then click **Place asset(s)**.
6. Repeat with rocks or anything else. To copy a placed object, select it and press **Shift+D**.

Tips:

- Turn on Blender's **Material Preview** shading to see textures.
- **Alt+D** makes a linked copy that shares its mesh. Moving it is independent, but editing the mesh in Edit Mode changes every linked copy.
- If moving one object also moves nearby ones, **Proportional Editing** is on: press **O** with the mouse over the viewport to turn it off.
- You can also block out with cubes and use **Swap selected object(s) to selected index asset**. See [Importing → Greybox](IMPORTING.md#greybox-with-cubes-then-swap).

## 3. Check materials

Every surface needs a Halo shader. HaloBridge handles this automatically for:

- **imported assets** — they keep their original shader, or are converted if they came from another game,
- **the starter ground** — it's an editable terrain material that's baked to new textures when you prepare.

For a mesh you made yourself, give it a shader one of two ways:

- **Use an indexed material:** select a material row in the asset list, select your mesh, and click **Apply material to selected object**.
- **Pick any shader in the kit:** select your mesh and its material, open **Shaders**, click **Scan existing shaders** once, click **Choose an existing shader...** and search by name or folder (for example `rock`), then click **Assign shader to active material**.

A plain Blender material with an image texture is not a Halo shader. Preparation reports any material it can't resolve.

To paint the starter ground with grass, rock and dirt, see [Paint terrain](EDITABLE-MATERIALS.md#paint-terrain).

## 4. Check collision

Select an object and open **Collision → Object collision**:

- **(Default) Automatic** — uses the object's original collision when HaloBridge can prove the mesh is unchanged, otherwise a sensible fallback (a box for characters and shields, the mesh's own surfaces for everything else). Leave this for almost everything.
- **Mesh surfaces** — the object's own faces are solid.
- **Simple box** — one solid box around the object. Useful for detailed props you only need to bump into.

Foliage (leaves using Halo's foliage shader) is automatically walk-through. To make another material walk-through, tick the Halo toolset's **Render Only** flag on that material in Blender's **Material Properties**.

## 5. Choose a sky

Open **Sapien Sky (Experimental)**:

1. Leave **Game** on Halo 3.
2. Click **Scan for map skies** (it reads your H3EK tags, so it may take a few seconds the first time).
3. Choose a level from the **Sky** drop-down, for example `guardian`.

If you don't choose one, HaloBridge uses the sky of the level you imported, or Deadlock (High Ground). To use a Halo: CE, Halo 2, ODST or Reach sky, choose that **Game** instead; see [Use a sky from another game](IMPORTING.md#use-a-sky-from-another-game).

## 6. Set up the build

Open **(Experimental) Sapien Map Preparation**:

1. **Export to Sapien:** Halo 3.
2. **Output Level Name (without .map):** change `levelname123` to a name of your own, such as `my_first_map`. Use 3 to 32 lowercase letters, numbers or underscores, starting with a letter. Each level needs its own name: preparing a different scene with the same name replaces that level.
3. **Generate Test Lighting for Sapien Level:** turn this **off** for your first build. Lighting runs 16 extra Tool stages and can take a long time; you can turn it on once the geometry works.
4. **Open Sapien when ready:** turn on if you want Sapien to start automatically.
5. **Skip objects with export problems:** leave off for now.

**Player start:** a new level gets one test player start above the ground, near the 3D cursor's position. Put the cursor over the area you want to spawn in before preparing.

## 7. Prepare

1. **Close Sapien** if it's open. Tool can't write to a level Sapien has open.
2. Save your `.blend`.
3. Click **Prepare current scene for sapien**.
4. A popup lists anything HaloBridge noticed: objects that will be skipped, converted materials, edited scenery that becomes static geometry, and so on. Read it, then **Continue with warnings** or cancel and fix things first.

While it runs, **Map Preparation Status** shows the current stage, the elapsed time, and what's still to come (scene export, materials, geometry and collision, sky and scenario, lighting / final checks). **Open live activity log** and **Open live compiler output** show every step. The stages take very different amounts of time; a compiler line like `creating initial planes... 1%` refers to one sub-step only. **Cancel preparation** stops the build and restores the previous version.

## 8. Test in Sapien

When preparation succeeds, click **Open in Sapien** (or Sapien opens by itself if you turned that on). Then:

- Fly around and check the ground, objects and sky.
- Sapien's camera may start somewhere odd, even underground. That's the editor camera, not the player start; fly to your level.
- Walk into objects to test collision.

If something failed, read **HaloBridge Warnings and Messages → Open diagnostic report**. It names the objects involved and the reason. Fix them in Blender and prepare again; see [Troubleshooting](TROUBLESHOOTING.md).

## 9. Keep iterating

Edit your scene and click **Prepare** again with the **same level name**. HaloBridge keeps a record of which tags it wrote and updates only those, so content you add in Sapien (such as gameplay objects) is meant to stay. Existing player starts are kept. Repeat builds haven't been tested on every kind of map, so save in Sapien and keep a backup of the level folder before rebuilding a level you've put work into.

Add game types, weapons, spawns and other gameplay in Sapien; HaloBridge only builds the level itself.

## Going further

### Start from an existing level

Import a level with **Import level from .scenario (Recommended)** (or **Import entire .map** for levels without kit tags), edit it, and prepare it under a new name. Unedited scenery and vehicles keep their original tags; everything else becomes static geometry. Whole levels can need cleanup before Tool accepts them, and very large levels take a long time to compile.

### Keep a vehicle drivable

An imported Halo 3 vehicle is normally exported as a static shape. To keep it a real vehicle:

1. Select it in the 3D View.
2. Under **Selected Asset → Original Halo 3 Vehicle**, click **Find matching original vehicles**.
3. Click **Use original vehicle tag** and choose the vehicle. Only vehicles that use this model are offered.
4. Prepare as usual. Keep a floor in the scene; a vehicle on its own isn't a level.

The original vehicle tag supplies the model, collision, physics and behaviour. Position, rotation and uniform scale are carried over; mesh edits aren't. **Use static mesh instead** switches back. To give it custom paint, see [Recolor vehicles](EDITABLE-MATERIALS.md#recolor-models-and-vehicles).

### Use other games' assets

Place assets from any game and prepare with **Export to Sapien** set to Halo 3. Materials are converted automatically. See [Use assets from any game](IMPORTING.md#use-assets-from-any-game-in-one-level).

### Build for ODST

Set **Export to Sapien** to **Halo 3: ODST** and set the H3ODSTEK folder (with **Import game** on ODST). Everything else works the same.
