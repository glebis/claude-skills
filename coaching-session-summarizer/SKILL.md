---
name: coaching-session-summarizer
description: This skill should be used to summarize coaching or therapy session transcripts after a Fathom/Granola sync. The agent analyzes the transcript itself (no API key, runs on the subscription) and appends key insights, decisions, action items, and trail connections. Supports quick extraction or deep analysis with cross-session pattern detection.
---

# Coaching Session Summarizer

## Overview

Analyzes a coaching/therapy session transcript and appends a structured summary
(key insights, decisions, action items, deep analysis, connected trails) to the
note.

**The agent (Claude Code) performs the analysis directly** — reading the
transcript and writing the summary in this session. There is **no Anthropic API
call and no billing**; it runs entirely on the active subscription. A legacy
API-based script is kept only as a headless fallback (see bottom).

## When to Use This Skill

- A new Fathom/Granola transcript was synced to the vault (coaching or therapy)
- User asks to summarize/analyze a session (`/summarize-session [file]` or similar)
- After `calendar-sync` or a Granola export, when a new `*-coaching.md`,
  `*-therapy.md`, or `*-session.md` file appears — offer to summarize it

## Workflow (agent-driven — default)

Do this in-session with native tools. No API key required.

### Step 1 — Gather context

Run the deterministic helper to get the transcript text, previous sessions, and
the trail list in one shot:

```bash
python3 ~/.claude/skills/coaching-session-summarizer/scripts/gather_context.py \
  <transcript-file> --vault ~/Brains/brain
```

It prints:
- **Previous sessions** with the same participant (paths) — `Read` these only in
  deep mode, for cross-session pattern detection
- **Available trails** — pick 2–4 most relevant to link
- **Session content** — the summary + transcript to analyze (any prior
  AI-Generated Summary is stripped so re-runs stay clean)

Pass `--participant <name-slug>` if the filename doesn't encode the person
(e.g. Granola exports titled by topic): `--participant gleb-kalinin`.

### Step 2 — Analyze

Read the session content and extract, in the analytical voice of a session
analyst (objective, using the speaker's authentic language where it matters):

- **Key Insights** — 3–5 main realizations / breakthroughs / observations
- **Decisions Made** — concrete choices or commitments
- **Action Items** — specific next steps; prefix time-sensitive ones with
  `[URGENT]` and scheduling items with `[SCHEDULING]`
- **Session Themes** — 2–3 recurring topics or patterns

**Deep mode** (default for therapy and milestone sessions) — also `Read` the
previous sessions and add:

- **Pattern Detection** — themes recurring across sessions
- **Progress Assessment** — movement on earlier commitments
- **Energy/Motivation Markers** — shifts in energy, resistance, affect
- **Potential Obstacles** — what might block progress

### Step 3 — Append with Edit

Append the summary to the **end** of the transcript file using `Edit` (never
overwrite existing content). Match this exact structure:

```markdown
## AI-Generated Summary

*Generated: YYYY-MM-DD*

### Key Insights
- ...

### Decisions Made
- ...

### Action Items
- [URGENT] ...
- ...

### Session Themes
- ...

## Deep Analysis

- **Pattern Detection**: ...
- **Progress Assessment**: ...
- **Energy/Motivation Markers**: ...
- **Potential Obstacles**: ...

## Connected Trails

- [[Trails/Trail - <Name>|<Name>]]
- [[Trails/Trail - <Name>|<Name>]]
```

Use the current date (`date +%Y-%m-%d`) in the Generated line. Omit the Deep
Analysis section in quick mode. Verify trail link names against the printed
trail list — case and exact wording matter for Obsidian links.

## Modes

- **quick** — Key Insights, Decisions, Action Items, Themes. Skip Deep Analysis
  and previous-session reads.
- **deep** (recommended for therapy / milestones) — everything, including
  reading previous sessions for pattern detection.

## Integration with Sync

After `calendar-sync` or a Granola/Fathom export, check for new session files
(`*-coaching.md`, `*-therapy.md`, `*-session.md`). If one appears, offer:
"New session detected — summarize now?" Default to deep mode for therapy.

## Notes

- Preserves the original transcript intact; the summary is always appended.
- Trail linking requires the `Trails/` directory in the vault root.
- Cross-session comparison works best with consistent naming:
  `YYYYMMDD-name-coaching.md` / `YYYYMMDD-name-therapy.md`.
- Re-running is safe: `gather_context.py` strips any prior AI-Generated Summary
  before printing, so the agent analyzes only the raw session. (Delete the old
  `## AI-Generated Summary` block from the file before re-appending if you want
  to replace rather than stack summaries.)

## Resources

### scripts/

- **gather_context.py** — *(default path)* deterministic context gatherer, no
  API. Prints transcript text + previous sessions + trail list for the agent to
  analyze in-session.
- **summarize_session.py** — *legacy / headless fallback.* Calls the Anthropic
  API directly (model via `SUMMARIZER_MODEL`, default `claude-sonnet-4-6`) and
  bills a funded `ANTHROPIC_API_KEY`. Use only when no interactive agent is
  available (e.g. cron). Exits with a clear message if the key has no credit.
