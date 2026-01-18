"""Message operations module.

Handles fetching, searching, sending, and editing messages.
"""
from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any

from telethon import TelegramClient, functions, types
from telethon.tl.types import User, Chat, Channel
from telethon.errors import FloodWaitError

logger = logging.getLogger(__name__)


def get_chat_type(entity) -> str:
    """Determine chat type from entity."""
    if isinstance(entity, User):
        return "private"
    elif isinstance(entity, Chat):
        return "group"
    elif isinstance(entity, Channel):
        return "channel"
    return "unknown"


def format_message(msg, chat_name: str, chat_type: str, include_chat_id: bool = False) -> Dict:
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
            if hasattr(reaction, 'reaction'):
                if hasattr(reaction.reaction, 'emoticon'):
                    reactions.append({
                        "emoji": reaction.reaction.emoticon,
                        "count": reaction.count
                    })
                elif hasattr(reaction.reaction, 'document_id'):
                    reactions.append({
                        "custom_id": str(reaction.reaction.document_id),
                        "count": reaction.count
                    })

    # Detect media type
    media_type = None
    if msg.media:
        media_type = type(msg.media).__name__
        # Common types: MessageMediaPhoto, MessageMediaDocument, MessageMediaWebPage
        if hasattr(msg.media, 'document') and msg.media.document:
            doc = msg.media.document
            for attr in doc.attributes:
                if hasattr(attr, 'voice') and attr.voice:
                    media_type = "voice"
                    break
                elif hasattr(attr, 'round_message') and attr.round_message:
                    media_type = "video_note"
                    break
                elif type(attr).__name__ == 'DocumentAttributeVideo':
                    media_type = "video"
                elif type(attr).__name__ == 'DocumentAttributeAudio':
                    media_type = "audio"

    result = {
        "id": msg.id,
        "chat": chat_name,
        "chat_type": chat_type,
        "sender": sender_name.strip(),
        "text": msg.text or "",
        "date": msg.date.isoformat() if msg.date else None,
        "has_media": msg.media is not None,
        "media_type": media_type,
    }

    if include_chat_id and hasattr(msg, 'chat_id'):
        result["chat_id"] = msg.chat_id

    if reactions:
        result["reactions"] = reactions

    # Include reply info
    if msg.reply_to:
        result["reply_to_msg_id"] = msg.reply_to.reply_to_msg_id

    return result


async def resolve_entity(client: TelegramClient, chat_name: str) -> tuple:
    """Resolve chat name/username/ID to entity and display name."""
    entity = None
    resolved_name = chat_name

    # Try username resolution first
    if chat_name.startswith('@'):
        try:
            entity = await client.get_entity(chat_name)
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


async def list_chats(
    client: TelegramClient,
    limit: int = 30,
    search: Optional[str] = None
) -> List[Dict]:
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


async def fetch_recent(
    client: TelegramClient,
    chat_id: Optional[int] = None,
    chat_name: Optional[str] = None,
    limit: int = 50,
    days: Optional[int] = None,
    include_chat_id: bool = False,
) -> List[Dict]:
    """Fetch recent messages."""
    messages = []

    if chat_id or chat_name:
        # Fetch from specific chat
        if chat_name and not chat_id:
            entity, _ = await resolve_entity(client, chat_name)
            if entity:
                chat_id = entity.id
            else:
                return []

        entity = await client.get_entity(chat_id)
        chat_type = get_chat_type(entity)
        name = getattr(entity, 'title', None) or getattr(entity, 'first_name', '') or "Unknown"

        kwargs = {"limit": limit}
        if days:
            kwargs["offset_date"] = datetime.now() - timedelta(days=days)

        async for msg in client.iter_messages(entity, **kwargs):
            formatted = format_message(msg, name, chat_type, include_chat_id)
            if include_chat_id:
                formatted["chat_id"] = chat_id
            messages.append(formatted)
            await asyncio.sleep(0.1)  # Rate limiting
    else:
        # Fetch from all recent chats
        dialogs = await client.get_dialogs(limit=10)
        max_per_chat = limit // 10

        for d in dialogs:
            name = d.name or "Unnamed"
            chat_type = get_chat_type(d.entity)

            try:
                async for msg in client.iter_messages(d.entity, limit=max_per_chat):
                    if days:
                        cutoff = datetime.now(msg.date.tzinfo) - timedelta(days=days)
                        if msg.date < cutoff:
                            break
                    formatted = format_message(msg, name, chat_type, include_chat_id)
                    if include_chat_id:
                        formatted["chat_id"] = d.id
                    messages.append(formatted)
                    await asyncio.sleep(0.1)
            except FloodWaitError as e:
                logger.warning(f"Rate limited, waiting {e.seconds}s...")
                await asyncio.sleep(e.seconds)

    return messages


