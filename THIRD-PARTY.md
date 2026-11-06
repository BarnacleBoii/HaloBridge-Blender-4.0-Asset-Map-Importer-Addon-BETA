# Third-party components

HaloBridge is distributed under GPL-3.0; see LICENSE.

Reclaimer Core, Reclaimer Blam, and the legacy AMF importer are by Gravemind2401 and contributors, GPL-3.0. Upstream: https://github.com/Gravemind2401/Reclaimer . Pinned source commit: `36224d7a4581f2a1f255099bf706aa56be9f6e21`.

Corresponding Core and Blam sources and their license are in `source/Reclaimer`; the legacy AMF importer is `halo_bridge/vendor/amf.py`. This distribution retargets Core/Blam to .NET 10, disables Blam assembly signing, uses C# 13, and removes native xcompress binary copying. The original Core signing key is an upstream build input, not a user credential. No upstream native xcompress DLLs are distributed: console/LZX-dependent formats are outside the public release's supported input route. Debug output is disabled and compiler source paths are mapped to a neutral prefix.

System.Drawing.Common 10.0.9 is a build dependency supplied through NuGet. Its runtime implementation is supplied by the user's installed Windows Desktop Runtime; no Microsoft runtime DLLs are bundled in the release. Rebuilding requires access to NuGet packages.

The Halo Asset Blender Development Toolset is an external dependency by General-101 and contributors: https://github.com/General-101/Halo-Asset-Blender-Development-Toolset . It is not redistributed. The tested adapter supports v364 and v432.

Halo assets, the Halo 3 Editing Kit, ManagedBlam, and MCC map files are external user-supplied dependencies. None are included in the public add-on or source archives. The code license does not apply to game content.
