#!/bin/bash
# Granola → Obsidian auto-sync
# Checks for new Granola meetings and exports any not yet in the vault.

set -euo pipefail

export PATH="$HOME/.local/bin:/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin:${PATH:-}"
export SOPS_AGE_KEY_FILE="${SOPS_AGE_KEY_FILE:-$HOME/.config/sops/age/keys.txt}"

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
GRANOLA_PY="$SCRIPT_DIR/granola.py"
VAULT="${GRANOLA_VAULT:-$HOME/Brains/brain}"
LOG="$HOME/Library/Logs/granola-sync.log"
SESSION_LOOP="$VAULT/scripts/session_loop_postsync.sh"
DRY_RUN="${DRY_RUN:-0}"

log() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') $1" >> "$LOG"
}

log "=== Sync started ==="

# Collect already-exported granola IDs from vault
KNOWN_IDS=$(find "$VAULT" -type f -name '*.md' -print0 2>/dev/null \
    | xargs -0 grep -h '^granola_id: ' 2>/dev/null \
    | sed 's/^granola_id: //' | sort -u || true)

# Get recent notes from Granola Personal API
API_OUTPUT=$(python3 "$GRANOLA_PY" list --format json 2>>"$LOG") || {
    log "ERROR: list failed"
    exit 1
}

# Extract note IDs
MEETING_IDS=$(echo "$API_OUTPUT" | python3 -c "
import sys, json
data = json.load(sys.stdin)
for m in data.get('notes', []):
    print(m['id'])
")

EXPORTED=0
SKIPPED=0

for mid in $MEETING_IDS; do
    if echo "$KNOWN_IDS" | grep -q "$mid"; then
        SKIPPED=$((SKIPPED + 1))
        continue
    fi
    if [ "$DRY_RUN" = "1" ]; then
        log "DRY RUN: would export: $mid"
        EXPORTED=$((EXPORTED + 1))
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

if [ "$DRY_RUN" = "1" ]; then
    log "DRY RUN: would run session-loop post-sync"
elif [ -x "$SESSION_LOOP" ]; then
    log "Running session-loop post-sync"
    VAULT="$VAULT" bash "$SESSION_LOOP" >> "$LOG" 2>&1 || {
        log "WARN: session-loop post-sync failed"
    }
else
    log "WARN: session-loop post-sync missing or not executable: $SESSION_LOOP"
fi
