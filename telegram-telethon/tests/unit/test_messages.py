"""Tests for messages module."""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch, PropertyMock
from datetime import datetime, timedelta

from telegram_telethon.modules.messages import (
    get_chat_type,
    format_message,
    resolve_entity,
    list_chats,
    fetch_recent,
    search_messages,
    fetch_unread,
    send_message,
    edit_message,
    delete_messages,
    forward_messages,
    mark_read,
)


class TestGetChatType:
    """Tests for chat type detection."""

    def test_user_is_private(self):
        """User entity returns 'private'."""
        from telethon.tl.types import User
        user = MagicMock(spec=User)
        assert get_chat_type(user) == "private"

    def test_chat_is_group(self):
        """Chat entity returns 'group'."""
        from telethon.tl.types import Chat
        chat = MagicMock(spec=Chat)
        assert get_chat_type(chat) == "group"

    def test_channel_is_channel(self):
        """Channel entity returns 'channel'."""
        from telethon.tl.types import Channel
        channel = MagicMock(spec=Channel)
        assert get_chat_type(channel) == "channel"

    def test_unknown_entity(self):
        """Unknown entity returns 'unknown'."""
        assert get_chat_type(MagicMock()) == "unknown"


class TestFormatMessage:
    """Tests for message formatting."""

    def test_basic_message(self):
        """Formats basic text message."""
        msg = MagicMock()
        msg.id = 123
        msg.text = "Hello world"
        msg.date = datetime(2024, 1, 15, 10, 30)
        msg.media = None
        msg.sender = MagicMock(first_name="John", last_name="Doe")
        msg.reactions = None
        msg.reply_to = None

        result = format_message(msg, "Test Chat", "private")

        assert result["id"] == 123
        assert result["text"] == "Hello world"
        assert result["sender"] == "John Doe"
        assert result["chat"] == "Test Chat"
        assert result["chat_type"] == "private"
        assert not result["has_media"]

    def test_message_with_media(self):
        """Formats message with media attachment."""
        msg = MagicMock()
        msg.id = 456
        msg.text = ""
        msg.date = datetime(2024, 1, 15)
        msg.media = MagicMock()
        type(msg.media).__name__ = "MessageMediaPhoto"
        msg.sender = MagicMock(first_name="Jane", last_name=None)
        msg.reactions = None
        msg.reply_to = None

        result = format_message(msg, "Photos", "channel")

        assert result["has_media"]
        assert result["media_type"] == "MessageMediaPhoto"

    def test_message_with_reactions(self):
        """Formats message with reactions."""
        msg = MagicMock()
        msg.id = 789
        msg.text = "Popular post"
        msg.date = datetime(2024, 1, 15)
        msg.media = None
        msg.sender = MagicMock(title="Group Name")
        msg.sender.first_name = None

        reaction = MagicMock()
        reaction.reaction = MagicMock(emoticon="👍")
        reaction.count = 5
        msg.reactions = MagicMock(results=[reaction])
        msg.reply_to = None

        result = format_message(msg, "Group", "group")

        assert "reactions" in result
        assert result["reactions"][0]["emoji"] == "👍"
        assert result["reactions"][0]["count"] == 5

    def test_message_with_reply(self):
        """Formats message that is a reply."""
        msg = MagicMock()
        msg.id = 100
        msg.text = "This is a reply"
        msg.date = datetime(2024, 1, 15)
        msg.media = None
        msg.sender = MagicMock(first_name="User", last_name=None)
        msg.reactions = None
        msg.reply_to = MagicMock(reply_to_msg_id=50)

        result = format_message(msg, "Chat", "private")

        assert result["reply_to_msg_id"] == 50

    def test_include_chat_id(self):
        """Includes chat_id when requested."""
        msg = MagicMock()
        msg.id = 111
        msg.text = "Test"
        msg.date = datetime(2024, 1, 15)
        msg.media = None
        msg.sender = MagicMock(first_name="User", last_name=None)
        msg.reactions = None
        msg.reply_to = None
        msg.chat_id = 999

        result = format_message(msg, "Chat", "private", include_chat_id=True)

        assert result["chat_id"] == 999


