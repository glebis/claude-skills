---
name: cmux
description: Controls the cmux macOS terminal app (Ghostty-based, AI-agent-aware) via its CLI socket API. Use this skill to: open browser preview panes when a dev server starts or an HTML file is created; spin up named workspaces for parallel subagents; show live sidebar progress/status during long tasks; open utility splits on demand (logs, URLs, terminals) in any direction. Also handles `/cmux demo` — an interactive walkthrough with 3 screens of options that runs personalized live demos. Trigger when: a server starts and needs previewing, an HTML/URL artifact is created, parallel subagents are dispatched, a long task needs visible progress, the user asks to open/show something in a split or tab, or the user invokes `/cmux demo`.
---

# cmux

Controls the cmux macOS terminal app via its CLI socket API to orchestrate workspaces, panes, browser previews, sidebar status, and notifications.

Full CLI reference: `references/api_reference.md`

## Quick Check

Always verify cmux is running before issuing commands:

```bash
cmux ping 2>/dev/null && echo "ok" || echo "cmux not available"
```

If unavailable, skip cmux enhancements silently — never block the main task.

## Core Use Cases

### 1. Auto Preview Routing

When a dev server starts or an HTML file is created, open it in a right-side browser pane:

```bash
# Dev server detected (e.g. localhost:3000)
cmux new-pane --type browser --direction right --url http://localhost:3000

# HTML file created — serve it first, then preview
cd <project-dir> && python3 -m http.server 8080 &
cmux new-pane --type browser --direction right --url http://localhost:8080/<file>.html
```

**When to trigger:**
- Output contains `localhost:PORT`, `127.0.0.1:PORT`, `Server running`, `Listening on`
- A `.html` file is written and the user would benefit from seeing it rendered
- superpowers or another skill opens a visual artifact

**Direction heuristic:** right for wide layouts, down for narrow/tall terminals.

---

### 2. Subagent Workspaces

When dispatching parallel agents (via `superpowers:dispatching-parallel-agents` or similar), give each agent its own named cmux workspace so it's visible in the sidebar:

```bash
# Create a workspace per agent (new-workspace has no --cwd — cd inside --command)
cmux new-workspace --command "cd /path/to/project && claude --dangerously-skip-permissions"
cmux rename-workspace "agent: fix-auth"

# Set status so the sidebar shows what the agent is doing
cmux set-status task "fix-auth" --icon "⚡"
cmux set-status state "running" --color "#F59E0B"
```

When an agent completes:
```bash
cmux notify --title "Agent done" --subtitle "fix-auth" --body "Merged and cleaned up"
cmux set-status state "done" --color "#10B981"
```

**Pattern:** workspace 1 = orchestrator, workspaces 2–8 = subagents. Use `cmux list-workspaces --json` to track IDs.

---

### 3. Sidebar Status & Progress

Show live feedback for long-running tasks without interrupting the main session:

```bash
# Task start
cmux set-progress 0 --label "Building..."
cmux set-status phase "build" --icon "🔨"

# Midpoint update
cmux set-progress 0.5 --label "Running tests..."
cmux set-status phase "test" --icon "🧪"

# Completion
cmux set-progress 1 --label "Done"
cmux notify --title "Task complete" --body "All tests passed"
cmux clear-progress
```

Use `cmux log <message> --level info` to append entries to the workspace log panel (visible via `⌘I`).

**When to use:** any task taking >10 seconds — file processing, test runs, builds, research sweeps, code generation loops.

---

### 4. Utility Splits on Demand

Open any content in a split pane in the requested direction:

```bash
# Open a URL in a browser split
cmux new-pane --type browser --direction right --url <url>

# Open a terminal split running a command (e.g. log tail)
cmux new-pane --type terminal --direction down
cmux send "tail -f /path/to/server.log"
cmux send-key "Enter"

# Resize to make it a narrow utility strip
cmux resize-pane --pane <id> -D --amount 20   # shrink height by 20 rows
```

**Direction mapping for natural language:**
| User says | Direction flag |
|---|---|
| "on the right" / "beside" | `--direction right` |
| "on the left" | `--direction left` |
| "below" / "at the bottom" | `--direction down` |
| "above" / "at the top" | `--direction up` |
| "in a new tab" / "new workspace" | `cmux new-workspace` |

---

### 5. Workspace & Tab Actions

`workspace-action` and `tab-action` expose the right-click context-menu actions.
Full table with flags in `references/api_reference.md` — the available action names are:

**`cmux workspace-action --action <name>`** (sidebar workspaces):
`pin` · `unpin` · `rename` (needs `--title`) · `clear-name` · `move-up` · `move-down` ·
`move-top` · `mark-read` · `mark-unread` · `close-others` · `close-above` · `close-below`

**`cmux tab-action --action <name>`** (horizontal tabs):
`rename` · `clear-name` · `pin` · `unpin` · `reload` · `duplicate` ·
`new-terminal-right` · `new-browser-right` · `mark-read` · `mark-unread` ·
`close-left` · `close-right` · `close-others`

> ⚠️ **Destructive actions act on OTHER tabs, not the one you name.**
> `close-others` / `close-above` / `close-below` (workspace) and
> `close-left` / `close-right` / `close-others` (tab) close everything *except* the
> target. `close-others` spares **pinned** workspaces only. Never run these to
> "test" — they will close the user's live tabs. Prefer `close-workspace --workspace <id>`
> to close one specific workspace.

