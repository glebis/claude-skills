#!/usr/bin/env python3
"""Enrich candidates with thin snippets by fetching linked content via Firecrawl.

Runs between ingestion and salience filter. Detects candidates where the snippet
is too short (just a redirect link or empty) and fetches the actual article content.
"""
import argparse
import json
import os
import re
import sys
import time
from pathlib import Path

try:
    import requests
except ImportError:
    print("Error: requests not installed. Run: pip install requests", file=sys.stderr)
    sys.exit(1)

FIRECRAWL_API_KEY = os.environ.get("FIRECRAWL_API_KEY", "")
FIRECRAWL_URL = "https://api.firecrawl.dev/v1/scrape"
MIN_SNIPPET_LENGTH = 150
MAX_FETCHES_PER_RUN = 15
FETCH_DELAY = 1.0


def extract_url(text):
    """Extract the first HTTP(S) URL from text."""
    match = re.search(r'https?://[^\s<>"\')\]]+', text)
    return match.group(0) if match else None


def is_thin(candidate):
    """Check if a candidate has insufficient content for scoring."""
    snippet = candidate.get("snippet", "")
    # Strip common noise patterns
    clean = re.sub(r'https?://[^\s]+', '', snippet)
    clean = re.sub(r'Read on LinkedIn|Read this article|View this post on the web', '', clean)
    clean = re.sub(r'\s+', ' ', clean).strip()
    return len(clean) < MIN_SNIPPET_LENGTH


def fetch_content(url):
    """Fetch article content via Firecrawl scrape API."""
    if not FIRECRAWL_API_KEY:
        return None

    try:
        resp = requests.post(
            FIRECRAWL_URL,
            headers={
                "Authorization": f"Bearer {FIRECRAWL_API_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "url": url,
                "formats": ["markdown"],
                "onlyMainContent": True,
            },
            timeout=30,
        )
        if resp.status_code == 200:
            data = resp.json()
            markdown = data.get("data", {}).get("markdown", "")
            return markdown[:1500] if markdown else None
        else:
            print(f"  Firecrawl {resp.status_code} for {url[:60]}", file=sys.stderr)
            return None
    except Exception as e:
        print(f"  Firecrawl error: {e}", file=sys.stderr)
        return None


def enrich_candidates(candidates):
    """Enrich thin candidates with fetched content."""
    enriched_count = 0
    fetch_count = 0

    for candidate in candidates:
        if not is_thin(candidate):
            continue

        if fetch_count >= MAX_FETCHES_PER_RUN:
            print(f"  Hit fetch limit ({MAX_FETCHES_PER_RUN}), stopping", file=sys.stderr)
            break

        # Find a URL to fetch
        url = extract_url(candidate.get("snippet", ""))
        if not url:
            url = candidate.get("url", "")
        if not url:
            continue

        # Skip non-article URLs
        if any(skip in url for skip in ["zoom.us", "meet.google", "cal.com", "luma.com/event/manage"]):
            continue

        # LinkedIn is behind auth — mark as needs-click, don't waste a fetch
        if "linkedin.com" in url:
            candidate["snippet"] = f"[LinkedIn article — content behind auth wall. Source is notable.] {candidate.get('snippet', '')}"
            candidate["needs_click"] = True
            enriched_count += 1
            continue

        print(f"  Fetching: {url[:70]}...", file=sys.stderr)
        content = fetch_content(url)
        fetch_count += 1

        if content and len(content) > MIN_SNIPPET_LENGTH:
            candidate["snippet"] = content[:1000]
            candidate["enriched"] = True
            enriched_count += 1

        time.sleep(FETCH_DELAY)

    return enriched_count


def main():
    parser = argparse.ArgumentParser(description="Enrich thin candidates with fetched content")
    parser.add_argument("--input", "-i", required=True, help="Input JSONL candidates")
    parser.add_argument("--output", "-o", required=True, help="Output JSONL (enriched)")
    args = parser.parse_args()

    candidates = []
    with open(args.input) as f:
        for line in f:
            if line.strip():
                candidates.append(json.loads(line))

    thin_count = sum(1 for c in candidates if is_thin(c))
    print(f"Enriching: {len(candidates)} candidates, {thin_count} have thin snippets", file=sys.stderr)

    enriched_count = enrich_candidates(candidates)
    print(f"  Enriched {enriched_count}/{thin_count} thin candidates", file=sys.stderr)

    with open(args.output, "w") as f:
        for c in candidates:
            f.write(json.dumps(c) + "\n")


if __name__ == "__main__":
    main()
