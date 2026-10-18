---
name: firecrawl-api
description: This skill should be used for scripted Firecrawl API access from a dependency-light Python script (search, scrape, extract, map) and for Firecrawl Alexandria structured-data tools (discover, inspect contract, run with a spend ceiling), including a local catalog of all Alexandria providers and tools. Use it when the official `firecrawl` CLI skill is unavailable or broken, when a pipeline needs a plain Python client, or when browsing the Alexandria catalog offline. The API key is read from SOPS with env fallback. For ordinary interactive web work prefer the official `firecrawl` CLI skill. Never use beautifulsoup.
---

# Firecrawl API script (firecrawl-api)

A standalone Python client for the Firecrawl API, with Alexandria support and a dated local catalog of its tools.

## When to Use

- The official `firecrawl` CLI is missing, broken, or not allowed in the environment.
- A script or pipeline needs a plain Python client instead of a Node CLI.
- A task needs structured records from an Alexandria provider, with an enforced per-run spend ceiling.
- Looking up which Alexandria providers and tools exist, without spending credits or network calls.

For everyday searching and scraping in an interactive session, use the official `firecrawl` skill instead.

## Setup

`FIRECRAWL_API_KEY` is read from SOPS (`~/.claude/skills/secrets.enc.yaml`) first, then from the environment if sops, the file, or the key is unavailable. The only dependency is `requests`. `sops` is optional.

All commands below use:

```bash
S=~/.claude/skills/firecrawl-api/scripts/firecrawl.py
```

`-o FILE` saves stdout to FILE only if the command succeeds. On failure the file is left unchanged and nothing is reported as saved.

## Web commands (v1 API)

```bash
python3 $S search "query" -n 5 [-f json] [-o out.md]      # web search with page markdown
python3 $S scrape "https://example.com/article" [-o page.md]
python3 $S extract "https://a.com" "https://b.com" -p "Get company name and founding year"
python3 $S map "https://docs.example.com" -n 500 -o sitemap.txt
```

`extract` defaults to JSON output. Timeouts: 120 s, or 300 s for `extract`.

## Alexandria (structured data providers)

[Alexandria](https://www.firecrawl.dev/alexandria) is Firecrawl's catalogue of data providers that return typed, sourced records (e.g. arXiv papers, podcast episodes). Use it when a task needs the same fields across many entities, exact figures, or provenance. Use web search or scrape when pages already answer the question. It requires an API key on a team with Alexandria access; the keyless tier has none.

Flow: check the local catalog → inspect the contract → run.

```bash
python3 $S tools "arXiv paper metadata by ID"                  # free semantic discovery
python3 $S find-tools --providers arxiv-org --level tools      # free catalogue browse
python3 $S find-tools --urls https://arxiv.org                 # tools matched to a website
python3 $S find-tools --categories companies --level providers # providers in a category
python3 $S find-tools --request '<next JSON from a result>'    # follow a `next` link
python3 $S contract arxiv-org/papers/get_paper                 # inputs, response, price (free)
python3 $S run arxiv-org/papers/get_paper --options '{"arxiv_id":"2608.21829"}'   # billed
```

**Costs:**
- `tools`, `find-tools`, and `contract` are free.
- `run` is billed at the tool's listed `creditsCost`.
- `tools --web` also returns web results. These are billed as a normal search and are **not** covered by the run ceiling.

**Spend ceiling for `run`.** `run` looks up the contract first (free), then:
- **Ceiling:** `--max-credits N`, else env `FIRECRAWL_MAX_CREDITS`, else 25 credits. The default covers 1,773 of the 1,834 flat-priced tools in the 2026-10-18 catalog.
- **Flat-priced tools:** refused if the listed price exceeds the ceiling.
- **Per-record tools:** estimated as price × the numeric `limit` in `--options`. Refused when there is no `limit`, because the cost cannot be bounded, or when the estimate exceeds the ceiling.
- **Unlisted price:** tools with no listed price are refused.
- **Refusals:** a refused run exits 1 before any billed call. Raise the ceiling explicitly for expensive tools (e.g. Similarweb, up to 550 credits).

**Several paid calls (a sweep or batch): use a ledger.** One ledger file per task enforces a total budget across runs:

```bash
L=/tmp/sweep-ledger.json
python3 $S run substack-com/newsletters/post --options '{"url":"…"}' --ledger $L --budget 60   # first run creates it
python3 $S run stackexchange-com/questions/search --options '{…}' --ledger $L               # later runs reuse it
python3 $S ledger $L                                                                        # budget, spend, every call
```

- Each run's ceiling is the lower of the per-run ceiling and the ledger's remaining budget.
- Successful runs record the `creditsCost` the API reports. Failed runs record the listed price, since a failed call may still be billed.
- After a failed run, the next run is refused until the cause is fixed. Pass `--after-failure` only once it is understood.

**Before paying, check eligibility for free.** If results must satisfy a criterion such as a date window or language, confirm it from free sources (search snippets, `scrape`, archive pages) before a paid fetch. Test an unfamiliar input format with one call before a batch.

**Known quirks:** read `~/.claude/skills/firecrawl-api/references/alexandria-quirks.md` before using Stack Exchange or Substack tools, and add an entry whenever a contract's text disagrees with what the API accepts.

**Rules:**
- A tool match is not data. Run `contract` and send exactly the inputs it declares.
- Each call prints `Request ID (free): …` or `Request ID (billed): …` to stderr. A `run` prints both: the free contract lookup, then the billed execution. Keep stderr apart from stdout JSON (`2>/dev/null` or `2>log`).
- Never wrap `run` in a retry or an `||` fallback: every execution is billed. Loops over many inputs must use `--ledger`.
- Free calls (`find-tools`, `contract`, free tools) retry automatically after a 429 rate-limit response; billed calls never do. The limit was 12 requests/minute, and each `run` makes two requests.
- Per-item errors in `data.alexandria[]` exit non-zero.
- A `THIRD_PARTY_DATA_TERMS_REQUIRED` error prints the terms URL. An org admin must accept the terms there; a data request does not authorize accepting them.

## Local catalog

- `~/.claude/skills/firecrawl-api/references/alexandria-catalog.md` (about 66k words): category index, then one table per provider with each tool's listed price and use.
- `~/.claude/skills/firecrawl-api/references/alexandria-catalog.json`: the same data for `jq`.

Never read the Markdown file whole. Search it:

```bash
C=~/.claude/skills/firecrawl-api/references
grep -n -i "podcast" $C/alexandria-catalog.md | head -20                 # find providers/tools by topic
sed -n '/^## ai-models$/,/^## apps$/p' $C/alexandria-catalog.md | head -80  # read one category
jq -r '.tools[] | select(.provider=="arxiv-org") | "\(.capability)\t\(.creditsCost)"' $C/alexandria-catalog.json
jq -r '.tools[] | select(.perRecord) | "\(.provider)/\(.capability) \(.creditsCost)/record"' $C/alexandria-catalog.json
```

The catalog is a dated snapshot (see its first lines), and prices and coverage change: confirm with `contract` before `run`. To refresh it (free, about 6 minutes because of the 12 requests/minute limit), run:

```bash
python3 ~/.claude/skills/firecrawl-api/scripts/build_catalog.py
```
