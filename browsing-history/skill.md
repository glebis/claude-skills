---
name: browsing-history
description: Query browsing history from all synced devices (iPhone, Mac, iPad, desktop). Supports natural language queries for filtering by date, device, domain, and keywords. Uses LLM classification for content categories. Can output to stdout or save as markdown/JSON to Obsidian vault.
---

# Browsing History Skill

Query browsing history from all synced devices with natural language.

## When to Use

Use this skill when the user asks about:
- Articles/pages they read (yesterday, last week, etc.)
- Browsing history from specific devices (iPhone, iPad, desktop)
- Finding pages by topic, domain, or keyword
- Exporting browsing history to files
- Grouping history by category or domain

## Database

Location: `~/data/browsing.db`

Synced devices: iPhone, iPad, Mac, desktop, Android

### Timestamps
- **visit_time**: Actual visit timestamp from Chrome (100% coverage for all devices)
- **first_seen**: Import timestamp (fallback when visit_time unavailable)

The skill uses `COALESCE(visit_time, first_seen)` for accurate time-based queries.

## Usage

```bash
python3 ~/.claude/skills/browsing-history/browsing_query.py "<query>" [options]
```

### Options

| Option | Description | Example |
|--------|-------------|---------|
| `--device` | Filter by device | `--device iPhone` |
| `--days` | Number of days back | `--days 7` |
| `--domain` | Filter by domain | `--domain medium.com` |
| `--limit` | Max results | `--limit 50` |
| `--format` | Output format | `--format json` |
| `--output` | Save to file | `--output history.md` |
| `--group-by` | Group results | `--group-by domain` or `--group-by category` |
| `--categorize` | Use LLM to categorize | `--categorize` |

### Example Queries

**Basic queries:**
```bash
# Yesterday's browsing history
python3 ~/.claude/skills/browsing-history/browsing_query.py "yesterday"

# Articles from iPhone yesterday
python3 ~/.claude/skills/browsing-history/browsing_query.py "yesterday" --device iPhone

# Last week's history grouped by domain
python3 ~/.claude/skills/browsing-history/browsing_query.py "last week" --group-by domain

# Find articles about economics
python3 ~/.claude/skills/browsing-history/browsing_query.py "economics" --days 7
```

**Save to Obsidian:**
```bash
# Save yesterday's history as markdown
python3 ~/.claude/skills/browsing-history/browsing_query.py "yesterday" \
  --output ~/Research/vault/browsing-2025-11-27.md

# Save with LLM categorization
python3 ~/.claude/skills/browsing-history/browsing_query.py "yesterday" \
  --categorize --group-by category \
  --output ~/Research/vault/browsing-categorized.md

# Save as JSON
python3 ~/.claude/skills/browsing-history/browsing_query.py "last week" \
  --format json --output ~/Research/vault/history.json
```

**Device-specific:**
```bash
# iPhone tabs
python3 ~/.claude/skills/browsing-history/browsing_query.py "yesterday" --device iPhone

# Desktop history
python3 ~/.claude/skills/browsing-history/browsing_query.py "today" --device desktop

# All mobile devices
python3 ~/.claude/skills/browsing-history/browsing_query.py "yesterday" --device mobile
```

**Search and filter:**
```bash
# Sites starting with "joy"
python3 ~/.claude/skills/browsing-history/browsing_query.py "joy" --days 7

# Medium.com articles
python3 ~/.claude/skills/browsing-history/browsing_query.py "last month" --domain medium.com
```

## Natural Language Patterns

The script recognizes:

| Pattern | Interpretation |
|---------|----------------|
| `yesterday` | Previous day |
| `today` | Current day |
| `last week` | Past 7 days |
| `last month` | Past 30 days |
| `last N days` | Past N days |

Keywords are searched in URL and title.

## Output Formats

### Markdown (default)
```markdown
# Browsing History: yesterday

*47 unique URLs from 2025-11-27*

## 2025-11-27

- [Article Title](https://example.com/article) - iPhone - 14:32
- [Another Page](https://another.com/page) - desktop - 16:45
```

### Markdown with categories (--categorize --group-by category)
```markdown
# Browsing History: yesterday

## News & Current Events
- [Breaking: Something Happened](https://news.com/...) - iPhone

## Technology & Programming
- [How to Build APIs](https://dev.to/...) - desktop

## Research & Learning
- [Academic Paper on AI](https://arxiv.org/...) - Mac
```

### JSON (--format json)
```json
{
  "query": "yesterday",
  "date_range": "2025-11-27",
  "total": 47,
  "results": [
    {"url": "...", "title": "...", "device": "iPhone", "time": "14:32", "category": "News"}
  ]
}
```

## Workflow Examples

**User: "Show me articles I read yesterday on my phone"**
```bash
python3 ~/.claude/skills/browsing-history/browsing_query.py "yesterday" --device iPhone
```

**User: "Save my browsing history from last week to Obsidian, grouped by category"**
```bash
python3 ~/.claude/skills/browsing-history/browsing_query.py "last week" \
  --categorize --group-by category \
  --output ~/Research/vault/browsing-week.md
```

**User: "Help me find that article about economics I read on my computer"**
```bash
python3 ~/.claude/skills/browsing-history/browsing_query.py "economics" \
  --device desktop --days 7
```

**User: "Sites that start with 'joy' from last week"**
```bash
python3 ~/.claude/skills/browsing-history/browsing_query.py "joy" --days 7
```

## Notes

- URLs are deduplicated per day (same URL on same day = one entry)
- **visit_time**: Actual visit timestamps from Chrome history
  - Desktop: 100% coverage (from Chrome SQLite `last_visit_time`)
  - Mobile: 100% coverage (extracted from Chrome Sync LevelDB)
- **first_seen**: Fallback import timestamp (~15min resolution)
- LLM categorization uses Claude 3.5 Haiku via `llm` CLI
