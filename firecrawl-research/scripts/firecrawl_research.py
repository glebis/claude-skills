#!/usr/bin/env python3
"""
FireCrawl Research Script
Enriches research by searching and scraping web sources via FireCrawl API
"""

import os
import re
import sys
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv
import requests
import time

# Load .env from skill directory
SKILL_DIR = Path(__file__).parent.parent
load_dotenv(SKILL_DIR / '.env')

FIRECRAWL_API_KEY = os.getenv('FIRECRAWL_API_KEY')
FIRECRAWL_BASE_URL = 'https://api.firecrawl.dev/v1'

# Free tier: 5 requests/minute
RATE_LIMIT_DELAY = 12  # seconds between requests


def validate_api_key():
    """Check if API key is configured"""
    if not FIRECRAWL_API_KEY:
        print("ERROR: FIRECRAWL_API_KEY not found in .env file")
        print(f"Please create {SKILL_DIR}/.env with your API key:")
        print("FIRECRAWL_API_KEY=your_api_key_here")
        sys.exit(1)


def extract_topics_from_markdown(file_path):
    """Extract research topics from markdown file"""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    topics = []

    # Extract from ## and ### headers
    headers = re.findall(r'^#{2,3}\s+(.+)$', content, re.MULTILINE)
    topics.extend(headers)

    # Extract from [research] or [search] tags
    research_items = re.findall(
        r'[-*]\s+\[(?:research|search)\]\s+(.+)$',
        content,
        re.MULTILINE
    )
    topics.extend(research_items)

    # Remove duplicates while preserving order
    seen = set()
    unique_topics = []
    for topic in topics:
        topic_clean = topic.strip()
        if topic_clean and topic_clean not in seen:
            seen.add(topic_clean)
            unique_topics.append(topic_clean)

    print(f"Extracted {len(unique_topics)} topics for research")
    return unique_topics


def search_firecrawl(query, limit=5):
    """Search via FireCrawl API"""
    url = f'{FIRECRAWL_BASE_URL}/search'
    headers = {
        'Authorization': f'Bearer {FIRECRAWL_API_KEY}',
        'Content-Type': 'application/json'
    }

    payload = {
        'query': query,
        'limit': limit,
        'scrapeOptions': {
            'formats': ['markdown'],
            'onlyMainContent': True
        }
    }

    print(f"Searching: {query}")
    response = requests.post(url, headers=headers, json=payload)

    if response.status_code == 200:
        data = response.json()
        return data.get('data', [])
    else:
        print(f"Error {response.status_code}: {response.text}")
        return []


def extract_urls_from_content(content):
    """Extract URLs from markdown content"""
    urls = re.findall(r'\*\*URL:\*\*\s+(.+)', content)
    return urls


def create_research_markdown(topic, results, output_dir):
    """Create markdown file with research results"""
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    # Generate safe filename
    safe_filename = re.sub(r'[^\w\s-]', '', topic).strip().replace(' ', '_')
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = output_path / f"{safe_filename}_{timestamp}.md"

    with open(filename, 'w', encoding='utf-8') as f:
        f.write(f"# Research: {topic}\n\n")
        f.write(f"**Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        f.write(f"**Sources:** {len(results)}\n\n")
        f.write("---\n\n")

        for idx, result in enumerate(results, 1):
            title = result.get('title', 'Untitled')
            url = result.get('url', 'N/A')
            markdown = result.get('markdown', '')

            f.write(f"## {idx}. {title}\n\n")
            f.write(f"**URL:** {url}\n\n")

            if markdown:
                # Limit content length for readability
                if len(markdown) > 3000:
                    markdown = markdown[:3000] + "\n\n... (truncated)"
                f.write(f"{markdown}\n\n")

            f.write("---\n\n")

    print(f"Created: {filename}")
    return str(filename)


def main():
    """Main research workflow"""
    if len(sys.argv) < 2:
        print("Usage: python firecrawl_research.py <markdown_file> [output_dir] [limit]")
        print("  markdown_file: File containing research topics")
        print("  output_dir: Where to save results (default: current directory)")
        print("  limit: Max results per topic (default: 5)")
        sys.exit(1)

    validate_api_key()

    input_file = sys.argv[1]
    output_dir = sys.argv[2] if len(sys.argv) > 2 else '.'
    search_limit = int(sys.argv[3]) if len(sys.argv) > 3 else 5

    if not os.path.exists(input_file):
        print(f"Error: File not found: {input_file}")
        sys.exit(1)

    print(f"\n=== FireCrawl Research ===")
    print(f"Input: {input_file}")
    print(f"Output: {output_dir}")
    print(f"Limit: {search_limit} results per topic\n")

    # Extract topics
    topics = extract_topics_from_markdown(input_file)

    if not topics:
        print("No topics found. Add ## headers or [research] tags to your markdown.")
        return

    # Process each topic
    for idx, topic in enumerate(topics, 1):
        print(f"\n[{idx}/{len(topics)}] Topic: {topic}")

        # Search and scrape
        results = search_firecrawl(topic, limit=search_limit)

        if results:
            create_research_markdown(topic, results, output_dir)
            print(f"Found {len(results)} sources")
        else:
            print("No results found")

        # Rate limiting for free tier
        if idx < len(topics):
            print(f"Waiting {RATE_LIMIT_DELAY}s (rate limit)...")
            time.sleep(RATE_LIMIT_DELAY)

    print(f"\n=== Complete ===")
    print(f"Processed {len(topics)} topics")


if __name__ == '__main__':
    main()
