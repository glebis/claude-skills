# release

A config-driven Claude Code skill that cuts software releases and maintains a
**tiered compatibility policy**. It bumps version files, runs a readiness gate,
updates a `COMPATIBILITY.md` (surfaces × tiers + deprecations), tags the release
(triggering your CI release workflow), and teaches the underlying standards as it
runs.

## Scope (honest)

Reference-tested on a **Tauri 2 + Rust + SvelteKit** desktop app
([Cull](https://github.com/glebis/cull)). It is generic **by config**
(`release.config.json`), but other stacks are not yet validated — treat first
runs elsewhere as `--dry-run`.

## Install

This skill lives in [`glebis/claude-skills`](https://github.com/glebis/claude-skills).
With the repo on your Claude Code skills path, invoke it as `/release`.

## Use

```
/release <patch|minor|major>
```

Requires a `release.config.json` at the repo root. Scaffold one from
`templates/release.config.json.tmpl`. Full field reference:
[`reference/config-schema.md`](reference/config-schema.md).

The engine (`scripts/release.py`) is stdlib-only Python and independently
runnable:

```bash
python3 scripts/release.py --config release.config.json plan minor   # preview
python3 scripts/release.py --config release.config.json bump  minor   # write versions
python3 -m unittest test_release -v                                   # 22 tests
```

## What it does, and why

The flow and its rationale are in [`SKILL.md`](SKILL.md). The standards it
encodes — SemVer, Go 1 compatibility promise, Kubernetes deprecation policy, SRE
Production-Readiness Review, Schema-Registry compatibility modes, Pact,
Keep a Changelog, RFC 9745/8594, MCP `protocolVersion` — are summarized with
links in [`reference/standards.md`](reference/standards.md).

## Files

| Path | Purpose |
|---|---|
| `SKILL.md` | the `/release` workflow + `--explain` lessons |
| `scripts/release.py` | the engine (pure functions + `plan`/`bump` CLI) |
| `scripts/test_release.py` | 22 unit tests |
| `reference/config-schema.md` | `release.config.json` reference |
| `reference/standards.md` | the standards map + links |
| `reference/compatibility-md.md` | how `COMPATIBILITY.md` is structured/updated |
| `templates/*.tmpl` | scaffolds for config, COMPATIBILITY, CONTRACTS |
