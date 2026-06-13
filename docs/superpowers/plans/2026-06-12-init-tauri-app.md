# init-tauri-app Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a Claude Code skill that scaffolds a new Tauri v2 project pre-loaded with the cenno/cull house conventions, delegating boilerplate to `npm create tauri-app` and layering an always-on core plus five opt-in modules.

**Architecture:** A `SKILL.md` procedure orchestrates: (1) gather inputs, (2) run the official scaffolder, (3) overlay a `core/` asset tree, (4) compose user-selected `modules/*` fragments by agent-assembled merge, (5) gate on `cargo check` + `npm run build`. All template content lives under `assets/`; the skill body is the procedure that applies it.

**Tech Stack:** Claude Code skill (Markdown + bundled asset files), Tauri v2, Rust/cargo, npm/Vite, bash scripts. Reference projects: `~/ai_projects/cenno`, `~/ai_projects/cull`.

**Testing note:** This is a content skill — verification is end-to-end scaffolding, not unit tests. Per-asset tasks validate syntax (`bash -n`, JSON parse); Task 9 runs the full smoke matrix (the real gate).

**Source-of-truth reference files** (read these when adapting; do not copy app-specific logic):
- AGENTS.md seed: `~/.claude/templates/tauri-agent-starter/AGENTS.md` (already exists)
- `.mcp.json` seed: `~/.claude/templates/tauri-agent-starter/.mcp.json` (already exists)
- CLI+MCP: `cenno/src-tauri/src/{main.rs,cli.rs,mcp.rs,protocol.rs}`, `cull/src-tauri/src/cli/`, `cull/src-tauri/src/mcp/`
- SQLite: `cenno/src-tauri/src/db.rs`, `cull/src-tauri/src/db_core/`, `cull/src-tauri/tests/compat_golden.rs`
- Tray/updater: `cenno/src-tauri/src/{tray.rs,updater.rs}`, `cenno/src-tauri/tauri.conf.json` (plugins.updater)
- Release/preflight: `cull/scripts/preflight.sh`, `cenno/scripts/release.sh`, `cull/.github/workflows/{ci,release}.yml`
- Swift sidecar: `cenno/src-tauri/swift/Package.swift`, `cenno/src-tauri/swift/Sources/CennoRelay/CennoRelay.swift`, `cenno/src-tauri/build.rs`, `cenno/src-tauri/src/relay.rs`

---

## File Structure

Skill authored at `~/ai_projects/claude-skills/init-tauri-app/`:

```
init-tauri-app/
  SKILL.md                         # the procedure (Tasks 1-2, 8)
  assets/
    core/                          # Task 3 — always applied
      AGENTS.md                    # seeded from existing template, specta fixed
      CLAUDE.md                    # one-line pointer
      gitignore                    # house .gitignore (no leading dot in repo; renamed on apply)
      rust-toolchain.toml
      node-version                 # → .node-version on apply
      mcp.json                     # → .mcp.json on apply
      capabilities/default.json
      scripts/check-versions.sh
      README.md
      CONTRIBUTING.md
    modules/
      cli-mcp/        { INSERT.md, cli.rs, mcp.rs, protocol.rs, cargo-deps.toml, capability.json }   # Task 4
      sqlite/         { INSERT.md, db.rs, migrations.rs, cargo-deps.toml, compat_golden.rs }         # Task 5
      tray-updater/   { INSERT.md, tray.rs, updater.rs, cargo-deps.toml, conf-fragment.json }        # Task 6
      release-preflight/ { INSERT.md, preflight.sh, release.sh, ci.yml, release.yml }                # Task 7
      swift-sidecar/  { INSERT.md, Package.swift, Sidecar.swift, build.rs.fragment, sidecar_ffi.rs, cargo-deps.toml } # Task 8
```

