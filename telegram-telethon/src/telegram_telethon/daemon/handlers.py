"""Event handlers for the daemon.

Routes incoming Telegram events to appropriate actions.
"""
from __future__ import annotations

import asyncio
import re
import time
from dataclasses import dataclass, field
from typing import Optional, List, Any, Dict, Callable, Awaitable

from ..core.config import TriggerConfig
from .claude_bridge import ClaudeBridge


@dataclass
class RouteMatch:
    """Result of matching an event to a trigger."""

    trigger: TriggerConfig
    captured_text: Optional[str] = None
    match_object: Optional[re.Match] = None


@dataclass
class ActionResult:
    """Result of handling an action."""

    success: bool
    response: Optional[str] = None
    error: Optional[str] = None
    should_reply: bool = False
    reply_to_message_id: Optional[int] = None


class EventRouter:
    """Routes events to matching triggers."""

    def __init__(self, triggers: List[TriggerConfig]):
        self.triggers = triggers

    def match(
        self,
        chat_name: str,
        message_text: str,
    ) -> Optional[RouteMatch]:
        """Find matching trigger for event.

        Args:
            chat_name: Name of the chat (or @username)
            message_text: Text of the message

        Returns:
            RouteMatch if found, None otherwise
        """
        for trigger in self.triggers:
            # Check chat match
            if not trigger.matches_chat(chat_name):
                continue

            # Check pattern match
            match = trigger.match_message(message_text)
            if match:
                # Extract captured group if present
                captured = None
                if match.groups():
                    captured = match.group(1)

                return RouteMatch(
                    trigger=trigger,
                    captured_text=captured,
                    match_object=match,
                )

        return None


class MessageHandler:
    """Handles matched message events."""

    def __init__(self, claude_bridge: ClaudeBridge):
        self.claude_bridge = claude_bridge

    async def handle(
        self,
        trigger: TriggerConfig,
        chat_id: int,
        message_text: str,
        captured_text: Optional[str],
        message_id: Optional[int] = None,
    ) -> ActionResult:
        """Handle a matched trigger.

        Args:
            trigger: The matched trigger config
            chat_id: Telegram chat ID
            message_text: Full message text
            captured_text: Text captured by regex group
            message_id: Original message ID (for replies)

        Returns:
            ActionResult with response or error
        """
        if trigger.action == "ignore":
            return ActionResult(
                success=True,
                should_reply=False,
            )

        if trigger.action == "reply":
            return ActionResult(
                success=True,
                response=trigger.reply_text,
                should_reply=True,
                reply_to_message_id=message_id if trigger.reply_mode == "inline" else None,
            )

        if trigger.action == "claude":
            # Use captured text or full message
            prompt = captured_text or message_text

            response = await self.claude_bridge.send(
                prompt,
                chat_id=chat_id,
                system_prompt=trigger.system_prompt,
            )

            if not response.success:
                return ActionResult(
                    success=False,
                    error=response.error,
                    should_reply=False,
                )

            return ActionResult(
                success=True,
                response=response.result,
                should_reply=True,
                reply_to_message_id=message_id if trigger.reply_mode == "inline" else None,
            )

        # Unknown action
        return ActionResult(
            success=False,
            error=f"Unknown action: {trigger.action}",
        )


@dataclass
class DebouncedMessage:
    """Pending debounced message."""

    chat_id: int
    trigger: TriggerConfig
    message_text: str
    captured_text: Optional[str]
    message_id: Optional[int]
    last_update: float
    task: Optional[asyncio.Task] = None


class DebounceManager:
    """Manages debounced message handling.

    For triggers with debounce_seconds > 0, waits until no new messages
    arrive for the specified duration before triggering the action.
    """

    def __init__(self):
        # Key: (chat_id, trigger_pattern) -> DebouncedMessage
        self._pending: Dict[tuple, DebouncedMessage] = {}

    def _key(self, chat_id: int, trigger: TriggerConfig) -> tuple:
        """Generate unique key for chat+trigger combination."""
        return (chat_id, trigger.pattern)

    async def schedule(
        self,
        chat_id: int,
        trigger: TriggerConfig,
        message_text: str,
        captured_text: Optional[str],
        message_id: Optional[int],
        callback: Callable[[DebouncedMessage], Awaitable[None]],
    ) -> bool:
        """Schedule a debounced message.

        Args:
            chat_id: Telegram chat ID
            trigger: Trigger config with debounce_seconds
            message_text: Full message text
            captured_text: Captured regex group text
            message_id: Original message ID
            callback: Async function to call when debounce completes

        Returns:
            True if newly scheduled, False if reset existing timer
        """
        key = self._key(chat_id, trigger)
        now = time.time()

        if key in self._pending:
            # Cancel existing timer and reset
            pending = self._pending[key]
            if pending.task and not pending.task.done():
                pending.task.cancel()

            # Update with latest message
            pending.message_text = message_text
            pending.captured_text = captured_text
            pending.message_id = message_id
            pending.last_update = now

            # Schedule new timer
            pending.task = asyncio.create_task(
                self._wait_and_execute(key, callback)
            )
            return False

        # Create new pending entry
        pending = DebouncedMessage(
            chat_id=chat_id,
            trigger=trigger,
            message_text=message_text,
            captured_text=captured_text,
            message_id=message_id,
            last_update=now,
        )
        pending.task = asyncio.create_task(
            self._wait_and_execute(key, callback)
        )
        self._pending[key] = pending
        return True

    async def _wait_and_execute(
        self,
        key: tuple,
        callback: Callable[[DebouncedMessage], Awaitable[None]],
    ) -> None:
        """Wait for debounce period then execute callback."""
        pending = self._pending.get(key)
        if not pending:
            return

        debounce_secs = pending.trigger.debounce_seconds

        while True:
            elapsed = time.time() - pending.last_update
            remaining = debounce_secs - elapsed

            if remaining <= 0:
                break

            try:
                await asyncio.sleep(remaining)
            except asyncio.CancelledError:
                return

        # Remove from pending and execute
        if key in self._pending:
            del self._pending[key]
            await callback(pending)

    def cancel(self, chat_id: int, trigger: TriggerConfig) -> bool:
        """Cancel a pending debounced message."""
        key = self._key(chat_id, trigger)
        if key in self._pending:
            pending = self._pending[key]
            if pending.task and not pending.task.done():
                pending.task.cancel()
            del self._pending[key]
            return True
        return False

    def cancel_all(self) -> int:
        """Cancel all pending debounced messages."""
        count = 0
        for pending in self._pending.values():
            if pending.task and not pending.task.done():
                pending.task.cancel()
                count += 1
        self._pending.clear()
        return count
