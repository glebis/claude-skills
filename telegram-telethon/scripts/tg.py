#!/usr/bin/env python3
"""Main CLI for telegram-telethon.

Interactive commands for Telegram operations.
"""
import asyncio
import json
import os
import sys
from pathlib import Path

# Add src to path for development
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import argparse

from telegram_telethon.core.config import Config, DaemonConfig, TriggerConfig, ClaudeConfig, DEFAULT_CONFIG_DIR
from telegram_telethon.core.auth import AuthWizard, AuthStatus, verify_connection


async def get_client():
    """Get authenticated Telegram client."""
    from telethon import TelegramClient

    config = Config.load(DEFAULT_CONFIG_DIR / "config.yaml")
    if not config.is_configured():
        print(json.dumps({"error": "Not configured. Run: tg.py setup"}))
        sys.exit(1)

    session_path = DEFAULT_CONFIG_DIR / "session"
    client = TelegramClient(str(session_path), config.api_id, config.api_hash)
    await client.start()
    return client


def is_interactive():
    """Check if running in interactive TTY mode."""
    return sys.stdin.isatty() and sys.stdout.isatty()


def setup_wizard(api_id=None, api_hash=None, phone=None, code=None, password=None):
    """Setup wizard with TTY detection and non-interactive support.

    In interactive mode: prompts for all values
    In non-interactive mode: requires --api-id, --api-hash, --phone flags
    """
    try:
        from rich.console import Console
        from rich.panel import Panel
        from rich.prompt import Prompt, Confirm
    except ImportError:
        print("Install dependencies: pip install rich questionary")
        sys.exit(1)

    console = Console()
    interactive = is_interactive()
    wizard = AuthWizard()

    # Step 1: Get API credentials
    if interactive:
        console.print(Panel.fit(
            "[bold]Telegram API Setup Wizard[/bold]",
            border_style="blue",
        ))

        console.print("\n[bold]Step 1/4: Get API Credentials[/bold]")
        console.print("─" * 40)
        console.print("1. Open: [link]https://my.telegram.org/auth[/link]")
        console.print("2. Log in with your phone number")
        console.print("3. Click 'API development tools'")
        console.print("4. Create new application (any name works)\n")

        while True:
            api_id = Prompt.ask("Enter your api_id")
            if wizard.validate_api_id(api_id):
                break
            console.print("[red]Invalid API ID - must be numeric[/red]")

        while True:
            api_hash = Prompt.ask("Enter your api_hash")
            if wizard.validate_api_hash(api_hash):
                break
            console.print("[red]Invalid API hash - must be 32 hex characters[/red]")
    else:
        # Non-interactive: require CLI args
        if not api_id or not api_hash or not phone:
            print(json.dumps({
                "error": "Non-interactive mode requires --api-id, --api-hash, and --phone",
                "hint": "Run interactively in a terminal, or provide all credentials via flags"
            }))
            sys.exit(1)

        if not wizard.validate_api_id(str(api_id)):
            print(json.dumps({"error": "Invalid API ID - must be numeric"}))
            sys.exit(1)

        if not wizard.validate_api_hash(api_hash):
            print(json.dumps({"error": "Invalid API hash - must be 32 hex characters"}))
            sys.exit(1)

    wizard.set_credentials(str(api_id), api_hash)

    # Step 2: Phone number
    if interactive:
        console.print("\n[bold]Step 2/4: Phone Authentication[/bold]")
        console.print("─" * 40)

        while True:
            phone = Prompt.ask("Phone number (with country code, e.g. +1234567890)")
            if wizard.validate_phone(phone):
                break
            console.print("[red]Invalid phone - must start with + and contain digits[/red]")
    else:
        if not wizard.validate_phone(phone):
            print(json.dumps({"error": "Invalid phone - must start with + and contain digits"}))
            sys.exit(1)

    wizard.set_phone(phone)

    if interactive:
        console.print("Sending code...")

    async def do_auth():
        nonlocal code, password
        try:
            await wizard.send_code()

            if interactive:
                console.print("[green]Code sent![/green]")
                code = Prompt.ask("Enter the code from Telegram")
            else:
                if not code:
                    # Save config so user can complete auth later
                    print(json.dumps({
                        "status": "code_sent",
                        "message": "Verification code sent to phone. Re-run with --code to complete.",
                        "next_step": f"python3 scripts/tg.py setup --api-id {api_id} --api-hash {api_hash} --phone {phone} --code YOUR_CODE"
                    }))
                    return None

            try:
                user = await wizard.sign_in(code)
                return user
            except Exception as e:
                if "2FA" in str(e):
                    if interactive:
                        console.print("\n[bold]Step 3/4: Two-Factor Auth[/bold]")
                        console.print("─" * 40)
                        password = Prompt.ask("Enter your 2FA password", password=True)
                    else:
                        if not password:
                            print(json.dumps({
                                "status": "2fa_required",
                                "message": "2FA password required. Re-run with --password flag.",
                                "next_step": f"python3 scripts/tg.py setup --api-id {api_id} --api-hash {api_hash} --phone {phone} --code {code} --password YOUR_PASSWORD"
                            }))
                            return None
                    user = await wizard.sign_in_2fa(password)
                    return user
                raise
        finally:
            await wizard.disconnect()

    try:
        user = asyncio.run(do_auth())
    except Exception as e:
        if interactive:
            console.print(f"[red]Authentication failed: {e}[/red]")
        else:
            print(json.dumps({"error": f"Authentication failed: {e}"}))
        sys.exit(1)

    if user is None:
        # Partial setup - code was sent but not provided
        return

    if interactive:
        console.print("\n[bold]Step 4/4: Verify Connection[/bold]")
        console.print("─" * 40)
        console.print(f"[green]✓[/green] Connected as: {user.first_name} (@{user.username})")
        console.print(f"[green]✓[/green] Config saved to: {DEFAULT_CONFIG_DIR}")
        console.print("\n[bold green]Ready![/bold green] Try: tg.py list")

        if Confirm.ask("\nWould you like to configure the daemon now?"):
            setup_daemon_config(console)
    else:
        print(json.dumps({
            "status": "success",
            "connected_as": {
                "first_name": user.first_name,
                "username": user.username,
            },
            "config_dir": str(DEFAULT_CONFIG_DIR)
        }))


