#!/usr/bin/env python3
"""
Send messages via Telegram Bot API.
Uses TELEGRAM_BOT_TOKEN environment variable.
Can send to specific chat_id or lookup from admin_contacts database.

Supports Telegram HTML formatting (default):
  <b>bold</b>, <i>italic</i>, <u>underline</u>, <s>strikethrough</s>
  <code>inline code</code>, <pre>code block</pre>
  <a href="URL">link</a>, <tg-spoiler>spoiler</tg-spoiler>

Use --raw to send without HTML parsing (plain text, auto-escaped).
"""
import argparse
import asyncio
import html
import json
import os
import re
import sqlite3
import sys
from pathlib import Path
from typing import Optional

# Try to load environment from common locations
def load_env():
    """Load environment variables from .env files."""
    try:
        from dotenv import load_dotenv

        # Load from multiple locations in priority order
        env_files = [
            Path.home() / ".env",
            Path("/Users/server/ai_projects/telegram_agent/.env.local"),
            Path("/Users/server/ai_projects/telegram_agent/.env"),
        ]

        for env_file in env_files:
            if env_file.exists():
                load_dotenv(env_file, override=False)
    except ImportError:
        pass  # dotenv not available, rely on system environment

load_env()

# Default admin contacts database
DEFAULT_DB_PATH = Path("/Users/server/ai_projects/telegram_agent/data/telegram_agent.db")
# Default chat_id (glebkalinin)
DEFAULT_CHAT_ID = 161427550


def get_chat_id_from_db(name: Optional[str] = None, role: Optional[str] = None) -> Optional[int]:
    """Lookup chat_id from admin_contacts database."""
    if not DEFAULT_DB_PATH.exists():
        return None

    try:
        conn = sqlite3.connect(str(DEFAULT_DB_PATH))
        cursor = conn.cursor()

        if name:
            cursor.execute(
                "SELECT chat_id FROM admin_contacts WHERE name LIKE ? AND active = 1",
                (f"%{name}%",)
            )
        elif role:
            cursor.execute(
                "SELECT chat_id FROM admin_contacts WHERE role = ? AND active = 1",
                (role,)
            )
        else:
            # Get first active contact (usually owner)
            cursor.execute(
                "SELECT chat_id FROM admin_contacts WHERE active = 1 ORDER BY id LIMIT 1"
            )

        row = cursor.fetchone()
        conn.close()

        return row[0] if row else None
    except Exception as e:
        print(json.dumps({"error": f"Database lookup failed: {e}"}), file=sys.stderr)
        return None


def list_contacts() -> list:
    """List all admin contacts from database."""
    if not DEFAULT_DB_PATH.exists():
        return []

    try:
        conn = sqlite3.connect(str(DEFAULT_DB_PATH))
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, chat_id, username, name, role, active FROM admin_contacts"
        )
        rows = cursor.fetchall()
        conn.close()

        return [
            {
                "id": row[0],
                "chat_id": row[1],
                "username": row[2],
                "name": row[3],
                "role": row[4],
                "active": bool(row[5])
            }
            for row in rows
        ]
    except Exception as e:
        print(json.dumps({"error": f"Failed to list contacts: {e}"}), file=sys.stderr)
        return []


# Telegram HTML allowed tags (used to detect if text contains HTML)
TELEGRAM_HTML_TAGS = re.compile(
    r'<(/?)(b|strong|i|em|u|ins|s|strike|del|code|pre|a|tg-spoiler|span)(\s[^>]*)?>',
    re.IGNORECASE
)


def format_for_telegram(text: str, raw: bool = False) -> tuple[str, Optional[str]]:
    """
    Format text for Telegram.

    Returns (formatted_text, parse_mode).

    - If raw=True: escapes HTML chars, returns (escaped_text, None)
    - If text contains HTML tags: returns (text, "HTML")
    - Otherwise: escapes HTML chars for safety, returns (escaped_text, "HTML")
    """
    if raw:
        # Raw mode: escape everything, no parse mode
        return html.escape(text), None

    # Check if text already contains Telegram HTML tags
    if TELEGRAM_HTML_TAGS.search(text):
        # Text has HTML formatting, use as-is
        return text, "HTML"

    # Plain text: escape for HTML safety but still use HTML mode
    # This allows us to be consistent with HTML mode
    return html.escape(text), "HTML"


async def send_message(chat_id: int, text: str, parse_mode: Optional[str] = None, raw: bool = False) -> dict:
    """Send a message via Telegram Bot API."""
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not token:
        return {"sent": False, "error": "TELEGRAM_BOT_TOKEN not set"}

    try:
        from telegram import Bot

        # Format text for Telegram
        if parse_mode is None and not raw:
            formatted_text, auto_parse_mode = format_for_telegram(text, raw=False)
            text = formatted_text
            parse_mode = auto_parse_mode
        elif raw:
            text = html.escape(text)
            parse_mode = None

        bot = Bot(token)
        msg = await bot.send_message(
            chat_id=chat_id,
            text=text,
            parse_mode=parse_mode
        )
        return {
            "sent": True,
            "chat_id": chat_id,
            "message_id": msg.message_id,
            "parse_mode": parse_mode
        }
    except Exception as e:
        return {"sent": False, "chat_id": chat_id, "error": str(e)}


async def main():
    # Check if first arg is a subcommand
    if len(sys.argv) > 1 and sys.argv[1] == "list":
        # List command
        contacts = list_contacts()
        print(json.dumps(contacts, indent=2))
        return

    # Default: send command
    parser = argparse.ArgumentParser(
        description="Send messages via Telegram Bot API (HTML formatting by default)",
        usage="%(prog)s --text TEXT [options]\n"
              "       %(prog)s list",
        epilog="""
HTML formatting (auto-detected):
  <b>bold</b>  <i>italic</i>  <u>underline</u>  <s>strike</s>
  <code>code</code>  <pre>block</pre>  <a href="URL">link</a>
  <tg-spoiler>spoiler</tg-spoiler>

Examples:
  %(prog)s --text "Hello world"
  %(prog)s --text "<b>Important:</b> Check this out"
  %(prog)s --text "Code: <code>print('hi')</code>"
""",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("--text", "-t", required=True, help="Message text (supports HTML tags)")
    parser.add_argument("--chat-id", "-c", type=int, help="Telegram chat ID")
    parser.add_argument("--name", "-n", help="Lookup chat_id by contact name")
    parser.add_argument("--role", "-r", help="Lookup chat_id by role")
    parser.add_argument("--raw", action="store_true", help="Send as plain text (no HTML parsing)")
    parser.add_argument("--parse-mode", "-p", choices=["HTML", "Markdown", "MarkdownV2"],
                        help="Override parse mode (default: auto-detect HTML)")

    args = parser.parse_args()

    # Determine chat_id
    chat_id = args.chat_id

    if not chat_id and args.name:
        chat_id = get_chat_id_from_db(name=args.name)
    elif not chat_id and args.role:
        chat_id = get_chat_id_from_db(role=args.role)
    elif not chat_id:
        # Use default (first active contact or hardcoded default)
        chat_id = get_chat_id_from_db() or DEFAULT_CHAT_ID

    if not chat_id:
        print(json.dumps({"sent": False, "error": "No chat_id specified and no contacts found"}))
        sys.exit(1)

    result = await send_message(
        chat_id=chat_id,
        text=args.text,
        parse_mode=args.parse_mode,
        raw=args.raw
    )
    print(json.dumps(result, indent=2))

    if not result.get("sent"):
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
