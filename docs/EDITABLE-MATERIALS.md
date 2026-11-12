# Editable materials (experimental)

[Home](../README.md) · [Sidebar reference](FEATURES.md#editable-materials-experimental) · [First map](FIRST-MAP.md)

Editable materials let you paint terrain and recolor models in Blender, then have preparation bake the result into **new** Halo 3 bitmaps and shaders inside your level's folder. The original game tags are never changed.

All controls are in the **Editable Materials (Experimental)** section of the sidebar and work on the **selected object's active material slot**.

## 1. Load the original textures

Select the object, pick its material slot in Blender's Material Properties, and make sure **Import game** is the game the material came from. Then click **Load Halo Shader Textures/Masks for Currently selected Material**.

HaloBridge reads the material's shader from its `.map`, including terrain blend maps, detail layers and color-change masks, and rebuilds the Blender preview. Check that the preview looks right before converting.

## Paint terrain

Halo terrain blends up to four shaders (for example grass, rock, dirt and sand) using a blend map. A paintable terrain lets you repaint where each one shows.

1. Load the original textures (above).
2. Click **Create paintable terrain**. The material becomes an editable copy that starts with the level's original blend.
3. Choose a **Texture resolution**: 512, 1024, 2048 or 4096. This is the size of the baked texture, so bigger terrain needs a higher value.
4. Expand **Repeat settings** to change how often each layer's texture tiles (X and Y are used).
5. Each layer has its own collapsible section, **Shader 1** to **Shader 4**, named after its texture. Open one to see its base, detail and normal images.
6. Click **Paint** in a layer's header. Blender switches to Texture Paint with that layer selected; paint on the mesh to show that layer there.
7. **Paint original blend** paints the level's original mix back.
8. Click **Pack texture edits into blend**, then save your `.blend`.
9. Prepare the level. HaloBridge bakes the color and normal result into textures and a shader under your level.

Tips:

- Look at each layer's images to see which number is grass, rock and so on; numbers follow the original shader.
- Terrain painting needs non-overlapping UVs in one 0–1 tile. HaloBridge adjusts the UV range when converting and compensates the texture tiling. Overlapping UVs paint the same spot twice.
- The starter template's **Jungle ground** is already a paintable terrain.
- Small brush buttons next to each image paint that image directly. In the Image Editor, a red mask shows a layer's weight.
- If an older editable material was already reduced to one texture, convert again from the original material to get its layers back.

## Recolor models and vehicles

**Create editable colors** gives a material a base texture plus four tint colors controlled by a mask.

1. Load the original textures.
2. Click **Create editable colors**.
3. Set **Color 1** to **Color 4**. They follow the mask's red, green, blue and alpha channels. If the original shader has a Halo color-change mask, that's used; otherwise Color 1 starts by covering the whole material, and you can load or paint a mask to limit it. The panel shows which mask is in use.
4. Pack your edits and save.
5. Prepare. The tinted result is baked into new textures.

**Original Halo 3 vehicles:** first match the vehicle (see [Keep a vehicle drivable](FIRST-MAP.md#keep-a-vehicle-drivable)), then select its exterior material slot and click **Create editable colors**. Preparation creates a copy of the vehicle, model and render model tags under your level that uses your paint and still points at the original gameplay and physics. Other material slots keep their original shaders. Turrets and other attachments with their own models aren't repainted. The paint is fixed, so it doesn't change with team colors.

**Characters and shields** (for example a Reach Elite placed as static geometry) work the same way; the result is static geometry.

## Things to know

- Converting assigns a new material to the active slot. A shared mesh is made single-user first so other copies don't change.
- Pack images and save before closing Blender, or your paint is lost.
- Only color and normal maps are baked. Live color change, reflections, specular, animation and other engine effects aren't reproduced.
- Keep node edits UV- and image-based. Unsupported nodes and UVs outside the tile are reported before export.
- Editable colors support UVs beyond the first tile for repeating textures with whole-number tiling. Terrain painting needs a single tile.
- Loading original textures only changes the preview. To export changes, create an editable material.
