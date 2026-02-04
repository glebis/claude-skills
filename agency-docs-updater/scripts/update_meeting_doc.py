#!/usr/bin/env python3
"""
Update agency-docs meeting documentation.
Creates/updates meeting MDX files with Fathom links, YouTube embeds, fact-checked summaries, and presentations.
"""

import os
import sys
import re
import json
import argparse
from pathlib import Path
from typing import Dict, Optional


def parse_fathom_frontmatter(fathom_file: str) -> Dict:
    """Extract Fathom meeting URL and metadata from frontmatter."""
    with open(fathom_file, 'r', encoding='utf-8') as f:
        content = f.read()

    # Parse frontmatter
    parts = content.split('---')
    if len(parts) < 3:
        raise ValueError("Invalid Fathom transcript format - missing frontmatter")

    frontmatter = parts[1].strip()
    metadata = {}
    for line in frontmatter.split('\n'):
        if ':' in line:
            key, value = line.split(':', 1)
            metadata[key.strip()] = value.strip().strip('"\'[]')

    return metadata


def extract_lab_number(fathom_file: str) -> str:
    """Extract lab number from Fathom transcript filename."""
    # Pattern: YYYYMMDD-claude-code-lab-XX.md
    filename = os.path.basename(fathom_file)
    match = re.search(r'claude-code-lab-(\d+)', filename)
    if not match:
        raise ValueError(f"Could not extract lab number from filename: {filename}")
    return match.group(1).zfill(2)


def find_presentation_file(lab_number: str) -> Optional[str]:
    """Find presentation markdown for lab number."""
    presentations_dir = Path.home() / 'ai_projects' / 'claude-code-lab' / 'presentations' / f'lab-{lab_number}'

    if not presentations_dir.exists():
        print(f"⚠️  Presentations directory not found: {presentations_dir}")
        return None

    # Find latest .md file (not .html)
    md_files = sorted(presentations_dir.glob('*.md'), key=lambda p: p.stat().st_mtime, reverse=True)

    # Filter out homework-prompt.md
    md_files = [f for f in md_files if 'homework-prompt' not in f.name.lower()]

    if md_files:
        return str(md_files[0])

    print(f"⚠️  No presentation markdown found in {presentations_dir}")
    return None


def determine_meeting_number(docs_dir: str) -> str:
    """Determine next meeting number from existing files."""
    meetings_dir = Path(docs_dir) / 'meetings'

    if not meetings_dir.exists():
        return "01"

    # Find all XX.mdx files
    existing = [f.stem for f in meetings_dir.glob('*.mdx') if f.stem.isdigit()]

    if not existing:
        return "01"

    # Return max + 1
    max_num = max(int(n) for n in existing)
    return str(max_num + 1).zfill(2)


def create_meeting_doc(
    meeting_number: str,
    fathom_url: str,
    youtube_url: str,
    summary: str,
    presentation_content: Optional[str],
    docs_dir: str
) -> str:
    """Create meeting MDX document."""

    # Extract YouTube video ID
    youtube_id = youtube_url.split('/')[-1].split('?v=')[-1].split('&')[0]

    # Build content
    content = f"""---
title: "Встреча {meeting_number}: [Название встречи]"
description: [Краткое описание встречи]
---

**Дата:** [Дата встречи] | **Длительность:** ~2 часа

## Видео

**Fathom:** [Запись на Fathom]({fathom_url})

**YouTube:** [Смотреть на YouTube]({youtube_url})

<iframe width="560" height="315" src="https://www.youtube.com/embed/{youtube_id}" frameBorder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture" allowFullScreen></iframe>

---

## Краткое содержание

{summary}

---
"""

    # Append presentation if available
    if presentation_content:
        # Remove frontmatter from presentation
        presentation_lines = presentation_content.split('\n')
        if presentation_lines[0].strip() == '---':
            # Find end of frontmatter
            end_idx = presentation_lines[1:].index('---') + 2 if '---' in presentation_lines[1:] else 0
            presentation_content = '\n'.join(presentation_lines[end_idx:]).strip()

        content += f"\n{presentation_content}\n"

    # Write file
    output_file = Path(docs_dir) / 'meetings' / f'{meeting_number}.mdx'
    output_file.parent.mkdir(parents=True, exist_ok=True)

    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(content)

    return str(output_file)


def detect_language(text: str) -> str:
    """Detect if text is primarily Russian or English."""
    # Count Cyrillic characters
    cyrillic_count = sum(1 for char in text if '\u0400' <= char <= '\u04FF')
    total_alpha = sum(1 for char in text if char.isalpha())

    if total_alpha == 0:
        return 'en'

    cyrillic_ratio = cyrillic_count / total_alpha
    return 'ru' if cyrillic_ratio > 0.3 else 'en'


