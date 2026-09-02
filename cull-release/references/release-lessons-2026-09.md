# Cull release lessons — 2026-09 v0.6.x cycle

Five tag/attempt cycles were needed to ship the first post-0.5.1 release
(v0.6.0 → v0.6.1 → v0.6.2), and the first post-release feature PR needed three
CI attempts because the packaged interaction smoke exposed a startup crash.
Each failure is recorded here with its root cause, fix, and prevention so the
next cycle is one attempt.

## Failure 0 — PR CI: TDZ crash blanked the app at startup (the sneaky one)

The lineage-zoom PR failed the packaged interaction smoke 3/3 times with a
blank window: the tab bar seeded `$state` via `lineageScaleToPosition(1)`
during instance init while `const LINEAGE_ZOOM_MAX` was declared later in the
script — a temporal dead zone `ReferenceError` at component creation that took
down the whole `+page` mount. svelte-check and unit tests cannot see TDZ
ordering; the app rendered a blank window in every packaged/WebKWebView run.

**Debugging traps that cost hours (do not repeat):**

- The local smoke harness can report a bogus **PASS**: when a previous
  instance was killed, a stale single-instance registration makes the next
  launch exit 0 instantly (empty app log + instant exit = bounce, not a pass).
  Always check the app log has the watcher lines before trusting a local pass.
- The packaged release build cannot show WKWebView console output, so the
  driver's errors are invisible. Diagnose frontend crashes by loading the app
  with the E2E mock in a real browser (`CULL_E2E_MOCK=1 npx vite dev` +
  agent-browser) — the console shows the error in seconds. The packaged
  screenshot/OCR loop burned hours by comparison.
- An NSProcessInfo activity assertion (added to keep App Nap / WebProcess
  suspension from starving the driver on busy desktops) is still worth keeping,
  but it masked nothing: the real failure was deterministic JS.

