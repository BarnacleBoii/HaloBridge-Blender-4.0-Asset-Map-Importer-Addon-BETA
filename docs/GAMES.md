# Supported games

[Home](../README.md) · [Installation](INSTALLATION.md) · [Importing](IMPORTING.md) · [Halo: Reach](REACH.md)

HaloBridge separates the game you **import from** (the **Import game** drop-down) from the game you **prepare for** (**Export to Sapien**). You can import from any of the five games below and prepare a Halo 3 or ODST level that mixes all of them.

## At a glance

| | Halo: CE | Halo 2 | Halo 3 | Halo 3: ODST | Halo: Reach |
| --- | --- | --- | --- | --- | --- |
| Index and place `.map` assets | ✅ | ✅ | ✅ | ✅ | ✅ |
| **Import entire .map** | ✅ | ✅ | ✅ | ✅ | ✅ |
| **Import level from .scenario** | ✅ via Tool | ✅ via Tool | ✅ from source | ✅ from source | ✅ placements from tags, geometry from `.map` |
| **Index .scenario Assets** | ✅ | ✅ | ✅ | ✅ | ✅ |
| Use its assets in a Halo 3 / ODST level | ✅ converted | ✅ converted | ✅ | ✅ | ✅ converted |
| Use its sky in a Halo 3 / ODST level | ✅ converted | ✅ converted | ✅ | ✅ | ✅ converted |
| Original collision reused | ➖ box / mesh | ➖ box / mesh | ✅ | ✅ | ✅ (models) |
| **Sapien destination** | ➖ | ➖ | ✅ | ✅ | not yet |

## Folders

| Game | Editing Kit folder | MCC maps folder | HaloBridge storage |
| --- | --- | --- | --- |
| Halo: CE | `HCEEK` | `halo1\maps` | `HaloBridge\halo1` |
| Halo 2 | `H2EK` | `halo2\h2_maps_win64_dx11` | `HaloBridge\halo2` |
| Halo 3 | `H3EK` | `halo3\maps` | `HaloBridge` |
| Halo 3: ODST | `H3ODSTEK` | `halo3odst\maps` | `HaloBridge\odst` |
| Halo: Reach | `HREK` | `haloreach\maps` | `HaloBridge\reach` |

**Detect folders** finds all of these automatically when they're in a Steam library or an Xbox app / Game Pass install. The kits are only needed for the features that use them; see [What each task needs](INSTALLATION.md#what-each-task-needs).

## Halo 3

The main game. Halo 3 `.scenario` import reads BSPs and render models from the source files stored in the H3EK tags, so you get original instance names, exact shader names, and scenery that is written back as real scenery tags when you prepare. Halo 3 is the default Sapien destination; its sky list comes from the H3EK tags (default Deadlock).

## Halo 3: ODST

Works exactly like Halo 3, using H3ODSTEK. ODST is also a full Sapien destination: set **Export to Sapien** to Halo 3: ODST. ODST and Halo 3 share many tags; when an ODST shader also exists at the same path in H3EK, a Halo 3 level reuses it instead of converting it. The default ODST sky is the one from `h100` (Mombasa Streets).

## Halo: Reach

Reach's Editing Kit has scenarios and placements but no source models or BSP sources, so `.scenario` import takes placements from HREK and geometry from the `.map`. Reach assets can go into a Halo 3 level as static geometry with converted materials. Reach Sapien preparation isn't available yet, because the Halo toolset's ASS exporter only targets Halo 2 and Halo 3. See [Halo: Reach](REACH.md).

## Halo: CE and Halo 2

Both import from MCC `.map` files without any Editing Kit. Their kits have no ManagedBlam, so `.scenario` import has the kit's own Tool build a map first (about 10 seconds for a Halo: CE level, one to two minutes for Halo 2) and then imports that map. Halo 2's maps are in MCC's `halo2\h2_maps_win64_dx11` folder.

In a Halo 3 level, their materials are converted and their objects use a box or mesh-surface collision (their kits can't be read for original collision). Their skies are camera-centred in the original games, so a converted sky is enlarged to surround your level.

Halo: CE shaders that Halo 3 can't represent, such as cloud tints and animated effects, are simplified: base, normal and alpha textures carry over.

## Halo 4

Listed internally but not enabled. It needs its own extraction and conversion work first.
