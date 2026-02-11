#!/usr/bin/env python3
"""
Telegram Post Tool

Create, preview, and send formatted Telegram posts from draft markdown files.
Converts markdown to Telegram HTML, attaches media with caption.
Default send target: Saved Messages (@glebkalinin).
"""

import argparse
import asyncio
import json
import os
import re
import sys
from datetime import datetime
from pathlib import Path

# Reuse telegram skill's client and config
sys.path.insert(0, str(Path.home() / ".claude/skills/telegram/scripts"))
from telegram_fetch import get_client

VAULT_PATH = Path.home() / "Brains/brain"
MAX_MESSAGE_LENGTH = 4096
DEFAULT_CHAT = "@glebkalinin"
DEFAULT_CHANNEL = "klodkot"

CHANNEL_CONFIG = {
    "klodkot": {
        "path": "Channels/klodkot",
        "language": "ru",
        "footer_html": '\n\n<b><a href="https://t.me/klodkot">КЛОДКОТ</a></b> — Claude Code и другие агенты: инструменты, кейсы, вдохновение',
        "tags_file": "klodkot-tags.md",
    },
    "mental-health-tech": {
        "path": "Channels/mental-health-tech",
        "language": "ru",
        "footer_html": '\n\n<b><a href="https://t.me/mentalhealthtech">Mental Health Tech</a></b> — технологии для ментального здоровья: приложения, исследования, инсайты',
        "tags_file": "mental-health-tech-tags.md",
    },
    "tool-building-ape": {
        "path": "Channels/tool-building-ape",
        "language": "en",
        "footer_html": "",
        "tags_file": "",
    },
    "opytnym-putem": {
        "path": "Channels/opytnym-putem",
        "language": "ru",
        "footer_html": "",
        "tags_file": "",
    },
}

KLODKOT_FOOTER = CHANNEL_CONFIG["klodkot"]["footer_html"]


def parse_frontmatter(content: str) -> tuple[dict, str]:
    """Extract YAML frontmatter and return (metadata, body)."""
    if not content.startswith("---"):
        return {}, content

    match = re.match(r'^---\n(.*?)\n---\n(.*)$', content, re.DOTALL)
    if not match:
        return {}, content

    frontmatter_text = match.group(1)
    body = match.group(2)

    metadata = {}
    for line in frontmatter_text.split('\n'):
        if ':' in line:
            key, value = line.split(':', 1)
            key = key.strip()
            value = value.strip().strip('"').strip("'")
            if value.startswith('[[') and value.endswith(']]'):
                value = value[2:-2]
            metadata[key] = value

    return metadata, body


def convert_markdown_to_telegram_html(text: str) -> str:
    """Convert markdown formatting to Telegram HTML.

    Handles:
    - ## Header -> <b>Header</b>
    - **bold** -> <b>bold</b>
    - *italic* -> <i>italic</i>
    - _italic_ -> <i>italic</i>
    - [text](url) -> <a href="url">text</a>
    - * item / - item -> arrow format
    """
    # Headers to bold (before other conversions)
    text = re.sub(r'^##\s+(.+?)$', r'<b>\1</b>', text, flags=re.MULTILINE)

    # Bullet lists to arrow format
    text = re.sub(r'^\*\s+(.+?)$', r'→ \1', text, flags=re.MULTILINE)
    text = re.sub(r'^-\s+(.+?)$', r'→ \1', text, flags=re.MULTILINE)

    # Markdown links [text](url) -> <a href="url">text</a>
    text = re.sub(r'\[([^\]]+)\]\(([^\)]+)\)', r'<a href="\2">\1</a>', text)

    # Bold **text** -> <b>text</b>
    text = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', text)

    # Italic *text* -> <i>text</i> (after bold, so **bold** is already handled)
    text = re.sub(r'\*(.+?)\*', r'<i>\1</i>', text)

    # Italic _text_ -> <i>text</i>
    text = re.sub(r'(?<!\w)_(.+?)_(?!\w)', r'<i>\1</i>', text)

    return text