**Fixes applied:** TDZ declaration order (PR #216), the
`CULL_NATIVE_SMOKE_ACTIVE` activity assertion, and an `app.html` error banner
that renders fatal frontend errors on-page so the smoke timeout screenshot
captures them.

**Prevention:** before pushing UI changes, load the app once with
`CULL_E2E_MOCK=1 npx vite dev` and check the console — module-init errors
appear immediately. Consider a browser-smoke step in CI for PRs that touch
app-shell components (TabBar/+page/persistence).

## Failure 1 — prepare gate: version-coupled docs not updated

`open-source-release-contract.test.ts` (HYG-006) requires SECURITY.md's
supported-versions table to name the new `X.Y.x` line once the version bump
lands. The bump happens mid-prepare, so the gap only surfaces inside the
prepare gate — after a full gate run.

**Fix applied:** SECURITY.md row landed on main before re-preparing.
**Prevention:** before running prepare on a minor/major, add the new
`X.Y.x` row to SECURITY.md (own PR) and skim every test that reads
`package.json` version (`rg -n "packageVersion|major" src/lib/*.contract.test.ts`).

## Failure 2 — tag burned by STALE_RELEASE_SOURCE (twice)

The workflow gate requires `origin/main` to be an ancestor of the tagged SHA at
workflow-run time and the tagged tree to carry the new version. Dependabot
auto-merge commits landed on main between tag push and the gate step (v0.6.0),
and again between the publish fix merging and the v0.6.1 dispatch. Tags are
immutable (protected-tags ruleset), so a burned tag means a new version number.

**Prevention (mandatory sequence):**

1. Merge the release PR.
2. `git fetch origin main && main_tip=$(git rev-parse origin/main)` — verify the
   tip IS the release PR merge commit (if another auto-merge landed, update the
   release branch and re-merge).
3. Verify no open PRs with auto-merge enabled are about to land
   (`gh pr list --state open`).
4. Re-anchor the record, then tag within seconds (see Failure 3).
5. Watch the run's gate step immediately; if STALE fires anyway, recover with a
   deeper version (v0.5.0 / v0.6.1 / v0.6.2 precedent) — never move a tag.

## Failure 3 — record anchor vs workflow gate (structural CLI bug, unfixed)

`runPrepare` records `releaseCommit` = pre-prepare `origin/main` tip, but the
release workflow gate requires the tagged SHA to be at-or-ahead of origin/main
**and** to carry the bumped version files — only the release PR's **merge
commit** satisfies both. `prepare`'s nextSteps hint even prints the bump commit
as `--expected-source`, which `runTag` rejects (SOURCE_MOVED), and tagging the
recorded anchor would ship a tree whose version files still say the old version
(VERSION_MISMATCH). v0.5.1 shipped only because its recovery re-prepared after
the merge.

**Working procedure until the CLI is fixed:** after the release PR merges,
re-anchor `.release-state/<version>.json`'s `releaseCommit` to the merge commit
(the cache is explicitly "a resumability cache; re-derive from external
evidence"), then `tag --expected-source <merge commit>`. Every gate still runs.

**Tracked as bd issue:** record anchor re-derivation + nextSteps hint fix.

## Failure 4 — publish could never pass (workflowRunId type drift)

c10cf8315 (Aug 20) made `verify-release-artifacts.sh` emit
`provenance.workflowRunId` as a **number**, but the publish job compared it
`!==` against the string `EXPECTED_RUN_ID` env — strict inequality, always
true, publication always exit 2. v0.5.1's verifier emitted a string, which is
why it was the last successful publish. Fixed by coercing both sides
(PR #212, `String(...)` on both).

**Prevention:** when a provenance/evidence field's type changes, grep the
publish job for comparisons against the same field
(`rg workflowRunId .github/workflows/release.yml`).

## Failure 5 — smoke gate could never find a closed bead

`queryReleaseIncidents()` used `bd list --json --limit 0`, and the installed bd
excludes closed issues by default — but the gate requires a **closed**
`cull-release-<version>-smoke` bead, so tagging always blocked with
`SMOKE_BEAD_MISSING`. Fixed by adding `--all` (PR #210).

**Prevention:** bd CLI default filters are part of the release contract; the
gate's fixture tests run with injected JSON (`CULL_RELEASE_TEST_MODE`), which
cannot catch real-bd drift. Run the tag command once against the real bd after
any bd upgrade.

## Failure 6 — disk gate (INSUFFICIENT_DISK)

Release gates (full preflight + golden cargo tests + production build in the
landing worktree) need ≥15 GiB; cargo `target/` dirs regrow to 7–11 GB per
build. The check is correct — build outputs must be pruned first.

**Prevention:** before check/prepare, delete regenerable `target/` dirs in the
main checkout, the landing worktree, and any feature worktrees.

## Failure 7 — dependabot auto-merge queue racing every PR

Every PR (release and fixes) hit `BEHIND` because queued dependabot auto-merges
kept advancing main mid-CI. Handling: `gh pr update-branch <n>`, re-watch, merge
the moment the state is CLEAN. Do not use `--admin` (gates are not bypassable).

## Cross-cutting norms reinforced by this cycle

- **Release notes are for end users.** The published body must cover the full
  delta since the last *public* release (not since the last tag), in plain
  language: features first, then improvements, then fixes; internal recovery
  story goes in one short "under the hood" paragraph. When a recovery folds
  unreleased internal versions (0.6.0/0.6.1 → 0.6.2), the notes must cover the
  whole folded delta.
- **Human smoke gate is per-version** — every recovery version re-triggers it.
  Build first, install via `scripts/install-local-build.sh`, refresh the smoke
  doc with the new binary SHA, close a fresh bead with
  `external_ref=cull-release-<version>-smoke`.
- **The bd Dolt DB is per-worktree.** Release gates run in the landing
  worktree; create/close smoke beads THERE, not in the main checkout.
- **The verifier wants exactly the 4 signed assets** in `--artifact-dir`;
  checksums.txt and release-provenance.json are outputs, not inputs.