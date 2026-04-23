---
name: jtbd
description: Terminal-first JTBD engine for founders and product people. Interview fast, kill jargon, capture real switching forces (Push/Pull/Habit/Anxiety), score opportunities, and export structured artifacts (JSON + one-pager + messaging angles + GTM brief). Use when the user says "help me figure out what to build", "analyze these customer reviews", "what are people actually hiring this for", "I need messaging for my product", "turn this interview into insights", "what should I prioritize", or any variation of articulating what a project does, why it matters, who it's for, or converting interview/review/transcript signal into a decision-grade brief. Also triggers on "describe my project", "JTBD", "jobs to be done", "switching forces", or "mine these reviews".
---

# JTBD Project Describer

## Purpose

Conduct a focused Jobs-to-Be-Done interview for one project and emit a decision-grade artifact bundle. The bundle contains a machine-readable `jtbd.json`, a shareable `one-pager.md`, and a `messaging-angles.md` derived from Switch forces. Ingest voice transcripts or review exports when available.

## When to invoke

- "Describe my project in JTBD."
- "Turn this interview transcript into a JTBD brief."
- "Mine these reviews for jobs."
- "I need messaging from this product idea."
- "Help me articulate what I'm actually building."
- "Update my JTBD brief with new data."
- "Decompose this job into outcomes."
- "Generate a GTM brief from this JTBD."

If the user wants a full design spec (what to build, scope, components), prefer `skill-studio` — it's the heavier tool. `jtbd` is the quick, rigorous record.

## Mode selection

Pick one at the start. Ask the user only if ambiguous.

| Mode | Input | Output |
|---|---|---|
| **Interview** (default) | live conversation | full artifact bundle |
| **Transcript ingest** | path to a voice interview transcript | full artifact bundle + confidence flags |
| **Review mining** | path to reviews (CSV/JSON) | `review-brief.md` pre-seed → then Interview |
| **Update** | path to existing `~/jtbd/<slug>/jtbd.json` | updated artifact bundle |

## Scope discipline

One project per session. If the user starts describing a second project, stop them: "That sounds like a separate project — let's finish this one first, then run `/jtbd` again for the next."

If the user drifts into implementation details, features, or tech stack: "Interesting, but let's stay at the job level — what is the person trying to accomplish?"

---

## Interview flow

### Pass 1 — Core (3–5 adaptive questions, one at a time)

1. **What is this?** — One-sentence description. Push for clarity if vague.
2. **Who struggles and when?** — The triggering situation. "Walk me through the last time this happened."
3. **What's painful today?** — Current workaround and why it's not working.
4. **What does success look like?** — The outcome, not the feature list.
5. **How should it feel?** — Emotional payoff (optional, ask if natural).

Stop when the core schema is confidently fillable.

### Pass 2 — Switch forces (required, one short burst)

The four forces are the single highest-leverage JTBD artifact. Do not skip this pass. See `references/switch_forces.md` for the question bank.

Before diving into individual forces, reconstruct the Switch Timeline (see `references/switch_forces.md`): "Walk me through the decision — when did it start?" Map the 6 moments (first thought → passive looking → active looking → deciding → consuming → ongoing use).

Probe briefly for each:
- **Push** — frustration with current situation.
- **Pull** — attraction to the new solution.
- **Habit** — inertia keeping them with the old.
- **Anxiety** — fear of switching / trying the new.

Do not fabricate. If the user genuinely doesn't know a force, mark it `"unknown"` and note the follow-up question in `open_questions[]`.

### Pass 3 — Job Map decomposition (optional)

Trigger when the user asks "what should I build?" or when ODI scoring is active and you need candidate outcomes.

1. Walk through the 8 universal job steps (see `references/job_map.md`).
2. For each step, ask: "Where does the pain live here?"
3. Focus on the 3-5 steps with highest pain.
4. Generate 3-5 ODI outcome statements per step using the strict format from `references/odi.md`.
5. Feed outcomes into ODI Scoring Mode if active.

Skip this pass for quick interviews. Use it when the user needs prioritization or roadmap input.

---

## Granularity Gate (pre-save validator)

Before drafting the JSON, score the interview output 0–2 on five dimensions. Any score <1 blocks save. Use `references/granularity_fixes.md` for rewrite prompts.

| Dimension | 0 (fail) | 1 (ok) | 2 (strong) |
|---|---|---|---|
| **Actor specificity** | "users" / "people" | a role | a named actor with context |
| **Context / trigger** | "always" / none | a situation | a specific moment |
| **Current workaround** | "nothing" / "various" | named alternative | described attempt + why it fails |
| **Measurable outcome** | "better" / "improved" | directional metric | quantified target |
| **Evidence quote** | none | paraphrase | verbatim quote |

If any dimension scores 0, ask one targeted follow-up question and re-score. Don't interrogate — one rewrite pass, then accept what you have and flag the weak dimensions in `evidence.weaknesses[]`.

For deterministic scoring on ingest paths, call `scripts/validate_granularity.py` with the draft JSON.

---

## Jargon Kill Switch

Every major claim must tie to one of:
- A verbatim or paraphrased quote.
- An observable behavior.
- A specific current workaround.

See `references/jargon_blacklist.md` for banned phrases and replacements. When the user or transcript says a banned phrase, reply with an evidence-demand: "What does that look like in practice?" / "Show me the last time that happened."

Do not put banned phrases in the output. If one slips through, replace with the concrete substitute from the blacklist.

---

## Output schema

### Core (always filled)

