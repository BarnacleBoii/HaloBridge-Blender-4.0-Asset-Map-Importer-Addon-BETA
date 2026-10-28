# Halo: Reach importing

[Home](../README.md) | [Features](FEATURES.md)

## Setup

Install MCC's **Halo: Reach game content** for the `.map` files. **Halo: Reach Mod Tools - MCC (HREK)** is a separate Steam Tools installation expected by the current setup checker. Reach extraction reads MCC maps and does not require extracted HREK tags. To prepare these assets for Halo 3 Sapien, install **H3EK and extract its Halo 3 tags**. See [requirements by workflow](INSTALLATION.md#mcc-maps-versus-mod-tools).

1. Select **(Experimental) Halo Reach** above Folders and Setup.
2. Choose **Detect folders**. Verify **Reach Editing Kit** points to HREK and **Reach maps** points to MCC's haloreach/maps directory.
3. Choose **Check setup**. The extraction helper requires .NET 10 Desktop Runtime x64. Reach previews do not use the Halo 3 exporter or collision helper.
4. Enter a filename such as **70_boneyard.map** and choose **Import Map Assets**.
5. Use search, filters, Preview Mode and Place asset(s), or **Import entire .map** for available terrain and static placements in original positions.

## Profiles and scope

Halo 3 storage is preserved. Reach defaults to Documents/HaloBridge/reach. Each game remembers its folder choices and map filename, and loads its own catalogue and cached files. Save your blend file to retain these profiles. Changing the selector removes temporary previews but does not delete placed objects.

## Use Reach assets in Halo 3 Sapien

1. Keep your imported Reach objects in the current Blender scene and edit/place them normally.
2. Switch **Import game** to **Halo 3**. This changes the catalogue and folders; it keeps your scene objects.
3. Verify the editing kit is **H3EK**, enter your output level name, and choose a Halo 3 sky.
4. Click **Prepare current scene for sapien**, review the static-geometry warning, and continue.

The export uses current meshes and transforms, including edits and modifiers. It generates collision from their surfaces and builds Halo 3 bitmap and shader tags in the output level folder. Diffuse textures, normal textures, UV tiling and cutout alpha are supported. Existing Reach imports are detected from their object metadata; reimporting is unnecessary. An explicitly assigned Halo 3 shader overrides conversion.

This is a static map-building workflow. Reach vehicles, weapons, machines and characters become static shapes, not functional game objects. Layered terrain shaders, water, glow, transparency blending and other complex effects are approximated from the Blender preview. Transparency becomes alpha-tested cutout. Differing texture tilings are resampled relative to the base texture; this can reduce detail and is approximate outside a single tile. Original Reach collision, scripts, animation and gameplay are not ported. Reach skies are not converted into Halo 3 sky tags; choose a Halo 3 sky.

Converted bitmaps currently use uncompressed formats for predictable quality. Large scenes can require substantial disk and runtime memory. Failed compilation restores the previous generated level. Missing textures or unsupported edited node graphs produce a material-specific diagnostic. Halo 3's geometry limits still apply. This version targets Halo 3 Sapien only.

Reach BSP indexing resolves instance sections from resource geometry and may take longer than Halo 3 indexing. Index warnings appear in Blender's **HaloBridge index report** text block. Whole-map omissions appear in the import report. A successful import does not guarantee all BSPs or model variants decoded.

## Verification in 0.7.0

Boneyard indexed 838 instance assets, 851 materials, 320 models and 28 scenery entries. Full extraction produced 8,474 placements from 2 of 3 BSPs; the hidden BSP failed decoding and was reported. Real instance/scenery/material extraction and repeat-cache reuse passed. Blender checks covered shared meshes, previews and a 21-placement sample spanning all seven map groups with original transforms. This is not a full-map runtime or Reach Sapien test.

## Conversion verification in 0.8.0

A real Boneyard instance and Halo 3 test ground compiled into a separate Halo 3 scenario. Repeat preparation with a cutout variant passed. Readback verified three instance definitions and 84 generated collision surfaces; shader tags referenced converted base, normal and alpha bitmaps and the cutout template. Automated Blender tests verified source UV/material preservation, texture conversion, tiled export UVs, edited meshes and sky selection. This does not establish full-map performance or multiplayer/Project Reclaimer compatibility.
