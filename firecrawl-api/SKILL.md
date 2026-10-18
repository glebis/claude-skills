---
name: firecrawl-api
description: Standalone Python script for the Firecrawl API (search, scrape, extract, map, plus Alexandria structured-data tools: discover, contract, run) that reads FIRECRAWL_API_KEY from SOPS with env fallback. Use when the official firecrawl CLI is unavailable or broken, or for scripted pipelines that need a plain Python dependency-light client. For normal web work prefer the official `firecrawl` CLI skill. Never use beautifulsoup.
---

# Firecrawl API script (firecrawl-api)

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
python3 ~/.claude/skills/firecrawl-api/scripts/firecrawl.py search "query" -n 5
```

Options:
- `-n` / `--limit` — number of results (default: 5)
- `-f` / `--format` — `markdown` (default) or `json`
- `-o` / `--output` — save to file

### Scrape a URL

```bash
python3 ~/.claude/skills/firecrawl-api/scripts/firecrawl.py scrape "https://example.com/article"
```

Options:
- `-f` / `--format` — `markdown` (default) or `json`
- `-o` / `--output` — save to file

### Extract structured data

```bash
python3 ~/.claude/skills/firecrawl-api/scripts/firecrawl.py extract "https://example.com" -p "Extract all product names and prices"
```

Options:
- `-p` / `--prompt` — extraction prompt (required)
- `-f` / `--format` — `markdown` or `json` (default)
- `-o` / `--output` — save to file

### Map a site (get all URLs)

```bash
python3 ~/.claude/skills/firecrawl-api/scripts/firecrawl.py map "https://example.com" -n 100
```

Options:
- `-n` / `--limit` — max URLs (default: 100)
- `-o` / `--output` — save to file

## Alexandria (structured data providers)

[Alexandria](https://www.firecrawl.dev/alexandria) is Firecrawl's catalogue of data providers that return typed, sourced records (e.g. arXiv papers, podcast episodes). Use it when the task needs the same fields across many entities, exact figures, or provenance; use plain search/scrape when web pages already answer the question. Requires an API key on a team with Alexandria access (the keyless tier has none).

Flow: discover → inspect contract → run. **Discovery, find-tools, and contract are free. `run` is billed at the tool's listed `creditsCost`.**

```bash
S=~/.claude/skills/firecrawl-api/scripts/firecrawl.py
python3 $S tools "arXiv paper metadata by ID"                  # free semantic discovery
python3 $S tools "podcast episodes about AI agents" --web      # + web results (billed)
python3 $S find-tools --providers arxiv-org --level tools      # free catalogue browse
python3 $S find-tools --urls https://arxiv.org                 # tools matched to a website
python3 $S find-tools --categories companies --level providers # providers in a category
python3 $S find-tools --request '<next JSON from a result>'    # follow a `next` link
python3 $S contract arxiv-org/papers/get_paper                 # inputs, response, price
python3 $S run arxiv-org/papers/get_paper --options '{"arxiv_id":"2608.21829"}' --max-credits 10
```

### Local catalog

[references/alexandria-catalog.md](references/alexandria-catalog.md) lists every category, provider, and tool with its listed price; [references/alexandria-catalog.json](references/alexandria-catalog.json) holds the same data for scripts. Grep it before running discovery, e.g. `grep -n -i "podcast" references/alexandria-catalog.md`. It is a dated snapshot: prices and coverage change, so confirm with `contract` before `run`. Refresh it (free, about 6 minutes because of the 12 requests/minute limit) with:

```bash
python3 ~/.claude/skills/firecrawl-api/scripts/build_catalog.py
```

Rules:
- A tool match is not data. Run `contract` and send exactly the inputs it declares.
- `run` looks up the contract first, then applies the spend policy in `allow_spend()` before executing.
- Every call prints a `Request ID` to stderr. Keep stderr separate from JSON on stdout (`2>/dev/null` or `2>log`).
- Never wrap `run` in a retry or `||` fallback: each execution is billed.
- Per-item errors in `data.alexandria[]` exit non-zero. A `THIRD_PARTY_DATA_TERMS_REQUIRED` error prints the terms URL: an org admin must accept them, and a data request does not authorize accepting terms.

## Common Patterns

**Scrape an article and save:**
```bash
python3 ~/.claude/skills/firecrawl-api/scripts/firecrawl.py scrape "https://blog.example.com/post" -o article.md
```

**Search and save results as JSON:**
```bash
python3 ~/.claude/skills/firecrawl-api/scripts/firecrawl.py search "topic" -n 10 -f json -o results.json
```

**Extract data from multiple URLs:**
```bash
python3 ~/.claude/skills/firecrawl-api/scripts/firecrawl.py extract "https://a.com" "https://b.com" -p "Get company name and founding year"
```

**Map a docs site:**
```bash
python3 ~/.claude/skills/firecrawl-api/scripts/firecrawl.py map "https://docs.example.com" -n 500 -o sitemap.txt
```

## Dependencies

```bash
pip install requests
```

No other dependencies required. `sops` is optional; without it the `FIRECRAWL_API_KEY` env var is used.
