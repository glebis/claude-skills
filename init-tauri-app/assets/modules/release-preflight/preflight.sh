#!/usr/bin/env bash
set -euo pipefail
TIER="${1:-quick}"   # hook | quick | full | release
run() { echo "+ $*"; "$@"; }
case "$TIER" in
  hook)    run bash -n scripts/*.sh ;;
  quick)   run npm run build; (cd src-tauri && run cargo check) ;;
  full)    "$0" quick; (cd src-tauri && run cargo fmt --check && run cargo clippy -- -D warnings && run cargo test) ;;
  release) "$0" full; run bash scripts/check-versions.sh; run npm run tauri build ;;
  *) echo "unknown tier: $TIER" >&2; exit 2 ;;
esac
echo "preflight $TIER OK"
