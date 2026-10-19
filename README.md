# HaloBridge — Blender 4.0 Asset / Map Importer (Beta)
(Coded with Chat GPT 6 Astra, guided by user input)
Quickly Import HaloMCC fully textured game assets and entire .maps into Blender, and prepare its current geometry for testing in Halo 3 Sapien. Currently Halo 3,Halo Reach have been added. Right now I plan on adding Halo 1,2,ODST,4

**v0.8.4 · Beta preview · Windows x64 · Blender 4.0**

**[Download v0.8.4](https://github.com/barnacleboii/HaloBridge-Blender-4.0-Asset-Map-Importer-Addon-BETA/releases/tag/v0.8.4)** · **[Installation](docs/INSTALLATION.md)** · **[First map tutorial](docs/FIRST-MAP.md)** · **[Feature guide](docs/FEATURES.md)** · **[Troubleshooting](docs/TROUBLESHOOTING.md)**

Download **HaloBridge-0.8.4.zip** from the release assets. GitHub's automatic **Source code** downloads are for development and do not include the compiled helpers needed to run the add-on.

## Halo 3 and Halo: Reach

Use **Import game**, above **Folders and Setup**, to select **Halo 3** or **Halo: Reach**. Each game remembers its folders, map filename, storage and catalogue. Save the blend file to retain these settings. Switching does not delete scene objects. Reach assets can share a scene with Halo 3 assets. Switch **Import game** back to **Halo 3**, verify H3EK, then use **Prepare current scene for sapien**. Reach meshes are converted to static Halo 3 geometry with generated collision and converted preview textures. Existing Reach objects do not need reimporting. See [Reach conversion](docs/REACH.md).

See [Reach setup and limitations](docs/REACH.md).

## What you can do

- Import fully textured static objects or entire campaign/multiplayer maps with their original position/material data.
- 3D Preview map assets in the asset list by just clicking on the name to show geometry at 3d cursor
- Search and filter certain assets by map and category.
- Place and edit multiple assets geometry, materials, textures.
- Edit, move, duplicate, or delete geometry in Blender and export that current scene.
- (Experimental)Choose a sky from installed Editing Kit maps, generate surface collision and optional draft lighting, then open the result in Sapien.

## Requirements at a glance

- Windows x64 and **Blender 4.0** (tested with 4.0.0).
- Your own installed **MCC Halo 3** map files; MCC **Halo: Reach** is optional for experimental Reach imports. Keep resource maps alongside level maps.
- **.NET 10 Windows x64 Desktop Runtime** for the extraction helper.
- For Halo 3 Sapien preparation: **Halo 3 Editing Kit with extracted tags**, **.NET Framework 4.8+**, and **Halo Asset Blender Development Toolset 2.364.0 (v364)** enabled in Blender.

See [installation](docs/INSTALLATION.md) for dependency links, folder setup and update instructions. No game maps, models, textures, tags or Editing Kit binaries are bundled.

## Start here

1. Install the [requirements and add-on](docs/INSTALLATION.md).
2. Open **3D View → N sidebar → HaloBridge**, choose **Detect folders**, then **Check setup**.
3. Enter a map filename such as `010_jungle.map` and choose **Import Map Assets**.
4. Turn **Preview Mode** on, select an asset, and choose **Place asset(s)**.
5. Build a small scene and follow the [first-map tutorial](docs/FIRST-MAP.md) to test it in Sapien.

You do not need a separate Reclaimer installation, Osoyoos, or a manually extracted asset library.

## Experimental Sapien preparation

**Sapien preparation is an experimental static-geometry workflow.** It exports your current meshes and generates collision from their surfaces. It does not recreate original AI, scripts, animated doors, breakable objects, vehicles, multiplayer rules, or baked lighting. A whole-map import is a visual starting point, not a complete recovered playable mission.

Some assets are missing or approximate, and invalid or oversized geometry can fail Halo's compiler. Preview materials are approximations; Halo 3 exports use installed shader tags, while Reach exports generate simplified Halo 3 shaders from preview textures. Large Project Reclaimer maps and multiplayer packaging need further testing. Start with a small level and keep your saved work.

Tested locally with Blender 4.0.0 and Halo exporter 2.364.0. A Shrine scene has compiled and opened in Sapien player simulation; a second clean PC and broad map compatibility have **not** been verified. See [verification history](TESTING.md) and [known limits](docs/LIMITATIONS.md).

## Guides

| Guide | Covers |
| --- | --- |
| [Install and update](docs/INSTALLATION.md) | Requirements, downloads, setup, storage and upgrades |
| [Create your first map](docs/FIRST-MAP.md) | Place assets, edit terrain, choose materials and test in Sapien |
| [Feature reference](docs/FEATURES.md) | Asset list, filters, preview, bulk actions, whole-map import and preparation |
| [Troubleshooting](docs/TROUBLESHOOTING.md) | Moving copies, missing textures, errors, slow imports and sky selection |
| [How HaloBridge works](docs/HOW-IT-WORKS.md) | Extraction, cache, geometry export and scenario preparation |
| [Limits and roadmap](docs/LIMITATIONS.md) | Supported scope and areas that need community testing |

## Community

[Report a bug or request a feature](https://github.com/barnacleboii/HaloBridge-Blender-4.0-Asset-Map-Importer-Addon-BETA/issues/new/choose). Include your version, steps to reproduce, and sanitized error text. Please do not upload game maps, tags, extracted assets, caches, or Blender files containing game content.

Code and documentation contributions are welcome: see [CONTRIBUTING.md](CONTRIBUTING.md). The release includes both the installable add-on and matching source archive.

HaloBridge is an independent community project, not an official Microsoft, Bungie, or 343 Industries tool. No Halo game content or Editing Kit binaries are included. Supply them from your own installations. Code is licensed under [GPL-3.0](LICENSE); see [dependency credits](THIRD-PARTY.md). The code license does not grant rights to Halo assets.
