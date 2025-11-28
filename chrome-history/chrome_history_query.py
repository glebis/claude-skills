#!/usr/bin/env python3
"""
Chrome history query with natural language parsing.
Queries BOTH desktop history (SQLite) and synced mobile history (LevelDB).

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
    'google.com/url', 'google.com/search', 'google.com/images',
}

# Domain clusters for grouping
DOMAIN_CLUSTERS = {
    'research': {'github.com', 'stackoverflow.com', 'arxiv.org', 'pubmed.ncbi.nlm.nih.gov',
                 'wikipedia.org', 'mdn.io', 'python.org', 'rust-lang.org', 'docs.rs', 'huggingface.co'},
    'reading': {'medium.com', 'substack.com', 'economist.com', 'nytimes.com', 'sciencedaily.com',
                'fastcompany.com', 'livescience.com', 'thenewstack.io', 'towardsdatascience.com',
                'cbsnews.com', 'designboom.com', 'meduza.io', 'euractiv.com', 'psychologytoday.com',
                'hackaday.com', 'lesswrong.com', 'yahoonews.com', 'johnathanbi.com', 'productcompass.pm'},
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
        'title_search': None,  # New: direct title search
    }

    # Check if this is a direct title search (not a time-based query)
    time_keywords = ['yesterday', 'last week', 'past week', 'this week', 'last month',
                     'past month', 'this month', 'last 2 weeks', 'today', 'this morning']
    has_time_keyword = any(kw in query for kw in time_keywords)

    # If no time keywords and query looks like a title, do title search
    if not has_time_keyword and len(query) > 10:
        result['title_search'] = query_text
        return result

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


def get_device_map(db):
    """
    Parse device_info records to build device ID -> device type mapping.
    Returns dict like {'H1hP7whLDFxssWDmKOKXew==': 'iPhone', ...}
    """
    devices = {}

    for record in db.iterate_records_raw():
        try:
            key = record.key.decode('utf-8', errors='replace') if record.key else ""
            value = record.value.decode('utf-8', errors='replace') if record.value else ""

            if 'device_info' not in key:
                continue

            # Extract device ID - it's a base64 string ending with ==
            # Pattern: device_info-dt-<base64>== or device_info-md-<base64>==
            match = re.search(r'device_info-[dm][td]-([A-Za-z0-9+/]{20,}==)', key)
            if not match:
                continue
            device_id = match.group(1)

            # Detect device type from value
            if 'IOS-PHONE' in value:
                devices[device_id] = 'iPhone'
            elif 'ANDROID-PHONE' in value:
                devices[device_id] = 'Android'
            elif 'IOS-TABLET' in value:
                devices[device_id] = 'iPad'
            elif 'ANDROID-TABLET' in value:
                devices[device_id] = 'Tablet'
            elif 'MAC' in value or 'OSX' in value:
                devices[device_id] = 'Mac'
            elif 'WINDOWS' in value:
                devices[device_id] = 'Windows'
            elif 'LINUX' in value:
                devices[device_id] = 'Linux'
            elif 'CHROMEOS' in value:
                devices[device_id] = 'ChromeOS'
        except Exception:
            continue

    return devices


def get_synced_history(search_term=None):
    """
    Query Chrome synced history from LevelDB (mobile/other devices).
    Returns list of {'url': str, 'title': str, 'source': 'iPhone'|'Mac'|etc}
    """
    try:
        from ccl_chromium_reader.ccl_chromium_indexeddb import ccl_leveldb
    except ImportError:
        return []

    leveldb_path = Path.home() / "Library/Application Support/Google/Chrome/Default/Sync Data/LevelDB"

    if not leveldb_path.exists():
        return []

    # Copy to temp to avoid lock issues
    temp_path = Path("/tmp/chrome_sync_leveldb_copy")
    try:
        if temp_path.exists():
            shutil.rmtree(temp_path)
        shutil.copytree(leveldb_path, temp_path)
    except Exception:
        return []

    results = []
    seen_urls = set()

    try:
        db = ccl_leveldb.RawLevelDb(temp_path)

        # First pass: build device map
        devices = get_device_map(db)

        # Second pass: extract URLs with device info
        db = ccl_leveldb.RawLevelDb(temp_path)  # Re-open for fresh iteration

        for record in db.iterate_records_raw():
            try:
                key = record.key.decode('utf-8', errors='replace') if record.key else ""
                value = record.value
                if not value:
                    continue

                value_str = value.decode('utf-8', errors='replace')

                # Determine device from session key
                device_type = 'synced'  # Default fallback
                if 'sessions' in key:
                    for dev_id, dev_type in devices.items():
                        if dev_id in key:
                            device_type = dev_type
                            break

                # Find URLs
                url_matches = list(re.finditer(r'https?://[^\x00-\x1f\x7f\s"<>]{10,200}', value_str))

                for match in url_matches:
                    url = match.group(0).rstrip('"\',.')

                    # Skip unwanted URLs
                    if any(skip in url for skip in ['google.com/search', 'google.com/images', '.png', '.jpg', '.ico', '.svg']):
                        continue

                    if url in seen_urls:
                        continue

                    # Apply search filter if provided
                    if search_term:
                        search_lower = search_term.lower()
                        # Search in URL and surrounding context
                        context_start = max(0, match.start() - 100)
                        context = value_str[context_start:match.end() + 50].lower()
                        if search_lower not in url.lower() and search_lower not in context:
                            continue

                    # Try to extract title from context
                    context_start = max(0, match.start() - 150)
                    context = value_str[context_start:match.start()]
                    title = ""

                    # Look for readable title text
                    title_match = re.search(r'([A-Za-z][A-Za-z0-9\s\-:,\.\'\"]{5,80})\s*$', context)
                    if title_match:
                        title = title_match.group(1).strip()

                    results.append({
                        'url': url,
                        'title': title or url,
                        'domain': urlparse(url).netloc,
                        'source': device_type,
                        'cluster': get_domain_cluster(url),
                    })
                    seen_urls.add(url)

            except Exception:
                continue

    except Exception as e:
        pass

    return results


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
            'source': 'desktop',
        })
        seen_urls.add(url)

    return visits


def search_all_history(search_term):
    """
    Search both desktop and synced history by title/URL.
    """
    results = []
    seen_urls = set()
    search_lower = search_term.lower()

    # Search desktop history (SQLite)
    chrome_history_path = Path.home() / "Library/Application Support/Google/Chrome/Default/History"
    temp_copy = Path("/tmp/chrome_history_temp")

    if chrome_history_path.exists():
        try:
            shutil.copy2(chrome_history_path, temp_copy)
            conn = sqlite3.connect(temp_copy)
            cursor = conn.cursor()

            # Search by title
            cursor.execute("""
                SELECT url, title, last_visit_time
                FROM urls
                WHERE lower(title) LIKE ? OR lower(url) LIKE ?
                ORDER BY last_visit_time DESC
                LIMIT 50
            """, (f'%{search_lower}%', f'%{search_lower}%'))

            epoch = datetime.datetime(1601, 1, 1)

            for url, title, chrome_time in cursor.fetchall():
                if url in seen_urls:
                    continue
                if not should_include(url):
                    continue

                dt = epoch + datetime.timedelta(microseconds=chrome_time)
                local_time = dt.replace(tzinfo=datetime.timezone.utc).astimezone().replace(tzinfo=None)

                results.append({
                    'time': local_time,
                    'url': url,
                    'title': title or url,
                    'domain': urlparse(url).netloc,
                    'cluster': get_domain_cluster(url),
                    'source': 'desktop',
                })
                seen_urls.add(url)

            conn.close()
        except Exception:
            pass

    # Search synced history (LevelDB)
    synced = get_synced_history(search_term)
    for item in synced:
        if item['url'] not in seen_urls:
            results.append(item)
            seen_urls.add(item['url'])

    return results


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


def format_results(visits, query_text, is_title_search=False):
    """Format results for markdown"""
    if not visits:
        return f"No browsing history found for: {query_text}"

    lines = [f"## Chrome History: {query_text}", ""]

    if is_title_search:
        # For title search, show flat list
        lines.insert(1, f"*Found {len(visits)} matches*\n")

        for visit in visits[:30]:
            time_str = visit.get('time', '').strftime('%Y-%m-%d %H:%M') if visit.get('time') else ''
            source = f"[{visit.get('source', 'unknown')}]"
            title = visit['title'].strip()[:70]

            lines.append(f"- {time_str} {source} {title}")
            lines.append(f"  {visit['url']}")

        return "\n".join(lines)

    # Group by cluster for time-based queries
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
            time_str = visit['time'].strftime('%H:%M') if visit.get('time') else ''
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
        print("  'Introducing Cosmos'  (title search)")
        sys.exit(1)

    query_text = ' '.join(sys.argv[1:])

    # Parse query
    parsed = parse_query(query_text)

    # Check if this is a title search
    if parsed.get('title_search'):
        visits = search_all_history(parsed['title_search'])
        result = format_results(visits, query_text, is_title_search=True)
    else:
        # Time-based query
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
        result = format_results(visits, query_text)

    print(result)