def translate_summary_to_russian(summary: str) -> str:
    """Translate English summary to Russian using Task agent."""
    import subprocess
    import tempfile

    print("⚙️  Translating summary to Russian...")

    # Create temp file with translation prompt
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as f:
        f.write(summary)
        temp_input = f.name

    try:
        # Use claude to translate
        result = subprocess.run([
            'claude', '-p',
            f'''Translate this meeting summary to Russian. Keep all technical terms in English (MCP, Skills, Claude Code, YOLO, vibe coding, etc.). Preserve all markdown formatting, code examples, paths, and table structures.

Input file: {temp_input}

Output the translated text directly.''',
            '--output-format', 'text'
        ], capture_output=True, text=True, encoding='utf-8')

        if result.returncode == 0:
            return result.stdout.strip()
        else:
            print(f"⚠️  Translation failed: {result.stderr}")
            return summary
    finally:
        os.unlink(temp_input)


def main():
    parser = argparse.ArgumentParser(
        description='Update agency-docs meeting documentation',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  # Auto-detect meeting number and language
  python3 update_meeting_doc.py transcript.md https://youtube.com/watch?v=abc summary.md

  # Specify meeting number
  python3 update_meeting_doc.py transcript.md https://youtube.com/watch?v=abc summary.md -n 07

  # Force Russian translation
  python3 update_meeting_doc.py transcript.md https://youtube.com/watch?v=abc summary.md -l ru

  # Update existing meeting with new summary
  python3 update_meeting_doc.py transcript.md https://youtube.com/watch?v=abc summary.md -n 07 --update
        '''
    )

    parser.add_argument('fathom_transcript', help='Path to Fathom transcript markdown file')
    parser.add_argument('youtube_url', help='YouTube video URL')
    parser.add_argument('summary_file', help='Path to summary markdown file')
    parser.add_argument('docs_dir', nargs='?', help='Target docs directory (optional, auto-detected)')
    parser.add_argument('-n', '--meeting-number', help='Specific meeting number (e.g., 07)')
    parser.add_argument('-l', '--language', choices=['en', 'ru', 'auto'], default='auto',
                        help='Summary language (auto-detect, en, or ru)')
    parser.add_argument('--update', action='store_true',
                        help='Update existing meeting file instead of creating new')

    args = parser.parse_args()

    # Parse Fathom frontmatter
    print(f"Parsing Fathom transcript: {args.fathom_transcript}")
    metadata = parse_fathom_frontmatter(args.fathom_transcript)
    fathom_url = metadata.get('meeting_url', metadata.get('url', metadata.get('fathom_url', '')))

    if not fathom_url:
        print("⚠️  Could not find Fathom URL in frontmatter (looking for 'meeting_url', 'url', or 'fathom_url')")
        sys.exit(1)

    # Extract lab number
    lab_number = extract_lab_number(args.fathom_transcript)
    print(f"✓ Detected lab number: {lab_number}")

    # Determine docs directory
    docs_dir = args.docs_dir
    if not docs_dir:
        docs_dir = str(Path.home() / 'Sites' / 'agency-docs' / 'content' / 'docs' / f'claude-code-internal-{lab_number}')

    print(f"✓ Target docs directory: {docs_dir}")

    # Determine meeting number
    if args.meeting_number:
        meeting_number = args.meeting_number.zfill(2)
        print(f"✓ Using specified meeting number: {meeting_number}")

        # Check if file exists
        meeting_file = Path(docs_dir) / 'meetings' / f'{meeting_number}.mdx'
        if meeting_file.exists() and not args.update:
            print(f"⚠️  Meeting file already exists: {meeting_file}")
            print("    Use --update flag to update existing file, or omit -n to create new meeting")
            sys.exit(1)
    else:
        meeting_number = determine_meeting_number(docs_dir)
        print(f"✓ Auto-detected meeting number: {meeting_number}")

    # Find presentation
    presentation_file = find_presentation_file(lab_number)
    presentation_content = None
    if presentation_file:
        print(f"✓ Found presentation: {presentation_file}")
        with open(presentation_file, 'r', encoding='utf-8') as f:
            presentation_content = f.read()
    else:
        print("ℹ️  No presentation found, continuing without")

    # Read summary
    with open(args.summary_file, 'r', encoding='utf-8') as f:
        summary = f.read()

    # Handle language detection and translation
    detected_lang = detect_language(summary)
    target_lang = args.language if args.language != 'auto' else 'ru'  # Default to Russian

    print(f"✓ Detected summary language: {detected_lang}")
    print(f"✓ Target language: {target_lang}")

    if detected_lang != target_lang and target_lang == 'ru':
        summary = translate_summary_to_russian(summary)

    # Create meeting doc
    output_file = create_meeting_doc(
        meeting_number,
        fathom_url,
        args.youtube_url,
        summary,
        presentation_content,
        docs_dir
    )

    action = "Updated" if args.update else "Created"
    print(f"\n✓ {action} meeting documentation: {output_file}")
    print(f"\nNext steps:")
    print(f"  1. Edit title and description in frontmatter")
    print(f"  2. cd {Path(docs_dir).parent.parent.parent}")
    print(f"  3. git add . && git commit -m '{action} meeting {meeting_number} documentation'")
    print(f"  4. git push")
    print(f"  5. Check Vercel deploy logs")


if __name__ == '__main__':
    main()
