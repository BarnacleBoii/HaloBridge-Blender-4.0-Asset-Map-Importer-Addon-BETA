# Installation and updates

[Home](../README.md) · [First map](FIRST-MAP.md) · [Troubleshooting](TROUBLESHOOTING.md)

## Requirements

| Component | Required version / setup |
| --- | --- |
| Windows | 64-bit Windows; other operating systems are not supported |
| Blender | 4.0; tested with 4.0.0 |
| MCC Halo 3 | Locally installed PC game, including the complete `halo3/maps` directory and resource maps |
| Halo 3 Editing Kit | Tool, Sapien and extracted tag archives; test the kit independently first |
| [Halo Asset Blender Development Toolset](https://github.com/General-101/Halo-Asset-Blender-Development-Toolset) | **2.364.0 (v364)** installed and enabled; other exporter versions are rejected |
| [.NET Desktop Runtime](https://dotnet.microsoft.com/en-us/download/dotnet/10.0) | **10**, Windows **x64** Desktop Runtime, not only the base .NET runtime |
| [.NET Framework](https://dotnet.microsoft.com/en-us/download/dotnet-framework/net48) | **4.8 or newer** |

See [Microsoft's H3EK overview](https://learn.microsoft.com/en-us/halo-master-chief-collection/h3/quickstart/quickstartoverview) for the game toolchain. HaloBridge does not install these dependencies for you.

## MCC maps versus Mod Tools

**These are separate installations.** “Supply your own MCC maps” means install the relevant game content in **Halo: The Master Chief Collection for PC**. HaloBridge reads its compiled `.map` files to extract models and textures. Installing the Mod Tools alone does not supply that MCC game folder.

| Workflow | What you need |
| --- | --- |
| Index or import a whole Halo 3 map's static layout | Installed MCC Halo 3, including `halo3/maps` and its resource maps |
| Use the full Halo 3 asset-placement workflow and prepare a Halo 3 Sapien level | MCC Halo 3 **plus Halo 3 Mod Tools - MCC (H3EK), with its tag archives extracted**. Individual BSP-instance extraction also reads the original H3EK collision tags. |
| Import Reach assets or a Reach map's static layout | Installed MCC Halo: Reach, including `haloreach/maps` and its resource maps. The current **Check setup** also expects **Halo: Reach Mod Tools - MCC (HREK)**, although extraction itself reads MCC maps, not HREK tags. |
| Use Reach assets in a Halo 3 Sapien level | MCC Reach assets **plus H3EK with extracted Halo 3 tags** and the Halo exporter. Switch **Import game** back to **Halo 3** before preparation. Reach Sapien is not used; extracting HREK tags is not required by this conversion. |

The current Halo 3 **Check setup** checks the full Editing Kit/export setup even if you only intend to import. A missing-kit warning does not mean the map files should be placed inside the Editing Kit.

### Install the Editing Kit for Halo 3 preparation

1. In Steam Library, enable the **Tools** filter and install **Halo 3 Mod Tools - MCC**. For the current Reach setup profile, also install **Halo: Reach Mod Tools - MCC**.
2. Open the H3EK installation folder and extract the supplied tag/data archives, preserving their folder structure. The resulting `tags` and `data` folders belong directly inside H3EK, alongside `tool.exe` and `sapien.exe`; avoid an extra nested `H3EK/H3EK` folder. See [Microsoft's Editing Kit instructions](https://learn.microsoft.com/en-us/halo-master-chief-collection/h3/quickstart/quickstartoverview).
3. Keep the original shader and scenario tags needed by your chosen assets and sky. For the default starter sky, confirm `tags/levels/multi/deadlock/deadlock.scenario` exists.
4. In HaloBridge, set **Halo 3 Editing Kit** to the H3EK root and **Halo 3 .map Files** to MCC's `halo3/maps` folder. For Reach importing, use the HREK root and MCC's `haloreach/maps` folder in that game's profile.
5. Run **Check setup**. HaloBridge does not download the games, install Mod Tools, or extract Editing Kit archives for you.

Steam's tool-installation options are described in the [official MCC Creator Hub](https://www.halowaypoint.com/news/halo-2-and-halo-3-mod-tools-release); [Halo Support](https://support.halowaypoint.com/hc/en-us/articles/8955559396372-Halo-The-Master-Chief-Collection-MCC-Update-August-2022) also identifies the Reach Tools entry.

## Download

Open the [v0.8.4 release](https://github.com/barnacleboii/HaloBridge-Blender-4.0-Asset-Map-Importer-Addon-BETA/releases/tag/v0.8.4). Under **Assets**, choose **HaloBridge-0.8.4.zip**.

| Download | Purpose |
| --- | --- |
| `HaloBridge-0.8.4.zip` | Install this in Blender; includes the compiled helpers |
| `HaloBridge-0.8.4-source.zip` | Matching source and build instructions for contributors |
| GitHub's automatic Source code ZIP / TAR | Repository snapshot; build the helpers before using it |

## Install in Blender

1. Save your work. In Blender, open **Edit → Preferences → Add-ons → Install**.
2. Select `HaloBridge-0.8.4.zip` without unzipping it.
3. Enable **HaloBridge - Blender 4.0 Importing** and the required Halo exporter.
4. In a 3D View, press **N** and open **HaloBridge**.
5. Choose **Detect folders**, inspect the two game folder paths, and choose **Check setup**. If detection misses an installation, choose its folders manually.
6. Resolve the reported missing requirements before importing or preparing a level.

## Update an existing installation

Save the blend file and close any active HaloBridge job. Disable and remove the old add-on in Blender Preferences, restart Blender, then install the new ZIP. Restart again if Blender still has old modules loaded. Do not remove your project storage to update the add-on.

## Where your work lives

The default storage is `Documents/HaloBridge` in your user folder. **Advanced storage** changes the chosen location; it does not move files. Existing blend files retain their saved storage path.

Keep `projects` ownership manifests and `backups`. These are needed for safe repeat preparation, not just temporary previews. Save your `.blend` separately. Moving a project between computers requires its dependencies and local paths to be resolved; automatic project migration is not implemented.

Prepared levels are written inside your Editing Kit at `tags/levels/multi/<level>/<level>.scenario`, with source geometry under `data/levels/multi/<level>/`. Use a unique output name for each project.
