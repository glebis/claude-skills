# Alexandria provider quirks

Observed behaviour that differs from a contract's text, or that costs credits in non-obvious ways. Each entry is dated. Recheck an entry before relying on it, and add new ones as they are found.

## Contract text vs validation

| Tool | Observed | Fix | Seen |
|---|---|---|---|
| `stackexchange-com/questions/search` | The contract says `fromdate` takes "Unix seconds, `YYYY-MM-DD` or an RFC 3339 date", but the API rejects a string: `invalid_option: fromdate must be number`. | Send Unix seconds, e.g. `python3 -c 'import datetime,zoneinfo;print(int(datetime.datetime(2026,7,18,tzinfo=zoneinfo.ZoneInfo("Europe/Berlin")).timestamp()))'`. Assume `todate` is the same. | 2026-10-18 |

General rule: when a contract offers several formats for one field, try one call with the most primitive form (a number, not a string) before running a batch.

## Cost traps

| Tool | Trap | Avoid it | Seen |
|---|---|---|---|
| `substack-com/newsletters/post` | Publication date is only known after paying 5 credits to fetch the post. Web search snippets often omit dates. In one sweep, 4 of 6 paid fetches were outside the research window. | Check the date for free first (search snippet, the post URL in a browser or `firecrawl scrape`, or the publication's archive page), then fetch. | 2026-10-18 |
| `stackexchange-com/questions/search` | A search with no matches is still a billed call (5 credits) that returns `total: 0`. | Treat zero results as a coverage gap. Don't retry with near-identical queries. | 2026-10-18 |
| Any `run` that fails | A failed call may still be billed. Whether failed validation calls were charged could not be confirmed from `credit-usage`. | Use `--ledger` so the listed price is recorded on failure and later runs stop until the cause is fixed. | 2026-10-18 |

## Rate limits

- The team limit was 12 requests/minute (2026-10-18). Each `run` makes two requests: the free contract lookup, then the execution.
- Free calls (find-tools, contract, Research Index) retry automatically after a 429. Billed calls never retry.

## Free tools worth knowing

- `firecrawl-research-index/search`, `inspect`, `read`, `related` cost 0 credits (2026-10-18). `read` returns targeted full-text passages; empty passages do not mean a section is absent.
