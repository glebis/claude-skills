# Insert: SQLite + migrations

1. Copy `db.rs`, `migrations.rs` → `src-tauri/src/`.
2. Copy `compat_golden.rs` → `src-tauri/tests/compat_golden.rs`.
3. Merge `cargo-deps.toml` into `src-tauri/Cargo.toml [dependencies]`.
4. In `src-tauri/src/lib.rs`: add `mod db; mod migrations;`.
5. Verify: `cd src-tauri && cargo check && cargo test db::tests`.
