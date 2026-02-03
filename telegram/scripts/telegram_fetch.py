#!/usr/bin/env python3
"""
Telegram message fetcher for Claude Code skill.
Fetches messages from Telegram with various filters and outputs.
"""
import asyncio
import argparse
import json
import sys
import re
import yaml
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, List, Dict, Any, Tuple

from telethon import TelegramClient
from telethon.tl.types import User, Chat, Channel
from telethon.tl.functions.messages import SearchGlobalRequest
from telethon.tl.types import InputMessagesFilterEmpty
from telethon.errors import FloodWaitError

# Config paths (shared with telegram_dl)
CONFIG_DIR = Path.home() / '.telegram_dl'
CONFIG_FILE = CONFIG_DIR / 'config.json'
SESSION_FILE = CONFIG_DIR / 'user.session'

# Obsidian vault
VAULT_PATH = Path.home() / 'Brains' / 'brain'


def load_config() -> Dict[str, Any]:
    """Load configuration from file."""
    if not CONFIG_FILE.exists():
        return {}
    with open(CONFIG_FILE, 'r') as f:
        return json.load(f)


def is_configured() -> bool:
    """Check if Telegram is configured."""
    config = load_config()
    return all(key in config for key in ['api_id', 'api_hash'])


def get_setup_instructions() -> Dict:
    """Return setup instructions for unconfigured Telegram."""
    return {
        "configured": False,
        "message": "Telegram is not configured. Follow these steps to set up:",
        "steps": [
            {
                "step": 1,
                "title": "Get Telegram API credentials",
                "instructions": [
                    "Go to https://my.telegram.org/auth",
                    "Log in with your phone number",
                    "Click 'API development tools'",
                    "Create a new application (any name/description)",
                    "Note your api_id and api_hash"
                ],
                "url": "https://my.telegram.org/auth"
            },
            {
                "step": 2,
                "title": "Run the authentication script",
                "instructions": [
                    "Clone or download telegram_dl: https://github.com/glebis/telegram_dl",
                    "Run: python telegram_dl.py",
                    "Enter your api_id and api_hash when prompted",
                    "Enter your phone number (with country code)",
                    "Enter the SMS code Telegram sends you",
                    "If you have 2FA, enter your password"
                ],
                "url": "https://github.com/glebis/telegram_dl"
            },
            {
                "step": 3,
                "title": "Verify configuration",
                "instructions": [
                    "Run: python telegram_fetch.py setup --status",
                    "Should show 'configured: true'"
                ]
            }
        ],
        "config_location": str(CONFIG_DIR),
        "session_file": str(SESSION_FILE)
    }


def get_status() -> Dict:
    """Get current configuration status."""
    config = load_config()
    configured = is_configured()
    session_exists = SESSION_FILE.exists()

    if configured and session_exists:
        return {
            "configured": True,
            "status": "ready",
            "config_location": str(CONFIG_DIR),
            "session_file": str(SESSION_FILE),
            "has_api_id": "api_id" in config,
            "has_api_hash": "api_hash" in config
        }
    elif configured and not session_exists:
        return {
            "configured": False,
            "status": "credentials_only",
            "message": "API credentials found but no session. Run telegram_dl.py to authenticate.",
            "config_location": str(CONFIG_DIR)
        }
    else:
        return get_setup_instructions()


async def get_client() -> TelegramClient:
    """Get authenticated Telegram client."""
    if not is_configured():
        # Print setup instructions as JSON and exit
        print(json.dumps(get_setup_instructions(), indent=2))
        sys.exit(1)

    if not SESSION_FILE.exists():
        print(json.dumps({
            "error": "Session file not found",
            "message": "API credentials exist but no session. Run telegram_dl.py to authenticate.",
            "config_location": str(CONFIG_DIR)
        }, indent=2))
        sys.exit(1)

    config = load_config()
    client = TelegramClient(str(SESSION_FILE), config["api_id"], config["api_hash"])
    await client.start()
    return client


def get_chat_type(entity) -> str:
    """Determine chat type from entity."""
    if isinstance(entity, User):
        return "private"
    elif isinstance(entity, Chat):
        return "group"
    elif isinstance(entity, Channel):
        return "channel"
    return "unknown"


def format_message(msg, chat_name: str, chat_type: str) -> Dict:
    """Format a message for output."""
    sender_name = "Unknown"
    if msg.sender:
        if hasattr(msg.sender, 'first_name'):
            sender_name = msg.sender.first_name or ""
            if hasattr(msg.sender, 'last_name') and msg.sender.last_name:
                sender_name += f" {msg.sender.last_name}"
        elif hasattr(msg.sender, 'title'):
            sender_name = msg.sender.title

    # Extract reactions if present
    reactions = []
    if hasattr(msg, 'reactions') and msg.reactions and hasattr(msg.reactions, 'results'):
        for reaction in msg.reactions.results:
            # Handle both emoji and custom reactions
            if hasattr(reaction, 'reaction'):
                if hasattr(reaction.reaction, 'emoticon'):
                    # Emoji reaction
                    reactions.append({
                        "emoji": reaction.reaction.emoticon,
                        "count": reaction.count
                    })
                elif hasattr(reaction.reaction, 'document_id'):
                    # Custom reaction
                    reactions.append({
                        "custom_id": str(reaction.reaction.document_id),
                        "count": reaction.count
                    })

    result = {
        "id": msg.id,
        "chat": chat_name,
        "chat_type": chat_type,
        "sender": sender_name.strip(),
        "text": msg.text or "",
        "date": msg.date.isoformat() if msg.date else None,
        "has_media": msg.media is not None
    }

    if reactions:
        result["reactions"] = reactions

    return result


