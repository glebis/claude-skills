"""Tests for formatting utilities."""
import pytest
from pathlib import Path
from datetime import datetime
import tempfile
import json

from telegram_telethon.utils.formatting import (
    format_messages_markdown,
    format_messages_json,
    format_output,
    format_chats_table,
    append_to_daily,
    append_to_person,
    save_to_file,
)


class TestFormatMessagesMarkdown:
    """Tests for markdown message formatting."""

    def test_single_message(self):
        """Formats single message."""
        messages = [{
            "chat": "John Doe",
            "chat_type": "private",
            "sender": "John",
            "text": "Hello there!",
            "date": "2024-01-15T10:30:00",
            "has_media": False,
        }]

        result = format_messages_markdown(messages)

        assert "## John Doe (private)" in result
        assert "2024-01-15 10:30" in result
        assert "John:" in result
        assert "> Hello there!" in result

    def test_multiple_chats(self):
        """Groups messages by chat."""
        messages = [
            {"chat": "Chat A", "chat_type": "private", "sender": "Alice",
             "text": "Hi", "date": "2024-01-15T10:00:00", "has_media": False},
            {"chat": "Chat B", "chat_type": "group", "sender": "Bob",
             "text": "Hey", "date": "2024-01-15T11:00:00", "has_media": False},
        ]

        result = format_messages_markdown(messages)

        assert "## Chat A (private)" in result
        assert "## Chat B (group)" in result

    def test_media_only_message(self):
        """Formats media-only message."""
        messages = [{
            "chat": "Photos",
            "chat_type": "channel",
            "sender": "Admin",
            "text": "",
            "date": "2024-01-15T10:00:00",
            "has_media": True,
            "media_type": "photo",
        }]

        result = format_messages_markdown(messages)

        assert "[photo]" in result

    def test_message_with_reactions(self):
        """Includes reactions in output."""
        messages = [{
            "chat": "Group",
            "chat_type": "group",
            "sender": "User",
            "text": "Great news!",
            "date": "2024-01-15T10:00:00",
            "has_media": False,
            "reactions": [
                {"emoji": "👍", "count": 5},
                {"emoji": "❤️", "count": 3},
            ],
        }]

        result = format_messages_markdown(messages)

        assert "**Reactions:**" in result
        assert "👍 5" in result
        assert "❤️ 3" in result

    def test_message_with_transcript(self):
        """Includes transcript in output."""
        messages = [{
            "chat": "Voice",
            "chat_type": "private",
            "sender": "User",
            "text": "[voice]",
            "date": "2024-01-15T10:00:00",
            "has_media": True,
            "transcript": "This is the transcribed text",
        }]

        result = format_messages_markdown(messages)

        assert "**Transcript:**" in result
        assert "This is the transcribed text" in result


class TestFormatMessagesJson:
    """Tests for JSON message formatting."""

    def test_json_output(self):
        """Formats messages as JSON."""
        messages = [
            {"id": 1, "text": "Hello"},
            {"id": 2, "text": "World"},
        ]

        result = format_messages_json(messages)
        parsed = json.loads(result)

        assert len(parsed) == 2
        assert parsed[0]["id"] == 1

    def test_unicode_handling(self):
        """Handles unicode characters."""
        messages = [{"text": "Привет 👋"}]

        result = format_messages_json(messages)
        parsed = json.loads(result)

        assert parsed[0]["text"] == "Привет 👋"


class TestFormatOutput:
    """Tests for output format selection."""

    def test_default_markdown(self):
        """Defaults to markdown format."""
        messages = [{"chat": "Test", "chat_type": "private", "sender": "User",
                    "text": "Hi", "date": "2024-01-15T10:00:00", "has_media": False}]

        result = format_output(messages)

        assert "## Test" in result

    def test_explicit_json(self):
        """Uses JSON when specified."""
        messages = [{"id": 1, "text": "Test"}]

        result = format_output(messages, output_format="json")

        assert result.startswith("[")


