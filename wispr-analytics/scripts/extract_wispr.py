#!/usr/bin/env python3
"""
Extract Wispr Flow dictation data from local SQLite database.

Usage:
    python3 extract_wispr.py [--period today|week|month|YYYY-MM-DD|YYYY-MM-DD:YYYY-MM-DD] [--mode all|technical|soft|trends|mental] [--format json|markdown] [--output PATH]

Modes:
    all       - Full analysis (default)
    technical - Coding/work patterns, app usage, productivity metrics
    soft      - Communication patterns, language use, interpersonal context
    trends    - Dictation volume, frequency changes, time-of-day patterns
    mental    - Sentiment indicators, energy proxies, activity pattern changes

Period shortcuts:
    today     - Current day
    yesterday - Previous day
    week      - Last 7 days
    month     - Last 30 days
    YYYY-MM-DD           - Specific date
    YYYY-MM-DD:YYYY-MM-DD - Date range
"""

import sqlite3
import json
import argparse
import os
import sys
from datetime import datetime, timedelta
from collections import Counter, defaultdict
from pathlib import Path

DB_PATH = os.path.expanduser("~/Library/Application Support/Wispr Flow/flow.sqlite")

APP_CATEGORIES = {
    "coding": [
        "com.googlecode.iterm2", "com.microsoft.VSCode",
        "com.exafunction.windsurf", "dev.zed.Zed",
        "com.cursor.Cursor", "com.apple.Terminal"
    ],
    "ai_tools": [
        "com.openai.chat", "com.anthropic.claudefordesktop",
        "ai.perplexity.comet", "com.openai.atlas"
    ],
    "communication": [
        "ru.keepcoder.Telegram", "com.apple.MobileSMS",
        "com.tinyspeck.slackmacgap", "us.zoom.xos"
    ],
    "writing": [
        "md.obsidian", "com.apple.Notes",
        "com.google.Chrome", "company.thebrowser.Browser"
    ],
}

def get_category(app_id):
    for cat, apps in APP_CATEGORIES.items():
        if app_id in apps:
            return cat
    return "other"

def parse_period(period_str):
    """Return (start_datetime_str, end_datetime_str) for SQL WHERE clause."""
    now = datetime.now()
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)

    if period_str == "today":
        start = today_start
        end = now
    elif period_str == "yesterday":
        start = today_start - timedelta(days=1)
        end = today_start
    elif period_str == "week":
        start = today_start - timedelta(days=7)
        end = now
    elif period_str == "month":
        start = today_start - timedelta(days=30)
        end = now
    elif ":" in period_str:
        parts = period_str.split(":")
        start = datetime.strptime(parts[0], "%Y-%m-%d")
        end = datetime.strptime(parts[1], "%Y-%m-%d").replace(hour=23, minute=59, second=59)
    else:
        start = datetime.strptime(period_str, "%Y-%m-%d")
        end = start.replace(hour=23, minute=59, second=59)

    return start.strftime("%Y-%m-%d %H:%M:%S"), end.strftime("%Y-%m-%d %H:%M:%S")

def extract_data(period="today"):
    """Extract dictation data for the given period."""
    start, end = parse_period(period)

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("""
        SELECT transcriptEntityId, formattedText, asrText, timestamp,
               app, url, numWords, duration, language, detectedLanguage,
               speechDuration
        FROM History
        WHERE isArchived = 0
          AND timestamp >= ? AND timestamp <= ?
          AND formattedText IS NOT NULL AND formattedText != ''
        ORDER BY timestamp ASC
    """, (start, end))

    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return rows, start, end

