"""Main daemon runner.

Connects to Telegram and listens for events, routing them to handlers.
"""
from __future__ import annotations

import asyncio
import logging
from pathlib import Path
from typing import Optional

from telethon import TelegramClient, events

from ..core.config import Config, DaemonConfig, DEFAULT_CONFIG_DIR
from .claude_bridge import ClaudeBridge
from .handlers import EventRouter, MessageHandler, DebounceManager, DebouncedMessage


logger = logging.getLogger(__name__)


class Daemon:
    """Main daemon process."""

    def __init__(
        self,
        config_dir: Path = DEFAULT_CONFIG_DIR,
        daemon_config_path: Optional[Path] = None,
    ):
        self.config_dir = config_dir
        self.daemon_config_path = daemon_config_path or (config_dir / "daemon.yaml")

        self._client: Optional[TelegramClient] = None
        self._running = False
        self._router: Optional[EventRouter] = None
        self._handler: Optional[MessageHandler] = None
        self._bridge: Optional[ClaudeBridge] = None
        self._debounce: DebounceManager = DebounceManager()

    async def start(self) -> None:
        """Start the daemon."""
        logger.info("Starting daemon...")

        # Load configs
        config = Config.load(self.config_dir / "config.yaml")
        if not config.is_configured():
            raise RuntimeError("Telegram not configured. Run 'tg.py setup' first.")

        daemon_config = DaemonConfig.load(self.daemon_config_path)

        # Initialize components
        self._bridge = ClaudeBridge(
            config=daemon_config.claude,
            sessions_file=self.config_dir / "sessions.json",
            max_concurrent=daemon_config.queue_max_concurrent,
        )
        await self._bridge.load_sessions()

        self._router = EventRouter(triggers=daemon_config.triggers)
        self._handler = MessageHandler(claude_bridge=self._bridge)

        # Create Telegram client
        session_path = self.config_dir / "session"
        self._client = TelegramClient(
            str(session_path),
            config.api_id,
            config.api_hash,
        )

        # Register event handler (incoming=True filters to only messages from others)
        # Remove filter to also catch own messages for testing
        @self._client.on(events.NewMessage())
        async def on_new_message(event):
            await self._handle_message(event)

        # Connect and run
        await self._client.start()

        me = await self._client.get_me()
        logger.info(f"Connected as {me.first_name} (@{me.username})")
        logger.info(f"Listening for {len(daemon_config.triggers)} trigger(s)...")

        self._running = True
        await self._client.run_until_disconnected()

    async def stop(self) -> None:
        """Stop the daemon."""
        logger.info("Stopping daemon...")
        self._running = False

        # Cancel pending debounced messages
        cancelled = self._debounce.cancel_all()
        if cancelled:
            logger.info(f"Cancelled {cancelled} pending debounced message(s)")

        if self._client:
            await self._client.disconnect()

        if self._bridge:
            await self._bridge.save_sessions()

    async def _handle_message(self, event) -> None:
        """Handle incoming message event."""
        try:
            # Get chat info
            chat = await event.get_chat()
            chat_name = getattr(chat, "title", None) or getattr(chat, "username", None) or str(chat.id)

            # Check if username-based
            if hasattr(chat, "username") and chat.username:
                chat_name = f"@{chat.username}"

            message_text = event.message.text or ""

            logger.debug(f"Message from {chat_name}: {message_text[:50]}...")

            # Route to trigger
            match = self._router.match(
                chat_name=chat_name,
                message_text=message_text,
            )

            if not match:
                logger.debug("No trigger matched")
                return

            logger.info(f"Matched trigger: {match.trigger.action} for {chat_name}")

            # Check if trigger uses debounce
            if match.trigger.debounce_seconds > 0:
                is_new = await self._debounce.schedule(
                    chat_id=event.chat_id,
                    trigger=match.trigger,
                    message_text=message_text,
                    captured_text=match.captured_text,
                    message_id=event.message.id,
                    callback=self._execute_debounced,
                )
                if is_new:
                    logger.info(f"Scheduled debounced response ({match.trigger.debounce_seconds}s)")
                else:
                    logger.debug(f"Reset debounce timer ({match.trigger.debounce_seconds}s)")
                return

            # Handle action immediately (no debounce)
            await self._execute_action(
                trigger=match.trigger,
                chat_id=event.chat_id,
                message_text=message_text,
                captured_text=match.captured_text,
                message_id=event.message.id,
            )

        except Exception as e:
            logger.exception(f"Error handling message: {e}")

    async def _execute_debounced(self, pending: DebouncedMessage) -> None:
        """Execute a debounced action after timer expires."""
        logger.info(f"Executing debounced action for chat {pending.chat_id}")
        await self._execute_action(
            trigger=pending.trigger,
            chat_id=pending.chat_id,
            message_text=pending.message_text,
            captured_text=pending.captured_text,
            message_id=pending.message_id,
        )

    async def _execute_action(
        self,
        trigger,
        chat_id: int,
        message_text: str,
        captured_text: Optional[str],
        message_id: Optional[int],
    ) -> None:
        """Execute a trigger action and send response."""
        result = await self._handler.handle(
            trigger=trigger,
            chat_id=chat_id,
            message_text=message_text,
            captured_text=captured_text,
            message_id=message_id,
        )

        # Send response
        if result.should_reply and result.response:
            # Check for SKIP signal (Claude decided not to respond)
            if result.response.strip().upper() == "SKIP":
                logger.info("Claude returned SKIP - not sending response")
                return

            await self._client.send_message(
                chat_id,
                result.response,
                reply_to=result.reply_to_message_id,
            )
            logger.info(f"Sent response ({len(result.response)} chars)")

        elif not result.success:
            logger.error(f"Handler error: {result.error}")


async def run_daemon(
    config_dir: Path = DEFAULT_CONFIG_DIR,
    daemon_config_path: Optional[Path] = None,
) -> None:
    """Run the daemon process."""
    daemon = Daemon(
        config_dir=config_dir,
        daemon_config_path=daemon_config_path,
    )

    try:
        await daemon.start()
    except KeyboardInterrupt:
        pass
    finally:
        await daemon.stop()
