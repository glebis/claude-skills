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
