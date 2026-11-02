---
name: cull-release-publish
description: Use when the user explicitly asks to publish or complete a prepared Cull release, or when the authorized cull-release orchestrator reaches publication after every repository and artifact gate passes.
---

# Cull Release Publish

## Authority

An explicit “Release Cull patch|minor|major” or direct “Publish prepared Cull
release X.Y.Z” request authorizes publication. Do not ask for another confirmation
after gates pass. That authority does not waive or bypass any gate.

Implicit invocation is disabled. Without that explicit authority, stop before any
tag, push, workflow dispatch, release, or tap mutation.

## Publish

1. Resolve the Cull checkout and parse one JSON envelope from
   `npm run release:cull -- state show --version "$VERSION" --json`.
2. Require state `prepared`, exact metadata, a clean release commit already pushed
   on `main`, green required checks, active branch/tag protection, publication
   enablement, and no conflicting tag.
3. Create one annotated tag for the prepared commit and push that tag normally.
   Never move, replace, or force-push a tag.
4. Watch the tag-bound GitHub release workflow. Never substitute a local build.
5. Require the secret-free verifier's exact artifact inventory, signatures,
   notarization, checksums, and provenance before automatic publication.
6. Wait for checksum-pinned Homebrew promotion and its audit/install/launch proof.
7. Record evidence transitions through `published` and `homebrew-promoted` using
   the repository CLI's state commands.

## Tag-time anchor and race rules (required)

- The release workflow gate requires the tagged SHA to be at-or-ahead of
  origin/main **and** to carry the bumped version files. Only the release PR's
  **merge commit** satisfies both. The record's `releaseCommit` (written by
  prepare as the pre-prepare tip) does not — re-anchor the record's
  `releaseCommit` to the merge commit (external-evidence cache repair) after the
  release PR merges, then pass that SHA to `--expected-source`.
- Immediately before tagging: `git fetch origin main` and verify the tip still
  equals the merge commit and no auto-merge PR is mid-flight. A single dependabot
  commit landing after the tag push burns the tag (STALE_RELEASE_SOURCE; tags
  are immutable) — recovery is a deeper version, not a tag move.
- Watch the run's gate step first; only then do the longer build/notarize steps
  matter. If the gate fails, stop and route through cull-release-recover.

On failure, use cull-release-recover. Never delete or rewrite a tag, delete a
release, replace published assets, bypass verification, or force workflow state.
