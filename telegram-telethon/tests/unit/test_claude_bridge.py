"""Tests for Claude Code integration bridge."""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import json
import asyncio
from pathlib import Path

from telegram_telethon.daemon.claude_bridge import (
    ClaudeBridge,
    ClaudeSession,
    ClaudeResponse,
    ClaudeError,
)
from telegram_telethon.core.config import ClaudeConfig


class TestClaudeSession:
    """Tests for Claude session persistence."""

    def test_session_creation(self):
        """Session stores chat_id and session_id."""
        session = ClaudeSession(chat_id=123, session_id="abc-123")
        assert session.chat_id == 123
        assert session.session_id == "abc-123"
        assert session.message_count == 0

    def test_session_increment(self):
        """Session tracks message count."""
        session = ClaudeSession(chat_id=123, session_id="abc-123")
        session.increment()
        assert session.message_count == 1
        session.increment()
        assert session.message_count == 2

    def test_session_serialization(self):
        """Session serializes to dict for persistence."""
        session = ClaudeSession(
            chat_id=123,
            session_id="abc-123",
            message_count=5,
        )
        data = session.to_dict()
        assert data["chat_id"] == 123
        assert data["session_id"] == "abc-123"
        assert data["message_count"] == 5

    def test_session_deserialization(self):
        """Session loads from dict."""
        data = {"chat_id": 123, "session_id": "abc-123", "message_count": 5}
        session = ClaudeSession.from_dict(data)
        assert session.chat_id == 123
        assert session.session_id == "abc-123"
        assert session.message_count == 5


class TestClaudeResponse:
    """Tests for Claude response parsing."""

    def test_parse_success_response(self):
        """Parses successful JSON response."""
        raw = '{"result": "Hello world", "session_id": "sess-123"}'
        response = ClaudeResponse.parse(raw)
        assert response.result == "Hello world"
        assert response.session_id == "sess-123"
        assert response.success

    def test_parse_error_response(self):
        """Handles error in response."""
        raw = '{"error": "Something went wrong"}'
        response = ClaudeResponse.parse(raw)
        assert not response.success
        assert "Something went wrong" in response.error

    def test_parse_invalid_json(self):
        """Handles invalid JSON gracefully."""
        raw = "not valid json"
        response = ClaudeResponse.parse(raw)
        assert not response.success
        assert "parse" in response.error.lower() or "json" in response.error.lower()

    def test_truncate_long_result(self):
        """Long results can be truncated for display."""
        response = ClaudeResponse(
            result="x" * 5000,
            session_id="sess-123",
            success=True,
        )
        truncated = response.truncated(max_length=100)
        assert len(truncated) <= 103  # 100 + "..."
        assert truncated.endswith("...")


