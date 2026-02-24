# Thinking Patterns — Implementation Instructions

You are running the Thinking Patterns skill. Follow these steps precisely.

## Constants

```
VAULT_ROOT = /Users/glebkalinin/Brains/brain
CONFIG_FILE = .claude/skills/thinking-patterns/config.json
EXTRACTION_PROMPT = .claude/skills/thinking-patterns/extraction-prompt.md
SYNTHESIS_PROMPT = .claude/skills/thinking-patterns/synthesis-prompt.md
BLINDSPOT_PROMPT = .claude/skills/thinking-patterns/blindspot-prompt.md
OUTPUT_FOLDER = ai-research
DAILY_DIR = Daily
EXTRACTION_BATCH_SIZE = 4
MAX_PARALLEL_AGENTS = 13
SYNTHESIS_AGENTS = 5
MIN_SESSIONS_FOR_FINDING = 2
```

---

## Step 0: Parse Arguments & Load Config

### 0a. Get today's date
```bash
date +"%Y%m%d"
```
Store as `TODAY` (e.g., `20260223`).

### 0b. Parse arguments
Check for flags in the skill invocation:
- `--dry-run`: only run Stage 0, output corpus stats and batch plan, then stop
- `--period START END`: override date range (format: YYYY-MM or YYYY-MM-DD)

