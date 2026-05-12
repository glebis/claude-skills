#!/usr/bin/env python3
"""Look up a Telegram chat ID by name. Fuzzy match, handles missing results.

Usage: python3 lookup_chat.py "Alexander"
"""

import json
import subprocess
import sys
from pathlib import Path


def lookup(query: str) -> dict | None:
    result = subprocess.run(
        [
            "python3",
            str(Path.home() / ".claude/skills/telegram/scripts/telegram_fetch.py"),
            "list", "--search", query, "--limit", "100",
        ],
        capture_output=True, text=True, timeout=30,
    )
    if result.returncode != 0:
        return None

    chats = json.loads(result.stdout)
    if not chats:
        return None
    return chats[0]


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: lookup_chat.py <name>")
        sys.exit(1)

    chat = lookup(sys.argv[1])
    if chat:
        print(f"{chat['name']} (id={chat['id']}, type={chat['type']})")
    else:
        print(f"No chat found matching '{sys.argv[1]}'")
        sys.exit(1)
