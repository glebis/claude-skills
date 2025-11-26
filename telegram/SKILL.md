---
name: telegram
description: This skill should be used when fetching, searching, downloading, or sending messages on Telegram. Use for queries like "show my Telegram messages", "search Telegram for...", "get unread messages", "send a message to...", or "add Telegram messages to my notes".
---

# Telegram Message Skill

Fetch, search, download, and send Telegram messages with flexible filtering and output options.

## Prerequisites

Authentication must be configured in `~/.telegram_dl/`. Run `setup` command to check status or get instructions:

```bash
python3 scripts/telegram_fetch.py setup
```

If not configured, follow these steps:
1. Get API credentials from https://my.telegram.org/auth
2. Clone telegram_dl: https://github.com/glebis/telegram_dl
3. Run `python telegram_dl.py` and follow interactive prompts
4. Verify with `python3 scripts/telegram_fetch.py setup`

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
python3 scripts/telegram_fetch.py recent --chat "Tool Building Ape"
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
python3 scripts/telegram_fetch.py send --chat "Tool Building Ape" --text "Thanks!" --reply-to 12345

# Send to a forum topic (for groups with topics enabled)
python3 scripts/telegram_fetch.py send --chat "Group Name" --text "Hello topic!" --topic 12
```

### Send Files

To send images, documents, or videos:

```bash
# Send an image
python3 scripts/telegram_fetch.py send --chat "John Doe" --file "/path/to/image.jpg"

# Send document with caption
python3 scripts/telegram_fetch.py send --chat "@username" --file "report.pdf" --text "Here's the report"

# Reply with media
python3 scripts/telegram_fetch.py send --chat "Group" --file "screenshot.png" --reply-to 12345
```

**Chat resolution order:**
1. `@username` - Resolves Telegram username directly
2. Numeric ID - Resolves chat by Telegram ID
3. Name match - Fuzzy search in existing dialogs

Returns JSON with send status, resolved chat name, message ID, and file info (for media).

### Download Attachments

To download media files from a chat:

```bash
# Download last 5 attachments from a chat (default)
python3 scripts/telegram_fetch.py download --chat "Tool Building Ape"

# Download last 10 attachments
python3 scripts/telegram_fetch.py download --chat "Project Group" --limit 10

# Download to custom directory
python3 scripts/telegram_fetch.py download --chat "@username" --output "/path/to/folder"

# Download from specific message
python3 scripts/telegram_fetch.py download --chat "John Doe" --message-id 12345
```

**Default output:** `~/Downloads/telegram_attachments/`

Returns JSON with download results (file names, paths, sizes).

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

### Save to File (Token-Efficient)

Save messages directly to file without consuming context tokens:

```bash
# Save 100 messages to markdown file
python3 scripts/telegram_fetch.py recent --chat "AGENCY: Community" --limit 100 -o ~/chat_archive.md

# Save with media files downloaded to same folder
python3 scripts/telegram_fetch.py recent --chat "Project Group" --limit 50 -o ~/project/archive.md --with-media

# Save search results to file
python3 scripts/telegram_fetch.py search "meeting" -o ~/meetings.md
```

Returns JSON with save status (file path, message count, media download results) - minimal token usage.

## Example User Requests

When user asks:

- "Show my recent Telegram messages" -> `recent --limit 20`
- "What Telegram messages did I get today?" -> `recent --days 1`
- "Search Telegram for messages about the project" -> `search "project"`
- "Get unread messages from Tool Building Ape" -> `unread` + filter output
- "Add my Telegram messages to daily note" -> `recent --to-daily`
- "What chats do I have on Telegram?" -> `list`
- "Send hello to John on Telegram" -> `send --chat "John" --text "Hello!"`
- "Message @username on Telegram" -> `send --chat "@username" --text "..."`
- "Reply to that message with thanks" -> `send --chat "..." --text "Thanks!" --reply-to <id>`
- "Send this image to John" -> `send --chat "John" --file "/path/to/image.jpg"`
- "Send report.pdf with caption" -> `send --chat "..." --file "report.pdf" --text "Here's the report"`
- "Send to topic 12 in Group" -> `send --chat "Group" --text "..." --topic 12`
- "Download attachments from Tool Building Ape" -> `download --chat "Tool Building Ape"`
- "Download last 10 files from Project Group" -> `download --chat "Project Group" --limit 10`
- "Save last 100 messages from AGENCY to file" -> `recent --chat "AGENCY: Community" --limit 100 -o ~/agency.md`
- "Archive chat with media" -> `recent --chat "Group" -o ~/archive.md --with-media`
- "Is Telegram configured?" -> `setup`
- "How do I set up Telegram?" -> `setup` (returns instructions if not configured)

## Rate Limiting

The script includes built-in rate limiting (0.1s between messages) and handles Telegram's FloodWaitError automatically with backoff.

## Dependencies

Requires `telethon` Python package. Install with: `pip install telethon`
