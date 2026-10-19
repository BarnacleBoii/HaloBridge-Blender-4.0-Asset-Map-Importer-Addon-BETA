# Release checklist

Repository: `BarnacleBoii/HaloBridge-Blender-4.0-Asset-Map-Importer-Addon-BETA`

Version: **v0.8.4 Beta**. Keep the repository **private** for owner review. Keep the release a **draft**, with **Pre-release** enabled. Only the owner should make the repository public after review.

1. Run the source tests and `python scripts/package.py`. The packager checks archive contents, Python syntax, prohibited game files and personal build paths.
2. Upload only the audited source tree, including GPL license, third-party notices, modified Reclaimer sources, guides and synthetic tests. Never upload the parent workspace, private fixtures, game data or caches.
3. Use branch `main`, tag `v0.8.4`, and the release description from `RELEASE-NOTES.md`.
4. Attach `HaloBridge-0.8.4.zip`, `HaloBridge-0.8.4-source.zip` and `SHA256SUMS.txt`. Automatic GitHub source archives do not contain compiled helpers.
5. Verify the private repository, draft release and downloads while signed in. Draft download links in README become available to ordinary readers only after the release is published and repository access permits it.
6. Review installation instructions on a clean Windows computer before widening compatibility claims. Keep Issues enabled and preserve source alongside binaries.

Suggested topics: `halo`, `halo-mcc`, `halo3`, `halo-reach`, `blender`, `blender-addon`, `modding`, `sapien`.

Local artifacts alone do not establish that a GitHub repository or release exists.
