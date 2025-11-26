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


async def get_client() -> TelegramClient:
    """Get authenticated Telegram client."""
    if not is_configured():
        print("ERROR: Telegram not configured. Run telegram_dl.py first to authenticate.", file=sys.stderr)
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

    return {
        "id": msg.id,
        "chat": chat_name,
        "chat_type": chat_type,
        "sender": sender_name.strip(),
        "text": msg.text or "",
        "date": msg.date.isoformat() if msg.date else None,
        "has_media": msg.media is not None
    }


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
    """
    entity, resolved_name = await resolve_entity(client, chat_name)

    if entity is None:
        return {"sent": False, "error": f"Chat '{chat_name}' not found"}

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
            lines.append(f"> {text}\n")

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

    # Search messages
    search_parser = subparsers.add_parser("search", help="Search messages")
    search_parser.add_argument("query", help="Search query")
    search_parser.add_argument("--chat-id", type=int, help="Limit to specific chat")
    search_parser.add_argument("--limit", type=int, default=50, help="Max results")
    search_parser.add_argument("--to-daily", action="store_true", help="Append to daily note")
    search_parser.add_argument("--to-person", help="Append to person's note")
    search_parser.add_argument("--json", action="store_true", help="Output as JSON")

    # Unread messages
    unread_parser = subparsers.add_parser("unread", help="Fetch unread messages")
    unread_parser.add_argument("--chat-id", type=int, help="Limit to specific chat")
    unread_parser.add_argument("--to-daily", action="store_true", help="Append to daily note")
    unread_parser.add_argument("--to-person", help="Append to person's note")
    unread_parser.add_argument("--json", action="store_true", help="Output as JSON")

    # Send message
    send_parser = subparsers.add_parser("send", help="Send a message or file")
    send_parser.add_argument("--chat", required=True, help="Chat name, @username, or ID")
    send_parser.add_argument("--text", help="Message text (or caption for files)")
    send_parser.add_argument("--file", help="File path to send (image, document, video)")
    send_parser.add_argument("--reply-to", type=int, help="Message ID to reply to")

    # Download media
    download_parser = subparsers.add_parser("download", help="Download media attachments")
    download_parser.add_argument("--chat", required=True, help="Chat name, @username, or ID")
    download_parser.add_argument("--limit", type=int, default=5, help="Max attachments to download (default 5)")
    download_parser.add_argument("--output", help="Output directory (default ~/Downloads/telegram_attachments)")
    download_parser.add_argument("--message-id", type=int, help="Download from specific message ID")

    args = parser.parse_args()

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
            output = format_output(messages, output_fmt)

            if args.to_daily:
                append_to_daily(output)
            elif args.to_person:
                append_to_person(output, args.to_person)
            else:
                print(output)

        elif args.command == "search":
            messages = await search_messages(
                client,
                query=args.query,
                chat_id=args.chat_id,
                limit=args.limit
            )
            output_fmt = "json" if args.json else "markdown"
            output = format_output(messages, output_fmt)

            if args.to_daily:
                append_to_daily(output)
            elif args.to_person:
                append_to_person(output, args.to_person)
            else:
                print(output)

        elif args.command == "unread":
            messages = await fetch_unread(client, chat_id=args.chat_id)
            output_fmt = "json" if args.json else "markdown"
            output = format_output(messages, output_fmt)

            if args.to_daily:
                append_to_daily(output)
            elif args.to_person:
                append_to_person(output, args.to_person)
            else:
                print(output)

        elif args.command == "send":
            if not args.text and not args.file:
                print(json.dumps({"sent": False, "error": "Must provide --text or --file"}))
            else:
                result = await send_message(
                    client,
                    chat_name=args.chat,
                    text=args.text or "",
                    reply_to=args.reply_to,
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

    finally:
        await client.disconnect()


if __name__ == "__main__":
    asyncio.run(main())