def check_stray_formatting(html: str) -> list[str]:
    """Check for unconverted markdown artifacts in HTML output.

    Returns list of warnings. Empty list = clean.
    """
    warnings = []

    # Stray markdown bold (not inside HTML tags)
    if re.search(r'(?<!<b>)\*\*(?!</b>)', html):
        warnings.append("Unconverted ** (bold) found")

    # Stray single * that aren't in HTML tags or hashtags
    stray_stars = re.findall(r'(?<![<*])\*(?![*>])', html)
    if stray_stars:
        warnings.append(f"Stray * characters found ({len(stray_stars)})")

    # Stray markdown headers
    if re.search(r'^#{1,3}\s', html, re.MULTILINE):
        warnings.append("Unconverted markdown headers (#) found")

    # Stray markdown links
    if re.search(r'\[([^\]]+)\]\(([^\)]+)\)', html):
        warnings.append("Unconverted markdown links found")

    return warnings


def strip_title(body: str) -> str:
    """Strip markdown H1 title from body."""
    lines = body.strip().split('\n')
    if lines and lines[0].startswith('# '):
        lines = lines[1:]
        while lines and not lines[0].strip():
            lines.pop(0)
        return '\n'.join(lines)
    return body


def strip_media_references(body: str) -> str:
    """Remove media wikilinks and 'Video attached' lines."""
    body = re.sub(r'!\[\[([^\[\]]+\.(mp4|png|jpg|jpeg))(?:\|[^\]]+)?\]\]\n?', '', body, flags=re.IGNORECASE)
    body = re.sub(r'^\*\*Видео прикреплено\*\*.*$', '', body, flags=re.MULTILINE)
    body = re.sub(r'\n{3,}', '\n\n', body)
    return body.strip()


def get_footer_html(channel: str) -> str | None:
    """Get footer HTML for a channel. Returns None if no footer configured."""
    # Match channel name from @handle or plain name
    clean = channel.lstrip('@').lower()
    for name, config in CHANNEL_CONFIG.items():
        if clean == name or clean == name.replace('-', ''):
            if config["footer_html"]:
                return config["footer_html"]
    return None


def should_add_footer(body: str, channel: str) -> bool:
    """Check if footer should be added for this channel."""
    footer = get_footer_html(channel)
    if not footer:
        return False
    # Check if any channel footer already present
    return not re.search(r'КЛОДКОТ|t\.me/klodkot|Mental Health Tech|t\.me/mentalhealthtech', body, re.IGNORECASE)


def resolve_video_path(video_field: str, draft_file_path: Path) -> Path | None:
    """Resolve video path from frontmatter field."""
    if not video_field:
        return None

    video_field = os.path.expanduser(video_field)

    # Try: relative to draft, channel attachments, vault root, absolute
    candidates = [
        draft_file_path.parent / video_field,
        draft_file_path.parent / "attachments" / video_field,
        VAULT_PATH / "Channels" / "klodkot" / "attachments" / video_field,
        VAULT_PATH / video_field,
    ]

    if Path(video_field).is_absolute():
        candidates.append(Path(video_field))

    for candidate in candidates:
        if candidate.exists():
            return candidate

    return None


def split_post(body: str) -> list[str]:
    """Split post body by --- markers into parts."""
    parts = re.split(r'\n---\n', body)
    return [p.strip() for p in parts if p.strip()]


def validate_parts(parts: list[str]) -> list[str]:
    """Re-split parts that exceed Telegram limits."""
    validated = []
    for part in parts:
        if len(part) <= MAX_MESSAGE_LENGTH:
            validated.append(part)
        else:
            paragraphs = part.split('\n\n')
            current = ""
            for para in paragraphs:
                if len(current) + len(para) + 2 <= MAX_MESSAGE_LENGTH:
                    current = current + "\n\n" + para if current else para
                else:
                    if current:
                        validated.append(current)
                    current = para
            if current:
                validated.append(current)
    return validated


def is_channel_target(chat: str) -> bool:
    """Check if target is a Telegram channel (not saved messages/DM)."""
    if not chat or chat == DEFAULT_CHAT:
        return False
    return chat.startswith('@') and chat != DEFAULT_CHAT


