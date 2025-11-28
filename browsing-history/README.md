# Browsing History Skill

Query browsing history from **all synced Chrome devices** (iPhone, iPad, Mac, desktop) with natural language.

## How It Differs from chrome-history

| Feature | chrome-history | browsing-history |
|---------|---------------|------------------|
| Data source | Local Chrome SQLite | Synced database (`~/data/browsing.db`) |
| Devices | Desktop only | All synced devices (iPhone, iPad, Mac, etc.) |
| Timestamps | Chrome visit time | Actual visit time with fallback |
| Categorization | Domain-based clusters | LLM-powered classification |
| Output formats | Markdown only | Markdown + JSON |
| Save to file | No | Yes |

## Prerequisites

### 1. Initialize Database

```bash
python3 ~/.claude/skills/browsing-history/scripts/init_db.py
```

### 2. Sync Chrome History

For local desktop history:
```bash
python3 ~/.claude/skills/browsing-history/scripts/sync_chrome_history.py
```

For synced devices (iPhone, iPad, etc.), you need a separate sync process that:
1. Parses Chrome Sync LevelDB data
2. Extracts URLs with device info and timestamps
3. Inserts into `~/data/browsing.db`

See [AnyBrowserHistory](https://github.com/nickolay/nickolay.github.io/tree/master/AnyBrowserHistory) for Chrome Sync parsing reference.

### 3. (Optional) LLM Categorization

Install llm CLI for smart categorization:
```bash
pip install llm llm-anthropic
llm keys set anthropic  # Enter your API key
```

## Usage

### Basic Queries

```bash
# Yesterday's history
python3 ~/.claude/skills/browsing-history/browsing_query.py "yesterday"

# Last week from iPhone
python3 ~/.claude/skills/browsing-history/browsing_query.py "last week" --device iPhone

# Search for AI articles
python3 ~/.claude/skills/browsing-history/browsing_query.py "AI" --days 7
```

### Grouping

```bash
# Group by domain
python3 ~/.claude/skills/browsing-history/browsing_query.py "today" --group-by domain

# Group by LLM-classified category
python3 ~/.claude/skills/browsing-history/browsing_query.py "today" --categorize --group-by category
```

### Save to File

```bash
# Save as markdown to Obsidian vault
python3 ~/.claude/skills/browsing-history/browsing_query.py "yesterday" \
  --output ~/Research/vault/browsing-history.md

# Save as JSON
python3 ~/.claude/skills/browsing-history/browsing_query.py "last week" \
  --format json --output history.json
```

## Options

| Option | Description |
|--------|-------------|
| `--device` | Filter: iPhone, iPad, Mac, desktop, mobile |
| `--days` | Number of days back |
| `--domain` | Filter by domain (partial match) |
| `--limit` | Max results (default: 200) |
| `--format` | Output: markdown (default) or json |
| `--output` | Save to file |
| `--group-by` | Group by: domain, category, or date |
| `--categorize` | Use LLM for smart categorization |

## Database Schema

```sql
CREATE TABLE browsing_history (
    id INTEGER PRIMARY KEY,
    url TEXT NOT NULL,
    title TEXT,
    device_type TEXT,        -- iPhone, iPad, Mac, desktop, etc.
    device_id TEXT,
    source_machine TEXT,
    first_seen TIMESTAMP,    -- When imported
    source TEXT,             -- chrome_sync or chrome_desktop
    domain TEXT,
    visit_time TIMESTAMP,    -- Actual visit time
    UNIQUE(url, device_id)
);
```

## Example Queries

| User Request | Command |
|--------------|---------|
| "Articles I read yesterday" | `browsing_query.py "yesterday"` |
| "iPhone tabs from last week" | `browsing_query.py "last week" --device iPhone` |
| "Find economics articles" | `browsing_query.py "economics" --days 7` |
| "Group by category" | `browsing_query.py "today" --categorize --group-by category` |
| "Save to Obsidian" | `browsing_query.py "yesterday" --output ~/vault/history.md` |
