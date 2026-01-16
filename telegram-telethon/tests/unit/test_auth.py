"""Tests for authentication module."""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from pathlib import Path

from telegram_telethon.core.auth import (
    AuthWizard,
    AuthError,
    AuthStatus,
    verify_connection,
)


class TestAuthStatus:
    """Tests for authentication status checking."""

    def test_not_configured_status(self, temp_config_dir):
        """Returns NOT_CONFIGURED when no config exists."""
        status = AuthStatus.check(temp_config_dir)
        assert status.state == "not_configured"
        assert not status.is_ready

    def test_credentials_only_status(self, temp_config_dir, sample_config):
        """Returns CREDENTIALS_ONLY when config exists but no session."""
        import yaml
        config_path = temp_config_dir / "config.yaml"
        with open(config_path, "w") as f:
            yaml.dump(sample_config, f)

        status = AuthStatus.check(temp_config_dir)
        assert status.state == "credentials_only"
        assert not status.is_ready

    def test_ready_status(self, temp_config_dir, sample_config):
        """Returns READY when config and session exist."""
        import yaml
        config_path = temp_config_dir / "config.yaml"
        session_path = temp_config_dir / "session.session"

        with open(config_path, "w") as f:
            yaml.dump(sample_config, f)
        session_path.touch()

        status = AuthStatus.check(temp_config_dir)
        assert status.state == "ready"
        assert status.is_ready


class TestAuthWizard:
    """Tests for interactive authentication wizard."""

    @pytest.fixture
    def wizard(self, temp_config_dir):
        """Create AuthWizard with temp directory."""
        return AuthWizard(config_dir=temp_config_dir)

    def test_wizard_init(self, wizard, temp_config_dir):
        """Wizard initializes with config directory."""
        assert wizard.config_dir == temp_config_dir

    async def test_validate_api_id_numeric(self, wizard):
        """API ID must be numeric."""
        assert wizard.validate_api_id("12345678")
        assert not wizard.validate_api_id("abc")
        assert not wizard.validate_api_id("")

    async def test_validate_api_hash_format(self, wizard):
        """API hash must be 32 hex characters."""
        valid_hash = "a" * 32
        assert wizard.validate_api_hash(valid_hash)
        assert not wizard.validate_api_hash("tooshort")
        assert not wizard.validate_api_hash("x" * 32)  # non-hex

    async def test_validate_phone_format(self, wizard):
        """Phone must start with + and contain digits."""
        assert wizard.validate_phone("+1234567890")
        assert wizard.validate_phone("+44 123 456 7890")  # spaces ok
        assert not wizard.validate_phone("1234567890")  # no +
        assert not wizard.validate_phone("+")  # too short

    @patch("telegram_telethon.core.auth.TelegramClient")
    async def test_send_code_success(self, mock_client_class, wizard):
        """send_code calls Telegram API and returns phone_code_hash."""
        mock_client = AsyncMock()
        mock_client.send_code_request = AsyncMock(
            return_value=MagicMock(phone_code_hash="hash123")
        )
        mock_client_class.return_value = mock_client

        wizard.config.api_id = 12345678
        wizard.config.api_hash = "a" * 32
        wizard.config.phone = "+1234567890"

        result = await wizard.send_code()
        assert result == "hash123"
        mock_client.send_code_request.assert_called_once_with("+1234567890")

    @patch("telegram_telethon.core.auth.TelegramClient")
    async def test_sign_in_success(self, mock_client_class, wizard):
        """sign_in authenticates and saves session."""
        mock_client = AsyncMock()
        mock_client.sign_in = AsyncMock(
            return_value=MagicMock(first_name="Test", username="testuser")
        )
        mock_client_class.return_value = mock_client
        wizard._client = mock_client
        wizard._phone_code_hash = "hash123"
        wizard.config.phone = "+1234567890"

        user = await wizard.sign_in("12345")
        assert user.first_name == "Test"
        mock_client.sign_in.assert_called_once()

    @patch("telegram_telethon.core.auth.TelegramClient")
    async def test_sign_in_requires_2fa(self, mock_client_class, wizard):
        """sign_in raises Auth2FARequired when 2FA needed."""
        from telethon.errors import SessionPasswordNeededError

        mock_client = AsyncMock()
        # SessionPasswordNeededError requires a request param in newer Telethon
        mock_error = SessionPasswordNeededError(request=MagicMock())
        mock_client.sign_in = AsyncMock(side_effect=mock_error)
        mock_client_class.return_value = mock_client
        wizard._client = mock_client
        wizard._phone_code_hash = "hash123"
        wizard.config.phone = "+1234567890"

        with pytest.raises(AuthError, match="2FA"):
            await wizard.sign_in("12345")

    @patch("telegram_telethon.core.auth.TelegramClient")
    async def test_sign_in_2fa(self, mock_client_class, wizard):
        """sign_in_2fa completes authentication with password."""
        mock_client = AsyncMock()
        mock_client.sign_in = AsyncMock(
            return_value=MagicMock(first_name="Test", username="testuser")
        )
        mock_client_class.return_value = mock_client
        wizard._client = mock_client

        user = await wizard.sign_in_2fa("mypassword")
        assert user.first_name == "Test"
        mock_client.sign_in.assert_called_with(password="mypassword")


class TestVerifyConnection:
    """Tests for connection verification."""

    @patch("telegram_telethon.core.auth.TelegramClient")
    async def test_verify_success(self, mock_client_class, temp_config_dir, sample_config):
        """verify_connection returns user info on success."""
        import yaml
        config_path = temp_config_dir / "config.yaml"
        with open(config_path, "w") as f:
            yaml.dump(sample_config, f)

        mock_client = AsyncMock()
        mock_client.start = AsyncMock()
        mock_client.get_me = AsyncMock(
            return_value=MagicMock(
                first_name="Test",
                last_name="User",
                username="testuser",
            )
        )
        mock_client.disconnect = AsyncMock()
        mock_client_class.return_value = mock_client

        result = await verify_connection(temp_config_dir)
        assert result["connected"]
        assert result["username"] == "testuser"

    @patch("telegram_telethon.core.auth.TelegramClient")
    async def test_verify_failure(self, mock_client_class, temp_config_dir, sample_config):
        """verify_connection returns error on failure."""
        import yaml
        config_path = temp_config_dir / "config.yaml"
        with open(config_path, "w") as f:
            yaml.dump(sample_config, f)

        mock_client = AsyncMock()
        mock_client.start = AsyncMock(side_effect=Exception("Connection failed"))
        mock_client_class.return_value = mock_client

        result = await verify_connection(temp_config_dir)
        assert not result["connected"]
        assert "error" in result