def setup_daemon_config(console=None):
    """Interactive daemon configuration."""
    try:
        from rich.console import Console
        from rich.prompt import Prompt, Confirm
    except ImportError:
        print("Install dependencies: pip install rich")
        sys.exit(1)

    if console is None:
        console = Console()

    console.print("\n[bold]Daemon Configuration[/bold]")
    console.print("─" * 40)

    triggers = []

    while True:
        console.print("\n[bold]Add a trigger[/bold]")
        chat = Prompt.ask("Chat to monitor (name, @username, or * for all)")
        pattern = Prompt.ask("Message pattern (regex)", default=r"^/claude (.+)$")
        action = Prompt.ask("Action", choices=["claude", "reply", "ignore"], default="claude")

        reply_mode = "inline"
        reply_text = None

        if action in ["claude", "reply"]:
            reply_mode = Prompt.ask("Reply mode", choices=["inline", "new"], default="inline")
        if action == "reply":
            reply_text = Prompt.ask("Reply text")

        triggers.append(TriggerConfig(
            chat=chat, pattern=pattern, action=action,
            reply_mode=reply_mode, reply_text=reply_text,
        ))

        console.print(f"[green]✓[/green] Added trigger: {chat} -> {action}")
        if not Confirm.ask("Add another trigger?", default=False):
            break

    console.print("\n[bold]Claude Configuration[/bold]")
    tools_input = Prompt.ask("Allowed tools (comma-separated)", default="Read,Edit,Bash,WebFetch")
    allowed_tools = [t.strip() for t in tools_input.split(",") if t.strip()]
    max_turns = int(Prompt.ask("Max turns per request", default="10"))
    timeout = int(Prompt.ask("Timeout in seconds", default="300"))

    daemon_config = DaemonConfig(
        triggers=triggers,
        claude=ClaudeConfig(allowed_tools=allowed_tools, max_turns=max_turns, timeout=timeout),
    )

    config_path = DEFAULT_CONFIG_DIR / "daemon.yaml"
    daemon_config.save(config_path)
    console.print(f"\n[green]✓[/green] Daemon config saved to: {config_path}")


def show_status():
    """Show current status."""
    status = AuthStatus.check()
    print(f"Config directory: {status.config_dir}")
    print(f"State: {status.state}")
    print(f"Ready: {status.is_ready}")

    if status.is_ready:
        result = asyncio.run(verify_connection())
        if result.get("connected"):
            print(f"Connected as: {result.get('first_name')} (@{result.get('username')})")
        else:
            print(f"Connection error: {result.get('error')}")