class TestResolveEntity:
    """Tests for entity resolution."""

    async def test_resolve_username(self):
        """Resolves @username to entity."""
        client = AsyncMock()
        entity = MagicMock(first_name="John", last_name="Doe")
        client.get_entity = AsyncMock(return_value=entity)

        result_entity, name = await resolve_entity(client, "@johndoe")

        assert result_entity == entity
        assert name == "John Doe"

    async def test_resolve_numeric_id(self):
        """Resolves numeric chat ID."""
        client = AsyncMock()
        entity = MagicMock(first_name="Channel", title=None)
        entity.first_name = "Channel"
        client.get_entity = AsyncMock(return_value=entity)

        result_entity, name = await resolve_entity(client, "123456789")

        assert result_entity == entity
        client.get_entity.assert_called_with(123456789)

    async def test_resolve_by_dialog_search(self):
        """Resolves by searching dialogs."""
        client = AsyncMock()
        client.get_entity = AsyncMock(side_effect=Exception("Not found"))

        dialog = MagicMock()
        dialog.name = "My Test Chat"
        dialog.entity = MagicMock()
        client.get_dialogs = AsyncMock(return_value=[dialog])

        result_entity, name = await resolve_entity(client, "test chat")

        assert result_entity == dialog.entity
        assert name == "My Test Chat"

    async def test_resolve_not_found(self):
        """Returns None when chat not found."""
        client = AsyncMock()
        client.get_entity = AsyncMock(side_effect=Exception("Not found"))
        client.get_dialogs = AsyncMock(return_value=[])

        result_entity, name = await resolve_entity(client, "nonexistent")

        assert result_entity is None


class TestListChats:
    """Tests for chat listing."""

    async def test_list_all_chats(self):
        """Lists all available chats."""
        from telethon.tl.types import User, Channel

        client = AsyncMock()

        # Use spec_set with explicit name attribute (name is special in MagicMock)
        dialog1 = MagicMock()
        dialog1.configure_mock(id=1, name="Chat One", unread_count=5, date=datetime(2024, 1, 15))
        dialog1.entity = MagicMock(spec=User)

        dialog2 = MagicMock()
        dialog2.configure_mock(id=2, name="Chat Two", unread_count=0, date=datetime(2024, 1, 14))
        dialog2.entity = MagicMock(spec=Channel)

        client.get_dialogs = AsyncMock(return_value=[dialog1, dialog2])

        result = await list_chats(client, limit=30)

        assert len(result) == 2
        assert result[0]["name"] == "Chat One"
        assert result[0]["unread"] == 5
        assert result[0]["type"] == "private"
        assert result[1]["type"] == "channel"

    async def test_list_chats_with_search(self):
        """Filters chats by search term."""
        from telethon.tl.types import User

        client = AsyncMock()

        dialog1 = MagicMock()
        dialog1.configure_mock(id=1, name="Work Chat", unread_count=0, date=datetime(2024, 1, 15))
        dialog1.entity = MagicMock(spec=User)

        dialog2 = MagicMock()
        dialog2.configure_mock(id=2, name="Family", unread_count=0, date=datetime(2024, 1, 14))
        dialog2.entity = MagicMock(spec=User)

        client.get_dialogs = AsyncMock(return_value=[dialog1, dialog2])

        result = await list_chats(client, search="work")

        assert len(result) == 1
        assert result[0]["name"] == "Work Chat"


