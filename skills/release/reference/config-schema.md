# `release.config.json` reference

A single JSON file at the repo root declaring how to release this project and
what its public API surfaces are.

```jsonc
{
  // Files whose version string must stay in sync. JSON uses a pointer; TOML a dotted key.
  "versionFiles": [
    { "path": "package.json", "kind": "json", "pointer": "/version" },
    { "path": "src-tauri/tauri.conf.json", "kind": "json", "pointer": "/version" },
    { "path": "src-tauri/Cargo.toml", "kind": "toml", "key": "package.version" }
  ],

  // Lockfiles to refresh after a bump (the skill reminds you / you wire the command).
  "lockfiles": ["src-tauri/Cargo.lock"],

  // Readiness gate: a single shell command that must exit 0.
  "gate": "npm run preflight -- release",

  // Extra gate commands (golden / contract tests). All must exit 0.
  "extraGate": [
    "cargo test --manifest-path src-tauri/Cargo.toml --features test-support --test compat_golden"
  ],

  // Changelog.
  "changelog": { "path": "CHANGELOG.md", "style": "keep-a-changelog", "from": "conventional-commits" },

  // The living compatibility doc.
  "compatibility": { "path": "docs/COMPATIBILITY.md" },

  // The declared PUBLIC API. tier ∈ {experimental, preview, stable}.
  // Only `stable` surfaces carry the compatibility promise; breaking one forces a major bump.
  "surfaces": [
    { "id": "db",      "name": "Database schema", "tier": "stable",  "mode": "BACKWARD_TRANSITIVE" },
    { "id": "mcp",     "name": "MCP token API",   "tier": "preview", "mode": "unversioned" },
    { "id": "exports", "name": "Export formats",  "tier": "stable",  "mode": "forward-compatible" }
  ],

  // Branch releases are cut from, and (optionally) the worktree where it's checked out.
  "releaseBranch": "main",
  "worktree": "../cull-main-landing",

  // Tagging. The tag (e.g. v0.2.0) should trigger your CI release workflow.
  "tag": { "prefix": "v", "push": true },

  // Optional: release-notes source.
  "issueTracker": { "kind": "bd", "binEnv": "BD_BIN" }
}
```

## Field notes

- **`kind: "json"`** needs `pointer` (RFC-6901-ish slash path, e.g. `/version`).
  **`kind: "toml"`** needs `key` (`section.name`, e.g. `package.version`). The
  rewrite is targeted (preserves formatting and unrelated keys).
- **`gate`** is your existing release-tier check (tests + lint + license + build).
  Keep CVE/SBOM here once you add `cargo-deny`/`cargo-cyclonedx`.
- **`surfaces[].mode`** is documentation today (e.g. `BACKWARD_TRANSITIVE`,
  `forward-compatible`, `unversioned`); it becomes enforceable as you add contract
  tests to `extraGate`. See `reference/standards.md`.
- **`tier`** drives the gate: a `breaking` change to a `stable` surface ⇒ `major`.
  Keep risky/young surfaces at `preview` so you can evolve them within minors.
