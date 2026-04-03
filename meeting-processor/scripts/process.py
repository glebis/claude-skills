#!/usr/bin/env python3
"""
Meeting Processor - Intelligent transcript analysis with type detection
"""

import os
import sys
import argparse
import json
import tempfile
from pathlib import Path
from datetime import datetime
import yaml

# Add scripts directory to path
sys.path.insert(0, str(Path(__file__).parent))

from detectors import detect_meeting_type
from extractors import leadgen, partnership, coaching


MEETING_PROCESSORS = {
    'leadgen': leadgen.process,
    'partnership': partnership.process,
    'coaching': coaching.process,
    # 'internal': internal.process,  # Future
}


def load_transcript(file_path):
    """Load transcript and extract existing frontmatter if present."""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Parse frontmatter if exists
    frontmatter = {}
    transcript_content = content

    if content.startswith('---'):
        parts = content.split('---', 2)
        if len(parts) >= 3:
            try:
                frontmatter = yaml.safe_load(parts[1]) or {}
                transcript_content = parts[2].strip()
            except yaml.YAMLError:
                pass

    return frontmatter, transcript_content


def save_analysis(file_path, frontmatter, transcript_content, analysis, meeting_type, mode):
    """Append analysis to transcript file."""

    # Update frontmatter
    frontmatter.update({
        'meeting_type': meeting_type,
        'processed_date': datetime.now().strftime('%Y-%m-%d'),
        'processing_mode': mode
    })

    # Build output
    output = f"---\n{yaml.dump(frontmatter, default_flow_style=False)}---\n\n{transcript_content}"

    # Remove old analysis section if exists
    if '\n## Meeting Analysis\n' in output:
        output = output.split('\n## Meeting Analysis\n')[0]

    # Append new analysis
    output += f"\n\n## Meeting Analysis\n\n{analysis}"

    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(output)


def main():
    parser = argparse.ArgumentParser(description='Process meeting transcripts with type-specific analysis')
    parser.add_argument('transcript', help='Path to transcript file')
    parser.add_argument('--mode', choices=['interactive', 'batch'], default='interactive',
                       help='Processing mode (default: interactive)')
    parser.add_argument('--type', choices=list(MEETING_PROCESSORS.keys()),
                       help='Force meeting type (auto-detect if not specified)')
    parser.add_argument('--output', help='Output file (default: append to transcript)')

    args = parser.parse_args()

    # Validate file
    if not os.path.exists(args.transcript):
        print(f"❌ Error: File not found: {args.transcript}")
        sys.exit(1)

    print("📄 Loading transcript...")
    frontmatter, transcript_content = load_transcript(args.transcript)

    # Detect or use specified meeting type
    if args.type:
        meeting_type = args.type
        print(f"📋 Using specified type: {meeting_type}")
    else:
        print("🔍 Detecting meeting type...")
        meeting_type = detect_meeting_type(transcript_content, args.mode == 'interactive')
        print(f"📋 Detected type: {meeting_type}")

    # Get processor
    if meeting_type not in MEETING_PROCESSORS:
        print(f"❌ Error: No processor for meeting type: {meeting_type}")
        sys.exit(1)

    # Process transcript
    processor = MEETING_PROCESSORS[meeting_type]
    print(f"🤖 Processing as {meeting_type} call ({args.mode} mode)...")

    analysis = processor(transcript_content, mode=args.mode)

    # Check if interactive questions needed
    if isinstance(analysis, dict) and analysis.get('needs_interaction'):
        print("\n🤔 Interactive mode: questions identified")
        print(f"   {len(analysis['questions'])} questions need user input")

        # Output questions as JSON for Claude to parse
        questions_json = json.dumps({
            'meeting_type': meeting_type,
            'questions': analysis['questions'],
            'partial_data': analysis['partial_data'],
            'transcript_file': args.transcript
        }, indent=2)

        print("\n__INTERACTIVE_QUESTIONS__")
        print(questions_json)
        print("__END_INTERACTIVE_QUESTIONS__")
        sys.exit(2)  # Exit code 2 signals interactive mode needed

    # Save results
    output_file = args.output or args.transcript
    print(f"💾 Saving analysis to {output_file}...")
    save_analysis(output_file, frontmatter, transcript_content, analysis, meeting_type, args.mode)

    print("✓ Processing complete!")


if __name__ == '__main__':
    main()
