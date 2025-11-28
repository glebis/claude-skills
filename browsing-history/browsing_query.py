#!/usr/bin/env python3
"""
Browsing history query from synced devices database.
Supports natural language queries, device filtering, and LLM categorization.
"""
from __future__ import annotations

import sqlite3
import argparse
import json
import re
import sys
import subprocess
from datetime import datetime, timedelta
from pathlib import Path
from collections import defaultdict
from typing import Optional

DB_PATH = Path.home() / "data" / "browsing.db"
VAULT_PATH = Path.home() / "Research" / "vault"

# Device mappings
DEVICE_ALIASES = {
    "mobile": ["iPhone", "iPad", "Android", "Tablet"],
    "phone": ["iPhone", "Android"],
    "tablet": ["iPad", "Tablet"],
    "desktop": ["desktop", "Mac", "Windows"],
    "iphone": ["iPhone"],
    "ipad": ["iPad"],
    "mac": ["Mac"],
    "android": ["Android"],
}

# Categories for LLM classification
CATEGORIES = [
    "News & Current Events",
    "Technology & Programming",
    "Research & Learning",
    "Social Media & Entertainment",
    "Shopping & Commerce",
    "Finance & Business",
    "Health & Wellness",
    "Travel & Lifestyle",
    "Reference & Documentation",
    "Other",
]


def parse_time_query(query: str) -> tuple[datetime, datetime]:
    """Parse natural language time expressions into date range."""
    query_lower = query.lower()
    today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)

    if "yesterday" in query_lower:
        start = today - timedelta(days=1)
        end = start + timedelta(days=1) - timedelta(seconds=1)
    elif "today" in query_lower:
        start = today
        end = datetime.now()
    elif "last week" in query_lower or "past week" in query_lower:
        start = today - timedelta(days=7)
        end = datetime.now()
    elif "last month" in query_lower or "past month" in query_lower:
        start = today - timedelta(days=30)
        end = datetime.now()
    elif match := re.search(r"last\s+(\d+)\s+days?", query_lower):
        days = int(match.group(1))
        start = today - timedelta(days=days)
        end = datetime.now()
    else:
        # Default: last 24 hours
        start = datetime.now() - timedelta(hours=24)
        end = datetime.now()

    return start, end


def extract_search_terms(query: str) -> list[str]:
    """Extract search keywords from query (excluding time words)."""
    time_words = {
        "yesterday", "today", "last", "week", "month", "days", "past",
        "my", "the", "from", "on", "in", "for", "about", "i", "read",
        "browsing", "history", "articles", "pages", "tabs", "sites",
        "phone", "iphone", "ipad", "mac", "desktop", "mobile", "computer"
    }

    words = re.findall(r'\b\w+\b', query.lower())
    terms = [w for w in words if w not in time_words and len(w) >= 2]

    return terms


def query_history(
    start_date: datetime,
    end_date: datetime,
    devices: list[str] | None = None,
    domain_filter: str | None = None,
    search_terms: list[str] | None = None,
    limit: int = 200
) -> list[dict]:
    """Query browsing history from database."""

    if not DB_PATH.exists():
        raise FileNotFoundError(f"Database not found: {DB_PATH}")

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Build query
    sql = """
        SELECT url, title, device_type, first_seen, visit_time, domain
        FROM browsing_history
        WHERE COALESCE(visit_time, first_seen) >= ? AND COALESCE(visit_time, first_seen) <= ?
    """
    # Database uses 'YYYY-MM-DD HH:MM:SS' format (space separator)
    params = [start_date.strftime("%Y-%m-%d %H:%M:%S"), end_date.strftime("%Y-%m-%d %H:%M:%S")]

    if devices:
        placeholders = ",".join("?" * len(devices))
        sql += f" AND device_type IN ({placeholders})"
        params.extend(devices)

    if domain_filter:
        sql += " AND domain LIKE ?"
        params.append(f"%{domain_filter}%")

    if search_terms:
        # Add SQL-level search for efficiency
        for term in search_terms:
            sql += " AND (url LIKE ? OR title LIKE ?)"
            params.append(f"%{term}%")
            params.append(f"%{term}%")

    sql += " ORDER BY COALESCE(visit_time, first_seen) DESC"

    # Use higher limit for SQL to allow for deduplication
    sql_limit = limit * 3 if limit else 600
    sql += f" LIMIT {sql_limit}"

    cursor.execute(sql, params)
    rows = cursor.fetchall()
    conn.close()

    results = []
    seen_per_day = defaultdict(set)  # Dedupe per day

    for row in rows:
        url = row["url"]
        visit_time = row["visit_time"]
        first_seen = row["first_seen"]
        event_time = visit_time or first_seen or ""

        # Parse date for deduplication
        try:
            dt = datetime.fromisoformat(event_time.replace("Z", "+00:00"))
            day_key = dt.date().isoformat()
        except:
            day_key = event_time[:10] if event_time else "unknown"

        # Deduplicate by URL per day
        if url in seen_per_day[day_key]:
            continue
        seen_per_day[day_key].add(url)

        title = row["title"] or ""

        results.append({
            "url": url,
            "title": title,
            "device": row["device_type"],
            "time": event_time,
            "domain": row["domain"],
        })

        # Apply final limit after deduplication
        if limit and len(results) >= limit:
            break

    return results


