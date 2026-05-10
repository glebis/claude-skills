#!/usr/bin/env python3
"""WOW scoring: score candidates for epistemic friction, select top items."""
import argparse
import json
import os
import subprocess
import sys
from datetime import datetime, timedelta
from pathlib import Path

VAULT = Path.home() / "Brains" / "brain"
CONFIG_DIR = Path(__file__).parent.parent / "config"
EVAL_DIR = Path(__file__).parent.parent / ".wow-eval"


def load_focus():
    """Load Base + Primary sections from My Focus.md."""
    focus_path = VAULT / "My Focus.md"
    if not focus_path.exists():
        return "No focus file found."
    text = focus_path.read_text()
    # Extract from ## Current & Urgent through ## Nice to have
    lines = text.split("\n")
    capture = False
    result = []
    for line in lines:
        if line.startswith("## Current") or line.startswith("## Base") or line.startswith("## Primary"):
            capture = True
        elif line.startswith("## Nice to have") or line.startswith("## My key"):
            capture = False
        if capture:
            result.append(line)
    return "\n".join(result) if result else text[:2000]


def load_recent_research(days=30):
    """Load titles + tags from recent ai-research files."""
    research_dir = VAULT / "ai-research"
    if not research_dir.exists():
        return "No ai-research directory."
    cutoff = datetime.now() - timedelta(days=days)
    entries = []
    for f in sorted(research_dir.glob("*.md"), reverse=True):
        # Parse date from filename: YYYYMMDD-topic.md
        try:
            date_str = f.stem[:8]
            file_date = datetime.strptime(date_str, "%Y%m%d")
            if file_date < cutoff:
                continue
        except ValueError:
            continue
        # Read frontmatter for tags
        text = f.read_text(errors="replace")
        tags = ""
        for line in text.split("\n")[:10]:
            if line.startswith("research_topic:"):
                tags = line.replace("research_topic:", "").strip()
                break
        entries.append(f"- {f.stem} [{tags}]")
    return "\n".join(entries[:30]) if entries else "No recent research files."


def load_recent_topics(days=7):
    """Extract headers from recent daily notes."""
    topics = []
    for i in range(days):
        date = datetime.now() - timedelta(days=i)
        daily_path = VAULT / "Daily" / f"{date.strftime('%Y%m%d')}.md"
        if not daily_path.exists():
            continue
        text = daily_path.read_text(errors="replace")
        for line in text.split("\n"):
            if line.startswith("## ") and line.strip() not in ("## do", "## log"):
                topics.append(f"- {date.strftime('%m/%d')}: {line.strip('# ').strip()}")
    return "\n".join(topics) if topics else "No recent daily note topics."


def score_candidates(candidates):
    """Send candidates through the WOW scoring prompt via llm CLI."""
    prompt_path = CONFIG_DIR / "wow_prompt.txt"
    prompt_template = prompt_path.read_text()

    focus = load_focus()
    research = load_recent_research()
    recent_topics = load_recent_topics()

    candidate_text = "\n\n".join(
        f"### Candidate {i+1}\nSource: {c['source_name']} ({c['source_type']})\n"
        f"Title: {c['title']}\nSnippet: {c['snippet'][:400]}"
        for i, c in enumerate(candidates)
    )

    prompt = prompt_template.format(
        focus=focus,
        research=research,
        recent_topics=recent_topics,
        candidates=candidate_text,
    )

    # Use llm CLI with default model
    result = subprocess.run(
        ["llm", "-s", "Respond with ONLY a JSON array. No markdown fences, no explanation.", prompt],
        capture_output=True, text=True
    )
    if result.returncode != 0:
        print(f"LLM error: {result.stderr}", file=sys.stderr)
        return []

    # Parse JSON from response
    response = result.stdout.strip()
    # Strip markdown fences if present
    if response.startswith("```"):
        response = "\n".join(response.split("\n")[1:])
    if response.endswith("```"):
        response = "\n".join(response.split("\n")[:-1])

    try:
        scored = json.loads(response)
    except json.JSONDecodeError as e:
        print(f"JSON parse error: {e}", file=sys.stderr)
        print(f"Raw response: {response[:500]}", file=sys.stderr)
        return []

    return scored


def select_top(scored, min_items=3, max_items=7):
    """Apply selection rules: diversity, source caps, sideways requirement."""
    scored.sort(key=lambda x: x.get("wow_score", 0), reverse=True)

    selected = []
    source_counts = {}
    topic_counts = {}

    for item in scored:
        if len(selected) >= max_items:
            break

        source = item.get("source", "")
        topic = item.get("connected_recent_note", "general")

        # Max 1 per source
        if source_counts.get(source, 0) >= 1:
            continue
        # Max 2 per topic cluster
        if topic_counts.get(topic, 0) >= 2:
            continue

        selected.append(item)
        source_counts[source] = source_counts.get(source, 0) + 1
        topic_counts[topic] = topic_counts.get(topic, 0) + 1

    # Ensure at least 1 sideways item (bridge_value > surprise)
    has_sideways = any(
        s.get("bridge_value", 0) > s.get("surprise", 0) for s in selected
    )
    if not has_sideways:
        for item in scored:
            if item not in selected and item.get("bridge_value", 0) > item.get("surprise", 0):
                if len(selected) >= max_items:
                    selected[-1] = item
                else:
                    selected.append(item)
                break

    return selected


def main():
    parser = argparse.ArgumentParser(description="Score candidates for WOW")
    parser.add_argument("--input", "-i", required=True, help="Input JSONL candidates")
    parser.add_argument("--output", "-o", required=True, help="Output JSON selected items")
    parser.add_argument("--all-scored", help="Also dump all scored items (for eval)")
    args = parser.parse_args()

    # Load candidates
    candidates = []
    with open(args.input) as f:
        for line in f:
            if line.strip():
                candidates.append(json.loads(line))

    if not candidates:
        print("No candidates to score.", file=sys.stderr)
        sys.exit(0)

    print(f"Scoring {len(candidates)} candidates...", file=sys.stderr)
    scored = score_candidates(candidates)

    if args.all_scored:
        Path(args.all_scored).parent.mkdir(parents=True, exist_ok=True)
        with open(args.all_scored, "w") as f:
            json.dump(scored, f, indent=2)
        print(f"All scored → {args.all_scored}", file=sys.stderr)

    # Merge original snippets back into scored items (LLM output loses them)
    candidate_by_title = {c.get("title", "").lower().strip(): c for c in candidates}
    for item in scored:
        title_key = item.get("title", "").lower().strip()
        if title_key in candidate_by_title:
            orig = candidate_by_title[title_key]
            item["snippet"] = orig.get("snippet", "")
            item["message_id"] = orig.get("message_id", "")
            item["source_type"] = orig.get("source_type", item.get("source_type", ""))

    selected = select_top(scored)
    print(f"Selected {len(selected)} WOW items", file=sys.stderr)

    with open(args.output, "w") as f:
        json.dump(selected, f, indent=2)

    # Print summary
    for item in selected:
        print(f"  [{item.get('wow_score', '?')}] {item.get('title', '?')[:60]}", file=sys.stderr)


if __name__ == "__main__":
    main()
