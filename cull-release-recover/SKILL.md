---
name: cull-release-recover
description: Use when a Cull release is stuck, inconsistent, failed in a workflow or artifact gate, missing Homebrew promotion, failed after publication, or needs a safe recovery or patch plan.
---

# Cull Release Recover

## Principle

Derive truth from external evidence, then resume the first incomplete safe phase.
Never erase immutable release history to make local state look consistent.

## Diagnose

1. Resolve the Cull checkout.
2. Run `npm run release:cull -- resume --version "$VERSION" --json` and parse
   exactly one JSON envelope. Treat local release state as a cache.
3. Authenticate and compare the prepared commit, remote annotated tag and peeled
   commit, Actions run, exact asset inventory, public release, updater metadata,
   provenance, and Homebrew cask/evidence.
4. Classify the next action exactly as `rerun-check`, `prepare-new-version`,
   `watch-build`, `verify-artifact`, `publish-verified-artifacts`,
   `promote-homebrew`, or `prepare-patch-plan`.
5. Execute only the safe resumable phase the user already authorized. Do not
   repeat a completed signed build or replace verified artifacts.

A post-publish verification failure creates or updates the stable P0 bd incident,
blocks later release checks, and returns `prepare-patch-plan`. Prepare the patch
plan but never publish that patch implicitly.

Never delete or move a tag or release. Never force-push, clobber assets, reset
unrelated work, bypass a gate, clean `cull.db`, or treat missing evidence as
success.
