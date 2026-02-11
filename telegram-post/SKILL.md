# Telegram Post Skill

Create, preview, and send formatted Telegram posts from draft markdown files. Built for [@klodkot](https://t.me/klodkot) and Gleb Kalinin's other Telegram channels.

**Note:** Channel configurations (footers, tags, language defaults) are specific to Gleb's channels. To use for your own channels, edit `CHANNEL_CONFIG` in `scripts/post.py`.

**Configured channels:** [@klodkot](https://t.me/klodkot), @mentalhealthtech, @toolbuildingape, @opytnymputem

## When to Use

Use this skill when:
- User asks to create a draft for a Telegram channel
- User asks to "post to Telegram" or "send to saved messages" from a draft file
- User wants to preview a draft before sending
- Draft files in `Channels/*/drafts/` need to be sent

## Commands

### `create` -- Create a new draft

```bash
# Default: klodkot channel
python3 scripts/post.py create "remotion-video-creation" --topic "Remotion Agent Skill" --source "https://example.com"

# Other channel
python3 scripts/post.py create "therapy-app-review" -c mental-health-tech --topic "Therapy apps"

# With video
python3 scripts/post.py create "demo-post" --video demo.mp4 --source "https://example.com"
```

Creates `Channels/{channel}/drafts/YYYYMMDD-{slug}.md` with proper frontmatter. Returns file path and tags reference for the channel.

Options:
- `--channel, -c`: Channel name (default: klodkot). Use `list` to see all
- `--topic, -t`: Topic for frontmatter
- `--source, -s`: Source URL
- `--video, -v`: Video filename (just name, not path)
- `--language, -l`: Override channel default (ru/en)

### `send` -- Send a draft

```bash
# Preview first (always do this)
python3 scripts/post.py send "Channels/klodkot/drafts/20260209-post.md" --dry-run

# Send to Saved Messages (default)
python3 scripts/post.py send "Channels/klodkot/drafts/20260209-post.md"

# Send to specific chat
python3 scripts/post.py send "draft.md" --chat "@klodkot"
python3 scripts/post.py send "draft.md" -c "Tool Building Ape"
```

### `list` -- List available channels

```bash
python3 scripts/post.py list
```

Returns: klodkot, mental-health-tech, tool-building-ape, opytnym-putem with language and tags info.

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
video: demo.mp4
---

## Post Title

Content with **bold** and *italic* and [links](url).

---

Second part (separate message).
```

### Video Path Resolution

The `video:` field should be just the filename (e.g., `demo.mp4`), NOT `attachments/demo.mp4`. Resolution order:
1. Relative to draft file directory
2. `../attachments/` (sibling to drafts folder)
3. `Channels/klodkot/attachments/`
4. Vault root

## Markdown to Telegram HTML Conversion

| Markdown | Telegram |
|----------|----------|
| `## Header` | `<b>Header</b>` |
| `**bold**` | `<b>bold</b>` |
| `*italic*` | `<i>italic</i>` |
| `_italic_` | `<i>italic</i>` |
| `[text](url)` | `<a href>` link |
| `* item` / `- item` | arrow format |
| `# Title` | stripped |

## Safety

- **Formatting check**: If stray `*`, `**`, `#`, or `[]()` remain after conversion, the script **refuses to send** and reports `formatting_warnings`
- `--dry-run` previews without sending
- Default target is Saved Messages, not channel -- prevents accidental publishes

## Typical Workflow

```bash
# 1. Create draft
python3 scripts/post.py create "remotion-skills" --topic "Remotion" --source "https://..."

# 2. Edit the draft in Obsidian (fill in content, add tags from tags reference)

# 3. Preview
python3 scripts/post.py send "Channels/klodkot/drafts/20260211-remotion-skills.md" --dry-run

# 4. Send to saved messages for final review
python3 scripts/post.py send "Channels/klodkot/drafts/20260211-remotion-skills.md"

# 5. When ready, send to channel
python3 scripts/post.py send "Channels/klodkot/drafts/20260211-remotion-skills.md" -c "@klodkot"
```

## Post-Publish (automatic when sending to channel)

When target is a channel (`@klodkot`, `@mentalhealthtech`), after successful send:
1. Updates frontmatter: `type: published`, `published_date`, `telegram_message_id`
2. Moves file from `drafts/` to `published/`
3. Adds entry to channel index (`klodkot.md`)

Does NOT trigger for Saved Messages (default target) -- safe for preview sends.

## Key Features

- **HTML formatting** via `parse_mode='html'` (Telethon direct, not subprocess)
- **Video with caption** on first message (not separate reply)
- **Channel footers** auto-appended (klodkot, mental-health-tech)
- **Multi-part splitting** by `---` markers, respects 4096 char limit
- **Channel-aware** draft creation with correct paths, language, tags reference
- **Post-publish** auto moves draft to published, updates frontmatter + index

## Dependencies

- Uses `telegram` skill credentials (`~/.telegram_dl/`)
- Python 3.10+, telethon
