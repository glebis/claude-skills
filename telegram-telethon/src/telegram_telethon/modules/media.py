"""Media operations module.

Handles downloading media, voice transcription, and file uploads.
"""
from __future__ import annotations

import asyncio
import logging
import os
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, List, Dict, Any

from telethon import TelegramClient, functions
from telethon.tl.types import DocumentAttributeAudio

from .messages import resolve_entity, get_chat_type

logger = logging.getLogger(__name__)


DEFAULT_DOWNLOAD_DIR = Path.home() / 'Downloads' / 'telegram_attachments'


@dataclass
class TranscriptResult:
    """Result of voice transcription."""
    success: bool
    text: Optional[str] = None
    method: Optional[str] = None  # "telegram", "groq", "whisper"
    error: Optional[str] = None
    pending: bool = False
    trial_remaining: Optional[int] = None


async def download_media(
    client: TelegramClient,
    chat_name: str,
    limit: int = 5,
    output_dir: Optional[str] = None,
    message_id: Optional[int] = None,
    media_type: Optional[str] = None,  # "voice", "video", "photo", "document"
) -> List[Dict]:
    """Download media attachments from a chat.

    Args:
        chat_name: Chat name, @username, or ID
        limit: Max attachments to download
        output_dir: Output directory
        message_id: Specific message ID to download from
        media_type: Filter by media type
    """
    out_path = Path(output_dir) if output_dir else DEFAULT_DOWNLOAD_DIR
    out_path.mkdir(parents=True, exist_ok=True)

    entity, resolved_name = await resolve_entity(client, chat_name)
    if entity is None:
        return [{"error": f"Chat '{chat_name}' not found"}]

    downloaded = []

    if message_id:
        # Download from specific message
        msg = await client.get_messages(entity, ids=message_id)
        if msg and msg.media:
            try:
                file_path = await client.download_media(msg, str(out_path))
                if file_path:
                    downloaded.append({
                        "message_id": msg.id,
                        "chat": resolved_name,
                        "file": os.path.basename(file_path),
                        "path": file_path,
                        "size": os.path.getsize(file_path),
                        "date": msg.date.isoformat() if msg.date else None,
                        "media_type": _detect_media_type(msg),
                    })
            except Exception as e:
                downloaded.append({"message_id": message_id, "error": str(e)})
        else:
            downloaded.append({"message_id": message_id, "error": "No media in message"})
    else:
        # Download recent media
        count = 0
        async for msg in client.iter_messages(entity, limit=100):
            if not msg.media:
                continue

            # Filter by media type if specified
            msg_type = _detect_media_type(msg)
            if media_type and msg_type != media_type:
                continue

            try:
                file_path = await client.download_media(msg, str(out_path))
                if file_path:
                    downloaded.append({
                        "message_id": msg.id,
                        "chat": resolved_name,
                        "file": os.path.basename(file_path),
                        "path": file_path,
                        "size": os.path.getsize(file_path),
                        "date": msg.date.isoformat() if msg.date else None,
                        "media_type": msg_type,
                    })
                    count += 1
                    if count >= limit:
                        break
            except Exception as e:
                downloaded.append({"message_id": msg.id, "error": str(e)})
            await asyncio.sleep(0.2)

    return downloaded


def _detect_media_type(msg) -> Optional[str]:
    """Detect the type of media in a message."""
    if not msg.media:
        return None

    media_class = type(msg.media).__name__

    if media_class == 'MessageMediaPhoto':
        return "photo"
    elif media_class == 'MessageMediaDocument':
        doc = msg.media.document
        if doc and hasattr(doc, 'attributes'):
            for attr in doc.attributes:
                attr_class = type(attr).__name__
                if attr_class == 'DocumentAttributeAudio':
                    if hasattr(attr, 'voice') and attr.voice:
                        return "voice"
                    return "audio"
                elif attr_class == 'DocumentAttributeVideo':
                    if hasattr(attr, 'round_message') and attr.round_message:
                        return "video_note"
                    return "video"
                elif attr_class == 'DocumentAttributeSticker':
                    return "sticker"
                elif attr_class == 'DocumentAttributeAnimated':
                    return "animation"
        return "document"
    elif media_class == 'MessageMediaWebPage':
        return "webpage"

    return "unknown"


async def transcribe_voice(
    client: TelegramClient,
    chat_name: str,
    message_id: int,
    fallback_method: Optional[str] = "groq",  # "groq", "whisper", None
    groq_api_key: Optional[str] = None,
) -> TranscriptResult:
    """Transcribe a voice message.

    First attempts Telegram's server-side transcription (Premium feature).
    Falls back to local transcription if unavailable or quota exceeded.

    Args:
        client: Telegram client
        chat_name: Chat containing the voice message
        message_id: Message ID of the voice message
        fallback_method: "groq" (Groq Whisper API), "whisper" (local), or None
        groq_api_key: API key for Groq (required if fallback_method="groq")
    """
    entity, resolved_name = await resolve_entity(client, chat_name)
    if entity is None:
        return TranscriptResult(success=False, error=f"Chat '{chat_name}' not found")

    # Try Telegram's transcription first
    try:
        result = await client(functions.messages.TranscribeAudioRequest(
            peer=entity,
            msg_id=message_id
        ))

        if result.pending:
            # Transcription in progress - wait for it
            for _ in range(30):  # Wait up to 30 seconds
                await asyncio.sleep(1)
                # Re-fetch to check status
                result = await client(functions.messages.TranscribeAudioRequest(
                    peer=entity,
                    msg_id=message_id
                ))
                if not result.pending:
                    break

        if result.text:
            return TranscriptResult(
                success=True,
                text=result.text,
                method="telegram",
                pending=result.pending,
                trial_remaining=getattr(result, 'trial_remains_num', None),
            )

    except Exception as e:
        error_str = str(e).lower()
        # Check if it's a "not premium" or "quota exceeded" error
        if "premium" not in error_str and "trial" not in error_str:
            return TranscriptResult(success=False, error=f"Telegram transcription failed: {e}")

    # Fallback to local transcription
    if not fallback_method:
        return TranscriptResult(
            success=False,
            error="Telegram transcription unavailable and no fallback configured"
        )

    # Download the voice message first
    msg = await client.get_messages(entity, ids=message_id)
    if not msg or not msg.media:
        return TranscriptResult(success=False, error="Message not found or has no media")

    with tempfile.TemporaryDirectory() as tmp_dir:
        file_path = await client.download_media(msg, tmp_dir)
        if not file_path:
            return TranscriptResult(success=False, error="Failed to download voice message")

        if fallback_method == "groq":
            return await _transcribe_with_groq(file_path, groq_api_key)
        elif fallback_method == "whisper":
            return await _transcribe_with_whisper(file_path)

    return TranscriptResult(success=False, error=f"Unknown fallback method: {fallback_method}")


