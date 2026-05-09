#!/usr/bin/env bash
set -euo pipefail

# ── Paths & Config ──────────────────────────────────────────────────
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILL_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
QUEUE_FILE="$SKILL_DIR/queue.jsonl"
APPLIED_FILE="$SKILL_DIR/queue.applied.jsonl"
LOCK_DIR="$SKILL_DIR/.queue.lock"

DB_PATH="${WISPR_DB:-$HOME/Library/Application Support/Wispr Flow/flow.sqlite}"
DICT_SCRIPT="$HOME/.claude/skills/wispr-analytics/scripts/wispr_dictionary.py"
# shellcheck disable=SC2034
EXPORT_PATH="${WISPR_EXPORT:-$HOME/ai_projects/claude-skills/wispr-analytics/data/dictionary.json}"

BACKUP_DIR="$HOME/Library/Application Support/Wispr Flow/backups"
MAX_BACKUPS=10

# ── Dependency Checks ───────────────────────────────────────────────
check_deps() {
    local missing=0
    for cmd in jq sqlite3; do
        if ! command -v "$cmd" >/dev/null 2>&1; then
            echo "ERROR: '$cmd' is required but not found." >&2
            missing=1
        fi
    done
    if [ ! -f "$DICT_SCRIPT" ]; then
        echo "ERROR: Dictionary script not found at $DICT_SCRIPT" >&2
        missing=1
    fi
    if [ "$missing" -eq 1 ]; then
        exit 1
    fi
}

# ── Locking (mkdir-based, macOS-safe) ───────────────────────────────
acquire_lock() {
    if ! mkdir "$LOCK_DIR" 2>/dev/null; then
        echo "ERROR: Could not acquire lock ($LOCK_DIR exists). Another instance running?" >&2
        exit 1
    fi
    trap 'release_lock' EXIT
}

release_lock() {
    rmdir "$LOCK_DIR" 2>/dev/null || true
}

# ── Utilities ───────────────────────────────────────────────────────
generate_id() {
    echo "$(date -u +%Y%m%dT%H%M%SZ)-$$"
}

normalize() {
    echo "$1" | tr '[:upper:]' '[:lower:]' | sed 's/^[[:space:]]*//;s/[[:space:]]*$//'
}

is_multi_word() {
    local wc
    wc=$(echo "$1" | wc -w | tr -d ' ')
    [ "$wc" -gt 1 ]
}

# ── Wispr Lifecycle Helpers ─────────────────────────────────────────
is_wispr_running() {
    pgrep -f "Wispr Flow" >/dev/null 2>&1
}

quit_wispr() {
    local force_flag="${1:-}"
    say "Shutting down Wispr" &
    echo "Quitting Wispr Flow..."
    osascript -e 'tell application "Wispr Flow" to quit' 2>/dev/null || true
    sleep 2
    pkill -TERM -f "Wispr Flow" 2>/dev/null || true

    local waited=0
    while pgrep -f "Wispr Flow" >/dev/null 2>&1 && [ "$waited" -lt 15 ]; do
        sleep 1
        waited=$((waited + 1))
    done

    if pgrep -f "Wispr Flow" >/dev/null 2>&1; then
        if [ "$force_flag" = "--force-quit" ]; then
            echo "Force-killing Wispr Flow..."
            pkill -9 -f "Wispr Flow" 2>/dev/null || true
            sleep 2
        else
            echo "ERROR: Wispr Flow did not quit within 15s. Use --force-quit to force-kill." >&2
            return 1
        fi
    fi
    echo "Wispr Flow stopped."
}

start_wispr() {
    echo "Starting Wispr Flow..."
    open -a "Wispr Flow"
    say "Wispr is back" &
    local waited=0
    while ! is_wispr_running && [ "$waited" -lt 10 ]; do
        sleep 1
        waited=$((waited + 1))
    done
    if is_wispr_running; then
        echo "Wispr Flow started."
    else
        echo "WARNING: Wispr Flow may not have started." >&2
    fi
}