def compute_stats(rows):
    """Compute quantitative statistics from dictation data."""
    if not rows:
        return {"total_dictations": 0, "message": "No dictations found for this period."}

    total_words = sum(r["numWords"] or 0 for r in rows)
    total_duration = sum(r["duration"] or 0 for r in rows)
    total_speech = sum(r["speechDuration"] or 0 for r in rows)

    # App distribution
    app_counts = Counter(r["app"] for r in rows if r["app"])
    app_words = defaultdict(int)
    for r in rows:
        if r["app"]:
            app_words[r["app"]] += r["numWords"] or 0

    # Category distribution
    cat_counts = Counter(get_category(r["app"]) for r in rows if r["app"])
    cat_words = defaultdict(int)
    for r in rows:
        if r["app"]:
            cat_words[get_category(r["app"])] += r["numWords"] or 0

    # Language distribution
    lang_counts = Counter(r["detectedLanguage"] or r["language"] or "unknown" for r in rows)

    # Hourly distribution
    hourly = Counter()
    for r in rows:
        if r["timestamp"]:
            try:
                ts = r["timestamp"].split(" ")[1].split(":")[0]
                hourly[int(ts)] += 1
            except (IndexError, ValueError):
                pass

    # Average words per dictation
    avg_words = total_words / len(rows) if rows else 0

    # Longest dictations
    longest = sorted(rows, key=lambda r: r["numWords"] or 0, reverse=True)[:5]

    return {
        "total_dictations": len(rows),
        "total_words": total_words,
        "total_duration_seconds": round(total_duration, 1),
        "total_speech_seconds": round(total_speech or 0, 1),
        "avg_words_per_dictation": round(avg_words, 1),
        "app_distribution": dict(app_counts.most_common(15)),
        "app_words": dict(sorted(app_words.items(), key=lambda x: x[1], reverse=True)[:15]),
        "category_distribution": dict(cat_counts.most_common()),
        "category_words": dict(sorted(cat_words.items(), key=lambda x: x[1], reverse=True)),
        "language_distribution": dict(lang_counts.most_common()),
        "hourly_distribution": dict(sorted(hourly.items())),
        "longest_dictations": [
            {"text": d["formattedText"][:200], "words": d["numWords"], "app": d["app"]}
            for d in longest
        ],
    }

def compute_trends(rows):
    """Compute daily trends for multi-day periods."""
    daily = defaultdict(lambda: {"count": 0, "words": 0, "duration": 0, "apps": Counter()})
    for r in rows:
        if r["timestamp"]:
            day = r["timestamp"].split(" ")[0]
            daily[day]["count"] += 1
            daily[day]["words"] += r["numWords"] or 0
            daily[day]["duration"] += r["duration"] or 0
            if r["app"]:
                daily[day]["apps"][get_category(r["app"])] += 1

    trend_data = []
    for day in sorted(daily.keys()):
        d = daily[day]
        trend_data.append({
            "date": day,
            "dictations": d["count"],
            "words": d["words"],
            "duration_min": round(d["duration"] / 60, 1),
            "top_category": d["apps"].most_common(1)[0][0] if d["apps"] else "none",
        })
    return trend_data

def extract_texts_by_mode(rows, mode):
    """Extract relevant text samples for LLM analysis based on mode."""
    if mode == "technical":
        filtered = [r for r in rows if get_category(r["app"]) in ("coding", "ai_tools")]
    elif mode == "soft":
        filtered = [r for r in rows if get_category(r["app"]) in ("communication", "writing")]
    elif mode == "mental":
        filtered = rows  # all text relevant for mental health
    else:
        filtered = rows

    # Sample strategy: take all if <100, otherwise proportional sample
    if len(filtered) <= 100:
        sample = filtered
    else:
        step = len(filtered) / 100
        sample = [filtered[int(i * step)] for i in range(100)]

    return [
        {
            "text": r["formattedText"],
            "timestamp": r["timestamp"],
            "app": r["app"],
            "words": r["numWords"],
            "category": get_category(r["app"]) if r["app"] else "unknown",
            "language": r["detectedLanguage"] or r["language"] or "unknown",
        }
        for r in sample if r["formattedText"]
    ]

