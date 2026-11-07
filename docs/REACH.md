# HaloBridge v0.9.1 — Reach importing and Halo 3 conversion

[Home](../README.md) | [Features](FEATURES.md)

## Setup

Install MCC's **Halo: Reach game content** for the `.map` files. **Halo: Reach Mod Tools - MCC (HREK)** is a separate Steam Tools installation expected by the current setup checker. Reach extraction reads MCC maps and does not require extracted HREK tags. To prepare these assets for Halo 3 Sapien, install **H3EK and extract its Halo 3 tags**. See [requirements by workflow](INSTALLATION.md#requirements).

1. Select **(Experimental) Halo Reach** above Folders and Setup.
2. Choose **Detect folders**. Verify **Reach Editing Kit** points to HREK and **Reach maps** points to MCC's haloreach/maps directory.
3. Choose **Check setup**. The extraction helper requires .NET 10 Desktop Runtime x64. Install the supported Halo Blender toolset too; HaloBridge checks it for asset placement and scene export.
4. Enter a filename such as **70_boneyard.map** and choose **Index Map Assets**.
5. Use search, filters, Preview Mode and Place asset(s), or **Import entire .map** for available terrain and static placements in original positions.

## Profiles and scope

Halo 3 storage is preserved. Reach defaults to Documents/HaloBridge/reach. Each game remembers its folder choices and map filename, and loads its own catalogue and cached files. Save your blend file to retain these profiles. Changing the selector removes temporary previews but does not delete placed objects.

## Use Reach assets in Halo 3 Sapien

1. Keep your imported Reach objects in the current Blender scene and edit/place them normally.
2. Keep **Import game** on Reach and choose **Halo 3** under **Export to Sapien**.
3. Configure **H3EK** once under **Folders and Setup** with Halo 3 selected; preparation reuses that saved path while importing Reach, enter your output level name, and choose a Halo 3 sky.
4. Click **Prepare current scene for sapien**, review the static-geometry warning, and continue.

The export uses current meshes and transforms, including edits and modifiers. It tries verified original collision geometry, falls back to supported static collision, and builds Halo 3 bitmap and shader tags in the output level folder. Diffuse textures, normal textures, UV tiling and cutout alpha are supported. Existing Reach imports are detected from their object metadata; reimporting is unnecessary. An explicitly assigned Halo 3 shader overrides conversion.

This is a static map-building workflow. Reach vehicles, weapons, machines and characters become static shapes, not functional game objects. Layered terrain shaders, water, glow, transparency blending and other complex effects are approximated from the Blender preview. Transparency becomes alpha-tested cutout. Differing texture tilings are resampled relative to the base texture; this can reduce detail and is approximate outside a single tile. Original Reach scripts, animation and gameplay are not ported. Reach skies are not converted into Halo 3 sky tags; choose a Halo 3 sky.

Converted bitmaps currently use uncompressed formats for predictable quality. Large scenes can require substantial disk and runtime memory. Failed compilation restores the previous generated level. Missing textures or unsupported edited node graphs produce a material-specific diagnostic. Halo 3's geometry limits still apply. This version targets Halo 3 Sapien only.

Reach BSP indexing resolves instance sections from resource geometry and may take longer than Halo 3 indexing. Index warnings appear in Blender's **HaloBridge index report** text block. Whole-map omissions appear in the import report. A successful import does not guarantee all BSPs or model variants decoded.

## Verification in 0.7.0

Boneyard indexed 838 instance assets, 851 materials, 320 models and 28 scenery entries. Full extraction produced 8,474 placements from 2 of 3 BSPs; the hidden BSP failed decoding and was reported. Real instance/scenery/material extraction and repeat-cache reuse passed. Blender checks covered shared meshes, previews and a 21-placement sample spanning all seven map groups with original transforms. This is not a full-map runtime or Reach Sapien test.

## Earlier conversion verification (0.8.0; still a limited fixture)

A real Boneyard instance and Halo 3 test ground compiled into a separate Halo 3 scenario. Repeat preparation with a cutout variant passed. Readback verified three instance definitions and 84 generated collision surfaces; shader tags referenced converted base, normal and alpha bitmaps and the cutout template. Automated Blender tests verified source UV/material preservation, texture conversion, tiled export UVs, edited meshes and sky selection. This does not establish full-map performance or multiplayer/Project Reclaimer compatibility.

## Shared interface and export destination

Reach uses the same browser, preview, multi-object swap, material/collision, sky, diagnostics and preparation panels as Halo 3. You do not need to switch the import game back to Halo 3 before preparing. The import game controls the source maps and catalogue; the export destination controls shaders, skies, starter shell, compiler and Sapien. The starter shell still uses Halo 3 Jungle assets and requires that map.

Halo 3 is the only implemented Sapien destination. Reach geometry and preview materials use the existing experimental static conversion route. Original Reach vehicle behavior and animation remain outside the static conversion route. Eligible model collision shapes can be read from HREK and recompiled. Halo CE, Halo 2, ODST and Halo 4 are reserved in the capability registry but are not enabled: they need extraction/conversion adapters and validation first.

## Requirements by operation

For models, textures and whole-map visual extraction, Reach data comes from MCC Reach maps and shared resources. Extracted HREK tags are not consumed by that extraction path, although Check setup still expects HREK executables. Halo 3 preparation uses H3EK and its extracted tags. See [Installation](INSTALLATION.md#requirements) for the complete distinction and shared Blender/runtime dependencies.

For a static Reach shield or character, select its material slot and use [editable colors](EDITABLE-MATERIALS.md). Repeating color materials can retain wrapped UVs. Glow and gameplay remain approximations.

## Original collision requirements in v0.9.1

Automatic collision reuse needs the matching source game's Editing Kit tags. Install and extract H3EK for Halo 3 sources and HREK for eligible Reach model collision. Keep the source kit paths configured under Folders and Setup for each import game. Halo 3 preparation still uses H3EK as its destination.

MCC maps supply the visual extraction data. Missing or unmatched original collision can use the documented static fallback. The preparation report identifies the route actually used. Model collision reuse does not recreate Reach gameplay in Halo 3.