async def list_chats(client: TelegramClient, limit: int = 30, search: Optional[str] = None, exact: bool = False) -> List[Dict]:
    """List available chats.

    Args:
        limit: Max number of chats to retrieve
        search: Search term to filter by name
        exact: If True, require exact name match (case-insensitive). If False, use substring matching.
    """
    dialogs = await client.get_dialogs(limit=limit)

    chats = []
    for d in dialogs:
        name = d.name or "Unnamed"
        if search:
            if exact:
                # Exact match (case-insensitive)
                if search.lower() != name.lower():
                    continue
            else:
                # Substring match (case-insensitive)
                if search.lower() not in name.lower():
                    continue
        chats.append({
            "id": d.id,
            "name": name,
            "type": get_chat_type(d.entity),
            "unread": d.unread_count,
            "last_message": d.date.isoformat() if d.date else None
        })

    return chats


async def fetch_recent(client: TelegramClient, chat_id: Optional[int] = None,
                       chat_name: Optional[str] = None, limit: int = 50,
                       days: Optional[int] = None) -> List[Dict]:
    """Fetch recent messages."""
    messages = []

    if chat_id or chat_name:
        # Fetch from specific chat
        if chat_name and not chat_id:
            dialogs = await client.get_dialogs()
            for d in dialogs:
                if chat_name.lower() in (d.name or "").lower():
                    chat_id = d.id
                    break
            if not chat_id:
                print(f"ERROR: Chat '{chat_name}' not found", file=sys.stderr)
                return []

        entity = await client.get_entity(chat_id)
        chat_type = get_chat_type(entity)
        name = getattr(entity, 'title', None) or getattr(entity, 'first_name', '') or "Unknown"

        if days:
            offset_date = datetime.now() - timedelta(days=days)
            async for msg in client.iter_messages(entity, limit=limit, offset_date=offset_date):
                messages.append(format_message(msg, name, chat_type))
                await asyncio.sleep(0.1)  # Rate limiting
        else:
            async for msg in client.iter_messages(entity, limit=limit):
                messages.append(format_message(msg, name, chat_type))
                await asyncio.sleep(0.1)
    else:
        # Fetch from all recent chats
        dialogs = await client.get_dialogs(limit=10)
        for d in dialogs:
            name = d.name or "Unnamed"
            chat_type = get_chat_type(d.entity)
            count = 0
            max_per_chat = limit // 10

            try:
                async for msg in client.iter_messages(d.entity, limit=max_per_chat):
                    if days:
                        cutoff = datetime.now(msg.date.tzinfo) - timedelta(days=days)
                        if msg.date < cutoff:
                            break
                    messages.append(format_message(msg, name, chat_type))
                    count += 1
                    await asyncio.sleep(0.1)
            except FloodWaitError as e:
                print(f"Rate limited, waiting {e.seconds}s...", file=sys.stderr)
                await asyncio.sleep(e.seconds)

    return messages


