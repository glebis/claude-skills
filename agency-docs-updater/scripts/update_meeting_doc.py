#!/usr/bin/env python3
"""
Update agency-docs meeting documentation.
Creates/updates meeting MDX files with Fathom links, YouTube embeds, fact-checked summaries, and presentations.

Reads path configuration from .env file in skill root, with sensible defaults.
"""

import os
import sys
import re
import argparse
from pathlib import Path
from typing import Dict, Optional
from urllib.parse import urlparse, parse_qs


def load_env():
    """Load .env file from skill root if it exists."""
    env_file = Path(__file__).parent.parent / '.env'
    if env_file.exists():
        with open(env_file, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    value = os.path.expanduser(value.strip())
                    os.environ.setdefault(key.strip(), value)


def get_path(env_var: str, default_relative: str) -> Path:
    """Get a path from env var or fall back to ~/default_relative."""
    value = os.environ.get(env_var)
    if value:
        return Path(os.path.expanduser(value))
    return Path.home() / default_relative


VAULT_DIR = lambda: get_path('VAULT_DIR', 'Brains/brain')
DOCS_SITE_DIR = lambda: get_path('DOCS_SITE_DIR', 'Sites/agency-docs')
PRESENTATIONS_DIR = lambda: get_path('PRESENTATIONS_DIR', 'ai_projects/claude-code-lab')
GITHUB_REPO = lambda: os.environ.get('GITHUB_REPO', 'glebis/agency-docs')
SITE_DOMAIN = lambda: os.environ.get('SITE_DOMAIN', 'agency-lab.glebkalinin.com')
LAB_SLUG = lambda: os.environ.get('LAB_SLUG', 'claude-code')


def parse_fathom_frontmatter(fathom_file: str) -> Dict:
    """Extract Fathom meeting URL and metadata from frontmatter."""
    with open(fathom_file, 'r', encoding='utf-8') as f:
        content = f.read()

    parts = content.split('---')
    if len(parts) < 3:
        raise ValueError("Invalid Fathom transcript format - missing frontmatter")

    frontmatter = parts[1].strip()
    try:
        import yaml
        metadata = yaml.safe_load(frontmatter) or {}
    except ImportError:
        metadata = {}
        for line in frontmatter.split('\n'):
            if ':' in line:
                key, value = line.split(':', 1)
                metadata[key.strip()] = value.strip().strip('"\'')

    return metadata


def extract_lab_number(fathom_file: str) -> str:
    """Extract lab number from Fathom transcript filename."""
    filename = os.path.basename(fathom_file)
    match = re.search(rf'{re.escape(LAB_SLUG())}-lab-(\d+)', filename)
    if not match:
        # generic fallback: any "<slug>-lab-NN" filename
        match = re.search(r'lab-(\d+)', filename)
    if not match:
        # registry vault_names (e.g. "goal-driven-ai-{lab}" -> 20261010-goal-driven-ai-01.md)
        import lab_layout
        for pat in lab_layout.load_registry().get(LAB_SLUG(), {}).get("vault_names", []):
            if "{lab}" in pat:
                rx = re.escape(pat).replace(r"\{lab\}", r"(\d{1,3})") + r"\.md$"
                match = re.search(rx, filename)
                if match:
                    break
    if not match:
        raise ValueError(f"Could not extract lab number from filename: {filename} (pass --lab NN)")
    return match.group(1).zfill(2)


def extract_date(fathom_file: str) -> Optional[str]:
    """Extract the YYYYMMDD date from the Fathom transcript filename, if present."""
    match = re.search(r'(\d{8})', os.path.basename(fathom_file))
    return match.group(1) if match else None


def find_presentation_file(lab_number: str, date_str: Optional[str] = None) -> Optional[str]:
    """Find presentation markdown for a lab number.

    When date_str (YYYYMMDD) is given, only a presentation whose filename contains
    that date is matched — this prevents picking an unrelated deck from another
    meeting just because it was the most recently modified file in the lab dir.
    """
    presentations_dir = PRESENTATIONS_DIR() / 'presentations' / f'lab-{lab_number}'

    if not presentations_dir.exists():
        print(f"⚠️  Presentations directory not found: {presentations_dir}")
        return None

    md_files = sorted(presentations_dir.glob('*.md'), key=lambda p: p.stat().st_mtime, reverse=True)
    md_files = [f for f in md_files if 'homework-prompt' not in f.name.lower()]

    if date_str:
        dated = [f for f in md_files if date_str in f.name]
        if not dated:
            print(f"ℹ️  No presentation matching date {date_str} in {presentations_dir}; skipping presentation")
            return None
        md_files = dated

    if md_files:
        return str(md_files[0])

    print(f"⚠️  No presentation markdown found in {presentations_dir}")
    return None


def determine_meeting_number(docs_dir: str) -> str:
    """Determine next meeting number from existing files."""
    meetings_dir = meetings_path(docs_dir)

    if not meetings_dir.exists():
        return "01"

    existing = [f.stem for f in meetings_dir.glob('*.mdx') if f.stem.isdigit()]

    if not existing:
        return "01"

    max_num = max(int(n) for n in existing)
    return str(max_num + 1).zfill(2)


def meetings_path(docs_dir: str) -> Path:
    """Accept either a docs section directory or its meetings directory."""
    path = Path(docs_dir)
    return path if path.name == 'meetings' else path / 'meetings'


def youtube_id_of(youtube_url: str) -> str:
    parsed = urlparse(youtube_url)
    qs = parse_qs(parsed.query)
    if 'v' in qs:
        return qs['v'][0]
    if parsed.netloc == 'youtu.be':
        return parsed.path.lstrip('/')
    raise ValueError(f'Cannot extract video ID from URL: {youtube_url}')


def recording_block(youtube_url: str, fathom_url: str = '', lang: str = 'ru') -> str:
    """Recording section body (no heading) — shared by create and merge."""
    yid = youtube_id_of(youtube_url)
    watch = "Смотреть на YouTube" if lang == 'ru' else "Watch on YouTube"
    return (f'<iframe width="560" height="315" src="https://www.youtube.com/embed/{yid}" frameBorder="0" '
            'allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture" '
            f'allowFullScreen></iframe>\n\n[{watch}]({youtube_url})')


def create_meeting_doc(
    meeting_number: str,
    fathom_url: str,
    youtube_url: str,
    summary: str,
    presentation_content: Optional[str],
    docs_dir: str
) -> str:
    """Create meeting MDX document. Note: --update is a full overwrite, not a merge."""

    parsed = urlparse(youtube_url)
    qs = parse_qs(parsed.query)
    if 'v' in qs:
        youtube_id = qs['v'][0]
    elif parsed.netloc == 'youtu.be':
        youtube_id = parsed.path.lstrip('/')
    else:
        raise ValueError(f'Cannot extract video ID from URL: {youtube_url}')

    content = f"""---
title: "Встреча {meeting_number}: [Название встречи]"
description: [Краткое описание встречи]
---

**Дата:** [Дата встречи] | **Длительность:** ~2 часа

## Видео

{f"**Fathom:** [Запись на Fathom]({fathom_url})" if fathom_url else ""}

**YouTube:** [Смотреть на YouTube]({youtube_url})

<iframe width="560" height="315" src="https://www.youtube.com/embed/{youtube_id}" frameBorder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture" allowFullScreen></iframe>

---

## Краткое содержание

{summary}

---
"""

    if presentation_content:
        presentation_lines = presentation_content.split('\n')
        if presentation_lines[0].strip() == '---':
            end_idx = presentation_lines[1:].index('---') + 2 if '---' in presentation_lines[1:] else 0
            presentation_content = '\n'.join(presentation_lines[end_idx:]).strip()
        content += f"\n{presentation_content}\n"

    output_file = meetings_path(docs_dir) / f'{meeting_number}.mdx'
    output_file.parent.mkdir(parents=True, exist_ok=True)

    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(content)

    return str(output_file)


def detect_language(text: str) -> str:
    """Detect if text is primarily Russian or English."""
    cyrillic_count = sum(1 for char in text if 'Ѐ' <= char <= 'ӿ')
    total_alpha = sum(1 for char in text if char.isalpha())

    if total_alpha == 0:
        return 'en'

    cyrillic_ratio = cyrillic_count / total_alpha
    return 'ru' if cyrillic_ratio > 0.3 else 'en'


def translate_summary_to_russian(summary: str) -> str:
    """Translate English summary to Russian using Claude CLI."""
    import subprocess
    import tempfile

    print("⚙️  Translating summary to Russian...")

    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as f:
        f.write(summary)
        temp_input = f.name

    try:
        result = subprocess.run([
            'claude', '-p',
            f'Translate this meeting summary to Russian. Keep all technical terms in English '
            f'(MCP, Skills, Claude Code, YOLO, vibe coding, etc.). Preserve all markdown formatting, '
            f'code examples, paths, and table structures.\n\nInput file: {temp_input}\n\n'
            f'Output the translated text directly.',
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
    load_env()

    parser = argparse.ArgumentParser(
        description='Update agency-docs meeting documentation',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  python3 update_meeting_doc.py transcript.md https://youtube.com/watch?v=abc summary.md
  python3 update_meeting_doc.py transcript.md https://youtube.com/watch?v=abc summary.md -n 07
  python3 update_meeting_doc.py transcript.md https://youtube.com/watch?v=abc summary.md -n 07 --update
        '''
    )

    parser.add_argument('fathom_transcript', help='Path to Fathom transcript markdown file')
    parser.add_argument('youtube_url', help='YouTube video URL')
    parser.add_argument('summary_file', help='Path to summary markdown file')
    parser.add_argument('docs_dir', nargs='?', help='Target docs directory (auto-detected from env)')
    parser.add_argument('--lab', help='Lab/cohort number override (else parsed from filename)')
    parser.add_argument('-n', '--meeting-number', help='Specific meeting number (e.g., 07)')
    parser.add_argument('-l', '--language', choices=['en', 'ru', 'auto'], default='auto',
                        help='Summary language (auto-detect, en, or ru)')
    parser.add_argument('--update', action='store_true',
                        help='Kept for compatibility: existing files are always merged now')
    parser.add_argument('--overwrite', action='store_true',
                        help='Destructive full rewrite of an existing meeting file (old --update)')
    parser.add_argument('--title', help='Fills frontmatter title only if it is a placeholder')
    parser.add_argument('--description', help='Fills frontmatter description only if placeholder')
    parser.add_argument('--transcript-url', help='Public transcript link → managed transcript block')
    parser.add_argument('--dry-run', action='store_true', help='Merge: print diff, write nothing')

    args = parser.parse_args()

    print(f"Parsing Fathom transcript: {args.fathom_transcript}")
    metadata = parse_fathom_frontmatter(args.fathom_transcript)
    fathom_url = metadata.get('meeting_url', metadata.get('url', metadata.get('fathom_url', '')))

    if not fathom_url:
        # GDA 01 #02 (2026-10-17): Fathom didn't record; Zoom cloud + Wispr Flow did.
        # A recording without Fathom is normal now — the page just omits the Fathom link.
        print("ℹ️  No Fathom URL in frontmatter — continuing without a Fathom link (Zoom/Wispr source)")

    lab_number = args.lab.zfill(2) if args.lab else extract_lab_number(args.fathom_transcript)
    print(f"✓ Detected lab number: {lab_number}")

    import lab_layout
    docs_dir = args.docs_dir
    if not docs_dir:
        # Resolve through the labs.json registry (falls back to the legacy
        # {slug}-internal-{lab} scheme for unregistered labs).
        layout = lab_layout.resolve(LAB_SLUG(), lab=lab_number)
        docs_dir = str(DOCS_SITE_DIR() / layout['meetings_dir'])
        if not layout['registered']:
            print(f"  ! lab '{LAB_SLUG()}' not in labs.json — using legacy layout")

    print(f"✓ Target docs directory: {docs_dir}")

    if args.meeting_number:
        if not re.match(r'^\d{1,3}$', args.meeting_number):
            print(f'Error: invalid meeting number: {args.meeting_number}')
            sys.exit(1)
        meeting_number = args.meeting_number.zfill(2)
        print(f"✓ Using specified meeting number: {meeting_number}")

        meeting_file = meetings_path(docs_dir) / f'{meeting_number}.mdx'
        if meeting_file.exists():
            print(f"✓ Meeting file exists — {'overwriting' if args.overwrite else 'smart merge'}: {meeting_file}")
    else:
        meeting_number = determine_meeting_number(docs_dir)
        print(f"✓ Auto-detected meeting number: {meeting_number}")

        meeting_file = meetings_path(docs_dir) / f'{meeting_number}.mdx'
        if meeting_file.exists():
            print(f"✓ Meeting file exists — {'overwriting' if args.overwrite else 'smart merge'}: {meeting_file}")

    presentation_file = find_presentation_file(lab_number, extract_date(args.fathom_transcript))
    presentation_content = None
    if presentation_file:
        print(f"✓ Found presentation: {presentation_file}")
        with open(presentation_file, 'r', encoding='utf-8') as f:
            presentation_content = f.read()
    else:
        print("ℹ️  No presentation found, continuing without")

    with open(args.summary_file, 'r', encoding='utf-8') as f:
        summary = f.read()

    detected_lang = detect_language(summary)
    target_lang = args.language if args.language != 'auto' else 'ru'

    print(f"✓ Detected summary language: {detected_lang}")
    print(f"✓ Target language: {target_lang}")

    if detected_lang != target_lang and target_lang == 'ru':
        summary = translate_summary_to_russian(summary)

    if meeting_file.exists() and not args.overwrite:
        import merge_meeting_doc
        layout_info = lab_layout.resolve(LAB_SLUG(), lab=lab_number)
        lang = args.language if args.language != 'auto' else layout_info.get('lang', 'ru')
        blocks = {'recording': recording_block(args.youtube_url, fathom_url, lang), 'summary': summary}
        if args.transcript_url:
            label = "Полный транскрипт встречи" if lang == 'ru' else "Full meeting transcript"
            blocks['transcript'] = f"[{label}]({args.transcript_url})"
        updates = {k: v for k, v in (('title', args.title), ('description', args.description)) if v}
        old_text = meeting_file.read_text(encoding='utf-8')
        new_text, changes = merge_meeting_doc.merge(
            old_text, blocks, updates, lang,
            keep_frontmatter=layout_info.get('preserve_placeholder_frontmatter', False) and not updates)
        for c in changes:
            print(f"  merge: {c}")
        if args.dry_run:
            import difflib
            sys.stdout.writelines(difflib.unified_diff(old_text.splitlines(True), new_text.splitlines(True)))
            return
        meeting_file.write_text(new_text, encoding='utf-8')
        print(f"\n✓ Merged into existing meeting page: {meeting_file} (presentation content not appended)")
        return

    output_file = create_meeting_doc(
        meeting_number,
        fathom_url,
        args.youtube_url,
        summary,
        presentation_content,
        docs_dir
    )

    action = "Rewrote" if args.overwrite else "Created"
    print(f"\n✓ {action} meeting documentation: {output_file}")
    print(f"\nNext steps:")
    print(f"  1. Edit title and description in frontmatter")
    print(f"  2. cd {DOCS_SITE_DIR()}")
    print(f"  3. git add {Path(output_file).relative_to(DOCS_SITE_DIR())}")
    print(f"     git commit -m '{action} meeting {meeting_number} documentation'")
    print(f"  4. git push")
    print(f"  5. Check Vercel deploy logs")


if __name__ == '__main__':
    main()
