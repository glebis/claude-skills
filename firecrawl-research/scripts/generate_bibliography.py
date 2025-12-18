#!/usr/bin/env python3
"""
Bibliography Generator from FireCrawl Research
Converts scraped web sources into BibTeX entries
"""

import os
import re
import sys
from pathlib import Path
from datetime import datetime
from urllib.parse import urlparse


def extract_urls_from_markdown(markdown_file):
    """Extract URLs from FireCrawl research markdown files"""
    with open(markdown_file, 'r', encoding='utf-8') as f:
        content = f.read()

    # Find URL lines
    url_pattern = r'\*\*URL:\*\*\s+(.+)'
    urls = re.findall(url_pattern, content)

    # Also extract titles
    title_pattern = r'^## \d+\.\s+(.+)$'
    titles = re.findall(title_pattern, content, re.MULTILINE)

    # Pair URLs with titles
    entries = []
    for i, url in enumerate(urls):
        title = titles[i] if i < len(titles) else "Untitled"
        entries.append({'url': url.strip(), 'title': title.strip()})

    return entries


def generate_cite_key(title, url, index):
    """Generate BibTeX citation key"""
    # Extract domain
    domain = urlparse(url).netloc.replace('www.', '').split('.')[0]

    # Clean title words
    words = re.sub(r'[^\w\s]', '', title).split()
    title_part = ''.join(words[:2]).title() if len(words) >= 2 else domain.title()

    # Year
    year = datetime.now().year

    # Create key
    cite_key = f"{title_part}{year}_{index}"
    return cite_key


def create_bibtex_entry(entry, index):
    """Create BibTeX @misc entry from URL and title"""
    cite_key = generate_cite_key(entry['title'], entry['url'], index)
    url = entry['url']
    title = entry['title']

    # Extract domain for author
    domain = urlparse(url).netloc.replace('www.', '')
    author = f"{{{domain.title()}}}"

    # Current date
    access_date = datetime.now().strftime('%Y-%m-%d')
    year = datetime.now().year

    bibtex = f"""@misc{{{cite_key},
  author       = {author},
  title        = {{{title}}},
  year         = {{{year}}},
  url          = {{{url}}},
  note         = {{Accessed: {access_date}}}
}}"""

    return bibtex, cite_key


def process_research_files(input_files, output_file='research.bib'):
    """Process multiple FireCrawl research markdown files"""
    all_entries = []
    cite_keys = []

    print(f"Processing {len(input_files)} file(s)...")

    for md_file in input_files:
        if not Path(md_file).exists():
            print(f"Warning: File not found: {md_file}")
            continue

        print(f"  Extracting from: {md_file}")
        entries = extract_urls_from_markdown(md_file)
        all_entries.extend(entries)

    if not all_entries:
        print("No URLs found in input files")
        return

    print(f"\nGenerating {len(all_entries)} BibTeX entries...")

    # Generate BibTeX
    bibtex_entries = []
    for idx, entry in enumerate(all_entries, 1):
        bibtex, cite_key = create_bibtex_entry(entry, idx)
        bibtex_entries.append(bibtex)
        cite_keys.append(cite_key)

    # Write to file
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("% Bibliography Generated from FireCrawl Research\n")
        f.write(f"% Created: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"% Sources: {len(all_entries)}\n\n")
        f.write('\n\n'.join(bibtex_entries))

    print(f"\n✓ Created: {output_file}")
    print(f"  Entries: {len(all_entries)}")

    # Print citation examples
    print("\nExample citations:")
    for key in cite_keys[:5]:
        print(f"  [@{key}]")
    if len(cite_keys) > 5:
        print(f"  ... and {len(cite_keys) - 5} more")


def main():
    """Main bibliography generation workflow"""
    if len(sys.argv) < 2:
        print("Usage: python generate_bibliography.py <file1.md> [file2.md ...] [-o output.bib]")
        print("\nExamples:")
        print("  python generate_bibliography.py research_output/*.md")
        print("  python generate_bibliography.py topic1.md topic2.md -o refs.bib")
        print("\nGenerates BibTeX bibliography from FireCrawl research markdown files")
        sys.exit(1)

    # Parse arguments
    input_files = []
    output_file = 'research.bib'

    args = sys.argv[1:]
    i = 0
    while i < len(args):
        if args[i] == '-o' and i + 1 < len(args):
            output_file = args[i + 1]
            i += 2
        else:
            input_files.append(args[i])
            i += 1

    if not input_files:
        print("ERROR: No input files specified")
        sys.exit(1)

    process_research_files(input_files, output_file)


if __name__ == '__main__':
    main()