def categorize_with_llm(results: list[dict]) -> list[dict]:
    """Use Claude to categorize URLs into content categories."""

    if not results:
        return results

    # Prepare batch for categorization
    items = []
    for i, r in enumerate(results[:100]):  # Limit to 100 for LLM
        title = r['title'] if r['title'] else r['url'][:60]
        items.append(f"{i}. {title[:80]} | {r['domain']}")

    prompt = f"""Categorize each of these web pages into exactly one category.

Categories:
{chr(10).join(f"- {c}" for c in CATEGORIES)}

Pages to categorize:
{chr(10).join(items)}

Respond with ONLY a JSON array of category names in the same order as the pages.
Example: ["Technology & Programming", "News & Current Events", ...]
"""

    # Try llm CLI first, then fall back to domain-based categorization
    try:
        result = subprocess.run(
            ["/opt/homebrew/bin/python3.11", "-m", "llm", "-m", "claude-3.5-haiku", prompt],
            capture_output=True,
            text=True,
            timeout=60
        )

        if result.returncode == 0:
            output = result.stdout.strip()
            match = re.search(r'\[.*\]', output, re.DOTALL)
            if match:
                categories = json.loads(match.group())
                for i, cat in enumerate(categories):
                    if i < len(results):
                        results[i]["category"] = cat
                return results
    except FileNotFoundError:
        print("Note: llm CLI not found, using domain-based categorization", file=sys.stderr)
    except Exception as e:
        print(f"LLM categorization failed: {e}, using domain-based fallback", file=sys.stderr)

    # Fallback: domain-based categorization
    domain_categories = {
        "News & Current Events": ["news", "cnn", "bbc", "nytimes", "guardian", "bloomberg", "reuters", "yahoo.com/news"],
        "Technology & Programming": ["github", "stackoverflow", "dev.to", "hackernews", "techcrunch", "verge", "arstechnica", "infoworld", "thenewstack"],
        "Research & Learning": ["arxiv", "scholar", "wikipedia", "medium", "substack", "lesswrong", "youtube.com/watch"],
        "Social Media & Entertainment": ["twitter", "reddit", "facebook", "instagram", "tiktok", "youtube.com", "twitch"],
        "Shopping & Commerce": ["amazon", "ebay", "etsy", "aliexpress"],
        "Finance & Business": ["bloomberg", "wsj", "ft.com", "investing", "coinbase"],
        "Health & Wellness": ["psychologytoday", "webmd", "healthline", "nih.gov"],
    }

    for r in results:
        domain = r["domain"].lower()
        found = False
        for category, keywords in domain_categories.items():
            if any(kw in domain for kw in keywords):
                r["category"] = category
                found = True
                break
        if not found:
            r["category"] = "Other"

    return results


