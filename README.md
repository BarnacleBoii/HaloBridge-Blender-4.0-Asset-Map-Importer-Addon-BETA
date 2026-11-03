![HaloBridge — Blender importer addon](docs/halobridgelogo.png)

# HaloBridge — Blender 4.0 Asset / Map Importer + Sapien Level Preparation(Beta)

A Blender 4.0 Addon that allows Quickly Importing Halo:MCC fully textured static game assets and entire .maps full textured into Blender, and an experimental option to prepare the current blender scene for a Halo 3 Sapien test level. Currently Supports Halo 3,Halo Reach. more planned.
(Coded with Chat GPT 6 Astra, guided by user input)
**v0.8.5 · Beta preview · Windows x64 · Blender 4.0**

**[Releases and Downloads](https://github.com/BarnacleBoii/HaloBridge-Blender-4.0-Asset-Map-Importer-Addon-BETA/releases)** · **[Installation](docs/INSTALLATION.md)** · **[First map tutorial](docs/FIRST-MAP.md)** · **[Feature guide](docs/FEATURES.md)** · **[Troubleshooting](docs/TROUBLESHOOTING.md)**

## Releases and Downloads

### [Open HaloBridge Releases →](https://github.com/BarnacleBoii/HaloBridge-Blender-4.0-Asset-Map-Importer-Addon-BETA/releases)

Open the latest release, expand **Assets**, and download **HaloBridge-<version>.zip** to install in Blender. You only need the installable add-on ZIP.

| File | What it is for |
| --- | --- |
| `HaloBridge-<version>.zip` | Blender add-on, including the compiled helpers |
| `HaloBridge-<version>-source.zip` | Matching source for developers and contributors |

GitHub's automatic **Source code** ZIP/TAR downloads are for development and do not include the compiled helpers needed to run the add-on.

Follow the [installation guide](docs/INSTALLATION.md) for requirements and setup. **Draft releases are review builds and are not available as published downloads.**


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

**MCC game files and Mod Tools are separate requirements.** Install MCC Halo 3 for its `.map` files. For the full Halo 3 placement/Sapien workflow, also install **Halo 3 Mod Tools - MCC (H3EK)** and extract its supplied tag/data archives. The Editing Kit alone does not replace the MCC maps installation.

For Reach imports, install MCC Halo: Reach. The current Reach setup checker also expects **Halo: Reach Mod Tools - MCC (HREK)**, but asset extraction does not require extracted HREK tags. Preparing Reach assets for Halo 3 still requires **H3EK with extracted Halo 3 tags**, not Reach Sapien. See [which files each workflow needs](docs/INSTALLATION.md#requirements).


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
