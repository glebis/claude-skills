# Insert: Tray + autostart + updater

1. Copy `tray.rs`, `updater.rs` → `src-tauri/src/`.
2. Merge `cargo-deps.toml` into `src-tauri/Cargo.toml [dependencies]`.
   **Also enable the `tray-icon` feature on the `tauri` crate** — `TrayIconBuilder` will not
   compile without it. Edit the `tauri = { version = "2", features = [...] }` line to include
   `"tray-icon"` (e.g. `features = ["tray-icon"]`).
3. Deep-merge `conf-fragment.json` into `src-tauri/tauri.conf.json` (substitute `<name>`).
   Leave `pubkey` as the REPLACE marker; AGENTS.md documents generating it with
   `npm run tauri signer generate`.
4. In `src-tauri/src/lib.rs`: add `mod tray; mod updater;` near the top. Register the three
   plugins on the builder and build the tray in `.setup(...)`, using these exact forms:
   ```rust
   use tauri_plugin_autostart::MacosLauncher;
   // ...inside tauri::Builder::default():
       .plugin(tauri_plugin_window_state::Builder::default().build())
       .plugin(tauri_plugin_autostart::init(MacosLauncher::LaunchAgent, None))
       .plugin(tauri_plugin_updater::Builder::new().build())
       .setup(|app| {
           crate::tray::build(app.handle())?;
           Ok(())
       })
   ```
5. Verify: `cd src-tauri && cargo check`.
