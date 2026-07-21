#!/bin/bash
#
# poll-and-publish.sh — fired daily by launchd (com.glebkalinin.agency-docs-publish).
#
# Polls Zoom for today's lab recording. When a completed MP4 of meaningful size
# appears, runs `/agency-docs-updater` headless to publish the meeting, then writes
# a per-day marker so it never double-publishes. If no recording shows up after the
# backoff retries (e.g. a non-lab day, or the lab ran very long), it exits quietly.
#
# Design notes:
#   - The Zoom API IS the schedule source of truth — no day-of-week list, no calendar
#     query. No recording => nothing to do => silent exit.
#   - Backoff happens inside this single launchd fire (the script sleeps between
#     checks). Started ~21:00 local; covers long (3h40) sessions + Zoom processing.

set -uo pipefail

# --- minimal-environment safety (launchd gives a bare PATH) ---
export PATH="/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin:$HOME/.local/bin"
export HOME="${HOME:-/Users/glebkalinin}"

# --- config (mirrors agency-docs-updater/.env defaults) ---
VAULT_DIR="${VAULT_DIR:-$HOME/Brains/brain}"
DOCS_SITE_DIR="${DOCS_SITE_DIR:-$HOME/Sites/agency-docs}"
SKILLS_REPO_DIR="${SKILLS_REPO_DIR:-$HOME/ai_projects/claude-skills}"
ZOOM_SCRIPT="$SKILLS_REPO_DIR/zoom/scripts/zoom_meetings.py"
CLAUDE_BIN="$HOME/.local/bin/claude"

LOG="$HOME/.claude/logs/agency-docs-publish.log"
DATE="$(date +%Y%m%d)"
MARKER="$HOME/.claude/state/agency-docs-published-$DATE.done"

# Minimum MP4 size (MB) to treat a recording as "the real lab", not a short test.
MIN_MB=50
# Backoff between checks, in seconds: first check is immediate, then these gaps.
# 0, +45m, +90m, +90m  => checks at ~21:00, 21:45, 23:15, 00:45 local.
DELAYS=(2700 5400 5400)

log() { echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*" >> "$LOG"; }

# --- already done today? ---
if [ -f "$MARKER" ]; then
  log "marker present ($MARKER) — already published today, exiting"
  exit 0
fi

# --- is today's lab recording ready on Zoom? ---
recordings_ready() {
  local out maxmb
  out="$(cd "$VAULT_DIR" && python3 "$ZOOM_SCRIPT" recordings \
        --start "$(date +%Y-%m-%d)" \
        --end "$(date -v+1d +%Y-%m-%d)" \
        --show-downloads 2>>"$LOG")"
  # Need at least one completed MP4...
  echo "$out" | grep -E '\*\*MP4\*\*.*completed' >/dev/null 2>&1 || return 1
  # ...of meaningful size (filters out short test/waiting-room clips).
  maxmb="$(echo "$out" | grep -E '\*\*MP4\*\*.*completed' \
           | sed -E 's/.*\(([0-9.]+) MB\).*/\1/' | sort -rn | head -1)"
  awk -v m="$maxmb" -v min="$MIN_MB" 'BEGIN{exit !((m+0) >= min)}'
}

publish() {
  log "recording ready — launching /agency-docs-updater (headless, skip-permissions)"
  cd "$DOCS_SITE_DIR" || { log "cannot cd to $DOCS_SITE_DIR"; return 1; }
  "$CLAUDE_BIN" -p "/agency-docs-updater" --dangerously-skip-permissions >> "$LOG" 2>&1
  local rc=$?
  if [ $rc -eq 0 ]; then
    touch "$MARKER"
    log "agency-docs-updater completed (rc=0); marker written"
  else
    log "agency-docs-updater exited rc=$rc — NOT writing marker (will retry next fire)"
  fi
  return $rc
}

log "=== poll start (date=$DATE) ==="
for attempt in 0 1 2 3; do
  if recordings_ready; then
    log "attempt $attempt: recording ready"
    publish
    exit $?
  fi
  log "attempt $attempt: no qualifying recording yet"
  if [ "$attempt" -lt 3 ]; then
    sleep "${DELAYS[$attempt]}"
  fi
done
log "=== gave up: no recording after $(( ${#DELAYS[@]} + 1 )) checks ==="
exit 0
