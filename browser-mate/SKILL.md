---
name: browser-mate
description: Use when automating a real, logged-in Chrome WITHOUT disturbing the user's open tabs — e.g. authenticated sessions like ChatGPT, LinkedIn, or any site needing a persistent login. Launches or reuses a dedicated debug Chrome instance per named profile that coexists with the user's main browser; it never quits or kills any browser (unlike real-browser, which closes Chrome Beta's tabs). Trigger on "automate this site without closing my tabs", "use my logged-in session", "open ChatGPT/LinkedIn in automation", or when a browser task must preserve the user's existing windows. macOS, requires the agent-browser CLI.
---

# browser-mate

Non-destructive Chrome automation. The problem it solves: to attach a CDP/`agent-browser`
session, Chrome must run with `--remote-debugging-port`. The `real-browser` skill achieves
this by **quitting Chrome Beta first**, destroying the user's open tabs. `browser-mate`
instead runs a **dedicated debug Chrome instance** (its own `--user-data-dir` + port) that
**coexists** with the user's main browser — Chrome permits concurrent instances when the
data dirs differ, so no quit is needed.

## The one invariant (never violate)

**Never quit, `pkill`, or `osascript quit` any browser.** The skill only ever launches a
new dedicated instance or reuses an existing one. The single `stop` path sends SIGTERM only
to a process matched by BOTH our dedicated `user_data_dir` AND our debug port — never the
user's browser.

## Usage

```bash
# Ensure a profile's debug Chrome is up (launch or reuse); prints the PORT on stdout
PORT=$(python3 scripts/browser.py chatgpt)

# Then drive it with agent-browser (always pass --cdp $PORT). See references/agent-browser.md
SID=$(LC_ALL=C tr -dc 'a-z0-9' < /dev/urandom | head -c 6)
agent-browser --cdp $PORT --session $SID open "https://chatgpt.com/"
agent-browser --cdp $PORT --session $SID snapshot -i
```

Other subcommands:

```bash
python3 scripts/browser.py list              # configured profiles
python3 scripts/browser.py status [profile]  # up/down
python3 scripts/browser.py stop chatgpt      # SIGTERM OUR instance only (graceful)
```

For the full `agent-browser` command set (click, fill, upload, screenshot, reliability,
upgrade gotchas), read `references/agent-browser.md`.

## Profiles

Config: `~/.config/browser-mate/profiles.json` (auto-created from `assets/profiles.example.json`
on first run). Each profile:

```json
{ "default": "automation",
  "profiles": {
    "automation": { "binary": "<chrome binary>", "user_data_dir": "~/.browser-mate/automation", "port": 9222 },
    "chatgpt":     { "binary": "<chrome binary>", "user_data_dir": "~/.browser-mate/chatgpt", "port": 9223, "default_url": "https://chatgpt.com/" }
  } }
```

- Each profile keeps its own login state — **log in once per profile, it persists**.
- Add a profile by editing the JSON: pick a **unique port** and a **dedicated `user_data_dir`**
  (the launcher validates uniqueness and refuses dirs that point at the user's real Chrome
  profile).

## Authentication

Cannot enter passwords (and must not). For a first-time login, launch the profile, then ask
the user to log in manually in that window once; the session persists in the profile's
`user_data_dir` for all future runs.

## Safety & limits

- **Loopback only.** The debug port binds to `127.0.0.1` (Chrome default). CDP has **no auth**
  — anyone local can drive it. Use on trusted machines; never pass `--remote-debugging-address`.
- **Dedicated data dir.** A profile's `user_data_dir` must never be the user's real Chrome
  profile (`~/Library/Application Support/Google/Chrome*`) — the launcher refuses these.
- **Locked dir.** If a profile's dir is already open in a non-debug Chrome window, the
  launcher **fails loudly rather than killing it**.
- Replaces `real-browser`'s launch step; interaction still uses `agent-browser`.