backup_db() {
    mkdir -p "$BACKUP_DIR"
    local ts
    ts="$(date -u +%Y%m%dT%H%M%SZ)"
    local backup_file="$BACKUP_DIR/flow-$ts.sqlite"
    sqlite3 "$DB_PATH" ".backup '$backup_file'"
    echo "Backup: $backup_file"

    # Prune old backups, keep newest MAX_BACKUPS
    local count
    count=$(find "$BACKUP_DIR" -name 'flow-*.sqlite' -type f | wc -l | tr -d ' ')
    if [ "$count" -gt "$MAX_BACKUPS" ]; then
        local to_remove
        to_remove=$((count - MAX_BACKUPS))
        # shellcheck disable=SC2012
        ls -1t "$BACKUP_DIR"/flow-*.sqlite | tail -n "$to_remove" | while IFS= read -r f; do
            rm -f "$f"
        done
    fi
}

# ── Variant Generation ─────────────────────────────────────────────
# Outputs "phrase|replacement" lines
generate_variants() {
    local mishear="$1"
    local correction="$2"
    local mode="$3"

    # Always include original
    echo "$mishear|$correction"

    if [ "$mode" = "exact" ]; then
        return
    fi

    # Lowercase variant
    local lower_mishear lower_correction
    lower_mishear="$(echo "$mishear" | tr '[:upper:]' '[:lower:]')"
    lower_correction="$(echo "$correction" | tr '[:upper:]' '[:lower:]')"
    if [ "$lower_mishear" != "$mishear" ] || [ "$lower_correction" != "$correction" ]; then
        echo "$lower_mishear|$lower_correction"
    fi

    # Title Case variant (capitalize first letter of each word)
    local title_mishear title_correction
    # Bash 3.2 compatible title case using awk
    title_mishear="$(echo "$mishear" | awk '{for(i=1;i<=NF;i++){$i=toupper(substr($i,1,1)) tolower(substr($i,2))}}1')"
    title_correction="$(echo "$correction" | awk '{for(i=1;i<=NF;i++){$i=toupper(substr($i,1,1)) tolower(substr($i,2))}}1')"
    if [ "$title_mishear" != "$mishear" ] || [ "$title_correction" != "$correction" ]; then
        # Also check it's not the same as lowercase
        if [ "$title_mishear" != "$lower_mishear" ] || [ "$title_correction" != "$lower_correction" ]; then
            echo "$title_mishear|$title_correction"
        fi
    fi
}

# ── DB Check Helper ────────────────────────────────────────────────
# Returns count of matching non-deleted entries; also sets CHECK_REPLACEMENT global
check_existing_in_db() {
    local phrase="$1"
    local escaped_phrase
    # shellcheck disable=SC2001
    escaped_phrase="$(echo "$phrase" | sed "s/'/''/g")"
    local result
    result=$(sqlite3 "$DB_PATH" "SELECT COUNT(*), COALESCE(MAX(replacement),'') FROM Dictionary WHERE phrase = '$escaped_phrase' AND isDeleted = 0;" 2>/dev/null || echo "0|")
    CHECK_COUNT="$(echo "$result" | cut -d'|' -f1)"
    CHECK_REPLACEMENT="$(echo "$result" | cut -d'|' -f2)"
}

