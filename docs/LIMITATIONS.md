# Known limits and community testing

[Home](../README.md) · [Verification history](../TESTING.md)

## Supported target

Windows x64, Blender 4.0.0, Halo exporter 2.364.0, and locally installed PC MCC Halo 3 maps with an extracted Halo 3 Editing Kit. Experimental MCC Halo: Reach importing and static conversion into Halo 3 are also available. Other exporter versions, console inputs and universal MCC conversion are not supported.

## Current limits

- **Static export:** doors, animated objects, breakable behavior, AI, scripts, triggers and multiplayer modes are not reconstructed. Add gameplay in Sapien separately.
- **Original vehicles:** explicitly matched Halo 3 model previews can use existing vehicle tags. Edited vehicle meshes and Reach vehicle conversion are not supported; actual driving and multiplayer need a playtest.
- **Collision:** generated from current mesh surfaces, generally two-sided. Original collision shapes, special surface behavior and material distinctions are not fully retained.
- **Visual fidelity:** preview textures and variants can be approximate. Water, layered shaders, fog, weather and baked lighting may differ from the game.
- **Whole-map coverage:** not every BSP or object is guaranteed to decode. Import reports identify known omissions. Campaign BSPs are assembled together rather than streamed as in game.
- **Compilation:** imported render geometry can be invalid for Tool, exceed limits or contain overlapping surfaces. A warning confirmation cannot make invalid geometry compile.
- **Lighting:** a draft preset is provided for testing. There is no multi-quality lighting selector or final-lighting workflow in this release.
- **Large maps:** preparation time, memory, visibility and runtime limits remain. Project Reclaimer packaging and multiplayer verification are separate work.
- **Project portability:** local paths and ownership manifests require care when changing computers or storage. Forced termination may interrupt rollback.
- **Release validation:** a second clean Windows machine and broad map/version coverage have not yet been tested.

## Feedback most useful for the next release

1. Fresh-install reports with exact Blender/exporter/runtime versions.
2. Small, reproducible extraction or material failures, using map and asset names rather than uploaded game content.
3. Current-scene export checks: edited shapes, deleted pieces, moved instances, collision and repeat preparation.
4. Measurements of import time, repeat-cache time and memory as scene size grows.
5. Clear documentation improvements and minimal code fixes with synthetic tests.

Future work may improve these areas, but this is not a promise of complete map reconstruction or a release schedule.
