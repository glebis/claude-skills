"""Tests for draft message functionality."""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch


class TestSaveDraft:
    @pytest.mark.asyncio
    async def test_save_draft_success(self):
        client = AsyncMock()
        entity = MagicMock()

        # Mock iter_drafts to return empty (no existing draft)
        async def mock_iter_drafts(entities):
            return
            yield  # Make it an async generator

        client.iter_drafts = mock_iter_drafts

        with patch('telegram_telethon.modules.messages.resolve_entity',
                   return_value=(entity, "Test Chat")):
            from telegram_telethon.modules.messages import save_draft
            result = await save_draft(client, "Test Chat", "Hello draft")

            assert result["saved"] is True
            assert result["chat"] == "Test Chat"

    @pytest.mark.asyncio
    async def test_save_draft_exceeds_length(self):
        client = AsyncMock()
        entity = MagicMock()

        # Mock iter_drafts to return empty (no existing draft)
        async def mock_iter_drafts(entities):
            return
            yield  # Make it an async generator

        client.iter_drafts = mock_iter_drafts

        with patch('telegram_telethon.modules.messages.resolve_entity',
                   return_value=(entity, "Test Chat")):
            from telegram_telethon.modules.messages import save_draft
            long_text = "x" * 5000
            result = await save_draft(client, "Test Chat", long_text)

            assert result["saved"] is False
            assert "exceeds" in result["error"]

    @pytest.mark.asyncio
    async def test_save_empty_clears_draft(self):
        client = AsyncMock()
        entity = MagicMock()

        with patch('telegram_telethon.modules.messages.resolve_entity',
                   return_value=(entity, "Test Chat")):
            from telegram_telethon.modules.messages import save_draft
            result = await save_draft(client, "Test Chat", "")

            assert result["saved"] is True
            assert result["cleared"] is True

    @pytest.mark.asyncio
    async def test_save_draft_chat_not_found(self):
        client = AsyncMock()

        with patch('telegram_telethon.modules.messages.resolve_entity',
                   return_value=(None, None)):
            from telegram_telethon.modules.messages import save_draft
            result = await save_draft(client, "Unknown Chat", "text")

            assert result["saved"] is False
            assert "not found" in result["error"]


class TestGetAllDrafts:
    @pytest.mark.asyncio
    async def test_get_all_drafts_empty(self):
        client = AsyncMock()

        async def mock_iter_drafts():
            return
            yield  # Make it an async generator

        client.iter_drafts = mock_iter_drafts

        from telegram_telethon.modules.messages import get_all_drafts
        result = await get_all_drafts(client)

        assert result == []


class TestClearAllDrafts:
    @pytest.mark.asyncio
    async def test_clear_all_drafts(self):
        client = AsyncMock()

        from telegram_telethon.modules.messages import clear_all_drafts
        result = await clear_all_drafts(client)

        assert result["cleared"] is True
        assert result["all"] is True


class TestSendDraft:
    @pytest.mark.asyncio
    async def test_send_draft_blocked_without_whitelist(self):
        client = AsyncMock()
        entity = MagicMock()

        with patch('telegram_telethon.modules.messages.resolve_entity',
                   return_value=(entity, "Test Group")), \
             patch('telegram_telethon.modules.messages.get_chat_type',
                   return_value="group"):
            from telegram_telethon.modules.messages import send_draft
            result = await send_draft(client, "Test Group", allowed_groups=[])

            assert result["sent"] is False
            assert "whitelist" in result["error"]

    @pytest.mark.asyncio
    async def test_send_draft_allowed_with_whitelist(self):
        client = AsyncMock()
        entity = MagicMock()

        mock_draft = MagicMock()
        mock_draft.is_empty = False
        mock_draft.raw_text = "Draft text"
        mock_draft.delete = AsyncMock()
        mock_msg = MagicMock(id=456)
        client.send_message = AsyncMock(return_value=mock_msg)

        async def mock_iter_drafts(entities):
            yield mock_draft

        client.iter_drafts = mock_iter_drafts

        with patch('telegram_telethon.modules.messages.resolve_entity',
                   return_value=(entity, "Test Group")), \
             patch('telegram_telethon.modules.messages.get_chat_type',
                   return_value="group"):
            from telegram_telethon.modules.messages import send_draft
            result = await send_draft(client, "Test Group", allowed_groups=["Test Group"])

            assert result["sent"] is True
            assert result["message_id"] == 456

    @pytest.mark.asyncio
    async def test_send_draft_no_draft_found(self):
        client = AsyncMock()
        entity = MagicMock()

        async def mock_iter_drafts(entities):
            return
            yield  # Make it an async generator

        client.iter_drafts = mock_iter_drafts

        with patch('telegram_telethon.modules.messages.resolve_entity',
                   return_value=(entity, "Test Chat")), \
             patch('telegram_telethon.modules.messages.get_chat_type',
                   return_value="private"):
            from telegram_telethon.modules.messages import send_draft
            result = await send_draft(client, "Test Chat")

            assert result["sent"] is False
            assert "No draft found" in result["error"]

    @pytest.mark.asyncio
    async def test_send_draft_private_chat_no_whitelist_needed(self):
        client = AsyncMock()
        entity = MagicMock()

        mock_draft = MagicMock()
        mock_draft.is_empty = False
        mock_draft.raw_text = "Private draft"
        mock_draft.delete = AsyncMock()
        mock_msg = MagicMock(id=789)
        client.send_message = AsyncMock(return_value=mock_msg)

        async def mock_iter_drafts(entities):
            yield mock_draft

        client.iter_drafts = mock_iter_drafts

        with patch('telegram_telethon.modules.messages.resolve_entity',
                   return_value=(entity, "Private User")), \
             patch('telegram_telethon.modules.messages.get_chat_type',
                   return_value="private"):
            from telegram_telethon.modules.messages import send_draft
            # No allowed_groups needed for private chats
            result = await send_draft(client, "Private User", allowed_groups=[])

            assert result["sent"] is True
            assert result["message_id"] == 789
