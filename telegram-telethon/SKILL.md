---
name: telegram-telethon
description: This skill should be used for comprehensive Telegram automation via Telethon API. Use for sending/receiving messages, monitoring chats, running a background daemon that triggers Claude Code sessions, managing channels/groups, and downloading media. Triggers on "telegram daemon", "monitor telegram", "telegram bot", "spawn Claude from telegram", or any Telethon-related request. IMPORTANT: Use `draft` command for "драфт/draft", use `send` for "отправь/send"; if ambiguous, ASK before sending.
---

## Claude Behavior Guidelines

### Draft vs Send: Follow User's Intent

| User says | Claude does | Clarify? |
|-----------|-------------|----------|
| "драфт", "draft", "сделай драфт" | `draft` | No |
| "отправь", "пошли", "send" | `send` | No |
| "напиши сообщение" (ambiguous) | Ask what user wants | Yes |

### Key Rules

1. **Explicit draft → draft**: "драфт", "draft" → use `draft` command immediately
2. **Explicit send → send**: "отправь", "пошли", "send" → use `send` command immediately
3. **Ambiguous → clarify**: If neither "draft" nor "send" verb present, ask: "Создать драфт или сразу отправить?"

### Examples

**User:** "сделай драфт для lv: привет"
**Claude:** Uses `draft --chat "lv" --text "привет"` immediately

**User:** "отправь сообщение Маше: встретимся в 5?"
**Claude:** Uses `send --chat "Маша" --text "встретимся в 5?"` immediately

**User:** "напиши сообщение для Маши: встретимся в 5?"
**Claude:** Asks "Создать драфт или сразу отправить?"

# Telegram Telethon Skill

Full Telethon API wrapper with daemon mode and Claude Code integration. Supports interactive setup, background message monitoring, and automatic Claude session spawning per chat.

## Package Layout

```
telegram-telethon/
├── SKILL.md                          # This file
├── pyproject.toml                    # Installable Python package
├── scripts/
│   ├── tg.py                         # Main CLI (messages, media, drafts, etc.)
│   └── tgd.py                        # Daemon controller
├── src/telegram_telethon/            # Importable package
│   ├── core/                         # auth, config
│   ├── modules/                      # messages, media
│   ├── daemon/                       # runner, handlers, claude_bridge
│   └── utils/                        # formatting
└── tests/                            # pytest unit + integration tests
```

Scripts import from `src/telegram_telethon`. Install the package in editable mode so `tg.py`/`tgd.py` can resolve imports:

```bash
cd telegram-telethon
pip install -e .
# or with dev tools (pytest, coverage):
pip install -e ".[dev]"
```

## Relationship to `telegram` Skill

The separate `telegram` skill (single-script `telegram_fetch.py` backed by `telegram_dl`) overlaps on list/recent/search/send/edit/download/thread but differs:

With the publish/markdown/schedule ports now complete, **`telegram-telethon` is a superset of `telegram`** on everything except the external `telegram_dl` auth dependency. Use this skill for:

- `publish` — draft→channel workflow (frontmatter, media albums, post-publish move + index update, post-flight lint)
- `--markdown` on `send` / `publish` — markdown→Telegram HTML conversion
- `--schedule` on `send` / `publish` — ISO / relative / natural-language scheduled delivery
- Daemon mode + Claude Code spawning, voice transcription (Telegram/Groq/Whisper), `delete` / `forward` / `mark-read`, local `draft` / `drafts` / `draft-send`, `lint-channel`, non-interactive auth setup.

## Prerequisites

### Interactive Setup (Terminal)

Run setup wizard on first use:

```bash
python3 scripts/tg.py setup
```

This guides through:
1. Getting API credentials from https://my.telegram.org/auth
2. Phone number verification
3. 2FA (if enabled)
4. Optional daemon trigger configuration

### Non-Interactive Setup (Claude Code)

For use from Claude Code or scripts without TTY:

