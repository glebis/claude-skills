#!/usr/bin/env python3
"""Backfill responder inbox with currently unread DMs from Telegram.

Fetches dialogs with unread messages, gets the last message from each,
queues only those where the last message is FROM the other person
(i.e., they're waiting for a reply).

Must be run when the daemon is NOT running (shares Telethon session).
"""

import asyncio
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path.home() / ".claude/skills/telegram-telethon/src"))

from telethon import TelegramClient
from telegram_telethon.core.config import Config, DEFAULT_CONFIG_DIR
from classify import load_config
from schema import get_db


async def backfill():
    config = Config.load(DEFAULT_CONFIG_DIR / "config.yaml")
    session_path = DEFAULT_CONFIG_DIR / "session"
    client = TelegramClient(str(session_path), config.api_id, config.api_hash)

    await client.start()
    me = await client.get_me()
    print(f"Connected as {me.first_name} (id={me.id})")

    responder_config = load_config()
    db = get_db()
    now = int(time.time())
    queued = 0
    skipped_bot = 0
    skipped_self = 0
    skipped_ignored = 0
    skipped_read = 0

    async for dialog in client.iter_dialogs(limit=200):
        # Only private DMs
        if not dialog.is_user:
            continue

        # Skip if no unread
        if dialog.unread_count == 0:
            skipped_read += 1
            continue

        entity = dialog.entity

        # Skip bots
        if getattr(entity, 'bot', False):
            skipped_bot += 1
            continue

        # Get sender name
        sender_name = getattr(entity, 'first_name', '') or ''
        if getattr(entity, 'last_name', None):
            sender_name += f" {entity.last_name}"
        sender_name = sender_name.strip()

        # Skip ignored contacts
        if responder_config.is_ignored(sender_name):
            skipped_ignored += 1
            continue

        # Get the last message
        msg = dialog.message
        if not msg:
            continue

        # Skip if last message is FROM us (we already replied)
        if msg.sender_id == me.id:
            skipped_self += 1
            continue

        text = msg.text or ""
        has_media = msg.media is not None
        media_type = type(msg.media).__name__ if msg.media else None

        # Classify
        result = responder_config.classify(sender_name, text, False)
        if result.route == "ignored":
            skipped_ignored += 1
            continue

        # Insert into inbox
        try:
            cursor = db.execute(
                """INSERT OR IGNORE INTO inbox (
                    chat_id, message_id, sender_id, sender_name, text,
                    has_media, media_type, received_at,
                    route, contact_mode, priority,
                    status, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'pending', ?, ?)""",
                (
                    dialog.id, msg.id, entity.id, sender_name, text,
                    1 if has_media else 0, media_type,
                    int(msg.date.timestamp()),
                    result.route, result.contact_mode, result.priority,
                    now, now,
                ),
            )
            if cursor.rowcount > 0:
                queued += 1
                print(f"  ✓ {sender_name:25s} unread={dialog.unread_count:3d}  route={result.route}")
        except Exception as e:
            print(f"  ✗ {sender_name}: {e}")

    db.commit()
    await client.disconnect()

    print(f"\nQueued: {queued}")
    print(f"Skipped: read={skipped_read} self={skipped_self} bot={skipped_bot} ignored={skipped_ignored}")


if __name__ == "__main__":
    asyncio.run(backfill())
