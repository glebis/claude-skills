# Agent guide — Tauri v2 project (Rust + web frontend)

Canonical instructions for any coding agent (Claude Code, Codex, Cursor) working in this repo.
`CLAUDE.md` just points here.

Architecture: Rust backend in `src-tauri/` ↔ web frontend (Vite) rendered in the OS-native
webview. The split defines everything below: the **Rust side is JSON-native**; the **webview
side is the blind spot** you close with the MCP server + unified logging.

## The loop (how you verify your own work)

1. Edit Rust or frontend.
2. **Rust:** `cargo check` in `src-tauri/` with JSON diagnostics — auto-apply machine-applicable fixes.
3. **Frontend:** Vite's error overlay + exit codes.
4. For UI/IPC behaviour: *look* at the running app via the Tauri MCP server.

## Rust side (primary signal — fast, parsable)

Run inside `src-tauri/`. `cargo check` is 2–3× faster than build and needs no binary:

```bash
cd src-tauri
cargo check  --message-format=json    # primary loop; apply `machine-applicable` suggestions
cargo clippy --message-format=json    # same schema + lint codes + suggested_replacement
cargo fmt --check                     # deterministic gate
cargo nextest run                     # isolated, parallel, fast test runner
```

Drive `cargo` **directly** for signal — `tauri dev`/`tauri build` are orchestrators with no JSON.
Reserve `tauri build` for final verification only (it's slow and triggers signing).

`rust-analyzer` is native to Claude Code. Set `cargo.targetDir = true` (or a separate target dir)
so it doesn't deadlock on the `target/` lock while `tauri dev` is running.

## Frontend side

```bash
pnpm install
pnpm dev          # Vite dev server (run backgrounded; pair with `tauri dev`)
pnpm build
pnpm check        # svelte-check / tsc, if configured
```

## Seeing the running app (the hard part)

Webviews don't share devtools across platforms; only Windows WebView2 speaks CDP. So:

- **Tauri MCP server** (`@hypothesi/tauri-mcp-server`, see `.mcp.json`) — screenshots, DOM
  snapshots, click/type, **execute + monitor live Tauri IPC**, stream logs. Requires its
  companion Rust plugin in `src-tauri/` and a **dev build running**. This is your eyes.
- **Unify logs with `tauri-plugin-log`** — Rust `println!` and frontend `console.*` otherwise go
  to *different* places. Fan both to Stdout + Webview + file for one readable stream.

## IPC boundary (Rust ↔ JS)

`invoke()` serializes via serde. Common silent failures:
- Command **error types must serialize** or the call fails opaquely.
- Large/complex return values can hang the promise.
- Rust↔TS type drift → hand-write IPC types in `src/lib/api.ts` mirroring the Rust command signatures — both cenno and cull deliberately avoid codegen deps.

## Compile-time discipline (keeps the agent loop tight)

- `cargo check` over `build` (biggest win).
- Faster linker: `mold` or `lld` in `.cargo/config.toml`.
- Separate rust-analyzer target dir (see above).

## Frontend ruleset — Svelte + TypeScript + Tauri

(Ported gap-filler; no maintained Claude skill covers this.)

- **Tauri commands:** define in Rust with `#[tauri::command]`; call via `invoke<T>()` with an
  explicit return type. Keep command signatures small and serializable.
- **State:** Svelte stores for UI state; Rust `tauri::State` for backend state. Don't duplicate
  source-of-truth across the boundary — pick one side per piece of state.
- **Errors:** return `Result<T, E>` where `E: serde::Serialize` (e.g. `thiserror` + a serializable
  wrapper). Surface to the UI as typed rejections, not strings.
- **Events:** prefer `invoke` for request/response; use `emit`/`listen` only for true push/streaming.
- **Types:** hand-write IPC types in `src/lib/api.ts` mirroring the Rust command signatures — both cenno and cull deliberately avoid codegen deps.
- **Design tokens:** plain CSS in `src/app.css`; style-dictionary is an optional upgrade (see cenno) — not set up by default.
- **Security:** least-privilege `capabilities/`; never expose a broad `fs`/`shell` scope; validate
  all command inputs in Rust.
- **Vite:** keep `clearScreen: false` and the fixed dev port Tauri expects; don't import Node-only
  modules into frontend code.

## Human gates

- macOS **notarization** is a slow network round-trip (2–20 min) and **sidecars/`externalBin` break
  it** — don't time-bomb the agent on it; flag for the human.
- Cross-platform release builds → `tauri-action` GitHub Action, matrix over macos/ubuntu/windows.
