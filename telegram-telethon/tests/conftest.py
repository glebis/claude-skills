"""Pytest configuration and shared fixtures."""
import pytest
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock
import tempfile
import shutil


@pytest.fixture
def temp_config_dir():
    """Create a temporary config directory."""
    tmp = tempfile.mkdtemp(prefix="tg_test_")
    yield Path(tmp)
    shutil.rmtree(tmp, ignore_errors=True)


@pytest.fixture
def sample_config():
    """Sample configuration dict."""
    return {
        "api_id": 12345678,
        "api_hash": "a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4",  # 32 hex chars
        "phone": "+1234567890",
    }


@pytest.fixture
def sample_daemon_config():
    """Sample daemon configuration."""
    return {
        "triggers": [
            {
                "chat": "@testuser",
                "pattern": r"^/claude (.+)",
                "action": "claude",
                "reply_mode": "inline",
            },
            {
                "chat": "Test Group",
                "pattern": r"@Bot (.+)",
                "action": "claude",
                "reply_mode": "new",
            },
        ],
        "claude": {
            "allowed_tools": ["Read", "Edit", "Bash"],
            "max_turns": 10,
            "timeout": 300,
        },
        "queue": {
            "max_concurrent": 1,
            "timeout": 600,
        },
    }


@pytest.fixture
def mock_telegram_client():
    """Mock TelegramClient for unit tests."""
    client = MagicMock()
    client.start = AsyncMock()
    client.disconnect = AsyncMock()
    client.is_connected = MagicMock(return_value=True)
    client.get_me = AsyncMock(return_value=MagicMock(
        first_name="Test",
        last_name="User",
        username="testuser",
        phone="+1234567890"
    ))
    client.get_dialogs = AsyncMock(return_value=[])
    client.iter_messages = MagicMock(return_value=AsyncMock())
    client.send_message = AsyncMock()
    client.run_until_disconnected = AsyncMock()
    return client


@pytest.fixture
def mock_subprocess():
    """Mock for subprocess calls to Claude CLI."""
    async def mock_communicate():
        return (
            b'{"result": "Test response", "session_id": "test-session-123"}',
            b''
        )

    process = MagicMock()
    process.communicate = mock_communicate
    process.returncode = 0
    return process
