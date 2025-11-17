---
name: chrome-history
description: Query Chrome browsing history with natural language. Filter by date range, article type, keywords, and specific sites.
---

# Chrome History Query Skill

Search and filter your Chrome browsing history using natural language queries.

## What It Does

1. Parses natural language queries to understand date ranges and filters
2. Queries Chrome's SQLite history database
3. Filters out noise (social media, email, redirects)
4. Groups results by type (reading, research, tools, events)
5. Returns formatted markdown with links

## Supported Queries

### Date Range
- "yesterday" → previous day only
- "today" → today only
- "last week" → past 7 days
- "last month" → past 30 days
- "last 2 weeks" → past 14 days

### Content Filters
- "articles I read" → reading cluster (news, blogs, essays)
- "scientific articles" → research cluster (papers, docs)
- "code/research" → GitHub, Stack Overflow, docs

### Keyword Filtering
- "articles about AI" → finds pages mentioning AI
- "scientific articles about climate" → finds research pages mentioning climate

### Site-Specific
- "reddit threads" → reddit.com only
- "on medium" → medium.com only
- "twitter posts" → twitter.com only

## Example Queries

```
"articles I read yesterday"
"articles about AI I read yesterday"
"scientific articles for the last week"
"research about machine learning this week"
"reddit threads last month"
"code repos I visited yesterday"
"on medium this week"
```

## Usage

Run directly with a query:
```bash
python3 ~/.claude/skills/chrome-history/chrome_history_query.py "articles I read yesterday"
```

Or integrate into Claude Code when user asks:
- "Show me articles I read yesterday"
- "What scientific papers did I look at last week?"
- "Show reddit threads I visited last month"
- "Articles about AI from yesterday?"

## Configuration

- **Chrome History**: `~/Library/Application Support/Google/Chrome/Default/History`
- **Vault Location**: `/Users/glebkalinin/Brains/brain`
- **Filtered Sites**: Social media, email, Google redirect wrappers
- **Clustering**: Automatic by domain type (reading, research, tools, events)

## Exclusions

Automatically filters out:
- Social media: Facebook, Instagram, Twitter, TikTok, Reddit, LinkedIn
- Email: Gmail, Outlook
- Shopping: Amazon, eBay
- Google redirects: google.com/url wrappers
- Utility sites: FreeFeed, YouTube

## Output Format

Results grouped by content type with timestamps:

```
## Chrome History: articles about AI yesterday

*Found 5 items*

### Reading (3)
- 14:22 [The more that people use AI...](url)
- 16:38 [AI makes you smarter but...](url)

### Research (2)
- 11:23 [GitHub: AI project](url)
```
