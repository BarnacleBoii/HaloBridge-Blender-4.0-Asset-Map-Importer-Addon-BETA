# Editable materials (experimental)

HaloBridge can author UV-painted terrain and masked colors for static Halo 3 level geometry. It bakes the edited surface into level-local bitmap and shader tags. Stock game tags are not edited.

## Read the source material

Select a placed mesh and its material slot. Choose the correct import game and a .map containing that shader, then click **Load Halo shader textures and masks**. Terrain blend maps and layers now contribute to the Blender color preview. Color-change masks become available to the color editor. This remains an approximation of Halo rendering, not a reproduction of every shader option, lighting or reflection.

## Paint terrain

1. Select the terrain and its material, then click **Create paintable terrain**.
2. Choose Grass, Rock and Dirt images using each image selector or folder button. Existing Jungle layers are initial textures, not a guarantee that a layer contains the surface its generic label describes.
3. Adjust Repeat to control texture tiling. Use matching normal layers when changing textures.
4. Click **Paint Grass**, **Paint Rock**, or **Paint Dirt**, then paint on the mesh in Texture Paint mode. Black mask means grass, red means rock, and green means dirt. Intermediate values blend the layers.
5. The small brush buttons also let you paint directly on a layer image.
6. Click **Pack texture edits into blend**, then save the blend file.
7. Return to Object Mode and prepare the scene. HaloBridge bakes color and normal textures and compiles custom shader tags.

Use UVs within one 0-1 tile. Overlapping UVs share the same painted area. To paint unique areas of a large landscape, unwrap appropriately or divide it into independently textured surfaces. Baking to 1024 pixels can lose tiled detail over a large surface; 512, 1024, 2048 and 4096 are supported. This version does not export a new native multi-layer terrain shader with unlimited tiled detail.

## Recolor armor or vehicles

Load the source shader textures first, then click **Create editable colors** on the desired material slot. Colors 1-4 correspond to R, G, B and alpha in the mask. A source Halo change-color mask is used when available. Without one, Color 1 initially affects the whole selected material; load or paint a mask to limit it. The mask source is displayed in the panel.

Color choices are baked for static geometry; this does not change an AI character's rank/team colors or the appearance of an original vehicle-tag placement. Use the static route for these custom materials. Other material slots retain their own settings.

## Limits and preservation

- Editable material creation assigns a separate material to the active slot and makes a shared mesh local before changing its slots.
- Custom masks and image edits can be packed into the blend; they should be packed and the blend saved before closing.
- Color and normal maps are baked; live Halo color changes, shader reflections, specular layering, animation and other engine effects are not reproduced.
- Node edits must remain UV/image-based. Unsupported nodes and out-of-tile UVs are reported before export.
- Original Halo shader preview improvements alone do not turn an imported stock shader into an editable exported shader. Create an editable material to export changes.

Existing indexed source maps help locate shaders when a different map is selected. Editable Colors supports UVs beyond the first tile for repeating textures with whole-number tiling. Terrain painting still requires a single UV tile.
