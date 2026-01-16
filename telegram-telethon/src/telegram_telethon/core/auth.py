"""Authentication module for Telegram API.

Provides interactive setup wizard and connection verification.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional, Any

from telethon import TelegramClient
from telethon.errors import SessionPasswordNeededError

from .config import Config, DEFAULT_CONFIG_DIR


class AuthError(Exception):
    """Authentication error."""
    pass


@dataclass
class AuthStatus:
    """Authentication status information."""

    state: str  # "not_configured", "credentials_only", "ready"
    config_dir: Path
    has_api_id: bool = False
    has_api_hash: bool = False
    has_session: bool = False
    username: Optional[str] = None
    error: Optional[str] = None

    @property
    def is_ready(self) -> bool:
        """Check if ready to connect."""
        return self.state == "ready"

    @classmethod
    def check(cls, config_dir: Path = DEFAULT_CONFIG_DIR) -> AuthStatus:
        """Check current authentication status."""
        config_path = config_dir / "config.yaml"
        session_path = config_dir / "session.session"

        if not config_path.exists():
            return cls(
                state="not_configured",
                config_dir=config_dir,
            )

        config = Config.load(config_path)

        if not config.is_configured():
            return cls(
                state="not_configured",
                config_dir=config_dir,
                has_api_id=config.api_id is not None,
                has_api_hash=config.api_hash is not None,
            )

        if not session_path.exists():
            return cls(
                state="credentials_only",
                config_dir=config_dir,
                has_api_id=True,
                has_api_hash=True,
            )

        return cls(
            state="ready",
            config_dir=config_dir,
            has_api_id=True,
            has_api_hash=True,
            has_session=True,
        )


class AuthWizard:
    """Interactive authentication wizard."""

    def __init__(self, config_dir: Path = DEFAULT_CONFIG_DIR):
        self.config_dir = config_dir
        self.config = Config(config_dir=config_dir)
        self._client: Optional[TelegramClient] = None
        self._phone_code_hash: Optional[str] = None

    def validate_api_id(self, value: str) -> bool:
        """Validate API ID format."""
        if not value:
            return False
        return value.isdigit()

    def validate_api_hash(self, value: str) -> bool:
        """Validate API hash format (32 hex characters)."""
        if not value or len(value) != 32:
            return False
        return all(c in "0123456789abcdef" for c in value.lower())

    def validate_phone(self, value: str) -> bool:
        """Validate phone number format."""
        if not value or not value.startswith("+"):
            return False
        # Remove spaces and check length
        digits = re.sub(r"\s+", "", value[1:])
        return len(digits) >= 7 and digits.isdigit()

    def set_credentials(self, api_id: str, api_hash: str) -> None:
        """Set API credentials."""
        self.config.api_id = int(api_id)
        self.config.api_hash = api_hash

    def set_phone(self, phone: str) -> None:
        """Set phone number."""
        self.config.phone = phone

    async def send_code(self) -> str:
        """Send authentication code to phone.

        Returns:
            phone_code_hash for sign_in
        """
        if not self.config.is_configured():
            raise AuthError("API credentials not set")

        self.config_dir.mkdir(parents=True, exist_ok=True)
        session_path = self.config_dir / "session"

        self._client = TelegramClient(
            str(session_path),
            self.config.api_id,
            self.config.api_hash,
        )

        await self._client.connect()

        result = await self._client.send_code_request(self.config.phone)
        self._phone_code_hash = result.phone_code_hash

        return self._phone_code_hash

    async def sign_in(self, code: str) -> Any:
        """Sign in with code.

        Args:
            code: SMS code received

        Returns:
            User object on success

        Raises:
            AuthError: If 2FA is required or sign-in fails
        """
        if not self._client or not self._phone_code_hash:
            raise AuthError("Must call send_code first")

        try:
            user = await self._client.sign_in(
                phone=self.config.phone,
                code=code,
                phone_code_hash=self._phone_code_hash,
            )
            # Save config on success
            self.config.save()
            return user
        except SessionPasswordNeededError:
            raise AuthError("2FA required - call sign_in_2fa with password")

    async def sign_in_2fa(self, password: str) -> Any:
        """Complete sign in with 2FA password.

        Args:
            password: 2FA password

        Returns:
            User object on success
        """
        if not self._client:
            raise AuthError("Must call send_code first")

        user = await self._client.sign_in(password=password)
        # Save config on success
        self.config.save()
        return user

    async def disconnect(self) -> None:
        """Disconnect client."""
        if self._client:
            await self._client.disconnect()
            self._client = None


async def verify_connection(config_dir: Path = DEFAULT_CONFIG_DIR) -> dict:
    """Verify Telegram connection.

    Returns:
        Dict with connection status and user info
    """
    config_path = config_dir / "config.yaml"
    session_path = config_dir / "session"

    if not config_path.exists():
        return {
            "connected": False,
            "error": "Config not found",
        }

    config = Config.load(config_path)

    if not config.is_configured():
        return {
            "connected": False,
            "error": "API credentials not configured",
        }

    client = TelegramClient(
        str(session_path),
        config.api_id,
        config.api_hash,
    )

    try:
        await client.start()
        me = await client.get_me()

        return {
            "connected": True,
            "first_name": me.first_name,
            "last_name": me.last_name,
            "username": me.username,
            "phone": me.phone,
        }
    except Exception as e:
        return {
            "connected": False,
            "error": str(e),
        }
    finally:
        await client.disconnect()
