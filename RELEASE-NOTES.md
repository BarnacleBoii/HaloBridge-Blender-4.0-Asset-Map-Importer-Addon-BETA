# HaloBridge v0.9 — Beta

Import Halo 3 and experimental Halo: Reach assets and static map layouts into **Blender 4.0**, then optionally prepare your current scene for **Halo 3 Sapien**.

## Downloads

Expand **Assets** below and download **HaloBridge-0.9.0.zip** to install the add-on.

- **HaloBridge-0.9.0.zip** — Blender installer, including compiled HaloBridge helpers.
- **HaloBridge-0.9.0-source.zip** — matching source for developers; not the installer.

Use the attached source ZIP for the refreshed v0.9 build. GitHub's automatic **Source code** archives refer to the original tag and do not include compiled helpers.

## Requirements

| Component | Required version / purpose |
| --- | --- |
| [Windows](https://www.microsoft.com/windows/) | 64-bit Windows |
| [Blender 4.0](https://download.blender.org/release/Blender4.0/) | Blender **4.0**; this build does not support newer Blender versions |
| [Halo: The Master Chief Collection](https://store.steampowered.com/app/976730/Halo_The_Master_Chief_Collection/) | Install Halo 3 and/or Reach content and retain the complete maps folder, including shared resource maps |
| [Halo Asset Blender Development Toolset](https://github.com/General-101/Halo-Asset-Blender-Development-Toolset) | **2.364.0 / v364**, installed and enabled; provides Halo Blender properties and ASS export. Current individual asset placement also checks it |
| [.NET Desktop Runtime](https://dotnet.microsoft.com/en-us/download/dotnet/10.0) | **10, Windows x64 Desktop Runtime**, for extraction; not just the base runtime |
| [.NET Framework](https://dotnet.microsoft.com/en-us/download/dotnet-framework/net48) | **4.8+**, for the Editing Kit/tag helper |
| [Halo 3 Mod Tools / H3EK](https://store.steampowered.com/app/1695791/Halo_3_Mod_Tools__MCC/) | Required for Halo 3 Sapien preparation and current individual Halo 3 BSP-instance placement; extract the supplied kit archives and retain the required tags |

**Only importing into Blender?** Indexing, model/material extraction and whole-map visual extraction read MCC maps. They do not inherently require extracted Editing Kit tags. **Individual Halo 3 BSP-instance placement is an exception:** it currently requests collision data from H3EK tags. The setup checker checks full-workflow prerequisites even for import-only users.

**Using Reach assets?** Reach extraction reads MCC Reach maps, not extracted HREK tags, although the current setup checker checks the Reach kit installation. Preparing Reach assets for Halo 3 uses **H3EK**, not Reach Sapien. Halo 3 remains the only implemented Sapien destination.

See the [detailed requirements and component explanations](https://github.com/BarnacleBoii/HaloBridge-Blender-4.0-Asset-Map-Importer-Addon-BETA/blob/main/docs/INSTALLATION.md#requirements).

## How to Install

1. Install Blender 4.0 and the required runtimes above.
2. Install and enable the **Halo Asset Blender Development Toolset v364 / 2.364.0** in Blender.
3. Download **HaloBridge-0.9.0.zip** from this release's Assets.
4. In Blender, open **Edit → Preferences → Add-ons → Install**, select the ZIP without extracting it, and enable **HaloBridge - Blender 4.0 Importing**.
5. In the 3D View, press **N** and open **HaloBridge**.
6. Choose **Import game**, then use **Folders and Setup → Detect folders** or enter the correct paths. The maps path is MCC's game maps folder; the Editing Kit path is the kit root containing its executables.
7. Run **Check setup** and read any issues in the context of your chosen workflow. Use **Choose .map file** to pick or type a filename.
8. Click **Import Map Assets** to browse individual assets, or **Import entire .map** for the available static layout. Use Material Preview to view textures.

For Sapien, configure H3EK with extracted tags under **Folders and Setup** while Halo 3 is selected. Preparation reuses that path even when browsing Reach. Save your scene and close Sapien before building.

**Updating:** save your work, finish or cancel jobs, remove/disable the old add-on in Preferences, restart Blender, and install the refreshed ZIP. Keep your cache, project manifests and backups. Restart Blender if the old interface remains visible.

[Full installation guide](https://github.com/BarnacleBoii/HaloBridge-Blender-4.0-Asset-Map-Importer-Addon-BETA/blob/main/docs/INSTALLATION.md) · [Blender-only importing](https://github.com/BarnacleBoii/HaloBridge-Blender-4.0-Asset-Map-Importer-Addon-BETA/blob/main/docs/IMPORTING.md) · [First Sapien test map](https://github.com/BarnacleBoii/HaloBridge-Blender-4.0-Asset-Map-Importer-Addon-BETA/blob/main/docs/FIRST-MAP.md)

## Changes in v0.9

- **Shared Halo 3/Reach menus:** material, collision, sky, preparation and activity controls are available without switching back to Halo 3. Output level and sky remain selected when changing import games.
- **Map picker:** searchable **Choose .map file** dropdown alongside manual filename entry.
- **Greybox swapping:** replace multiple selected objects, including ordinary cubes, with the highlighted asset. Keeps position, rotation and collections; uses the asset's original import scale.
- **Preview feedback:** green ON / red OFF status icons and highlighted Place Asset(s) while previewing, without flashing.
- **Warnings near preparation:** a second message panel above Map Preparation Status mirrors the original top panel, including ACTION REQUIRED and relevant buttons.
- **Single-sided export:** no blanket doubling of opaque surfaces. Explicit two-sided settings and double-sided alpha previews remain supported; open single-sided surfaces use appropriate Halo flags.
- **Clearer diagnostics:** reports open at line 1; structure failures identify the main Blender source object rather than leaving only an unexplained cluster number.
- **Simpler setup:** one saved Halo 3 Editing Kit path; no duplicate export path field. Asset List is left-aligned above categories, and the old output-name example is removed.
- **Updated guides:** workflow-specific requirements, detailed installation, Blender-only importing, Features, First Map and troubleshooting.
- **Future game framework:** shared capability definitions are in place; Halo CE, Halo 2, ODST and Halo 4 are not enabled yet.

## Important Notes

Whole-map importing is a **static visual layout**, not a recovered playable mission. Ordinary exported meshes use generated surface collision. Verified Halo 3 vehicles can instead use their original tags. Reach gameplay, animation and original collision tags are not converted into equivalent Halo 3 game objects.

Terrain complexity and Halo compiler limits still apply. HaloBridge does not automatically simplify or split your geometry. Test lighting is for quick iteration; successful preparation is not a finished multiplayer map or Project Reclaimer package.

No game maps, models, textures or Editing Kit libraries are included. Supply your own installations.

[Feature guide](https://github.com/BarnacleBoii/HaloBridge-Blender-4.0-Asset-Map-Importer-Addon-BETA/blob/main/docs/FEATURES.md) · [Troubleshooting](https://github.com/BarnacleBoii/HaloBridge-Blender-4.0-Asset-Map-Importer-Addon-BETA/blob/main/docs/TROUBLESHOOTING.md) · [Known limitations](https://github.com/BarnacleBoii/HaloBridge-Blender-4.0-Asset-Map-Importer-Addon-BETA/blob/main/docs/LIMITATIONS.md) · [Report an issue](https://github.com/BarnacleBoii/HaloBridge-Blender-4.0-Asset-Map-Importer-Addon-BETA/issues/new/choose)