**Renaming / selecting (common gotchas):**
- Rename the sidebar/switcher label → `cmux workspace-action --action rename --title "<name>"`
  (or `cmux rename-workspace <name>`). `rename-tab` only renames an inner tab and does
  **not** change the switcher label.
- Select/focus a workspace → `cmux select-workspace --workspace <id>`. There is no
  `--action select` (it errors "Unknown workspace action").

When unsure of a command's exact flags, run `cmux <command> --help` — every command
embeds full usage.

---

## Combining Use Cases

**Full workflow example — superpowers runs a subagent that builds a UI:**

```bash
# 1. Announce work in sidebar
cmux set-progress 0 --label "Scaffolding UI..."
cmux set-status agent "ui-builder" --icon "🎨"

# 2. Subagent does its work...

# 3. Server starts → auto-preview
cmux new-pane --type browser --direction right --url http://localhost:5173

# 4. Mark done
cmux set-progress 1 --label "Preview ready"
cmux notify --title "UI ready" --body "Preview open on the right"
cmux clear-progress
```

## Demo Mode (`/cmux demo`)

When invoked as `/cmux demo`, run an interactive personalized walkthrough. Always verify `cmux ping` first — abort with a clear message if unavailable.

### Screen 1 — Workflow

Ask with `AskUserQuestion`:

```
question: "What best describes how you work?"
header: "Workflow"
options:
  - label: "Coding agent manager"
    description: "Running multiple Claude sessions in parallel"
  - label: "Web dev"
    description: "Browser preview, dev servers, HTML artifacts"
  - label: "Research / long tasks"
    description: "Vault work, builds, sweeps that take minutes"
  - label: "Show me everything"
    description: "Run all demos back to back"
```

### Screen 2 — Mode

```
question: "How do you want to explore?"
header: "Demo mode"
options:
  - label: "Walk me through it"
    description: "Step by step with explanations between each demo"
  - label: "Auto-run"
    description: "Run all relevant demos back to back, narrate as you go"
  - label: "Just the commands"
    description: "Show what you'd run, skip execution"
```

### Screen 3 — tmux

```
question: "Do you use tmux?"
header: "tmux"
options:
  - label: "Yes, daily"
    description: "Show me the cmux + tmux combo"
  - label: "For SSH / remote only"
    description: "Show the remote persistence pattern"
  - label: "Not really"
    description: "Skip tmux, focus on cmux-native features"
```

### Demo Catalog

Run demos based on Screen 1 answer. Each demo: announce what's happening, execute the commands, narrate what the user is seeing, suggest what to try next.

**A — Browser preview pane** (web dev, show everything)
1. Create `/tmp/cmux-preview.html` with a minimal styled page
2. `python3 -m http.server <PORT> --directory /tmp &`
3. `cmux new-pane --type browser --direction right --url http://localhost:<PORT>/cmux-preview.html`
4. Use `cmux browser --surface <id> screenshot` to show the rendered result inline
5. Suggest: "Try editing the HTML — navigate the browser pane to reload"

**B — Sidebar progress** (research / long tasks, show everything)
1. Animate through 0→0.3→0.7→1.0 with label changes (`set-progress`, `set-status`)
2. Fire `cmux notify` on completion
3. `cmux log` a few entries, mention `⌘I` to open the log panel
4. Suggest: "Watch this sidebar during your next vault scan or research sweep"

**C — Subagent workspaces** (coding agent manager, show everything)
1. `cmux new-workspace --command "echo 'agent: fix-auth'"` + rename
2. `cmux set-status` with agent name + color
3. `cmux notify` simulating completion
4. `cmux close-workspace` cleanup
5. Suggest: "Next time you run parallel agents via /dispatching-parallel-agents, this happens automatically"

**D — tmux inside cmux** (if Screen 3 = daily or SSH)
1. `cmux new-pane --type terminal --direction right`
2. `cmux send --surface <id> "tmux new-session -s work\n"`
3. Build 2–3 named windows (`editor`, `server`, `git`)
4. Capture with `cmux read-screen --surface <id>` and show output
5. Suggest: "tmux keeps the session alive if cmux restarts. Use `tmux attach -t work` to reconnect."

**E — Utility split on demand** (all workflows)
1. `cmux new-pane --type terminal --direction down`
2. Send a `tail -f` or `git log --follow -p` command into it
3. `cmux resize-pane -D --amount 10` to shrink it to a strip
4. Suggest: "Say 'open a log strip at the bottom' during any task and this happens automatically"

### Auto mode

In auto mode (Screen 2 = "Auto-run"):
- Run all demos relevant to Screen 1 without pausing for confirmation
- Use `cmux set-progress` and `cmux set-status` to show overall demo progress in the sidebar
- Narrate each step in text as it executes
- At the end: print a summary of what ran and key shortcuts to remember

### Cleanup

After each demo (or at the end of auto mode), close any panes/workspaces/processes created:
```bash
cmux close-surface --surface <id>   # or close-workspace
kill <server-pid>
cmux clear-progress
cmux clear-status <key>
```

---

## Error Handling

- If `cmux ping` fails: skip all cmux calls, proceed with task normally
- If a `new-pane` or `new-workspace` call fails: log a warning, don't retry
- Never let cmux failures block or slow down the main task
- In demo mode: if a command fails, explain what should have happened and move on
