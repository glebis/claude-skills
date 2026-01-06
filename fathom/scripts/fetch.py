#!/usr/bin/env python3
"""
Fathom meeting fetcher CLI.

Fetches meetings, transcripts, summaries, and action items from Fathom API.
"""

import argparse
import sys
import subprocess
from pathlib import Path
from datetime import date

from utils import FathomClient, format_meeting_markdown, meeting_filename

# Default output directory (Obsidian vault)
DEFAULT_OUTPUT = Path.home() / 'Brains' / 'brain'
TRANSCRIPT_ANALYZER = Path.home() / '.claude' / 'skills' / 'transcript-analyzer' / 'scripts'


def list_meetings(client: FathomClient, limit: int = 10):
    """List recent meetings."""
    meetings = client.list_meetings(limit=limit, include_transcript=False)

    if not meetings:
        print("No meetings found.")
        return

    print(f"\n{'ID':<40} {'Date':<12} {'Title'}")
    print("-" * 80)

    for m in meetings:
        mid = str(m.get('recording_id', ''))
        created = m.get('created_at', '')[:10]
        title = (m.get('meeting_title') or m.get('title', 'Untitled'))[:40]
        print(f"{mid:<40} {created:<12} {title}")


def fetch_meeting(client: FathomClient, recording_id: str, output_dir: Path, analyze: bool = False):
    """Fetch a specific meeting and save to file."""
    print(f"Fetching meeting {recording_id}...")

    # Get meeting with transcript
    meetings = client.list_meetings(include_transcript=True, limit=100)
    meeting = None
    for m in meetings:
        if str(m.get('recording_id')) == recording_id or recording_id in m.get('url', ''):
            meeting = m
            break

    if not meeting:
        print(f"Meeting {recording_id} not found")
        return None

    # Try to get additional summary if available
    try:
        summary = client.get_summary(recording_id)
    except:
        summary = None

    # Format and save
    markdown = format_meeting_markdown(meeting, summary=summary)
    filename = meeting_filename(meeting)
    output_path = output_dir / filename

    output_path.write_text(markdown)
    print(f"Saved: {output_path}")

    # Optionally run transcript analyzer
    if analyze:
        run_analyzer(output_path, output_dir)

    return output_path


def fetch_today(client: FathomClient, output_dir: Path, analyze: bool = False):
    """Fetch all meetings from today."""
    today = date.today().isoformat()
    print(f"Fetching meetings from {today}...")

    meetings = client.list_meetings(created_after=today, include_transcript=True)

    if not meetings:
        print("No meetings found for today.")
        return []

    saved = []
    for meeting in meetings:
        markdown = format_meeting_markdown(meeting)
        filename = meeting_filename(meeting)
        output_path = output_dir / filename

        output_path.write_text(markdown)
        print(f"Saved: {output_path}")
        saved.append(output_path)

        if analyze:
            run_analyzer(output_path, output_dir)

    return saved


def fetch_since(client: FathomClient, since_date: str, output_dir: Path, analyze: bool = False):
    """Fetch all meetings since a date."""
    print(f"Fetching meetings since {since_date}...")

    meetings = client.list_meetings(created_after=since_date, include_transcript=True)

    if not meetings:
        print(f"No meetings found since {since_date}.")
        return []

    saved = []
    for meeting in meetings:
        markdown = format_meeting_markdown(meeting)
        filename = meeting_filename(meeting)
        output_path = output_dir / filename

        output_path.write_text(markdown)
        print(f"Saved: {output_path}")
        saved.append(output_path)

        if analyze:
            run_analyzer(output_path, output_dir)

    return saved


def run_analyzer(transcript_path: Path, output_dir: Path):
    """Run transcript-analyzer on a transcript file."""
    if not TRANSCRIPT_ANALYZER.exists():
        print("transcript-analyzer skill not found, skipping analysis")
        return

    analysis_name = transcript_path.stem + '-analysis.md'
    analysis_path = output_dir / 'Projects' / analysis_name

    print(f"Running transcript analysis...")
    try:
        subprocess.run(
            ['npm', 'run', 'cli', '--', str(transcript_path), '-o', str(analysis_path)],
            cwd=str(TRANSCRIPT_ANALYZER),
            check=True,
            capture_output=True
        )
        print(f"Analysis saved: {analysis_path}")
    except subprocess.CalledProcessError as e:
        print(f"Analysis failed: {e}")
    except FileNotFoundError:
        print("npm not found, skipping analysis")


def main():
    parser = argparse.ArgumentParser(
        description='Fetch meetings from Fathom API',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python fetch.py --list                    # List recent meetings
  python fetch.py --id abc123               # Fetch specific meeting
  python fetch.py --today                   # Fetch all today's meetings
  python fetch.py --since 2025-01-01        # Fetch since date
  python fetch.py --today --analyze         # Fetch and analyze
        """
    )

    parser.add_argument('--list', action='store_true', help='List recent meetings')
    parser.add_argument('--id', type=str, help='Fetch specific meeting by recording ID')
    parser.add_argument('--today', action='store_true', help='Fetch all meetings from today')
    parser.add_argument('--since', type=str, help='Fetch meetings since date (YYYY-MM-DD)')
    parser.add_argument('--analyze', action='store_true', help='Run transcript-analyzer on fetched meetings')
    parser.add_argument('--output', '-o', type=str, default=str(DEFAULT_OUTPUT),
                        help=f'Output directory (default: {DEFAULT_OUTPUT})')
    parser.add_argument('--limit', type=int, default=10, help='Max meetings to list (default: 10)')

    args = parser.parse_args()
    output_dir = Path(args.output)

    if not output_dir.exists():
        print(f"Output directory does not exist: {output_dir}")
        sys.exit(1)

    try:
        client = FathomClient()
    except ValueError as e:
        print(f"Error: {e}")
        sys.exit(1)

    if args.list:
        list_meetings(client, limit=args.limit)
    elif args.id:
        fetch_meeting(client, args.id, output_dir, analyze=args.analyze)
    elif args.today:
        fetch_today(client, output_dir, analyze=args.analyze)
    elif args.since:
        fetch_since(client, args.since, output_dir, analyze=args.analyze)
    else:
        # Default: list meetings
        list_meetings(client, limit=args.limit)


if __name__ == '__main__':
    main()