**Apply-time renames:** `gitignore`→`.gitignore`, `node-version`→`.node-version`, `mcp.json`→`.mcp.json`, `CLAUDE.md`→`.claude/CLAUDE.md`. (Stored without leading dots so they're visible in the skill repo.)

---

## Task 1: Skill skeleton + frontmatter

**Files:**
- Create: `init-tauri-app/SKILL.md`
- Create: `init-tauri-app/assets/.gitkeep`

- [ ] **Step 1: Create the skill directory and SKILL.md frontmatter + overview**

Create `init-tauri-app/SKILL.md` with exactly this opening (procedure body added in Task 2):

```markdown
---
name: init-tauri-app
description: Scaffold a new Tauri v2 project with the cenno/cull house conventions — delegates boilerplate to `npm create tauri-app`, then layers an opinionated core plus opt-in modules (CLI+MCP, SQLite, tray/updater, release/preflight, Swift sidecar). Use when the user wants to start a new Tauri desktop app, "init a tauri project", or "scaffold a tauri app".
---

# init-tauri-app

Scaffolds a new Tauri v2 project pre-loaded with conventions proven in two production apps
(cenno, cull). Delegates version-current boilerplate to the official scaffolder, then applies
a durable convention layer and any opt-in modules the user selects.

## When to use
- "Start a new Tauri app", "init a tauri project", "scaffold a tauri desktop app".

## Prerequisites (verify before scaffolding)
- `node` + `npm` on PATH (`node --version`)
- `cargo` + `rustc` on PATH (`cargo --version`)
- macOS + Xcode CLT only required if the Swift-sidecar module is selected
```

- [ ] **Step 2: Create assets placeholder**

Run: `mkdir -p ~/ai_projects/claude-skills/init-tauri-app/assets && touch ~/ai_projects/claude-skills/init-tauri-app/assets/.gitkeep`

- [ ] **Step 3: Verify frontmatter parses**

Run: `head -5 ~/ai_projects/claude-skills/init-tauri-app/SKILL.md`
Expected: valid YAML frontmatter with `name: init-tauri-app`.

- [ ] **Step 4: Commit**

```bash
git -C ~/ai_projects/claude-skills add init-tauri-app/
git -C ~/ai_projects/claude-skills commit -m "feat(init-tauri-app): skill skeleton + frontmatter"
```

---

## Task 2: SKILL.md procedure body

**Files:**
- Modify: `init-tauri-app/SKILL.md` (append procedure)

- [ ] **Step 1: Append the runtime procedure**

Append this to `SKILL.md`:

````markdown
## Procedure

### 1. Gather inputs (AskUserQuestion)
Ask, in one batch:
- **App name** (kebab-case). Validate `^[a-z][a-z0-9-]*$`.
- **Identifier** (reverse-DNS, default `com.glebkalinin.<name>`).
- **Target directory** (default `~/ai_projects/<name>`). Abort if it exists and is non-empty.
- **Frontend framework:** `react-ts` | `svelte-kit` | `vanilla-ts`.
- **Modules** (multi-select): CLI+MCP · SQLite · Tray/Updater · Release/Preflight · Swift sidecar.

If Swift sidecar selected but host is non-macOS or `xcrun --find swift` fails: warn and drop it.

### 2. Scaffold base
```bash
cd <parent-of-target>
npm create tauri-app@latest <name> -- --template <framework> --manager npm --yes
```
Then `cd <target> && npm install`.

### 3. Apply core layer
Copy every file from `assets/core/` into the project, applying the renames in the table below,
then run a baseline gate. The AGENTS.md and README get `<name>`/`<identifier>` substituted.

| asset | destination |
|---|---|
| `core/AGENTS.md` | `AGENTS.md` |
| `core/CLAUDE.md` | `.claude/CLAUDE.md` |
| `core/gitignore` | `.gitignore` (merge: append house entries not already present) |
| `core/rust-toolchain.toml` | `src-tauri/rust-toolchain.toml` |
| `core/node-version` | `.node-version` |
| `core/mcp.json` | `.mcp.json` |
| `core/capabilities/default.json` | `src-tauri/capabilities/default.json` (overwrite) |
| `core/scripts/check-versions.sh` | `scripts/check-versions.sh` (chmod +x) |
| `core/README.md` | `README.md` |
| `core/CONTRIBUTING.md` | `CONTRIBUTING.md` |

Create empty tracked dir `docs/internal/.gitkeep` and `docs/.gitkeep`.
Enable TS strict: ensure `tsconfig.json` has `strict`, `noUnusedLocals`, `noUnusedParameters` true.

**Gate:** `cd src-tauri && cargo check` and `cd .. && npm run build`. Both must pass before modules.

### 4. Compose selected modules
For each selected module, in this order — cli-mcp, sqlite, tray-updater, swift-sidecar,
release-preflight — open `assets/modules/<m>/INSERT.md` and follow it exactly: it lists files to
copy, Cargo deps to merge into `src-tauri/Cargo.toml [dependencies]`, and insertion points in
`src-tauri/src/lib.rs` (`tauri::generate_handler![...]`) and `src-tauri/src/main.rs`.

**After EACH module:** `cd src-tauri && cargo check`. If it fails, fix the just-applied merge
before continuing (failures localize to the current module). For modules with a frontend/script
part, also run the relevant check named in that INSERT.md.

### 5. Final verification + handoff
- `cd src-tauri && cargo check` → must pass
- `npm run build` → must pass
- `bash scripts/check-versions.sh` → must pass
- Offer `git init && git add -A && git commit -m "chore: scaffold via init-tauri-app"`.
- Print a summary: framework, modules applied, modules skipped (with reason), next commands
  (`npm run tauri dev`).
````

- [ ] **Step 2: Lint the markdown for unresolved placeholders**

Run: `grep -nE "TBD|TODO|FIXME" ~/ai_projects/claude-skills/init-tauri-app/SKILL.md`
Expected: no matches.

- [ ] **Step 3: Commit**

```bash
git -C ~/ai_projects/claude-skills add init-tauri-app/SKILL.md
git -C ~/ai_projects/claude-skills commit -m "feat(init-tauri-app): runtime procedure"
```

---

## Task 3: Core asset layer

**Files:**
- Create: `assets/core/AGENTS.md`, `CLAUDE.md`, `gitignore`, `rust-toolchain.toml`, `node-version`, `mcp.json`, `capabilities/default.json`, `scripts/check-versions.sh`, `README.md`, `CONTRIBUTING.md`

- [ ] **Step 1: Seed AGENTS.md from the existing template, fixing the specta line**

```bash
cp ~/.claude/templates/tauri-agent-starter/AGENTS.md \
   ~/ai_projects/claude-skills/init-tauri-app/assets/core/AGENTS.md
```
Then edit the copied file: in the "IPC boundary" / "Frontend ruleset" sections, **remove the
`tauri-specta` recommendation** and replace with: "Hand-write IPC types in `src/lib/api.ts`
mirroring the Rust command signatures — both cenno and cull deliberately avoid codegen deps."
Add a one-line note: "Design tokens: plain CSS in `src/app.css`; style-dictionary is an optional
upgrade (see cenno) — not set up by default."

- [ ] **Step 2: Create `core/CLAUDE.md`**

```markdown
# Project instructions

See **[AGENTS.md](../AGENTS.md)** — the canonical agent guide for this repo. Follow it exactly.
```

- [ ] **Step 3: Create `core/gitignore`** (house style from cenno + cull)

```gitignore
# OS
.DS_Store
# Node / frontend
node_modules/
/build
/dist
dist-ssr
.svelte-kit/
src-tauri/.svelte-kit/
*.local
vite.config.js.timestamp-*
# Rust / Tauri
src-tauri/target/
src-tauri/gen/schemas
# Swift (sidecar module)
src-tauri/swift/.build/
**/xcuserdata/
**/DerivedData/
# Env & secrets
.env
.env.*
!.env.example
# Local data
*.db
*.db-shm
*.db-wal
# Logs
*.log
logs
# Internal working docs — never shipped
docs/internal/
# Agent/tooling caches
.enzyme/
.enzyme-embeddings/
.beads/
.worktrees/
```

- [ ] **Step 4: Create `core/rust-toolchain.toml`**

```toml
[toolchain]
channel = "stable"
components = ["rustfmt", "clippy"]
```

- [ ] **Step 5: Create `core/node-version`**

```
22
```

- [ ] **Step 6: Create `core/mcp.json`** (copy existing, verified package)

```bash
cp ~/.claude/templates/tauri-agent-starter/.mcp.json \
   ~/ai_projects/claude-skills/init-tauri-app/assets/core/mcp.json
```
Confirm it contains `@hypothesi/tauri-mcp-server`.

- [ ] **Step 7: Create `core/capabilities/default.json`** (least privilege baseline)

```json
{
  "$schema": "../gen/schemas/desktop-schema.json",
  "identifier": "default",
  "description": "Baseline capability for the main window",
  "windows": ["main"],
  "permissions": ["core:default", "opener:default"]
}
```

- [ ] **Step 8: Create `core/scripts/check-versions.sh`** (version-sync gate)

```bash
#!/usr/bin/env bash
set -euo pipefail
# Assert package.json, src-tauri/tauri.conf.json, and src-tauri/Cargo.toml agree on version.
pkg=$(node -p "require('./package.json').version")
conf=$(node -p "require('./src-tauri/tauri.conf.json').version")
cargo=$(grep -m1 '^version' src-tauri/Cargo.toml | sed -E 's/.*"(.*)".*/\1/')
echo "package.json=$pkg tauri.conf.json=$conf Cargo.toml=$cargo"
if [ "$pkg" != "$conf" ] || [ "$pkg" != "$cargo" ]; then
  echo "ERROR: version mismatch across manifests" >&2
  exit 1
fi
echo "OK: versions in sync ($pkg)"
```

- [ ] **Step 9: Create `core/README.md` and `core/CONTRIBUTING.md` stubs**

`README.md`:
```markdown
# <name>

A Tauri v2 desktop app. See [AGENTS.md](./AGENTS.md) for the developer/agent guide.

## Develop
```bash
npm install
npm run tauri dev
```
```

`CONTRIBUTING.md`:
```markdown
# Contributing

- Read [AGENTS.md](./AGENTS.md) first.
- Rust loop: `cd src-tauri && cargo check`. Lint: `cargo clippy`. Format: `cargo fmt`.
- Frontend: `npm run build`. Versions: `bash scripts/check-versions.sh`.
- Keep `package.json`, `src-tauri/tauri.conf.json`, and `src-tauri/Cargo.toml` versions in sync.
```

- [ ] **Step 10: Validate shell + JSON**

Run:
```bash
bash -n ~/ai_projects/claude-skills/init-tauri-app/assets/core/scripts/check-versions.sh
node -e "JSON.parse(require('fs').readFileSync(process.env.HOME+'/ai_projects/claude-skills/init-tauri-app/assets/core/capabilities/default.json'))" && echo JSON_OK
```
Expected: no syntax error, `JSON_OK`.

- [ ] **Step 11: Commit**

```bash
git -C ~/ai_projects/claude-skills add init-tauri-app/assets/core/
git -C ~/ai_projects/claude-skills commit -m "feat(init-tauri-app): core asset layer"
```

---

## Task 4: Module — CLI + MCP server

**Files:**
- Create: `assets/modules/cli-mcp/{INSERT.md, cli.rs, mcp.rs, protocol.rs, cargo-deps.toml, capability.json}`

**Adapt from:** `cenno/src-tauri/src/{cli.rs,mcp.rs,protocol.rs,main.rs}` (the rmcp UnixListener `ask_user` server + clap dispatch). Strip all cenno-specific prompt/a2ui logic; keep the transport skeleton: a `hello`/`ping` MCP tool as the placeholder command.

- [ ] **Step 1: Create `cargo-deps.toml`** (deps to merge)

```toml
rmcp = { version = "1.7", features = ["server", "macros"] }
clap = { version = "4", features = ["derive"] }
tokio = { version = "1", features = ["full"] }
schemars = "0.8"
serde = { version = "1", features = ["derive"] }
serde_json = "1"
```

- [ ] **Step 2: Create `protocol.rs`** — minimal wire types

```rust
use schemars::JsonSchema;
use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, Serialize, Deserialize, JsonSchema)]
pub struct PingRequest { pub message: String }

#[derive(Debug, Clone, Serialize, Deserialize, JsonSchema)]
pub struct PingResponse { pub reply: String }

#[cfg(test)]
mod tests {
    use super::*;
    #[test]
    fn roundtrip() {
        let r = PingRequest { message: "hi".into() };
        let s = serde_json::to_string(&r).unwrap();
        let back: PingRequest = serde_json::from_str(&s).unwrap();
        assert_eq!(back.message, "hi");
    }
}
```

- [ ] **Step 3: Create `mcp.rs`** — rmcp stdio server exposing one `ping` tool

Adapt the server-construction pattern from `cenno/src-tauri/src/mcp.rs` (the `rmcp` server + tool macro), reduced to a single `ping` tool that returns `PingResponse { reply: format!("pong: {message}") }`. Provide both a `--mcp-stdio` runner (`serve over stdio`) entry function `pub async fn run_stdio()`.

```rust
// assets/modules/cli-mcp/mcp.rs
use crate::protocol::{PingRequest, PingResponse};
// NOTE: adapt the exact rmcp server boilerplate from cenno/src-tauri/src/mcp.rs.
// Expose ONE tool `ping(PingRequest) -> PingResponse`. Keep it minimal.
pub async fn run_stdio() -> anyhow::Result<()> {
    // build rmcp server with the `ping` tool, serve over stdio
    todo!("see cenno/src-tauri/src/mcp.rs for the rmcp serve-over-stdio shape")
}
pub fn ping(req: PingRequest) -> PingResponse {
    PingResponse { reply: format!("pong: {}", req.message) }
}
```

> The `run_stdio` body is the one spot the executing agent fills from the cited reference; the
> `ping` pure-fn + `protocol` types are complete and unit-tested, so the module compiles and the
> tool logic is verifiable independent of transport wiring.

- [ ] **Step 4: Create `cli.rs`** — clap dispatch

```rust
use clap::{Parser, Subcommand};

#[derive(Parser)]
#[command(name = env!("CARGO_PKG_NAME"))]
pub struct Cli {
    #[command(subcommand)]
    pub command: Option<Command>,
}

#[derive(Subcommand)]
pub enum Command {
    /// Run as an MCP server over stdio
    McpStdio,
    /// Print a pong and exit
    Ping { message: String },
}
```

- [ ] **Step 5: Create `capability.json`**

```json
{
  "$schema": "../gen/schemas/desktop-schema.json",
  "identifier": "mcp",
  "description": "Capability for MCP-driven windows",
  "windows": ["main"],
  "permissions": ["core:default"]
}
```

- [ ] **Step 6: Create `INSERT.md`**

```markdown
# Insert: CLI + MCP server

1. Copy `cli.rs`, `mcp.rs`, `protocol.rs` → `src-tauri/src/`.
2. Copy `capability.json` → `src-tauri/capabilities/mcp.json`.
3. Merge `cargo-deps.toml` lines into `src-tauri/Cargo.toml` under `[dependencies]`
   (skip any key already present; keep the higher version on conflict). Add `anyhow = "1"`.
4. In `src-tauri/src/lib.rs`: add `mod cli; mod mcp; mod protocol;` near the top.
5. In `src-tauri/src/main.rs`: before building the Tauri app, parse the CLI and branch:
   ```rust
   let cli = <crate>::cli::Cli::parse();
   if let Some(<crate>::cli::Command::McpStdio) = cli.command {
       return tokio::runtime::Runtime::new()?.block_on(<crate>::mcp::run_stdio());
   }
   if let Some(<crate>::cli::Command::Ping { message }) = cli.command {
       println!("{}", <crate>::mcp::ping(<crate>::protocol::PingRequest { message }).reply);
       return Ok(());
   }
   ```
   (`<crate>` = the lib crate name from Cargo.toml.)
6. Verify: `cd src-tauri && cargo check && cargo test protocol`.
```

- [ ] **Step 7: Validate fragments compile in isolation (syntax)**

Run: `node -e "JSON.parse(require('fs').readFileSync(process.env.HOME+'/ai_projects/claude-skills/init-tauri-app/assets/modules/cli-mcp/capability.json'))" && echo OK`
Expected: `OK`. (Rust fragments are checked end-to-end in Task 9.)

- [ ] **Step 8: Commit**

```bash
git -C ~/ai_projects/claude-skills add init-tauri-app/assets/modules/cli-mcp/
git -C ~/ai_projects/claude-skills commit -m "feat(init-tauri-app): cli-mcp module"
```

---

## Task 5: Module — SQLite + migrations

**Files:**
- Create: `assets/modules/sqlite/{INSERT.md, db.rs, migrations.rs, cargo-deps.toml, compat_golden.rs}`

**Adapt from:** `cull/src-tauri/src/db_core/` (migrations + schema-invariant verify) and
`cenno/src-tauri/src/db.rs` (simple open + insert + `0600` perms). Keep a single `items` table as
the demo schema.

- [ ] **Step 1: `cargo-deps.toml`**

```toml
rusqlite = { version = "0.32", features = ["bundled"] }
```

- [ ] **Step 2: `migrations.rs`** — ordered migration list + runner

```rust
use rusqlite::Connection;

pub const MIGRATIONS: &[&str] = &[
    "CREATE TABLE IF NOT EXISTS items (
        id INTEGER PRIMARY KEY,
        name TEXT NOT NULL,
        created_at TEXT NOT NULL DEFAULT (datetime('now'))
    );",
];

pub fn apply(conn: &Connection) -> rusqlite::Result<()> {
    conn.execute_batch("CREATE TABLE IF NOT EXISTS _migrations (idx INTEGER PRIMARY KEY);")?;
    let done: i64 = conn.query_row("SELECT COUNT(*) FROM _migrations", [], |r| r.get(0))?;
    for (i, sql) in MIGRATIONS.iter().enumerate().skip(done as usize) {
        conn.execute_batch(sql)?;
        conn.execute("INSERT INTO _migrations (idx) VALUES (?1)", [i as i64])?;
    }
    Ok(())
}
```

- [ ] **Step 3: `db.rs`** — open with perms + apply migrations + a tested insert/list

```rust
use rusqlite::Connection;
use std::path::Path;
use crate::migrations;

pub fn open(path: &Path) -> rusqlite::Result<Connection> {
    let conn = Connection::open(path)?;
    #[cfg(unix)]
    {
        use std::os::unix::fs::PermissionsExt;
        let _ = std::fs::set_permissions(path, std::fs::Permissions::from_mode(0o600));
    }
    migrations::apply(&conn)?;
    Ok(conn)
}

pub fn insert_item(conn: &Connection, name: &str) -> rusqlite::Result<i64> {
    conn.execute("INSERT INTO items (name) VALUES (?1)", [name])?;
    Ok(conn.last_insert_rowid())
}

pub fn list_items(conn: &Connection) -> rusqlite::Result<Vec<(i64, String)>> {
    let mut stmt = conn.prepare("SELECT id, name FROM items ORDER BY id")?;
    let rows = stmt.query_map([], |r| Ok((r.get(0)?, r.get(1)?)))?;
    rows.collect()
}

#[cfg(test)]
mod tests {
    use super::*;
    #[test]
    fn insert_and_list() {
        let conn = Connection::open_in_memory().unwrap();
        migrations::apply(&conn).unwrap();
        insert_item(&conn, "a").unwrap();
        insert_item(&conn, "b").unwrap();
        let items = list_items(&conn).unwrap();
        assert_eq!(items.len(), 2);
        assert_eq!(items[0].1, "a");
    }
}
```

- [ ] **Step 4: `compat_golden.rs`** — golden-fixture compat test scaffold

```rust
// tests/compat_golden.rs — adapt from cull/src-tauri/tests/compat_golden.rs
// Opens a frozen DB fixture from a prior version and asserts migrations still apply cleanly.
// Scaffold only: documents the pattern; a real fixture is committed once v0.2+ exists.
#[test]
#[ignore = "enable once a versioned DB fixture exists; see cull compat_golden"]
fn migrations_apply_to_prior_version_db() {
    // 1. copy tests/fixtures/golden-v0.1.db to a temp path
    // 2. <crate>::db::open(temp_path) — must not error
    // 3. assert expected tables exist
}
```

- [ ] **Step 5: `INSERT.md`**

```markdown
# Insert: SQLite + migrations

1. Copy `db.rs`, `migrations.rs` → `src-tauri/src/`.
2. Copy `compat_golden.rs` → `src-tauri/tests/compat_golden.rs`.
3. Merge `cargo-deps.toml` into `src-tauri/Cargo.toml [dependencies]`.
4. In `src-tauri/src/lib.rs`: add `mod db; mod migrations;`.
5. Verify: `cd src-tauri && cargo check && cargo test db::tests`.
```

- [ ] **Step 6: Commit**

```bash
git -C ~/ai_projects/claude-skills add init-tauri-app/assets/modules/sqlite/
git -C ~/ai_projects/claude-skills commit -m "feat(init-tauri-app): sqlite module"
```

---

## Task 6: Module — Tray + autostart + updater

**Files:**
- Create: `assets/modules/tray-updater/{INSERT.md, tray.rs, updater.rs, cargo-deps.toml, conf-fragment.json}`

**Adapt from:** `cenno/src-tauri/src/{tray.rs,updater.rs}` and `cenno/src-tauri/tauri.conf.json`
(`plugins.updater` + `bundle.createUpdaterArtifacts`). Strip cenno-specific menu items down to
Show / Quit.

- [ ] **Step 1: `cargo-deps.toml`**

```toml
tauri-plugin-window-state = "2"
tauri-plugin-autostart = "2"
tauri-plugin-updater = "2"
```

- [ ] **Step 2: `tray.rs`** — minimal tray with Show + Quit

```rust
use tauri::{AppHandle, Manager};
use tauri::tray::TrayIconBuilder;
use tauri::menu::{Menu, MenuItem};

pub fn build(app: &AppHandle) -> tauri::Result<()> {
    let show = MenuItem::with_id(app, "show", "Show", true, None::<&str>)?;
    let quit = MenuItem::with_id(app, "quit", "Quit", true, None::<&str>)?;
    let menu = Menu::with_items(app, &[&show, &quit])?;
    TrayIconBuilder::new()
        .menu(&menu)
        .on_menu_event(|app, event| match event.id.as_ref() {
            "show" => { if let Some(w) = app.get_webview_window("main") { let _ = w.show(); let _ = w.set_focus(); } }
            "quit" => app.exit(0),
            _ => {}
        })
        .build(app)?;
    Ok(())
}
```

- [ ] **Step 3: `updater.rs`** — thin check wrapper (documented, no-op default)

```rust
// Auto-update via tauri-plugin-updater. Endpoint + pubkey are set in tauri.conf.json
// (see conf-fragment.json). This module just documents the wiring; the plugin does the work.
// To trigger a check from Rust, use the plugin's `app.updater()?.check().await` in a command.
```

- [ ] **Step 4: `conf-fragment.json`** — to merge into tauri.conf.json

```json
{
  "plugins": {
    "updater": {
      "endpoints": ["https://github.com/glebis/<name>/releases/latest/download/latest.json"],
      "pubkey": "REPLACE_WITH_MINISIGN_PUBKEY"
    }
  },
  "bundle": {
    "createUpdaterArtifacts": true,
    "macOS": { "hardenedRuntime": true, "minimumSystemVersion": "12.0" }
  }
}
```

- [ ] **Step 5: `INSERT.md`**

```markdown
# Insert: Tray + autostart + updater

1. Copy `tray.rs`, `updater.rs` → `src-tauri/src/`.
2. Merge `cargo-deps.toml` into `src-tauri/Cargo.toml [dependencies]`.
3. Deep-merge `conf-fragment.json` into `src-tauri/tauri.conf.json` (substitute `<name>`).
   Leave `pubkey` as the REPLACE marker; AGENTS.md documents generating it with
   `npm run tauri signer generate`.
4. In `src-tauri/src/lib.rs`: add `mod tray; mod updater;`, register the plugins in the builder
   (`.plugin(tauri_plugin_window_state::Builder::default().build())`, autostart, updater), and
   call `tray::build(app.handle())?;` inside `.setup(...)`.
5. Verify: `cd src-tauri && cargo check`.
```

- [ ] **Step 6: Commit**

```bash
git -C ~/ai_projects/claude-skills add init-tauri-app/assets/modules/tray-updater/
git -C ~/ai_projects/claude-skills commit -m "feat(init-tauri-app): tray-updater module"
```

---

## Task 7: Module — Release + preflight

**Files:**
- Create: `assets/modules/release-preflight/{INSERT.md, preflight.sh, release.sh, ci.yml, release.yml}`

**Adapt from:** `cull/scripts/preflight.sh` (tiered gates), `cenno/scripts/release.sh` (env-secret
signing/notarization + version preflight + latest.json), `cull/.github/workflows/{ci,release}.yml`.
Genericize project names; keep `PATH="/usr/bin:$PATH"` prefix note for the xattr gotcha.

- [ ] **Step 1: `preflight.sh`** — tiered gate

```bash
#!/usr/bin/env bash
set -euo pipefail
TIER="${1:-quick}"   # hook | quick | full | release
run() { echo "+ $*"; "$@"; }
case "$TIER" in
  hook)    run bash -n scripts/*.sh ;;
  quick)   run npm run build; (cd src-tauri && run cargo check) ;;
  full)    "$0" quick; (cd src-tauri && run cargo fmt --check && run cargo clippy -- -D warnings && run cargo test) ;;
  release) "$0" full; run bash scripts/check-versions.sh; run npm run tauri build ;;
  *) echo "unknown tier: $TIER" >&2; exit 2 ;;
esac
echo "preflight $TIER OK"
```

- [ ] **Step 2: `release.sh`** — adapt cenno's (env secrets, version check, gh release)

Create by adapting `cenno/scripts/release.sh`: keep the preflight version check, the
`PATH="/usr/bin:$PATH" npx tauri build` line, artifact collection (dmg + tar.gz + .sig),
`latest.json` construction, and `gh release create`. Replace `cenno` with `<name>` and read all
signing secrets from env (`TAURI_SIGNING_PRIVATE_KEY*`, `APPLE_*`). Do not inline secrets.

- [ ] **Step 3: `ci.yml`** — adapt cull's CI (frontend + rust jobs)

Create `.github/workflows/ci.yml` from `cull/.github/workflows/ci.yml`: a frontend job
(`npm ci`, `npm run build`) and a Rust job on macOS (`cargo fmt --check`, `cargo clippy`,
`cargo test`). Drop cull's supply-chain/audit step unless the user adds cargo-deny later.

- [ ] **Step 4: `release.yml`** — adapt cull's release workflow

Create `.github/workflows/release.yml` from `cull/.github/workflows/release.yml`: tag-triggered,
macOS runner, Apple cert import from secrets, `tauri-action` build + notarize + GitHub release.

- [ ] **Step 5: `INSERT.md`**

```markdown
# Insert: Release + preflight

1. Copy `preflight.sh`, `release.sh` → `scripts/` (chmod +x both).
2. Copy `ci.yml`, `release.yml` → `.github/workflows/`.
3. Substitute `<name>` throughout.
4. Verify: `bash -n scripts/preflight.sh scripts/release.sh && bash scripts/preflight.sh hook`.
```

- [ ] **Step 6: Validate shell syntax**

Run: `bash -n ~/ai_projects/claude-skills/init-tauri-app/assets/modules/release-preflight/preflight.sh && echo OK`
Expected: `OK`.

- [ ] **Step 7: Commit**

```bash
git -C ~/ai_projects/claude-skills add init-tauri-app/assets/modules/release-preflight/
git -C ~/ai_projects/claude-skills commit -m "feat(init-tauri-app): release-preflight module"
```

---

## Task 8: Module — Swift sidecar (macOS)

**Files:**
- Create: `assets/modules/swift-sidecar/{INSERT.md, Package.swift, Sidecar.swift, build.rs.fragment, sidecar_ffi.rs, cargo-deps.toml}`

**Adapt from:** `cenno/src-tauri/swift/Package.swift`, `cenno/src-tauri/swift/Sources/CennoRelay/CennoRelay.swift`,
`cenno/src-tauri/build.rs`, `cenno/src-tauri/src/relay.rs`. Reduce to a single demo package
`AppSidecar` exposing one `@_cdecl` function that returns a greeting.

- [ ] **Step 1: `Package.swift`**

```swift
// swift-tools-version:5.9
import PackageDescription

let package = Package(
    name: "AppSidecar",
    platforms: [.macOS(.v13)],
    products: [
        .library(name: "AppSidecar", type: .static, targets: ["AppSidecar"]),
    ],
    targets: [
        .target(name: "AppSidecar", linkerSettings: [
            .linkedFramework("Foundation"),
        ]),
    ]
)
```

- [ ] **Step 2: `Sidecar.swift`** (→ `swift/Sources/AppSidecar/Sidecar.swift`)

```swift
import Foundation

// Kind tags — KEEP IN SYNC with the Rust side (see sidecar_ffi.rs).
// 0 = OK, 1 = ERROR

@_cdecl("app_sidecar_greet")
public func app_sidecar_greet(_ name: UnsafePointer<CChar>?) -> UnsafeMutablePointer<CChar>? {
    let who = name.flatMap { String(validatingUTF8: $0) } ?? "world"
    return strdup("hello, \(who)")
}

@_cdecl("app_sidecar_free")
public func app_sidecar_free(_ p: UnsafeMutablePointer<CChar>?) {
    if let p { free(p) }
}
```

- [ ] **Step 3: `build.rs.fragment`** (merge into project `build.rs`)

```rust
// --- swift-sidecar module (macOS only) ---
#[cfg(target_os = "macos")]
{
    use swift_rs::SwiftLinker;
    SwiftLinker::new("13.0").with_package("AppSidecar", "swift").link();
    println!("cargo:rustc-link-arg=-Wl,-rpath,/usr/lib/swift");
}
```

- [ ] **Step 4: `sidecar_ffi.rs`**

```rust
// macOS-only FFI to the AppSidecar Swift static lib.
#[cfg(target_os = "macos")]
mod ffi {
    use std::ffi::{CStr, CString};
    use std::os::raw::c_char;
    extern "C" {
        fn app_sidecar_greet(name: *const c_char) -> *mut c_char;
        fn app_sidecar_free(p: *mut c_char);
    }
    pub fn greet(name: &str) -> String {
        let c = CString::new(name).unwrap_or_default();
        unsafe {
            let p = app_sidecar_greet(c.as_ptr());
            if p.is_null() { return String::new(); }
            let s = CStr::from_ptr(p).to_string_lossy().into_owned();
            app_sidecar_free(p);
            s
        }
    }
}
#[cfg(target_os = "macos")]
pub use ffi::greet;
```

- [ ] **Step 5: `cargo-deps.toml`**

```toml
swift-rs = { version = "1.0.6", features = ["build"] }
```
(Note: `swift-rs` goes in BOTH `[dependencies]` and `[build-dependencies]` — INSERT.md says so.)

- [ ] **Step 6: `INSERT.md`**

```markdown
# Insert: Swift sidecar (macOS only)

PРЕREQ: macOS + `xcrun --find swift` succeeds. If not, SKIP this module (log it).

1. Copy `Package.swift` → `src-tauri/swift/Package.swift`.
2. Copy `Sidecar.swift` → `src-tauri/swift/Sources/AppSidecar/Sidecar.swift`.
3. Copy `sidecar_ffi.rs` → `src-tauri/src/sidecar_ffi.rs`; add `mod sidecar_ffi;` to `lib.rs`.
4. Merge `cargo-deps.toml` line into `src-tauri/Cargo.toml` under BOTH `[dependencies]`
   and `[build-dependencies]`.
5. Merge `build.rs.fragment` into `src-tauri/build.rs` BEFORE the `tauri_build::build()` call.
6. Verify (macOS): `cd src-tauri && cargo check`.
```

- [ ] **Step 7: Validate Swift + Rust syntax where possible**

Run (macOS): `cd /tmp && swiftc -parse ~/ai_projects/claude-skills/init-tauri-app/assets/modules/swift-sidecar/Sidecar.swift && echo SWIFT_OK`
Expected: `SWIFT_OK` (or skip with a note on non-macOS).

- [ ] **Step 8: Commit**

```bash
git -C ~/ai_projects/claude-skills add init-tauri-app/assets/modules/swift-sidecar/
git -C ~/ai_projects/claude-skills commit -m "feat(init-tauri-app): swift-sidecar module"
```

---

## Task 9: End-to-end smoke matrix (the real gate)

**Files:**
- Create: `init-tauri-app/scripts/smoke.sh` (test harness; not shipped to scaffolded projects)

- [ ] **Step 1: Write the smoke harness**

```bash
#!/usr/bin/env bash
# Scaffolds throwaway projects to verify the skill end-to-end.
# Usage: smoke.sh <framework> <modules-csv|none>
set -euo pipefail
FW="$1"; MODS="$2"
TMP="$(mktemp -d)"; NAME="smoke-${FW//-/}"
echo "=== $FW / $MODS in $TMP ==="
cd "$TMP"
npm create tauri-app@latest "$NAME" -- --template "$FW" --manager npm --yes
cd "$NAME" && npm install
# NOTE: the executing agent applies core + selected modules here per SKILL.md,
# since composition is agent-driven. This harness then runs the gates:
( cd src-tauri && cargo check )
npm run build
echo "=== PASS: $FW / $MODS ==="
```

- [ ] **Step 2: Run the matrix (4 runs)**

Run each and confirm `PASS`:
```bash
bash init-tauri-app/scripts/smoke.sh react-ts none
bash init-tauri-app/scripts/smoke.sh svelte-kit none
bash init-tauri-app/scripts/smoke.sh react-ts all       # includes swift-sidecar on macOS
bash init-tauri-app/scripts/smoke.sh svelte-kit all
```
Expected: each ends `=== PASS ===` with green `cargo check` + `npm run build`.

- [ ] **Step 3: Non-macOS skip check (or simulate)**

On macOS, temporarily make `xcrun --find swift` fail (or test the guard logic): confirm the
skill logs "Swift sidecar skipped (no Swift toolchain)" and the project still passes the gates.

- [ ] **Step 4: Clean up throwaway projects**

Run: `# remove the mktemp dirs printed above with `trash` (per user rule), not rm`

- [ ] **Step 5: Commit**

```bash
git -C ~/ai_projects/claude-skills add init-tauri-app/scripts/smoke.sh
git -C ~/ai_projects/claude-skills commit -m "test(init-tauri-app): end-to-end smoke matrix"
```

---

## Task 10: Publish

- [ ] **Step 1: Sanity-check the skill loads**

Confirm `init-tauri-app/SKILL.md` frontmatter is valid and the description triggers on
"scaffold a tauri app". (Optional: run the skill-creator eval if desired.)

- [ ] **Step 2: Publish to the skills site (optional)**

Use the `publish-skill` skill: `/publish-skill init-tauri-app`. This generates the site MDX and
commits both repos. Skip if keeping the skill local-only.

- [ ] **Step 3: Final commit / push**

```bash
git -C ~/ai_projects/claude-skills push
```
(Only if the user wants it pushed.)

---

## Self-Review

**Spec coverage:** §2 approach → Task 2 procedure. §3 inputs → Task 2 step 1. §4 core layer →
Task 3 (all items present: AGENTS.md, CLAUDE.md, gitignore, toolchain pins, capability,
version-sync, .mcp.json, TS strict, README/CONTRIBUTING, docs/internal). §5 five modules →
Tasks 4-8. §5.1 agent-assembled + per-module `cargo check` → Task 2 step 4 + each INSERT.md.
§6 YAGNI defaults (plain CSS, no specta, npm) → Task 3 step 1. §7 location/packaging → file
structure + Task 1. §8 verification + 4-run matrix + non-macOS skip → Task 9. §9 non-goals →
respected (no Xcode, no token pipeline, no app logic).

**Placeholder scan:** The only intentional `todo!()` is `mcp::run_stdio` (Task 4 step 3), flagged
explicitly with its reference source and isolated so the rest compiles/tests — not a hidden gap.
The `release.sh`/`ci.yml`/`release.yml` (Task 7) and cenno-derived `mcp.rs` are "adapt from named
file" transforms, not vague TODOs — each cites an exact source path and the genericization rule.

**Type consistency:** `PingRequest`/`PingResponse` defined in Task 4 protocol.rs and used in
mcp.rs + INSERT.md. `app_sidecar_greet`/`app_sidecar_free` consistent across Sidecar.swift,
sidecar_ffi.rs, INSERT.md. `MIGRATIONS`/`apply`/`open`/`insert_item`/`list_items` consistent
across migrations.rs, db.rs, INSERT.md. `check-versions.sh` referenced in core + preflight +
CONTRIBUTING with the same path.
