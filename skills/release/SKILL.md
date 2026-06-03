---
name: release
description: >-
  Cut a software release and maintain a tiered compatibility policy. Use when the
  user wants to release, ship a version, bump the version, tag a release, write a
  changelog, or update COMPATIBILITY. Config-driven via release.config.json;
  bumps version files, runs a readiness gate, updates COMPATIBILITY.md tiers and
  deprecations, tags (→ release workflow), and reports closed issues. Teaches the
  underlying standards as it runs.
---

# release — tiered compatibility & release workflow

A config-driven release orchestrator. Mechanics live in `scripts/release.py`
(unit-tested, stdlib-only); this file is the workflow you (or an agent) follow.
Read `reference/config-schema.md` for `release.config.json` and
`reference/standards.md` for *why* each step exists.

> **Scope honesty:** reference-tested on a Tauri + Rust + SvelteKit repo (Cull).
> Other stacks are supported *by config*, not yet validated. Treat first runs on
> a new stack as a dry run (see "Dry run" below) until you trust it.

## When to use
The user says "release", "ship it", "cut a version", "bump version", "tag a
release", "update the changelog/COMPATIBILITY". Requires a `release.config.json`
at the repo root (scaffold from `templates/release.config.json.tmpl`).

## Mental model — your public API is your declared surfaces
A version only means something once you declare *what you promise to keep
working*. `release.config.json → surfaces[]` is that declaration; each surface
has a **tier** (`experimental → preview → stable`) and a compatibility **mode**.
Only `stable` surfaces carry the promise. Breaking a `stable` surface forces a
**major** bump — the engine enforces this. (Standards: see `reference/standards.md`.)

## Command
`/release <patch|minor|major>` — run the steps below. On an unfamiliar repo, do a
**dry run first** (see below). When the user asks to "explain", expand each step's
*why* into a short lesson from `reference/standards.md`.

## Steps

1. **Preconditions.** The configured `releaseBranch` (default `main`, in
   `worktree` if set) is checked out, clean, and synced with `origin`. Abort
   clearly otherwise. — *why: a release tag must point at a known-good, pushed tree.*

2. **Version.** `python3 scripts/release.py --config <cfg> plan <kind>` prints the
   new version + tag. It asserts the version files currently agree. Show `old → new`.
   — *why: SemVer math; 0.x lets minors break (pre-1.0).* [[Semantic Versioning (SemVer)]]

3. **Readiness gate.** Run `cfg.gate` then each `cfg.extraGate[]`. All must exit 0
   (fmt, clippy, tests, license audit, prod build, golden contract tests). Block on
   failure. — *why: this is a Production-Readiness Review.* [[Production Readiness Review]]
   - TODO (deferred): cargo-deny / cargo-audit / SBOM. List, don't enforce yet.

4. **Changelog.** Collect commit subjects since the last tag
   (`git log <lastTag>..HEAD --format=%s`) and draft a section — the engine's
   `draft_changelog` buckets them into Added/Changed/Fixed (Keep a Changelog).
   Insert under the top of `CHANGELOG.md`; **hand-curate** the user-facing lines.
   — *why: humans read changelogs; conventional commits seed them.* [[Keep a Changelog]]

5. **Compatibility review.** Open `cfg.compatibility.path` (COMPATIBILITY.md). Ask:
   - Did any surface change tier? (update the Surfaces table)
   - New deprecations? (add a row: item / deprecated-in / removable-in / replacement)
   - **Does this change break a `stable` surface?** If yes, the required bump is
     `major` — re-run with `major` or the release is invalid. (Enforced by
     `enforce_bump`.) Stamp "Last updated: <new version> (<date>)".
   — *why: tiers + deprecation windows are how you evolve without lying.* [[Kubernetes API Deprecation Policy]]

6. **Bump & commit.** `python3 scripts/release.py --config <cfg> bump <kind>` writes
   every version file; refresh `cfg.lockfiles` (e.g. `cargo update -p <crate>` or a
   build). Commit `chore(release): v<new>` including CHANGELOG + COMPATIBILITY.

7. **Tag & push.** `git tag v<new>` and push the tag (→ the repo's release
   workflow) and the branch. Confirm the tag trigger exists *before the first
   release* (`grep -A3 '^on:' .github/workflows/*.yml`).

8. **Report.** Print the tag, the release-workflow URL, and issues closed since the
   last tag (if `cfg.issueTracker` is set, e.g. bd) — those are the release notes.

## Dry run
There is no `--dry-run` flag — a dry run is steps 1–5 done *without mutating*:
run `python3 scripts/release.py --config <cfg> plan <kind>` (pure: prints the
version/tag, writes nothing) and optionally run `cfg.gate` to check readiness.
Do NOT run `bump`, commit, or tag. The `bump` subcommand is the only engine
command that writes (version files only); commit/tag/push are git steps you take
in step 6–7, never the engine.

## Manual fallback (no skill)
`plan` → run gate → edit CHANGELOG + COMPATIBILITY → `bump` → commit → tag → push.
The engine is just `scripts/release.py`; everything else is git.

## Growing into Contracts & Modes
The readiness gate runs *golden/contract tests* (`cfg.extraGate`). Start with one
(a DB round-trip), then add export and API contract tests. See the consuming
repo's `docs/CONTRACTS.md` and `reference/standards.md`. [[Pact — Consumer-Driven Contract Testing]]
