---
name: cull-release-verify
description: Use when verifying or auditing a Cull release, DMG, updater archive, notarization, Homebrew cask, installed version, launch health, or post-publication distribution state.
---

# Cull Release Verify

## Principle

Reconstruct release truth from immutable public evidence. Verification is
read-only by default.

## Verify

1. Resolve the Cull checkout and select the explicit version or latest public
   release.
2. Run `npm run release:cull -- state show --version "$VERSION" --json` and parse
   exactly one JSON envelope.
3. Bind the annotated Git tag object and peeled commit to the published release,
   authenticated workflow run, provenance, and required asset inventory.
4. Download artifacts to an isolated temporary directory. Run Cull's exact
   artifact verifier; check updater signature, SHA-256 checksums, DMG contents,
   embedded version and architecture, codesign, Gatekeeper, and notarization
   staple.
5. Compare Homebrew version and SHA-256 with public provenance and require its
   promotion evidence.
6. Report version, commit, tag object, workflow, asset hashes, release URL, tap
   commit, installed-version evidence, launch evidence, and mismatches.

Default to no installation. When the user explicitly requests an install smoke,
use an isolated location and preserve any existing app. Never edit release state,
the GitHub release, tags, the tap, system Applications, or `cull.db`.
