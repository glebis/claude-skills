# Chrome History Query Skill

Query your Chrome browsing history using natural language. Searches **both desktop history AND synced mobile/tablet history**.

## Features

- **Desktop + Mobile History**: Queries SQLite (desktop) and LevelDB (synced devices)
- **Natural Language Queries**: "articles I read yesterday" or "scientific papers from last week"
- **Title Search**: Direct title/URL search for queries >10 chars without time keywords
- **Smart Filtering**: Excludes noise (social media, email, redirects)
- **Content Clustering**: Results grouped by type (reading, research, tools, events)
- **Date Range Support**: Yesterday, today, last week, last month, last 2 weeks
- **Source Tags**: Results show `[desktop]` or `[synced]` origin

## Installation

Copy to your Claude Code skills folder:

```bash
cp -r chrome-history ~/.claude/skills/
```

Install dependency for synced history (LevelDB parsing):

```bash
pip install git+https://github.com/cclgroupltd/ccl_chromium_reader.git
```

Without this dependency, synced mobile history won't be available (desktop history still works).

## Usage

### Basic Queries

```bash
# Time-based queries (desktop history)
python3 ~/.claude/skills/chrome-history/chrome_history_query.py "articles I read yesterday"
python3 ~/.claude/skills/chrome-history/chrome_history_query.py "research this week"
python3 ~/.claude/skills/chrome-history/chrome_history_query.py "last month"

# Title search (desktop + synced history)
python3 ~/.claude/skills/chrome-history/chrome_history_query.py "Introducing Cosmos"
python3 ~/.claude/skills/chrome-history/chrome_history_query.py "how-to-build-a-rag"
```

### Query Patterns

**By Date:**
- "yesterday" → previous day only
- "today" → today only
- "last week" → past 7 days
- "last month" → past 30 days
- "last 2 weeks" → past 14 days

**By Content Type:**
- "articles I read" → news/blogs/essays (reading cluster)
- "scientific articles" → research papers (research cluster)
- "research" / "code" → technical docs, GitHub repos
- "reading" → all articles/news

**By Keywords:**
- "about AI" → pages mentioning AI
- "about climate" → pages mentioning climate
- "about machine learning" → pages mentioning ML

**By Specific Sites:**
- "on reddit" → reddit.com only
- "from medium" → medium.com only
- "code repos" → GitHub repos
- "twitter posts" → twitter.com only

### Full Query Examples

```bash
# What articles did I read yesterday?
python3 ~/.claude/skills/chrome-history/chrome_history_query.py "articles I read yesterday"

# Scientific papers from the past week
python3 ~/.claude/skills/chrome-history/chrome_history_query.py "scientific articles for the last week"

# Reddit threads from the past month
python3 ~/.claude/skills/chrome-history/chrome_history_query.py "reddit threads last month"

# Research on specific topic
python3 ~/.claude/skills/chrome-history/chrome_history_query.py "research about machine learning this week"

# Code repos I visited this week
python3 ~/.claude/skills/chrome-history/chrome_history_query.py "code this week"

# All research sites from today
python3 ~/.claude/skills/chrome-history/chrome_history_query.py "research today"
```

## Content Clustering

Results are automatically grouped by type:

- **Reading**: News articles, blogs, essays, newsletters
  - Sources: Economist, Medium, NYTimes, Substack, Fast Company, Psychology Today, etc.

- **Research**: Technical documentation, papers, source code
  - Sources: GitHub, Stack Overflow, ArXiv, Wikipedia, Hugging Face, MDN, etc.

- **Tools**: Applications, services, productivity tools
  - Sources: OpenAI, Claude, banking apps, password managers, etc.

- **Events**: Calendar, ticketing, announcements
  - Sources: Eventbrite, Meetup, announcement sites, etc.

- **Other**: Uncategorized sites

## What Gets Filtered Out

Automatically excluded to reduce noise:

**Social Media**: Facebook, Instagram, Twitter, TikTok, LinkedIn, Threads, Reddit, Mastodon

