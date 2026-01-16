"""Claude Code integration bridge.

Handles spawning Claude Code sessions, session persistence,
and request queuing for rate limiting.
"""
from __future__ import annotations

import asyncio
import json
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any

from ..core.config import ClaudeConfig


class ClaudeError(Exception):
    """Claude bridge error."""
    pass


@dataclass
class ClaudeSession:
    """Persistent Claude session for a chat."""

    chat_id: int
    session_id: str
    message_count: int = 0
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    last_used: str = field(default_factory=lambda: datetime.now().isoformat())

    def increment(self) -> None:
        """Increment message count and update last_used."""
        self.message_count += 1
        self.last_used = datetime.now().isoformat()

    def to_dict(self) -> dict:
        """Serialize to dictionary."""
        return {
            "chat_id": self.chat_id,
            "session_id": self.session_id,
            "message_count": self.message_count,
            "created_at": self.created_at,
            "last_used": self.last_used,
        }

    @classmethod
    def from_dict(cls, data: dict) -> ClaudeSession:
        """Deserialize from dictionary."""
        return cls(
            chat_id=data["chat_id"],
            session_id=data["session_id"],
            message_count=data.get("message_count", 0),
            created_at=data.get("created_at", datetime.now().isoformat()),
            last_used=data.get("last_used", datetime.now().isoformat()),
        )


@dataclass
class ClaudeResponse:
    """Response from Claude Code."""

    result: Optional[str] = None
    session_id: Optional[str] = None
    success: bool = False
    error: Optional[str] = None
    raw: Optional[str] = None

    @classmethod
    def parse(cls, raw: str) -> ClaudeResponse:
        """Parse JSON response from Claude CLI."""
        try:
            data = json.loads(raw)

            # Handle array format (multiple JSON events)
            if isinstance(data, list):
                # Find the result event
                for event in data:
                    if event.get("type") == "result":
                        return cls(
                            result=event.get("result"),
                            session_id=event.get("session_id"),
                            success=not event.get("is_error", False),
                            error=event.get("result") if event.get("is_error") else None,
                            raw=raw,
                        )
                # No result found
                return cls(
                    success=False,
                    error="No result in Claude response",
                    raw=raw,
                )

            # Handle single object format
            if "error" in data:
                return cls(
                    success=False,
                    error=data["error"],
                    raw=raw,
                )

            return cls(
                result=data.get("result"),
                session_id=data.get("session_id"),
                success=True,
                raw=raw,
            )
        except json.JSONDecodeError as e:
            return cls(
                success=False,
                error=f"Failed to parse JSON response: {e}",
                raw=raw,
            )

    def truncated(self, max_length: int = 4000) -> str:
        """Get truncated result for display."""
        if not self.result:
            return ""
        if len(self.result) <= max_length:
            return self.result
        return self.result[:max_length] + "..."


class ClaudeBridge:
    """Bridge for Claude Code subprocess communication."""

    def __init__(
        self,
        config: ClaudeConfig,
        sessions_file: Optional[Path] = None,
        max_concurrent: int = 1,
        max_queue_size: int = 10,
    ):
        self.config = config
        self.sessions_file = sessions_file
        self.sessions: Dict[int, ClaudeSession] = {}
        self.max_concurrent = max_concurrent
        self.max_queue_size = max_queue_size

        # Queue management
        self._semaphore = asyncio.Semaphore(max_concurrent)
        self._queue_size = 0

    async def load_sessions(self) -> None:
        """Load sessions from disk."""
        if not self.sessions_file or not self.sessions_file.exists():
            return

        try:
            data = json.loads(self.sessions_file.read_text())
            for key, session_data in data.items():
                chat_id = int(key)
                self.sessions[chat_id] = ClaudeSession.from_dict(session_data)
        except (json.JSONDecodeError, KeyError) as e:
            import logging
            logging.getLogger(__name__).warning(
                f"Failed to load sessions from {self.sessions_file}: {e}"
            )

    async def save_sessions(self) -> None:
        """Save sessions to disk."""
        if not self.sessions_file:
            return

        self.sessions_file.parent.mkdir(parents=True, exist_ok=True)

        data = {
            str(chat_id): session.to_dict()
            for chat_id, session in self.sessions.items()
        }

        self.sessions_file.write_text(json.dumps(data, indent=2))

    def clear_session(self, chat_id: int) -> None:
        """Clear session for a chat (start fresh)."""
        if chat_id in self.sessions:
            del self.sessions[chat_id]

    async def send(
        self,
        prompt: str,
        chat_id: int,
        system_prompt: Optional[str] = None,
    ) -> ClaudeResponse:
        """Send prompt to Claude and return response.

        Args:
            prompt: The prompt to send
            chat_id: Telegram chat ID (for session tracking)
            system_prompt: Optional system prompt to guide Claude's behavior

        Returns:
            ClaudeResponse with result or error
        """
        # Check queue capacity
        if self._queue_size >= self.max_queue_size:
            return ClaudeResponse(
                success=False,
                error="Queue is full - too many pending requests. Please try again later.",
            )

        self._queue_size += 1
        try:
            async with self._semaphore:
                return await self._execute(prompt, chat_id, system_prompt)
        finally:
            self._queue_size -= 1

    async def _execute(
        self,
        prompt: str,
        chat_id: int,
        system_prompt: Optional[str] = None,
    ) -> ClaudeResponse:
        """Execute Claude CLI command."""
        # Build command
        cmd = ["claude", "-p", prompt, "--output-format", "json"]

        # Add system prompt if provided
        if system_prompt:
            cmd.extend(["--system-prompt", system_prompt])

        # Add session resume if exists (only if no system prompt - fresh context)
        session = self.sessions.get(chat_id)
        if session and not system_prompt:
            cmd.extend(["--resume", session.session_id])

        # Add config-based args
        cmd.extend(self.config.build_cli_args())

        # Log the command being executed
        import logging
        logger = logging.getLogger(__name__)
        logger.info(f"Claude command: {' '.join(cmd[:6])}...")  # First 6 args
        if system_prompt:
            logger.info(f"System prompt length: {len(system_prompt)} chars")

        try:
            # Execute subprocess with ANTHROPIC_API_KEY unset (use subscription auth)
            import os
            env = os.environ.copy()
            env.pop("ANTHROPIC_API_KEY", None)

            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env=env,
            )

            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(),
                    timeout=self.config.timeout,
                )
            except asyncio.TimeoutError:
                process.kill()
                return ClaudeResponse(
                    success=False,
                    error=f"Timeout after {self.config.timeout}s",
                )

            if process.returncode != 0:
                return ClaudeResponse(
                    success=False,
                    error=f"Claude exited with code {process.returncode}: {stderr.decode()}",
                )

            # Parse response
            response = ClaudeResponse.parse(stdout.decode())

            # Update session tracking
            if response.success and response.session_id:
                if chat_id in self.sessions:
                    self.sessions[chat_id].session_id = response.session_id
                    self.sessions[chat_id].increment()
                else:
                    self.sessions[chat_id] = ClaudeSession(
                        chat_id=chat_id,
                        session_id=response.session_id,
                    )
                # Auto-save sessions
                await self.save_sessions()

            return response

        except OSError as e:
            return ClaudeResponse(
                success=False,
                error=f"Failed to execute Claude CLI: {e}",
            )
        except Exception as e:
            return ClaudeResponse(
                success=False,
                error=f"Unexpected error: {e}",
            )
