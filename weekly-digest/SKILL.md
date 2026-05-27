---
name: weekly-digest
description: Research, score, and publish a weekly industry digest on any topic. Casts a wide net via web search (20+ candidates), verifies sources for AI-generated slop, scores each item on five parameters (Novelty, Relevance, Slopiness, Technical depth, Feasibility), selects the top items, and generates both markdown files and a Tufte-style HTML report. Use this skill whenever the user says "/weekly-digest", "run the weekly digest", "industry digest", "what's new in [topic]", "weekly roundup", "news digest on [topic]", "research what happened this week in [topic]", or any request to create a curated, scored summary of recent developments in a field. Also use when the user wants to monitor a topic area with quality filtering — the slopiness scoring is the key differentiator from a simple news search.
---

# Weekly Digest

A research-to-publication pipeline that produces a scored, source-verified industry digest. The workflow has seven phases: init, scoping, research, verification, scoring, output, and presentation.

## Phase 0: Init

Read `~/.claude/skills/weekly-digest/settings.json`. Two possible states:

**State A — file missing, or `subjects` is empty and file has no `version` field (fresh install):** Run onboarding:

1. Ask: "What topic do you want to track?" — get a specific topic. If the user declines or says "just run it" without specifying, respond: "A topic is required — there's no default. What field do you want to monitor?" Do not invent a topic.
2. Ask: "Any geographic focus? (e.g., European, Asian — not American)" — optional, default null
3. Generate a slug from the topic for `output_prefix` (lowercase, hyphenated, no spaces — e.g., "agent orchestration" → "agent-orch")
4. Write the full settings file with all defaults + the new subject:
   ```json
   { "version": 1, "top_n": 5, "target_candidates": 20, "lookback_days": 7,
     "output_dir": "output", "language": "en",
     "weights": { "novelty": 1, "relevance": 1, "slopiness": 1, "technical": 1, "feasibility": 1 },
     "obsidian_vault": null, "subjects": [{ ... }] }
   ```
5. Validate `output_dir` exists (create if needed) before proceeding.
6. Confirm: "Saved. Run `/weekly-digest add [topic]` to add more subjects."
7. Proceed to Phase 1 with the newly configured subject.

**State B — subjects exist, user ran `/weekly-digest` (no args):** Run all subjects sequentially.

**When subjects list is empty but `version` field exists (user cleared subjects intentionally):** Don't auto-onboard. Respond: "No subjects configured. Add one with `/weekly-digest add [topic]`."

For the full settings schema, see `settings.example.json` in the skill directory.

## Configuration

Settings live at `~/.claude/skills/weekly-digest/settings.json`.

### Settings schema

```json
{
  "version": 1,
  "top_n": 5,
  "target_candidates": 20,
  "lookback_days": 7,
  "output_dir": "output",
  "language": "en",
  "weights": {
    "novelty": 1,
    "relevance": 1,
    "slopiness": 1,
    "technical": 1,
    "feasibility": 1
  },
  "obsidian_vault": null,
  "subjects": [
    {
      "topic": "agent orchestration",
      "geo_focus": "European, UK, Asian — not American",
      "output_prefix": "agent-orch"
    }
  ]
}
```

All fields except `subjects` are optional — missing keys use defaults shown above. The `output_prefix` must be a lowercase hyphenated slug (no spaces).

### Managing subjects

- `/weekly-digest config` — show current settings
- `/weekly-digest add [topic]` — interactively add a new default subject (ask for geo focus and output prefix)
- `/weekly-digest remove [topic]` — remove a subject from defaults
- `/weekly-digest` (no args) — run all default subjects sequentially, producing separate file sets for each
- `/weekly-digest [topic]` — run a single topic as a one-off (ignores defaults)

### Settings reference

| Key | Default | What it does |
|-----|---------|-------------|
| `top_n` | 5 | How many items appear in the digest |
| `target_candidates` | 20 | How many candidates to aim for in research |
| `lookback_days` | 7 | How far back to search (appended to queries as date range) |
| `output_dir` | `"output"` | Directory for generated files (relative to cwd) |
| `language` | `"en"` | Preferred source language; non-matching sources deprioritized |
| `weights` | all 1.0 | Per-parameter multipliers for the overall score formula |
| `obsidian_vault` | null | Path to Obsidian vault; when set, digest is copied to `{vault}/Digests/YYYYMMDD-{prefix}.md` |