# ── cmd_dry_run ────────────────────────────────────────────────────
cmd_dry_run() {
    if [ ! -f "$QUEUE_FILE" ] || [ ! -s "$QUEUE_FILE" ]; then
        echo "Queue is empty. Nothing to preview."
        return 0
    fi

    if [ ! -f "$DB_PATH" ]; then
        echo "ERROR: Wispr DB not found at $DB_PATH" >&2
        exit 1
    fi

    local stats_file
    stats_file="$(mktemp /tmp/wispr-fix-dryrun.XXXXXX)"

    while IFS= read -r line; do
        local mishear correction variant_mode
        mishear=$(echo "$line" | jq -r '.mishear')
        correction=$(echo "$line" | jq -r '.correction')
        variant_mode=$(echo "$line" | jq -r '.variant_mode')

        echo "--- \"$mishear\" -> \"$correction\" [$variant_mode]"

        generate_variants "$mishear" "$correction" "$variant_mode" | while IFS='|' read -r var_phrase var_replacement; do
            check_existing_in_db "$var_phrase"
            if [ "$CHECK_COUNT" -gt 0 ]; then
                if [ "$CHECK_REPLACEMENT" = "$var_replacement" ]; then
                    echo "  SKIP (exists): \"$var_phrase\" -> \"$var_replacement\""
                    echo "S" >> "$stats_file"
                else
                    echo "  REVIEW (conflict): \"$var_phrase\" -> \"$var_replacement\" (current: \"$CHECK_REPLACEMENT\")"
                    echo "R" >> "$stats_file"
                fi
            else
                echo "  APPLY: \"$var_phrase\" -> \"$var_replacement\""
                echo "A" >> "$stats_file"
            fi
        done
    done < "$QUEUE_FILE"

    local total_apply total_skip total_review
    total_apply=$(grep -c "^A$" "$stats_file" 2>/dev/null || true)
    total_skip=$(grep -c "^S$" "$stats_file" 2>/dev/null || true)
    total_review=$(grep -c "^R$" "$stats_file" 2>/dev/null || true)
    total_apply=${total_apply:-0}
    total_skip=${total_skip:-0}
    total_review=${total_review:-0}
    rm -f "$stats_file"

    echo ""
    echo "Summary: $total_apply to apply, $total_skip to skip, $total_review need review"
}

