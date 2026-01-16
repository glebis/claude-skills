"""Tests for daemon event handlers."""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import re

from telegram_telethon.daemon.handlers import (
    EventRouter,
    MessageHandler,
    ActionResult,
)
from telegram_telethon.core.config import TriggerConfig, DaemonConfig


class TestEventRouter:
    """Tests for event routing logic."""

    @pytest.fixture
    def router(self):
        """Create router with sample triggers."""
        triggers = [
            TriggerConfig(
                chat="@testuser",
                pattern=r"^/claude (.+)$",
                action="claude",
                reply_mode="inline",
            ),
            TriggerConfig(
                chat="Test Group",
                pattern=r"@Bot (.+)$",
                action="claude",
                reply_mode="new",
            ),
            TriggerConfig(
                chat="*",
                pattern=r"^/ping$",
                action="reply",
                reply_text="pong",
            ),
        ]
        return EventRouter(triggers=triggers)

    def test_match_specific_chat(self, router):
        """Matches trigger for specific chat."""
        result = router.match(
            chat_name="@testuser",
            message_text="/claude do something",
        )
        assert result is not None
        assert result.trigger.action == "claude"
        assert result.captured_text == "do something"

    def test_match_group_chat(self, router):
        """Matches trigger for group chat."""
        result = router.match(
            chat_name="Test Group",
            message_text="@Bot analyze this",
        )
        assert result is not None
        assert result.trigger.reply_mode == "new"
        assert result.captured_text == "analyze this"

    def test_match_wildcard(self, router):
        """Wildcard matches any chat."""
        result = router.match(
            chat_name="Random Chat",
            message_text="/ping",
        )
        assert result is not None
        assert result.trigger.action == "reply"

    def test_no_match(self, router):
        """Returns None when no trigger matches."""
        result = router.match(
            chat_name="Unknown Chat",
            message_text="hello world",
        )
        assert result is None

    def test_first_match_wins(self, router):
        """First matching trigger is used."""
        # Add overlapping trigger
        router.triggers.insert(0, TriggerConfig(
            chat="*",
            pattern=r"^/claude",
            action="ignore",
        ))

        result = router.match(
            chat_name="@testuser",
            message_text="/claude test",
        )
        # First trigger (ignore) should win
        assert result.trigger.action == "ignore"

    def test_case_insensitive_chat_match(self, router):
        """Chat name matching is case insensitive."""
        result = router.match(
            chat_name="TEST GROUP",
            message_text="@Bot test",
        )
        assert result is not None


class TestMessageHandler:
    """Tests for message handling logic."""

    @pytest.fixture
    def handler(self):
        """Create message handler with mock bridge."""
        mock_bridge = AsyncMock()
        mock_bridge.send = AsyncMock(return_value=MagicMock(
            success=True,
            result="Claude response",
            session_id="sess-123",
        ))
        return MessageHandler(claude_bridge=mock_bridge)

    async def test_handle_claude_action(self, handler):
        """Claude action sends to bridge and returns response."""
        trigger = TriggerConfig(
            chat="*",
            pattern=".*",
            action="claude",
        )
        result = await handler.handle(
            trigger=trigger,
            chat_id=123,
            message_text="test prompt",
            captured_text="test prompt",
        )

        assert result.success
        assert result.response == "Claude response"
        handler.claude_bridge.send.assert_called_once_with(
            "test prompt",
            chat_id=123,
        )

    async def test_handle_reply_action(self, handler):
        """Reply action returns configured text."""
        trigger = TriggerConfig(
            chat="*",
            pattern=".*",
            action="reply",
            reply_text="pong",
        )
        result = await handler.handle(
            trigger=trigger,
            chat_id=123,
            message_text="/ping",
            captured_text=None,
        )

        assert result.success
        assert result.response == "pong"

    async def test_handle_ignore_action(self, handler):
        """Ignore action returns no response."""
        trigger = TriggerConfig(
            chat="*",
            pattern=".*",
            action="ignore",
        )
        result = await handler.handle(
            trigger=trigger,
            chat_id=123,
            message_text="ignored",
            captured_text=None,
        )

        assert result.success
        assert result.response is None
        assert result.should_reply is False

    async def test_handle_claude_failure(self, handler):
        """Handles Claude bridge failure."""
        handler.claude_bridge.send = AsyncMock(return_value=MagicMock(
            success=False,
            error="Claude unavailable",
        ))

        trigger = TriggerConfig(
            chat="*",
            pattern=".*",
            action="claude",
        )
        result = await handler.handle(
            trigger=trigger,
            chat_id=123,
            message_text="test",
            captured_text="test",
        )

        assert not result.success
        assert "unavailable" in result.error.lower()

    async def test_reply_mode_inline(self, handler):
        """Inline reply mode sets reply_to_message_id."""
        trigger = TriggerConfig(
            chat="*",
            pattern=".*",
            action="claude",
            reply_mode="inline",
        )
        result = await handler.handle(
            trigger=trigger,
            chat_id=123,
            message_id=456,
            message_text="test",
            captured_text="test",
        )

        assert result.reply_to_message_id == 456

    async def test_reply_mode_new(self, handler):
        """New reply mode doesn't set reply_to_message_id."""
        trigger = TriggerConfig(
            chat="*",
            pattern=".*",
            action="claude",
            reply_mode="new",
        )
        result = await handler.handle(
            trigger=trigger,
            chat_id=123,
            message_id=456,
            message_text="test",
            captured_text="test",
        )

        assert result.reply_to_message_id is None


class TestActionResult:
    """Tests for action result model."""

    def test_success_result(self):
        """Success result has response."""
        result = ActionResult(
            success=True,
            response="Hello",
            should_reply=True,
        )
        assert result.success
        assert result.response == "Hello"

    def test_failure_result(self):
        """Failure result has error."""
        result = ActionResult(
            success=False,
            error="Something went wrong",
        )
        assert not result.success
        assert result.error == "Something went wrong"
        assert result.should_reply is False  # Don't reply on error by default

    def test_reply_context(self):
        """Result can include reply context."""
        result = ActionResult(
            success=True,
            response="OK",
            should_reply=True,
            reply_to_message_id=123,
        )
        assert result.reply_to_message_id == 123
