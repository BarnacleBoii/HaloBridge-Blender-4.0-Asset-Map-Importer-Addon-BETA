![HaloBridge — Blender importer addon](docs/halobridgelogo.png)

# HaloBridge — Blender 4.0 Asset / Map Importer + Sapien Level Preparation(Beta)

HaloBridge is a Blender 4.0 Add-on created to streamline the Halo map modding/asset-management workflow, quickly import Halo:MCC fully textured static game assets and entire .maps fully textured into Blender, and an experimental option to prepare the current blender scene for a Halo 3 Sapien test level. Currently Supports Halo 3, Halo Reach(Experimental). more planned.

(Coded with Chat GPT 6 Astra, guided by user input)

**v0.9.1 · Beta preview · Windows x64 · Blender 4.0**

**Viewport scale:** HaloBridge uses a 100× working scale and converts it during export. For large scenes, adjust Clip Start and End to the area you are editing. An extreme near/far range can worsen depth flickering. See [viewport troubleshooting](docs/TROUBLESHOOTING.md#flickering-glass-or-large-map-viewport).

**[Releases and Downloads](https://github.com/BarnacleBoii/HaloBridge-Blender-4.0-Asset-Map-Importer-Addon-BETA/releases)** · **[Installation](docs/INSTALLATION.md)** · **[First map tutorial](docs/FIRST-MAP.md)** · **[Feature guide](docs/FEATURES.md)** · **[Troubleshooting](docs/TROUBLESHOOTING.md)**

## Releases and Downloads

Latest Version: v0.9.1

### [Open HaloBridge Releases →](https://github.com/BarnacleBoii/HaloBridge-Blender-4.0-Asset-Map-Importer-Addon-BETA/releases)

Open the latest release, expand **Assets**, and download **HaloBridge-<version>.zip** to install in Blender. You only need the installable add-on ZIP.

GitHub's automatic **Source code** ZIP/TAR downloads are for development and do not include the compiled helpers needed to run the add-on.

Follow the [installation guide](docs/INSTALLATION.md) for requirements and setup. **Draft releases are review builds and are not available as published downloads.**

## Requirements

**MCC maps provide the models and textures. Mod Tools provide editable tags and the Sapien compilation tools.** You do not need to prepare a Sapien level to use HaloBridge assets in Blender.

| Component | Required version / setup |

| --- | --- |

| [Windows](https://www.microsoft.com/windows/) | 64-bit Windows; other operating systems are not supported |

| [Blender 4.0](https://download.blender.org/release/Blender4.0/) | 4.0; tested with 4.0.0 |

| [Halo: The Master Chief Collection](https://store.steampowered.com/app/976730/Halo_The_Master_Chief_Collection/) | Fully Installed PC game, Including Halo 3 or Reach installed |

| [Halo 3 Mod Tools Editing Kit](https://store.steampowered.com/app/1695791/Halo_3_Mod_Tools__MCC/) | Tool, Sapien and extracted data/tag archives |

| [Halo Asset Blender Development Toolset](https://github.com/General-101/Halo-Asset-Blender-Development-Toolset) | **2.364.0 (v364) or 2.432.0 (v432)** installed and enabled; other exporter versions are rejected |

| [.NET Desktop Runtime](https://dotnet.microsoft.com/en-us/download/dotnet/10.0) | **10**, Windows **x64** Desktop Runtime, not only the base .NET runtime |

| [.NET Framework](https://dotnet.microsoft.com/en-us/download/dotnet-framework/net48) | **4.8 or newer** |

All users need **Windows x64, Blender 4.0, the supported Halo Blender toolset v364 or v432, and .NET 10 Desktop Runtime x64**. The tag helper uses **.NET Framework 4.8+**. Check setup currently checks full-workflow prerequisites even for import-only users; MCC alone does not support every current placement route. Halo 3 is the only implemented Sapien destination.

Start with the **[detailed installation guide and requirements matrix](docs/INSTALLATION.md#requirements)**, then choose **[Blender-only importing](docs/IMPORTING.md)** or **[First Sapien test map](docs/FIRST-MAP.md)**. No game maps, models, textures, tags or Editing Kit libraries are bundled. You do not need a standalone Reclaimer installation or a manually exported asset library.

## New in v0.9.1

- **Original collision first.** Automatic collision tries verified source collision geometry for eligible imported models and BSP instances. Edited or unmatched objects use the available box or surface fallback. Preparation reports list the collision route for each exported static object.
- **Large static models.** Oversized instances can export as several aligned Halo instances while staying one editable Blender object. This addresses the Reach Elite render-index overflow while retaining its visible triangles.
- **Paintable terrain.** Supported layered terrain starts with the original blended appearance. Numbered shader-layer buttons paint an overlay, and Paint original blend restores the source mixture. Texture resolution has 512, 1024, 2048 and 4096 options. Repeat controls start collapsed.
- **Original vehicle paint.** Editable colors can generate level-local vehicle/model/render-model copies for matched Halo 3 vehicles, with the original gameplay and physics references retained.
- **Snowbound materials.** Halo 3 previews now support default, detail blend, two-detail and two-detail-overlay albedo operations when their parameters are available. The missing second detail texture is extracted, restoring Snowbound's purple icy-metal layer.
- **Paired transparent faces.** Imported meshes whose transparent triangles all have opposite-facing mates get a local material with backface culling, reducing overlapping front/back rendering. This preserves the mesh faces.
- **Shader controls.** Materials and Shaders identifies the active object/material. Assign shader to active material explains its Sapien effect. The picker captures its chosen category, shows the matching count, and keeps manual path entry. Collision controls have their own section.
- **Texture-loading label.** The button is now Load Halo Shader Textures/Masks for Currently selected Material.
- **Neutral normal fallback.** The known unreadable default_vector placeholder can use a flat normal instead of interrupting extraction for that specific decode error.

See the [feature index](docs/FEATURES.md) for instructions and [release notes](RELEASE-NOTES.md) for installation and limitations.

## What you can do

- Import fully textured static objects or entire campaign/multiplayer maps with their original position/material data.

- Import available terrain and static placements from campaign/DLC/multiplayer maps with preview textures; gameplay requires separate authoring; eligible source collision can be reused during preparation.

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

6. For Importing individual assets click "Index Map Assets", For Entire map imports click "Import entire .map"

7. Scroll Down a little bit in the HaloBridge Menu to see "Indexed Asset List", you can toggle categories like Structures, Vegetation, Materials, Rocks, and Water or search for certain assets like "tree", "chief", "scorpion"

8. **Preview Mode** ON, allows you to select an asset from the list and temporarily render at the 3D cursor until you [Place Asset] which automatically turns **Preview Mode** off.

  

Build a small scene and follow the [first-map tutorial](docs/FIRST-MAP.md) to test it in Sapien.

## Experimental Sapien Map Preparation

**Sapien preparation is experimental and targets Halo 3 only.** Reach assets can be converted into static Halo 3 geometry; native Reach Sapien export is not implemented. It exports current meshes and tries verified original collision for eligible assets, with box or surface fallback for edited or unmatched meshes. Explicitly marked Halo 3 vehicle previews can instead use their original vehicle tags; see [Original Halo 3 vehicles](docs/FEATURES.md#collision-and-original-vehicles). It does not reconstruct original AI, scripts, animated doors, breakable objects, multiplayer rules, or baked lighting. A whole-map import is a visual starting point, not a complete recovered playable mission.

 Invalid or oversized geometry can fail Halo's compiler. Preview materials are approximations; Halo 3 exports use installed shader tags, while Reach exports generate simplified Halo 3 shaders from preview textures. Large Project Reclaimer maps and multiplayer packaging need further testing. Start with a small level and keep your saved work.

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

