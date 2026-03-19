#!/bin/bash
# Granola → Obsidian auto-sync
# Checks for new Granola meetings and exports any not yet in the vault.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
GRANOLA_PY="$SCRIPT_DIR/granola.py"
VAULT="${GRANOLA_VAULT:-$HOME/Brains/brain}"
LOG="$HOME/Library/Logs/granola-sync.log"

log() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') $1" >> "$LOG"
}

log "=== Sync started ==="

# Collect already-exported granola IDs from vault
KNOWN_IDS=$(grep -rh '^granola_id: ' "$VAULT"/*.md "$VAULT"/**/*.md 2>/dev/null \
    | sed 's/^granola_id: //' | sort -u || true)

# Get recent meetings from API
API_OUTPUT=$(python3 "$GRANOLA_PY" api-list --limit 20 2>>"$LOG") || {
    log "ERROR: api-list failed"
    exit 1
}

# Extract meeting IDs
MEETING_IDS=$(echo "$API_OUTPUT" | python3 -c "
import sys, json
data = json.load(sys.stdin)
for m in data.get('meetings', []):
    print(m['id'])
")

EXPORTED=0
SKIPPED=0

for mid in $MEETING_IDS; do
    if echo "$KNOWN_IDS" | grep -q "$mid"; then
        SKIPPED=$((SKIPPED + 1))
        continue
    fi
    log "Exporting: $mid"
    python3 "$GRANOLA_PY" export "$mid" --vault "$VAULT" 2>>"$LOG" && {
        EXPORTED=$((EXPORTED + 1))
        log "OK: $mid"
    } || {
        log "FAIL: $mid"
    }
done

log "Done: exported=$EXPORTED skipped=$SKIPPED"
