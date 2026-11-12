# Troubleshooting

[Home](../README.md) · [Installation](INSTALLATION.md) · [Sidebar reference](FEATURES.md) · [Known limits](LIMITATIONS.md)

**First step for any problem:** look at **HaloBridge Warnings and Messages** near the bottom of the sidebar and click **Open diagnostic report**. It names the objects, files and reasons involved. For setup problems, run **Check setup**.

## Contents

- **Setup:** [HaloBridge tab missing](#the-halobridge-tab-doesnt-appear) · [Detect folders found nothing](#detect-folders-didnt-find-my-folders) · [Check setup complaints](#check-setup-reports-problems) · [Helper or runtime errors](#a-helper-wont-start)
- **Importing:** [Empty asset list](#the-asset-list-is-empty) · [Map picker empty](#the-map-picker-is-empty-or-a-map-isnt-found) · [Slow imports](#importing-or-previewing-is-slow) · [Missing textures](#textures-are-missing-white-or-flat) · [Missing BSPs](#missing-bsps-or-objects-after-a-whole-level-import) · [.scenario import problems](#scenario-import-problems)
- **Editing:** [Copies move together](#moving-one-object-moves-others) · [Swap changes size](#swapped-assets-have-a-different-size) · [Flickering / grey view](#flickering-surfaces-or-a-grey-cut-off-view)
- **Preparing:** [Level name rejected](#output-level-name-is-rejected) · [Prepare fails](#prepare-fails) · [Seems stuck](#preparation-seems-stuck) · [Geometry limits](#cluster--too-many-vertices-triangles-or-strip-segments) · [Collision errors](#collision-errors-and-red-debug-geometry) · [Ownership conflict](#old-output-or-ownership-conflict)
- **Sky:** [Wrong or white sky](#wrong-white-or-dark-sky)
- **In Sapien:** [Player start underground](#the-camera-or-player-start-is-underground)
- [Reporting a bug](#reporting-a-bug)

## Setup

### The HaloBridge tab doesn't appear

- Make sure the add-on is ticked in **Edit → Preferences → Add-ons**. Expand it: an error there names the problem.
- The tab is in the 3D View's sidebar: hover over the viewport and press **N**.
- You installed the release ZIP (**HaloBridge-0.10.0.zip**), not GitHub's "Source code" ZIP or the `-source` ZIP.
- After updating, restart Blender.

### Detect folders didn't find my folders

Detect folders searches every Steam library, `SteamLibrary` folders at the root of local drives, Foundry's settings, and Xbox app / Game Pass installs (`XboxGames`). It only fills **empty** fields and only accepts a maps folder that actually contains `.map` files.

- If a field already had a wrong path, clear it and click **Detect folders** again.
- If the game's content isn't downloaded in MCC, the maps folder won't be found. Check MCC's installed content.
- For other locations (an external drive, a custom folder), set the path yourself with the field's folder button. Use the kit folder that contains `tool.exe`, and the folder that contains the `.map` files.

### Check setup reports problems

Check setup checks the **whole** workflow, including Sapien preparation, so some messages may not matter for what you're doing. Compare with [What each task needs](INSTALLATION.md#what-each-task-needs).

| Message mentions | Fix |
| --- | --- |
| Halo Asset Blender Development Toolset | Install and enable it (v432 or newer; v364 also works on Blender 4.0). |
| "cannot export on Blender ... (Python 3.13)" | Your toolset is too old for Blender 5.x. Install the current release. |
| Editing Kit folder / `tool.exe` / `ManagedBlam.dll` | The kit path is wrong or points at a subfolder. Use the folder containing `tool.exe`. |
| tag archives / `deadlock.scenario` | The kit's tags aren't extracted. See [Installation](INSTALLATION.md#1-install-the-games-and-mod-tools). |
| MCC maps folder | The maps path is wrong or empty. |
| .NET 10 Desktop Runtime | Install the **Desktop** runtime, **x64**, then restart Blender. |
| .NET Framework 4.8 | Install .NET Framework 4.8. |
| Helper missing | Reinstall the release ZIP. |

### A helper won't start

HaloBridge runs two small programs from its `bin` folder. If Windows security or antivirus software blocks them, the report says the helper failed to start. Reinstall from the official release ZIP and, if your security software quarantined a file, restore it. Don't turn off your security software entirely.

## Importing

### The asset list is empty

**Detect folders** sets folders but doesn't index anything. Choose a map with **Choose .map file** and click **Index .map Assets** (or choose a scenario and click **Index .scenario Assets**). If the list still looks empty: clear **Search Assets**, choose **All Levels** and **All Sources**, turn on every category toggle, and check you're on **Imported Assets** rather than **Hidden Assets**.

### The map picker is empty or a map isn't found

The picker lists the files directly inside the **.map Files** folder for the current game. Check the path, then reopen the picker (it refreshes each time). You can also type a filename including `.map`. Remember Halo 2 uses `halo2\h2_maps_win64_dx11`.

### Importing or previewing is slow

The first use of an asset or level extracts geometry and converts textures, and a whole level can contain thousands of objects and several BSPs. Several minutes can be normal for big campaign levels. Later imports reuse the cache and are much faster. Watch the progress line instead of clicking again. Cancel works between steps; a single big step can take a while to finish.

### Textures are missing, white or flat

- Switch the viewport to **Material Preview**.
- For `.scenario` imports, set the game's **.map Files** folder too: textures come from the matching map. A shader that isn't in that map has no preview texture.
- Halo: CE / Halo 2 assets imported with an older version: select the material and click **Load Halo Shader Textures/Masks for Currently selected Material**, or re-import.
- Halo's layered shaders, reflections and lighting are approximated in Blender, so some surfaces will look different from the game.

### Missing BSPs or objects after a whole-level import

Read the import report. Make sure the maps folder is complete (shared resource maps must stay next to level maps) and the storage folder is writable. Some content can't be recovered as static geometry (cutscene-only objects, Reach's developer-only BSPs). Approximated variants are listed as such.

### .scenario import problems

- **"BSP has no source"** — that BSP tag doesn't contain its source file. Use **Import entire .map** for that level.
- **Halo: CE / Halo 2 build fails** — the kit's Tool couldn't build the scenario. The report includes Tool's output. Make sure the kit folder is right and its tags are intact.
- **Reach geometry missing** — set the Reach **.map Files** folder; Reach geometry comes from the map.

## Editing

### Moving one object moves others

Turn off **Proportional Editing**: hover over the viewport and press **O** (the circle icon in the viewport header shouldn't be highlighted). Also check you're in Object Mode with only one object selected, and that the objects aren't parented to each other.

Linked copies (**Alt+D**, swaps, instanced BSP geometry) share one mesh: moving them in Object Mode is independent, but editing vertices in Edit Mode changes all of them. Use **Object → Relations → Make Single User → Object & Data** to give one its own mesh.

### Swapped assets have a different size

This is by design: a swap keeps each object's position and rotation, but the asset keeps its original size. Scale the results afterwards. Placing from a preview keeps the preview's scale instead.

### Flickering surfaces or a grey, cut-off view

- Distant geometry fading to grey or disappearing: click **Remove Grey Blender Fog (View Distance)**.
- Flickering where surfaces overlap: a very wide clip range reduces depth precision. In the viewport's **View** panel (N sidebar → View), raise **Clip Start** (for example 1 m) and lower **Clip End** to what you need.
- Glass and other see-through surfaces with a back face: HaloBridge gives them backface culling when you load the material. Reload older materials with **Load Halo Shader Textures/Masks**.

## Preparing

### Output level name is rejected

Use 3–32 characters: lowercase letters, numbers and underscores, starting with a letter. No `.map`, no spaces, no capitals, no folders. Example: `my_first_map`. The old placeholder `Level_Name_Here` must be replaced.

### Prepare fails

1. Open **Open diagnostic report**. It lists every issue found so far; later stages can't be checked until earlier ones pass.
2. Close Sapien and try again (Tool can't write to a level Sapien has open).
3. Run **Check setup**.
4. For geometry errors, the report names the Blender object. Hide or delete it and prepare again to confirm, then fix its mesh.

**Continue with warnings** accepts known omissions; it can't get past a compiler error. When a build fails, the previous successful version of the level is restored.

### Preparation seems stuck

Open **Open live activity log** or **Open live compiler output** in **Map Preparation Status**. The status shows elapsed time, time since the compiler last printed something, CPU use (100% = one full core) and memory. A busy CPU means it's working.

The longest stage is usually geometry and collision. A compiler line like `creating initial planes... 1%` is one sub-step, not the whole build. Very dense meshes (heavily subdivided terrain) are slow to compile: the **Main structure** line in the activity log names the object and its triangle count. Test lighting adds 16 more stages; turn it off for faster tests.

**Cancel preparation** stops the build and restores the previous version.

### Cluster / too many vertices, triangles or strip segments

"Cluster" numbers come from Tool, not from Blender. The report's **Structure geometry context** and the activity log's **Main structure** line name the Blender object. Reduce the density of that mesh (on a copy first), or split a huge terrain into several objects. HaloBridge doesn't simplify geometry for you. Very large single models are automatically split into aligned pieces to stay within Halo's per-instance limit.

### Collision errors and red debug geometry

- **Ambiguous or degenerate edges** — HaloBridge automatically recompiles that object with a simple box, then without collision, and lists it in the report. Walk into it in Sapien to check.
- **Red trees or "overlapping surfaces" labels in Sapien** — these are Tool's debug markers, not a visible asset. They point at overlapping or duplicate faces. The report lists them by object name.
- **Leaves you can't walk through** — Automatic makes Halo foliage shaders walk-through. For other leaf materials, tick the Halo toolset's **Render Only** flag in Material Properties (not on trunks or ground you want to stand on).
- **Plane builder unable to converge / open edges** — the mesh has holes, duplicate faces or self-intersections. Clean it up, or set its **Object collision** to **Simple box**.

### Old output or ownership conflict

HaloBridge only overwrites a level it created itself (it keeps a record in its `projects` folder). If the name belongs to something else, or the record is missing, use a new **Output Level Name**. If Sapien changed the level since your last build, HaloBridge asks before replacing its placements. Don't delete project records to force an overwrite.

## Sky

### Wrong, white or dark sky

- Choose the sky explicitly: **Sapien Sky → Game → Sky**. For the destination game, click **Scan for map skies** first.
- A converted sky chosen with an older version looks white: choose it again.
- A converted sky looks grey (Halo: CE clouds) or very bright (Halo: CE / Halo 2 layers): that's a known limit of the conversion.
- A dark level with a converted sky: turn on **Generate Test Lighting**. HaloBridge lights the level with a kit sky first because converted skies carry no lighting.
- If you picked another game's sky but none is placed, preparation stops and says so.

## In Sapien

### The camera or player start is underground

A new level gets a player start above the ground near the 3D cursor. Sapien's **editor camera** is separate and remembers its last position, so it can start underground; fly up to your level. Existing player starts are kept on later builds, so move them in Sapien if you change the terrain.

## Reporting a bug

Open [Issues → New issue → Bug report](https://github.com/BarnacleBoii/HaloBridge-Blender-4.0-Asset-Map-Importer-Addon-BETA/issues/new/choose) and include:

- HaloBridge, Blender and Halo toolset versions,
- the game and map or scenario,
- whether it was a first import or a repeat,
- exact steps,
- the diagnostic report text, with personal folder names (like your Windows user name) removed.

Don't attach maps, tags, caches or `.blend` files containing game content.
