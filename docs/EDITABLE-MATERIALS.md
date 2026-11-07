# Editable materials (experimental)

HaloBridge can author UV-painted terrain and masked colors for static Halo 3 level geometry. It bakes the edited surface into level-local bitmap and shader tags. Stock game tags are not edited.

## Read the source material

Select a placed mesh and its material slot. Choose the correct import game and a .map containing that shader, then click **Load Halo Shader Textures/Masks for Currently selected Material**. Terrain blend maps and layers now contribute to the Blender color preview. Color-change masks become available to the color editor. This remains an approximation of Halo rendering, not a reproduction of every shader option, lighting or reflection.

## Paint terrain

1. Select terrain and its original Halo material slot. Load its source textures with **Load Halo Shader Textures/Masks for Currently selected Material**. Confirm the blended preview before continuing.
2. Click **Create paintable terrain**. Supported layered terrain retains its source blend and gains a paint overlay. An older editable material that was already reduced to one texture needs a fresh conversion from the original material to recover the source blend.
3. Choose a texture resolution from **512, 1024, 2048 or 4096**. Expand **Repeat settings** to adjust tiling with compact X/Y/Z controls. UV sampling uses X/Y.
4. Click a numbered shader-layer paint button and paint on the mesh in Texture Paint mode. Layer numbers refer to the source shader's textures, so inspect the images when choosing grass, rock or another surface. **Paint original blend** restores the underlying source mixture. Older three-layer editable materials retain their existing mask interpretation.
5. Use the small texture brush buttons to paint a selected image directly. A red mask in the Image Editor represents a layer weight. View the mesh in Material Preview to see the mixed surface.
6. Click **Pack texture edits into blend**, then save. Return to Object Mode and prepare the scene to bake the color and normal textures into level-local tags.

Terrain painting needs unique UVs in a single tile. Conversion can normalize the active material's used UV range while compensating its original texture sampling. Overlapping UVs still paint the same area. Large terrain can lose fine detail when baked to one image. Custom export produces baked textures, with the selected resolution determining the available detail.

## Recolor armor or vehicles

Load the source shader textures first, then click **Create editable colors** on the desired material slot. Colors 1-4 correspond to R, G, B and alpha in the mask. A source Halo change-color mask is used when available. Without one, Color 1 initially affects the whole selected material; load or paint a mask to limit it. The mask source is displayed in the panel.

For an original Halo 3 vehicle, choose its exterior material slot, click **Create editable colors**, and adjust the tint. Preparation bakes the painted slots and creates a vehicle, model and render model under the output level. These tags reference the original gameplay and physics resources. Other shader slots keep their original references. Turrets or other attachments with their own render models are separate. Custom colors represent fixed paint rather than AI rank or team-color logic.

## Limits and preservation

- Editable material creation assigns a separate material to the active slot and makes a shared mesh local before changing its slots.
- Custom masks and image edits can be packed into the blend; they should be packed and the blend saved before closing.
- Color and normal maps are baked; live Halo color changes, shader reflections, specular layering, animation and other engine effects are not reproduced.
- Node edits must remain UV/image-based. Unsupported nodes and out-of-tile UVs are reported before export.
- Original Halo shader preview improvements alone do not turn an imported stock shader into an editable exported shader. Create an editable material to export changes.

Existing indexed source maps help locate shaders when a different map is selected. Editable Colors supports UVs beyond the first tile for repeating textures with whole-number tiling. Terrain painting still requires a single UV tile.
