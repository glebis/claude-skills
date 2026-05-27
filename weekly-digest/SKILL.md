---
name: weekly-digest
description: Research, score, and publish a weekly industry digest on any topic. Casts a wide net via web search (20+ candidates), verifies sources for AI-generated slop, scores each item on five parameters (Novelty, Relevance, Slopiness, Technical depth, Feasibility), selects the top 5, and generates both markdown files and a Tufte-style HTML report. Use this skill whenever the user says "/weekly-digest", "run the weekly digest", "industry digest", "what's new in [topic]", "weekly roundup", "news digest on [topic]", "research what happened this week in [topic]", or any request to create a curated, scored summary of recent developments in a field. Also use when the user wants to monitor a topic area with quality filtering — the slopiness scoring is the key differentiator from a simple news search.
---

# Weekly Digest

A research-to-publication pipeline that produces a scored, source-verified industry digest. The workflow has six phases: scoping, research, verification, scoring, output, and presentation.

## Why this skill exists

Most AI-generated news roundups are themselves slop — they regurgitate press releases and market forecasts without checking whether the underlying claims are real. This skill treats source quality as a first-class scoring dimension. The slopiness parameter penalizes content with no named sources, no direct quotes, vague metrics, and SEO keyword density. The result is a digest where every item has been checked against primary sources.

## Configuration: Default Subjects

The skill supports a settings file at `~/.claude/skills/weekly-digest/settings.json` that stores default subjects to monitor. When the user runs `/weekly-digest` without a topic, use the defaults from this file instead of asking.

```json
{
  "subjects": [
    {
      "topic": "agent orchestration",
      "geo_focus": "European, UK, Asian — not American",
      "output_prefix": "agent-orch"
    },
    {
      "topic": "design innovation",
      "geo_focus": null,
      "output_prefix": "design"
    }
  ]
}
```

**Managing settings:**
- `/weekly-digest config` — show current settings
- `/weekly-digest add [topic]` — interactively add a new default subject (ask for geo focus and output prefix)
- `/weekly-digest remove [topic]` — remove a subject from defaults
- `/weekly-digest` (no args) — run all default subjects sequentially, producing separate file sets for each
- `/weekly-digest [topic]` — run a single topic (ignores defaults, uses the provided topic)

When running multiple subjects, name output files with the prefix: `output/YYYYMMDD-{prefix}-raw.md`, `output/YYYYMMDD-{prefix}-digest.md`, `output/YYYYMMDD-{prefix}-report.html`.

If `settings.json` doesn't exist and the user runs without a topic, create it interactively by asking what subjects they want to monitor.

## Phase 1: Scope

Parse the user's request for two inputs:

- **Topic** (required, or from settings): e.g., "agent orchestration", "quantum computing", "climate tech"
- **Geographic focus** (optional, or from settings): e.g., "European, UK, Asian — not American". Default: no filter

Auto-detect today's date for file naming (YYYYMMDD format).

If the user doesn't specify a topic and no defaults exist in settings, ask. If they give a vague topic like "AI", push back and ask them to narrow it — broad topics produce generic results.

## Phase 2: Research

Run **4-6 parallel WebSearch queries** designed to cover different angles of the topic. The goal is 20+ unique candidate items. Structure searches like this:

| Query pattern | What it catches |
|---------------|-----------------|
| `[topic] breakthrough announcements [month] [year]` | Major launches, product releases |
| `[topic] startup funding [year] [geo]` | Funding rounds, new entrants |
| `[topic] open source release [year]` | OSS frameworks, tools |
| `[topic] research paper arxiv [year]` | Academic contributions |
| `[topic] enterprise production [year] [geo]` | Real deployments, case studies |
| `[topic] regulation governance [year] [geo]` | Policy, compliance, standards |

If a geographic focus is specified, add geographic terms to queries and add a dedicated regional search.

Deduplicate across search results. Aim for diversity — reject a candidate pool that's all from the same source type (e.g., all market forecasts or all press releases).

## Phase 3: Source Verification

For the **top 8-10 candidates** (those that look most promising), use WebFetch on primary sources to check for slop indicators:

**Red flags** (increase slopiness score):
- No direct quotes from named people
- No specific dates, deal terms, or technical details
- Narrative-essay structure with no attribution
- "Cherry-picked metrics" with no links to verification
- Future dates presented as fact (speculative content)
- Phrases like "poised to", "set to revolutionize", "game-changing"

**Green flags** (decrease slopiness score):
- Named executives with direct quotes
- Specific dates, dollar amounts, version numbers
- Official press releases, government sources, arXiv
- Conference announcements with venues and dates
- Case studies with named customers and metrics

When a secondary source (like a tech news site) has slop indicators but the underlying story might be real, check the primary source (company blog, official press release, arXiv abstract). Score the best available source, not the worst.

## Phase 4: Scoring

Rate each candidate 0-10 on five parameters:

| Parameter | What it measures | 0 means | 10 means |
|-----------|-----------------|---------|----------|
| **Novelty** | How new or unprecedented | Old news, incremental | World's first, paradigm shift |
| **Relevance** | How relevant to the user | Unrelated vertical | Directly useful for their work |
| **Slopiness** | Source quality (inverted in overall) | Solid primary source | Pure AI slop or SEO filler |
| **Technical** | Technical depth | Zero technical content | Deep architecture, reference impl |
| **Feasibility** | Real vs. speculative | Sci-fi, vaporware | Shipping in production |

**Overall score** = (Novelty + Relevance + (10 - Slopiness) + Technical + Feasibility) / 5

Slopiness is inverted so that lower slop = higher overall score.

**Relevance scoring** depends on who the user is. Check memory/profile for context — a Berlin-based AI instructor scores differently than a healthcare CTO. If no profile context is available, score relevance based on how actionable the item is for a technical audience.

## Phase 5: Output Files

Generate two markdown files in the project's `output/` directory (create if needed):

### `output/YYYYMMDD-raw.md`

All 20+ candidates with:
- Title and 1-2 sentence description
- Scoring table (all 5 parameters + overall)
- Notes explaining the scores
- Source link
- Ranked by overall score at the bottom

### `output/YYYYMMDD-digest.md`

Top 5 items selected by overall score, each with:
- Title
- 2-sentence summary (informative, not hype)
- All 5 parameter scores displayed inline
- Source link

Include a brief note at the top explaining the selection method and pointing to the raw file.

## Phase 6: Presentation

Invoke the `/tufte-report` skill to generate a Tufte-style HTML report. The report should include:

1. **Summary cards** — Top 5 items as ranked cards with overall scores
2. **Detail section** — Each item with 2-sentence summary and horizontal score bars for all 5 parameters
3. **Full candidate table** — All 22+ items ranked by overall score with all parameter values
4. **Methodology section** — How sources were verified, what slopiness means

Save the report as `output/YYYYMMDD-report.html` and open it in the browser.

## Example invocations

**Simple:**
```
/weekly-digest agent orchestration
```

**With geographic focus:**
```
/weekly-digest climate tech, focus on European and Asian news
```

**Conversational:**
```
What's new in multi-agent systems this week? Focus on non-US news.
```

## Output quality checklist

Before presenting results, verify:
- [ ] At least 20 candidates in the raw file
- [ ] At least 3 different source types (news, academic, official, funding)
- [ ] Top candidates have been source-verified via WebFetch
- [ ] No item in top 5 has slopiness > 4
- [ ] Every item has a working source link
- [ ] 2-sentence summaries contain specific facts, not vague claims
- [ ] Tufte report opens in browser
