---
name: telegram-telethon
description: This skill should be used for comprehensive Telegram automation via Telethon API. Use for sending/receiving messages, monitoring chats, running a background daemon that triggers Claude Code sessions, managing channels/groups, and downloading media. Triggers on "telegram daemon", "monitor telegram", "telegram bot", "spawn Claude from telegram", or any Telethon-related request.
---

# Telegram Telethon Skill

Full Telethon API wrapper with daemon mode and Claude Code integration. Supports interactive setup, background message monitoring, and automatic Claude session spawning per chat.

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
python3 scripts/tg.py send --chat "Chat Name" --text "Message text" [--reply-to MSG_ID] [--file path] [--topic TOPIC_ID]

# Edit message
python3 scripts/tg.py edit --chat "Chat Name" --message-id MESSAGE_ID --text "New text"

# Delete messages
python3 scripts/tg.py delete --chat "Chat Name" --message-ids 123 456 789 [--no-revoke]

# Forward messages
python3 scripts/tg.py forward --from "Source" --to "Dest" --message-ids 123 456

# Mark messages as read
python3 scripts/tg.py mark-read --chat "Chat Name" [--max-id MSG_ID]
```

### Media Operations

```bash
# Download media from chat
python3 scripts/tg.py download "Chat Name" [--limit 5] [--output-dir ~/Downloads] [--message-id ID] [--type voice|video|photo]

# Transcribe voice messages
python3 scripts/tg.py transcribe "Chat Name" MESSAGE_ID [--method telegram|groq|whisper]

# Batch transcribe voice messages
python3 scripts/tg.py transcribe "Chat Name" --batch [--limit 10]
```

### Obsidian Integration

```bash
# Append messages to today's daily note
python3 scripts/tg.py to-daily "Chat Name" [--vault ~/Brains/brain] [--section "Telegram"]

# Append messages to a person's note
python3 scripts/tg.py to-person "Chat Name" "Person Name" [--vault ~/Brains/brain]
```

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

## Troubleshooting

| Issue | Solution |
|-------|----------|
| "Config not found" | Run `python3 scripts/tg.py setup` |
| "Session expired" | Delete `session.session` and re-run setup |
| "Claude timeout" | Increase `timeout` in `daemon.yaml` |
| "Queue full" | Reduce request rate or wait |
| "No trigger matched" | Check `pattern` regex and `chat` name match |