```bash
# Step 1: Provide credentials and trigger code send
python3 scripts/tg.py setup --api-id 12345678 --api-hash abc123... --phone +1234567890

# Step 2: User receives code on phone, then complete auth
python3 scripts/tg.py setup --api-id 12345678 --api-hash abc123... --phone +1234567890 --code 12345

# If 2FA enabled, add password
python3 scripts/tg.py setup --api-id 12345678 --api-hash abc123... --phone +1234567890 --code 12345 --password mypassword
```

The script auto-detects TTY and switches between interactive/non-interactive modes.

## Quick Start

```bash
# Check connection status
python3 scripts/tg.py status

# List chats
python3 scripts/tg.py list

# Get recent messages from a chat
python3 scripts/tg.py recent "John Doe" --limit 20

# Search messages
python3 scripts/tg.py search "meeting notes"

# Configure daemon triggers interactively
python3 scripts/tg.py daemon-config

# Start daemon (foreground with logs)
python3 scripts/tgd.py start --foreground

# Start daemon (background)
python3 scripts/tgd.py start

# View daemon logs
python3 scripts/tgd.py logs
```

## CLI Commands

### Message Operations

```bash
# List all chats
python3 scripts/tg.py list [--limit 30] [--search "term"]

# Fetch recent messages
python3 scripts/tg.py recent [CHAT] [--limit 50] [--days 7] [--format markdown|json] [--output file.md]

# Search messages by content
python3 scripts/tg.py search QUERY [--chat "Chat Name"] [--limit 50] [--format markdown|json]

# Fetch unread messages
python3 scripts/tg.py unread [--chat "Chat Name"] [--format markdown|json]

# Fetch forum thread
python3 scripts/tg.py thread CHAT_ID THREAD_ID [--limit 100]

# Send message
python3 scripts/tg.py send --chat "Chat Name" --text "Message text" [--reply-to MSG_ID] [--file path] [--topic TOPIC_ID] [--markdown] [--html] [--schedule "+1h" | "tomorrow 10:00" | "2026-04-10T09:30"]

# Edit message
python3 scripts/tg.py edit --chat "Chat Name" --message-id MESSAGE_ID --text "New text"

# Delete messages
python3 scripts/tg.py delete --chat "Chat Name" --message-ids 123 456 789 [--no-revoke]

# Forward messages
python3 scripts/tg.py forward --from "Source" --to "Dest" --message-ids 123 456

# Mark messages as read
python3 scripts/tg.py mark-read --chat "Chat Name" [--max-id MSG_ID]
```

### Draft Operations

```bash
# Save/update a draft message
python3 scripts/tg.py draft --chat "Chat Name" --text "Draft text" [--reply-to MSG_ID] [--no-preview]

# Clear a draft (save empty text)
python3 scripts/tg.py draft --chat "Chat Name" --text ""

# Clear all drafts
python3 scripts/tg.py draft --clear-all

# List all drafts
python3 scripts/tg.py drafts [--limit 50]

# Send a draft as a message (clears the draft)
python3 scripts/tg.py draft-send --chat "Chat Name"
```

**Note:** Use `"me"` as the chat name to target Saved Messages (your own chat). The literal name "Saved Messages" doesn't work as it's localized differently per user.

### Media Operations

```bash
# Download media from chat
python3 scripts/tg.py download "Chat Name" [--limit 5] [--output-dir ~/Downloads] [--message-id ID] [--type voice|video|photo]

# Transcribe a single voice message (MESSAGE_ID required)
python3 scripts/tg.py transcribe "Chat Name" MESSAGE_ID [--method telegram|groq|whisper]

# Batch-transcribe recent voice messages (omit MESSAGE_ID, use --batch)
python3 scripts/tg.py transcribe "Chat Name" --batch [--limit 10] [--method telegram|groq|whisper]
```

### Publish a Draft to a Channel

End-to-end publish workflow: parse a draft markdown file, resolve the destination channel from folder structure or frontmatter `channel:`, upload media (single file or album), post-process to move the draft to `published/` and insert an entry in the channel index.

