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

## Burned-tag recovery (STALE_RELEASE_SOURCE / post-publish failure)

When a pushed tag's workflow fails and the tag is immutable (protected tags),
never move it. Follow the v0.5.0 / v0.6.1 / v0.6.2 precedent:

1. Record the failure: `state fail --version "$VERSION" --code GATE_FAILED|PUBLISH_FAILED|... --evidence-json '{...}'`.
2. Fix the underlying cause on main through a normal PR (never inside the tag).
3. Prepare the next version from current main. Pick the next deeper number
   (failed 0.6.0 → 0.6.1 → 0.6.2). Curated notes still follow the user-facing
   norm: cover the full delta since the last public release, plain language.
4. The recovery release PR may carry small non-owned commits (smoke records,
   doc fixes) — only the release *commit* is file-scoped.
5. Re-run the human smoke gate for the new version (fresh build, fresh
   `docs/releases/<v>-smoke.md`, fresh closed bead with
   `external_ref=cull-release-<version>-smoke` in the **landing worktree's** bd).
6. Re-anchor the record to the release PR merge commit before tagging (see
   cull-release-publish).
7. The `resume` command derives state from the local cache and can lag external
   reality (e.g. it may say `watch-signed-build` for a workflow that already
   failed). Authenticate the workflow run itself before trusting it.

A post-publish verification failure creates or updates the stable P0 bd incident,
blocks later release checks, and returns `prepare-patch-plan`. Prepare the patch
plan but never publish that patch implicitly.

Never delete or move a tag or release. Never force-push, clobber assets, reset
unrelated work, bypass a gate, clean `cull.db`, or treat missing evidence as
success.
