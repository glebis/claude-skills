#!/usr/bin/env python3
"""Hook for tgd.py daemon — writes incoming DMs to responder.db.

Called from the Telethon daemon's event handler. This module must be
importable from the daemon process. It does NO LLM reasoning — only
deterministic routing and queue writes.
"""

import logging
import sqlite3
import time
from pathlib import Path
from typing import Optional

from classify import load_config, ResponderConfig, RouteResult

logger = logging.getLogger(__name__)

_config: Optional[ResponderConfig] = None
_conn: Optional[sqlite3.Connection] = None


def _get_config() -> ResponderConfig:
    global _config
    if _config is None:
        _config = load_config()
    return _config


def _get_db() -> sqlite3.Connection:
    global _conn
    if _conn is None:
        from schema import get_db
        _conn = get_db()
    return _conn


def reload_config() -> None:
    """Force config reload (call after editing config.yaml)."""
    global _config
    _config = None


def on_new_dm(
    chat_id: int,
    message_id: int,
    sender_id: int,
    sender_name: str,
    text: Optional[str],
    has_media: bool = False,
    media_type: Optional[str] = None,
    is_bot: bool = False,
    received_at: Optional[int] = None,
) -> Optional[str]:
    """Process an incoming DM event.

    Called by the Telethon daemon on each new private message.

    Returns:
        The route string if queued, None if ignored/duplicate.
    """
    config = _get_config()
    now = int(time.time())
    received_at = received_at or now

    result = config.classify(sender_name, text or "", is_bot)

    if result.route == "ignored":
        logger.debug(f"Ignored message from {sender_name}")
        return None

    db = _get_db()

    try:
        cursor = db.execute(
            """INSERT OR IGNORE INTO inbox (
                chat_id, message_id, sender_id, sender_name, text,
                has_media, media_type, received_at,
                route, contact_mode, priority,
                status, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'pending', ?, ?)""",
            (
                chat_id, message_id, sender_id, sender_name, text,
                1 if has_media else 0, media_type, received_at,
                result.route, result.contact_mode, result.priority,
                now, now,
            ),
        )
        db.commit()
    except sqlite3.Error as e:
        logger.error(f"DB error writing inbox: {e}")
        return None

    if cursor.rowcount == 0:
        logger.debug(f"Duplicate message {chat_id}:{message_id}")
        return None

    logger.info(f"Queued: {sender_name} → {result.route} (mode={result.contact_mode})")

    signal_path = config.daemon.get("signal_path", "/tmp/tg-responder-signal")
    try:
        Path(signal_path).touch()
    except OSError:
        pass

    return result.route