async def _transcribe_with_groq(file_path: str, api_key: Optional[str]) -> TranscriptResult:
    """Transcribe audio using Groq's Whisper API."""
    if not api_key:
        api_key = os.environ.get("GROQ_API_KEY")

    if not api_key:
        return TranscriptResult(
            success=False,
            error="GROQ_API_KEY not provided and not in environment"
        )

    try:
        import httpx

        async with httpx.AsyncClient() as http_client:
            with open(file_path, 'rb') as f:
                response = await http_client.post(
                    "https://api.groq.com/openai/v1/audio/transcriptions",
                    headers={"Authorization": f"Bearer {api_key}"},
                    files={"file": (os.path.basename(file_path), f, "audio/ogg")},
                    data={"model": "whisper-large-v3"},
                    timeout=60.0,
                )

            if response.status_code == 200:
                data = response.json()
                return TranscriptResult(
                    success=True,
                    text=data.get("text", ""),
                    method="groq",
                )
            else:
                return TranscriptResult(
                    success=False,
                    error=f"Groq API error {response.status_code}: {response.text}"
                )
    except ImportError:
        return TranscriptResult(
            success=False,
            error="httpx not installed. Run: pip install httpx"
        )
    except Exception as e:
        return TranscriptResult(success=False, error=f"Groq transcription failed: {e}")


async def _transcribe_with_whisper(file_path: str) -> TranscriptResult:
    """Transcribe audio using local Whisper."""
    try:
        # Try using whisper CLI
        result = subprocess.run(
            ["whisper", file_path, "--model", "base", "--output_format", "txt"],
            capture_output=True,
            text=True,
            timeout=120,
        )

        if result.returncode == 0:
            # Read the output file
            txt_path = Path(file_path).with_suffix('.txt')
            if txt_path.exists():
                text = txt_path.read_text().strip()
                txt_path.unlink()  # Clean up
                return TranscriptResult(
                    success=True,
                    text=text,
                    method="whisper",
                )

        return TranscriptResult(
            success=False,
            error=f"Whisper failed: {result.stderr}"
        )
    except FileNotFoundError:
        return TranscriptResult(
            success=False,
            error="Whisper not installed. Run: pip install openai-whisper"
        )
    except subprocess.TimeoutExpired:
        return TranscriptResult(success=False, error="Whisper transcription timed out")
    except Exception as e:
        return TranscriptResult(success=False, error=f"Whisper error: {e}")


async def transcribe_batch(
    client: TelegramClient,
    chat_name: str,
    limit: int = 10,
    fallback_method: Optional[str] = "groq",
    groq_api_key: Optional[str] = None,
) -> List[Dict]:
    """Transcribe multiple voice messages from a chat.

    Args:
        chat_name: Chat to fetch voice messages from
        limit: Max messages to transcribe
        fallback_method: Transcription fallback
        groq_api_key: Groq API key
    """
    entity, resolved_name = await resolve_entity(client, chat_name)
    if entity is None:
        return [{"error": f"Chat '{chat_name}' not found"}]

    results = []
    count = 0

    async for msg in client.iter_messages(entity, limit=100):
        if _detect_media_type(msg) != "voice":
            continue

        result = await transcribe_voice(
            client,
            chat_name,
            msg.id,
            fallback_method=fallback_method,
            groq_api_key=groq_api_key,
        )

        results.append({
            "message_id": msg.id,
            "date": msg.date.isoformat() if msg.date else None,
            "sender": getattr(msg.sender, 'first_name', 'Unknown') if msg.sender else 'Unknown',
            "success": result.success,
            "text": result.text,
            "method": result.method,
            "error": result.error,
        })

        count += 1
        if count >= limit:
            break

        await asyncio.sleep(0.5)  # Rate limiting

    return results


async def download_profile_photo(
    client: TelegramClient,
    chat_name: str,
    output_dir: Optional[str] = None,
) -> Dict:
    """Download a user or chat's profile photo."""
    out_path = Path(output_dir) if output_dir else DEFAULT_DOWNLOAD_DIR
    out_path.mkdir(parents=True, exist_ok=True)

    entity, resolved_name = await resolve_entity(client, chat_name)
    if entity is None:
        return {"error": f"Chat '{chat_name}' not found"}

    try:
        file_path = await client.download_profile_photo(entity, str(out_path))
        if file_path:
            return {
                "downloaded": True,
                "chat": resolved_name,
                "file": os.path.basename(file_path),
                "path": file_path,
                "size": os.path.getsize(file_path),
            }
        return {"downloaded": False, "error": "No profile photo"}
    except Exception as e:
        return {"downloaded": False, "error": str(e)}