```json
{
  "name": "project-slug",
  "hook": "One sentence: what this is for whom, concretely.",
  "jtbd": {
    "situation": "When [specific context/trigger]...",
    "motivation": "I want to [action/goal]...",
    "outcome": "So I can [measurable result]..."
  },
  "problem": {
    "what_hurts": "Specific pain point with evidence."
  },
  "needs": {
    "functional": ["what it must do"],
    "emotional": ["how user wants to feel"]
  },
  "switch_forces": {
    "push": "What's frustrating about today.",
    "pull": "What's attractive about the new.",
    "habit": "What keeps them stuck.",
    "anxiety": "What they fear about switching."
  },
  "outputs": ["what the project produces/delivers"],
  "evidence": {
    "source": "interview | voice_transcript | reviews",
    "quotes": ["verbatim quotes if available"],
    "weaknesses": ["dimensions that scored 0 or 1 in granularity gate"]
  }
}
```

### Extended (include only when naturally surfaced)

```json
{
  "problem": { "cost_today": "What the pain costs (time, money, stress)." },
  "needs": { "social": ["relational/status needs"] },
  "before_after": {
    "before": "Visible + felt state before.",
    "after": "Visible + felt state after."
  },
  "scenarios": [{ "title": "Short label", "vignette": "1-2 sentence day-in-the-life story" }],
  "trigger": { "type": "manual | scheduled | event", "detail": "e.g. after every client call" },
  "version": 1,
  "guardrails": ["what it must NOT do"],
  "odi": {
    "outcomes": [
      { "statement": "Minimize the time it takes to...", "importance": 8.5, "satisfaction": 3.2, "opportunity_score": 13.8 }
    ]
  },
  "open_questions": ["follow-ups the interviewer didn't resolve"]
}
```

See `references/odi.md` for the importance/satisfaction/opportunity formula and when ODI is worth adding.

---

## Transcript Ingest Mode

When the user provides a transcript path:

1. Read the transcript.
2. Run `scripts/ingest_transcript.py <path>` — it proposes schema field mappings with confidence flags.
3. Review the proposal with the user. Fill gaps by asking targeted follow-ups (not the full interview).
4. Run Switch forces pass on the transcript content.
5. Apply Granularity Gate + Jargon Kill Switch as normal.
6. Set `evidence.source = "voice_transcript"` and preserve verbatim quotes in `evidence.quotes`.

---

## Review-Mining Intake

When the user provides a reviews export:

1. Run `scripts/mine_reviews.py <path>` — clusters reviews by pain, outcome, and workaround.
2. The script emits `review-brief.md` in the output folder using `templates/review-brief.md` as a pre-seed.
3. Present the brief to the user. Ask: "Does this match your sense? Any missing patterns?"
4. Use the brief as Pass 0 before the regular interview — skip Pass 1 questions that the reviews already answered.
5. Set `evidence.source = "reviews"`.

See `references/review_taxonomy.md` for the clustering taxonomy.

---

## Update Mode

When the user provides a path to an existing `jtbd.json`:

1. Read the existing JSON.
2. Show the user the current state: hook, job statement, switch forces.
3. Ask: "What changed? New interview data? Pivot? New insight?"
4. Run only the passes that need updating — don't re-interview from scratch.
5. Apply Granularity Gate + Jargon Kill Switch as normal.
6. Save updated JSON (increment a `version` field if present).
7. Regenerate one-pager.md, messaging-angles.md, and gtm-brief.md from the updated JSON.

---

## ODI Scoring Mode (optional)

Trigger when the user asks for prioritization, "what to build next," or roadmap input. Add the `odi` extended block.

1. Derive candidate outcome statements from the interview.
2. Ask the user to rate each outcome on importance (1–10) and current-solution satisfaction (1–10).
3. Run `scripts/odi_score.py` to compute opportunity scores.
4. Sort descending. Top 3 go into `odi.outcomes[]`.

Only add ODI when the user has 3+ candidate outcomes — below that, skip it.

---

## After the interview — Output Bundle

1. Apply Granularity Gate + Jargon Kill Switch.
2. Draft `jtbd.json` and show it to the user for review.
3. Ask: "Anything to adjust? Want to add extended fields (before/after, scenarios, guardrails, ODI)?"
4. Apply edits.
5. Create output folder: `~/jtbd/<project-slug>/`. If it exists, ask overwrite or rename.
6. Write three files using templates:
   - `jtbd.json` — source of truth.
   - `one-pager.md` — stakeholder-shareable summary (from `templates/one-pager.md`).
   - `messaging-angles.md` — copy angles derived from Switch forces (from `templates/messaging-angles.md`).
   - `gtm-brief.md` — positioning, channels, experiments (from `templates/gtm-brief.md`). Only generated when switch forces are fully captured (no `"unknown"` values).
7. Report all paths.

## Downstream pipeline (superpowers integration)

The `jtbd.json` is a contract between `/jtbd` and downstream agents. See `references/superpowers_handoff.md` for the full field mapping.

**Short version:** when brainstorming starts and a `jtbd.json` exists, it should skip the questions the JSON already answers (who, what, why, constraints) and focus on the questions it doesn't (how, architecture, scope, technical choices). Switch forces inform approach selection. Open questions become brainstorming priorities.

**Chain:** `/jtbd` → `jtbd.json` → brainstorm → writing-plans → implementation

After the interview, suggest: "Want to brainstorm approaches? I can feed this into superpowers with your job, forces, and needs as context."

## Naming convention

`project-slug` = lowercase, hyphens, no spaces. Derive from the project name. Max 40 chars.

## Tone

Direct, curious, slightly challenging. You are a product thinker helping someone sharpen their thinking — not a form to fill out. Push back on fuzzy language: "What do you mean by 'better'?" / "Better for whom?" / "Show me the last time this happened."

Never let jargon ("seamless," "delightful," "drive engagement," "empower users") into the output. Every claim must have an evidence hook.