async def search_messages(client: TelegramClient, query: str,
                         chat_id: Optional[int] = None, limit: int = 50) -> List[Dict]:
    """Search messages by content."""
    messages = []

    if chat_id:
        # Search in specific chat
        entity = await client.get_entity(chat_id)
        chat_type = get_chat_type(entity)
        name = getattr(entity, 'title', None) or getattr(entity, 'first_name', '') or "Unknown"

        async for msg in client.iter_messages(entity, search=query, limit=limit):
            messages.append(format_message(msg, name, chat_type))
            await asyncio.sleep(0.1)
    else:
        # Global search - search across recent chats instead of using SearchGlobalRequest
        # (SearchGlobalRequest API has changed in newer Telethon versions)
        dialogs = await client.get_dialogs(limit=20)
        for d in dialogs:
            name = d.name or "Unnamed"
            chat_type = get_chat_type(d.entity)
            try:
                async for msg in client.iter_messages(d.entity, search=query, limit=limit // 20 + 1):
                    messages.append(format_message(msg, name, chat_type))
                    await asyncio.sleep(0.1)
                    if len(messages) >= limit:
                        break
            except Exception:
                continue  # Skip chats we can't search
            if len(messages) >= limit:
                break


    return messages


async def resolve_entity(client: TelegramClient, chat_name: str) -> tuple:
    """Resolve chat name/username/ID to entity and display name."""
    entity = None
    resolved_name = chat_name

    # Try username resolution first if it looks like a username
    if chat_name.startswith('@') or (not chat_name.replace('-', '').replace('_', '').isalnum() == False and not chat_name.lstrip('-').isdigit()):
        try:
            username = chat_name if chat_name.startswith('@') else f"@{chat_name}"
            entity = await client.get_entity(username)
            resolved_name = getattr(entity, 'first_name', '') or getattr(entity, 'title', '') or chat_name
            if hasattr(entity, 'last_name') and entity.last_name:
                resolved_name += f" {entity.last_name}"
        except Exception:
            pass

    # Try numeric chat ID
    if entity is None and chat_name.lstrip('-').isdigit():
        try:
            entity = await client.get_entity(int(chat_name))
            resolved_name = getattr(entity, 'first_name', '') or getattr(entity, 'title', '') or chat_name
        except Exception:
            pass

    # Search in existing dialogs
    if entity is None:
        dialogs = await client.get_dialogs()
        for d in dialogs:
            if chat_name.lower() in (d.name or "").lower():
                entity = d.entity
                resolved_name = d.name
                break

    return entity, resolved_name


async def edit_message(client: TelegramClient, chat_id: Optional[int] = None,
                       chat_name: Optional[str] = None, message_id: int = None,
                       text: str = None) -> Dict:
    """Edit an existing message.

    Args:
        chat_id: Chat ID
        chat_name: Chat name, @username, or ID
        message_id: ID of the message to edit
        text: New text content

    Returns:
        Dict with edit status
    """
    # Resolve chat using either chat_id or chat_name
    if chat_id:
        entity, resolved_name = await resolve_entity(client, str(chat_id))
    elif chat_name:
        entity, resolved_name = await resolve_entity(client, chat_name)
    else:
        return {"edited": False, "error": "Must provide --chat or --chat-id"}

    if entity is None:
        chat_ref = chat_id if chat_id else chat_name
        return {"edited": False, "error": f"Chat '{chat_ref}' not found"}

    try:
        await client.edit_message(entity, message_id, text)
        return {
            "edited": True,
            "chat": resolved_name,
            "message_id": message_id
        }
    except Exception as e:
        return {"edited": False, "error": str(e), "message_id": message_id}


async def send_message(client: TelegramClient, chat_name: str, text: str,
                       reply_to: Optional[int] = None,
                       file_path: Optional[str] = None) -> Dict:
    """Send a message or file to a chat, optionally as a reply.

    Supports:
    - Chat names (fuzzy match in existing dialogs)
    - Usernames (@username or just username)
    - Phone numbers
    - Chat IDs (numeric)
    - File attachments (images, documents, videos)

    Safety: Groups/channels require explicit whitelist in config.json
    """
    entity, resolved_name = await resolve_entity(client, chat_name)

    if entity is None:
        return {"sent": False, "error": f"Chat '{chat_name}' not found"}

    # Safety check: block group/channel sends unless whitelisted
    chat_type = get_chat_type(entity)
    if chat_type in ["group", "channel"]:
        config = load_config()
        allowed_groups = config.get("allowed_send_groups", [])

        # Check if chat is whitelisted (by name or ID)
        entity_id = getattr(entity, 'id', None)
        if resolved_name not in allowed_groups and str(entity_id) not in allowed_groups:
            return {
                "sent": False,
                "error": f"Sending to groups/channels requires whitelist. Add '{resolved_name}' or '{entity_id}' to allowed_send_groups in {CONFIG_FILE}",
                "chat_type": chat_type,
                "chat_name": resolved_name,
                "chat_id": entity_id
            }

    try:
        # Send file if provided
        if file_path:
            import os
            if not os.path.exists(file_path):
                return {"sent": False, "error": f"File not found: {file_path}"}

            file_size = os.path.getsize(file_path)
            file_name = os.path.basename(file_path)

            msg = await client.send_file(
                entity,
                file_path,
                caption=text if text else None,
                reply_to=reply_to
            )
            return {
                "sent": True,
                "chat": resolved_name,
                "message_id": msg.id,
                "reply_to": reply_to,
                "file": {
                    "name": file_name,
                    "size": file_size,
                    "path": file_path
                }
            }
        else:
            # Send text message
            msg = await client.send_message(
                entity,
                text,
                reply_to=reply_to
            )
            return {
                "sent": True,
                "chat": resolved_name,
                "message_id": msg.id,
                "reply_to": reply_to
            }
    except Exception as e:
        return {"sent": False, "error": str(e)}


DEFAULT_ATTACHMENTS_DIR = Path.home() / 'Downloads' / 'telegram_attachments'


async def download_media(client: TelegramClient, chat_name: str,
                         limit: int = 5, output_dir: Optional[str] = None,
                         message_id: Optional[int] = None) -> List[Dict]:
    """Download media attachments from a chat.

    Args:
        chat_name: Chat name, @username, or ID
        limit: Max number of attachments to download (default 5)
        output_dir: Output directory (default ~/Downloads/telegram_attachments)
        message_id: Specific message ID to download from (optional)
    """
    import os

    # Set output directory
    if output_dir:
        out_path = Path(output_dir)
    else:
        out_path = DEFAULT_ATTACHMENTS_DIR

    out_path.mkdir(parents=True, exist_ok=True)

    entity, resolved_name = await resolve_entity(client, chat_name)
    if entity is None:
        return [{"error": f"Chat '{chat_name}' not found"}]

    downloaded = []

    if message_id:
        # Download from specific message
        msg = await client.get_messages(entity, ids=message_id)
        if msg and msg.media:
            try:
                file_path = await client.download_media(msg, str(out_path))
                if file_path:
                    downloaded.append({
                        "message_id": msg.id,
                        "chat": resolved_name,
                        "file": os.path.basename(file_path),
                        "path": file_path,
                        "size": os.path.getsize(file_path),
                        "date": msg.date.isoformat() if msg.date else None
                    })
            except Exception as e:
                downloaded.append({"message_id": message_id, "error": str(e)})
        else:
            downloaded.append({"message_id": message_id, "error": "No media in message"})
    else:
        # Download recent media
        count = 0
        async for msg in client.iter_messages(entity, limit=100):
            if msg.media and hasattr(msg.media, 'document') or hasattr(msg, 'photo') and msg.photo:
                try:
                    file_path = await client.download_media(msg, str(out_path))
                    if file_path:
                        downloaded.append({
                            "message_id": msg.id,
                            "chat": resolved_name,
                            "file": os.path.basename(file_path),
                            "path": file_path,
                            "size": os.path.getsize(file_path),
                            "date": msg.date.isoformat() if msg.date else None
                        })
                        count += 1
                        if count >= limit:
                            break
                except Exception as e:
                    downloaded.append({"message_id": msg.id, "error": str(e)})
            await asyncio.sleep(0.2)  # Rate limiting

    return downloaded


async def fetch_unread(client: TelegramClient, chat_id: Optional[int] = None) -> List[Dict]:
    """Fetch unread messages."""
    messages = []
    dialogs = await client.get_dialogs()

    for d in dialogs:
        if chat_id and d.id != chat_id:
            continue
        if d.unread_count == 0:
            continue

        name = d.name or "Unnamed"
        chat_type = get_chat_type(d.entity)

        try:
            async for msg in client.iter_messages(d.entity, limit=d.unread_count):
                messages.append(format_message(msg, name, chat_type))
                await asyncio.sleep(0.1)
        except FloodWaitError as e:
            print(f"Rate limited, waiting {e.seconds}s...", file=sys.stderr)
            await asyncio.sleep(e.seconds)

    return messages


def format_output(messages: List[Dict], output_format: str = "markdown") -> str:
    """Format messages for output."""
    if output_format == "json":
        return json.dumps(messages, indent=2, ensure_ascii=False)

    # Markdown format
    lines = []
    current_chat = None

    for msg in messages:
        if msg["chat"] != current_chat:
            current_chat = msg["chat"]
            lines.append(f"\n## {current_chat} ({msg['chat_type']})\n")

        date_str = ""
        if msg["date"]:
            dt = datetime.fromisoformat(msg["date"])
            date_str = dt.strftime("%Y-%m-%d %H:%M")

        sender = msg["sender"]
        text = msg["text"] or "[media]" if msg["has_media"] else msg["text"]

        if text:
            lines.append(f"**{date_str}** - {sender}:")
            lines.append(f"> {text}")

            # Add reactions if present
            if "reactions" in msg and msg["reactions"]:
                reaction_str = " ".join([
                    f"{r['emoji']} {r['count']}" if 'emoji' in r
                    else f"[custom] {r['count']}"
                    for r in msg["reactions"]
                ])
                lines.append(f"> **Reactions:** {reaction_str}")

            lines.append("")  # Empty line

    return "\n".join(lines)


def append_to_daily(content: str):
    """Append content to today's daily note."""
    today = datetime.now().strftime("%Y%m%d")
    daily_path = VAULT_PATH / "Daily" / f"{today}.md"

    if not daily_path.exists():
        print(f"Creating daily note: {daily_path}", file=sys.stderr)
        daily_path.parent.mkdir(parents=True, exist_ok=True)
        daily_path.write_text(f"# {today}\n\n")

    with open(daily_path, 'a') as f:
        f.write(f"\n## Telegram Messages\n{content}\n")

    print(f"Appended to {daily_path}", file=sys.stderr)


def append_to_person(content: str, person_name: str):
    """Append content to a person's note."""
    person_path = VAULT_PATH / f"{person_name}.md"

    if not person_path.exists():
        print(f"Creating person note: {person_path}", file=sys.stderr)
        person_path.write_text(f"# {person_name}\n\n")

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    with open(person_path, 'a') as f:
        f.write(f"\n## Telegram ({timestamp})\n{content}\n")

    print(f"Appended to {person_path}", file=sys.stderr)


async def save_to_file(client: TelegramClient, messages: List[Dict], output_path: str,
                       with_media: bool = False, output_format: str = "markdown") -> Dict:
    """Save messages to file, optionally downloading media.

    Args:
        client: Telegram client for media downloads
        messages: List of message dicts
        output_path: Path to output file
        with_media: Whether to download media files
        output_format: 'markdown' or 'json'

    Returns:
        Dict with save status and media download results
    """
    import os

    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)

    # Format content
    if output_format == "json":
        content = json.dumps(messages, indent=2, ensure_ascii=False)
    else:
        content = format_output(messages, "markdown")

    # Write to file
    output_file.write_text(content, encoding='utf-8')

    result = {
        "saved": True,
        "file": str(output_file),
        "message_count": len(messages)
    }

    # Download media if requested
    if with_media and messages:
        media_dir = output_file.parent / "media"
        media_dir.mkdir(exist_ok=True)

        downloaded = []
        for msg in messages:
            if msg.get("has_media") and msg.get("chat_id") and msg.get("message_id"):
                try:
                    # Get the entity from chat_id
                    entity = await client.get_entity(msg["chat_id"])
                    tg_msg = await client.get_messages(entity, ids=msg["message_id"])
                    if tg_msg and tg_msg.media:
                        file_path = await client.download_media(tg_msg, str(media_dir))
                        if file_path:
                            downloaded.append({
                                "message_id": msg["message_id"],
                                "file": os.path.basename(file_path),
                                "path": file_path
                            })
                except Exception as e:
                    downloaded.append({
                        "message_id": msg.get("message_id"),
                        "error": str(e)
                    })
                await asyncio.sleep(0.2)  # Rate limiting

        result["media"] = downloaded
        result["media_dir"] = str(media_dir)

    return result


