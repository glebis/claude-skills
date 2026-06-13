// Auto-update via tauri-plugin-updater. Endpoint + pubkey are set in tauri.conf.json
// (see conf-fragment.json). This module just documents the wiring; the plugin does the work.
// To trigger a check from Rust, use the plugin's `app.updater()?.check().await` in a command.
