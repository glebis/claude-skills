---
name: wispr-fix
description: Queue and batch-apply Wispr Flow dictation corrections. Use when the user invokes /wispr-fix or writes "wispr fix: X -> Y" to correct a speech-to-text mishear.
---

# Wispr Fix: Dictation Correction Queue

Queue dictation corrections instantly during work. Apply them all at once when convenient.

## Invocation Patterns

### Explicit add
User says: `/wispr-fix "Clauthe Code" "Claude Code"`
Action: Run the add command.

### Auto-detect pattern
User writes: `wispr fix: X -> Y`
Action: Parse X and Y, run the add command.

### Flush / dry-run / list
User says: `/wispr-fix flush`, `/wispr-fix dry-run`, `/wispr-fix list`
Action: Run the corresponding command.

## Commands

All commands use the script at `~/.claude/skills/wispr-fix/scripts/wispr-fix.sh`.

### Queue a correction
```bash
~/.claude/skills/wispr-fix/scripts/wispr-fix.sh add "<mishear>" "<correction>"
```
Use `--exact` to skip case variant generation (auto-applied for single words).

### List pending corrections
```bash
~/.claude/skills/wispr-fix/scripts/wispr-fix.sh list
```

### Remove a queued correction
```bash
~/.claude/skills/wispr-fix/scripts/wispr-fix.sh remove "<mishear>"
```
Supports fuzzy matching on the mishear string.

### Preview what flush will do
```bash
~/.claude/skills/wispr-fix/scripts/wispr-fix.sh dry-run
```

### Apply all queued corrections
```bash
~/.claude/skills/wispr-fix/scripts/wispr-fix.sh flush
```
Options: `--force-quit` (force-kill Wispr if graceful quit fails), `--no-restart` (don't restart Wispr after).

**IMPORTANT:** Flush will quit Wispr Flow, apply all corrections to the SQLite database, and restart it. Always inform the user before running flush.

### Restore from backup
```bash
~/.claude/skills/wispr-fix/scripts/wispr-fix.sh restore latest
```

## Argument Parsing

When the user invokes `/wispr-fix` with arguments:

| Input | Action |
|-------|--------|
| `"X" "Y"` or `X Y` (two quoted/unquoted args) | `add "X" "Y"` |
| `flush` | `flush` |
| `flush --force-quit` | `flush --force-quit` |
| `dry-run` | `dry-run` |
| `list` | `list` |
| `remove "X"` | `remove "X"` |
| `restore latest` | `restore latest` |
| (no args) | `list` (show current queue) |

## Auto-Detect Pattern

When you see `wispr fix: X -> Y` in user text (the `wispr fix:` prefix is required):
1. Parse X (everything between `wispr fix:` and `->`)
2. Parse Y (everything after `->`)
3. Trim whitespace from both
4. Run `add "X" "Y"`
5. Confirm to the user: "Queued: 'X' -> 'Y'"

## Notes
- Corrections are queued instantly — no Wispr restart needed
- Flush quits Wispr, backs up DB, applies corrections, verifies integrity, exports dictionary, restarts Wispr
- The queue persists between sessions at `~/.claude/skills/wispr-fix/queue.jsonl`
- Applied corrections are logged in `queue.applied.jsonl`
- Backups are stored in `~/Library/Application Support/Wispr Flow/backups/` (last 10 retained)
