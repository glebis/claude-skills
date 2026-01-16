#!/usr/bin/env python3
"""Daemon CLI for telegram-telethon.

Controls the background daemon process.
"""
import asyncio
import logging
import sys
from pathlib import Path

# Add src to path for development
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import argparse

from telegram_telethon.core.config import DEFAULT_CONFIG_DIR
from telegram_telethon.daemon.runner import run_daemon


def setup_logging(foreground: bool = False, log_file: Path = None):
    """Configure logging."""
    handlers = []

    if foreground:
        handlers.append(logging.StreamHandler(sys.stdout))

    if log_file:
        log_file.parent.mkdir(parents=True, exist_ok=True)
        handlers.append(logging.FileHandler(log_file))

    if not handlers:
        handlers.append(logging.StreamHandler(sys.stdout))

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=handlers,
    )


def cmd_start(args):
    """Start the daemon."""
    log_file = None
    if not args.foreground:
        log_file = DEFAULT_CONFIG_DIR / "daemon.log"

    setup_logging(foreground=args.foreground, log_file=log_file)

    print("Starting daemon...")
    if not args.foreground:
        print(f"Logs: {log_file}")
        print("Press Ctrl+C to stop")

    try:
        asyncio.run(run_daemon(
            config_dir=DEFAULT_CONFIG_DIR,
        ))
    except KeyboardInterrupt:
        print("\nStopped.")


def cmd_status(args):
    """Show daemon status."""
    # Check if daemon is running (simple check via PID file or process)
    print("Daemon status: Not implemented yet")
    print("Use 'tg.py status' for connection status")


def cmd_logs(args):
    """Tail daemon logs."""
    log_file = DEFAULT_CONFIG_DIR / "daemon.log"

    if not log_file.exists():
        print(f"No log file found at {log_file}")
        print("Start daemon first with: tgd.py start")
        return

    import subprocess
    try:
        subprocess.run(["tail", "-f", "-n", str(args.lines), str(log_file)])
    except KeyboardInterrupt:
        pass


def main():
    parser = argparse.ArgumentParser(description="Telegram Daemon CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Start
    start_parser = subparsers.add_parser("start", help="Start daemon")
    start_parser.add_argument(
        "--foreground", "-f",
        action="store_true",
        help="Run in foreground (logs to stdout)"
    )
    start_parser.set_defaults(func=cmd_start)

    # Status
    status_parser = subparsers.add_parser("status", help="Show daemon status")
    status_parser.set_defaults(func=cmd_status)

    # Logs
    logs_parser = subparsers.add_parser("logs", help="Tail daemon logs")
    logs_parser.add_argument(
        "--lines", "-n",
        type=int,
        default=50,
        help="Number of lines to show"
    )
    logs_parser.set_defaults(func=cmd_logs)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