async def fetch_thread_messages(client: TelegramClient, chat_id: int,
                                thread_id: int, limit: int = 100) -> List[Dict]:
    """Fetch messages from a specific forum thread."""
    entity = await client.get_entity(chat_id)
    chat_type = get_chat_type(entity)
    name = getattr(entity, 'title', None) or getattr(entity, 'first_name', '') or "Unknown"

    messages = []
    async for msg in client.iter_messages(entity, reply_to=thread_id, limit=limit):
        messages.append(format_message(msg, name, chat_type))
        await asyncio.sleep(0.1)  # Rate limiting

    return messages


# ============================================================================
# Publishing Functions
# ============================================================================

def parse_draft_frontmatter(content: str) -> Tuple[Dict, str]:
    """Parse frontmatter and body from draft content.

    Returns:
        Tuple of (frontmatter_dict, body_content)
    """
    parts = content.split('---', 2)
    if len(parts) < 3:
        return {}, content

    try:
        frontmatter = yaml.safe_load(parts[1])
        body = parts[2].strip()
        return frontmatter, body
    except Exception as e:
        raise ValueError(f"Failed to parse frontmatter: {e}")


def extract_media_references(frontmatter: Dict, body: str) -> List[str]:
    """Extract media file references from frontmatter and body.

    Returns:
        List of media filenames (mp4, png, jpg, jpeg)
    """
    media_files = []

    # Check frontmatter video field
    if 'video' in frontmatter and frontmatter['video']:
        media_files.append(frontmatter['video'])

    # Find wikilinks with media extensions
    wikilink_pattern = r'\[\[([^\[\]]+\.(mp4|png|jpg|jpeg))(?:\|[^\]]+)?\]\]'
    matches = re.findall(wikilink_pattern, body, re.IGNORECASE)
    for match in matches:
        media_files.append(match[0])

    return media_files