class TestClaudeBridge:
    """Tests for Claude bridge main functionality."""

    @pytest.fixture
    def bridge(self, temp_config_dir):
        """Create ClaudeBridge with temp persistence."""
        config = ClaudeConfig(
            allowed_tools=["Read", "Edit"],
            max_turns=5,
            timeout=60,
        )
        return ClaudeBridge(
            config=config,
            sessions_file=temp_config_dir / "sessions.json",
        )

    async def test_new_session_created(self, bridge, mock_subprocess):
        """First message to chat creates new session."""
        with patch("asyncio.create_subprocess_exec") as mock_exec:
            mock_exec.return_value = mock_subprocess

            result = await bridge.send("Test prompt", chat_id=123)

            assert result.success
            assert result.session_id == "test-session-123"
            assert 123 in bridge.sessions
            assert bridge.sessions[123].session_id == "test-session-123"

    async def test_existing_session_resumed(self, bridge, mock_subprocess):
        """Subsequent messages resume existing session."""
        # Pre-populate session
        bridge.sessions[123] = ClaudeSession(
            chat_id=123,
            session_id="existing-session",
        )

        with patch("asyncio.create_subprocess_exec") as mock_exec:
            mock_exec.return_value = mock_subprocess

            await bridge.send("Follow up", chat_id=123)

            # Check --resume was passed
            call_args = mock_exec.call_args[0]
            assert "--resume" in call_args
            assert "existing-session" in call_args

    async def test_cli_args_built_correctly(self, bridge, mock_subprocess):
        """Claude CLI called with correct arguments."""
        with patch("asyncio.create_subprocess_exec") as mock_exec:
            mock_exec.return_value = mock_subprocess

            await bridge.send("Test prompt", chat_id=123)

            call_args = mock_exec.call_args[0]
            assert "claude" in call_args
            assert "-p" in call_args
            assert "Test prompt" in call_args
            assert "--output-format" in call_args
            assert "json" in call_args
            assert "--allowedTools" in call_args
            assert "--max-turns" in call_args

    async def test_timeout_handling(self, bridge):
        """Handles Claude timeout gracefully."""
        async def slow_communicate():
            await asyncio.sleep(10)
            return (b'{}', b'')

        with patch("asyncio.create_subprocess_exec") as mock_exec:
            mock_process = MagicMock()
            mock_process.communicate = slow_communicate
            mock_exec.return_value = mock_process

            # Set short timeout
            bridge.config.timeout = 0.1

            result = await bridge.send("Test", chat_id=123)
            assert not result.success
            assert "timeout" in result.error.lower()

    async def test_sessions_persist_to_file(self, bridge, mock_subprocess, temp_config_dir):
        """Sessions are saved to disk."""
        with patch("asyncio.create_subprocess_exec") as mock_exec:
            mock_exec.return_value = mock_subprocess

            await bridge.send("Test", chat_id=123)
            await bridge.save_sessions()

            # Verify file written
            sessions_file = temp_config_dir / "sessions.json"
            assert sessions_file.exists()

            data = json.loads(sessions_file.read_text())
            assert "123" in data or 123 in data

    async def test_sessions_load_from_file(self, temp_config_dir):
        """Sessions are loaded on startup."""
        sessions_file = temp_config_dir / "sessions.json"
        sessions_file.write_text(json.dumps({
            "123": {
                "chat_id": 123,
                "session_id": "persisted-session",
                "message_count": 10,
            }
        }))

        config = ClaudeConfig()
        bridge = ClaudeBridge(config=config, sessions_file=sessions_file)
        await bridge.load_sessions()

        assert 123 in bridge.sessions
        assert bridge.sessions[123].session_id == "persisted-session"
        assert bridge.sessions[123].message_count == 10

    async def test_clear_session(self, bridge, mock_subprocess):
        """Can clear session for fresh start."""
        bridge.sessions[123] = ClaudeSession(chat_id=123, session_id="old")

        bridge.clear_session(123)
        assert 123 not in bridge.sessions

    async def test_subprocess_error_handling(self, bridge):
        """Handles subprocess errors gracefully."""
        with patch("asyncio.create_subprocess_exec") as mock_exec:
            mock_exec.side_effect = OSError("Command not found")

            result = await bridge.send("Test", chat_id=123)
            assert not result.success
            assert "failed" in result.error.lower() or "error" in result.error.lower()


class TestClaudeBridgeQueue:
    """Tests for request queuing."""

    @pytest.fixture
    def bridge_with_queue(self, temp_config_dir):
        """Bridge with queue enabled."""
        config = ClaudeConfig(max_turns=5)
        return ClaudeBridge(
            config=config,
            sessions_file=temp_config_dir / "sessions.json",
            max_concurrent=1,
        )

    async def test_sequential_processing(self, bridge_with_queue, mock_subprocess):
        """Requests are processed sequentially."""
        call_order = []

        async def track_calls():
            call_order.append(len(call_order))
            await asyncio.sleep(0.1)
            return (
                b'{"result": "ok", "session_id": "sess"}',
                b''
            )

        with patch("asyncio.create_subprocess_exec") as mock_exec:
            mock_process = MagicMock()
            mock_process.communicate = track_calls
            mock_process.returncode = 0
            mock_exec.return_value = mock_process

            # Queue multiple requests
            tasks = [
                bridge_with_queue.send("A", chat_id=1),
                bridge_with_queue.send("B", chat_id=2),
                bridge_with_queue.send("C", chat_id=3),
            ]
            await asyncio.gather(*tasks)

            # All should complete
            assert len(call_order) == 3

    async def test_queue_size_limit(self, bridge_with_queue):
        """Queue rejects when full."""
        bridge_with_queue.max_queue_size = 2

        # Fill the queue
        bridge_with_queue._queue_size = 2

        result = await bridge_with_queue.send("Test", chat_id=999)
        assert not result.success
        assert "queue" in result.error.lower() or "busy" in result.error.lower()
