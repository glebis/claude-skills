---
name: cull-release-check
description: Use when assessing whether Cull is ready to release, auditing or dry-running a Cull release, identifying version blockers, or before any Cull prepare or publish operation.
---

# Cull Release Check

## Principle

Treat Cull's JSON release CLI as authoritative. This skill is strictly read-only.

## Run the check

1. Resolve the checkout: current Git repository when its origin matches
   `glebis/cull`; otherwise absolute `CULL_REPO`; otherwise
   `$HOME/ai_projects/cull`.
2. Require an explicit `patch|minor|major` only when calculating a new target.
   Otherwise inspect the current candidate.
3. Capture `git status --porcelain` and `git rev-parse HEAD`.
4. Run `npm run release:cull -- check --bump "$KIND" --json` from the checkout.
5. Parse exactly one JSON envelope from stdout. Treat extra stdout, invalid JSON,
   or a nonzero exit as a blocker.
6. Capture status and HEAD again. If either changed, return
   `CHECK_MUTATED_REPOSITORY` and stop.

Before reporting green, sanity-check the two blockers that recur between
releases: free disk (delete regenerable `target/` dirs — gates need ≥15 GiB and
targets regrow 7–11 GB per build) and the dependabot auto-merge queue (it can
advance main between check and tag; wait for it to drain or account for it).

## Report contract

Report current and target versions, source SHA, branch and sync state, disk,
toolchains, contract gates, CI, secret presence, and every blocker. Report secret
presence only; never print environment values or secret contents.

## Mutation boundary

Run no preparation, commit, tag, push, workflow dispatch, publication, Homebrew
promotion, installation, or recovery apply action. If the CLI proposes one,
report it without executing it.
