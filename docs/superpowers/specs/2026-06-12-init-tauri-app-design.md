# init-tauri-app — Design Spec

**Date:** 2026-06-12
**Status:** Draft for review
**Author:** Gleb + Claude (brainstormed)

## 1. Purpose

A Claude Code skill that scaffolds a new **Tauri v2** project pre-loaded with the
house conventions observed in two real apps (cenno, cull). It does **not** reinvent
Tauri boilerplate — it delegates that to the official scaffolder and layers
opinionated structure on top.

Out of scope: `init-xcode-app` (a separate, lighter skill specced later).

## 2. Approach: delegate + layer

```
npm create tauri-app   →   apply core layer   →   compose opt-in modules   →   verify (cargo check)
   (official, version-          (always)              (user-selected)              (correctness gate)
    current boilerplate +
    framework choice)
```

Rationale: Tauri owns the parts that churn with each release; the skill owns only
the durable conventions. Lowest maintenance burden.

## 3. Runtime flow

1. **Gather inputs** (via `AskUserQuestion`; cenno panel is an optional nicety, not a dependency):
   - App name (kebab-case)
   - Reverse-DNS identifier (e.g. `com.glebkalinin.<name>`)
   - Target directory (default: `~/ai_projects/<name>`)
   - **Frontend framework:** `react-ts` | `svelte-kit` | `vanilla-ts`
   - **Module toggles** (multi-select): CLI+MCP · SQLite · Tray/Updater · Release/Preflight · Swift sidecar (macOS)
2. **Scaffold base:**
   `npm create tauri-app@latest <name> -- --template <fw> --manager npm --yes`
   (fully non-interactive)
3. **Apply core layer** (always — see §4)
4. **Compose selected modules** (see §5)
5. **Verify:** `cargo check` in `src-tauri/` + `npm run build`; report pass/fail.
   Optional `git init` + first commit.

## 4. Core layer (always applied)

Durable conventions shared by cenno + cull:

- **`AGENTS.md`** — canonical agent guide (seeded from
  `~/.claude/templates/tauri-agent-starter/AGENTS.md`, which already exists)
- **`.claude/CLAUDE.md`** — one-line pointer to AGENTS.md
- **Layout:** `src/` (frontend) · `src-tauri/` (backend) · `docs/` · `scripts/`
- **`docs/internal/`** present and git-ignored; public `docs/*.md` tracked
- **House `.gitignore`:** `target/`, `build/`, `dist/`, `node_modules/`, `.svelte-kit/`,
  `.enzyme/`, `.enzyme-embeddings/`, `.beads/`, `.env` (keep `.env.example`),
  local `*.db`/`*.db-shm`/`*.db-wal`, `.DS_Store`
- **Toolchain pins:** `rust-toolchain.toml` (rustfmt + clippy) + `.node-version`
- **Baseline capability:** minimal `capabilities/default.json` (least privilege)
- **Version-sync script:** asserts `package.json` == `src-tauri/tauri.conf.json`
  (== `Cargo.toml` when present) — prevents release skew
- **`.mcp.json`:** the hypothesi `@hypothesi/tauri-mcp-server` dev server (project-scoped)
- **TypeScript strict** (`strict`, `noUnusedLocals`, `noUnusedParameters`)
- **README.md + CONTRIBUTING.md** stubs

## 5. Opt-in modules

Each module is a self-contained fragment: an AGENTS.md doc section + Rust module
stub(s) + Cargo deps + any capability/script/CI files.