class TestSendMessage:
    """Tests for message sending."""

    async def test_send_to_private_chat(self):
        """Sends message to private chat."""
        client = AsyncMock()
        entity = MagicMock()

        with patch('telegram_telethon.modules.messages.resolve_entity',
                   return_value=(entity, "John Doe")):
            with patch('telegram_telethon.modules.messages.get_chat_type',
                       return_value="private"):
                msg = MagicMock(id=123)
                client.send_message = AsyncMock(return_value=msg)

                result = await send_message(client, "John", "Hello!")

        assert result["sent"]
        assert result["message_id"] == 123

    async def test_send_to_group_requires_whitelist(self):
        """Sending to group requires whitelist."""
        client = AsyncMock()
        entity = MagicMock(id=999)

        with patch('telegram_telethon.modules.messages.resolve_entity',
                   return_value=(entity, "Test Group")):
            with patch('telegram_telethon.modules.messages.get_chat_type',
                       return_value="group"):
                result = await send_message(client, "Test Group", "Hello!")

        assert not result["sent"]
        assert "whitelist" in result["error"].lower()

    async def test_send_to_whitelisted_group(self):
        """Sends to whitelisted group."""
        client = AsyncMock()
        entity = MagicMock(id=999)

        with patch('telegram_telethon.modules.messages.resolve_entity',
                   return_value=(entity, "Test Group")):
            with patch('telegram_telethon.modules.messages.get_chat_type',
                       return_value="group"):
                msg = MagicMock(id=456)
                client.send_message = AsyncMock(return_value=msg)

                result = await send_message(
                    client, "Test Group", "Hello!",
                    allowed_groups=["Test Group"]
                )

        assert result["sent"]

    async def test_send_chat_not_found(self):
        """Returns error when chat not found."""
        client = AsyncMock()

        with patch('telegram_telethon.modules.messages.resolve_entity',
                   return_value=(None, "Unknown")):
            result = await send_message(client, "Unknown", "Hello!")

        assert not result["sent"]
        assert "not found" in result["error"]


class TestEditMessage:
    """Tests for message editing."""

    async def test_edit_success(self):
        """Edits message successfully."""
        client = AsyncMock()
        entity = MagicMock()
        client.edit_message = AsyncMock()

        with patch('telegram_telethon.modules.messages.resolve_entity',
                   return_value=(entity, "Chat")):
            result = await edit_message(client, "Chat", 123, "Updated text")

        assert result["edited"]
        assert result["message_id"] == 123

    async def test_edit_not_found(self):
        """Returns error when chat not found."""
        client = AsyncMock()

        with patch('telegram_telethon.modules.messages.resolve_entity',
                   return_value=(None, "Unknown")):
            result = await edit_message(client, "Unknown", 123, "Text")

        assert not result["edited"]


class TestDeleteMessages:
    """Tests for message deletion."""

    async def test_delete_success(self):
        """Deletes messages successfully."""
        client = AsyncMock()
        entity = MagicMock()
        client.delete_messages = AsyncMock()

        with patch('telegram_telethon.modules.messages.resolve_entity',
                   return_value=(entity, "Chat")):
            result = await delete_messages(client, "Chat", [1, 2, 3])

        assert result["deleted"]
        assert result["message_ids"] == [1, 2, 3]


class TestForwardMessages:
    """Tests for message forwarding."""

    async def test_forward_success(self):
        """Forwards messages successfully."""
        client = AsyncMock()
        from_entity = MagicMock()
        to_entity = MagicMock()
        client.forward_messages = AsyncMock()

        with patch('telegram_telethon.modules.messages.resolve_entity',
                   side_effect=[(from_entity, "Source"), (to_entity, "Dest")]):
            result = await forward_messages(client, "Source", "Dest", [1, 2])

        assert result["forwarded"]
        assert result["message_count"] == 2

    async def test_forward_source_not_found(self):
        """Returns error when source not found."""
        client = AsyncMock()

        with patch('telegram_telethon.modules.messages.resolve_entity',
                   side_effect=[(None, "Unknown"), (MagicMock(), "Dest")]):
            result = await forward_messages(client, "Unknown", "Dest", [1])

        assert not result["forwarded"]


class TestMarkRead:
    """Tests for marking messages as read."""

    async def test_mark_read_success(self):
        """Marks messages as read."""
        client = AsyncMock()
        entity = MagicMock()
        client.send_read_acknowledge = AsyncMock()

        with patch('telegram_telethon.modules.messages.resolve_entity',
                   return_value=(entity, "Chat")):
            result = await mark_read(client, "Chat")

        assert result["marked"]
        client.send_read_acknowledge.assert_called_once()
