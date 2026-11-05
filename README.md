![HaloBridge — Blender importer addon](docs/halobridgelogo.png)

# HaloBridge — Blender 4.0 Asset / Map Importer + Sapien Level Preparation(Beta)

A Blender 4.0 Addon that allows Quickly Importing Halo:MCC fully textured static game assets and entire .maps full textured into Blender, and an experimental option to prepare the current blender scene for a Halo 3 Sapien test level. Currently Supports Halo 3,Halo Reach. more planned.
(Coded with Chat GPT 6 Astra, guided by user input)
**v0.9 · Beta preview · Windows x64 · Blender 4.0**

**[Releases and Downloads](https://github.com/BarnacleBoii/HaloBridge-Blender-4.0-Asset-Map-Importer-Addon-BETA/releases)** · **[Installation](docs/INSTALLATION.md)** · **[First map tutorial](docs/FIRST-MAP.md)** · **[Feature guide](docs/FEATURES.md)** · **[Troubleshooting](docs/TROUBLESHOOTING.md)**

## Releases and Downloads

### [Open HaloBridge Releases →](https://github.com/BarnacleBoii/HaloBridge-Blender-4.0-Asset-Map-Importer-Addon-BETA/releases)

Open the latest release, expand **Assets**, and download **HaloBridge-<version>.zip** to install in Blender. You only need the installable add-on ZIP.
GitHub's automatic **Source code** ZIP/TAR downloads are for development and do not include the compiled helpers needed to run the add-on.

Follow the [installation guide](docs/INSTALLATION.md) for requirements and setup. **Draft releases are review builds and are not available as published downloads.**

## Requirements — Blender importing or Sapien testing?

**MCC maps provide the models and textures. Mod Tools provide editable tags and the Sapien compilation tools.** You do not need to prepare a Sapien level to use HaloBridge assets in Blender.
| Component | Required version / setup |
| --- | --- |
| [Windows](https://www.microsoft.com/windows/) | 64-bit Windows; other operating systems are not supported |
| [Blender 4.0](https://download.blender.org/release/Blender4.0/) | 4.0; tested with 4.0.0 |
| [Halo: The Master Chief Collection](https://store.steampowered.com/app/976730/Halo_The_Master_Chief_Collection/) | Fully Installed PC game, Including Halo 3 or Reach installed |
| [Halo 3 "Mod Tools" Editing Kit](https://store.steampowered.com/app/1695791/Halo_3_Mod_Tools__MCC/) | Tool, Sapien and extracted data/tag archives |
| [Halo Asset Blender Development Toolset](https://github.com/General-101/Halo-Asset-Blender-Development-Toolset) | **2.364.0 (v364)** installed and enabled; other exporter versions are rejected |
| [.NET Desktop Runtime](https://dotnet.microsoft.com/en-us/download/dotnet/10.0) | **10**, Windows **x64** Desktop Runtime, not only the base .NET runtime |
| [.NET Framework](https://dotnet.microsoft.com/en-us/download/dotnet-framework/net48) | **4.8 or newer** |


| Workflow | Game files and kit needs |
| --- | --- |
| Blender-only indexing, model/material extraction and whole-map visual layout | Install the selected MCC game and keep its complete maps/resource directory. These extraction routes read MCC data, not extracted Editing Kit tags. |
| Individual Halo 3 BSP-instance placement | Also needs **H3EK with matching extracted BSP tags** because the current placement path requests collision metadata. |
| Prepare any scene for **Halo 3 Sapien**, including Reach assets | Needs **H3EK tools and extracted Halo 3 tags**, plus the shader/sky dependencies used by the scene. |
| Reach importing | MCC Reach maps/resources supply assets. Extracted HREK tags are not required by extraction, but the current full-workflow setup checker checks HREK installation. |

All users need **Windows x64, Blender 4.0, the supported Halo Blender toolset 2.364.0, and .NET 10 Desktop Runtime x64**. The tag helper uses **.NET Framework 4.8+**. Check setup currently checks full-workflow prerequisites even for import-only users; MCC alone does not support every current placement route. Halo 3 is the only implemented Sapien destination.

Start with the **[detailed installation guide and requirements matrix](docs/INSTALLATION.md#requirements)**, then choose **[Blender-only importing](docs/IMPORTING.md)** or **[First Sapien test map](docs/FIRST-MAP.md)**. No game maps, models, textures, tags or Editing Kit libraries are bundled. You do not need a standalone Reclaimer installation or a manually exported asset library.

### Why install the Halo Blender toolset too?

**HaloBridge is the browser and workflow; the [Halo Asset Blender Development Toolset](https://github.com/General-101/Halo-Asset-Blender-Development-Toolset) provides Halo-specific Blender properties and the ASS geometry exporter used for Sapien preparation.** In the current build, individual asset placement also checks this add-on, including Reach placement, so install and enable **v364 / 2.364.0** even for the supported Blender-only placement workflow. It does not supply or extract the game content; that comes from your MCC maps.

See [why each component is needed](docs/INSTALLATION.md#why-the-halo-asset-blender-development-toolset-is-required) for the difference between this Blender add-on, Steam Mod Tools, the two .NET runtimes, and the optional-versus-required import paths.

## New in v0.9

Latest interface refresh:

- **Choose .map file:** searchable dropdown lists maps from the selected game folder, alongside an editable filename field.
- **Warnings where you need them:** a second HaloBridge Warnings and Messages section sits above Map Preparation Status. The original top panel remains; both show the same errors and action buttons.
- **Preview status:** green ON / red OFF icons, with Place Asset(s) highlighted while previewing. No flashing or global theme changes.
- **One Editing Kit setup:** preparation reuses the Halo 3 path saved under Folders and Setup. The duplicate export-kit path field has been removed.
- Shared Halo 3/Reach menus, including material, sky, collision and preparation controls.
- Prepare Reach assets for Halo 3 without switching import games.
- Swap multiple greybox cubes or placed objects for a chosen asset, using its original scale.
- Single-sided terrain export and improved handling of open collision surfaces.
- Diagnostic reports open at the top and identify the main Blender structure behind cluster errors.
See the [release notes](RELEASE-NOTES.md) for changes, validation and remaining limits. Save and restart Blender when updating; keep your cache and project records.

## What you can do

- Import fully textured static objects or entire campaign/multiplayer maps with their original position/material data.
- Import available terrain and static placements from campaign/DLC/multiplayer maps with preview textures; original collision and gameplay are not reconstructed.
- 3D Preview individual map assets in the asset index list by clicking on the object name to show a temporary geometry render at the 3d cursor which you can place
- Search and filter certain assets by map and category.
- Place, edit, move, duplicate, swap or delete geometry/materials in Blender.
- (Experimental)Choose a sky from installed Editing Kit maps, generate surface collision and optional draft lighting, then open the result in Sapien.
- (Experimental)Sapien Map Preparation allows the current blender scene to exported straight into Halo 3 Sapien

## Getting Started with HaloBridge

1. After Installing the [requirements and add-on](docs/INSTALLATION.md).
2. Open Blender, Press "N"(key) for sidebar menu on the right of viewport → Choose **HaloBridge**
3. [Import Game] Choose the game you want to extract assets from(example: "Halo 3").
4. Under [Folders and Setup] We can click **Detect folders** which finds folders automatically or manually type the folder paths: the "Halo 3 Editing Kit" is the file path for the Steam Halo Mod Tools Folder Location and the "Halo 3 .map Files" is where the Games Folders .map files are(steamapps\common\Halo The Master Chief Collection\halo3\maps) or wherever your .map file is you want to extract from, then **Check setup**. Its report checks the full workflow; see the requirements matrix if you only need Blender importing.
5. Enter a map filename such as `010_jungle.map` or Choose from the dropdown menu
6. For Importing individual assets click "Import Map Assets", For Entire map imports click "Import entire .map"
7. Scroll Down a little bit in the HaloBridge Menu to see "Asset List", you can toggle categories like Structures, Vegetation, Materials, Rocks, and Water or search for certain assets like "tree", "chief", "scorpion"
8. **Preview Mode** ON, allows you to select an asset from the list and temporarily render at the 3D cursor until you [Place Asset] which automatically turns **Preview Mode** off.
  
Build a small scene and follow the [first-map tutorial](docs/FIRST-MAP.md) to test it in Sapien.

## Experimental Sapien Map Preparation

**Sapien preparation is experimental and targets Halo 3 only.** Reach assets can be converted into static Halo 3 geometry; native Reach Sapien export is not implemented. It exports your current meshes and generates collision from their surfaces. Explicitly marked Halo 3 vehicle previews can instead use their original vehicle tags; see [Original Halo 3 vehicles](docs/FEATURES.md#original-halo-3-vehicles). It does not reconstruct original AI, scripts, animated doors, breakable objects, multiplayer rules, or baked lighting. A whole-map import is a visual starting point, not a complete recovered playable mission.

Some assets are missing or approximate, and invalid or oversized geometry can fail Halo's compiler. Preview materials are approximations; Halo 3 exports use installed shader tags, while Reach exports generate simplified Halo 3 shaders from preview textures. Large Project Reclaimer maps and multiplayer packaging need further testing. Start with a small level and keep your saved work.

## Guides

| Guide | Covers |
| --- | --- |
| [Install and update](docs/INSTALLATION.md) | Requirements, downloads, setup, storage and upgrades |
| [Blender-only importing](docs/IMPORTING.md) | Browse and place textured assets or import static map layouts without a Sapien build |
| [Create your first map](docs/FIRST-MAP.md) | Place assets, edit terrain, choose materials and test in Sapien |
| [Feature reference](docs/FEATURES.md) | Asset list, filters, preview, bulk actions, whole-map import and preparation |
| [Troubleshooting](docs/TROUBLESHOOTING.md) | Moving copies, missing textures, errors, slow imports and sky selection |
| [How HaloBridge works](docs/HOW-IT-WORKS.md) | Extraction, cache, geometry export and scenario preparation |
| [Limits and roadmap](docs/LIMITATIONS.md) | Supported scope and areas that need community testing |

## Bug Reports/Feedback/Suggestions

[Report a bug or request a feature](https://github.com/barnacleboii/HaloBridge-Blender-4.0-Asset-Map-Importer-Addon-BETA/issues/new/choose). Include your version, steps to reproduce, and sanitized error text.

Code and documentation contributions are welcome: see [CONTRIBUTING.md](CONTRIBUTING.md). The release includes both the installable add-on and matching source archive.

HaloBridge is an independent community project, not an official Microsoft, Bungie, or 343 Industries tool. No Halo game content or Editing Kit binaries are included. Supply them from your own installations. Code is licensed under [GPL-3.0](LICENSE); see [dependency credits](THIRD-PARTY.md). The code license does not grant rights to Halo assets.
