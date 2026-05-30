#!/usr/bin/env python3
"""
Coaching Session Summarizer

Extracts key insights, decisions, action items, and trail connections from
coaching session transcripts using LLM analysis.
"""

import anthropic
import argparse
import os
import sys
from pathlib import Path
import re
from datetime import datetime

# Centralized model — bump here when migrating. As of 2026-05 the previous
# pin (claude-sonnet-4-20250514) was deprecated (EOL 2026-06-15).
MODEL = os.environ.get("SUMMARIZER_MODEL", "claude-sonnet-4-6")

def load_transcript(file_path):
    """Load transcript content from markdown file."""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Extract frontmatter and transcript
    parts = content.split('---', 2)
    if len(parts) >= 3:
        frontmatter = parts[1]
        body = parts[2]
    else:
        frontmatter = ""
        body = content

    return frontmatter, body

def extract_transcript_only(body):
    """Extract just the transcript section, excluding summaries."""
    # Find transcript section
    transcript_match = re.search(r'## Transcript\s*\n(.*?)(?:\n## |$)', body, re.DOTALL)
    if transcript_match:
        return transcript_match.group(1).strip()
    return body.strip()

def get_previous_sessions(vault_path, current_session, participant_name):
    """Find previous coaching sessions with same participant."""
    vault = Path(vault_path)
    pattern = f"*{participant_name.lower().replace(' ', '-')}*.md"

    sessions = []
    for session_file in vault.glob(pattern):
        if 'coaching' in session_file.stem and session_file.name != current_session:
            sessions.append(session_file)

    # Sort by date (YYYYMMDD prefix)
    sessions.sort(key=lambda x: x.stem[:8] if x.stem[:8].isdigit() else '0')
    return sessions[-3:] if len(sessions) > 3 else sessions  # Last 3 sessions

def find_trails(vault_path):
    """Load all trail files for semantic matching."""
    trails_dir = Path(vault_path) / "Trails"
    if not trails_dir.exists():
        return []

    trails = []
    for trail_file in trails_dir.glob("Trail*.md"):
        with open(trail_file, 'r', encoding='utf-8') as f:
            content = f.read()
            # Extract title from filename
            title = trail_file.stem.replace('Trail - ', '')
            trails.append({
                'name': title,
                'file': trail_file.name,
                'preview': content[:500]  # First 500 chars for context
            })
    return trails

def quick_extract(client, transcript, mode="quick"):
    """Perform quick extraction of key elements."""

    system_prompt = """You are a coaching session analyst. Extract key information concisely and objectively.

Focus on:
1. Key Insights: Main realizations, breakthroughs, or important observations (3-5 items)
2. Decisions Made: Concrete choices or commitments the coachee made
3. Action Items: Specific next steps with implied urgency/timeline
4. Themes: Recurring topics or patterns

Be concise and use the coachee's authentic language where meaningful.
Output in markdown format with clear sections."""

    prompt = f"""Analyze this coaching session transcript and extract:

## Key Insights
- List 3-5 main realizations or important observations

## Decisions Made
- List concrete decisions or commitments

## Action Items
- List specific next steps (mark urgent items with [URGENT] prefix)

## Session Themes
- Note 2-3 recurring topics or patterns

Transcript:
{transcript}"""

    message = client.messages.create(
        model=MODEL,
        max_tokens=2000,
        system=system_prompt,
        messages=[{"role": "user", "content": prompt}]
    )

    return message.content[0].text

def deep_analysis(client, transcript, previous_sessions_summary, trails):
    """Perform deeper analysis with pattern detection and trail matching."""

    trails_context = "\n".join([f"- {t['name']}: {t['preview'][:200]}..." for t in trails])

    system_prompt = """You are a coaching session analyst performing deep analysis.

Focus on:
1. Patterns across sessions
2. Progress on previous commitments
3. Emotional/energy shifts
4. Connections to existing trails/projects
5. Potential obstacles or blockers

Be insightful while remaining objective."""

    prompt = f"""Perform deep analysis of this coaching session:

## Context
Previous sessions summary:
{previous_sessions_summary if previous_sessions_summary else "No previous sessions available"}

Available Trails (projects/areas of focus):
{trails_context if trails_context else "No trails found"}

## Analysis Required

1. **Pattern Detection**: What themes recur across sessions?
2. **Progress Assessment**: How has the coachee progressed on previous commitments?
3. **Trail Connections**: Which trails/projects are relevant to this session? (Use exact trail names)
4. **Energy/Motivation Markers**: Note shifts in energy, enthusiasm, or resistance
5. **Potential Obstacles**: What might block progress?

Transcript:
{transcript}

Provide analysis in markdown with clear sections."""

    message = client.messages.create(
        model=MODEL,
        max_tokens=3000,
        system=system_prompt,
        messages=[{"role": "user", "content": prompt}]
    )

    return message.content[0].text