async def search_messages(
    client: TelegramClient,
    query: str,
    chat_id: Optional[int] = None,
    chat_name: Optional[str] = None,
    limit: int = 50,
) -> List[Dict]:
    """Search messages by content."""
    messages = []

    if chat_id or chat_name:
        # Search in specific chat
        if chat_name and not chat_id:
            entity, _ = await resolve_entity(client, chat_name)
            if entity:
                chat_id = entity.id

        if chat_id:
            entity = await client.get_entity(chat_id)
            chat_type = get_chat_type(entity)
            name = getattr(entity, 'title', None) or getattr(entity, 'first_name', '') or "Unknown"

            async for msg in client.iter_messages(entity, search=query, limit=limit):
                messages.append(format_message(msg, name, chat_type))
                await asyncio.sleep(0.1)
    else:
        # Global search across recent chats
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
                continue
            if len(messages) >= limit:
                break

    return messages


async def fetch_unread(
    client: TelegramClient,
    chat_id: Optional[int] = None,
) -> List[Dict]:
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
            await asyncio.sleep(e.seconds)

    return messages


async def fetch_thread(
    client: TelegramClient,
    chat_id: int,
    thread_id: int,
    limit: int = 100,
) -> List[Dict]:
    """Fetch messages from a forum thread."""
    entity = await client.get_entity(chat_id)
    chat_type = get_chat_type(entity)
    name = getattr(entity, 'title', None) or getattr(entity, 'first_name', '') or "Unknown"

    messages = []
    async for msg in client.iter_messages(entity, reply_to=thread_id, limit=limit):
        messages.append(format_message(msg, name, chat_type))
        await asyncio.sleep(0.1)

    return messages


async def send_message(
    client: TelegramClient,
    chat_name: str,
    text: str,
    reply_to: Optional[int] = None,
    file_path: Optional[str] = None,
    allowed_groups: Optional[List[str]] = None,
) -> Dict:
    """Send a message or file to a chat."""
    import os

    entity, resolved_name = await resolve_entity(client, chat_name)

    if entity is None:
        return {"sent": False, "error": f"Chat '{chat_name}' not found"}

    # Safety check for groups/channels
    chat_type = get_chat_type(entity)
    if chat_type in ["group", "channel"]:
        allowed = allowed_groups or []
        entity_id = getattr(entity, 'id', None)
        if resolved_name not in allowed and str(entity_id) not in allowed:
            return {
                "sent": False,
                "error": f"Sending to groups/channels requires whitelist. Add '{resolved_name}' to allowed_send_groups.",
                "chat_type": chat_type,
                "chat_name": resolved_name,
                "chat_id": entity_id
            }

    try:
        if file_path:
            if not os.path.exists(file_path):
                return {"sent": False, "error": f"File not found: {file_path}"}

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
                    "name": os.path.basename(file_path),
                    "size": os.path.getsize(file_path),
                }
            }
        else:
            msg = await client.send_message(entity, text, reply_to=reply_to)
            return {
                "sent": True,
                "chat": resolved_name,
                "message_id": msg.id,
                "reply_to": reply_to
            }
    except Exception as e:
        return {"sent": False, "error": str(e)}


async def edit_message(
    client: TelegramClient,
    chat_name: str,
    message_id: int,
    text: str,
) -> Dict:
    """Edit an existing message."""
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


async def delete_messages(
    client: TelegramClient,
    chat_name: str,
    message_ids: List[int],
    revoke: bool = True,
) -> Dict:
    """Delete messages."""
    entity, resolved_name = await resolve_entity(client, chat_name)

    if entity is None:
        return {"deleted": False, "error": f"Chat '{chat_name}' not found"}

    try:
        await client.delete_messages(entity, message_ids, revoke=revoke)
        return {
            "deleted": True,
            "chat": resolved_name,
            "message_ids": message_ids,
            "revoked": revoke
        }
    except Exception as e:
        return {"deleted": False, "error": str(e)}


async def forward_messages(
    client: TelegramClient,
    from_chat: str,
    to_chat: str,
    message_ids: List[int],
) -> Dict:
    """Forward messages to another chat."""
    from_entity, from_name = await resolve_entity(client, from_chat)
    to_entity, to_name = await resolve_entity(client, to_chat)

    if from_entity is None:
        return {"forwarded": False, "error": f"Source chat '{from_chat}' not found"}
    if to_entity is None:
        return {"forwarded": False, "error": f"Destination chat '{to_chat}' not found"}

    try:
        result = await client.forward_messages(to_entity, message_ids, from_entity)
        return {
            "forwarded": True,
            "from_chat": from_name,
            "to_chat": to_name,
            "message_count": len(message_ids) if isinstance(message_ids, list) else 1,
        }
    except Exception as e:
        return {"forwarded": False, "error": str(e)}