| Module | Adds |
|---|---|
| **CLI + MCP server** | `src-tauri/src/cli/` (clap) + `src-tauri/src/mcp/` (rmcp); `--mcp-stdio`/`--mcp-http`/`ask` dispatch in `main.rs`; MCP capability. *The signature cenno/cull pattern.* |
| **SQLite + migrations** | `src-tauri/src/db_core/` (rusqlite, bundled driver) + migrations module + golden-fixture compat test scaffold |
| **Tray + autostart + updater** | tray module + `tauri-plugin-window-state` / `-autostart` / `-updater` (minisign); updater config in `tauri.conf.json` |
| **Release + preflight** | `scripts/preflight.sh` (hook/quick/full/release tiers) + `scripts/release.sh` (sign + notarize, env-secret based) + `.github/workflows/{ci,release}.yml` |
| **Swift sidecar** (macOS only) | `src-tauri/swift/Package.swift` (static-lib products) + `@_cdecl` entry-point stubs + `build.rs` (`swift-rs` linker + `-Wl,-rpath,/usr/lib/swift`) + Rust FFI module stub + kind-tag sync doc. *The cenno pattern for native macOS (Speech/CloudKit) from the Rust backend.* |

### 5.1 Composition mechanism (the one hard part)

Modules overlap on shared files: `Cargo.toml [dependencies]`, `lib.rs`
`generate_handler![...]`, `main.rs` CLI dispatch. **Chosen approach: agent-assembled
+ `cargo check` gate.** The skill ships each fragment plus explicit insertion
instructions; Claude merges them into the shared files intelligently, and
`cargo check` (run after composition) is the correctness gate. Rejected
alternatives: marker-comment injection (too rigid) and forced non-overlap
(constrains idiomatic output).

Risk: agent merge errors. Mitigation: the build gate catches compile breakage; the
skill instructs a `cargo check` after **each** module is applied, not just at the
end, so failures localize to the module that introduced them.

The **Swift sidecar** module additionally touches `build.rs` and adds the `swift/`
SPM tree; it is **macOS-gated** — the skill skips it (with a logged note) on
non-macOS hosts and when the Xcode command-line tools / Swift toolchain are absent,
since `cargo check` on that module requires them.

## 6. Decisions made (YAGNI defaults)

- **Design tokens:** plain CSS (`src/app.css`, cull-style, no build step). Cenno's
  style-dictionary/DTCG pipeline documented in AGENTS.md as an optional upgrade, not a toggle.
- **No `tauri-specta`/`ts-rs`** — hand-written IPC types, matching both apps. (Also:
  correct the existing `tauri-agent-starter` template, which wrongly recommended specta.)
- **npm**, not pnpm — matches both apps.
- Seed the core AGENTS.md from the existing `~/.claude/templates/tauri-agent-starter/`
  rather than rewriting.

## 7. Location & packaging

- Authored in `glebis/claude-skills` at `init-tauri-app/`
- `SKILL.md` (the procedure) + `assets/` holding:
  - `core/` — AGENTS.md seed, .gitignore, toolchain pins, capability baseline,
    version-sync script, .mcp.json, README/CONTRIBUTING stubs
  - `modules/{cli-mcp,sqlite,tray-updater,release-preflight,swift-sidecar}/` — per-module
    fragments + `INSERT.md` insertion instructions
- Installed to `~/.claude/skills/init-tauri-app/`

## 8. Verification / success criteria

A run is successful when, for any framework × any subset of modules:
- the project scaffolds without manual fixups,
- `cargo check` passes in `src-tauri/`,
- `npm run build` passes,
- `AGENTS.md` + `.claude/CLAUDE.md` exist with the pointer relationship,
- `.gitignore` and toolchain pins match the house style,
- version-sync script passes.

Manual test matrix before publish: `{react-ts, svelte-kit} × {no modules, all modules}`
= 4 smoke runs, each ending in green `cargo check` + `npm run build`. The
"all modules" runs include the Swift sidecar and therefore run on macOS with Xcode
CLT; a non-macOS run must confirm the sidecar is cleanly skipped (logged, no error).

## 9. Non-goals

- Xcode/Apple scaffolding (separate skill)
- Cross-platform Linux/Windows specifics beyond what the base template provides
- Design-token build pipeline (documented, not generated)
- App-specific logic from cenno/cull (e.g. a2ui, ONNX, image pipeline)
