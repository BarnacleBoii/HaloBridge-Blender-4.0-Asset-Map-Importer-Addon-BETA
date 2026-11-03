![HaloBridge](https://raw.githubusercontent.com/BarnacleBoii/HaloBridge-Blender-4.0-Asset-Map-Importer-Addon-BETA/main/docs/halobridgelogo.png)

# HaloBridge v0.8.5 — Beta

## Download and update

Download **HaloBridge-0.8.5.zip** to install the Blender addon. **HaloBridge-0.8.5-source.zip** is for developers. Save your scene, finish/cancel active jobs, remove the old addon through Blender Preferences, restart Blender, install the new ZIP, and enable HaloBridge. Keep your cache and project records.

## Changes

- **Skip objects with export problems:** optional partial preparation lists each excluded object and reason before confirmation. Objects stay in Blender. Compiler failures still stop preparation; at least one valid mesh is required.
- **Material validation:** uses materials assigned to evaluated faces. Unused material slots no longer prevent export. Highlighting an Asset List material still does not assign it.
- **Preparation warnings:** Continue/Cancel remain visible above Prepare. Warnings are no longer saved as failed builds, and underlying error lists are no longer overwritten by a generic confirmation error.
- **Existing shader picker:** shaders are grouped by level/shared category and selected through a searchable popup. Use Scan existing shaders first. Manual path entry remains available.
- **Sky picker:** searchable selection, visible selected scenario path, and selection stored independently of the scanned list. Use Find map skies first.
- **Level Imported:** normalized map-name matching and retained dropdown entries improve selection stability. The exact reported disappearance was not reproduced locally.
- **Static model:** replaces the confusing Source check label.
- **Export target:** Halo 3 supported; Reach Sapien is explicitly unavailable. Reach assets can still be converted to static Halo 3 geometry.

## Requirements and guides

Windows x64, Blender 4.0, .NET 10 Desktop Runtime, and your own MCC map files. The complete Halo 3 workflow requires H3EK with extracted tags, .NET Framework 4.8+, and Halo Asset Blender Development Toolset 2.364.0.

[Installation](https://github.com/BarnacleBoii/HaloBridge-Blender-4.0-Asset-Map-Importer-Addon-BETA/blob/main/docs/INSTALLATION.md) · [Feature guide](https://github.com/BarnacleBoii/HaloBridge-Blender-4.0-Asset-Map-Importer-Addon-BETA/blob/main/docs/FEATURES.md)

## Verification and limits

23 unit tests and Blender checks for partial export, source-scene preservation, shader assignment, filters, warning handling, Reach conversion and edited geometry passed. A real Halo 3 asset exported to ASS with its shader references intact while an invalid plane was omitted. The installed H3EK shader catalogue and a real sky scenario were checked. This is not a full playtest of testleveldudebro or all maps, nor visual validation of every popup on every display.

Sapien preparation remains experimental static geometry with generated collision. Original gameplay, animation, AI, scripts and multiplayer behavior are not recreated. Some sky/object placement differences and map extraction omissions remain unresolved. Project Reclaimer multiplayer packaging is not verified. No Halo game content is bundled.