async def mark_read(
    client: TelegramClient,
    chat_name: str,
    max_id: Optional[int] = None,
) -> Dict:
    """Mark messages as read."""
    entity, resolved_name = await resolve_entity(client, chat_name)

    if entity is None:
        return {"marked": False, "error": f"Chat '{chat_name}' not found"}

    try:
        await client.send_read_acknowledge(entity, max_id=max_id)
        return {
            "marked": True,
            "chat": resolved_name,
            "max_id": max_id
        }
    except Exception as e:
        return {"marked": False, "error": str(e)}


MAX_DRAFT_LENGTH = 4096


async def save_draft(
    client: TelegramClient,
    chat_name: str,
    text: str,
    reply_to: Optional[int] = None,
    no_webpage: bool = False
) -> Dict:
    """Save a draft message to a chat.

    Args:
        client: Authenticated TelegramClient
        chat_name: Chat name, @username, or ID
        text: Draft text (empty string clears draft)
        reply_to: Optional message ID to reply to
        no_webpage: Disable link preview

    Returns:
        Dict with status and draft info
    """
    # Input validation
    if len(text) > MAX_DRAFT_LENGTH:
        return {
            "saved": False,
            "error": f"Draft text exceeds {MAX_DRAFT_LENGTH} characters ({len(text)} provided)"
        }

    entity, resolved_name = await resolve_entity(client, chat_name)
    if not entity:
        return {"saved": False, "error": f"Chat '{chat_name}' not found"}

    reply_obj = None
    if reply_to:
        reply_obj = types.InputReplyToMessage(reply_to_msg_id=reply_to)

    await client(functions.messages.SaveDraftRequest(
        peer=entity,
        message=text,
        no_webpage=no_webpage,
        reply_to=reply_obj
    ))

    return {
        "saved": True,
        "chat": resolved_name,
        "text_preview": text[:50] + "..." if len(text) > 50 else text,
        "cleared": text == ""
    }


async def get_all_drafts(client: TelegramClient) -> List[Dict]:
    """Get all drafts across all chats.

    Returns:
        List of draft dicts with chat info and text
    """
    drafts = []
    async for draft in client.iter_drafts():
        if draft.is_empty:
            continue
        entity = await draft.get_entity()
        name = getattr(entity, 'title', None) or \
               getattr(entity, 'first_name', 'Unknown')
        drafts.append({
            "chat": name,
            "chat_id": entity.id,
            "text": draft.raw_text,
            "text_preview": draft.raw_text[:50] + "..." if len(draft.raw_text) > 50 else draft.raw_text,
            "date": draft.date.isoformat() if hasattr(draft, 'date') and draft.date else None
        })
    return drafts


async def clear_all_drafts(client: TelegramClient) -> Dict:
    """Clear all drafts.

    Returns:
        Dict with status
    """
    await client(functions.messages.ClearAllDraftsRequest())
    return {"cleared": True, "all": True}


async def send_draft(
    client: TelegramClient,
    chat_name: str,
    allowed_groups: Optional[List[str]] = None,
) -> Dict:
    """Send draft as message and clear it.

    Args:
        client: Authenticated TelegramClient
        chat_name: Chat to send draft from
        allowed_groups: Whitelist for groups/channels (security check)

    Returns:
        Dict with status and message info
    """
    entity, resolved_name = await resolve_entity(client, chat_name)
    if not entity:
        return {"sent": False, "error": f"Chat '{chat_name}' not found"}

    # Security: Authorization check for groups/channels (same as send_message)
    chat_type = get_chat_type(entity)
    if chat_type in ["group", "channel"]:
        allowed = allowed_groups or []
        entity_id = getattr(entity, 'id', None)
        if resolved_name not in allowed and str(entity_id) not in allowed:
            return {
                "sent": False,
                "error": f"Sending to groups/channels requires whitelist. Add '{resolved_name}' to allowed_send_groups.",
            }

    # Get draft for this chat
    draft = None
    async for d in client.iter_drafts([entity]):
        draft = d
        break

    if not draft or draft.is_empty:
        return {"sent": False, "error": f"No draft found for '{resolved_name}'"}

    # Send the draft text as a message
    text_preview = draft.raw_text[:50] + "..." if len(draft.raw_text) > 50 else draft.raw_text
    draft_text = draft.raw_text

    # Use client.send_message directly (more reliable than draft.send())
    msg = await client.send_message(entity, draft_text)

    # Clear the draft after sending
    await draft.delete()

    return {
        "sent": True,
        "chat": resolved_name,
        "message_id": msg.id,
        "text_preview": text_preview
    }
