# HaloBridge v0.9.1 — known limits and community testing

[Home](../README.md) · [Verification history](../TESTING.md)

## Supported target

Windows x64, Blender 4.0.0, Halo exporter v364 or v432, and locally installed PC MCC maps. H3EK with extracted tags is required for Halo 3 Sapien preparation and the current individual Halo 3 BSP-instance placement route; see the [requirements matrix](INSTALLATION.md#requirements). Experimental MCC Halo: Reach importing and static conversion into Halo 3 are also available. Other exporter versions, console inputs and universal MCC conversion are not supported.

## Current limits

- **Static export:** doors, animated objects, breakable behavior, AI, scripts, triggers and multiplayer modes are not reconstructed. Add gameplay in Sapien separately.
- **Original vehicles:** explicitly matched Halo 3 model previews can use existing vehicle tags. Edited vehicle meshes and Reach vehicle conversion are not supported; actual driving and multiplayer need a playtest.
- **Collision:** Automatic tries verified original geometry, then box or current-surface fallback. Opaque faces are not automatically doubled; open single-sided meshes use non-manifold surface flags. These flags do not repair arbitrary self-intersections or duplicates. Original collision shapes, special surface behavior and material distinctions are not fully retained.
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

## Import-only setup caveat

Check setup currently checks full-workflow prerequisites even for Blender-only use. Indexing and visual extraction do not automatically require every reported Editing Kit feature. Individual Halo 3 BSP-instance placement is an exception: it calls the tag helper for collision data. The minimum-dependency import-only configuration has not been validated on a second clean machine.

Halo 3 is the only Sapien destination. Reach importing/static conversion is experimental. Halo CE, Halo 2, ODST and Halo 4 are reserved in the shared framework but are not enabled.

Painted terrain exports as a baked UV tile. Large surfaces may lose detail. Masked colors apply to static geometry. Original vehicle placements use the colors supplied by their tags. [Editable materials](EDITABLE-MATERIALS.md).

## v0.9.1 scope

Original collision reuse is conditional on source identity, available tags, geometry matching and supported part selection. The fallback may change contact behavior. Recompiled static collision preserves the available shape, while gameplay, animation and detailed physics behavior depend on supported original object tags.

Internal instance partitioning addresses individual render-index limits. Large terrain clusters, visibility, lighting and overall map complexity can still fail compilation or perform poorly.

Regular shader preview improvements currently target supported Halo 3 albedo modes. Reach conversion, water, reflections, glow and other engine effects remain approximate. Snowbound shader and paired-face checks do not establish correctness for every material or map. Whole-map round trips and Project Reclaimer multiplayer releases need independent testing.

