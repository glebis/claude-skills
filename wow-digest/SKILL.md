---
name: wow-digest
description: Daily digest of 3-7 genuinely surprising items from newsletters and Telegram channels. Scores content for epistemic friction, not just relevance. Appends to daily note. Use when the user says "/wow-digest", "run the wow digest", "what's surprising today", "morning reading", or "digest my newsletters".
---

# wow-digest

## Purpose

Pull last 24h of newsletters (email) and Telegram channel posts, filter noise,
score survivors for genuine surprise against the user's focus and recent research,
and append 3-7 WOW items to today's daily note.

## Workflow

1. Run `scripts/ingest.py` to pull and normalize candidates from all sources
2. Run `scripts/enrich.py` to fetch full content for link-only newsletters (LinkedIn, beehiiv, Substack)
3. Run `scripts/salience_filter.py` to drop obvious noise (marketing, payments, greetings)
4. Run `scripts/wow_score.py` on filtered candidates to score and select WOW items
4. Append selected items to today's daily note under `## Reading`
5. Save raw candidates to `.wow-eval/candidates/YYYYMMDD.jsonl` for replay
6. Archive processed newsletter emails via GWS
7. During eval phase: run `scripts/feedback.py` to collect human verdicts

## Manual run

```bash
python3 scripts/ingest.py --days 1 --output /tmp/wow-candidates.jsonl
python3 scripts/enrich.py --input /tmp/wow-candidates.jsonl --output /tmp/wow-enriched.jsonl
python3 scripts/salience_filter.py --input /tmp/wow-enriched.jsonl --output /tmp/wow-filtered.jsonl
python3 scripts/wow_score.py --input /tmp/wow-filtered.jsonl --output /tmp/wow-selected.json
# Then the skill appends to daily note and archives emails
```

## Dry-Run Mode

When the user says `/wow-digest --dry-run` or "preview the digest", run the full pipeline but:
1. Do NOT append to daily note
2. Do NOT archive emails
3. Instead, print the selected items with scores and hooks directly in the conversation

This lets the user preview what would be appended without side effects.

## Context Sourcing

The scoring prompt uses three context signals from the vault (`~/Brains/brain/`):

- **`{focus}`** — From `My Focus.md`, sections `## Current`, `## Base`, `## Primary` (stops at `## Nice to have`). This tells the scorer what the user cares about right now.
- **`{research}`** — From `ai-research/*.md` files (last 30 days), parsed from filenames (`YYYYMMDD-topic.md`) and `research_topic:` frontmatter. Shows what the user has already investigated.
- **`{recent_topics}`** — From `Daily/YYYYMMDD.md` headings (last 7 days), excluding `## do` and `## log`. Shows recent daily note themes.

If these files don't exist, scoring still works but with degraded personalization.

## Dedup

Ingestion deduplicates against the last 7 days of `.wow-eval/candidates/*.jsonl` using SHA-256 hashes of `title|source_name` (case-insensitive). Same article shared to multiple channels or re-sent in a newsletter won't appear twice. Pass `--no-dedup` to `ingest.py` to skip.

## Config

Edit `config/sources.yaml` to add/remove email patterns or Telegram channels.
Edit `config/wow_prompt.txt` to tune the scoring prompt.

## Output Format

After scoring, append to today's daily note (`Daily/YYYYMMDD.md`) ABOVE the `- - -` separator, below any existing content:

```markdown
## Reading

- **[Title]** (Source) — hook explaining WHY it's surprising
- **[Title]** (Source) — hook
...

_WOW digest · N candidates → M selected · YYYY-MM-DD_
```

CRITICAL: Always run `date +"%Y%m%d"` to get today's date. Never assume.

If `## Reading` already exists in the daily note, append items to it rather than creating a duplicate section.

## Archive

After appending to daily note, archive processed newsletter emails:
1. Collect all `message_id` values from email candidates
2. Run GWS batchModify to remove INBOX label

```bash
gws gmail users messages batchModify \
  --params '{"userId":"me"}' \
  --json '{"ids":["ID1","ID2",...],"removeLabelIds":["INBOX"]}'
```

## Eval Mode (first 2 weeks)

During eval phase, do NOT auto-archive. Instead:

1. Run ingest + scoring as normal
2. Present the selected items to the user with FULL CONTENT, not just titles. For each item show:
   - Title + source
   - The snippet (first 300-500 chars of actual content)
   - The LLM's hook and challenged_assumption
   - WOW score breakdown (relevance, surprise, bridge_value, predictability)
3. Show all items in a single text block first so the user can read the content
4. Then ask via AskUserQuestion: "Was this actually WOW?" with options: wow / meh / noise / already_knew
5. Record feedback via `scripts/feedback.py`
6. Show current feedback stats
7. Only archive after user confirms

CRITICAL: The user CANNOT judge WOW from titles alone. Always show the snippet content.
If the snippet is empty or too short, fetch the full email body via GWS before presenting.

To check if eval mode is active:
- If `.wow-eval/feedback.jsonl` has fewer than 50 entries → eval mode
- If 50+ entries → auto mode (archive without asking)