# ── cmd_flush ──────────────────────────────────────────────────────
cmd_flush() {
    local force_flag=""
    local no_restart=0

    while [ $# -gt 0 ]; do
        case "$1" in
            --force-quit) force_flag="--force-quit"; shift ;;
            --no-restart) no_restart=1; shift ;;
            *) echo "ERROR: Unknown flag '$1'" >&2; exit 1 ;;
        esac
    done

    if [ ! -f "$QUEUE_FILE" ] || [ ! -s "$QUEUE_FILE" ]; then
        echo "Queue is empty. Nothing to flush."
        return 0
    fi

    # Quit Wispr if running
    if is_wispr_running; then
        quit_wispr "$force_flag" || exit 1
    fi

    # Verify DB exists
    if [ ! -f "$DB_PATH" ]; then
        echo "ERROR: Wispr DB not found at $DB_PATH" >&2
        exit 1
    fi

    # Backup
    backup_db

    # Verify Dictionary table exists
    local table_check
    table_check=$(sqlite3 "$DB_PATH" "SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name='Dictionary';" 2>/dev/null || echo "0")
    if [ "$table_check" -eq 0 ]; then
        echo "ERROR: Dictionary table not found in database." >&2
        exit 1
    fi

    acquire_lock

    local tmpfile
    tmpfile="$(mktemp "$SKILL_DIR/queue.tmp.XXXXXX")"
    local flush_stats
    flush_stats="$(mktemp /tmp/wispr-fix-flush-stats.XXXXXX)"

    while IFS= read -r line; do
        local mishear correction variant_mode
        mishear=$(echo "$line" | jq -r '.mishear')
        correction=$(echo "$line" | jq -r '.correction')
        variant_mode=$(echo "$line" | jq -r '.variant_mode')

        # Process variants - use temp file to track per-entry results
        local var_results
        var_results="$(mktemp /tmp/wispr-fix-var.XXXXXX)"

        generate_variants "$mishear" "$correction" "$variant_mode" | while IFS='|' read -r var_phrase var_replacement; do
            check_existing_in_db "$var_phrase"
            if [ "$CHECK_COUNT" -gt 0 ]; then
                if [ "$CHECK_REPLACEMENT" = "$var_replacement" ]; then
                    echo "SKIPPED" >> "$var_results"
                else
                    echo "REVIEW" >> "$var_results"
                    echo "  REVIEW: \"$var_phrase\" conflicts (current: \"$CHECK_REPLACEMENT\")"
                fi
            else
                # Add via python script
                if python3 "$DICT_SCRIPT" add "$var_phrase" "$var_replacement" >/dev/null 2>&1; then
                    echo "APPLIED" >> "$var_results"
                    echo "  Added: \"$var_phrase\" -> \"$var_replacement\""
                else
                    echo "FAILED" >> "$var_results"
                    echo "  FAILED: \"$var_phrase\" -> \"$var_replacement\""
                fi
            fi
        done

        # Read back counts from var_results
        local entry_review entry_failed
        entry_review=$(grep -c "^REVIEW$" "$var_results" 2>/dev/null || true)
        entry_failed=$(grep -c "^FAILED$" "$var_results" 2>/dev/null || true)
        entry_review=${entry_review:-0}
        entry_failed=${entry_failed:-0}

        # Accumulate stats
        cat "$var_results" >> "$flush_stats"
        rm -f "$var_results"

        if [ "$entry_review" -gt 0 ] || [ "$entry_failed" -gt 0 ]; then
            # Keep in queue
            echo "$line" >> "$tmpfile"
        else
            # Record as applied
            local applied_entry
            applied_entry=$(echo "$line" | jq -c --arg status "applied" --arg at "$(date -u +%Y-%m-%dT%H:%M:%SZ)" '. + {status: $status, applied_at: $at}')
            echo "$applied_entry" >> "$APPLIED_FILE"
        fi
    done < "$QUEUE_FILE"

    local total_applied total_skipped total_review total_failed
    total_applied=$(grep -c "^APPLIED$" "$flush_stats" 2>/dev/null || true)
    total_skipped=$(grep -c "^SKIPPED$" "$flush_stats" 2>/dev/null || true)
    total_review=$(grep -c "^REVIEW$" "$flush_stats" 2>/dev/null || true)
    total_failed=$(grep -c "^FAILED$" "$flush_stats" 2>/dev/null || true)
    total_applied=${total_applied:-0}
    total_skipped=${total_skipped:-0}
    total_review=${total_review:-0}
    total_failed=${total_failed:-0}
    rm -f "$flush_stats"

    mv "$tmpfile" "$QUEUE_FILE"
    if [ ! -s "$QUEUE_FILE" ]; then
        rm -f "$QUEUE_FILE"
    fi

    release_lock
    # Clear the trap since we manually released
    trap - EXIT

    # Integrity check
    local integrity
    integrity=$(sqlite3 "$DB_PATH" "PRAGMA integrity_check;" 2>/dev/null || echo "error")
    if [ "$integrity" != "ok" ]; then
        echo "WARNING: Database integrity check returned: $integrity" >&2
    fi

    # Export dictionary
    python3 "$DICT_SCRIPT" export >/dev/null 2>&1 || echo "WARNING: Export failed" >&2

    # Restart Wispr unless told not to
    if [ "$no_restart" -eq 0 ]; then
        start_wispr
    fi

    echo ""
    echo "Flush complete."
    echo "  Applied: $total_applied"
    echo "  Skipped: $total_skipped"
    echo "  Needs Review: $total_review"
    echo "  Failed: $total_failed"

    if [ -f "$QUEUE_FILE" ] && [ -s "$QUEUE_FILE" ]; then
        local remaining
        remaining=$(wc -l < "$QUEUE_FILE" | tr -d ' ')
        echo "  Remaining in queue: $remaining"
    fi
}

