# cmux CLI Reference

Full CLI for the cmux macOS terminal app (built on Ghostty). All commands
communicate via a Unix socket (default `/tmp/cmux.sock`). The CLI binary lives at
`/Applications/cmux.app/Contents/Resources/bin/cmux`.

> This reference is generated from the live `cmux --help` and `cmux <command> --help`
> output. When in doubt, run `cmux <command> --help` — every command embeds full
> usage, flags, and examples. Run `cmux --help` for the complete command list.

## Handles & IDs

Most commands accept any of these for `--workspace` / `--surface` / `--pane` / `--tab`:
- **UUID** — e.g. `A86B2F94-DF74-...`
- **short ref** — `window:1`, `workspace:2`, `pane:3`, `surface:4` (`tab-action` also takes `tab:<n>`)
- **index** — positional integer

Output defaults to refs. Pass `--id-format uuids` or `--id-format both` to include UUIDs.
Resolve refs with `cmux list-workspaces` / `list-panes` / `list-pane-surfaces`.

## Global Flags
- `--socket <path>` — Unix socket location (default `/tmp/cmux.sock`, or `$CMUX_SOCKET_PATH`)
- `--window <id>` — target a specific window
- `--password <pw>` — socket auth (`--password` > `$CMUX_SOCKET_PASSWORD` > keychain)
- `--json` — JSON output
- `--id-format refs|uuids|both`

## Environment (auto-set inside cmux terminals)
- `CMUX_WORKSPACE_ID` — default `--workspace` for ALL commands
- `CMUX_SURFACE_ID` — default `--surface`
- `CMUX_TAB_ID` — default `--tab` for `tab-action`/`rename-tab`
- `CMUX_SOCKET_PATH` — override socket path

---

## ⚠️ Context-Menu Actions (`workspace-action` / `tab-action`)

These two commands expose the right-click context-menu actions. **Several are
destructive and act on tabs OTHER than the one you name** — read before using.

### `cmux workspace-action --action <name> [--workspace <id>] [--title <text>]`

| Action | Effect | Destructive |
|---|---|---|
| `pin` / `unpin` | Pin/unpin the workspace (pinned tabs survive `close-others`) | no |
| `rename` | Rename the workspace (the sidebar/switcher label) — needs `--title` | no |
| `clear-name` | Reset to the auto-derived name | no |
| `move-up` / `move-down` / `move-top` | Reorder in the sidebar | no |
| `close-others` | **Closes every OTHER unpinned workspace in the window** | ⚠️ YES |
| `close-above` / `close-below` | **Closes unpinned workspaces above/below this one** | ⚠️ YES |
| `mark-read` / `mark-unread` | Toggle the unread indicator | no |

### `cmux tab-action --action <name> [--tab <id>] [--title <text>] [--url <url>]`

| Action | Effect | Destructive |
|---|---|---|
| `rename` / `clear-name` | Rename / reset the tab title (needs `--title` for rename) | no |
| `pin` / `unpin` | Pin/unpin the tab | no |
| `reload` | Reload the tab (re-runs the browser/terminal surface) | no |
| `duplicate` | Open a copy of the tab | no |
| `new-terminal-right` / `new-browser-right` | New terminal/browser tab to the right (`--url` for browser) | no |
| `mark-read` / `mark-unread` | Toggle unread indicator | no |
| `close-left` / `close-right` / `close-others` | **Close tabs to the left/right, or all others** | ⚠️ YES |

> **Renaming:** to rename the sidebar/switcher label use
> `workspace-action --action rename --title "<name>"` (or the top-level
> `rename-workspace <name>`). `rename-tab` only renames an *inner* tab/surface —
> it does NOT change the switcher label, and silently no-ops on the title shown by
> `list-workspaces`.
>
> **To SELECT/focus a workspace** there is no action — use the top-level
> `select-workspace --workspace <id>` (or `focus-pane`). `workspace-action --action select`
> is invalid ("Unknown workspace action").

---

## System
```
cmux version
cmux ping                    # test socket connectivity (use to gate all cmux calls)
cmux capabilities            # list supported API methods
cmux identify [--workspace <id>] [--surface <id>] [--no-caller]
```

## Windows
```
cmux list-windows
cmux current-window
cmux new-window
cmux focus-window --window <id>
cmux close-window --window <id>
cmux next-window | previous-window | last-window
cmux rename-window [--workspace <id>] <title>
```

## Workspaces
```
cmux list-workspaces
cmux current-workspace
cmux new-workspace [--command <text>]          # NOTE: no --cwd flag exists
cmux select-workspace --workspace <id>         # the way to focus/switch a workspace
cmux close-workspace --workspace <id>
cmux rename-workspace [--workspace <id>] <title>
cmux reorder-workspace --workspace <id> (--index <n> | --before <id> | --after <id>) [--window <id>]
cmux move-workspace-to-window --workspace <id> --window <id>
cmux workspace-action --action <name> ...      # see action table above
```

## Panes
```
cmux list-panes [--workspace <id>]
cmux new-pane [--type terminal|browser] [--direction left|right|up|down] [--workspace <id>] [--url <url>]
cmux new-split <left|right|up|down> [--workspace <id>] [--surface <id>] [--panel <id>]
cmux focus-pane --pane <id> [--workspace <id>]
cmux last-pane [--workspace <id>]
cmux resize-pane --pane <id> (-L|-R|-U|-D) [--amount <n>] [--workspace <id>]   # tmux-style
cmux swap-pane --pane <id> --target-pane <id> [--workspace <id>]
cmux break-pane [--workspace <id>] [--pane <id>] [--surface <id>] [--no-focus]
cmux join-pane --target-pane <id> [--workspace <id>] [--pane <id>] [--surface <id>] [--no-focus]
```

