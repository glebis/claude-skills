#!/usr/bin/env python3
"""
Telegram message fetcher for Claude Code skill.
Fetches messages from Telegram with various filters and outputs.
"""
import asyncio
import argparse
import json
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, List, Dict, Any

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


async def list_chats(client: TelegramClient, limit: int = 30, search: Optional[str] = None) -> List[Dict]:
    """List available chats."""
    dialogs = await client.get_dialogs(limit=limit)

    chats = []
    for d in dialogs:
        name = d.name or "Unnamed"
        if search and search.lower() not in name.lower():
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


async def edit_message(client: TelegramClient, chat_name: str, message_id: int,
                       text: str) -> Dict:
    """Edit an existing message.

    Args:
        chat_name: Chat name, @username, or ID
        message_id: ID of the message to edit
        text: New text content

    Returns:
        Dict with edit status
    """
    entity, resolved_name = await resolve_entity(client, chat_name)

    if entity is None:
        return {"edited": False, "error": f"Chat '{chat_name}' not found"}

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


async def main():
    parser = argparse.ArgumentParser(description="Fetch Telegram messages")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # List chats
    list_parser = subparsers.add_parser("list", help="List available chats")
    list_parser.add_argument("--limit", type=int, default=30, help="Max chats to show")
    list_parser.add_argument("--search", help="Filter chats by name")

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
    edit_parser.add_argument("--chat", required=True, help="Chat name, @username, or ID")
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

    args = parser.parse_args()

    # Handle setup command before requiring authentication
    if args.command == "setup":
        result = get_status()
        print(json.dumps(result, indent=2))
        return

    client = await get_client()

    try:
        if args.command == "list":
            chats = await list_chats(client, limit=args.limit, search=args.search)
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

    finally:
        await client.disconnect()


if __name__ == "__main__":
    asyncio.run(main())