# ── cmd_restore ────────────────────────────────────────────────────
cmd_restore() {
    local target="${1:-latest}"

    if is_wispr_running; then
        echo "ERROR: Wispr Flow is running. Quit it first before restoring." >&2
        exit 1
    fi

    local restore_path=""

    if [ "$target" = "latest" ]; then
        if [ ! -d "$BACKUP_DIR" ]; then
            echo "ERROR: No backup directory found at $BACKUP_DIR" >&2
            exit 1
        fi
        # shellcheck disable=SC2012
        restore_path="$(ls -1t "$BACKUP_DIR"/flow-*.sqlite 2>/dev/null | head -n 1)"
        if [ -z "$restore_path" ]; then
            echo "ERROR: No backups found in $BACKUP_DIR" >&2
            exit 1
        fi
    else
        restore_path="$target"
    fi

    if [ ! -f "$restore_path" ]; then
        echo "ERROR: Backup file not found: $restore_path" >&2
        exit 1
    fi

    # Backup current DB before overwriting
    echo "Backing up current database before restore..."
    backup_db

    # Restore
    cp "$restore_path" "$DB_PATH"

    # Integrity check
    local integrity
    integrity=$(sqlite3 "$DB_PATH" "PRAGMA integrity_check;" 2>/dev/null || echo "error")
    if [ "$integrity" = "ok" ]; then
        echo "Restored from: $restore_path"
        echo "Integrity check: OK"
    else
        echo "Restored from: $restore_path"
        echo "WARNING: Integrity check returned: $integrity" >&2
    fi
}

# ── cmd_add ─────────────────────────────────────────────────────────
cmd_add() {
    local mishear=""
    local correction=""
    local exact_flag=0

    while [ $# -gt 0 ]; do
        case "$1" in
            --exact) exact_flag=1; shift ;;
            *)
                if [ -z "$mishear" ]; then
                    mishear="$1"
                elif [ -z "$correction" ]; then
                    correction="$1"
                else
                    echo "ERROR: Too many arguments. Usage: wispr-fix add [--exact] <mishear> <correction>" >&2
                    exit 1
                fi
                shift
                ;;
        esac
    done

    if [ -z "$mishear" ] || [ -z "$correction" ]; then
        echo "ERROR: Both <mishear> and <correction> are required." >&2
        echo "Usage: wispr-fix add [--exact] <mishear> <correction>" >&2
        exit 1
    fi

    local norm_mishear norm_correction
    norm_mishear="$(normalize "$mishear")"
    norm_correction="$(normalize "$correction")"

    if [ "$norm_mishear" = "$norm_correction" ]; then
        echo "ERROR: Mishear and correction are identical after normalization." >&2
        exit 1
    fi

    acquire_lock

    # Dedup check against existing queue
    if [ -f "$QUEUE_FILE" ]; then
        local existing
        existing=$(jq -r --arg m "$norm_mishear" --arg c "$norm_correction" \
            'select((.mishear | ascii_downcase) == $m and (.correction | ascii_downcase) == $c)' \
            "$QUEUE_FILE" 2>/dev/null || true)
        if [ -n "$existing" ]; then
            echo "SKIP: This correction already exists in the queue." >&2
            exit 0
        fi
    fi

    # Determine variant mode
    local variant_mode="default"
    if [ "$exact_flag" -eq 1 ]; then
        variant_mode="exact"
    elif ! is_multi_word "$mishear"; then
        variant_mode="exact"
    fi

    local entry_id
    entry_id="$(generate_id)"

    local entry
    entry=$(jq -c -n \
        --arg id "$entry_id" \
        --arg mishear "$mishear" \
        --arg correction "$correction" \
        --arg variant_mode "$variant_mode" \
        --arg ts "$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
        '{id: $id, mishear: $mishear, correction: $correction, variant_mode: $variant_mode, added: $ts}')

    echo "$entry" >> "$QUEUE_FILE"

    local variant_note=""
    if [ "$variant_mode" = "exact" ]; then
        variant_note=" (exact match only)"
    else
        variant_note=" (with variants)"
    fi

    echo "Added: \"$mishear\" -> \"$correction\"$variant_note"
}

# ── cmd_list ────────────────────────────────────────────────────────
cmd_list() {
    if [ ! -f "$QUEUE_FILE" ] || [ ! -s "$QUEUE_FILE" ]; then
        echo "Queue is empty."
        return 0
    fi

    local count
    count=$(wc -l < "$QUEUE_FILE" | tr -d ' ')
    echo "Pending corrections: $count"
    echo ""

    local i=1
    while IFS= read -r line; do
        local mishear correction variant_mode ts
        mishear=$(echo "$line" | jq -r '.mishear')
        correction=$(echo "$line" | jq -r '.correction')
        variant_mode=$(echo "$line" | jq -r '.variant_mode')
        ts=$(echo "$line" | jq -r '.added')
        echo "  $i. \"$mishear\" -> \"$correction\"  [$variant_mode]  ($ts)"
        i=$((i + 1))
    done < "$QUEUE_FILE"
}