def resolve_media_paths(filenames: List[str], vault_path: Path) -> List[Path]:
    """Resolve media filenames to absolute paths.

    Searches in:
    1. Channels/klodkot/attachments/
    2. Sources/

    Returns:
        List of absolute paths

    Raises:
        FileNotFoundError if any file not found
    """
    search_dirs = [
        vault_path / "Channels" / "klodkot" / "attachments",
        vault_path / "Sources"
    ]

    resolved = []
    for filename in filenames:
        found = False
        for search_dir in search_dirs:
            candidate = search_dir / filename
            if candidate.exists():
                resolved.append(candidate)
                found = True
                break

        if not found:
            raise FileNotFoundError(
                f"Media file not found: {filename}. "
                f"Searched in: {', '.join(str(d) for d in search_dirs)}"
            )

    return resolved


def strip_draft_header(body: str) -> str:
    """Strip markdown header ending with '- Telegram Draft' or similar."""
    lines = body.strip().split('\n')

    if lines and lines[0].startswith('#'):
        first_line = lines[0]
        # Remove headers ending with common draft markers
        if any(marker in first_line.lower() for marker in ['telegram draft', 'draft', '— draft']):
            # Remove first line and any following empty lines
            lines = lines[1:]
            while lines and not lines[0].strip():
                lines.pop(0)
            return '\n'.join(lines)

    return body


def strip_media_wikilinks(body: str) -> str:
    """Strip media wikilinks from body text.

    Removes: ![[image.png]], ![[video.mp4|caption]], etc.
    These will be sent as Telegram media attachments.
    """
    # Pattern matches ![[filename.ext]] or ![[filename.ext|caption]]
    # where ext is mp4, png, jpg, jpeg
    pattern = r'!\[\[([^\[\]]+\.(mp4|png|jpg|jpeg))(?:\|[^\]]+)?\]\]\n?'
    cleaned = re.sub(pattern, '', body, flags=re.IGNORECASE)

    # Remove multiple consecutive newlines that might result
    cleaned = re.sub(r'\n{3,}', '\n\n', cleaned)

    return cleaned.strip()


def check_footer_exists(body: str) -> bool:
    """Check if footer signature already exists in body."""
    footer_patterns = [
        r'КЛОДКОТ',
        r't\.me/klodkot'
    ]

    for pattern in footer_patterns:
        if re.search(pattern, body, re.IGNORECASE):
            return True

    return False


def append_footer(body: str) -> str:
    """Append standard footer to body."""
    footer = '\n\n**[КЛОДКОТ](https://t.me/klodkot)** — Claude Code и другие агенты: инструменты, кейсы, вдохновение'
    return body + footer


def convert_markdown_to_telegram_html(text: str) -> str:
    """Convert markdown formatting to Telegram HTML.

    Conversions:
    - ## Header → <b>Header</b>
    - **bold** → <b>bold</b>
    - _italic_ → <i>italic</i>
    - [text](url) → <a href="url">text</a>
    - * item → → item (bullet lists to arrows)
    """
    # Convert headers to bold (must be done first, before other conversions)
    text = re.sub(r'^##\s+(.+?)$', r'<b>\1</b>', text, flags=re.MULTILINE)

    # Convert bullet lists to arrow format
    text = re.sub(r'^\*\s+(.+?)$', r'→ \1', text, flags=re.MULTILINE)
    text = re.sub(r'^-\s+(.+?)$', r'→ \1', text, flags=re.MULTILINE)

    # Convert bold **text** to <b>text</b>
    text = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', text)

    # Convert italic _text_ to <i>text</i>
    text = re.sub(r'_(.+?)_', r'<i>\1</i>', text)

    # Convert markdown links [text](url) to <a href="url">text</a>
    text = re.sub(r'\[([^\]]+)\]\(([^\)]+)\)', r'<a href="\2">\1</a>', text)

    return text


