# Release procedure

For v0.9.1 and later, update the add-on version, README, user guides, feature index, changelog and release notes together. Preserve owner edits from GitHub. Run applicable tests, then scripts/package.py. Review the source diff and both audited archives.

Commit the exact release source, create a new version tag at that commit, and upload the installer and matching source ZIP to a draft prerelease. Verify both uploads before publishing. Keep the repository visibility and older releases intact. The public release page includes requirements, installation, changes and limitations. Detailed verification belongs in TESTING.md.

Exclude game content, caches, personal paths, diagnostics and local test scenes. The supplied docs/halobridgelogo.png is the approved project image. Review the live release state and verify anonymous downloads after publishing.
