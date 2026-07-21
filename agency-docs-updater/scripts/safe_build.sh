#!/usr/bin/env bash
# Run `npm run build` in the docs site, recovering from the known corrupt/low-space
# .next cache failure (TypeError: Cannot read properties of null (reading 'hash'),
# or ENOSPC). The MDX map step runs first, so this error is NOT an MDX error —
# clearing .next and retrying once fixes it deterministically.
set -uo pipefail

DOCS_SITE_DIR="${DOCS_SITE_DIR:-$HOME/Sites/agency-docs}"
cd "$DOCS_SITE_DIR" || { echo "✗ DOCS_SITE_DIR not found: $DOCS_SITE_DIR"; exit 1; }

clear_next() {
  if command -v trash >/dev/null 2>&1; then trash .next 2>/dev/null || true; else rm -rf .next; fi
}

tmp="$(mktemp)"
npm run build 2>&1 | tee "$tmp"
status=${PIPESTATUS[0]}

if [ "$status" -ne 0 ] && grep -qE "reading 'hash'|ENOSPC|Cannot read properties of null" "$tmp"; then
  echo "↻ Detected corrupt/low-space .next cache — clearing and retrying once"
  clear_next
  npm run build 2>&1 | tee "$tmp"
  status=${PIPESTATUS[0]}
fi

rm -f "$tmp"
exit "$status"
