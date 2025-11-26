---
name: telegram
description: This skill should be used when fetching, searching, downloading, or sending messages on Telegram. Use for queries like "show my Telegram messages", "search Telegram for...", "get unread messages", "send a message to...", or "add Telegram messages to my notes".
---

# Telegram Message Skill

Fetch, search, download, and send Telegram messages with flexible filtering and output options.

## Prerequisites

Authentication must be configured in `~/.telegram_dl/`. If not configured, run `telegram_dl.py` from `/Users/glebkalinin/ai_projects/telegram_dl/` first to authenticate.

## Quick Start

Run the script at `scripts/telegram_fetch.py` with appropriate commands:

```bash
# List available chats
python3 scripts/telegram_fetch.py list

# Get recent messages
python3 scripts/telegram_fetch.py recent --limit 20

# Search messages
python3 scripts/telegram_fetch.py search "meeting"

# Get unread messages
python3 scripts/telegram_fetch.py unread
```

## Commands

### List Chats

To see available Telegram chats:

```bash
python3 scripts/telegram_fetch.py list
python3 scripts/telegram_fetch.py list --limit 50
python3 scripts/telegram_fetch.py list --search "AI"
```

Returns JSON with chat IDs, names, types, and unread counts.

### Fetch Recent Messages

To get recent messages:

```bash
# From all chats (last 50 messages across top 10 chats)
python3 scripts/telegram_fetch.py recent

# From specific chat
python3 scripts/telegram_fetch.py recent --chat "AI Mindset"
python3 scripts/telegram_fetch.py recent --chat-id 123456789

# With limits
python3 scripts/telegram_fetch.py recent --limit 100
python3 scripts/telegram_fetch.py recent --days 7
```

### Search Messages

To search message content:

```bash
# Global search across all chats
python3 scripts/telegram_fetch.py search "project deadline"

# Search in specific chat
python3 scripts/telegram_fetch.py search "meeting" --chat-id 123456789

# Limit results
python3 scripts/telegram_fetch.py search "important" --limit 20
```

### Fetch Unread Messages

To get only unread messages:

```bash
python3 scripts/telegram_fetch.py unread
python3 scripts/telegram_fetch.py unread --chat-id 123456789
```

### Send Messages

To send a message to a chat:

```bash
# Send to existing chat by name
python3 scripts/telegram_fetch.py send --chat "John Doe" --text "Hello!"

# Send to username (works even without prior conversation)
python3 scripts/telegram_fetch.py send --chat "@username" --text "Hello!"

# Reply to a specific message (use message ID from recent/search output)
python3 scripts/telegram_fetch.py send --chat "AI Mindset" --text "Thanks!" --reply-to 12345
```

**Chat resolution order:**
1. `@username` - Resolves Telegram username directly
2. Numeric ID - Resolves chat by Telegram ID
3. Name match - Fuzzy search in existing dialogs

Returns JSON with send status, resolved chat name, and message ID.

## Output Options

### Default (Markdown to stdout)

By default, outputs formatted markdown suitable for Claude to read and summarize.

### JSON Format

Add `--json` flag for structured data:

```bash
python3 scripts/telegram_fetch.py recent --json
```

### Append to Obsidian Daily Note

Add messages to today's daily note in the vault:

```bash
python3 scripts/telegram_fetch.py recent --to-daily
python3 scripts/telegram_fetch.py search "project" --to-daily
```

Appends to `~/Brains/brain/Daily/YYYYMMDD.md`

### Append to Person's Note

Add messages to a specific person's note:

```bash
python3 scripts/telegram_fetch.py recent --chat "John Doe" --to-person "John Doe"
```

Creates or appends to `~/Brains/brain/{PersonName}.md`

## Example User Requests

When user asks:

- "Show my recent Telegram messages" -> `recent --limit 20`
- "What Telegram messages did I get today?" -> `recent --days 1`
- "Search Telegram for messages about the project" -> `search "project"`
- "Get unread messages from AI Mindset" -> `unread` + filter output
- "Add my Telegram messages to daily note" -> `recent --to-daily`
- "What chats do I have on Telegram?" -> `list`
- "Send hello to John on Telegram" -> `send --chat "John" --text "Hello!"`
- "Message @username on Telegram" -> `send --chat "@username" --text "..."`
- "Reply to that message with thanks" -> `send --chat "..." --text "Thanks!" --reply-to <id>`

## Rate Limiting

The script includes built-in rate limiting (0.1s between messages) and handles Telegram's FloodWaitError automatically with backoff.

## Dependencies

Requires `telethon` Python package. Install with: `pip install telethon`
