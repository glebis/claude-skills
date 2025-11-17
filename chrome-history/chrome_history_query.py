#!/usr/bin/env python3
"""
Chrome history query with natural language parsing.
Supports queries like:
- "articles I read yesterday"
- "articles about AI I read yesterday"
- "scientific articles for the last week"
- "threads on reddit for the last month"
"""

import sqlite3
import shutil
import datetime
import re
from pathlib import Path
from urllib.parse import urlparse
from datetime import timedelta

# Sites to exclude
BLOCKLIST = {
    'facebook.com', 'instagram.com', 'twitter.com', 'x.com', 'tiktok.com',
    'reddit.com', 'youtube.com', 'amazon.com', 'ebay.com', 'pinterest.com',
    'linkedin.com', 'threads.net', 'mastodon.social',
    'gmail.com', 'outlook.com', 'mail.google.com',
    'freefeed.net',
    'google.com/url',
}

# Domain clusters for grouping
DOMAIN_CLUSTERS = {
    'research': {'github.com', 'stackoverflow.com', 'arxiv.org', 'pubmed.ncbi.nlm.nih.gov',
                 'wikipedia.org', 'mdn.io', 'python.org', 'rust-lang.org', 'docs.rs', 'huggingface.co'},
    'reading': {'medium.com', 'substack.com', 'economist.com', 'nytimes.com', 'sciencedaily.com',
                'fastcompany.com', 'livescience.com', 'thenewstack.io', 'towardsdatascience.com',
                'cbsnews.com', 'designboom.com', 'meduza.io', 'euractiv.com', 'psychologytoday.com',
                'hackaday.com', 'lesswrong.com', 'yahoonews.com'},
    'tools': {'openai.com', 'claude-code.glebkalinin.com', 'tbank.ru', 'tinkoff.ru', 'passwords.google.com'},
    'events': {'eventbrite.de', 'co-berlin.org', 'mubi.com'},
}

# Special sites that can be queried by name
SPECIAL_SITES = {
    'reddit': 'reddit.com',
    'hackernews': 'news.ycombinator.com',
    'twitter': 'twitter.com',
    'medium': 'medium.com',
    'youtube': 'youtube.com',
}

def parse_query(query_text):
    """
    Parse natural language query into date_range and filters.
    Returns: {'start_date': date, 'end_date': date, 'keywords': [str], 'clusters': [str], 'domain': str}
    """
    query = query_text.lower().strip()
    result = {
        'start_date': None,
        'end_date': None,
        'keywords': [],
        'clusters': [],
        'domain': None,
    }

    # Parse time range
    today = datetime.date.today()

    if 'yesterday' in query:
        yesterday = today - timedelta(days=1)
        result['start_date'] = yesterday
        result['end_date'] = yesterday

    elif 'last week' in query or 'past week' in query or 'this week' in query:
        result['start_date'] = today - timedelta(days=7)
        result['end_date'] = today

    elif 'last month' in query or 'past month' in query or 'this month' in query:
        result['start_date'] = today - timedelta(days=30)
        result['end_date'] = today

    elif 'last 2 weeks' in query or 'past 2 weeks' in query:
        result['start_date'] = today - timedelta(days=14)
        result['end_date'] = today

    elif 'today' in query or 'this morning' in query or 'tonight' in query:
        result['start_date'] = today
        result['end_date'] = today

    else:
        # Default to today if no time specified
        result['start_date'] = today
        result['end_date'] = today

    # Parse cluster/type filters
    if 'article' in query or 'reading' in query:
        result['clusters'].append('reading')
    if 'research' in query or 'scientific' in query or 'paper' in query:
        result['clusters'].append('research')
    if 'code' in query or 'github' in query:
        result['clusters'].append('research')

    # Parse special site filters
    for site_name, site_domain in SPECIAL_SITES.items():
        if site_name in query or f'on {site_name}' in query or f'at {site_name}' in query:
            result['domain'] = site_domain

    # Extract keywords (things after "about")
    match = re.search(r'about\s+([a-z\s]+?)(?:\s+i\s+read|$|\.)', query)
    if match:
        keywords = match.group(1).strip().split()
        result['keywords'] = [kw for kw in keywords if len(kw) > 2]

    return result


