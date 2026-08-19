#!/usr/bin/env python3
"""
Trail check-in script for Obsidian vault.
Lists trails and extracts metadata for interactive check-ins.
"""

import json
import os
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

VAULT_PATH = Path.home() / "Brains" / "brain"
TRAILS_PATH = VAULT_PATH / "Trails"


def extract_frontmatter(content: str) -> Dict[str, any]:
    """Extract YAML frontmatter from markdown file."""
    fm_match = re.match(r'^---\n(.*?)\n---\n', content, re.DOTALL)
    if not fm_match:
        return {}

    fm_text = fm_match.group(1)
    fm = {}

    for line in fm_text.split('\n'):
        if ':' in line:
            key, value = line.split(':', 1)
            key = key.strip()
            value = value.strip().strip("'\"")

            # Handle dates in [[YYYYMMDD]] format
            if value.startswith('[[') and value.endswith(']]'):
                value = value[2:-2]

            fm[key] = value

    return fm


def extract_objective(content: str) -> str:
    """Extract objective from trail (first paragraph under ## Objective)."""
    obj_match = re.search(r'## Objective\n\n(.*?)(?:\n\n|\n##)', content, re.DOTALL)
    if not obj_match:
        return ""

    # Get first paragraph
    paragraphs = obj_match.group(1).strip().split('\n\n')
    return paragraphs[0].replace('\n', ' ').strip()


def list_trails() -> List[Dict]:
    """List all trails with metadata."""
    trails = []

    if not TRAILS_PATH.exists():
        return trails

    for trail_file in sorted(TRAILS_PATH.glob("Trail - *.md")):
        try:
            content = trail_file.read_text()
            fm = extract_frontmatter(content)
            objective = extract_objective(content)

            # Extract trail name from filename
            trail_name = trail_file.stem.replace("Trail - ", "")

            trails.append({
                "name": trail_name,
                "filename": trail_file.name,
                "status": fm.get("status", "unknown"),
                "last_updated": fm.get("last_updated", "never"),
                "next_review": fm.get("next_review", ""),
                "direction": fm.get("direction", ""),
                "velocity": fm.get("velocity", ""),
                "objective": objective[:200] + "..." if len(objective) > 200 else objective
            })
        except Exception as e:
            print(f"Error reading {trail_file}: {e}", file=sys.stderr)
            continue

    return trails


def show_trail(trail_name: str) -> Optional[Dict]:
    """Get detailed info for a specific trail."""
    trail_file = TRAILS_PATH / f"Trail - {trail_name}.md"

    if not trail_file.exists():
        return None

    content = trail_file.read_text()
    fm = extract_frontmatter(content)

    # Extract sections
    objective = extract_objective(content)

    # Extract current position
    pos_match = re.search(r'## Current Position\n\n(.*?)(?:\n##)', content, re.DOTALL)
    current_position = pos_match.group(1).strip() if pos_match else ""

    # Extract open questions
    questions_match = re.search(r'## Open Questions\n\n(.*?)(?:\n##)', content, re.DOTALL)
    open_questions = questions_match.group(1).strip() if questions_match else ""

    # Extract metrics table
    metrics_match = re.search(r'## Metrics\n\n\| Metric.*?\n\|[-\s|]+\n(.*?)(?:\n\n|\n##)', content, re.DOTALL)
    metrics = []
    if metrics_match:
        for line in metrics_match.group(1).strip().split('\n'):
            if line.startswith('|'):
                parts = [p.strip() for p in line.split('|')[1:-1]]
                if len(parts) >= 3:
                    metrics.append({
                        "metric": parts[0],
                        "current": parts[1],
                        "target": parts[2] if len(parts) > 2 else "",
                        "notes": parts[3] if len(parts) > 3 else ""
                    })

    return {
        "name": trail_name,
        "filename": trail_file.name,
        "path": str(trail_file),
        "frontmatter": fm,
        "objective": objective,
        "current_position": current_position,
        "open_questions": open_questions,
        "metrics": metrics,
        "full_content": content
    }


def main():
    if len(sys.argv) < 2:
        print(json.dumps({"error": "No command specified. Use: list, show <name>"}))
        sys.exit(1)

    command = sys.argv[1]

    if command == "list":
        trails = list_trails()
        print(json.dumps({"trails": trails}, indent=2))

    elif command == "show":
        if len(sys.argv) < 3:
            print(json.dumps({"error": "Trail name required"}))
            sys.exit(1)

        trail_name = sys.argv[2]
        trail = show_trail(trail_name)

        if trail:
            print(json.dumps(trail, indent=2))
        else:
            print(json.dumps({"error": f"Trail not found: {trail_name}"}))
            sys.exit(1)

    else:
        print(json.dumps({"error": f"Unknown command: {command}"}))
        sys.exit(1)


if __name__ == "__main__":
    main()