**Email**: Gmail, Outlook, mail.google.com

**Shopping**: Amazon, eBay, Pinterest

**Utilities**: FreeFeed, YouTube

**Wrappers**: Google redirect URLs (google.com/url)

## Output Format

Results are displayed as:

```
## Chrome History: articles I read yesterday
*Found 9 items*

### Reading (9)
- 23:08 Article title goes here
  https://example.com/article
- 22:15 Another article title
  https://example.com/another-article

### Research (3)
- 14:32 GitHub repo name
  https://github.com/user/repo
```

- **Time**: Visit time in HH:MM format
- **Title**: Full page title (truncated at 75 chars)
- **URL**: Direct link to the page

## How It Works

1. **Dual Database Access**:
   - **Desktop**: SQLite database (`~/Library/.../Chrome/Default/History`)
   - **Synced**: LevelDB database (`~/Library/.../Chrome/Default/Sync Data/LevelDB/`)
2. **Query Detection**: Queries >10 chars without time keywords trigger title search across both sources
3. **Lock Avoidance**: Copies databases to `/tmp/` to avoid conflicts with running Chrome
4. **Smart Filtering**: Excludes blocked domains and noise
5. **Clustering**: Categorizes by domain type
6. **Deduplication**: Shows each URL once with source tag

## Configuration

- **Desktop History DB**: `~/Library/Application Support/Google/Chrome/Default/History`
- **Synced History DB**: `~/Library/Application Support/Google/Chrome/Default/Sync Data/LevelDB/`
- **Temp Copies**: `/tmp/chrome_history_temp`, `/tmp/chrome_sync_leveldb_copy`

## Requirements

- Python 3.7+
- SQLite3 (built-in)
- macOS with Google Chrome installed
- `ccl_chromium_reader` (optional, for synced history)

## Limitations

- **Synced History**: No timestamps available (LevelDB doesn't store visit times reliably)
- **Keyword Matching**: Only matches keywords in URL and page title, not full page content
- **Platform Specific**: macOS only (Chrome history location varies by OS)
- **Title Search**: Queries with time keywords use desktop history only

## Future Improvements

- [ ] Full-text search using indexed content
- [ ] Cross-browser support (Firefox, Safari)
- [ ] Linux/Windows support
- [ ] Export to CSV/JSON
- [ ] Weekly/monthly summaries
- [ ] Time-of-day analysis (when you read vs. code)
- [ ] Domain visit frequency stats
- [ ] Integration with Obsidian daily notes

## Examples

### Check yesterday's reading
```bash
python3 ~/.claude/skills/chrome-history/chrome_history_query.py "articles I read yesterday"
```

Output:
```
## Chrome History: articles I read yesterday
*Found 12 items*

### Reading (12)
- 14:22 The Future of AI: What We Know and Don't Know
  https://example.com/ai-future
- 13:45 How to Build Better Habits
  https://example.com/habits
...
```

### Find this week's research
```bash
python3 ~/.claude/skills/chrome-history/chrome_history_query.py "research this week"
```

Output:
```
## Chrome History: research this week
*Found 34 items*

### Research (34)
- 16:32 anthropics/claude-code: Official CLI for Claude
  https://github.com/anthropics/claude-code
- 15:18 [2511.02208] Training Proactive and Personalized LLM Agents
  https://arxiv.org/abs/2511.02208
...
```

## Troubleshooting

### "No Chrome history found"
- Ensure Chrome is closed (or history DB is not locked)
- Check that `~/Library/Application Support/Google/Chrome/Default/History` exists
- Try again after closing Chrome completely

### "Permission denied"
- May need to grant Full Disk Access to Terminal
- System Preferences → Security & Privacy → Full Disk Access → Terminal

### Empty results with keywords
- Keyword matching only works with URL/title text
- Try without keywords or use site-specific filters instead
- Example: Instead of "about AI today", try "research today"

## Author

Created for Gleb Kalinin's personal knowledge management system.

## License

MIT
