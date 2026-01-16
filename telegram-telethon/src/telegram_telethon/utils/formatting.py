"""Output formatting utilities."""
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional


# Default Obsidian vault path
DEFAULT_VAULT_PATH = Path.home() / 'Brains' / 'brain'


def format_messages_markdown(messages: List[Dict]) -> str:
    """Format messages as markdown."""
    lines = []
    current_chat = None

    for msg in messages:
        if msg.get("chat") != current_chat:
            current_chat = msg.get("chat")
            chat_type = msg.get("chat_type", "unknown")
            lines.append(f"\n## {current_chat} ({chat_type})\n")

        date_str = ""
        if msg.get("date"):
            try:
                dt = datetime.fromisoformat(msg["date"])
                date_str = dt.strftime("%Y-%m-%d %H:%M")
            except (ValueError, TypeError):
                date_str = msg["date"]

        sender = msg.get("sender", "Unknown")
        text = msg.get("text", "")

        if msg.get("has_media") and not text:
            media_type = msg.get("media_type", "media")
            text = f"[{media_type}]"

        if text:
            lines.append(f"**{date_str}** - {sender}:")
            lines.append(f"> {text}")

            # Add reactions if present
            if msg.get("reactions"):
                reaction_str = " ".join([
                    f"{r['emoji']} {r['count']}" if 'emoji' in r
                    else f"[custom] {r['count']}"
                    for r in msg["reactions"]
                ])
                lines.append(f"> **Reactions:** {reaction_str}")

            # Add transcript if present
            if msg.get("transcript"):
                lines.append(f"> **Transcript:** {msg['transcript']}")

            lines.append("")  # Empty line

    return "\n".join(lines)


def format_messages_json(messages: List[Dict]) -> str:
    """Format messages as JSON."""
    return json.dumps(messages, indent=2, ensure_ascii=False)


def format_output(messages: List[Dict], output_format: str = "markdown") -> str:
    """Format messages for output."""
    if output_format == "json":
        return format_messages_json(messages)
    return format_messages_markdown(messages)


def format_chats_table(chats: List[Dict]) -> str:
    """Format chat list as a table."""
    if not chats:
        return "No chats found."

    lines = ["| Name | Type | Unread | Last Message |", "|------|------|--------|--------------|"]

    for chat in chats:
        name = chat.get("name", "Unknown")
        chat_type = chat.get("type", "unknown")
        unread = chat.get("unread", 0)
        last_msg = chat.get("last_message", "")
        if last_msg:
            try:
                dt = datetime.fromisoformat(last_msg)
                last_msg = dt.strftime("%Y-%m-%d %H:%M")
            except (ValueError, TypeError):
                pass

        unread_str = str(unread) if unread > 0 else "-"
        lines.append(f"| {name} | {chat_type} | {unread_str} | {last_msg} |")

    return "\n".join(lines)


def append_to_daily(
    content: str,
    vault_path: Optional[Path] = None,
    section_header: str = "Telegram Messages",
) -> Path:
    """Append content to today's daily note.

    Args:
        content: Content to append
        vault_path: Path to Obsidian vault
        section_header: Header for the section

    Returns:
        Path to the daily note
    """
    vault = vault_path or DEFAULT_VAULT_PATH
    today = datetime.now().strftime("%Y%m%d")
    daily_path = vault / "Daily" / f"{today}.md"

    if not daily_path.exists():
        daily_path.parent.mkdir(parents=True, exist_ok=True)
        daily_path.write_text(f"# {today}\n\n")

    with open(daily_path, 'a') as f:
        f.write(f"\n## {section_header}\n{content}\n")

    return daily_path


def append_to_person(
    content: str,
    person_name: str,
    vault_path: Optional[Path] = None,
) -> Path:
    """Append content to a person's note.

    Args:
        content: Content to append
        person_name: Name of the person
        vault_path: Path to Obsidian vault

    Returns:
        Path to the person's note
    """
    vault = vault_path or DEFAULT_VAULT_PATH
    person_path = vault / f"{person_name}.md"

    if not person_path.exists():
        person_path.write_text(f"# {person_name}\n\n")

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    with open(person_path, 'a') as f:
        f.write(f"\n## Telegram ({timestamp})\n{content}\n")

    return person_path


def save_to_file(
    messages: List[Dict],
    output_path: str,
    output_format: str = "markdown",
) -> Dict:
    """Save messages to file.

    Args:
        messages: List of message dicts
        output_path: Path to output file
        output_format: 'markdown' or 'json'

    Returns:
        Dict with save status
    """
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)

    content = format_output(messages, output_format)
    output_file.write_text(content, encoding='utf-8')

    return {
        "saved": True,
        "file": str(output_file),
        "message_count": len(messages),
        "format": output_format,
    }