async def cmd_list(args):
    """List chats."""
    from telegram_telethon.modules.messages import list_chats
    from telegram_telethon.utils.formatting import format_chats_table

    client = await get_client()
    try:
        chats = await list_chats(client, limit=args.limit, search=args.search)
        if args.json:
            print(json.dumps(chats, indent=2, ensure_ascii=False))
        else:
            print(format_chats_table(chats))
    finally:
        await client.disconnect()


async def cmd_recent(args):
    """Fetch recent messages."""
    from telegram_telethon.modules.messages import fetch_recent
    from telegram_telethon.utils.formatting import format_output, append_to_daily, append_to_person, save_to_file

    client = await get_client()
    try:
        messages = await fetch_recent(
            client, chat_id=args.chat_id, chat_name=args.chat,
            limit=args.limit, days=args.days, include_chat_id=True,
        )
        output_fmt = "json" if args.json else "markdown"

        if args.output:
            result = save_to_file(messages, args.output, output_fmt)
            print(json.dumps(result, indent=2, ensure_ascii=False))
        elif args.to_daily:
            path = append_to_daily(format_output(messages, output_fmt))
            print(f"Appended to {path}")
        elif args.to_person:
            path = append_to_person(format_output(messages, output_fmt), args.to_person)
            print(f"Appended to {path}")
        else:
            print(format_output(messages, output_fmt))
    finally:
        await client.disconnect()


async def cmd_search(args):
    """Search messages."""
    from telegram_telethon.modules.messages import search_messages
    from telegram_telethon.utils.formatting import format_output, append_to_daily, save_to_file

    client = await get_client()
    try:
        messages = await search_messages(
            client, query=args.query, chat_id=args.chat_id,
            chat_name=args.chat, limit=args.limit,
        )
        output_fmt = "json" if args.json else "markdown"

        if args.output:
            result = save_to_file(messages, args.output, output_fmt)
            print(json.dumps(result, indent=2, ensure_ascii=False))
        elif args.to_daily:
            path = append_to_daily(format_output(messages, output_fmt))
            print(f"Appended to {path}")
        else:
            print(format_output(messages, output_fmt))
    finally:
        await client.disconnect()


async def cmd_unread(args):
    """Fetch unread messages."""
    from telegram_telethon.modules.messages import fetch_unread
    from telegram_telethon.utils.formatting import format_output, append_to_daily

    client = await get_client()
    try:
        messages = await fetch_unread(client, chat_id=args.chat_id)
        output_fmt = "json" if args.json else "markdown"

        if args.to_daily:
            path = append_to_daily(format_output(messages, output_fmt))
            print(f"Appended to {path}")
        else:
            print(format_output(messages, output_fmt))
    finally:
        await client.disconnect()


async def cmd_thread(args):
    """Fetch thread messages."""
    from telegram_telethon.modules.messages import fetch_thread
    from telegram_telethon.utils.formatting import format_output, save_to_file

    client = await get_client()
    try:
        messages = await fetch_thread(client, chat_id=args.chat_id, thread_id=args.thread_id, limit=args.limit)
        output_fmt = "json" if args.json else "markdown"

        if args.output:
            result = save_to_file(messages, args.output, output_fmt)
            print(json.dumps(result, indent=2, ensure_ascii=False))
        else:
            print(format_output(messages, output_fmt))
    finally:
        await client.disconnect()


async def cmd_send(args):
    """Send a message."""
    from telegram_telethon.modules.messages import send_message

    client = await get_client()
    try:
        config = Config.load(DEFAULT_CONFIG_DIR / "config.yaml")
        allowed_groups = config.allowed_send_groups

        reply_to = args.topic if args.topic else args.reply_to
        result = await send_message(
            client, chat_name=args.chat, text=args.text or "",
            reply_to=reply_to, file_path=args.file, allowed_groups=allowed_groups,
        )
        print(json.dumps(result, indent=2, ensure_ascii=False))
    finally:
        await client.disconnect()


async def cmd_delete(args):
    """Delete messages."""
    from telegram_telethon.modules.messages import delete_messages

    client = await get_client()
    try:
        result = await delete_messages(
            client, chat_name=args.chat, message_ids=args.message_ids,
            revoke=not args.no_revoke,
        )
        print(json.dumps(result, indent=2, ensure_ascii=False))
    finally:
        await client.disconnect()


async def cmd_forward(args):
    """Forward messages."""
    from telegram_telethon.modules.messages import forward_messages

    client = await get_client()
    try:
        result = await forward_messages(
            client, from_chat=args.from_chat, to_chat=args.to_chat,
            message_ids=args.message_ids,
        )
        print(json.dumps(result, indent=2, ensure_ascii=False))
    finally:
        await client.disconnect()


