---
name: telegram
description: This skill should be used when fetching, searching, downloading, sending, editing, or publishing messages on Telegram. Use for queries like "show my Telegram messages", "search Telegram for...", "get unread messages", "send a message to...", "edit that message", "publish this draft to klodkot", or "add Telegram messages to my notes".
---

# Telegram Message Skill

Fetch, search, download, send, and publish Telegram messages with flexible filtering and output options.

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
python3 scripts/telegram_fetch.py list --search "claude code глеб + саши" --exact
```

**Options:**
- `--search "text"`: Filter by substring match (case-insensitive)
- `--exact`: Require exact name match instead of substring (use with --search)
- `--limit N`: Max chats to retrieve (default: 30, increase if chat not found)

**Important:** If you're looking for a specific chat by exact name and it's not found, increase `--limit` to 100 or 200, as the chat may not be in the most recent 30.

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

# Send with markdown formatting (converts **bold**, _italic_, [links](url) to Telegram HTML)
python3 scripts/telegram_fetch.py send --chat "@username" --text "**Bold** and _italic_ text" --markdown
```

**Formatting (`--markdown` flag):**
- Without `--markdown`: text is sent as-is (plain text, no formatting)
- With `--markdown`: converts markdown to Telegram HTML (`**bold**` -> bold, `_italic_` -> italic, `[text](url)` -> link, `## Header` -> bold, `* item` -> arrow list)
- **IMPORTANT**: Always use `--markdown` when sending draft content that contains markdown formatting
- The `publish` command handles markdown conversion automatically; the `send` command does NOT unless `--markdown` is specified

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

### Edit Messages

To edit an existing message:

```bash
# Edit a message by ID
python3 scripts/telegram_fetch.py edit --chat "@mentalhealthtech" --message-id 76 --text "Updated text"

# Edit in a group/channel
python3 scripts/telegram_fetch.py edit --chat "Mental health tech" --message-id 123 --text "Corrected content"
```

**Note:** You can only edit your own messages. Telegram formatting (**bold**, etc.) is preserved.

Returns JSON with edit status and message ID.

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

### Fetch Forum Thread Messages

To get messages from a specific forum thread (topics in groups):

```bash
# Fetch from thread 174 in Claude Code Lab
python3 scripts/telegram_fetch.py thread --chat-id -1003237581133 --thread-id 174

# Fetch with custom limit
python3 scripts/telegram_fetch.py thread --chat-id -1003237581133 --thread-id 174 --limit 50

# Save to file
python3 scripts/telegram_fetch.py thread --chat-id -1003237581133 --thread-id 174 -o ~/thread.md

# Append to daily note
python3 scripts/telegram_fetch.py thread --chat-id -1003237581133 --thread-id 174 --to-daily

# JSON output
python3 scripts/telegram_fetch.py thread --chat-id -1003237581133 --thread-id 174 --json
```

**Messages are sorted newest first** (reverse chronological order).

**How to find thread ID:**
- Forum topic IDs appear in the thread URL: `https://t.me/c/CHAT_ID/THREAD_ID`
- Use `recent` command on the chat to see message IDs in threads

Returns markdown or JSON with all messages from the specified thread.

### Publish Draft to Channel

To publish a draft from the klodkot channel to Telegram:

```bash
# Dry run (preview without sending)
python3 scripts/telegram_fetch.py publish --draft "Channels/klodkot/drafts/20260122-anthropic-consciousness-question.md" --dry-run

# Publish to channel
python3 scripts/telegram_fetch.py publish --draft "Channels/klodkot/drafts/20260122-anthropic-consciousness-question.md"
```

**Workflow:**
1. Parses draft frontmatter and body
2. Validates channel field (must be "klodkot")
3. Extracts media references from frontmatter `video:` field and wikilinks
4. Resolves media paths in `Channels/klodkot/attachments/` or `Sources/`
5. Strips draft headers (e.g., "# Title - Telegram Draft")
6. Appends footer if not present: "**[КЛОДКОТ](https://t.me/klodkot)** — Claude Code и другие агенты: инструменты, кейсы, вдохновение"
7. Sends to @klodkot channel (multiple media as album)
8. Updates frontmatter with `published_date`, `telegram_message_id`
9. Moves file from `drafts/` to `published/`
10. Updates channel index with new entry at top

**Media handling:**
- Frontmatter: `video: filename.mp4`
- Wikilinks: `[[filename.mp4]]`, `[[image.png|alt text]]`
- Multiple media sent as Telegram album

**Safety:**
- `--dry-run` shows preview without sending
- Validates before sending
- Rollback on send failure (file not moved)
- Warnings on post-publish errors (file sent but move/index update failed)

**Returns:** JSON with publish status, message ID, warnings (if any)

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
- "Find the exact chat named X" -> `list --search "X" --exact --limit 200`
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
- "Edit that message" -> `edit --chat "..." --message-id <id> --text "new text"`
- "Fix the typo in message 123" -> `edit --chat "..." --message-id 123 --text "corrected text"`
- "Is Telegram configured?" -> `setup`
- "How do I set up Telegram?" -> `setup` (returns instructions if not configured)
- "Publish this draft to klodkot" -> `publish --draft "Channels/klodkot/drafts/...md"`
- "Preview this draft before publishing" -> `publish --draft "..." --dry-run`

## Rate Limiting

The script includes built-in rate limiting (0.1s between messages) and handles Telegram's FloodWaitError automatically with backoff.

## Dependencies

Requires Python packages:
- `telethon` - Telegram API client
- `pyyaml` - YAML parsing for draft frontmatter

Install with: `pip install telethon pyyaml`
