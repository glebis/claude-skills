#!/usr/bin/env python3
"""
Extract YouTube video transcripts and metadata to Markdown format.
Saves to ~/Brains/brain/ with YAML frontmatter.
"""

import json
import subprocess
import sys
import re
from pathlib import Path
from datetime import datetime


def sanitize_filename(title):
    """Convert video title to safe filename."""
    # Remove invalid characters
    clean = re.sub(r'[<>:"/\\|?*]', '', title)
    # Replace spaces and limit length
    clean = clean.replace(' ', '_')
    return clean[:100]


def format_duration(seconds):
    """Convert seconds to HH:MM:SS format."""
    if not seconds:
        return "00:00:00"
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    return f"{h:02d}:{m:02d}:{s:02d}"


def format_timestamp(seconds):
    """Convert seconds to HH:MM:SS timestamp."""
    return format_duration(seconds)


def extract_metadata(url):
    """Extract video metadata using yt-dlp."""
    cmd = [
        'yt-dlp',
        '--dump-json',
        '--no-download',
        url
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise Exception(f"Failed to extract metadata: {result.stderr}")

    return json.loads(result.stdout)


def extract_subtitles(url, video_id):
    """Extract subtitles/transcript using yt-dlp. Tries English first, then Russian."""
    output_template = f'/tmp/{video_id}'

    # Try English first
    for lang in ['en', 'ru']:
        # Clean up any previous attempts
        for old_file in Path('/tmp').glob(f'{video_id}*.vtt'):
            old_file.unlink()

        cmd = [
            'yt-dlp',
            '--write-auto-subs',
            '--write-subs',
            '--sub-lang', lang,
            '--sub-format', 'vtt',
            '--skip-download',
            '-o', output_template,
            url
        ]

        subprocess.run(cmd, capture_output=True, text=True)

        # Try to find the subtitle file
        subtitle_files = list(Path('/tmp').glob(f'{video_id}*.vtt'))
        if subtitle_files:
            return subtitle_files[0], lang

    return None, None


def parse_vtt(vtt_path):
    """Parse VTT subtitle file to extract timestamps and text."""
    with open(vtt_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Remove WEBVTT header and metadata
    lines = content.split('\n')
    entries = []
    current_time = None
    current_text = []

    for line in lines:
        # Match timestamp line (00:00:05.000 --> 00:00:08.000)
        if '-->' in line:
            if current_time and current_text:
                entries.append((current_time, ' '.join(current_text)))
            # Extract start time
            current_time = line.split('-->')[0].strip()
            current_text = []
        elif line.strip() and not line.startswith('WEBVTT') and not line.isdigit():
            # Remove VTT formatting tags
            clean_text = re.sub(r'<[^>]+>', '', line)
            if clean_text.strip():
                current_text.append(clean_text.strip())

    # Add last entry
    if current_time and current_text:
        entries.append((current_time, ' '.join(current_text)))

    return entries


def deduplicate_entries(entries):
    """Remove entries that are prefixes of subsequent entries."""
    if not entries:
        return []

    deduplicated = []

    for idx in range(len(entries)):
        timestamp, text = entries[idx]

        # Check if this text is a prefix of any subsequent entry
        is_prefix = False
        for next_idx in range(idx + 1, min(idx + 5, len(entries))):
            _, next_text = entries[next_idx]

            if next_text.startswith(text) and len(next_text) > len(text):
                is_prefix = True
                break

        if not is_prefix:
            deduplicated.append((timestamp, text))

    return deduplicated


def group_by_chapters(transcript_entries, chapters):
    """Group transcript entries by video chapters."""
    if not chapters:
        return [("Transcript", transcript_entries)]

    grouped = []
    chapter_times = [(ch['start_time'], ch['title']) for ch in chapters]
    chapter_times.append((float('inf'), None))  # End marker

    for i, (start_time, title) in enumerate(chapter_times[:-1]):
        next_start = chapter_times[i + 1][0]

        # Filter transcript entries for this chapter
        chapter_entries = []
        for timestamp, text in transcript_entries:
            # Convert timestamp to seconds
            parts = timestamp.split(':')
            if len(parts) == 3:
                h, m, s = parts
                total_seconds = int(h) * 3600 + int(m) * 60 + float(s)
            else:
                m, s = parts
                total_seconds = int(m) * 60 + float(s)

            if start_time <= total_seconds < next_start:
                chapter_entries.append((timestamp, text))

        if chapter_entries:
            grouped.append((title, chapter_entries))

    return grouped if grouped else [("Transcript", transcript_entries)]


def create_markdown(metadata, transcript_entries):
    """Create Markdown document with YAML frontmatter."""
    # Extract metadata fields
    title = metadata.get('title', 'Unknown')
    channel = metadata.get('channel', metadata.get('uploader', 'Unknown'))
    url = metadata.get('webpage_url', '')
    upload_date = metadata.get('upload_date', '')
    if upload_date:
        upload_date = f"{upload_date[:4]}-{upload_date[4:6]}-{upload_date[6:]}"
    duration = format_duration(metadata.get('duration'))
    description = metadata.get('description', '').replace('\n', ' ').strip()
    tags = metadata.get('tags', [])
    view_count = metadata.get('view_count', 0)
    like_count = metadata.get('like_count', 0)
    chapters = metadata.get('chapters', [])

    # Build YAML frontmatter
    md = "---\n"
    md += f"title: \"{title}\"\n"
    md += f"channel: \"{channel}\"\n"
    md += f"url: {url}\n"
    md += f"upload_date: {upload_date}\n"
    md += f"duration: {duration}\n"
    md += f"description: \"{description[:500]}...\"\n"
    md += f"tags: {json.dumps(tags)}\n"
    md += f"view_count: {view_count}\n"
    md += f"like_count: {like_count}\n"
    md += "---\n\n"

    # Add title
    md += f"# {title}\n\n"

    # Group transcript by chapters
    grouped = group_by_chapters(transcript_entries, chapters)

    for chapter_title, entries in grouped:
        md += f"## {chapter_title}\n\n"

        for timestamp, text in entries:
            # Convert VTT timestamp (00:00:05.000) to simple format (00:00:05)
            simple_ts = timestamp.split('.')[0]
            md += f"**{simple_ts}** {text}\n\n"

    return md


def main():
    if len(sys.argv) < 2:
        print("Usage: python extract_transcript.py <youtube_url> [output_filename]")
        sys.exit(1)

    url = sys.argv[1]
    custom_filename = sys.argv[2] if len(sys.argv) > 2 else None

    print(f"Extracting metadata from {url}...")
    metadata = extract_metadata(url)

    video_id = metadata['id']
    title = metadata.get('title', 'Unknown')

    print(f"Extracting subtitles for: {title}")
    subtitle_file, lang = extract_subtitles(url, video_id)

    if not subtitle_file:
        print("No subtitles available for this video (tried English and Russian).")
        sys.exit(1)

    print(f"Found {lang} subtitles")

    print("Parsing transcript...")
    transcript_entries = parse_vtt(subtitle_file)

    print("Removing duplicates...")
    transcript_entries = deduplicate_entries(transcript_entries)

    print("Creating Markdown document...")
    markdown = create_markdown(metadata, transcript_entries)

    # Determine output path
    vault_path = Path.home() / "Brains" / "brain"
    if custom_filename:
        output_file = vault_path / custom_filename
    else:
        filename = sanitize_filename(title) + ".md"
        output_file = vault_path / filename

    # Ensure vault directory exists
    vault_path.mkdir(parents=True, exist_ok=True)

    # Write output
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(markdown)

    print(f"✓ Saved to: {output_file}")

    # Cleanup
    if subtitle_file.exists():
        subtitle_file.unlink()


if __name__ == '__main__':
    main()