```bash
# Dry-run preview
python3 scripts/tg.py publish --draft "Channels/klodkot/drafts/20260416-post.md" --dry-run

# Publish now
python3 scripts/tg.py publish --draft "20260416-post"  # slug works too

# Publish scheduled for later
python3 scripts/tg.py publish --draft "..." --schedule "tomorrow 10:00"
```

The result JSON includes `published`, `channel`, `message_id`, `media_count`, `moved_to`, and — crucially — `lint_warnings` when the final body contains leaked markdown/HTML that Telegram wouldn't render. Post-publish bookkeeping failures (e.g. index write error) surface as `warnings` but don't roll back the send.

### Markdown Formatting on Send

Pass `--markdown` to convert a markdown-flavored message into Telegram HTML before sending:

```bash
python3 scripts/tg.py send --chat "@mychannel" --markdown \
  --text $'## Release\n\n**v2** ships _today_. See [docs](https://example.com).\n\n* fast\n* stable'
```

Rules (applied in order): `## Header` → bold line; `* item` / `- item` at line start → `→ item`; `**bold**` → `<b>`; `_italic_` → `<i>`; `[text](url)` → `<a href>`. Pre-existing HTML passes through unchanged, so the flag is safe to add to content that was already authored as HTML.

Pair with `lint-channel` below to catch cases where `--markdown` was forgotten.

### Sending Pre-written HTML

Pass `--html` to send text that already contains Telegram-compatible HTML tags (`<b>`, `<i>`, `<a href>`, `<code>`, `<pre>`, `<u>`, `<s>`, `<tg-spoiler>`, `<blockquote>`):

```bash
python3 scripts/tg.py send --chat "@mychannel" --html \
  --text '<b>Release v2</b> ships today. See <a href="https://example.com">docs</a>.'
```

Unlike `--markdown` (which converts markdown syntax to HTML), `--html` sends the text as-is with `parse_mode='html'`. Use `--html` when you have already authored HTML content or when programmatically building messages with tags.

### Scheduled Delivery

Pass `--schedule` with one of three formats (naive times default to Europe/Berlin):

```bash
# Relative: send in one hour
python3 scripts/tg.py send --chat "@mychannel" --text "..." --schedule "+1h"

# Natural: send tomorrow morning
python3 scripts/tg.py send --chat "@mychannel" --text "..." --schedule "tomorrow 09:30"

# Absolute: send at a specific time
python3 scripts/tg.py send --chat "@mychannel" --text "..." --schedule "2026-04-20T15:00"
```

The response includes ``"scheduled_for": "<iso datetime>"`` when the message is queued for later. Telegram displays scheduled messages in the chat's scheduled-messages view.

### Lint Published Messages

Scan a channel (or a single message) for unrendered markdown/HTML that leaked into the raw message text — i.e. the sender forgot `--markdown` or the HTML conversion failed, so readers see literal `**bold**`, `<b>…</b>`, `[text](url)`, or `## Header` in the post.

```bash
# Scan last 50 messages in @mychannel
python3 scripts/tg.py lint-channel --chat "@mychannel"

# Scan last 200 messages
python3 scripts/tg.py lint-channel --chat "@mychannel" --limit 200

# Lint a single message by ID
python3 scripts/tg.py lint-channel --chat "@mychannel" --message-id 1234

# Machine-readable output for pipelines / CI
python3 scripts/tg.py lint-channel --chat "@mychannel" --json
```

The detector lives in `modules/lint.py` as a pure function (`detect_unrendered_markup(text, entities)`), so it can also be called directly on drafts or wired into a post-flight check after publishing. Content inside `MessageEntityCode`/`MessageEntityPre` spans is ignored (inline code / code blocks are expected to contain raw characters).

### Obsidian Integration

`--to-daily` and `--to-person` are flags on the read commands (`recent`, `search`, `unread`), not standalone subcommands:

