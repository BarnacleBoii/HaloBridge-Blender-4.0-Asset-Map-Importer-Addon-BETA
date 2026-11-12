# Installing and updating HaloBridge v0.10.1

[Home](../README.md) · [Importing](IMPORTING.md) · [First map](FIRST-MAP.md) · [Sidebar reference](FEATURES.md) · [Troubleshooting](TROUBLESHOOTING.md)

This guide takes you from nothing to a working HaloBridge sidebar with its folders set up. It takes about 15 minutes, plus download time for the games and Mod Tools.

## Contents

1. [What you need](#what-you-need)
2. [What each task needs](#what-each-task-needs)
3. [Install the games and Mod Tools](#1-install-the-games-and-mod-tools)
4. [Install Blender, the runtimes and the Halo toolset](#2-install-blender-the-runtimes-and-the-halo-toolset)
5. [Install HaloBridge](#3-install-halobridge)
6. [Set up folders](#4-set-up-folders)
7. [Check setup](#5-check-setup)
8. [Where HaloBridge stores its files](#where-halobridge-stores-its-files)
9. [Updating](#updating-without-losing-work)
10. [Uninstalling](#uninstalling)

## What you need

| Component | Version | Why HaloBridge needs it |
| --- | --- | --- |
| [Windows](https://www.microsoft.com/windows/) | 64-bit Windows 10 or 11 | The helper programs and Halo's Editing Kits are Windows-only. |
| [Blender](https://www.blender.org/download/) | **4.0 to 5.2** (5.2 recommended) | Hosts the add-on. Differences between these versions are handled inside HaloBridge. |
| [Halo Asset Blender Development Toolset](https://github.com/General-101/Halo-Asset-Blender-Development-Toolset) | Blender 4.1–5.2: **v432 or newer**. Blender 4.0: **v364 or v432** | A separate Blender add-on. It adds Halo material properties and the **ASS exporter** HaloBridge uses to write level geometry for Halo's compiler. HaloBridge also checks for it before placing assets. |
| [.NET 10 Desktop Runtime](https://dotnet.microsoft.com/en-us/download/dotnet/10.0) | **10**, Windows **x64**, **Desktop Runtime** | Runs HaloBridge's map reader (the extraction helper). The plain ".NET Runtime" is not enough; choose "Desktop Runtime" and "x64". |
| [.NET Framework](https://dotnet.microsoft.com/en-us/download/dotnet-framework/net48) | **4.8 or newer** | Runs HaloBridge's Editing Kit helper, which reads and writes tags through the kit's ManagedBlam. Usually already installed with Windows. |
| [Halo: The Master Chief Collection](https://store.steampowered.com/app/976730/Halo_The_Master_Chief_Collection/) | Steam or Xbox app / PC Game Pass | Its `.map` files supply models, textures and placements for the asset list, whole-map imports and preview textures. |
| [Halo 3 Mod Tools (H3EK)](https://store.steampowered.com/app/1695791/Halo_3_Mod_Tools__MCC/) | Current Steam version, tag archives extracted | Supplies Tool (the level compiler), Sapien, ManagedBlam and the Halo 3 tags. Required for Sapien preparation and Halo 3 `.scenario` import. |
| [HaloBridge](https://github.com/BarnacleBoii/HaloBridge-Blender-4.0-Asset-Map-Importer-Addon-BETA/releases) | **HaloBridge-0.10.1.zip** | The add-on plus its two helper programs. Do not use the source ZIP. |

You do **not** need Reclaimer, Foundry, Osoyoos, or a manually exported asset library. HaloBridge includes its own map reader.

## What each task needs

✅ required · ➖ not needed · ⭕ optional

| Task | MCC maps | H3EK | Other game's Mod Tools | Halo toolset | .NET 10 Desktop | .NET Framework 4.8 |
| --- | --- | --- | --- | --- | --- | --- |
| Browse, preview and place assets from a `.map` | ✅ | ➖ | ➖ | ✅ | ✅ | ➖ |
| **Import entire .map** (any game) | ✅ | ➖ | ➖ | ✅ | ✅ | ➖ |
| Place a single Halo 3 BSP instance from the list | ✅ | ✅ | ➖ | ✅ | ✅ | ✅ |
| **Import level from .scenario**, Halo 3 | ⭕ textures | ✅ | ➖ | ✅ | ✅ | ✅ |
| **Import level from .scenario**, ODST | ⭕ textures | ➖ | ✅ H3ODSTEK | ✅ | ✅ | ✅ |
| **Import level from .scenario**, Reach | ✅ geometry | ➖ | ✅ HREK | ✅ | ✅ | ✅ |
| **Import level from .scenario**, Halo: CE / Halo 2 | ➖ | ➖ | ✅ HCEEK / H2EK | ✅ | ✅ | ➖ |
| Prepare a **Halo 3** Sapien level | ⭕ | ✅ | ⭕ for original collision | ✅ | ✅ | ✅ |
| Prepare an **ODST** Sapien level | ⭕ | ➖ | ✅ H3ODSTEK | ✅ | ✅ | ✅ |

"Other game's Mod Tools" also matters during preparation: when a Halo 3 level contains ODST or Reach models, HaloBridge reads their original collision from that game's kit if it is installed. Without it, those objects get a box or mesh-surface collision instead.

## 1. Install the games and Mod Tools

**MCC.** Install Halo: The Master Chief Collection and make sure the games you want to import from are actually downloaded (in Steam: right-click MCC → Properties → DLC / Installed content). HaloBridge reads these folders inside the MCC install:

| Game | Maps folder inside MCC |
| --- | --- |
| Halo: CE | `halo1\maps` |
| Halo 2 | `halo2\h2_maps_win64_dx11` |
| Halo 3 | `halo3\maps` |
| Halo 3: ODST | `halo3odst\maps` |
| Halo: Reach | `haloreach\maps` |

Keep each maps folder complete. Level maps load textures and objects from shared files (`shared.map`, `campaign.map` and others) in the same folder, so don't move one map on its own.

**Mod Tools.** In your Steam Library, tick **Tools** in the library filter and install **Halo 3 Mod Tools - MCC** (folder `H3EK`). Install the other games' Mod Tools only if you need them (`H3ODSTEK`, `HREK`, `HCEEK`, `H2EK`). Mod Tools are separate from MCC and install to their own folder.

**Extract the tags.** Open the kit's folder (Steam → right-click the tool → Manage → Browse local files) and extract the tag and data archives it ships with, keeping their folder structure. When you're done, the kit folder should look like this:

```
H3EK\
  tool.exe
  sapien.exe
  bin\ManagedBlam.dll
  tags\levels\multi\deadlock\deadlock.scenario   ← tags extracted correctly
  data\
```

If you see `tags\tags\...` or `H3EK\H3EK\...`, an archive was extracted one folder too deep.

## 2. Install Blender, the runtimes and the Halo toolset

1. Install [Blender](https://www.blender.org/download/) 4.0 to 5.2 (x64). 5.2 is recommended.
2. Install the [.NET 10 Desktop Runtime x64](https://dotnet.microsoft.com/en-us/download/dotnet/10.0). On that page, find **.NET Desktop Runtime 10** and download the **Windows x64** installer.
3. If you're on an older Windows install, also install [.NET Framework 4.8](https://dotnet.microsoft.com/en-us/download/dotnet-framework/net48). **Check setup** tells you if it's missing.
4. Download the [Halo Asset Blender Development Toolset](https://github.com/General-101/Halo-Asset-Blender-Development-Toolset/releases) (v432 or newer) and install it in Blender using its own instructions. Enable it in **Edit → Preferences → Add-ons**.
5. Restart Blender after installing the runtimes.

## 3. Install HaloBridge

1. Open the [HaloBridge releases page](https://github.com/BarnacleBoii/HaloBridge-Blender-4.0-Asset-Map-Importer-Addon-BETA/releases), expand **Assets** under v0.10.1 and download **HaloBridge-0.10.1.zip**. Don't unzip it.
2. In Blender, open **Edit → Preferences → Add-ons**.
   - Blender 4.2 and newer: click the **⌄** drop-down at the top right → **Install from Disk…**
   - Blender 4.0 / 4.1: click **Install…**
3. Select `HaloBridge-0.10.1.zip` and click **Install**.
4. Tick **HaloBridge - Halo Level Importing** to enable it. Keep the Halo toolset enabled too.
5. Close Preferences. Hover over the 3D View, press **N**, and click the **HaloBridge** tab on the right edge.

If the tab doesn't appear, reopen Preferences and expand HaloBridge: an error message there usually names the missing piece.

## 4. Set up folders

Everything in HaloBridge depends on two folders per game: the **Editing Kit** folder (the one that contains `tool.exe`) and the **.map Files** folder.

1. At the top of the sidebar, choose the **Import game** (start with Halo 3).
2. Open **Folders and Setup** and click **Detect folders**. HaloBridge looks in:
   - every Steam library listed in Steam's own library file (including libraries on other drives),
   - `SteamLibrary` folders at the root of each local drive,
   - kits registered in Foundry's settings, if you use Foundry,
   - Xbox app / PC Game Pass installs of MCC (the `XboxGames` folder on each drive).

   It only fills **empty** fields, so it never overwrites a path you typed yourself.
3. Check the two fields:
   - **Halo 3 Editing Kit** should end in `H3EK` (not `H3EK\tags`).
   - **Halo 3 .map Files** should end in `halo3\maps` and contain files such as `guardian.map`.
4. To change a path, click the folder icon at the end of the field, or paste a path in.
5. Repeat for each game you want to use. HaloBridge remembers the folders, the chosen map and the asset list for each game separately, so switching **Import game** back and forth is safe. Save your `.blend` to keep these settings with your project.

## 5. Check setup

Click **Check setup**. HaloBridge checks:

- 64-bit Windows and Blender 4.0 or newer,
- the Halo toolset (installed, enabled, and providing the export options HaloBridge uses),
- the Editing Kit (`tool.exe`, `sapien.exe`, `bin\ManagedBlam.dll`) and that its tags are extracted,
- that the maps folder contains `.map` files,
- the two bundled helper programs,
- the .NET 10 Desktop Runtime and .NET Framework 4.8.

"Setup checks passed" means you're ready. Otherwise a report opens in Blender's Text Editor (**HaloBridge diagnostics**) with one line per problem and what to do about it.

Check setup checks the **full** workflow, including Sapien preparation. If you only want to import into Blender, compare its messages with [What each task needs](#what-each-task-needs): for example, a missing ODST kit doesn't matter if you only import ODST `.map` files.

## Where HaloBridge stores its files

HaloBridge never changes your MCC files or the original tags in your Editing Kit. It writes to two places.

**1. Its storage folder** (cache, asset lists, project records). By default this is `HaloBridge` inside your Windows **Documents** folder. If OneDrive has moved your Documents folder, HaloBridge uses that location. If you already have `%USERPROFILE%\Documents\HaloBridge` from an earlier version, it keeps using it. Halo 3 uses the folder itself; other games use a subfolder (`odst`, `reach`, `halo1`, `halo2`).

| Folder | Contents |
| --- | --- |
| `catalogue.json` | The asset list for that game |
| `assets\` | Extracted meshes and textures, reused on later placements |
| `map_scenes\`, `scenario_scenes\` | Whole-level imports |
| `kit_maps\` | Maps built by the Halo: CE / Halo 2 Tool for `.scenario` import |
| `jobs\` | Logs from every helper and compiler run |
| `projects\`, `backups\` | Records of what each preparation wrote, used for safe repeat builds and rollback |

The cache can grow to several GB. If OneDrive syncs your Documents folder, choose a non-synced folder: tick **Advanced storage** at the bottom of **Folders and Setup** and set **Storage location**. This doesn't move existing files. Keep `projects` and `backups` with a level you are still working on.

**2. Your Editing Kit**, only when you prepare a level. For output name `my_level`:

- `H3EK\tags\levels\multi\my_level\` — the scenario, BSP, shaders, bitmaps and sky tags
- `H3EK\data\levels\multi\my_level\` — the exported source geometry

Your saved `.blend` files can refer to textures in the cache. To move a project to another PC, either keep the cache with it or use **File → External Data → Pack Resources** in Blender first.

## Updating without losing work

1. Save your `.blend`, finish or cancel any running HaloBridge job, and close Sapien.
2. In **Edit → Preferences → Add-ons**, find HaloBridge and remove it (**⌄ → Uninstall** on 4.2+, **Remove** on 4.0/4.1).
3. **Restart Blender.** Old Python code stays loaded until you do.
4. Install the new ZIP as in [step 3](#3-install-halobridge), enable it, and reopen your scene.
5. Check that your folder paths are still set and run **Check setup**.

Don't delete the storage folder when updating. Cached assets are refreshed automatically when a new version needs it.

## Uninstalling

Remove HaloBridge in **Preferences → Add-ons**. To free disk space you can then delete the HaloBridge storage folder; this also deletes the records of your prepared levels. Levels already prepared in your Editing Kit stay there until you delete their `levels\multi\<name>` folders.

---

Next: [Import a level into Blender](IMPORTING.md) or [build your first Sapien map](FIRST-MAP.md).
