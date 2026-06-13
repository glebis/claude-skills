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
