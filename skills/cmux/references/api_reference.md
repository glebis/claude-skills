# cmux CLI Reference

Full CLI for the cmux macOS terminal app (built on Ghostty). All commands communicate via Unix socket at `/tmp/cmux.sock`.

## Global Flags
- `--socket <path>` – Unix socket location (default: `/tmp/cmux.sock`)
- `--json` – JSON output
- `--window <id>` – Target specific window

## System
```
cmux ping                    # Test socket connectivity
cmux capabilities            # List API capabilities
cmux identify                # Get current context (workspace, pane IDs)
```

## Workspace Commands
```
cmux list-workspaces
cmux new-workspace [--cwd <path>] [--command <cmd>]
cmux current-workspace
cmux select-workspace --workspace <id>
cmux close-workspace --workspace <id>
cmux rename-workspace <name>
cmux reorder-workspace --workspace <id> [--index <n>|--before <id>|--after <id>]
```

## Pane Commands
```
cmux list-panes [--workspace <id>]
cmux new-pane --direction <left|right|up|down> [--type <terminal|browser>] [--url <url>]
cmux focus-pane --pane <id>
cmux resize-pane --pane <id> [-R|-L|-U|-D] [--amount <n>]
cmux last-pane [--workspace <id>]
```

## Surface / Tab Commands
```
cmux list-panels [--workspace <id>]
cmux new-surface [--type <terminal|browser>] [--url <url>]
cmux new-split <left|right|up|down>
cmux close-surface [--surface <id>]
cmux focus-panel --panel <id>
cmux move-surface --surface <id> [--pane <id>|--workspace <id>] [--focus true]
cmux rename-tab <name> [--tab <id>]
cmux tab-action --action <next|previous|close|rename|reload> [--title <name>] [--url <url>]
```

## Terminal I/O
```
cmux send <text>             # Send text to active terminal
cmux send-key <key>          # Send keystroke
cmux read-screen [--scrollback] [--lines <n>]
cmux capture-pane [--scrollback] [--lines <n>]   # tmux alias
```

## Sidebar Status & Metadata
```
cmux set-status <key> <value> [--icon <name>] [--color <hex>]
cmux clear-status <key>
cmux list-status [--workspace <id>]
cmux set-progress <0-1> [--label <text>]
cmux clear-progress
cmux log <message> [--level <info|warn|error|debug>] [--source <name>]
cmux list-log [--limit <n>]
cmux clear-log [--workspace <id>]
```

## Notifications
```
cmux notify --title <title> [--subtitle <text>] [--body <text>]
cmux list-notifications
cmux clear-notifications
```

## Browser Automation
All browser commands prefixed with `cmux browser [--surface <id>]`:
```
cmux browser open <url>              # Open URL in new browser split
cmux browser navigate <url>
cmux browser reload
cmux browser url
cmux browser snapshot [--interactive] [--compact] [--selector <css>]
cmux browser eval <script>
cmux browser wait [--selector <css>|--text <str>|--url-contains <str>|--timeout <s>]
cmux browser click <selector>
cmux browser type <selector> <text>
cmux browser fill <selector> <text>
cmux browser screenshot [--out <path>] [--json]
cmux browser get <text|html|value|attr|title|url>
cmux browser find <role|text|label|placeholder> <value>
```

## Advanced
```
cmux tree [--all] [--workspace <id>]         # Display full hierarchy
cmux surface-health [--workspace <id>]
cmux trigger-flash [--surface <id>]          # Visual alert flash
cmux drag-surface-to-split --surface <id> <direction>
cmux refresh-surfaces
cmux hooks setup                              # Install Claude Code stop/notification hooks
cmux restore-session                          # Reapply last saved workspace snapshot
cmux claude-teams                             # Launch Claude Code teammate mode
```

## Exit Codes
- `0` – Success
- `1` – Error (message to stderr)

## Checking if cmux is available
```bash
cmux ping 2>/dev/null && echo "available" || echo "not available"
```