def format_markdown_stats(stats, period, trends=None):
    """Format statistics as markdown."""
    lines = []
    lines.append(f"## Wispr Flow Analytics: {period}")
    lines.append("")
    lines.append(f"- **Total dictations**: {stats['total_dictations']}")
    lines.append(f"- **Total words**: {stats['total_words']:,}")
    lines.append(f"- **Total speech time**: {stats.get('total_speech_seconds', 0) / 60:.1f} min")
    lines.append(f"- **Avg words/dictation**: {stats['avg_words_per_dictation']}")
    lines.append("")

    # Category breakdown
    lines.append("### Activity by Category")
    for cat, count in stats.get("category_distribution", {}).items():
        words = stats.get("category_words", {}).get(cat, 0)
        lines.append(f"- **{cat}**: {count} dictations, {words:,} words")
    lines.append("")

    # Language
    lines.append("### Language Distribution")
    for lang, count in stats.get("language_distribution", {}).items():
        lines.append(f"- {lang}: {count}")
    lines.append("")

    # Hourly
    if stats.get("hourly_distribution"):
        lines.append("### Hourly Activity")
        for hour, count in stats["hourly_distribution"].items():
            bar = "#" * min(count, 40)
            lines.append(f"- {hour:02d}:00 {bar} ({count})")
        lines.append("")

    # Trends
    if trends:
        lines.append("### Daily Trends")
        lines.append("| Date | Dictations | Words | Duration (min) | Top Category |")
        lines.append("|------|-----------|-------|----------------|--------------|")
        for t in trends:
            lines.append(f"| {t['date']} | {t['dictations']} | {t['words']:,} | {t['duration_min']} | {t['top_category']} |")
        lines.append("")

    # Top apps
    lines.append("### Top Apps")
    for app, count in list(stats.get("app_distribution", {}).items())[:10]:
        words = stats.get("app_words", {}).get(app, 0)
        short_name = app.split(".")[-1] if app else "unknown"
        lines.append(f"- **{short_name}**: {count} dictations, {words:,} words")

    return "\n".join(lines)

def main():
    parser = argparse.ArgumentParser(description="Extract Wispr Flow dictation data")
    parser.add_argument("--period", default="today",
                        help="today, yesterday, week, month, YYYY-MM-DD, or YYYY-MM-DD:YYYY-MM-DD")
    parser.add_argument("--mode", default="all",
                        choices=["all", "technical", "soft", "trends", "mental"],
                        help="Analysis mode")
    parser.add_argument("--format", default="json", choices=["json", "markdown"],
                        help="Output format")
    parser.add_argument("--output", default=None,
                        help="Output file path (default: stdout)")
    parser.add_argument("--texts-only", action="store_true",
                        help="Output only text samples for LLM analysis")

    args = parser.parse_args()

    rows, start, end = extract_data(args.period)
    period_label = f"{start} to {end}" if args.period not in ("today", "yesterday", "week", "month") else args.period

    if args.texts_only:
        texts = extract_texts_by_mode(rows, args.mode)
        result = json.dumps(texts, ensure_ascii=False, indent=2)
    elif args.format == "json":
        stats = compute_stats(rows)
        trends = compute_trends(rows) if len(set(r["timestamp"].split(" ")[0] for r in rows if r["timestamp"])) > 1 else None
        texts = extract_texts_by_mode(rows, args.mode)
        result = json.dumps({
            "period": period_label,
            "mode": args.mode,
            "stats": stats,
            "trends": trends,
            "text_samples": texts[:50],  # limit for JSON output
        }, ensure_ascii=False, indent=2)
    else:
        stats = compute_stats(rows)
        trends = compute_trends(rows) if len(set(r["timestamp"].split(" ")[0] for r in rows if r["timestamp"])) > 1 else None
        result = format_markdown_stats(stats, period_label, trends)

    if args.output:
        Path(args.output).parent.mkdir(parents=True, exist_ok=True)
        with open(args.output, "w") as f:
            f.write(result)
        print(f"Output written to {args.output}", file=sys.stderr)
    else:
        print(result)

if __name__ == "__main__":
    main()