def match_trails(client, summary, trails):
    """Match session content to relevant trails."""
    if not trails:
        return []

    trails_list = "\n".join([f"- {t['name']}" for t in trails])

    prompt = f"""Based on this session summary, identify the 2-4 most relevant trails (projects/focus areas):

Available Trails:
{trails_list}

Session Summary:
{summary}

Output ONLY the trail names, one per line, no explanations."""

    message = client.messages.create(
        model=MODEL,
        max_tokens=500,
        messages=[{"role": "user", "content": prompt}]
    )

    matched = [line.strip('- ').strip() for line in message.content[0].text.split('\n') if line.strip()]
    return matched

def format_output(frontmatter, quick_summary, deep_summary=None, matched_trails=None):
    """Format the final output with enhanced frontmatter and sections."""

    # Parse existing frontmatter
    fm_dict = {}
    for line in frontmatter.split('\n'):
        if ':' in line:
            key, value = line.split(':', 1)
            fm_dict[key.strip()] = value.strip()

    # Add trails if matched
    if matched_trails:
        trails_links = '\n  - '.join([f'"[[Trails/Trail - {t}|{t}]]"' for t in matched_trails])
        fm_dict['trails'] = f'\n  - {trails_links}'

    # Reconstruct frontmatter
    new_fm = "---\n"
    for key, value in fm_dict.items():
        new_fm += f"{key}: {value}\n"
    new_fm += "---\n\n"

    # Build output
    output = new_fm
    output += "## AI-Generated Summary\n\n"
    output += f"*Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}*\n\n"
    output += quick_summary

    if deep_summary:
        output += "\n\n## Deep Analysis\n\n"
        output += deep_summary

    if matched_trails:
        output += "\n\n## Connected Trails\n\n"
        for trail in matched_trails:
            output += f"- [[Trails/Trail - {trail}|{trail}]]\n"

    return output

def main():
    parser = argparse.ArgumentParser(description='Summarize coaching session transcript')
    parser.add_argument('transcript_file', help='Path to transcript markdown file')
    parser.add_argument('--vault', default=os.path.expanduser('~/Brains/brain'),
                       help='Path to Obsidian vault')
    parser.add_argument('--mode', choices=['quick', 'deep', 'hybrid'], default='hybrid',
                       help='Analysis mode')
    parser.add_argument('--output', help='Output file (default: append to input file)')

    args = parser.parse_args()

    # Get API key
    api_key = os.environ.get('ANTHROPIC_API_KEY')
    if not api_key:
        print("Error: ANTHROPIC_API_KEY not set", file=sys.stderr)
        sys.exit(1)

    client = anthropic.Anthropic(api_key=api_key)

    # Load transcript
    print(f"Loading transcript: {args.transcript_file}")
    frontmatter, body = load_transcript(args.transcript_file)
    transcript = extract_transcript_only(body)

    # Extract participant name from frontmatter
    participant_match = re.search(r'coach:\s*"?\[\[@?([^\]|]+)', frontmatter)
    participant_name = participant_match.group(1) if participant_match else "Unknown"

    try:
        # Quick extract
        print(f"Performing quick extraction (model: {MODEL})...")
        quick_summary = quick_extract(client, transcript, mode=args.mode)

        deep_summary = None
        matched_trails = None

        if args.mode in ['deep', 'hybrid']:
            # Find previous sessions and trails
            print("Loading context for deep analysis...")
            previous_sessions = get_previous_sessions(args.vault,
                                                      Path(args.transcript_file).name,
                                                      participant_name)
            trails = find_trails(args.vault)

            prev_summary = ""
            if previous_sessions:
                prev_summary = f"Previous {len(previous_sessions)} sessions found"

            # Deep analysis
            print("Performing deep analysis...")
            deep_summary = deep_analysis(client, transcript, prev_summary, trails)

            # Match trails
            print("Matching relevant trails...")
            matched_trails = match_trails(client, quick_summary, trails)
    except anthropic.BadRequestError as e:
        if "credit balance is too low" in str(e):
            print(
                "\nError: the ANTHROPIC_API_KEY in this environment has no credit "
                "balance.\nThis script bills the Anthropic API directly.\n"
                "Options:\n"
                "  1. Add credits / use a funded key (export ANTHROPIC_API_KEY=...).\n"
                "  2. Ask Claude Code to run the analysis in-session (no API billing).",
                file=sys.stderr,
            )
            sys.exit(2)
        raise
    except anthropic.AuthenticationError:
        print("\nError: ANTHROPIC_API_KEY is invalid or expired.", file=sys.stderr)
        sys.exit(2)

    # Format output
    output = format_output(frontmatter, quick_summary, deep_summary, matched_trails)

    # Write output
    output_file = args.output or args.transcript_file

    if output_file == args.transcript_file:
        # Append to existing file
        with open(output_file, 'a', encoding='utf-8') as f:
            f.write("\n\n" + output)
        print(f"\n✓ Summary appended to {output_file}")
    else:
        # Write new file
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(output)
        print(f"\n✓ Summary written to {output_file}")

    print("\nSummary complete!")
    if matched_trails:
        print(f"Connected trails: {', '.join(matched_trails)}")

if __name__ == '__main__':
    main()
