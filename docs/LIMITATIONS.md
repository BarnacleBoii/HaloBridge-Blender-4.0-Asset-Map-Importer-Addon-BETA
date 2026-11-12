# Known limits

[Home](../README.md) · [Supported games](GAMES.md) · [Troubleshooting](TROUBLESHOOTING.md) · [Verification history](../TESTING.md)

HaloBridge v0.10.0 is a beta. This page lists what it doesn't do yet, so you know what to expect before you build on it.

## Platform

- Windows x64 only. Blender 4.0 to 5.2.
- The Halo Asset Blender Development Toolset must be v432 or newer on Blender 4.1+ (v364 or v432 on 4.0).
- MCC on PC (Steam or Xbox app / Game Pass). Console files aren't supported.

## Importing

- **Static content only.** AI, scripts, triggers, game types, animations, doors that open and break, and baked lighting aren't imported. A whole-level import is a visual starting point, not the playable mission.
- **Placement types.** From a `.scenario`, scenery, crates, machines, controls and vehicles are built; weapons and equipment are imported for reference only. Bipeds, decals, decorators, lights, cutscene flags, AI and zone sets aren't imported. All BSPs import together; zone sets aren't applied.
- **Source files.** Halo 3 / ODST `.scenario` import needs the source files stored inside the kit's BSP and render model tags. A BSP without one is skipped and reported; a render model without one uses its `.map` mesh.
- **Preview textures** come from the matching `.map`. A shader that isn't in that map has no preview texture.
- **Reach** `.scenario` geometry comes from the `.map` (default variants), because HREK has no source models. Reach's developer-only BSPs don't decode.
- **Halo: CE and Halo 2** `.scenario` import uses a map built by the kit's Tool, so instance names and material flags are the map's, not the authored source's.
- **Whole-map coverage.** Not every BSP or object is guaranteed to decode; the import report lists what's missing. Campaign maps load every streamed area at once.
- **Material previews** approximate Halo's rendering. Layered shaders, water, reflections, glow, fog and lighting can look different.

## Sapien preparation

- **Destinations:** Halo 3 and Halo 3: ODST. Reach Sapien preparation isn't available (the Halo toolset's ASS exporter only targets Halo 2 and Halo 3). Halo: CE and Halo 2 levels can't be prepared either; their assets can be used in a Halo 3 level.
- **What's exported:** your current meshes as static geometry, plus unedited original scenery and matched vehicles as their original tags. Gameplay must be added in Sapien.
- **Original vehicles:** Halo 3 / ODST vehicles only, matched to their own model. Mesh edits don't carry over; other games' vehicles become static shapes.
- **Collision:** original collision is reused only when HaloBridge can prove the mesh is unchanged and the source game's kit is installed (Halo 3, ODST, Reach models). Otherwise a box or the mesh's surfaces are used. Halo: CE and Halo 2 objects never reuse original collision. Fallback collision can feel different from the original.
- **Converted materials** (from other games) keep base color, normal map, UV tiling and cut-out transparency. Detail layers, blend modes, reflections, glow and animated effects aren't converted. Converted bitmaps are uncompressed, so large scenes need more disk space and memory.
- **Converted skies** keep geometry and base, normal and alpha textures. Sky lighting, fog, atmosphere and animated clouds aren't converted. Halo: CE clouds look grey, and Halo: CE / Halo 2 skies blend additively and can look bright.
- **Lighting:** only a draft test lighting preset. There's no final-quality lighting option.
- **Compiler limits:** imported geometry can be invalid for Tool, exceed its limits, or overlap. HaloBridge reports this but doesn't simplify geometry for you.
- **Editable materials** bake to one UV tile per material, so large terrain can lose detail.
- **Repeat builds** keep content you added in Sapien, but this hasn't been tested on every kind of map. Keep backups.

## Projects and portability

- Saved `.blend` files refer to textures in the HaloBridge cache. Keep the cache or pack resources before moving a project to another PC.
- Project records in the storage folder are tied to the paths on your PC.
- Forcing Blender to close during preparation can interrupt the automatic rollback.

## Not tested yet

- A full multiplayer release through Project Reclaimer.
- Every map in every game. Large levels and unusual maps may hit new problems.

## Feedback that helps most

1. Fresh-install reports with exact Blender, toolset and runtime versions.
2. Small, reproducible import or material problems, named by map and asset (please don't upload game files).
3. Preparation results for edited, moved and deleted objects, collision, and repeat builds.
4. Import and preparation times and memory use on large levels.

These areas may improve in future versions; this isn't a promise of complete level reconstruction or a release schedule.
