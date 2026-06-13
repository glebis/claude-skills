# Insert: Swift sidecar (macOS only)

PREREQ: macOS + `xcrun --find swift` succeeds. If not, SKIP this module (log it).

1. Copy `Package.swift` → `src-tauri/swift/Package.swift`.
2. Copy `Sidecar.swift` → `src-tauri/swift/Sources/AppSidecar/Sidecar.swift`.
3. Copy `sidecar_ffi.rs` → `src-tauri/src/sidecar_ffi.rs`; add `mod sidecar_ffi;` to `lib.rs`.
4. Merge `cargo-deps.toml` line into `src-tauri/Cargo.toml` under BOTH `[dependencies]`
   and `[build-dependencies]`.
5. Merge `build.rs.fragment` into `src-tauri/build.rs` BEFORE the `tauri_build::build()` call.
6. Verify (macOS): `cd src-tauri && cargo check`.
