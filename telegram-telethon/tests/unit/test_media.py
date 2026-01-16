"""Tests for media module."""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from pathlib import Path
import tempfile
import os

from telegram_telethon.modules.media import (
    download_media,
    transcribe_voice,
    transcribe_batch,
    download_profile_photo,
    TranscriptResult,
    _detect_media_type,
)


class TestDetectMediaType:
    """Tests for media type detection."""

    def test_no_media(self):
        """Returns None for message without media."""
        msg = MagicMock()
        msg.media = None
        assert _detect_media_type(msg) is None

    def test_photo(self):
        """Detects photo media."""
        msg = MagicMock()
        msg.media = MagicMock()
        type(msg.media).__name__ = "MessageMediaPhoto"
        assert _detect_media_type(msg) == "photo"

    def test_voice_message(self):
        """Detects voice message."""
        msg = MagicMock()
        msg.media = MagicMock()
        type(msg.media).__name__ = "MessageMediaDocument"

        attr = MagicMock()
        type(attr).__name__ = "DocumentAttributeAudio"
        attr.voice = True

        msg.media.document = MagicMock()
        msg.media.document.attributes = [attr]

        assert _detect_media_type(msg) == "voice"

    def test_video(self):
        """Detects video media."""
        msg = MagicMock()
        msg.media = MagicMock()
        type(msg.media).__name__ = "MessageMediaDocument"

        attr = MagicMock()
        type(attr).__name__ = "DocumentAttributeVideo"
        attr.round_message = False

        msg.media.document = MagicMock()
        msg.media.document.attributes = [attr]

        assert _detect_media_type(msg) == "video"

    def test_video_note(self):
        """Detects video note (round video)."""
        msg = MagicMock()
        msg.media = MagicMock()
        type(msg.media).__name__ = "MessageMediaDocument"

        attr = MagicMock()
        type(attr).__name__ = "DocumentAttributeVideo"
        attr.round_message = True

        msg.media.document = MagicMock()
        msg.media.document.attributes = [attr]

        assert _detect_media_type(msg) == "video_note"

    def test_sticker(self):
        """Detects sticker."""
        msg = MagicMock()
        msg.media = MagicMock()
        type(msg.media).__name__ = "MessageMediaDocument"

        attr = MagicMock()
        type(attr).__name__ = "DocumentAttributeSticker"

        msg.media.document = MagicMock()
        msg.media.document.attributes = [attr]

        assert _detect_media_type(msg) == "sticker"


class TestTranscriptResult:
    """Tests for TranscriptResult dataclass."""

    def test_success_result(self):
        """Creates successful result."""
        result = TranscriptResult(
            success=True,
            text="Hello world",
            method="telegram"
        )
        assert result.success
        assert result.text == "Hello world"
        assert result.method == "telegram"
        assert result.error is None

    def test_failure_result(self):
        """Creates failure result."""
        result = TranscriptResult(
            success=False,
            error="Transcription failed"
        )
        assert not result.success
        assert result.error == "Transcription failed"

    def test_pending_result(self):
        """Creates pending result."""
        result = TranscriptResult(
            success=True,
            text="Partial...",
            pending=True,
            trial_remaining=3
        )
        assert result.pending
        assert result.trial_remaining == 3


class TestDownloadMedia:
    """Tests for media downloading."""

    async def test_download_specific_message(self):
        """Downloads media from specific message."""
        client = AsyncMock()
        entity = MagicMock()

        msg = MagicMock()
        msg.id = 123
        msg.media = MagicMock()
        msg.date = MagicMock()
        msg.date.isoformat.return_value = "2024-01-15T10:00:00"

        client.get_messages = AsyncMock(return_value=msg)

        with tempfile.TemporaryDirectory() as tmpdir:
            downloaded_path = os.path.join(tmpdir, "test_file.jpg")
            # Create a dummy file
            Path(downloaded_path).touch()

            client.download_media = AsyncMock(return_value=downloaded_path)

            with patch('telegram_telethon.modules.media.resolve_entity',
                       return_value=(entity, "Test Chat")):
                with patch('telegram_telethon.modules.media._detect_media_type',
                           return_value="photo"):
                    result = await download_media(
                        client, "Test Chat",
                        message_id=123,
                        output_dir=tmpdir
                    )

        assert len(result) == 1
        assert result[0]["message_id"] == 123
        assert result[0]["file"] == "test_file.jpg"

    async def test_download_no_media_in_message(self):
        """Returns error when message has no media."""
        client = AsyncMock()
        entity = MagicMock()

        msg = MagicMock()
        msg.media = None
        client.get_messages = AsyncMock(return_value=msg)

        with patch('telegram_telethon.modules.media.resolve_entity',
                   return_value=(entity, "Test Chat")):
            result = await download_media(client, "Test Chat", message_id=123)

        assert "error" in result[0]
        assert "No media" in result[0]["error"]

    async def test_download_chat_not_found(self):
        """Returns error when chat not found."""
        client = AsyncMock()

        with patch('telegram_telethon.modules.media.resolve_entity',
                   return_value=(None, "Unknown")):
            result = await download_media(client, "Unknown")

        assert "error" in result[0]
        assert "not found" in result[0]["error"]


