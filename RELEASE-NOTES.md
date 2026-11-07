# HaloBridge v0.9.1 — Public early release

Import Halo 3 and experimental Halo: Reach assets into Blender 4.0 and prepare custom geometry for Halo 3 Sapien.

## Downloads

- **HaloBridge-0.9.1.zip** is the Blender installer, including compiled helpers.
- **HaloBridge-0.9.1-source.zip** contains the matching source for developers.

Expand Assets below to download the installer. GitHub's automatic source archives omit compiled helpers. This release has its own v0.9.1 tag matching the published source commit.

## Requirements

| Component | Required version / purpose |
| --- | --- |
| [Windows](https://www.microsoft.com/windows/) | 64-bit Windows |
| [Blender 4.0](https://download.blender.org/release/Blender4.0/) | Blender **4.0**; this build does not support newer Blender versions |
| [Halo: The Master Chief Collection](https://store.steampowered.com/app/976730/Halo_The_Master_Chief_Collection/) | Install Halo 3 and/or Reach content and retain the complete maps folder, including shared resource maps |
| [Halo Asset Blender Development Toolset](https://github.com/General-101/Halo-Asset-Blender-Development-Toolset) | **v364 or v432**, installed and enabled; provides Halo Blender properties and ASS export. Current individual asset placement also checks it |
| [.NET Desktop Runtime](https://dotnet.microsoft.com/en-us/download/dotnet/10.0) | **10, Windows x64 Desktop Runtime**, for extraction; not just the base runtime |
| [.NET Framework](https://dotnet.microsoft.com/en-us/download/dotnet-framework/net48) | **4.8+**, for the Editing Kit/tag helper |
| [Halo 3 Mod Tools / H3EK](https://store.steampowered.com/app/1695791/Halo_3_Mod_Tools__MCC/) | Required for Halo 3 Sapien preparation and current individual Halo 3 BSP-instance placement; extract the supplied kit archives and retain the required tags |

**Only importing into Blender?** Indexing, model/material extraction and whole-map visual extraction read MCC maps. They do not inherently require extracted Editing Kit tags. **Individual Halo 3 BSP-instance placement is an exception:** it currently requests collision data from H3EK tags. The setup checker checks full-workflow prerequisites even for import-only users.

**Using Reach assets?** Reach extraction reads MCC Reach maps, not extracted HREK tags, although the current setup checker checks the Reach kit installation. Preparing Reach assets for Halo 3 uses **H3EK**, not Reach Sapien. Halo 3 remains the only implemented Sapien destination.

See the [detailed requirements and component explanations](https://github.com/BarnacleBoii/HaloBridge-Blender-4.0-Asset-Map-Importer-Addon-BETA/blob/main/docs/INSTALLATION.md#requirements).

## How to Install

1. Install Blender 4.0 and the required runtimes above.
2. Install and enable the **Halo Asset Blender Development Toolset v364 or v432** in Blender.
3. Download **HaloBridge-0.9.1.zip** from this release's Assets.
4. In Blender, open **Edit → Preferences → Add-ons → Install**, select the ZIP without extracting it, and enable **HaloBridge - Blender 4.0 Importing**.
5. In the 3D View, press **N** and open **HaloBridge**.
6. Choose **Import game**, then use **Folders and Setup → Detect folders** or enter the correct paths. The maps path is MCC's game maps folder; the Editing Kit path is the kit root containing its executables.
7. Run **Check setup** and read any issues in the context of your chosen workflow. Use **Choose .map file** to pick or type a filename.
8. Click **Index Map Assets** to browse individual assets, or **Import entire .map** for the available static layout. Use Material Preview to view textures.

For Sapien, configure H3EK with extracted tags under **Folders and Setup** while Halo 3 is selected. Preparation reuses that path even when browsing Reach. Save your scene and close Sapien before building.

**Updating:** save your work, finish or cancel jobs, remove/disable the old add-on in Preferences, restart Blender, and install the refreshed ZIP. Keep your cache, project manifests and backups. Restart Blender if the old interface remains visible.

[Full installation guide](https://github.com/BarnacleBoii/HaloBridge-Blender-4.0-Asset-Map-Importer-Addon-BETA/blob/main/docs/INSTALLATION.md) · [Blender-only importing](https://github.com/BarnacleBoii/HaloBridge-Blender-4.0-Asset-Map-Importer-Addon-BETA/blob/main/docs/IMPORTING.md) · [First Sapien test map](https://github.com/BarnacleBoii/HaloBridge-Blender-4.0-Asset-Map-Importer-Addon-BETA/blob/main/docs/FIRST-MAP.md)

## Changes in v0.9.1

- **Original collision first.** Automatic collision tries verified source collision geometry for eligible imported models and BSP instances. Edited or unmatched objects use the available box or surface fallback. Preparation reports list the collision route for each exported static object.
- **Large static models.** Oversized instances can export as several aligned Halo instances while staying one editable Blender object. This addresses the Reach Elite render-index overflow while retaining its visible triangles.
- **Paintable terrain.** Supported layered terrain starts with the original blended appearance. Numbered shader-layer buttons paint an overlay, and Paint original blend restores the source mixture. Texture resolution has 512, 1024, 2048 and 4096 options. Repeat controls start collapsed.
- **Original vehicle paint.** Editable colors can generate level-local vehicle/model/render-model copies for matched Halo 3 vehicles, with the original gameplay and physics references retained.
- **Snowbound materials.** Halo 3 previews now support default, detail blend, two-detail and two-detail-overlay albedo operations when their parameters are available. The missing second detail texture is extracted, restoring Snowbound's purple icy-metal layer.
- **Paired transparent faces.** Imported meshes whose transparent triangles all have opposite-facing mates get a local material with backface culling, reducing overlapping front/back rendering. This preserves the mesh faces.
- **Shader controls.** Materials and Shaders identifies the active object/material. Assign shader to active material explains its Sapien effect. The picker captures its chosen category, shows the matching count, and keeps manual path entry. Collision controls have their own section.
- **Texture-loading label.** The button is now Load Halo Shader Textures/Masks for Currently selected Material.
- **Neutral normal fallback.** The known unreadable default_vector placeholder can use a flat normal instead of interrupting extraction for that specific decode error.

## Using the new material controls

Select a mesh and its active material. Materials and Shaders shows the target. Scan existing shaders, choose a category, and use the filtered shader picker. Assign shader to active material sets the Sapien reference. Use Load Halo Shader Textures/Masks for Currently selected Material to refresh the Blender textures.

For painting, start from the original material and follow the [editable-material guide](https://github.com/BarnacleBoii/HaloBridge-Blender-4.0-Asset-Map-Importer-Addon-BETA/blob/main/docs/EDITABLE-MATERIALS.md). Existing painted copies keep their own stored images and mask interpretation. Pack images and save before updating.

## Known limits

Sapien preparation remains experimental and targets Halo 3. Original collision reuse requires a matching source and available tags. Edited or unmatched assets can use fallback collision. Large terrain and clusters still have compiler limits. Preview shaders approximate engine rendering, and this release does not establish universal map conversion or multiplayer compatibility.

[Feature index and detailed instructions](https://github.com/BarnacleBoii/HaloBridge-Blender-4.0-Asset-Map-Importer-Addon-BETA/blob/main/docs/FEATURES.md) · [Troubleshooting](https://github.com/BarnacleBoii/HaloBridge-Blender-4.0-Asset-Map-Importer-Addon-BETA/blob/main/docs/TROUBLESHOOTING.md) · [Report a problem](https://github.com/BarnacleBoii/HaloBridge-Blender-4.0-Asset-Map-Importer-Addon-BETA/issues/new/choose)
