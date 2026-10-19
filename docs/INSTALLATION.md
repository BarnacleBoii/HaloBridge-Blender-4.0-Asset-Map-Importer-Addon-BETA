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

You need existing H3EK shader tags for assets you export. The default sky uses High Ground (`deadlock`); the starter shell uses the jungle map. See [Microsoft's H3EK overview](https://learn.microsoft.com/en-us/halo-master-chief-collection/h3/quickstart/quickstartoverview) for the game toolchain. HaloBridge does not install these dependencies for you.

## Download

Open the [v0.8.4 release](https://github.com/barnacleboii/HaloBridge-Blender-4.0-Asset-Map-Importer-Addon-BETA/releases/tag/v0.8.4). Under **Assets**, choose **HaloBridge-0.8.4.zip**.

| Download | Purpose |
| --- | --- |
| `HaloBridge-0.8.4.zip` | Install this in Blender; includes the compiled helpers |
| `HaloBridge-0.8.4-source.zip` | Matching source and build instructions for contributors |
| `SHA256SUMS.txt` | File checksums for these two archives |
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
