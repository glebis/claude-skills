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
