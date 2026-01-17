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
VIDEO_DOWNLOADER = Path(__file__).parent / 'download_video.py'


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


def fetch_meeting(client: FathomClient, recording_id: str, output_dir: Path, analyze: bool = False, download_vid: bool = False):
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

    # Optionally download video
    if download_vid:
        share_url = meeting.get('share_url', '')
        if share_url:
            download_video(share_url, output_path)
        else:
            print("No share_url found for video download")

    # Optionally run transcript analyzer
    if analyze:
        run_analyzer(output_path, output_dir)

    return output_path


def fetch_today(client: FathomClient, output_dir: Path, analyze: bool = False, download_vid: bool = False):
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

        if download_vid:
            share_url = meeting.get('share_url', '')
            if share_url:
                download_video(share_url, output_path)

        if analyze:
            run_analyzer(output_path, output_dir)

    return saved


def fetch_since(client: FathomClient, since_date: str, output_dir: Path, analyze: bool = False, download_vid: bool = False):
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

        if download_vid:
            share_url = meeting.get('share_url', '')
            if share_url:
                download_video(share_url, output_path)

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


def verify_video(video_path: Path) -> bool:
    """Verify video file is valid using ffprobe."""
    try:
        result = subprocess.run(
            ['ffprobe', '-v', 'error', '-show_format', '-show_streams', str(video_path)],
            capture_output=True,
            timeout=10
        )
        return result.returncode == 0
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired, FileNotFoundError):
        return False


def download_video(share_url: str, output_path: Path, max_retries: int = 3):
    """Download video using fathom video downloader with validation and retry."""
    if not VIDEO_DOWNLOADER.exists():
        print("Video downloader not found, skipping video download")
        return

    # Generate output filename based on meeting markdown filename
    video_filename = output_path.stem + '.mp4'
    video_path = output_path.parent / video_filename

    for attempt in range(1, max_retries + 1):
        print(f"Downloading video from {share_url}... (attempt {attempt}/{max_retries})")

        # Remove corrupted file if exists
        if video_path.exists():
            video_path.unlink()

        try:
            subprocess.run(
                ['python3', str(VIDEO_DOWNLOADER), share_url, '--output-name', str(video_path.stem)],
                cwd=str(output_path.parent),
                check=True,
                timeout=1800  # 30 minute timeout
            )

            # Verify the downloaded video
            if video_path.exists() and verify_video(video_path):
                print(f"Video saved and verified: {video_path}")
                return
            else:
                print(f"Video verification failed (attempt {attempt}/{max_retries})")

        except subprocess.CalledProcessError as e:
            print(f"Video download failed: {e}")
        except subprocess.TimeoutExpired:
            print(f"Video download timed out (attempt {attempt}/{max_retries})")
        except FileNotFoundError:
            print("python3 not found, skipping video download")
            return

    print(f"Failed to download valid video after {max_retries} attempts")


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
  python fetch.py --id abc123 --download-video  # Fetch meeting and download video
        """
    )

    parser.add_argument('--list', action='store_true', help='List recent meetings')
    parser.add_argument('--id', type=str, help='Fetch specific meeting by recording ID')
    parser.add_argument('--today', action='store_true', help='Fetch all meetings from today')
    parser.add_argument('--since', type=str, help='Fetch meetings since date (YYYY-MM-DD)')
    parser.add_argument('--analyze', action='store_true', help='Run transcript-analyzer on fetched meetings')
    parser.add_argument('--download-video', action='store_true', help='Download video recording (requires ffmpeg)')
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
        fetch_meeting(client, args.id, output_dir, analyze=args.analyze, download_vid=args.download_video)
    elif args.today:
        fetch_today(client, output_dir, analyze=args.analyze, download_vid=args.download_video)
    elif args.since:
        fetch_since(client, args.since, output_dir, analyze=args.analyze, download_vid=args.download_video)
    else:
        # Default: list meetings
        list_meetings(client, limit=args.limit)


if __name__ == '__main__':
    main()
