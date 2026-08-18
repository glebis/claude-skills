---
name: telegram-post
description: 'Create, preview, and send formatted Telegram posts from draft markdown files. Use when the user asks to draft a Telegram channel post, preview a draft before sending, or publish a draft from Channels/*/drafts/ to saved messages or a channel. Triggers on "post to Telegram", "send to saved messages", "publish draft", "telegram post".'
---

# Telegram Post Skill

Create, preview, and send formatted Telegram posts from draft markdown files.

**Script location**: `~/.Codex/skills/telegram/scripts/telegram_fetch.py`
(NOT `scripts/post.py` -- that file does not exist)

## When to Use

Use this skill when:
- User asks to create a draft for a Telegram channel
- User asks to "post to Telegram" or "send to saved messages" from a draft file
- User wants to preview a draft before sending
- Draft files in `Channels/*/drafts/` need to be sent

## Sending Drafts

### To Saved Messages (preview)

Use the `send` command with `--markdown` flag to preserve formatting:

```bash
# Send draft content with formatting to saved messages
python3 ~/.Codex/skills/telegram/scripts/telegram_fetch.py send \
  --chat "@glebkalinin" \
  --text "DRAFT_BODY_HERE" \
  --markdown
```

### With Image/File

```bash
# Send image with caption (first part) + follow-up text message (rest)
python3 ~/.Codex/skills/telegram/scripts/telegram_fetch.py send \
  --chat "@glebkalinin" \
  --file "/path/to/image.png" \
  --text "CAPTION_TEXT" \
  --markdown
```

**IMPORTANT: Image caption limits**
- Telegram captions are limited to 1024 characters
- If the draft body exceeds 1024 chars, split into: image + short caption, then follow-up text message(s)
- Always use `--markdown` when sending draft content with formatting

### To Channel (publish)

Use the `publish` command for channel posts -- it handles markdown conversion, footer, and post-publish automation. Works with **any channel** in `Channels/`.

```bash
# Preview -- accepts slug, filename, or full path
python3 ~/.Codex/skills/telegram/scripts/telegram_fetch.py publish \
  --draft "20260413-delusional-spiraling" --dry-run

# Publish (auto-detects channel from folder or frontmatter)
python3 ~/.Codex/skills/telegram/scripts/telegram_fetch.py publish \
  --draft "20260413-delusional-spiraling"

# Schedule for later
python3 ~/.Codex/skills/telegram/scripts/telegram_fetch.py publish \
  --draft "20260413-delusional-spiraling" --schedule "2026-04-16T09:00"

# Full path also works
python3 ~/.Codex/skills/telegram/scripts/telegram_fetch.py publish \
  --draft "Channels/klodkot/drafts/20260211-post.md"
```

The `publish` command automatically:
- Resolves channel from draft folder path or frontmatter `channel` field
- Converts markdown to Telegram HTML
- Appends the correct channel footer if missing (reads from published posts)
- Sends with `parse_mode='html'`
- Updates frontmatter (`published_date`, `telegram_message_id`)
- Moves file from `drafts/` to `published/`
- Updates the channel's index file

**Supported channels**: Any folder in `Channels/` with a `{name}/{name}.md` index file containing `telegram_channel` in frontmatter (klodkot, mental-health-tech, opytnym-putem, tool-building-ape, etc.)

## Formatting Reference

### `--markdown` flag (for `send` command)

Converts markdown to Telegram HTML before sending:

| Markdown | Telegram |
|----------|----------|
| `**bold**` | bold |
| `_italic_` | italic |
| `[text](url)` | clickable link |
| `## Header` | bold |
| `* item` / `- item` | arrow format |

**Without `--markdown`**: text is sent as-is (plain text). `**bold**` appears literally as `**bold**`.

### `publish` command

Handles markdown conversion automatically -- no `--markdown` flag needed.

## Draft Preparation Workflow

1. Read the draft file from `Channels/{channel}/drafts/`
2. Strip YAML frontmatter (everything between `---` markers)
3. Strip `![[image.png]]` wikilink embeds (handle images separately via `--file`)
4. Resolve media paths: check `Attachments/`, `Channels/{channel}/attachments/`, `Channels/{channel}/videos/`, vault root
5. Check text length:
   - If <= 1024 chars and has image/video: send as single message with media + caption
   - If > 1024 chars and has image/video: send media with short caption (title only), then rest as follow-up text
   - If no media: send as text message(s), split at 4096 char limit
6. Always use `--markdown` flag for draft content

## Post-Send Workflow (when user says "move to published" or similar)

After sending a draft to saved messages or channel:
1. Move file from `Channels/{channel}/drafts/` to `Channels/{channel}/published/`
2. Update frontmatter: change `type: draft` to `type: published` and add `published_date: '[[YYYYMMDD]]'` (today's date)
3. Both steps should be done automatically when the user requests moving to published

## Draft File Format

```markdown
---
created_date: '[[YYYYMMDD]]'
type: draft
channel: klodkot
status: draft
language: ru
topic: Topic description
source: https://example.com
---
![[optional-image.png]]

_Source attribution_

**Post Title**

Content with **bold** and _italic_ and [links](url).

#tag1@channel #tag2@channel

**[CHANNEL](https://t.me/channel)** -- footer
```

## Common Pitfalls

- **Do NOT send raw HTML** via `send` command -- it shows as literal `<b>text</b>`. Use `--markdown` instead.
- **Do NOT manually construct HTML** -- the `--markdown` flag handles conversion.
- **Image captions** have a 1024 char limit in Telegram. Split long posts.
- `scripts/post.py` does NOT exist. Always use `~/.Codex/skills/telegram/scripts/telegram_fetch.py`.

## Dependencies

- Uses `telegram` skill credentials (`~/.telegram_dl/`)
- Python 3.10+, telethon, pyyaml
