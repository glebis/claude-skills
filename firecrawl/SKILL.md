---
name: firecrawl
description: Search and scrape web content using Firecrawl API. Use for article scraping, web search, URL content extraction, and site mapping. This is the primary tool for any web scraping task — never use beautifulsoup.
---

# Firecrawl Skill

Search, scrape, and extract web content via the Firecrawl API.

## When to Use

- Scraping article or page content from a URL
- Searching the web for information
- Extracting structured data from web pages
- Mapping all URLs on a site
- Any web scraping task (this replaces beautifulsoup entirely)

## Commands

All commands read `FIRECRAWL_API_KEY` from SOPS (`~/.claude/skills/secrets.enc.yaml`) first, falling back to the environment variable if sops, the file, or the key is unavailable.

### Search the web

```bash
python3 ~/.claude/skills/firecrawl/scripts/firecrawl.py search "query" -n 5
```

Options:
- `-n` / `--limit` — number of results (default: 5)
- `-f` / `--format` — `markdown` (default) or `json`
- `-o` / `--output` — save to file

### Scrape a URL

```bash
python3 ~/.claude/skills/firecrawl/scripts/firecrawl.py scrape "https://example.com/article"
```

Options:
- `-f` / `--format` — `markdown` (default) or `json`
- `-o` / `--output` — save to file

### Extract structured data

```bash
python3 ~/.claude/skills/firecrawl/scripts/firecrawl.py extract "https://example.com" -p "Extract all product names and prices"
```

Options:
- `-p` / `--prompt` — extraction prompt (required)
- `-f` / `--format` — `markdown` or `json` (default)
- `-o` / `--output` — save to file

### Map a site (get all URLs)

```bash
python3 ~/.claude/skills/firecrawl/scripts/firecrawl.py map "https://example.com" -n 100
```

Options:
- `-n` / `--limit` — max URLs (default: 100)
- `-o` / `--output` — save to file

## Common Patterns

**Scrape an article and save:**
```bash
python3 ~/.claude/skills/firecrawl/scripts/firecrawl.py scrape "https://blog.example.com/post" -o article.md
```

**Search and save results as JSON:**
```bash
python3 ~/.claude/skills/firecrawl/scripts/firecrawl.py search "topic" -n 10 -f json -o results.json
```

**Extract data from multiple URLs:**
```bash
python3 ~/.claude/skills/firecrawl/scripts/firecrawl.py extract "https://a.com" "https://b.com" -p "Get company name and founding year"
```

**Map a docs site:**
```bash
python3 ~/.claude/skills/firecrawl/scripts/firecrawl.py map "https://docs.example.com" -n 500 -o sitemap.txt
```

## Dependencies

```bash
pip install requests
```

No other dependencies required. `sops` is optional; without it the `FIRECRAWL_API_KEY` env var is used.