class TestFormatChatsTable:
    """Tests for chat table formatting."""

    def test_empty_list(self):
        """Returns message for empty list."""
        result = format_chats_table([])
        assert "No chats found" in result

    def test_chat_table(self):
        """Formats chats as table."""
        chats = [
            {"name": "John", "type": "private", "unread": 5, "last_message": "2024-01-15T10:00:00"},
            {"name": "Group", "type": "group", "unread": 0, "last_message": "2024-01-14T09:00:00"},
        ]

        result = format_chats_table(chats)

        assert "| Name | Type | Unread | Last Message |" in result
        assert "| John | private | 5 |" in result
        assert "| Group | group | - |" in result  # 0 unread shows as "-"


class TestAppendToDaily:
    """Tests for daily note appending."""

    def test_creates_daily_if_missing(self):
        """Creates daily note if it doesn't exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            vault = Path(tmpdir)
            today = datetime.now().strftime("%Y%m%d")

            result = append_to_daily("Test content", vault_path=vault)

            assert result.exists()
            assert today in str(result)
            content = result.read_text()
            assert "## Telegram Messages" in content
            assert "Test content" in content

    def test_appends_to_existing(self):
        """Appends to existing daily note."""
        with tempfile.TemporaryDirectory() as tmpdir:
            vault = Path(tmpdir)
            today = datetime.now().strftime("%Y%m%d")
            daily_dir = vault / "Daily"
            daily_dir.mkdir(parents=True)
            daily_path = daily_dir / f"{today}.md"
            daily_path.write_text("# Existing content\n\nSome notes.\n")

            result = append_to_daily("New messages", vault_path=vault)

            content = result.read_text()
            assert "# Existing content" in content
            assert "## Telegram Messages" in content
            assert "New messages" in content

    def test_custom_section_header(self):
        """Uses custom section header."""
        with tempfile.TemporaryDirectory() as tmpdir:
            vault = Path(tmpdir)

            result = append_to_daily(
                "Content",
                vault_path=vault,
                section_header="Custom Section"
            )

            content = result.read_text()
            assert "## Custom Section" in content


class TestAppendToPerson:
    """Tests for person note appending."""

    def test_creates_person_note(self):
        """Creates person note if missing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            vault = Path(tmpdir)

            result = append_to_person("Chat history", "John Doe", vault_path=vault)

            assert result.exists()
            assert "John Doe.md" in str(result)
            content = result.read_text()
            assert "# John Doe" in content
            assert "## Telegram" in content
            assert "Chat history" in content

    def test_appends_to_existing_person(self):
        """Appends to existing person note."""
        with tempfile.TemporaryDirectory() as tmpdir:
            vault = Path(tmpdir)
            person_path = vault / "John Doe.md"
            person_path.write_text("# John Doe\n\nExisting notes.\n")

            result = append_to_person("New conversation", "John Doe", vault_path=vault)

            content = result.read_text()
            assert "Existing notes" in content
            assert "New conversation" in content


class TestSaveToFile:
    """Tests for file saving."""

    def test_save_markdown(self):
        """Saves as markdown."""
        messages = [{"chat": "Test", "chat_type": "private", "sender": "User",
                    "text": "Hello", "date": "2024-01-15T10:00:00", "has_media": False}]

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "output.md"

            result = save_to_file(messages, str(output_path), "markdown")

            assert result["saved"]
            assert result["message_count"] == 1
            assert output_path.exists()
            content = output_path.read_text()
            assert "## Test" in content

    def test_save_json(self):
        """Saves as JSON."""
        messages = [{"id": 1, "text": "Test"}]

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "output.json"

            result = save_to_file(messages, str(output_path), "json")

            assert result["saved"]
            assert result["format"] == "json"
            content = json.loads(output_path.read_text())
            assert content[0]["id"] == 1

    def test_creates_parent_directories(self):
        """Creates parent directories if needed."""
        messages = [{"id": 1}]

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "nested" / "dir" / "output.json"

            result = save_to_file(messages, str(output_path), "json")

            assert result["saved"]
            assert output_path.exists()
