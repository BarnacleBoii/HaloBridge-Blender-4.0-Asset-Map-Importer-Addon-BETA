# HaloBridge v0.8.4 — Beta

Import MCC Halo 3 assets and original map layouts into Blender 4.0. Browse, preview and place assets, edit your scene, and experimentally prepare current static geometry for Halo 3 Sapien. Experimental Halo: Reach importing and static conversion into Halo 3 are included.

## Downloads and installation

- **HaloBridge-0.8.4.zip**: install this ZIP through Blender 4.0 → Edit → Preferences → Add-ons → Install, then enable HaloBridge.
- **HaloBridge-0.8.4-source.zip**: matching GPL source, including modified Reclaimer libraries, build instructions and tests.
- **SHA256SUMS.txt**: checksums for both archives.

GitHub's automatic source ZIP/TAR does not include built helpers. Follow [Installation](https://github.com/BarnacleBoii/HaloBridge-Blender-4.0-Asset-Map-Importer-Addon-BETA/blob/main/docs/INSTALLATION.md), [First map](https://github.com/BarnacleBoii/HaloBridge-Blender-4.0-Asset-Map-Importer-Addon-BETA/blob/main/docs/FIRST-MAP.md) and [Feature guide](https://github.com/BarnacleBoii/HaloBridge-Blender-4.0-Asset-Map-Importer-Addon-BETA/blob/main/docs/FEATURES.md) in the repository before starting.

Requires Windows x64, Blender 4.0 and .NET 10 Desktop Runtime. Supply your own MCC maps. Halo 3 preparation additionally requires H3EK with extracted tags, .NET Framework 4.8+ and Halo exporter 2.364.0. No game content is bundled.

## Included in this build

- Original source material and bitmap names in Blender, with automatic migration of generated names when reopening saved scenes. User names are preserved; shader references and cache identities remain stable.
- Mesh counts, current asset names and compiler/lighting stage status during preparation.
- A fix for asset-only scenes reaching the lightmapper without a structure mesh.
- Intentional material assignment and placement undo handling, plus experimental Reach texture-to-Halo-3 conversion.

## Experimental limits

Sapien preparation exports current static mesh surfaces with generated collision. It does not restore missions, AI, scripts, functioning vehicles, animated doors, breakable behavior or multiplayer modes. Whole-map imports may omit unsupported elements and approximate variants. Large maps can fail compiler or runtime limits. Reach shaders are simplified; Reach skies and gameplay are not converted. Project Reclaimer packaging and multiplayer are not verified.

Local checks include 23 unit tests, Blender naming/migration and undo tests, a real Halo 3 material-name compile, and a mixed Reach/Halo 3 lighting build. This is not validation of every map or a clean second Windows installation. See TESTING.md for details.

Save your .blend and retain project ownership manifests/backups. Report reproducible issues with sanitized diagnostics, never game files or extracted assets.