async def cmd_mark_read(args):
    """Mark messages as read."""
    from telegram_telethon.modules.messages import mark_read

    client = await get_client()
    try:
        result = await mark_read(client, chat_name=args.chat, max_id=args.max_id)
        print(json.dumps(result, indent=2, ensure_ascii=False))
    finally:
        await client.disconnect()


async def cmd_edit(args):
    """Edit a message."""
    from telegram_telethon.modules.messages import edit_message

    client = await get_client()
    try:
        result = await edit_message(client, chat_name=args.chat, message_id=args.message_id, text=args.text)
        print(json.dumps(result, indent=2, ensure_ascii=False))
    finally:
        await client.disconnect()


async def cmd_download(args):
    """Download media."""
    from telegram_telethon.modules.media import download_media

    client = await get_client()
    try:
        results = await download_media(
            client, chat_name=args.chat, limit=args.limit,
            output_dir=args.output, message_id=args.message_id,
            media_type=args.type,
        )
        print(json.dumps(results, indent=2, ensure_ascii=False))
    finally:
        await client.disconnect()


async def cmd_transcribe(args):
    """Transcribe voice messages."""
    from telegram_telethon.modules.media import transcribe_voice, transcribe_batch

    client = await get_client()
    try:
        groq_key = args.groq_key or os.environ.get("GROQ_API_KEY")

        if args.message_id:
            result = await transcribe_voice(
                client, chat_name=args.chat, message_id=args.message_id,
                fallback_method=args.fallback, groq_api_key=groq_key,
            )
            print(json.dumps({
                "success": result.success,
                "text": result.text,
                "method": result.method,
                "error": result.error,
            }, indent=2, ensure_ascii=False))
        else:
            results = await transcribe_batch(
                client, chat_name=args.chat, limit=args.limit,
                fallback_method=args.fallback, groq_api_key=groq_key,
            )
            print(json.dumps(results, indent=2, ensure_ascii=False))
    finally:
        await client.disconnect()