### 0c. Load config
Read `.claude/skills/thinking-patterns/config.json`. Extract:
- `period_start`, `period_end` (override with --period if given)
- `weights` (session type weights)
- `reference_docs` (Profile Brief, My Focus, etc.)
- `speaker_identifiers` (names to match Gleb's speech)
- `session_type_keywords` (for classifying transcripts)

### 0d. Load reference documents
Read these files (parallel Read calls):
- `20260130-profile-brief.md`
- `My Focus.md`
- `My Focus - Strategic Decisions Framework.md`

Store their content — it will be passed to synthesis agents for execution gap analysis.

---

## Stage 0: Corpus Discovery

### 0e. Find all transcripts in date range
Use Bash to find Fathom transcripts:

```bash
find /Users/glebkalinin/Brains/brain -maxdepth 1 -name "2025*.md" -o -name "2026*.md" | sort
```

Then filter by date range (period_start to period_end). Only include files that:
1. Have a filename starting with YYYYMMDD where the date falls within the range
2. Contain Fathom transcript content (check for `source: fathom` in frontmatter, OR presence of transcript-like content with speaker names)

Exclude files that are clearly NOT transcripts:
- Files ending in `-analysis.md`
- Files in subdirectories (non-root files unless they match transcript patterns)
- Files shorter than 50 lines (likely summaries, not transcripts)

### 0f. Classify each transcript

For each transcript file, determine `session_type` using these keywords in the filename:

| session_type | Filename keywords | Weight |
|---|---|---|
| coaching | coaching, coach, anastasia, grebenshekova | 1.0 |
| client_meeting | meeting, call, between | 0.9 |
| podcast | podcast, agency-community | 0.8 |
| impromptu | impromptu | 0.7 |
| workshop | workshop, skills-subagents | 0.6 |
| lab | lab, claude-code-lab | 0.4 |

If no keyword matches, default to `client_meeting` (0.9).

Also read the YAML frontmatter `type` field — if it says `coaching`, `transcript`, etc., use that as additional signal.

### 0g. Extract Gleb's speech lines from each transcript

Read each transcript file. Two transcript formats exist in the vault:

**Format A** (older Fathom, timestamped):
```
  00:00:42 - Gleb Kalinin (glebis@gmail.com)
      Speech text here across one or more lines.
  00:01:09 - Other Speaker
      Their text.
```
Extract: collect all text lines that follow a `Gleb Kalinin` header, until the next speaker header.

**Format B** (newer Fathom, bold markdown):
```
**Gleb Kalinin**: Speech text here.
```
Extract: collect all lines starting with `**Gleb Kalinin**:`.

Speaker identifiers to match (case-insensitive):
- "Gleb Kalinin"
- "Gleb"
- "Калинин Глеб"
- "Глеб Калинин"
- "Глеб"

**Format C** (newer Fathom, unidentified speakers):
```
**Unknown**: Speech text here.
```
Some Fathom transcripts label all speakers as `**Unknown**` (diarization failure).

Recovery strategy for `**Unknown**` transcripts:
1. Read the YAML frontmatter `participants` field
2. If participants list has 1-2 people AND Gleb is one of them:
   - In a **1-person** meeting (Gleb only): treat ALL `**Unknown**` speech as Gleb's
   - In a **2-person** meeting: treat `**Unknown**` speech as mixed — include ALL lines but add a `"speaker_uncertain": true` flag to the extraction metadata. The extraction agent should still analyze the full conversation but note lower confidence since some lines may be the other speaker's.
3. If participants list has 3+ people: skip the transcript (too ambiguous to attribute speech)
4. If no participants field exists: skip the transcript

**Important**: Only extract Gleb's speech (or likely-Gleb speech in Format C recovery). Discard other identified speakers.

Strip frontmatter, summary sections, action items, linked topics — only keep raw transcript speech.

**Exclude non-transcript files**: Some files in the date range have Fathom markers but are actually summaries (no `## Transcript` section, bold headers are section titles not speaker names). If a file has `**Unknown**` speakers but the bold-formatted lines read like section headers ("**Status Update:**", "**Key Insight:**"), skip it — it's a summary, not a transcript.

Read transcripts in parallel batches of 10 (use 10 Read tool calls in a single message).

### 0h. Build corpus manifest

For each transcript, store:
```json
{
  "filename": "20260210-impromptu-zoom-meeting.md",
  "session_date": "2026-02-10",
  "session_type": "impromptu",
  "weight": 0.7,
  "line_count": 120,
  "word_count": 3500,
  "gleb_lines": "extracted speech text..."
}
```

Sort by date ascending.

### 0i. Dry-run output (if --dry-run)

If `--dry-run` flag was set, output:

```
Thinking Patterns — Corpus Discovery

Period: {period_start} to {period_end}
Transcripts found: {total_count}
Total lines (Gleb's speech): {total_lines}
Total words (Gleb's speech): {total_words}

By type:
  coaching:        {count} sessions ({total_words} words, weight: 1.0)
  client_meeting:  {count} sessions ({total_words} words, weight: 0.9)
  podcast:         {count} sessions ({total_words} words, weight: 0.8)
  impromptu:       {count} sessions ({total_words} words, weight: 0.7)
  workshop:        {count} sessions ({total_words} words, weight: 0.6)
  lab:             {count} sessions ({total_words} words, weight: 0.4)

Batch plan:
  Stage 1: {num_batches} extraction agents, {batch_size} transcripts each
  Stage 3: 5 synthesis agents

Estimated cost: ~${cost}
Estimated time: ~{minutes} minutes
```

Then STOP. Do not proceed to Stage 1.

### 0j. Plan batches for Stage 1

Group transcripts into batches of up to 4 (EXTRACTION_BATCH_SIZE), trying to keep each batch's total word count roughly even. Prioritize putting shorter transcripts together. Target 10-13 batches.

---

## Stage 1: Per-Transcript Cognitive Extraction

### 1a. Read the extraction prompt
Read `.claude/skills/thinking-patterns/extraction-prompt.md` to get the full prompt template.

### 1b. Launch extraction agents in parallel

For each batch, launch a Task agent:

```
Task(
  subagent_type: "general-purpose",
  model: "sonnet",
  description: "Extract cognitive patterns batch N",
  prompt: "[FULL EXTRACTION PROMPT from extraction-prompt.md]

Here are the transcripts to analyze:

TRANSCRIPT 1:
filename: {filename}
session_type: {session_type}
weight: {weight}

--- GLEB'S SPEECH ---
{gleb_lines}
--- END ---

TRANSCRIPT 2:
...

Return ONLY a valid JSON array with one object per transcript. No markdown fences."
)
```

**Launch up to 13 Task agents in a SINGLE message** (all in parallel). Each processes 1-4 transcripts.

### 1c. Collect results

Parse the JSON arrays returned by each Task agent. Combine into one flat array of extraction results.

If a Task agent returns malformed JSON:
1. Try to salvage by finding the JSON array within the text (strip markdown fences if present)
2. If still unparseable, skip that batch and note the error
3. Do not retry

Store all results as `extraction_results` — an array of objects, one per transcript.

---

## Stage 2: Aggregation

### 2a. Parse and aggregate all extraction results

For each of the 12 dimensions, aggregate across all transcripts:

1. **Collect**: Gather all findings from all transcripts for each dimension
2. **De-duplicate**: Remove near-identical quotes/findings (same quote appearing in overlapping transcripts)
3. **Frequency count**: Count how many sessions each pattern appears in
4. **Cluster**: Group similar findings (e.g., all "should statements" together, all "journey metaphors" together)
5. **Sort by frequency**: Most common patterns first

### 2b. Package into 5 synthesis bundles

Create 5 data packages for the synthesis agents:

**Bundle 1** (Agent 1: Narratives + Metaphors + Language):
- agency_language data (all sessions)
- emotional_indicators data (all sessions)
- energy_signals data (all sessions)
- conceptual_metaphors data (all sessions)
- code_switching data (all sessions)
- hedging_and_certainty data (all sessions)

**Bundle 2** (Agent 2: Decisions + Problem Framing + Biases):
- problem_framing data (all sessions)
- decision_moments data (all sessions)
- hedging_and_certainty data (all sessions)
- cognitive_distortions data (all sessions)

**Bundle 3** (Agent 3: Avoidance + Energy + Execution Gap):
- avoidance_and_deflection data (all sessions)
- energy_signals data (all sessions)
- code_switching data (all sessions)
- emotional_indicators data (all sessions)
- competing_commitments data (all sessions)
- problem_framing data (all sessions)
- Reference docs content (Profile Brief, My Focus, Strategic Decisions Framework)

**Bundle 4** (Agent 4: Role Shifts + Developmental Markers):
- role_register_markers data (all sessions)
- hedging_and_certainty data (all sessions)
- agency_language data (all sessions)

**Bundle 5** (Agent 5: Blind Spot Detection):
- ALL 12 dimensions aggregated data
- Reference docs content
- (Will also receive synthesis findings from Agents 1-4 — see Stage 3b)

### 2c. Truncation strategy

Each synthesis agent receives a LOT of data. To keep within context limits:
- For each dimension, include at most the 30 highest-frequency findings
- For each finding, include the quote (max 200 characters), date, session_type, and context
- Include frequency counts so agents know what's most common
- Include the session count (how many sessions this pattern appeared in)

If a bundle would exceed ~50,000 characters, truncate the least-weighted findings first (using session type weights).

---

## Stage 3: Cross-Session Synthesis

### 3a. Read the synthesis prompt
Read `.claude/skills/thinking-patterns/synthesis-prompt.md` to get the full prompt template.

### 3b. Launch synthesis agents 1-4 in parallel

For Agents 1-4, launch Task agents:

```
Task(
  subagent_type: "general-purpose",
  model: "sonnet",
  description: "Synthesize thinking patterns - Agent N",
  prompt: "[SYNTHESIS PROMPT — Agent N section only]

You are Agent {N}. Your assigned sections:
{list of sections from synthesis-prompt.md for this agent}

Here is the aggregated extraction data for your dimensions:

{BUNDLE N — JSON formatted}

Session metadata:
{list of all sessions with dates and types}

Reference documents (for execution gap analysis):
{reference doc contents — only for Agent 3}

Return ONLY a valid JSON object. No markdown fences."
)
```

**Launch Agents 1-4 in a SINGLE message** (all in parallel).

### 3c. Collect synthesis results from Agents 1-4

Parse JSON results. Combine all section findings.

### 3d. Launch Agent 5 (Blind Spot Detection)

Agent 5 runs AFTER Agents 1-4 because it needs their findings.

Read `.claude/skills/thinking-patterns/blindspot-prompt.md`.

```
Task(
  subagent_type: "general-purpose",
  model: "sonnet",
  description: "Detect blind spots and contradictions",
  prompt: "[BLINDSPOT PROMPT]

Here is the aggregated extraction data (all 12 dimensions):
{BUNDLE 5 — all data}

Here are the synthesis findings from Agents 1-4:
{combined synthesis results}

Reference documents:
{Profile Brief, My Focus, Strategic Decisions Framework}

Return ONLY a valid JSON object. No markdown fences."
)
```

### 3e. Collect blind spot results

Parse JSON. Extract the `top_5_blind_spots` for the summary section.

---

## Stage 4: Output

### 4a. Compile the analysis document

Create the file content using this template:

```markdown
---
created_date: '[[{TODAY}]]'
type: thinking-patterns-analysis
period: {period_start} to {period_end}
corpus:
  total_sessions: {count}
  total_words: {word_count}
  session_types:
    coaching: {count}
    client_meeting: {count}
    podcast: {count}
    impromptu: {count}
    workshop: {count}
    lab: {count}
methodology:
  tier_1: "Burns cognitive distortions, LIWC dimensions, epistemic markers, Russell's Circumplex"
  tier_2: "Lakoff conceptual metaphors, McAdams narrative identity, Kegan immunity to change, ACT flexibility"
  tier_3: "Kegan developmental stages, Schon reflective practice, agency language ratio"
related:
  - "[[20260130-profile-brief]]"
  - "[[My Focus]]"
  - "[[My Focus - Strategic Decisions Framework]]"
tags:
  - thinking-patterns
  - cognitive-analysis
  - longitudinal
---

# Thinking Patterns Analysis — {period_start} to {period_end}

> Longitudinal cognitive pattern analysis across {session_count} recorded conversations.
> Evidence-based frameworks: Burns' distortions, Lakoff metaphors, Kegan developmental stages, ACT flexibility markers, McAdams narrative identity.

## 1. Recurring Narratives

{Agent 1 findings for recurring_narratives section}

For each finding:
### {pattern_name}

{description}

**Evidence:**
{For each evidence item:}
- [{session_date}] ({session_type}): "{quote}" {translation if Russian}

**Trend**: {temporal_trend} | **Confidence**: {confidence} | **Sessions**: {sessions_count}

---

## 2. Problem Framing Patterns

{Agent 2 findings for problem_framing section — same format}

## 3. Metaphors & Unconscious Language

{Agent 1 findings for metaphors section}

## 4. Decision Heuristics

{Agent 2 findings for decision_heuristics section}

## 5. Topics Avoided

{Agent 3 findings for avoidance section}

## 6. Contradictions & Competing Commitments

{Agent 5 findings for contradictions section}

For each Immunity to Change map:
### Immunity Map: {goal}

| Column | Content |
|--------|---------|
| **I want to...** | {goal} |
| **I do instead...** | {doing_instead} |
| **Hidden commitment** | {hidden_commitment} |
| **Big assumption** | {big_assumption} |

**Evidence spanning {sessions_spanning} sessions**

## 7. Energy Patterns

{Agent 3 findings for energy section}

## 8. Role Shifts

{Agent 4 findings for role_shifts section}

## 9. Execution Gap

{Agent 3 findings for execution_gap section}

## 10. Cognitive Distortions & Biases

{Agent 2 findings for distortions section}

---

## The 5 Things You Don't See

{Agent 5 top_5_blind_spots}

For each:
### {rank}. {title}

{description}

**Key evidence**: {evidence_summary}

**Question to sit with**: _{actionable_question}_

**Confidence**: {confidence}

---

## Appendix

### Evidence Index

| Session | Date | Type | Weight | Words |
|---------|------|------|--------|-------|
{For each session in corpus:}
| [[{filename without .md}]] | {date} | {type} | {weight} | {words} |

### Methodology

**Tier 1 (Validated Frameworks)**:
- Burns' 10 cognitive distortion categories (F1 up to 0.82 for LLM detection)
- LIWC-22 dimensions: Analytical Thinking, Clout, Authenticity, Emotional Tone
- Epistemic markers: modal auxiliaries, plausibility shields
- Russell's Circumplex Model: valence x arousal tracking
- Code-switching: bilingual emotional arousal signals

**Tier 2 (Established Theory)**:
- Lakoff & Johnson conceptual metaphor theory (MIPVU extraction)
- McAdams Narrative Identity Theory: agency, communion, redemption, contamination
- Kegan & Lahey Immunity to Change: competing commitments
- ACT flexibility markers: should/must density, present-tense ratio
- Cognitive bias detection: System 1/2 markers

**Tier 3 (Applied Coaching)**:
- Kegan developmental stages: locus of evaluation, perspective complexity
- Schon reflective practice: reflection-in-action vs reflection-on-action
- Agency language ratio

### Framework References
- Burns, D. (1980). Feeling Good: The New Mood Therapy
- Lakoff, G., & Johnson, M. (1980). Metaphors We Live By
- McAdams, D. P. (2001). The Psychology of Life Stories
- Kegan, R., & Lahey, L. (2009). Immunity to Change
- Hayes, S. C. (2004). Acceptance and Commitment Therapy
- Russell, J. A. (1980). A Circumplex Model of Affect
- Tausczik, Y. R., & Pennebaker, J. W. (2010). LIWC analysis
```

### 4b. Save the analysis file

Write to: `ai-research/{TODAY}-thinking-patterns-analysis.md`

### 4c. Update daily note

Read `Daily/{TODAY}.md`. If it doesn't exist, create from template.

Check if a `## Research` section exists. If yes, append to it. If no, add it.

Append:
```markdown
## Research

- [[{TODAY}-thinking-patterns-analysis|Thinking Patterns Analysis ({period_start} — {period_end})]] — {session_count} sessions, {word_count} words analyzed. Top blind spots: {blind_spot_1_title}, {blind_spot_2_title}.
```

### 4d. Summary to user

Output a concise summary:

```
Thinking Patterns analysis complete — {TODAY}

Corpus: {session_count} sessions, {word_count} words ({period_start} — {period_end})

Top findings:
1. {most confident finding from each section — 1 line each}

The 5 Things You Don't See:
1. {blind_spot_1_title} ({confidence})
2. {blind_spot_2_title} ({confidence})
3. {blind_spot_3_title} ({confidence})
4. {blind_spot_4_title} ({confidence})
5. {blind_spot_5_title} ({confidence})

Full analysis: ai-research/{TODAY}-thinking-patterns-analysis.md
```

---

## Error Handling

- **No transcripts found**: Tell user "No Fathom transcripts found in {period_start} to {period_end}. Check date range."
- **Fewer than 5 transcripts**: Warn user, proceed but note limited corpus in output
- **No Gleb speech extracted**: Skip that transcript, warn in dry-run output
- **Task agent returns bad JSON**: Try to salvage (strip fences, find JSON array). If unparseable, skip batch, log error. Do NOT retry.
- **Synthesis agent returns bad JSON**: Same salvage strategy. Skip that section if unparseable.
- **Reference docs missing**: Warn user, proceed without execution gap analysis
- **Extremely long transcripts** (>5000 words of Gleb's speech): Truncate to first 5000 words for extraction, note truncation

## Performance Notes

- Reading transcripts: batch into groups of 10 parallel Read calls
- Stage 1: up to 13 extraction Task agents in ONE message (parallel)
- Stage 3: 4 synthesis Task agents in ONE message (parallel), then 1 blind spot agent
- Total: ~5-6 tool-call rounds for the heavy lifting
- Estimated runtime: ~6 minutes
- Estimated cost: ~$3.50