```bash
# Append recent messages to today's daily note (Daily/YYYYMMDD.md in the active vault)
python3 scripts/tg.py recent "Chat Name" --to-daily

# Append search results to today's daily note
python3 scripts/tg.py search "query" --to-daily

# Append recent messages to a person's note
python3 scripts/tg.py recent "Chat Name" --to-person "Person Name"
```

The target vault path is resolved by the formatting helpers in `utils/formatting.py`; there are currently no `--vault` or `--section` overrides on the CLI.

### Voice Transcription

The skill supports three transcription methods with automatic fallback:

1. **Telegram API** (default) - Uses Telegram Premium's server-side transcription
2. **Groq** - Uses Groq's Whisper API (requires `GROQ_API_KEY` environment variable)
3. **Whisper** - Uses local OpenAI Whisper model (requires `pip install openai-whisper`)

```bash
# Use Telegram's transcription (Premium feature)
python3 scripts/tg.py transcribe "Chat" 123

# Force Groq transcription
python3 scripts/tg.py transcribe "Chat" 123 --method groq

# Force local Whisper
python3 scripts/tg.py transcribe "Chat" 123 --method whisper
```

## Daemon Mode

The daemon monitors Telegram for messages matching configured triggers and can:
- Reply with static text
- Spawn Claude Code sessions to handle requests
- Resume existing Claude sessions per-chat
- Queue requests to prevent rate limiting

### Trigger Configuration

Triggers are stored in `~/.config/telegram-telethon/daemon.yaml`:

```yaml
triggers:
  # Respond to /claude command in DMs
  - chat: "@myusername"
    pattern: "^/claude (.+)$"
    action: claude
    reply_mode: inline

  # Respond to @Bot mentions in a group
  - chat: "AI Assistants"
    pattern: "@Bot (.+)$"
    action: claude
    reply_mode: new

  # Simple ping-pong in any chat
  - chat: "*"
    pattern: "^/ping$"
    action: reply
    reply_text: "pong"

claude:
  allowed_tools:
    - Read
    - Edit
    - Bash
    - WebFetch
  max_turns: 10
  timeout: 300

queue:
  max_concurrent: 1
  timeout: 600
```

### Trigger Fields

| Field | Description |
|-------|-------------|
| `chat` | Chat name, `@username`, or `*` for all chats |
| `pattern` | Regex pattern (capture group 1 becomes Claude prompt) |
| `action` | `claude`, `reply`, or `ignore` |
| `reply_mode` | `inline` (reply to message) or `new` (separate message) |
| `reply_text` | Static text for `reply` action |

### Claude Integration

When action is `claude`:
1. Text captured by regex group 1 is sent to Claude Code via `claude -p "..." --output-format json`
2. Claude sessions persist per-chat in `sessions.json`
3. Subsequent messages from same chat resume session via `--resume <session_id>`
4. Responses are sent back to Telegram as reply or new message

## Session Persistence

Claude sessions are saved to `~/.config/telegram-telethon/sessions.json`:
- Each chat_id maps to a Claude session_id
- Sessions survive daemon restarts
- Track message count and last used timestamp

To reset: delete chat entry from `sessions.json` or configure a `/reset` trigger.

## Example Configurations

### Personal AI Assistant

Respond to all DMs to yourself:

```yaml
triggers:
  - chat: "@yourusername"
    pattern: "(.+)"
    action: claude
    reply_mode: inline
```

### Group Bot with Mention Trigger

Only respond when @mentioned:

```yaml
triggers:
  - chat: "Dev Team"
    pattern: "@AssistantBot (.+)"
    action: claude
    reply_mode: inline
```

### Multi-Action Setup

```yaml
triggers:
  - chat: "*"
    pattern: "^/ask (.+)"
    action: claude
    reply_mode: inline

  - chat: "*"
    pattern: "^/ping$"
    action: reply
    reply_text: "pong"

  - chat: "Noisy Group"
    pattern: ".*"
    action: ignore
```

## File Structure

```
~/.config/telegram-telethon/
├── config.yaml        # API credentials (api_id, api_hash, phone)
├── daemon.yaml        # Daemon triggers and Claude config
├── session.session    # Telethon session file
├── sessions.json      # Claude session persistence
└── daemon.log         # Daemon log file
```