# ── cmd_remove ──────────────────────────────────────────────────────
cmd_remove() {
    if [ $# -lt 1 ]; then
        echo "ERROR: Provide the mishear string to remove." >&2
        echo "Usage: wispr-fix remove <mishear>" >&2
        exit 1
    fi

    local target="$1"
    local norm_target
    norm_target="$(normalize "$target")"

    if [ ! -f "$QUEUE_FILE" ] || [ ! -s "$QUEUE_FILE" ]; then
        echo "Queue is empty, nothing to remove."
        return 0
    fi

    acquire_lock

    local tmpfile
    tmpfile="$(mktemp "$SKILL_DIR/queue.tmp.XXXXXX")"
    local removed=0
    local removed_items=""

    while IFS= read -r line; do
        local mishear
        mishear=$(echo "$line" | jq -r '.mishear')
        local norm_mishear
        norm_mishear="$(normalize "$mishear")"

        # Match: exact normalized match or substring
        if [ "$norm_mishear" = "$norm_target" ] || echo "$norm_mishear" | grep -qi "$norm_target"; then
            local correction
            correction=$(echo "$line" | jq -r '.correction')
            removed_items="$removed_items  - \"$mishear\" -> \"$correction\"
"
            removed=$((removed + 1))
        else
            echo "$line" >> "$tmpfile"
        fi
    done < "$QUEUE_FILE"

    mv "$tmpfile" "$QUEUE_FILE"

    # Clean up empty file
    if [ ! -s "$QUEUE_FILE" ]; then
        rm -f "$QUEUE_FILE"
    fi

    if [ "$removed" -eq 0 ]; then
        echo "No matches found for \"$target\"."
    else
        echo "Removed $removed entry/entries:"
        printf "%s" "$removed_items"
    fi
}

# ── Usage ───────────────────────────────────────────────────────────
usage() {
    cat <<'USAGE'
wispr-fix — Wispr Flow dictionary queue manager

Usage:
  wispr-fix add [--exact] <mishear> <correction>
  wispr-fix list
  wispr-fix remove <mishear>
  wispr-fix dry-run
  wispr-fix flush [--force-quit] [--no-restart]
  wispr-fix restore [<backup-path>|latest]
  wispr-fix help

Commands:
  add       Queue a correction (mishear -> correct spelling)
  list      Show pending corrections in the queue
  remove    Remove entries matching <mishear> (exact or substring)
  dry-run   Preview what flush would do (check DB for conflicts)
  flush     Apply all queued corrections to Wispr Flow DB
  restore   Restore DB from a backup (default: latest)
  help      Show this help message

Options:
  --exact       Force exact-match mode (default for single words)
  --force-quit  Force-kill Wispr Flow if graceful quit fails (flush)
  --no-restart  Don't restart Wispr Flow after flush

Environment:
  WISPR_DB      Override path to Wispr Flow SQLite database
  WISPR_EXPORT  Override export path
USAGE
}

# ── Dispatcher ──────────────────────────────────────────────────────
main() {
    check_deps

    if [ $# -lt 1 ]; then
        usage
        exit 1
    fi

    local cmd="$1"
    shift

    case "$cmd" in
        add)      cmd_add "$@" ;;
        list)     cmd_list ;;
        remove)   cmd_remove "$@" ;;
        dry-run)  cmd_dry_run ;;
        flush)    cmd_flush "$@" ;;
        restore)  cmd_restore "$@" ;;
        help)     usage ;;
        *)
            echo "ERROR: Unknown command '$cmd'" >&2
            usage
            exit 1
            ;;
    esac
}

main "$@"
