#!/usr/bin/env python3
"""
Firecrawl CLI — search, scrape, and extract web content via Firecrawl API.
"""

import argparse
import json
import os
import shutil
import subprocess
import sys
import requests

SOPS_SECRETS = os.path.expanduser("~/.claude/skills/secrets.enc.yaml")
AGE_KEY_FILE = os.path.expanduser("~/.config/sops/age/keys.txt")


def load_api_key():
    """Read FIRECRAWL_API_KEY from SOPS first; fall back to the env var.

    Falls back silently when sops, the secrets file, or the key is missing,
    or when decryption fails or times out.
    """
    if shutil.which("sops") and os.path.exists(SOPS_SECRETS):
        env = dict(os.environ)
        if "SOPS_AGE_KEY_FILE" not in env and os.path.exists(AGE_KEY_FILE):
            env["SOPS_AGE_KEY_FILE"] = AGE_KEY_FILE
        try:
            r = subprocess.run(
                ["sops", "-d", "--extract", '["FIRECRAWL_API_KEY"]', SOPS_SECRETS],
                capture_output=True, text=True, env=env, timeout=10,
            )
            if r.returncode == 0 and r.stdout.strip():
                return r.stdout.strip()
        except (OSError, subprocess.TimeoutExpired):
            pass
    return os.getenv("FIRECRAWL_API_KEY")


API_KEY = load_api_key()
BASE = "https://api.firecrawl.dev/v1"
HEADERS = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json",
}


def die(msg):
    print(f"ERROR: {msg}", file=sys.stderr)
    sys.exit(1)


def search(query, limit=5, fmt="markdown"):
    """Search the web and return scraped results."""
    r = requests.post(
        f"{BASE}/search",
        headers=HEADERS,
        json={
            "query": query,
            "limit": limit,
            "scrapeOptions": {
                "formats": ["markdown"],
                "onlyMainContent": True,
            },
        },
    )
    if r.status_code != 200:
        die(f"Search failed ({r.status_code}): {r.text}")

    results = r.json().get("data", [])

    if fmt == "json":
        print(json.dumps(results, indent=2, ensure_ascii=False))
        return results

    for i, item in enumerate(results, 1):
        title = item.get("title", "Untitled")
        url = item.get("url", "")
        md = item.get("markdown", "")
        print(f"## {i}. {title}\n")
        print(f"**URL:** {url}\n")
        if md:
            print(md[:3000])
            if len(md) > 3000:
                print("\n... (truncated)")
        print("\n---\n")

    print(f"Total: {len(results)} results")
    return results


def scrape(url, fmt="markdown"):
    """Scrape a single URL and return content."""
    r = requests.post(
        f"{BASE}/scrape",
        headers=HEADERS,
        json={
            "url": url,
            "formats": ["markdown"],
            "onlyMainContent": True,
        },
    )
    if r.status_code != 200:
        die(f"Scrape failed ({r.status_code}): {r.text}")

    data = r.json().get("data", {})

    if fmt == "json":
        print(json.dumps(data, indent=2, ensure_ascii=False))
        return data

    title = data.get("metadata", {}).get("title", "Untitled")
    md = data.get("markdown", "")
    print(f"# {title}\n")
    print(f"**URL:** {url}\n")
    print(md)
    return data


def extract(urls, prompt, fmt="markdown"):
    """Extract structured data from URLs using a prompt."""
    if isinstance(urls, str):
        urls = [urls]

    r = requests.post(
        f"{BASE}/extract",
        headers=HEADERS,
        json={
            "urls": urls,
            "prompt": prompt,
        },
    )
    if r.status_code != 200:
        die(f"Extract failed ({r.status_code}): {r.text}")

    data = r.json().get("data", {})

    if fmt == "json":
        print(json.dumps(data, indent=2, ensure_ascii=False))
    else:
        print(json.dumps(data, indent=2, ensure_ascii=False))

    return data


def map_site(url, limit=100):
    """Get all URLs from a website."""
    r = requests.post(
        f"{BASE}/map",
        headers=HEADERS,
        json={"url": url, "limit": limit},
    )
    if r.status_code != 200:
        die(f"Map failed ({r.status_code}): {r.text}")

    data = r.json()
    links = data.get("links", [])
    for link in links:
        print(link)
    print(f"\nTotal: {len(links)} URLs")
    return links


def main():
    if not API_KEY:
        die("FIRECRAWL_API_KEY not found in SOPS (~/.claude/skills/secrets.enc.yaml) or environment")

    parser = argparse.ArgumentParser(description="Firecrawl CLI")
    sub = parser.add_subparsers(dest="command", required=True)

    # search
    p_search = sub.add_parser("search", help="Search the web")
    p_search.add_argument("query", help="Search query")
    p_search.add_argument("-n", "--limit", type=int, default=5)
    p_search.add_argument("-f", "--format", choices=["markdown", "json"], default="markdown")
    p_search.add_argument("-o", "--output", help="Save to file")

    # scrape
    p_scrape = sub.add_parser("scrape", help="Scrape a URL")
    p_scrape.add_argument("url", help="URL to scrape")
    p_scrape.add_argument("-f", "--format", choices=["markdown", "json"], default="markdown")
    p_scrape.add_argument("-o", "--output", help="Save to file")

    # extract
    p_extract = sub.add_parser("extract", help="Extract structured data from URLs")
    p_extract.add_argument("urls", nargs="+", help="URLs to extract from")
    p_extract.add_argument("-p", "--prompt", required=True, help="Extraction prompt")
    p_extract.add_argument("-f", "--format", choices=["markdown", "json"], default="json")
    p_extract.add_argument("-o", "--output", help="Save to file")

    # map
    p_map = sub.add_parser("map", help="Get all URLs from a site")
    p_map.add_argument("url", help="Site URL")
    p_map.add_argument("-n", "--limit", type=int, default=100)
    p_map.add_argument("-o", "--output", help="Save to file")

    args = parser.parse_args()

    # Redirect stdout to file if --output specified
    original_stdout = sys.stdout
    if hasattr(args, "output") and args.output:
        sys.stdout = open(args.output, "w", encoding="utf-8")

    try:
        if args.command == "search":
            search(args.query, args.limit, args.format)
        elif args.command == "scrape":
            scrape(args.url, args.format)
        elif args.command == "extract":
            extract(args.urls, args.prompt, args.format)
        elif args.command == "map":
            map_site(args.url, args.limit)
    finally:
        if sys.stdout != original_stdout:
            sys.stdout.close()
            sys.stdout = original_stdout
            print(f"Saved to {args.output}")


if __name__ == "__main__":
    main()