## Development

```bash
# Install with dev dependencies
cd telegram-telethon
pip install -e ".[dev]"

# Run all tests
pytest

# Run with coverage
pytest --cov=telegram_telethon

# Run specific test file
pytest tests/unit/test_claude_bridge.py -v
```

## Example User Requests

Mapping natural-language asks to commands:

| User says | Command |
|-----------|---------|
| "Is Telegram connected?" | `status` |
| "What chats do I have?" | `list` |
| "Find chat named X exactly" | `list --search "X"` (increase `--limit` if not found) |
| "Show recent messages from John" | `recent "John" --limit 20` |
| "Messages from the last week in Group Y" | `recent "Group Y" --days 7` |
| "Search Telegram for 'deadline'" | `search "deadline"` |
| "Unread messages from Group Z" | `unread --chat "Group Z"` |
| "Mark Group Z as read" | `mark-read --chat "Group Z"` |
| "Get thread 174 in Lab" | `thread <chat_id> 174 --limit 100` |
| "Send 'hi' to John" / "отправь John: hi" | `send --chat "John" --text "hi"` |
| "Post a markdown-formatted note to @channel" | `send --chat "@channel" --markdown --text "..."` |
| "Schedule this for tomorrow at 10am" | `send --chat "..." --text "..." --schedule "tomorrow 10:00"` |
| "Send this in an hour" | `send --chat "..." --text "..." --schedule "+1h"` |
| "Reply thanks to message 12345" | `send --chat "..." --text "thanks" --reply-to 12345` |
| "Send image.jpg to John" | `send --chat "John" --file image.jpg` |
| "Save a draft for John: hi" / "сделай драфт" | `draft --chat "John" --text "hi"` |
| "List my drafts" | `drafts` |
| "Send the draft for John" | `draft-send --chat "John"` |
| "Delete messages 123, 456 from John" | `delete --chat "John" --message-ids 123 456` |
| "Forward msg 789 from John to Maria" | `forward --from "John" --to "Maria" --message-ids 789` |
| "Edit message 76 in @channel" | `edit --chat "@channel" --message-id 76 --text "..."` |
| "Download last 5 voice notes from John" | `download "John" --type voice --limit 5` |
| "Transcribe voice message 512 from John" | `transcribe "John" 512` |
| "Batch-transcribe recent voices from John" | `transcribe "John" --batch --limit 10` |
| "Add John's messages to daily note" | `recent "John" --to-daily` |
| "Add messages to a person's note" | `recent "Chat" --to-person "Person Name"` |
| "Publish this draft to the klodkot channel" | `publish --draft "20260416-post"` |
| "Preview a draft before publishing" | `publish --draft "..." --dry-run` |
| "Publish this at 10am tomorrow" | `publish --draft "..." --schedule "tomorrow 10:00"` |
| "Check if @mychannel has unrendered markup" | `lint-channel --chat "@mychannel"` |
| "Lint message 1234 in @mychannel" | `lint-channel --chat "@mychannel" --message-id 1234` |
| "Start the Telegram daemon" | `python3 scripts/tgd.py start` (or `--foreground`) |
| "Show daemon logs" | `python3 scripts/tgd.py logs` |
| "Configure daemon triggers" | `daemon-config` |

**Saved Messages:** Use `"me"` (not "Saved Messages") — the label is localized per user.

## Troubleshooting

| Issue | Solution |
|-------|----------|
| "Config not found" | Run `python3 scripts/tg.py setup` |
| "Session expired" | Delete `session.session` and re-run setup |
| `ModuleNotFoundError: telegram_telethon` | Run `pip install -e .` from the skill directory |
| "Claude timeout" | Increase `timeout` in `daemon.yaml` |
| "Queue full" | Reduce request rate or wait |
| "No trigger matched" | Check `pattern` regex and `chat` name match |
| Chat not found by name | Increase `--limit` on `list` (default 30); may not be in recent dialogs |