def detect_channel_from_path(file_path: Path) -> str | None:
    """Detect channel name from file path (e.g., Channels/klodkot/drafts/...)."""
    parts = file_path.parts
    try:
        idx = parts.index("Channels")
        if idx + 1 < len(parts):
            return parts[idx + 1]
    except ValueError:
        pass
    return None


def update_draft_frontmatter(file_path: Path, message_id: int) -> None:
    """Update draft frontmatter with publish metadata."""
    content = file_path.read_text(encoding='utf-8')
    today = datetime.now().strftime("%Y%m%d")

    # Replace/add fields in frontmatter
    # type: draft -> type: published
    content = re.sub(r'^type:\s*draft\s*$', 'type: published', content, count=1, flags=re.MULTILINE)
    # status: draft -> status: published
    content = re.sub(r'^status:\s*draft\s*$', 'status: published', content, count=1, flags=re.MULTILINE)

    # Insert published_date and telegram_message_id before closing ---
    # Find the second --- (closing frontmatter)
    parts = content.split('---', 2)
    if len(parts) >= 3:
        fm = parts[1]
        # Add new fields if not present
        if 'published_date' not in fm:
            fm = fm.rstrip('\n') + f"\npublished_date: '[[{today}]]'\n"
        if 'telegram_message_id' not in fm:
            fm = fm.rstrip('\n') + f"\ntelegram_message_id: {message_id}\n"
        content = f"---{fm}---{parts[2]}"

    file_path.write_text(content, encoding='utf-8')


def move_to_published(file_path: Path) -> Path:
    """Move draft to published/ folder. Returns new path."""
    published_dir = file_path.parent.parent / "published"
    published_dir.mkdir(exist_ok=True)
    new_path = published_dir / file_path.name
    file_path.rename(new_path)
    return new_path


def update_channel_index(channel: str, filename: str, body: str) -> None:
    """Update channel index file with new published entry."""
    config = CHANNEL_CONFIG.get(channel)
    if not config:
        return

    index_path = VAULT_PATH / config["path"] / f"{channel}.md"
    if not index_path.exists():
        return

    content = index_path.read_text(encoding='utf-8')
    lines = content.split('\n')

    # Find Published section
    insert_idx = None
    for i, line in enumerate(lines):
        if '**Published**:' in line and 'published/' in line:
            insert_idx = i + 1
            break

    if insert_idx is None:
        return

    # Extract description from body
    description = "New post"
    for line in body.strip().split('\n'):
        line = line.strip()
        if not line or line.startswith('#'):
            continue
        # Strip markdown
        line = re.sub(r'\*\*([^*]+)\*\*', r'\1', line)
        line = re.sub(r'\*([^*]+)\*', r'\1', line)
        line = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', line)
        line = line.strip()
        if line:
            if len(line) > 80:
                line = line[:77] + '...'
            description = line
            break

    filename_no_ext = filename.replace('.md', '')
    new_entry = f"- [[{filename_no_ext}]] — {description}"
    lines.insert(insert_idx, new_entry)
    index_path.write_text('\n'.join(lines), encoding='utf-8')