## Phase 1: Scope

Parse the user's request for:

- **Topic** (required, or from settings): e.g., "agent orchestration", "quantum computing", "climate tech"
- **Geographic focus** (optional, or from settings): e.g., "European, UK, Asian — not American". Default: no filter

Auto-detect today's date for file naming (YYYYMMDD format).

If the user gives a vague topic like "AI", push back and ask them to narrow it — broad topics produce generic results.

## Phase 2: Research

Run **4-6 parallel WebSearch queries** designed to cover different angles of the topic. The goal is `target_candidates` unique items (default 20). Use `lookback_days` to scope recency — include month/year in queries for the configured window. Structure searches like this:

| Query pattern | What it catches |
|---------------|-----------------|
| `[topic] breakthrough announcements [month] [year]` | Major launches, product releases |
| `[topic] startup funding [year] [geo]` | Funding rounds, new entrants |
| `[topic] open source release [year]` | OSS frameworks, tools |
| `[topic] research paper arxiv [year]` | Academic contributions |
| `[topic] enterprise production [year] [geo]` | Real deployments, case studies |
| `[topic] regulation governance [year] [geo]` | Policy, compliance, standards |

If a geographic focus is specified, add geographic terms to queries and add a dedicated regional search. When `language` is set, prefer sources in that language.

Deduplicate across search results. Aim for diversity — reject a candidate pool that's all from the same source type (e.g., all market forecasts or all press releases). Check that at least 3 of these 6 categories are represented.

**If fewer than 15 candidates are found:** widen one query by removing the year/month filter and run it again. If still below 15, proceed with what exists and note the shortfall in the raw file header.

## Phase 3: Source Verification

Select the **top 8-10 candidates for verification** using this pre-screening signal: pick items whose search snippets contain at least one of: a specific named person/organization, a specific date, a version number, or a dollar amount. Deprioritize items with exclusively superlative or vague language.

Use WebFetch on primary sources to check for slop indicators:

**Red flags** (high slopiness score):
- No direct quotes from named people
- No specific dates, deal terms, or technical details
- Narrative-essay structure with no attribution
- "Cherry-picked metrics" with no links to verification
- Future dates presented as fact (speculative content)
- Phrases like "poised to", "set to revolutionize", "game-changing"

**Green flags** (low slopiness score):
- Named executives with direct quotes
- Specific dates, dollar amounts, version numbers
- Official press releases, government sources, arXiv
- Conference announcements with venues and dates
- Case studies with named customers and metrics

When a secondary source has slop indicators but the underlying story might be real, check the primary source (company blog, official press release, arXiv abstract). Score the best available source, not the worst.

**If WebFetch fails** (paywall, 403, timeout, empty content): note the failure in scoring notes, score slopiness conservatively at 5 (unknown quality), and move on. Record the failed URL in the failure log.

## Phase 4: Scoring

Rate each candidate 0-10 on five parameters:

| Parameter | What it measures | 0 means | 10 means |
|-----------|-----------------|---------|----------|
| **Novelty** | How new or unprecedented | Old news, incremental | World's first, paradigm shift |
| **Relevance** | How relevant to the user | Unrelated vertical | Directly useful for their work |
| **Slopiness** | How likely the source is slop | Solid primary source | Pure AI slop or SEO filler |
| **Technical** | Technical depth | Zero technical content | Deep architecture, reference impl |
| **Feasibility** | Real vs. speculative | Sci-fi, vaporware | Shipping in production |

**Slopiness convention:** 0 = verified, trustworthy source. 10 = pure slop. The formula inverts it so that low-slop items score higher.

### Overall score formula

```
Overall = (w₁·Novelty + w₂·Relevance + w₃·(10 - Slopiness) + w₄·Technical + w₅·Feasibility) / (w₁ + w₂ + w₃ + w₄ + w₅)
```

Weight mapping from `settings.json` keys to formula symbols:
- `w₁` = `weights.novelty`
- `w₂` = `weights.relevance`
- `w₃` = `weights.slopiness`
- `w₄` = `weights.technical`
- `w₅` = `weights.feasibility`

Default: all 1.0, making this a simple average.

### Relevance scoring anchors

Relevance depends on who the user is. Check memory/profile for context. When no profile is available, use these anchors for a technical-practitioner audience:

