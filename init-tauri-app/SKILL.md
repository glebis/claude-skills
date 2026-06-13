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

## Procedure

### 1. Gather inputs (AskUserQuestion)
Ask, in one batch:
- **App name** (kebab-case). Validate `^[a-z][a-z0-9-]*$`.
- **Identifier** (reverse-DNS, default `com.glebkalinin.<name>`).
- **Target directory** (default `~/ai_projects/<name>`). Abort if it exists and is non-empty.
- **Frontend framework:** `react-ts` | `svelte-kit` | `vanilla-ts`.
- **Modules** (multi-select): CLI+MCP · SQLite · Tray/Updater · Release/Preflight · Swift sidecar.
- **JTBD artifact (optional):** a path to a `jtbd.json`. If not given, the skill auto-discovers
  `./jtbd.json` then `~/jtbd/<name>/jtbd.json`. See Step 1.5.

If Swift sidecar selected but host is non-macOS or `xcrun --find swift` fails: warn and drop it.

### 1.5 Ingest JTBD (optional, additive)
1. **Resolve** the artifact, first hit wins: explicit path → `./jtbd.json` → `~/jtbd/<name>/jtbd.json`.
   If none found, skip this whole step (the scaffold proceeds with empty product context — no error).
2. **Confirm:** echo the artifact's `hook` and ask the user to confirm before using it. On decline, skip.
3. **Validate:** the artifact must parse and have `name`, `hook`, `jtbd`. If not, warn and skip
   ingestion (never abort the scaffold). `render-jtbd.sh` exits 3 on invalid input — treat that as "skip".
4. **Pre-fill:** if valid, default the app name to `name` and identifier to `com.glebkalinin.<name>`
   (still confirm with the user in Step 1 if not already chosen).
5. The artifacts are written during Step 3 (core layer) — see the JTBD block there.

### 2. Scaffold base
```bash
cd <parent-of-target>
npm create tauri-app@latest <name> -- --template <framework> --manager npm --yes
```
Then `cd <target> && npm install`.

**Known upstream fix (current rustc + Tauri 2.11.x):** a *bare* scaffold's first `cargo check`
can fail with `error[E0119]` on `cookie`/`time` (transitive `cookie 0.18.1` vs `time 0.3.48`).
This is not a skill bug — it hits any fresh `create-tauri-app`. If it occurs, run once in
`src-tauri/`: `cargo update -p time --precise 0.3.47`, then re-check.

### 3. Apply core layer
Copy every file from `assets/core/` into the project, applying the renames in the table below,
then run a baseline gate. Substitute `<name>` (and `<identifier>` where the token appears) in
AGENTS.md and README.

| asset | destination |
|---|---|
| `core/AGENTS.md` | `AGENTS.md` |
| `core/CLAUDE.md` | `.claude/CLAUDE.md` |
| `core/gitignore` | `.gitignore` (merge: append only house lines not already present; skip lines — including comment headers — that already exist) |
| `core/rust-toolchain.toml` | `src-tauri/rust-toolchain.toml` |
| `core/node-version` | `.node-version` |
| `core/mcp.json` | `.mcp.json` |
| `core/capabilities/default.json` | `src-tauri/capabilities/default.json` (overwrite) |
| `core/scripts/check-versions.sh` | `scripts/check-versions.sh` (chmod +x) |
| `core/README.md` | `README.md` |
| `core/CONTRIBUTING.md` | `CONTRIBUTING.md` |

**If a JTBD artifact was confirmed in Step 1.5, also:**
- Render `assets/jtbd/PRODUCT.md.template` → `docs/PRODUCT.md` via
  `scripts/render-jtbd.sh <artifact> assets/jtbd/PRODUCT.md.template <artifact-path>`.
- Render `assets/jtbd/guardrails-check.md.template` → `docs/internal/guardrails-check.md`.
- Render `assets/jtbd/agents-product-section.md.template` and **insert it into `AGENTS.md`
  immediately after the first heading** (so product context leads the file).
- Copy the artifact verbatim to project-root `jtbd.json` (never modify the source).
- Field→destination details: `assets/jtbd/jtbd-map.md`.

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
