#!/usr/bin/env python3
"""
Re-process meeting with user answers from interactive mode
"""

import os
import sys
import json
import argparse
from pathlib import Path

# Add scripts directory to path
sys.path.insert(0, str(Path(__file__).parent))

from process import load_transcript, save_analysis, MEETING_PROCESSORS


def main():
    parser = argparse.ArgumentParser(description='Re-process with user answers')
    parser.add_argument('questions_file', help='Path to questions JSON file')
    parser.add_argument('answers_file', help='Path to answers JSON file')

    args = parser.parse_args()

    # Load questions context
    with open(args.questions_file, 'r') as f:
        context = json.load(f)

    # Load user answers
    with open(args.answers_file, 'r') as f:
        answers = json.load(f)

    meeting_type = context['meeting_type']
    transcript_file = context['transcript_file']
    partial_data = context['partial_data']

    print(f"📄 Reprocessing {meeting_type} meeting with user answers...")

    # Load transcript
    frontmatter, transcript_content = load_transcript(transcript_file)

    # Get processor and apply answers
    processor = MEETING_PROCESSORS[meeting_type]
    analysis = processor(transcript_content, mode='interactive', user_answers=answers)

    # Save results
    print(f"💾 Saving analysis to {transcript_file}...")
    save_analysis(transcript_file, frontmatter, transcript_content, analysis, meeting_type, 'interactive')

    print("✓ Processing complete!")


if __name__ == '__main__':
    main()