def get_chrome_history(date_range, filters):
    """
    Query Chrome history for date range with optional filters.
    date_range: {'start': date, 'end': date}
    filters: {'keywords': [str], 'clusters': [str], 'domain': str}
    """
    epoch = datetime.datetime(1601, 1, 1)

    # Convert dates to Chrome timestamps (microseconds since 1601)
    day_start = datetime.datetime.combine(date_range['start'], datetime.time.min)
    day_end = datetime.datetime.combine(date_range['end'], datetime.time.max)

    microseconds_start = int((day_start - epoch).total_seconds() * 1_000_000)
    microseconds_end = int((day_end - epoch).total_seconds() * 1_000_000)

    # Copy Chrome History DB
    chrome_history_path = Path.home() / "Library/Application Support/Google/Chrome/Default/History"
    temp_copy = Path("/tmp/chrome_history_temp")

    if not chrome_history_path.exists():
        return []

    try:
        shutil.copy2(chrome_history_path, temp_copy)
    except Exception:
        return []

    # Query
    conn = sqlite3.connect(temp_copy)
    cursor = conn.cursor()

    query = """
    SELECT urls.url, urls.title, visits.visit_time
    FROM urls
    JOIN visits ON urls.id = visits.url
    WHERE visits.visit_time >= ? AND visits.visit_time <= ?
    ORDER BY visits.visit_time DESC
    """

    cursor.execute(query, (microseconds_start, microseconds_end))
    results = cursor.fetchall()
    conn.close()

    # Filter and process
    visits = []
    seen_urls = set()

    for url, title, chrome_time in results:
        dt = epoch + datetime.timedelta(microseconds=chrome_time)
        local_time = dt.replace(tzinfo=datetime.timezone.utc).astimezone().replace(tzinfo=None)

        # Apply blocklist
        if not should_include(url):
            continue

        # Apply domain filter
        if filters['domain']:
            if filters['domain'] not in url:
                continue

        # Deduplicate
        if url in seen_urls:
            continue

        # Apply cluster filter
        if filters['clusters']:
            cluster = get_domain_cluster(url)
            if cluster not in filters['clusters']:
                continue

        # Apply keyword filter
        if filters['keywords']:
            combined_text = f"{url} {title or ''}".lower()
            if not any(kw in combined_text for kw in filters['keywords']):
                continue

        visits.append({
            'time': local_time,
            'url': url,
            'title': title or url,
            'domain': urlparse(url).netloc,
            'cluster': get_domain_cluster(url),
        })
        seen_urls.add(url)

    return visits


def should_include(url):
    """Check if URL should be included"""
    domain = urlparse(url).netloc.replace('www.', '')

    for blocked in BLOCKLIST:
        if blocked in domain or blocked in url:
            return False

    if url.startswith(('chrome://', 'about:', 'data:')):
        return False

    return True


def get_domain_cluster(url):
    """Return cluster name for a URL"""
    domain = urlparse(url).netloc.replace('www.', '')

    for cluster_name, sites in DOMAIN_CLUSTERS.items():
        for site in sites:
            if site in domain:
                return cluster_name
    return 'other'


def format_results(visits, query_text):
    """Format results for markdown"""
    if not visits:
        return f"No browsing history found for: {query_text}"

    lines = [f"## Chrome History: {query_text}", ""]

    # Group by cluster
    clusters = {}
    for visit in visits:
        cluster = visit['cluster']
        if cluster not in clusters:
            clusters[cluster] = []
        clusters[cluster].append(visit)

    cluster_order = ['reading', 'research', 'tools', 'events', 'other']

    total = 0
    for cluster_name in cluster_order:
        if cluster_name not in clusters:
            continue

        visits_in_cluster = clusters[cluster_name]
        total += len(visits_in_cluster)
        lines.append(f"### {cluster_name.capitalize()} ({len(visits_in_cluster)})")

        for visit in visits_in_cluster:
            time_str = visit['time'].strftime('%H:%M')
            title = visit['title'].strip()
            if len(title) > 75:
                title = title[:72] + "..."

            lines.append(f"- {time_str} {title}")
            lines.append(f"  {visit['url']}")

        lines.append("")

    lines.insert(1, f"*Found {total} items*\n")
    return "\n".join(lines)


if __name__ == '__main__':
    import sys

    if len(sys.argv) < 2:
        print("Usage: chrome_history_query.py '<query>'")
        print("Examples:")
        print("  'articles I read yesterday'")
        print("  'scientific articles for the last week'")
        print("  'reddit threads last month'")
        sys.exit(1)

    query_text = ' '.join(sys.argv[1:])

    # Parse query
    parsed = parse_query(query_text)

    # Get history
    date_range = {
        'start': parsed['start_date'],
        'end': parsed['end_date'],
    }

    filters = {
        'keywords': parsed['keywords'],
        'clusters': parsed['clusters'],
        'domain': parsed['domain'],
    }

    visits = get_chrome_history(date_range, filters)

    # Format and print
    result = format_results(visits, query_text)
    print(result)
