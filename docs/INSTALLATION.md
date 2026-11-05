# HaloBridge v0.9 — installation and updates

[Home](../README.md) · [Installation](INSTALLATION.md) · [First map](FIRST-MAP.md) · [Features](FEATURES.md) · [Troubleshooting](TROUBLESHOOTING.md)

## Requirements

**Choose your workflow first.** MCC supplies compiled map geometry and textures. Mod Tools supply editable tags and programs such as Tool and Sapien. Their folders are different; one installation does not replace the other.

| What you want to do | MCC content | Editing Kit / extracted tags |
| --- | --- | --- |
| List assets with Import Map Assets | Selected game's complete maps folder | Indexing itself does not use Editing Kit tags |
| Import models, materials and textures into Blender | Selected game's maps plus shared resource maps | Extraction reads MCC data; see the Halo 3 BSP-instance exception below |
| Place an individual Halo 3 BSP instance | Halo 3 maps/resources | **H3EK with the matching extracted BSP tags**: current placement also requests original collision data |
| Import entire .map as a static visual layout | Selected game's maps/resources | Layout extraction reads MCC maps, not HREK/H3EK tags; this is not playable scenario reconstruction |
| Prepare a scene for Halo 3 Sapien | Maps for the Halo assets you imported | **H3EK, extracted tags and its tools**; shader, sky and vehicle dependencies must exist |
| Import Reach assets for Blender | Reach maps/resources | Extracted HREK tags are not required by the extractor; the current setup checker nevertheless checks HREK installation |
| Prepare Reach assets for Halo 3 Sapien | Reach maps/resources | **H3EK with extracted Halo 3 tags** for the destination; not Reach Sapien |

**MCC alone is not enough for every HaloBridge operation.** For the complete Halo 3 browser/placement/preparation workflow, install H3EK and extract its supplied archives. For Blender-only use, the supported extraction routes above do not inherently need game tags, but this release is not a separately validated minimal-dependency installer.

### Software dependencies