class TestTranscribeVoice:
    """Tests for voice transcription."""

    async def test_telegram_transcription_success(self):
        """Succeeds with Telegram's native transcription."""
        client = AsyncMock()
        entity = MagicMock()

        # Mock successful transcription - client() is the callable
        transcribe_result = MagicMock()
        transcribe_result.pending = False
        transcribe_result.text = "Hello, this is a test message"
        client.return_value = transcribe_result

        with patch('telegram_telethon.modules.media.resolve_entity',
                   return_value=(entity, "Test Chat")):
            result = await transcribe_voice(client, "Test Chat", 123)

        assert result.success
        assert result.text == "Hello, this is a test message"
        assert result.method == "telegram"

    async def test_telegram_transcription_pending(self):
        """Waits for pending transcription."""
        client = AsyncMock()
        entity = MagicMock()

        # First call returns pending, second returns complete
        pending_result = MagicMock()
        pending_result.pending = True
        pending_result.text = ""

        complete_result = MagicMock()
        complete_result.pending = False
        complete_result.text = "Transcribed text"

        client.side_effect = [pending_result, complete_result]

        with patch('telegram_telethon.modules.media.resolve_entity',
                   return_value=(entity, "Test Chat")):
            with patch('asyncio.sleep', new_callable=AsyncMock):
                result = await transcribe_voice(client, "Test Chat", 123)

        assert result.success
        assert result.text == "Transcribed text"

    async def test_fallback_to_groq(self):
        """Falls back to Groq when Telegram fails."""
        client = AsyncMock()
        entity = MagicMock()

        # Telegram transcription fails with premium error
        client.side_effect = Exception("premium required")

        msg = MagicMock()
        msg.media = MagicMock()
        client.get_messages = AsyncMock(return_value=msg)
        client.download_media = AsyncMock(return_value="/tmp/voice.ogg")

        with patch('telegram_telethon.modules.media.resolve_entity',
                   return_value=(entity, "Test Chat")):
            with patch('telegram_telethon.modules.media._transcribe_with_groq',
                       return_value=TranscriptResult(success=True, text="Groq result", method="groq")):
                result = await transcribe_voice(
                    client, "Test Chat", 123,
                    fallback_method="groq",
                    groq_api_key="test_key"
                )

        assert result.success
        assert result.method == "groq"

    async def test_no_fallback_configured(self):
        """Returns error when no fallback and Telegram fails."""
        client = AsyncMock()
        entity = MagicMock()

        client.side_effect = Exception("premium required")

        with patch('telegram_telethon.modules.media.resolve_entity',
                   return_value=(entity, "Test Chat")):
            result = await transcribe_voice(
                client, "Test Chat", 123,
                fallback_method=None
            )

        assert not result.success
        assert "no fallback" in result.error.lower()

    async def test_chat_not_found(self):
        """Returns error when chat not found."""
        client = AsyncMock()

        with patch('telegram_telethon.modules.media.resolve_entity',
                   return_value=(None, "Unknown")):
            result = await transcribe_voice(client, "Unknown", 123)

        assert not result.success
        assert "not found" in result.error


