---
name: cull-release
description: Use when orchestrating or resuming Cull's complete release cycle, reporting its current release state, or fulfilling an explicit Cull patch, minor, or major release request through verified GitHub and Homebrew distribution.
---

# Cull Release

## Principle

Orchestrate Cull's repository-enforced phases; never recreate release logic in
the skill. Read `references/phase-contracts.md` before acting.

## Start or resume

1. Resolve Cull from a matching current origin, absolute `CULL_REPO`, or
   `$HOME/ai_projects/cull`.
2. For a new release, require explicit `patch|minor|major`; never infer it.
3. Use cull-release-check. Stop on every blocker.
4. Use cull-release-prepare in its isolated worktree.
5. Use cull-release-publish after preparation. An explicit complete-release
   request already authorizes publication: Do not ask for a second publication confirmation.
6. Use cull-release-verify after GitHub publication and Homebrew promotion.
7. On interruption, derive the last verified state from commit, tag, workflow,
   artifacts, release, and tap evidence. Resume the first incomplete phase; do
   not repeat completed work.
8. Route every mismatch or failed phase through cull-release-recover.

## Completion report

Report version, release commit, annotated tag object, workflow run, artifact
hashes, release URL, Homebrew tap commit, and final
`post-publish-verified` state. Do not print secret values.