def update_frontmatter(file_path: Path, message_id: int) -> None:
    """Update draft frontmatter with publish metadata.

    Updates:
    - type: published
    - published_date: '[[YYYYMMDD]]'
    - telegram_message_id: {message_id}
    """
    content = file_path.read_text(encoding='utf-8')
    frontmatter, body = parse_draft_frontmatter(content)

    # Update frontmatter
    frontmatter['type'] = 'published'
    frontmatter['published_date'] = f"[[{datetime.now().strftime('%Y%m%d')}]]"
    frontmatter['telegram_message_id'] = message_id

    # Reconstruct file
    yaml_str = yaml.dump(frontmatter, allow_unicode=True, default_flow_style=False)
    new_content = f"---\n{yaml_str}---\n\n{body}"

    file_path.write_text(new_content, encoding='utf-8')


def extract_first_line(body: str) -> str:
    """Extract first meaningful line from body for index description.

    Strips markdown formatting and truncates to 80 chars.
    """
    lines = body.strip().split('\n')

    for line in lines:
        line = line.strip()
        # Skip empty lines and markdown headers
        if not line or line.startswith('#'):
            continue

        # Strip markdown formatting
        line = re.sub(r'\*\*([^*]+)\*\*', r'\1', line)  # Bold
        line = re.sub(r'\*([^*]+)\*', r'\1', line)      # Italic
        line = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', line)  # Links
        line = line.strip()

        if line:
            # Truncate if too long
            if len(line) > 80:
                line = line[:77] + '...'
            return line

    return "New post"


def update_channel_index(index_path: Path, filename: str, description: str) -> None:
    """Update channel index with new published entry.

    Inserts at top of Published section.
    """
    content = index_path.read_text(encoding='utf-8')
    lines = content.split('\n')

    # Find the line with "**Published**: `published/`"
    insert_idx = None
    for i, line in enumerate(lines):
        if '**Published**:' in line and 'published/' in line:
            insert_idx = i + 1
            break

    if insert_idx is None:
        raise ValueError("Could not find **Published**: section in channel index")

    # Extract filename without extension
    filename_no_ext = filename.replace('.md', '')

    # Create new entry
    new_entry = f"- [[{filename_no_ext}]] — {description}"

    # Insert at top
    lines.insert(insert_idx, new_entry)

    # Write back
    index_path.write_text('\n'.join(lines), encoding='utf-8')


async def publish_draft(client: TelegramClient, draft_path: str, dry_run: bool) -> Dict:
    """Publish a draft to Telegram channel.

    Workflow:
    1. Parse draft frontmatter + body
    2. Validate channel field
    3. Extract and resolve media paths
    4. Check/append footer if needed
    5. Send to Telegram (or preview if dry_run)
    6. Update frontmatter, move file, update index (only if send succeeded)

    Args:
        client: Telegram client
        draft_path: Path to draft file (can be relative to vault)
        dry_run: If True, preview only without sending

    Returns:
        Dict with publish status and details
    """
    # Convert to absolute path
    draft_file = Path(draft_path)
    if not draft_file.is_absolute():
        draft_file = VAULT_PATH / draft_path

    if not draft_file.exists():
        return {"published": False, "error": f"Draft file not found: {draft_path}"}

    try:
        # Parse draft
        content = draft_file.read_text(encoding='utf-8')
        frontmatter, body = parse_draft_frontmatter(content)

        # Check if already published
        if frontmatter.get('telegram_message_id'):
            return {
                "published": False,
                "error": f"Draft already published (message_id: {frontmatter['telegram_message_id']})",
                "already_published": True,
                "message_id": frontmatter['telegram_message_id']
            }

        if frontmatter.get('type') == 'published':
            return {
                "published": False,
                "error": "Draft type is already 'published'",
                "already_published": True
            }

        # Validate channel
        channel = frontmatter.get('channel', '')
        # Handle both "klodkot" and "[[klodkot (Telegram channel)]]"
        if isinstance(channel, str):
            # Extract channel name from wikilink if present
            if '[[' in channel:
                channel_match = re.search(r'\[\[([^\]|]+)', channel)
                if channel_match:
                    channel_name = channel_match.group(1).split('(')[0].strip().lower()
                else:
                    channel_name = ''
            else:
                channel_name = channel.lower()

            if 'klodkot' not in channel_name:
                return {
                    "published": False,
                    "error": f"Invalid channel: {channel}. Expected 'klodkot'"
                }
        else:
            return {
                "published": False,
                "error": f"Invalid channel type: {type(channel)}. Expected string"
            }

        # Strip draft header
        body = strip_draft_header(body)

        # Extract media references (before stripping them from body)
        media_filenames = extract_media_references(frontmatter, body)

        # Resolve media paths
        media_paths = []
        if media_filenames:
            try:
                media_paths = resolve_media_paths(media_filenames, VAULT_PATH)
            except FileNotFoundError as e:
                return {"published": False, "error": str(e)}

        # Strip media wikilinks from body (they'll be sent as attachments)
        body = strip_media_wikilinks(body)

        # Check and append footer if needed
        footer_exists = check_footer_exists(body)
        final_body = body if footer_exists else append_footer(body)

        # Convert markdown to Telegram HTML
        final_body = convert_markdown_to_telegram_html(final_body)

        # Prepare preview
        preview = {
            "draft_file": str(draft_file),
            "channel": channel,
            "media_count": len(media_paths),
            "media_files": [p.name for p in media_paths],
            "footer_exists": footer_exists,
            "body_preview": final_body[:200] + "..." if len(final_body) > 200 else final_body
        }

        if dry_run:
            preview["published"] = False
            preview["dry_run"] = True
            return preview

        # Send to Telegram
        entity, resolved_name = await resolve_entity(client, "@klodkot")
        if entity is None:
            return {"published": False, "error": "Could not resolve @klodkot channel"}

        try:
            if media_paths:
                # Send as album with caption
                msg = await client.send_file(
                    entity,
                    [str(p) for p in media_paths],
                    caption=final_body,
                    parse_mode='html'
                )
                # msg is a list when sending multiple files
                message_id = msg[0].id if isinstance(msg, list) else msg.id
            else:
                # Send text message
                msg = await client.send_message(entity, final_body, parse_mode='html')
                message_id = msg.id
        except Exception as e:
            return {"published": False, "error": f"Failed to send to Telegram: {e}"}

        # Post-publish operations (only if send succeeded)
        warnings = []

        try:
            # Update frontmatter
            update_frontmatter(draft_file, message_id)

            # Move file to published/
            published_dir = draft_file.parent.parent / "published"
            published_dir.mkdir(exist_ok=True)
            new_path = published_dir / draft_file.name
            draft_file.rename(new_path)

            # Update channel index
            index_path = VAULT_PATH / "Channels" / "klodkot" / "klodkot.md"
            description = extract_first_line(body)
            update_channel_index(index_path, draft_file.name, description)

        except Exception as e:
            warnings.append(f"Post-publish error: {e}")

        result = {
            "published": True,
            "channel": resolved_name,
            "message_id": message_id,
            "media_count": len(media_paths),
            "moved_to": str(new_path) if 'new_path' in locals() else None
        }

        if warnings:
            result["warnings"] = warnings

        return result

    except Exception as e:
        return {"published": False, "error": f"Unexpected error: {e}"}