async def send_post(file_path: str, chat: str = None, delay: float = 0.5, dry_run: bool = False) -> dict:
    """Send a formatted post from a draft file."""
    path = Path(file_path)
    if not path.is_absolute():
        path = VAULT_PATH / file_path

    if not path.exists():
        return {"error": f"File not found: {path}", "sent": False}

    content = path.read_text(encoding='utf-8')
    metadata, body = parse_frontmatter(content)

    # Resolve target chat
    target_chat = chat or metadata.get('channel') or metadata.get('telegram_channel') or DEFAULT_CHAT

    # Resolve video
    video_field = metadata.get('video')
    video_path = None
    if video_field:
        video_path = resolve_video_path(video_field, path)
        if not video_path and not dry_run:
            return {
                "error": f"Video file not found: {video_field}",
                "sent": False,
                "video_missing": True
            }

    # Process body
    body = strip_title(body)
    body = strip_media_references(body)

    # Split into parts
    parts = split_post(body)

    # Convert each part to HTML
    html_parts = []
    for i, part in enumerate(parts):
        html = convert_markdown_to_telegram_html(part)

        # Add channel footer to last part
        if i == len(parts) - 1 and should_add_footer(html, target_chat):
            footer = get_footer_html(target_chat)
            if footer:
                html += footer

        html_parts.append(html)

    html_parts = validate_parts(html_parts)

    if not html_parts:
        return {"error": "No content to send", "sent": False}

    # Check for stray formatting in all parts
    all_warnings = []
    for i, html in enumerate(html_parts):
        warnings = check_stray_formatting(html)
        if warnings:
            all_warnings.extend([f"Part {i+1}: {w}" for w in warnings])

    results = {
        "file": str(path),
        "target": target_chat,
        "parts_count": len(html_parts),
        "parts": [],
        "video": str(video_path) if video_path else None,
        "dry_run": dry_run,
    }

    if all_warnings:
        results["formatting_warnings"] = all_warnings

    if dry_run:
        for i, html in enumerate(html_parts, 1):
            results["parts"].append({
                "part": i,
                "length": len(html),
                "preview": html[:200] + "..." if len(html) > 200 else html
            })
        if video_path:
            results["video_preview"] = f"Would upload: {video_path.name} ({video_path.stat().st_size} bytes)"
        return results

    # Abort if formatting warnings
    if all_warnings:
        results["sent"] = False
        results["error"] = "Stray formatting detected. Fix before sending. Use --dry-run to preview."
        return results

    # Send via Telethon with parse_mode='html'
    client = await get_client()
    await client.start()

    try:
        # Resolve entity
        if target_chat == DEFAULT_CHAT:
            entity = await client.get_me()
        else:
            entity = await client.get_entity(target_chat)

        first_message_id = None

        for i, html in enumerate(html_parts):
            # First part: attach video if present
            if i == 0 and video_path:
                msg = await client.send_file(
                    entity, str(video_path),
                    caption=html,
                    parse_mode='html'
                )
            else:
                msg = await client.send_message(
                    entity, html,
                    parse_mode='html'
                )

            if i == 0:
                first_message_id = msg.id

            results["parts"].append({
                "part": i + 1,
                "length": len(html),
                "sent": True,
                "message_id": msg.id
            })

            if i < len(html_parts) - 1:
                await asyncio.sleep(delay)

        results["sent"] = True
        if first_message_id:
            results["first_message_id"] = first_message_id

    except Exception as e:
        results["sent"] = False
        results["error"] = str(e)
    finally:
        await client.disconnect()

    # Post-publish: update frontmatter, move to published, update index
    # Only when sending to a channel (not saved messages)
    if results.get("sent") and is_channel_target(target_chat) and first_message_id:
        post_warnings = []
        channel_name = detect_channel_from_path(path) or metadata.get('channel')

        try:
            update_draft_frontmatter(path, first_message_id)
        except Exception as e:
            post_warnings.append(f"Frontmatter update failed: {e}")

        try:
            new_path = move_to_published(path)
            results["moved_to"] = str(new_path)
        except Exception as e:
            post_warnings.append(f"Move to published failed: {e}")

        if channel_name:
            try:
                update_channel_index(channel_name, path.name, body)
            except Exception as e:
                post_warnings.append(f"Index update failed: {e}")

        if post_warnings:
            results["post_publish_warnings"] = post_warnings

    return results


