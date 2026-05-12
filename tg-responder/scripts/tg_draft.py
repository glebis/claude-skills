#!/usr/bin/env python3
"""Set Telegram native drafts so they appear on the user's phone.

Usage: python3 tg_draft.py --chat-id 12345 --text "Draft text" [--reply-to 678]
"""

import argparse
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path.home() / ".claude/skills/telegram-telethon/src"))

from telethon import TelegramClient
from telethon.tl.functions.messages import SaveDraftRequest
from telethon.tl.types import InputReplyToMessage
from telegram_telethon.core.config import Config, DEFAULT_CONFIG_DIR


async def set_draft(chat_id: int, text: str, reply_to: int | None = None) -> bool:
    config = Config.load(DEFAULT_CONFIG_DIR / "config.yaml")
    session_path = DEFAULT_CONFIG_DIR / "session"
    client = TelegramClient(str(session_path), config.api_id, config.api_hash)

    await client.start()
    try:
        reply_obj = InputReplyToMessage(reply_to_msg_id=reply_to) if reply_to else None
        await client(SaveDraftRequest(
            peer=chat_id,
            message=text,
            reply_to=reply_obj,
        ))
        return True
    finally:
        await client.disconnect()


def main():
    parser = argparse.ArgumentParser(description="Set Telegram draft")
    parser.add_argument("--chat-id", type=int, required=True)
    parser.add_argument("--text", required=True)
    parser.add_argument("--reply-to", type=int, default=None)
    args = parser.parse_args()

    ok = asyncio.run(set_draft(args.chat_id, args.text, args.reply_to))
    print("ok" if ok else "failed")


if __name__ == "__main__":
    main()