## Surfaces / Tabs / Panels
```
cmux list-pane-surfaces [--workspace <id>] [--pane <id>]
cmux new-surface [--type terminal|browser] [--pane <id>] [--workspace <id>] [--url <url>]
cmux close-surface [--surface <id>] [--workspace <id>]
cmux move-surface --surface <id> [--pane <id>] [--workspace <id>] [--window <id>] [--before <id>|--after <id>|--index <n>] [--focus true|false]
cmux reorder-surface --surface <id> (--index <n> | --before <id> | --after <id>)
cmux drag-surface-to-split --surface <id> <left|right|up|down>
cmux rename-tab [--workspace <id>] [--tab <id>] [--surface <id>] <title>   # inner tab only — see note above
cmux tab-action --action <name> ...           # see action table above
cmux list-panels [--workspace <id>]
cmux focus-panel --panel <id> [--workspace <id>]
cmux refresh-surfaces
cmux surface-health [--workspace <id>]
cmux trigger-flash [--workspace <id>] [--surface <id>]
```

## Terminal I/O
```
cmux send [--workspace <id>] [--surface <id>] <text>
cmux send-key [--workspace <id>] [--surface <id>] <key>
cmux send-panel --panel <id> [--workspace <id>] <text>
cmux send-key-panel --panel <id> [--workspace <id>] <key>
cmux read-screen [--workspace <id>] [--surface <id>] [--scrollback] [--lines <n>]
cmux capture-pane [--workspace <id>] [--surface <id>] [--scrollback] [--lines <n>]   # tmux alias of read-screen
cmux clear-history [--workspace <id>] [--surface <id>]
cmux respawn-pane [--workspace <id>] [--surface <id>] [--command <cmd>]
cmux pipe-pane --command <shell-command> [--workspace <id>] [--surface <id>]
```

## Sidebar Status & Metadata
```
cmux set-status <key> <value> [--icon <name>] [--color <#hex>] [--workspace <id>]
cmux clear-status <key> [--workspace <id>]
cmux list-status [--workspace <id>]
cmux set-progress <0.0-1.0> [--label <text>] [--workspace <id>]
cmux clear-progress [--workspace <id>]
cmux log [--level <info|warn|error|debug>] [--source <name>] [--workspace <id>] [--] <message>
cmux list-log [--limit <n>] [--workspace <id>]
cmux clear-log [--workspace <id>]
cmux sidebar-state [--workspace <id>]
```

## Notifications & Claude hooks
```
cmux notify --title <text> [--subtitle <text>] [--body <text>] [--workspace <id>] [--surface <id>]
cmux list-notifications
cmux clear-notifications
cmux claude-hook <session-start|stop|notification> [--workspace <id>] [--surface <id>]
```

## tmux-compatibility helpers
```
cmux find-window [--content] [--select] <query>
cmux wait-for [-S|--signal] <name> [--timeout <seconds>]
cmux set-hook [--list] [--unset <event>] | <event> <command>
cmux set-buffer [--name <name>] <text>
cmux list-buffers
cmux paste-buffer [--name <name>] [--workspace <id>] [--surface <id>]
cmux popup
cmux display-message [-p|--print] <text>
cmux copy-mode
cmux bind-key | unbind-key
cmux set-app-focus <active|inactive|clear>
cmux simulate-app-active
```

## Browser Automation
All prefixed with `cmux browser [--surface <id>]`. Highlights (run `cmux browser` for the full list):
```
cmux browser open [url]                  # create a browser split in the caller's workspace
cmux browser open-split [url]
cmux browser goto|navigate <url> [--snapshot-after]
cmux browser back|forward|reload [--snapshot-after]
cmux browser url|get-url
cmux browser snapshot [--interactive|-i] [--cursor] [--compact] [--max-depth <n>] [--selector <css>]
cmux browser eval <script>
cmux browser wait [--selector <css>] [--text <t>] [--url-contains <t>] [--load-state interactive|complete] [--function <js>] [--timeout-ms <ms>]
cmux browser click|dblclick|hover|focus|check|uncheck|scroll-into-view <selector> [--snapshot-after]
cmux browser type <selector> <text> [--snapshot-after]
cmux browser fill <selector> [text] [--snapshot-after]    # empty text clears
cmux browser press|keydown|keyup <key> [--snapshot-after]
cmux browser select <selector> <value> [--snapshot-after]
cmux browser scroll [--selector <css>] [--dx <n>] [--dy <n>] [--snapshot-after]
cmux browser get <url|title|text|html|value|attr|count|box|styles> [...]
cmux browser is <visible|enabled|checked> <selector>
cmux browser find <role|text|label|placeholder|alt|title|testid|first|last|nth> ...
cmux browser frame <selector|main>
cmux browser dialog <accept|dismiss> [text]
cmux browser download [wait] [--path <path>] [--timeout-ms <ms>]
cmux browser cookies <get|set|clear> [...]
cmux browser storage <local|session> <get|set|clear> [...]
cmux browser tab <new|list|switch|close|<index>> [...]
cmux browser console <list|clear>
cmux browser errors <list|clear>
cmux browser highlight <selector>
cmux browser state <save|load> <path>
cmux browser addinitscript|addscript <script>
cmux browser addstyle <css>
```
Note: cmux's browser is a WKWebView — `viewport`, `geolocation`, `offline`, `trace`,
`network`, `screencast`, `input` return `not_supported`.
Legacy aliases still work: `open-browser`, `navigate`, `browser-back`, `browser-forward`, `browser-reload`, `get-url`.

## Exit Codes
- `0` — success
- `1` — error (message to stderr)

## Availability gate
```bash
cmux ping 2>/dev/null && echo "available" || echo "not available"
```
If unavailable, skip all cmux enhancements silently — never block the main task.
