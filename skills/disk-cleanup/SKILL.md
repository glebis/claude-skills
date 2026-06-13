---
name: disk-cleanup
description: Scan and clean macOS caches, package-manager data, crash dumps, and app caches to reclaim disk space. Deterministic — a config registry (targets.json) plus two scripts (survey.py read-only, clean.py executor) do all the measuring and deleting; the agent only relays a compressed summary and makes the few human-judgment calls. IMPORTANT — use this skill whenever the user's request on macOS involves: freeing disk space, cleaning/clearing caches, "disk is full", "clean up my Mac", "free up space", "what's eating my disk", "running low on disk", needing space for an install, or any low-storage complaint. Covers the whole workflow survey → choose → clean → empty Trash.
---

# Disk Cleanup

**Deterministic by design.** All target knowledge lives in `targets.json`; all measuring and
deleting lives in `scripts/survey.py` (read-only) and `scripts/clean.py` (executor, **dry-run by
default**). They run headless with **zero dependencies** (stdlib only) — a user can run them in a
terminal without any agent. The agent's job is small: run the scripts, relay the compressed
output, and decide the handful of things that need human judgment.

## The two scripts

```bash
python3 scripts/survey.py            # read-only: sizes, risk, flags, uncategorized. Touches nothing.
python3 scripts/survey.py --json     # same, machine-readable (preferred for the agent)

python3 scripts/clean.py --preset safe              # DRY-RUN plan (default — nothing deleted)
python3 scripts/clean.py --preset safe --go         # execute (safe risk only)
python3 scripts/clean.py --preset full --allow-medium --go --empty-trash   # safe+medium, then empty Trash
python3 scripts/clean.py --ids cargo-registry-cache,go-mod-cache --go       # specific targets
python3 scripts/clean.py --preset safe --skip ollama-models --go            # exclude one
```

`trash` is used for all file removal (never `rm`); freed space sits in Trash until emptied
(`--empty-trash`, or the user empties it). Sizes are `du` estimates — approximate on APFS.

## Safety model (enforced in code, not prose)

- **Risk gating:** `safe` runs automatically; `medium` needs `--allow-medium`; `never` is
  refused even if named by id. `advisory` targets only print guidance, never execute.
- **Preflight on every trashed path:** canonical `realpath` → must resolve under an
  `allowed_roots` entry → must not be a symlink → never `$HOME` or `/`. Anything failing is
  skipped and reported, not deleted.
- **Dry-run by default:** `clean.py` prints the plan and touches nothing unless `--go`.

## Agent workflow

1. Run `python3 scripts/survey.py --json`. Relay the **compressed** summary: disk free,
   `safe`/`medium` recoverable totals, any `flags` (e.g. crash-loop), and the top targets.
   Do not dump the whole JSON.
2. **Auto-path:** for a plain "clean up safe stuff", show the `safe` total and run
   `clean.py --preset safe --go` (offer `--empty-trash`). Safe targets are regenerable.
3. **Escalate to the user ONLY for** (these are genuine judgment calls the scripts deliberately
   refuse to auto-decide):
   - `medium` targets (ML models, device support, project `node_modules`) — confirm before `--allow-medium`.
   - `uncategorized` discoveries — unknown dirs >100 MB; ask or investigate before adding.
   - `advisory` notes — surface them (Telegram cache, simulators via `simctl`, `uv/tools`,
     Chrome whole-dir, Xcode Archives); never act on them automatically.
   - surgical Docker / simulator decisions (see below).
4. Run `clean.py` with the resolved selection. Relay the result (`freed_human`, disk before→after).

## Maintaining the registry

Add or correct targets by editing `targets.json` — no code change needed. Each target:
`{id, category, risk, method, paths|find, regenerates, priority, note}`. Methods:
- `trash` — trash literal paths (globs allowed).
- `find-trash` — exact-name dir sweep with a `min_mb` floor (crash dumps, project `node_modules`).
- `command` — run a CLI (`npm cache clean`…); set `scope_path` so freed bytes can be measured.
- `simctl` — `xcrun simctl delete unavailable` (removes only sims for uninstalled runtimes; safe).
- `downloads-scan` — config-driven (`config.json` → `downloads_scan`): files older than `age_days`
  whose name doesn't match `exclude_patterns`. The dry-run **lists every file by name** for review.
- `advisory` — never executes; only prints guidance.

Keep installed software at `risk: never` (learned the hard way: `uv/tools`, `uv/python`,
`~/.rustup/toolchains`, `~/.bun`, `~/.deno` are NOT caches). Every non-advisory target's paths
must resolve under `allowed_roots` or preflight will (correctly) refuse them.

## Still agent-driven (only what genuinely can't be deterministic)

- **Docker only** — surgical and stateful: survey with `docker images` / `docker ps -as` /
  `docker system df -v`, let the user pick per-name (`docker rm`/`rmi`/`volume rm`/`builder prune`),
  or blunt `docker system prune -a -f`. A named volume removed = data gone; confirm by name.
  (Everything else — simulators via the `simctl` method, Downloads via `downloads-scan`,
  crash dumps, all caches — now runs through the scripts.)