class TestTranscribeWithGroq:
    """Tests for Groq transcription."""

    async def test_groq_success(self):
        """Groq transcription succeeds."""
        from telegram_telethon.modules.media import _transcribe_with_groq

        with tempfile.NamedTemporaryFile(suffix=".ogg", delete=False) as f:
            f.write(b"fake audio data")
            temp_path = f.name

        try:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"text": "Transcribed text"}

            with patch('httpx.AsyncClient') as mock_client:
                mock_instance = AsyncMock()
                mock_instance.post = AsyncMock(return_value=mock_response)
                mock_instance.__aenter__ = AsyncMock(return_value=mock_instance)
                mock_instance.__aexit__ = AsyncMock()
                mock_client.return_value = mock_instance

                result = await _transcribe_with_groq(temp_path, "test_api_key")

            assert result.success
            assert result.text == "Transcribed text"
            assert result.method == "groq"
        finally:
            os.unlink(temp_path)

    async def test_groq_no_api_key(self):
        """Returns error when no API key."""
        from telegram_telethon.modules.media import _transcribe_with_groq

        with patch.dict(os.environ, {}, clear=True):
            # Ensure GROQ_API_KEY is not in environment
            if "GROQ_API_KEY" in os.environ:
                del os.environ["GROQ_API_KEY"]

            result = await _transcribe_with_groq("/tmp/test.ogg", None)

        assert not result.success
        assert "GROQ_API_KEY" in result.error


class TestTranscribeBatch:
    """Tests for batch transcription."""

    async def test_batch_multiple_messages(self):
        """Transcribes multiple voice messages."""
        client = AsyncMock()
        entity = MagicMock()

        # Create mock voice messages
        msg1 = MagicMock()
        msg1.id = 1
        msg1.date = MagicMock()
        msg1.date.isoformat.return_value = "2024-01-15T10:00:00"
        msg1.sender = MagicMock(first_name="Alice")
        msg1.media = MagicMock()

        msg2 = MagicMock()
        msg2.id = 2
        msg2.date = MagicMock()
        msg2.date.isoformat.return_value = "2024-01-15T11:00:00"
        msg2.sender = MagicMock(first_name="Bob")
        msg2.media = MagicMock()

        async def mock_iter_messages(*args, **kwargs):
            for msg in [msg1, msg2]:
                yield msg

        client.iter_messages = mock_iter_messages

        with patch('telegram_telethon.modules.media.resolve_entity',
                   return_value=(entity, "Test Chat")):
            with patch('telegram_telethon.modules.media._detect_media_type',
                       return_value="voice"):
                with patch('telegram_telethon.modules.media.transcribe_voice',
                           return_value=TranscriptResult(success=True, text="Test", method="telegram")):
                    with patch('asyncio.sleep', new_callable=AsyncMock):
                        result = await transcribe_batch(client, "Test Chat", limit=2)

        assert len(result) == 2
        assert result[0]["sender"] == "Alice"
        assert result[1]["sender"] == "Bob"


class TestDownloadProfilePhoto:
    """Tests for profile photo downloading."""

    async def test_download_success(self):
        """Downloads profile photo successfully."""
        client = AsyncMock()
        entity = MagicMock()

        with tempfile.TemporaryDirectory() as tmpdir:
            photo_path = os.path.join(tmpdir, "photo.jpg")
            Path(photo_path).touch()

            client.download_profile_photo = AsyncMock(return_value=photo_path)

            with patch('telegram_telethon.modules.media.resolve_entity',
                       return_value=(entity, "Test User")):
                result = await download_profile_photo(
                    client, "Test User",
                    output_dir=tmpdir
                )

        assert result["downloaded"]
        assert result["chat"] == "Test User"

    async def test_no_profile_photo(self):
        """Returns error when no profile photo."""
        client = AsyncMock()
        entity = MagicMock()
        client.download_profile_photo = AsyncMock(return_value=None)

        with patch('telegram_telethon.modules.media.resolve_entity',
                   return_value=(entity, "Test User")):
            result = await download_profile_photo(client, "Test User")

        assert not result["downloaded"]
        assert "No profile photo" in result["error"]

    async def test_chat_not_found(self):
        """Returns error when chat not found."""
        client = AsyncMock()

        with patch('telegram_telethon.modules.media.resolve_entity',
                   return_value=(None, "Unknown")):
            result = await download_profile_photo(client, "Unknown")

        assert "error" in result
        assert "not found" in result["error"]