- **10** — has working code, API, or reference implementation you can use today
- **7** — describes a technique or tool you could adopt within a week
- **5** — informative trend with some actionable takeaway
- **3** — interesting but tangential to most practitioners
- **0** — market analysis or forecast with no actionable component

## Phase 5: Output Files

Generate files in the configured `output_dir` (default: `output/`, relative to cwd). Create the directory if needed — if creation fails (permissions, invalid path), abort with a clear error before writing.

**Slug rule for all runs:** every run has a `{prefix}` slug. For settings-based subjects, use `output_prefix` from the subject config. For single-topic one-off runs, derive a slug from the topic using the same rule as Phase 0 step 3 (lowercase, hyphenated, no spaces — e.g., "quantum computing" → "quantum-computing").

**File naming** (always uses prefix):
- `YYYYMMDD-{prefix}-raw.md`
- `YYYYMMDD-{prefix}-digest.md`
- `YYYYMMDD-{prefix}-failures.md` (only if failures exist)
- `YYYYMMDD-{prefix}-report.html` (from Phase 6)

### Raw file (`*-raw.md`)

All candidates (target: 20+) with:
- Title and 1-2 sentence description
- Scoring table (all 5 parameters + overall, including weights if non-default)
- Notes explaining the scores
- Source link
- Ranked by overall score at the bottom

### Digest file (`*-digest.md`)

Top `top_n` items (default: 5) selected by overall score, each with:
- Title
- 2-sentence summary (informative, not hype — must contain specific facts)
- All 5 parameter scores displayed inline
- Source link

Include a brief note at the top explaining the selection method and pointing to the raw file.

### Failure log (`*-failures.md`)

Record in a separate file:
- URLs where WebFetch failed (with error type)
- Queries that returned fewer than 5 results
- Items dropped for slopiness > 8
- Any shortfall notes (< target candidates found)

Only create this file if there are failures to log.

### Diff mode

If a previous digest exists for the same subject, compare. To find the previous digest: list all files matching `*-{prefix}-digest.md` in `output_dir`, parse the `YYYYMMDD` date prefix. If a file from today already exists (same-day rerun), treat it as the previous version and rename it to `YYYYMMDD-{prefix}-digest.prev.md` before writing the new one. Otherwise select the most recent file older than today. Compare:
- Items in both runs → mark as **persistent** in the new digest
- Items only in the new run → mark as **new**
- Items that dropped off → note in the raw file footer as "previously ranked, no longer appearing"

### Obsidian export

If `obsidian_vault` is set in settings.json, copy the digest file to `{obsidian_vault}/Digests/YYYYMMDD-{prefix}.md` after generation (using the same `{prefix}` slug as the output files). Create the `Digests/` directory if needed.

## Phase 6: Presentation

Invoke the `/tufte-report` skill to generate a Tufte-style HTML report. The tufte-report skill must be installed at `~/.claude/skills/tufte-report/` — if it is not available, skip this phase and tell the user: "Install the tufte-report skill from github.com/glebis/claude-skills for HTML report generation."

The report should include:

1. **Summary cards** — Top `top_n` items as ranked cards with overall scores
2. **Detail section** — Each item with 2-sentence summary and horizontal score bars for all 5 parameters
3. **Full candidate table** — All candidates ranked by overall score with all parameter values
4. **Methodology section** — How sources were verified, what slopiness means, weights used

Save the report as `{output_dir}/YYYYMMDD-{prefix}-report.html` and open it in the browser.

## Example invocations

```
/weekly-digest agent orchestration
/weekly-digest climate tech, focus on European and Asian news
/weekly-digest config
/weekly-digest add quantum computing
/weekly-digest remove design innovation
/weekly-digest                          # runs all saved subjects
```

## Output quality checklist

Before presenting results, verify:
- [ ] At least `target_candidates` items in the raw file (or shortfall noted)
- [ ] At least 3 different source types (news, academic, official, funding)
- [ ] Top candidates have been source-verified via WebFetch
- [ ] No item in top `top_n` has slopiness > 6 — if one does, drop it and promote the next-ranked item. (Items at slopiness 5 from WebFetch failures are allowed through; only clearly sloppy sources at 7+ are blocked.)
- [ ] Every item has a working source link
- [ ] 2-sentence summaries contain specific facts, not vague claims
- [ ] Failure log created if any failures occurred
- [ ] Diff annotations added if previous digest exists
- [ ] Obsidian export completed if vault path is configured