def create_draft(channel: str, slug: str, topic: str = None, source: str = None,
                 video: str = None, language: str = None) -> dict:
    """Create a new draft file with proper frontmatter.

    Args:
        channel: Channel name (klodkot, mental-health-tech, etc.)
        slug: URL-friendly slug for filename
        topic: Optional topic description
        source: Optional source URL
        video: Optional video filename
        language: Override channel default language

    Returns:
        Dict with created file path and status
    """
    config = CHANNEL_CONFIG.get(channel)
    if not config:
        return {
            "created": False,
            "error": f"Unknown channel: {channel}. Known: {', '.join(CHANNEL_CONFIG.keys())}"
        }

    today = datetime.now().strftime("%Y%m%d")
    lang = language or config["language"]

    # Build filename
    filename = f"{today}-{slug}.md"
    drafts_dir = VAULT_PATH / config["path"] / "drafts"
    file_path = drafts_dir / filename

    if file_path.exists():
        return {"created": False, "error": f"Draft already exists: {file_path}"}

    # Ensure drafts dir exists
    drafts_dir.mkdir(parents=True, exist_ok=True)

    # Build frontmatter
    fm_lines = [
        "---",
        f"created_date: '[[{today}]]'",
        "type: draft",
        f"channel: {channel}",
        f"status: draft",
        f"language: {lang}",
    ]
    if topic:
        fm_lines.append(f"topic: {topic}")
    if source:
        fm_lines.append(f"source: {source}")
    if video:
        fm_lines.append(f"video: {video}")
    fm_lines.append("---")
    fm_lines.append("")
    fm_lines.append("## ")
    fm_lines.append("")
    fm_lines.append("")

    content = "\n".join(fm_lines)
    file_path.write_text(content, encoding="utf-8")

    result = {
        "created": True,
        "file": str(file_path),
        "relative": str(file_path.relative_to(VAULT_PATH)),
        "channel": channel,
        "language": lang,
    }

    # Include tags reference path if available
    if config["tags_file"]:
        tags_path = VAULT_PATH / config["path"] / config["tags_file"]
        if tags_path.exists():
            result["tags_reference"] = str(tags_path.relative_to(VAULT_PATH))

    return result


def main():
    parser = argparse.ArgumentParser(
        description="Create, preview, and send Telegram posts from draft files"
    )
    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    # Send command (default behavior for backwards compat)
    send_parser = subparsers.add_parser("send", help="Send a draft to Telegram")
    send_parser.add_argument(
        "file",
        help="Path to draft markdown file (absolute or relative to vault)"
    )
    send_parser.add_argument(
        "--chat", "-c",
        help=f"Target chat (default: {DEFAULT_CHAT} = Saved Messages)"
    )
    send_parser.add_argument(
        "--delay", "-d",
        type=float,
        default=0.5,
        help="Delay between messages in seconds (default: 0.5)"
    )
    send_parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview formatted output without sending"
    )

    # Create command
    create_parser = subparsers.add_parser("create", help="Create a new draft")
    create_parser.add_argument(
        "slug",
        help="URL-friendly slug for filename (e.g., 'remotion-video-creation')"
    )
    create_parser.add_argument(
        "--channel", "-c",
        default=DEFAULT_CHANNEL,
        help=f"Channel name (default: {DEFAULT_CHANNEL})"
    )
    create_parser.add_argument(
        "--topic", "-t",
        help="Topic description for frontmatter"
    )
    create_parser.add_argument(
        "--source", "-s",
        help="Source URL"
    )
    create_parser.add_argument(
        "--video", "-v",
        help="Video filename (just the name, not path)"
    )
    create_parser.add_argument(
        "--language", "-l",
        help="Override channel default language (ru/en)"
    )

    # List command
    list_parser = subparsers.add_parser("list", help="List available channels")

    args = parser.parse_args()

    # Handle no subcommand (backwards compat: treat first arg as file)
    if args.command is None:
        # Check if there's a positional arg that looks like a file
        if len(sys.argv) > 1 and not sys.argv[1].startswith('-'):
            # Legacy mode: treat as send
            args.command = "send"
            args.file = sys.argv[1]
            args.chat = None
            args.delay = 0.5
            args.dry_run = '--dry-run' in sys.argv
        else:
            parser.print_help()
            sys.exit(1)

    if args.command == "send":
        result = asyncio.run(send_post(
            file_path=args.file,
            chat=args.chat,
            delay=args.delay,
            dry_run=args.dry_run
        ))
        print(json.dumps(result, indent=2, ensure_ascii=False))
        if result.get("error") or not result.get("sent", True):
            sys.exit(1)

    elif args.command == "create":
        result = create_draft(
            channel=args.channel,
            slug=args.slug,
            topic=args.topic,
            source=args.source,
            video=args.video,
            language=args.language,
        )
        print(json.dumps(result, indent=2, ensure_ascii=False))
        if not result.get("created"):
            sys.exit(1)

    elif args.command == "list":
        channels = []
        for name, config in CHANNEL_CONFIG.items():
            channels.append({
                "name": name,
                "path": config["path"],
                "language": config["language"],
                "has_tags": bool(config["tags_file"]),
            })
        print(json.dumps(channels, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