async def main():
    parser = argparse.ArgumentParser(description="Fetch Telegram messages")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # List chats
    list_parser = subparsers.add_parser("list", help="List available chats")
    list_parser.add_argument("--limit", type=int, default=30, help="Max chats to show")
    list_parser.add_argument("--search", help="Filter chats by name")
    list_parser.add_argument("--exact", action="store_true", help="Require exact name match (case-insensitive)")

    # Recent messages
    recent_parser = subparsers.add_parser("recent", help="Fetch recent messages")
    recent_parser.add_argument("--chat", help="Chat name to filter")
    recent_parser.add_argument("--chat-id", type=int, help="Chat ID to filter")
    recent_parser.add_argument("--limit", type=int, default=50, help="Max messages")
    recent_parser.add_argument("--days", type=int, help="Only messages from last N days")
    recent_parser.add_argument("--to-daily", action="store_true", help="Append to daily note")
    recent_parser.add_argument("--to-person", help="Append to person's note")
    recent_parser.add_argument("--json", action="store_true", help="Output as JSON")
    recent_parser.add_argument("--output", "-o", help="Save to file (markdown) instead of stdout")
    recent_parser.add_argument("--with-media", action="store_true", help="Download media to same folder as output file")

    # Search messages
    search_parser = subparsers.add_parser("search", help="Search messages")
    search_parser.add_argument("query", help="Search query")
    search_parser.add_argument("--chat-id", type=int, help="Limit to specific chat")
    search_parser.add_argument("--limit", type=int, default=50, help="Max results")
    search_parser.add_argument("--to-daily", action="store_true", help="Append to daily note")
    search_parser.add_argument("--to-person", help="Append to person's note")
    search_parser.add_argument("--json", action="store_true", help="Output as JSON")
    search_parser.add_argument("--output", "-o", help="Save to file (markdown) instead of stdout")
    search_parser.add_argument("--with-media", action="store_true", help="Download media to same folder as output file")

    # Unread messages
    unread_parser = subparsers.add_parser("unread", help="Fetch unread messages")
    unread_parser.add_argument("--chat-id", type=int, help="Limit to specific chat")
    unread_parser.add_argument("--to-daily", action="store_true", help="Append to daily note")
    unread_parser.add_argument("--to-person", help="Append to person's note")
    unread_parser.add_argument("--json", action="store_true", help="Output as JSON")
    unread_parser.add_argument("--output", "-o", help="Save to file (markdown) instead of stdout")
    unread_parser.add_argument("--with-media", action="store_true", help="Download media to same folder as output file")

    # Send message
    send_parser = subparsers.add_parser("send", help="Send a message or file")
    send_parser.add_argument("--chat", required=True, help="Chat name, @username, or ID")
    send_parser.add_argument("--text", help="Message text (or caption for files)")
    send_parser.add_argument("--file", help="File path to send (image, document, video)")
    send_parser.add_argument("--reply-to", type=int, help="Message ID to reply to")
    send_parser.add_argument("--topic", type=int, help="Forum topic ID to send to (for groups with topics)")

    # Download media
    download_parser = subparsers.add_parser("download", help="Download media attachments")
    download_parser.add_argument("--chat", required=True, help="Chat name, @username, or ID")
    download_parser.add_argument("--limit", type=int, default=5, help="Max attachments to download (default 5)")
    download_parser.add_argument("--output", help="Output directory (default ~/Downloads/telegram_attachments)")
    download_parser.add_argument("--message-id", type=int, help="Download from specific message ID")

    # Edit message
    edit_parser = subparsers.add_parser("edit", help="Edit an existing message")
    edit_parser.add_argument("--chat", help="Chat name to filter")
    edit_parser.add_argument("--chat-id", type=int, help="Chat ID to filter")
    edit_parser.add_argument("--message-id", type=int, required=True, help="Message ID to edit")
    edit_parser.add_argument("--text", required=True, help="New message text")

    # Setup/status
    setup_parser = subparsers.add_parser("setup", help="Check status or get setup instructions")
    setup_parser.add_argument("--status", action="store_true", help="Check configuration status")

    # Thread messages
    thread_parser = subparsers.add_parser("thread", help="Fetch messages from a forum thread")
    thread_parser.add_argument("--chat-id", type=int, required=True, help="Chat ID")
    thread_parser.add_argument("--thread-id", type=int, required=True, help="Thread/topic ID")
    thread_parser.add_argument("--limit", type=int, default=100, help="Max messages (default 100)")
    thread_parser.add_argument("--to-daily", action="store_true", help="Append to daily note")
    thread_parser.add_argument("--to-person", help="Append to person's note")
    thread_parser.add_argument("--json", action="store_true", help="Output as JSON")
    thread_parser.add_argument("--output", "-o", help="Save to file (markdown) instead of stdout")

    # Publish draft
    publish_parser = subparsers.add_parser("publish", help="Publish draft to channel")
    publish_parser.add_argument("--draft", required=True, help="Draft file path (relative to vault or absolute)")
    publish_parser.add_argument("--dry-run", action="store_true", help="Preview only, don't send")

    args = parser.parse_args()

    # Handle setup command before requiring authentication
    if args.command == "setup":
        result = get_status()
        print(json.dumps(result, indent=2))
        return

    client = await get_client()

    try:
        if args.command == "list":
            chats = await list_chats(client, limit=args.limit, search=args.search, exact=args.exact)
            print(json.dumps(chats, indent=2, ensure_ascii=False))

        elif args.command == "recent":
            messages = await fetch_recent(
                client,
                chat_id=args.chat_id,
                chat_name=args.chat,
                limit=args.limit,
                days=args.days
            )
            output_fmt = "json" if args.json else "markdown"

            if args.output:
                # Save to file instead of stdout
                result = await save_to_file(
                    client, messages, args.output,
                    with_media=args.with_media,
                    output_format=output_fmt
                )
                print(json.dumps(result, indent=2))
            elif args.to_daily:
                output = format_output(messages, output_fmt)
                append_to_daily(output)
            elif args.to_person:
                output = format_output(messages, output_fmt)
                append_to_person(output, args.to_person)
            else:
                output = format_output(messages, output_fmt)
                print(output)

        elif args.command == "search":
            messages = await search_messages(
                client,
                query=args.query,
                chat_id=args.chat_id,
                limit=args.limit
            )
            output_fmt = "json" if args.json else "markdown"

            if args.output:
                result = await save_to_file(
                    client, messages, args.output,
                    with_media=args.with_media,
                    output_format=output_fmt
                )
                print(json.dumps(result, indent=2))
            elif args.to_daily:
                output = format_output(messages, output_fmt)
                append_to_daily(output)
            elif args.to_person:
                output = format_output(messages, output_fmt)
                append_to_person(output, args.to_person)
            else:
                output = format_output(messages, output_fmt)
                print(output)

        elif args.command == "unread":
            messages = await fetch_unread(client, chat_id=args.chat_id)
            output_fmt = "json" if args.json else "markdown"

            if args.output:
                result = await save_to_file(
                    client, messages, args.output,
                    with_media=args.with_media,
                    output_format=output_fmt
                )
                print(json.dumps(result, indent=2))
            elif args.to_daily:
                output = format_output(messages, output_fmt)
                append_to_daily(output)
            elif args.to_person:
                output = format_output(messages, output_fmt)
                append_to_person(output, args.to_person)
            else:
                output = format_output(messages, output_fmt)
                print(output)

        elif args.command == "send":
            if not args.text and not args.file:
                print(json.dumps({"sent": False, "error": "Must provide --text or --file"}))
            else:
                # --topic is an alias for --reply-to (forum topics use reply_to internally)
                reply_to = args.topic if args.topic else args.reply_to
                result = await send_message(
                    client,
                    chat_name=args.chat,
                    text=args.text or "",
                    reply_to=reply_to,
                    file_path=args.file
                )
                print(json.dumps(result, indent=2))

        elif args.command == "download":
            results = await download_media(
                client,
                chat_name=args.chat,
                limit=args.limit,
                output_dir=args.output,
                message_id=args.message_id
            )
            print(json.dumps(results, indent=2))

        elif args.command == "edit":
            result = await edit_message(
                client,
                chat_id=args.chat_id,
                chat_name=args.chat,
                message_id=args.message_id,
                text=args.text
            )
            print(json.dumps(result, indent=2))

        elif args.command == "thread":
            messages = await fetch_thread_messages(
                client,
                chat_id=args.chat_id,
                thread_id=args.thread_id,
                limit=args.limit
            )
            output_fmt = "json" if args.json else "markdown"

            if args.output:
                result = await save_to_file(
                    client, messages, args.output,
                    with_media=False,
                    output_format=output_fmt
                )
                print(json.dumps(result, indent=2))
            elif args.to_daily:
                output = format_output(messages, output_fmt)
                append_to_daily(output)
            elif args.to_person:
                output = format_output(messages, output_fmt)
                append_to_person(output, args.to_person)
            else:
                output = format_output(messages, output_fmt)
                print(output)

        elif args.command == "publish":
            result = await publish_draft(client, args.draft, args.dry_run)
            print(json.dumps(result, indent=2, ensure_ascii=False))
            if not result.get("published", False) and not result.get("dry_run", False):
                sys.exit(1)

    finally:
        await client.disconnect()


if __name__ == "__main__":
    asyncio.run(main())