| Component | Version and purpose |
| --- | --- |
| [Windows](https://www.microsoft.com/windows/) | x64; other operating systems unsupported |
| [Blender 4.0](https://download.blender.org/release/Blender4.0/) | **4.0**, tested with 4.0.0; newer Blender releases are not supported by this build |
| [HaloBridge v0.9](https://github.com/BarnacleBoii/HaloBridge-Blender-4.0-Asset-Map-Importer-Addon-BETA/releases/tag/v0.9) | Install **HaloBridge-0.9.0.zip**, not a source archive |
| [Halo Asset Blender Development Toolset](https://github.com/General-101/Halo-Asset-Blender-Development-Toolset) | **2.364.0 (v364)** installed and enabled; HaloBridge checks this version during object placement and export, including Reach objects |
| [.NET Desktop Runtime](https://dotnet.microsoft.com/en-us/download/dotnet/10.0) | **10, Windows x64**, for the bundled extraction helper; the base runtime alone is not the Desktop Runtime |
| [.NET Framework](https://dotnet.microsoft.com/en-us/download/dotnet-framework/net48) | **4.8 or newer**, for the Editing Kit/tag helper; checked by Check setup |
| [MCC game content](https://store.steampowered.com/app/976730/Halo_The_Master_Chief_Collection/) | Install the game you are importing, Halo 3 and/or Reach; all MCC games need not be installed |

Dependency downloads: [Blender 4.0 archives](https://download.blender.org/release/Blender4.0/), [Halo Blender toolset](https://github.com/General-101/Halo-Asset-Blender-Development-Toolset), [.NET 10 Desktop Runtime](https://dotnet.microsoft.com/en-us/download/dotnet/10.0), [.NET Framework 4.8](https://dotnet.microsoft.com/en-us/download/dotnet-framework/net48). Use the toolset's v364 release, not an arbitrary latest version.

### Why the Halo Asset Blender Development Toolset is required

This is a **separate Blender add-on**, not the Halo Mod Tools installed through Steam. Install and enable **both HaloBridge and the Halo Asset Blender Development Toolset** in Blender Preferences.

HaloBridge provides the asset browser, map extraction, previews, placement tools and preparation workflow. The Halo Blender toolset supplies the Halo-specific Blender properties and the **ASS exporter** that HaloBridge calls when preparing level geometry. ASS is an intermediate geometry file consumed by Halo's compiler; Sapien does not load a `.blend` directly. The toolset also supplies the JMS reader used by HaloBridge's optional legacy import route.

**Why install it if I only want assets in Blender?** In v0.9, HaloBridge's individual-object placement path checks and enables this toolset before creating an asset, including Reach assets. Preparation also uses its material flags and exporter. The MCC extraction helper itself does not use the toolset to read textures or list map assets. This is a dependency of the current HaloBridge integration, not a claim that all MCC extraction inherently needs a Blender exporter. Install it for the supported browsing/placement workflow even if you do not plan to use Sapien.

**Why exactly v364 / 2.364.0?** That is the version the integration was verified against, including its ASS export options and coordinate conversion. HaloBridge explicitly rejects other versions; a newer toolset release is not automatically compatible. You normally use HaloBridge's buttons rather than manually exporting an ASS file. The toolset does not supply game maps, textures, tags, Tool or Sapien, and does not replace MCC or H3EK.

### What the other components provide

| Component | Why HaloBridge needs it |
| --- | --- |
| Blender 4.0 | Hosts the add-on, displays imported meshes/materials and lets you edit the scene. The add-on and supported exporter are tested against this Blender API version. |
| MCC Halo 3 / Reach content | Supplies the actual source geometry, bitmaps and placement information in compiled maps. Shared resource maps contain dependencies that may not be inside the level map itself. |
| H3EK / Halo 3 Mod Tools | Supplies Tool to compile geometry, Sapien to inspect/edit the generated scenario, ManagedBlam for tag access, and editable tags used for shaders, skies, original vehicles and the current individual BSP-instance collision lookup. Required for Halo 3 preparation; see the workflow matrix for import-only exceptions. |
| HREK / Reach Mod Tools | The current Reach setup checker checks this installation. Reach visual extraction reads MCC maps and does not consume extracted HREK tags. HREK is not the destination for HaloBridge's current Sapien preparation. |
| .NET 10 Desktop Runtime x64 | Runs HaloBridge's bundled extraction helper. Choose **Desktop Runtime**, not just the base runtime, and **x64**, not x86. Users do not need the SDK unless building the helper from source. |
| .NET Framework 4.8+ | Runs the separate tag/scenario helper used with the Editing Kit. This is a different runtime family from .NET 10; installing one does not replace the other. It is often already present on Windows. |
| HaloBridge installer ZIP | Supplies the Blender interface and compiled HaloBridge helpers. The source ZIP does not contain the built helpers and is not the normal user installer. |

## 1. Install the game content

1. Install Halo: The Master Chief Collection and the Halo 3 and/or Reach content you want to import. Make sure the relevant content is actually downloaded, not just listed as owned.
2. Find MCC's installation folder, for example through Steam's Manage → Browse local files.
3. Keep the complete selected game's maps directory. Halo 3 normally uses `halo3/maps`; Reach uses `haloreach/maps` beneath the MCC installation.
4. Do not move one level map away from its shared resource maps. Missing resource maps can cause missing textures or extraction failures.

You do not need a standalone Reclaimer installation, Osoyoos, or a manually exported AMF/RMF library for the normal workflow. The release includes HaloBridge's extraction helper and its redistributable dependencies; it does not contain Halo content.

## 2. Install Blender dependencies and HaloBridge

1. Install Windows x64 Blender 4.0 and the runtimes listed above. Restart Blender after installing runtimes.
2. Download the **v364 / 2.364.0** Halo Blender toolset from its project releases. Follow its release installation instructions, enable it in Blender, and verify its version in Preferences.
3. Open the [HaloBridge v0.9 release](https://github.com/BarnacleBoii/HaloBridge-Blender-4.0-Asset-Map-Importer-Addon-BETA/releases/tag/v0.9). Expand **Assets** and download **HaloBridge-0.9.0.zip**.
4. In Blender, save your work, then open **Edit → Preferences → Add-ons → Install**. Select that ZIP without unzipping it.
5. Enable **HaloBridge - Blender 4.0 Importing**. Keep the Halo Blender toolset enabled too. Save Preferences if automatic preference saving is disabled.
6. Move the mouse over a 3D View, press **N**, and choose the **HaloBridge** sidebar tab. If it is missing, confirm you are in a 3D View and that the add-on enabled without an error.

The attached **HaloBridge-0.9.0-source.zip** is for developers, not installation. GitHub's automatic Source code ZIP/TAR files also lack compiled helpers. Refreshed v0.9 assets may be newer than its original tag: use the attached source ZIP for the source matching the current installer.

## 3. Configure Blender-only importing

1. Select **Import game**: Halo 3 or **(Experimental) Halo Reach**.
2. Under **Folders and Setup**, click **Detect folders**. It fills empty fields; inspect the results, especially if you use multiple Steam libraries. Correct incorrect paths manually.
3. Set **Halo 3 .map Files** or **Halo: Reach .map Files** to the directory containing that game's maps, not its parent MCC directory and not the Editing Kit `tags` folder.
4. If using Editing Kit features, set its field to the tool installation root containing `tool.exe`, not the `tags` or `data` subdirectory.
5. Choose **Check setup** and read the full report. **This is currently a full-workflow checker, not an import-only readiness test.** It checks Editing Kit executables, ManagedBlam, runtimes, and (for Halo 3) a default scenario even when you only intend to import. Missing kit/tag messages can be unrelated to map indexing or visual layout extraction. Do not ignore runtime, map-resource, exporter or extraction errors.
6. Under **Choose .map file**, use the arrow to search available filenames or type one, including `.map`.
7. Choose **Import Map Assets** for a browser, or **Import entire .map** for a static layout. See the [Blender-only guide](IMPORTING.md).

Switching import games remembers separate folders and catalogues. Save your `.blend` to retain those profiles. It does not remove scene objects. For an individual Halo 3 BSP instance that fails with a collision/tag-helper error, complete the H3EK setup below; MCC-only placement is not supported for that route yet.

## 4. Add Halo 3 Sapien preparation

1. In Steam Library, enable the **Tools** filter and install **Halo 3 Mod Tools - MCC**. MCC and this tool are separate installs. **Halo: Reach Mod Tools - MCC** is the separate Reach kit; it is not a substitute for H3EK when exporting to Halo 3.
2. Open H3EK's installation folder. Extract the supplied tag/source archives as directed by the kit, preserving folder structure. `tags` and `data` belong directly under the kit root, alongside its executables; avoid accidentally nesting another kit folder inside it.
3. Verify `tool.exe`, `sapien.exe`, `bin/ManagedBlam.dll`, and the extracted `tags` folder exist. Keep the original shader/bitmap/BSP/scenario dependencies used by your assets and selected sky. The current default sky/setup check expects `tags/levels/multi/deadlock/deadlock.scenario`.
4. With **Import game → Halo 3**, set the H3EK root once under **Folders and Setup**. Run **Check setup**. Follow the kit's own setup instructions if its tools cannot launch independently.
5. You can return to Reach to browse Reach assets. **Export to Sapien → Halo 3** reuses the saved Halo 3 folders. There is no second export-kit path to enter.
6. Follow [First Map](FIRST-MAP.md). Save your blend, close Sapien, prepare a small scene, then open the generated `.scenario`. The preparation button does not produce a finished multiplayer `.map` or Project Reclaimer package.

See [Microsoft's H3EK toolchain and folder overview](https://learn.microsoft.com/en-us/halo-master-chief-collection/h3/quickstart/quickstartoverview). HaloBridge does not install games, extract kit archives, or supply game licenses/content.

## Update without losing your work

1. Save your `.blend`. Finish or cancel active jobs. Close Sapien before another build.
2. Disable/remove the old HaloBridge add-on through Blender Preferences, then restart Blender so old Python modules are unloaded.
3. Install the refreshed installer ZIP, enable HaloBridge, and restart Blender if an older interface remains visible.
4. Reopen your scene, verify saved folder paths, and check setup. Do not delete the cache or ownership manifests as an update step.

## Storage and generated files

Default storage is `Documents/HaloBridge`; Reach normally uses its `reach` subfolder. **Advanced storage** changes the selected location but does not move files. Keep `projects`, ownership manifests and backups: they support repeat exports and rollback. Save your blend separately. Textures may reference cached files, so retain the cache or deliberately pack/relink images when moving a Blender project.

Prepared tags appear under `H3EK/tags/levels/multi/<level>/<level>.scenario`, and generated source geometry under `H3EK/data/levels/multi/<level>/`. Use distinct output names for distinct projects. Local map/cache paths and project records are not automatically portable to another computer. Game assets and caches must not be uploaded to this GitHub repository.