def format_markdown(
    results: list[dict],
    query: str,
    group_by: str | None = None,
    date_range: tuple[datetime, datetime] | None = None
) -> str:
    """Format results as markdown."""

    lines = [f"# Browsing History: {query}", ""]

    if date_range:
        start, end = date_range
        if start.date() == end.date():
            lines.append(f"*{len(results)} unique URLs from {start.date()}*")
        else:
            lines.append(f"*{len(results)} unique URLs from {start.date()} to {end.date()}*")
        lines.append("")

    if not results:
        lines.append("No results found.")
        return "\n".join(lines)

    if group_by == "category":
        # Group by category
        by_category = defaultdict(list)
        for r in results:
            cat = r.get("category", "Other")
            by_category[cat].append(r)

        for cat in CATEGORIES:
            if cat in by_category:
                lines.append(f"## {cat}")
                lines.append("")
                for r in by_category[cat]:
                    title = r["title"] or r["url"][:60]
                    lines.append(f"- [{title}]({r['url']}) - {r['device']}")
                lines.append("")

    elif group_by == "domain":
        # Group by domain
        by_domain = defaultdict(list)
        for r in results:
            by_domain[r["domain"]].append(r)

        for domain in sorted(by_domain.keys(), key=lambda d: -len(by_domain[d])):
            lines.append(f"## {domain} ({len(by_domain[domain])})")
            lines.append("")
            for r in by_domain[domain]:
                title = r["title"] or r["url"][:60]
                time_str = r["time"][11:16] if len(r["time"]) > 16 else ""
                lines.append(f"- [{title}]({r['url']}) - {r['device']} {time_str}")
            lines.append("")

    elif group_by == "date":
        # Group by date
        by_date = defaultdict(list)
        for r in results:
            date_key = r["time"][:10]
            by_date[date_key].append(r)

        for date_key in sorted(by_date.keys(), reverse=True):
            lines.append(f"## {date_key}")
            lines.append("")
            for r in by_date[date_key]:
                title = r["title"] or r["url"][:60]
                time_str = r["time"][11:16] if len(r["time"]) > 16 else ""
                lines.append(f"- [{title}]({r['url']}) - {r['device']} {time_str}")
            lines.append("")

    else:
        # Flat list grouped by date (default)
        by_date = defaultdict(list)
        for r in results:
            date_key = r["time"][:10]
            by_date[date_key].append(r)

        for date_key in sorted(by_date.keys(), reverse=True):
            lines.append(f"## {date_key}")
            lines.append("")
            for r in by_date[date_key]:
                title = r["title"] or r["url"][:60]
                time_str = r["time"][11:16] if len(r["time"]) > 16 else ""
                lines.append(f"- [{title}]({r['url']}) - {r['device']} - {time_str}")
            lines.append("")

    return "\n".join(lines)


def format_json(results: list[dict], query: str, date_range: tuple[datetime, datetime]) -> str:
    """Format results as JSON."""
    start, end = date_range

    output = {
        "query": query,
        "date_range": {
            "start": start.isoformat(),
            "end": end.isoformat(),
        },
        "total": len(results),
        "results": results,
    }

    return json.dumps(output, indent=2, ensure_ascii=False)


def main():
    parser = argparse.ArgumentParser(
        description="Query browsing history from synced devices"
    )
    parser.add_argument(
        "query",
        nargs="?",
        default="",
        help="Natural language query (e.g., 'yesterday', 'last week', 'articles about AI')"
    )
    parser.add_argument(
        "--device",
        help="Filter by device (iPhone, iPad, Mac, desktop, mobile, phone, tablet)"
    )
    parser.add_argument(
        "--days",
        type=int,
        help="Number of days back to search"
    )
    parser.add_argument(
        "--domain",
        help="Filter by domain (partial match)"
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=200,
        help="Maximum results (default: 200)"
    )
    parser.add_argument(
        "--format",
        choices=["markdown", "json"],
        default="markdown",
        help="Output format (default: markdown)"
    )
    parser.add_argument(
        "--output",
        help="Save to file instead of stdout"
    )
    parser.add_argument(
        "--summary",
        action="store_true",
        help="When saving to file, print only a brief summary (count and sample) to stdout"
    )
    parser.add_argument(
        "--group-by",
        choices=["domain", "category", "date"],
        help="Group results by domain, category, or date"
    )
    parser.add_argument(
        "--categorize",
        action="store_true",
        help="Use LLM to categorize URLs"
    )

    args = parser.parse_args()

    # Determine date range
    if args.days:
        start = datetime.now() - timedelta(days=args.days)
        end = datetime.now()
    else:
        start, end = parse_time_query(args.query)

    # Determine device filter
    devices = None
    if args.device:
        device_key = args.device.lower()
        if device_key in DEVICE_ALIASES:
            devices = DEVICE_ALIASES[device_key]
        else:
            devices = [args.device]

    # Extract search terms from query
    search_terms = extract_search_terms(args.query)

    # Query database
    try:
        results = query_history(
            start_date=start,
            end_date=end,
            devices=devices,
            domain_filter=args.domain,
            search_terms=search_terms,
            limit=args.limit
        )
    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    # Categorize if requested
    if args.categorize or args.group_by == "category":
        results = categorize_with_llm(results)

    # Format output
    if args.format == "json":
        output = format_json(results, args.query, (start, end))
    else:
        output = format_markdown(
            results,
            args.query or (f"last {args.days} days" if args.days else "last 24 hours"),
            group_by=args.group_by,
            date_range=(start, end)
        )

    # Output
    if args.output:
        output_path = Path(args.output).expanduser()
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(output, encoding="utf-8")
        if args.summary:
            lines = output.splitlines()
            if len(lines) <= 4:
                sample_lines = lines
            else:
                sample_lines = lines[:2] + lines[-2:]

            print(f"Exported {len(results)} records to {output_path}")
            if sample_lines:
                print("Sample:")
                print("\n".join(sample_lines))
        else:
            print(f"Saved to: {output_path}")
    else:
        print(output)


if __name__ == "__main__":
    main()