def main():
    parser = argparse.ArgumentParser(description="Telegram Telethon CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Setup
    setup_p = subparsers.add_parser("setup", help="Run setup wizard")
    setup_p.add_argument("--api-id", type=int, help="Telegram API ID (for non-interactive)")
    setup_p.add_argument("--api-hash", help="Telegram API hash (for non-interactive)")
    setup_p.add_argument("--phone", help="Phone number with country code (for non-interactive)")
    setup_p.add_argument("--code", help="Verification code from Telegram")
    setup_p.add_argument("--password", help="2FA password if enabled")

    subparsers.add_parser("status", help="Show connection status")
    subparsers.add_parser("daemon-config", help="Configure daemon triggers")

    # List chats
    list_p = subparsers.add_parser("list", help="List chats")
    list_p.add_argument("--limit", type=int, default=30, help="Max chats")
    list_p.add_argument("--search", help="Filter by name")
    list_p.add_argument("--json", action="store_true", help="JSON output")

    # Recent messages
    recent_p = subparsers.add_parser("recent", help="Fetch recent messages")
    recent_p.add_argument("--chat", help="Chat name")
    recent_p.add_argument("--chat-id", type=int, help="Chat ID")
    recent_p.add_argument("--limit", type=int, default=50, help="Max messages")
    recent_p.add_argument("--days", type=int, help="Only last N days")
    recent_p.add_argument("--json", action="store_true", help="JSON output")
    recent_p.add_argument("--to-daily", action="store_true", help="Append to daily note")
    recent_p.add_argument("--to-person", help="Append to person's note")
    recent_p.add_argument("-o", "--output", help="Save to file")

    # Search
    search_p = subparsers.add_parser("search", help="Search messages")
    search_p.add_argument("query", help="Search query")
    search_p.add_argument("--chat", help="Chat name")
    search_p.add_argument("--chat-id", type=int, help="Chat ID")
    search_p.add_argument("--limit", type=int, default=50, help="Max results")
    search_p.add_argument("--json", action="store_true", help="JSON output")
    search_p.add_argument("--to-daily", action="store_true", help="Append to daily note")
    search_p.add_argument("-o", "--output", help="Save to file")

    # Unread
    unread_p = subparsers.add_parser("unread", help="Fetch unread messages")
    unread_p.add_argument("--chat-id", type=int, help="Limit to chat")
    unread_p.add_argument("--json", action="store_true", help="JSON output")
    unread_p.add_argument("--to-daily", action="store_true", help="Append to daily note")

    # Thread
    thread_p = subparsers.add_parser("thread", help="Fetch forum thread")
    thread_p.add_argument("--chat-id", type=int, required=True, help="Chat ID")
    thread_p.add_argument("--thread-id", type=int, required=True, help="Thread ID")
    thread_p.add_argument("--limit", type=int, default=100, help="Max messages")
    thread_p.add_argument("--json", action="store_true", help="JSON output")
    thread_p.add_argument("-o", "--output", help="Save to file")

    # Send
    send_p = subparsers.add_parser("send", help="Send message")
    send_p.add_argument("--chat", required=True, help="Chat name, @username, or ID")
    send_p.add_argument("--text", help="Message text")
    send_p.add_argument("--file", help="File to send")
    send_p.add_argument("--reply-to", type=int, help="Reply to message ID")
    send_p.add_argument("--topic", type=int, help="Forum topic ID")

    # Edit
    edit_p = subparsers.add_parser("edit", help="Edit message")
    edit_p.add_argument("--chat", required=True, help="Chat")
    edit_p.add_argument("--message-id", type=int, required=True, help="Message ID")
    edit_p.add_argument("--text", required=True, help="New text")

    # Delete
    del_p = subparsers.add_parser("delete", help="Delete messages")
    del_p.add_argument("--chat", required=True, help="Chat")
    del_p.add_argument("--message-ids", type=int, nargs="+", required=True, help="Message IDs to delete")
    del_p.add_argument("--no-revoke", action="store_true", help="Don't delete for everyone")

    # Forward
    fwd_p = subparsers.add_parser("forward", help="Forward messages")
    fwd_p.add_argument("--from", dest="from_chat", required=True, help="Source chat")
    fwd_p.add_argument("--to", dest="to_chat", required=True, help="Destination chat")
    fwd_p.add_argument("--message-ids", type=int, nargs="+", required=True, help="Message IDs")

    # Mark read
    read_p = subparsers.add_parser("mark-read", help="Mark messages as read")
    read_p.add_argument("--chat", required=True, help="Chat")
    read_p.add_argument("--max-id", type=int, help="Mark up to this message ID")

    # Download
    dl_p = subparsers.add_parser("download", help="Download media")
    dl_p.add_argument("--chat", required=True, help="Chat")
    dl_p.add_argument("--limit", type=int, default=5, help="Max files")
    dl_p.add_argument("--output", "-o", help="Output directory")
    dl_p.add_argument("--message-id", type=int, help="Specific message")
    dl_p.add_argument("--type", choices=["voice", "video", "photo", "document"], help="Filter by type")

    # Transcribe
    tr_p = subparsers.add_parser("transcribe", help="Transcribe voice messages")
    tr_p.add_argument("--chat", required=True, help="Chat")
    tr_p.add_argument("--message-id", type=int, help="Specific message (omit for batch)")
    tr_p.add_argument("--limit", type=int, default=10, help="Max messages for batch")
    tr_p.add_argument("--fallback", choices=["groq", "whisper", "none"], default="groq", help="Fallback method")
    tr_p.add_argument("--groq-key", help="Groq API key (or set GROQ_API_KEY)")

    args = parser.parse_args()

    if args.command == "setup":
        setup_wizard(
            api_id=args.api_id,
            api_hash=args.api_hash,
            phone=args.phone,
            code=args.code,
            password=args.password,
        )
    elif args.command == "status":
        show_status()
    elif args.command == "daemon-config":
        setup_daemon_config()
    elif args.command == "list":
        asyncio.run(cmd_list(args))
    elif args.command == "recent":
        asyncio.run(cmd_recent(args))
    elif args.command == "search":
        asyncio.run(cmd_search(args))
    elif args.command == "unread":
        asyncio.run(cmd_unread(args))
    elif args.command == "thread":
        asyncio.run(cmd_thread(args))
    elif args.command == "send":
        asyncio.run(cmd_send(args))
    elif args.command == "edit":
        asyncio.run(cmd_edit(args))
    elif args.command == "delete":
        asyncio.run(cmd_delete(args))
    elif args.command == "forward":
        asyncio.run(cmd_forward(args))
    elif args.command == "mark-read":
        asyncio.run(cmd_mark_read(args))
    elif args.command == "download":
        asyncio.run(cmd_download(args))
    elif args.command == "transcribe":
        asyncio.run(cmd_transcribe(args))


if __name__ == "__main__":
    main()
