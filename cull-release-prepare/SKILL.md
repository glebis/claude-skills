---
name: cull-release-prepare
description: Use when the user explicitly asks to prepare or bump a Cull patch, minor, or major release, curate its changelog and compatibility review, or create its focused release commit without publishing.
---

# Cull Release Prepare

## Principle

Prepare one reproducible release commit.

Preparation cannot tag, push, dispatch workflows, publish, or update Homebrew.

## Required inputs

- An explicit `patch|minor|major`; never infer the bump.
- Green cull-release-check evidence bound to `expectedSource` and
  `expectedVersion`.
- Curated release notes and compatibility-review JSON matching Cull's CLI schema.

## Prepare

1. Fetch `origin/main` and create a dedicated clean worktree from it. Preserve
   unrelated dirty worktrees.
2. Confirm the check evidence still matches HEAD and the expected next version.
3. Store curated notes in a safely quoted path. Use argument arrays or separately
   quoted variables; never evaluate a concatenated command.
4. Run the dry run first: `npm run release:cull -- prepare ... --dry-run --json`.
5. Parse exactly one JSON envelope. Continue only when it lists exactly the
   configured version, changelog, compatibility, and state files.
6. Run the same prepare command without `--dry-run`.
7. Verify one `chore(release): vX.Y.Z` commit, state `prepared`, the declared file
   set, no tag, and no remote mutation.

On failure, show diagnostics and changed files. Never reset, discard, or overwrite
work outside the release-owned file set.
