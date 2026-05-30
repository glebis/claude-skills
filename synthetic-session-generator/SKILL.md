---
name: synthetic-session-generator
description: This skill should be used to generate realistic, persona-consistent synthetic coaching and therapy session transcripts for evals, demos, and training data. It produces fictional but believable coach/client (or therapist/client) dialogue grounded in a chosen modality (ICF/GROW coaching, CBT, IFS parts work, ACT/motivational interviewing) and exports to Fathom/Granola transcript style, plain dialogue, structured JSON, or Obsidian markdown. Triggers on requests like "generate a synthetic coaching session", "make fake therapy transcripts for evals", "create demo session transcripts", "synthetic CBT dialogue", "persona-consistent coaching transcript", "test data for my session summarizer", or "mock coaching call".
---

# Synthetic Session Generator

## Purpose

Generate fictional but believable coaching/therapy session transcripts that read like real recorded
sessions, while remaining clearly synthetic. Outputs feed three jobs: **eval datasets** (with
ground-truth labels to benchmark summarizers and analyzers), **product demos** (realistic sessions
without exposing real client data), and **training/prompt examples** (few-shot material for a
coaching or therapy assistant).

Realism comes from two disciplines: **persona consistency** (a client speaks the same way, carries
the same history and presenting issues across a session arc) and **modality fidelity** (the
practitioner uses the techniques, question forms, and pacing of the chosen framework). Every output
is watermarked as synthetic so it can never be mistaken for a real clinical record.

## When to Use

Use when a user asks for fake/synthetic/mock/demo coaching or therapy transcripts, eval or test data
for session-analysis tools (e.g. the `coaching-session-summarizer`), few-shot dialogue examples, or
persona-consistent session series. Do **not** use to analyze or summarize a *real* transcript — that
is the job of `coaching-session-summarizer` or `transcript-analyzer`.

## Workflow

### Step 0 — Setup mode (configure defaults)

When the user wants to configure the skill ("setup", "set my defaults", "always use Russian / IFS /
50-minute sessions"), run setup mode. Offer the three choices via AskUserQuestion, then persist them:

- **Language** — output language for the transcript (`en`, `ru`, `de`, `es`, `fr`, `pt`, `it`, `nl`).
- **Modality** — default framework (`icf-grow`, `cbt`, `ifs`, `act-mi`).
- **Session duration** — minutes (e.g. 25 / 50 / 80); mapped to a turn budget (~0.6 turns/min).

```bash
python3 scripts/setup_config.py --language ru --modality cbt --duration 50 --show
python3 scripts/setup_config.py --show     # view current defaults
```

This writes `config.json` in the skill directory. Later `scaffold_session.py` runs inherit these
defaults, so the user only specifies what differs (e.g. persona and session position). Per-run flags
always override the saved config.

### Step 1 — Gather the generation spec

Honour the setup-mode defaults (Step 0); only ask for parameters the user hasn't already fixed.

Collect (or infer sensible defaults for) these parameters. Ask only for what materially changes the
output; default the rest.

- **Use case**: eval / demo / training (drives whether ground-truth labels are emitted).
- **Modality**: `icf-grow`, `cbt`, `ifs`, or `act-mi`. See `references/modalities.md` for the
  technique cheat-sheet, signature moves, and vocabulary of each.
- **Persona**: pick an existing persona from `references/personas.md`, or generate a new one and
  **persist it** back into that file so a session series stays consistent. A persona = name,
  demographics, presenting issue, history, speech register, defenses/resistances, goals.
- **Session position**: intake / early / mid-arc / breakthrough / rupture-and-repair / closing.
  This sets emotional tone and what prior material is referenced.
- **Format**: `fathom`, `plain`, `json`, or `markdown` (see Step 3). Markdown is always produced.
- **Language**: defaults from setup config; pass `--language`. Author **all** dialogue, persona
  voice, and the watermark-adjacent text in that language; keep eval tag *keys* in English.
- **Duration / length**: `--duration <minutes>` (preferred — maps to a turn budget) or the coarse
  `--length` (short ~15 / standard ~30 / long ~50+).

### Step 2 — Build the session skeleton, then write the dialogue

Run the scaffolding script to turn the spec into a structured skeleton (phases, beat list, turn
budget, JSON shell, and the synthetic watermark):

```bash
python3 scripts/scaffold_session.py --modality cbt --persona maya --position mid-arc \
    --length standard --format json --out /tmp/session_skeleton.json
```

Then **write the actual dialogue by hand** (model-authored), filling each beat. The script provides
structure and guardrails; Claude provides the natural, non-templated language. Key realism rules
(full list in `references/realism_guide.md`):

- Open with logistics/check-in small talk; never jump straight to deep work.
- Give the client disfluencies, hedges, self-interruption, and at least one moment of resistance or
  avoidance. Real clients don't deliver clean insights on cue.
- Keep the practitioner in-modality: CBT uses thought records and Socratic questioning; IFS uses
  parts language and "How do you feel toward that part?"; GROW moves Goal→Reality→Options→Will;
  ACT/MI uses values, defusion, and change talk. Avoid mixing modalities unless depicting eclectic
  practice deliberately.
- Maintain persona voice: vocabulary, sentence length, and recurring metaphors stay stable.
- End with a summary, a between-session task/experiment, and scheduling.

### Step 3 — Render formats (always include markdown)

Author once in the JSON turn structure, then convert. **Always render the markdown format** (it is
the canonical, human-readable artifact); add any other formats the user asked for.

```bash
# markdown is always produced:
python3 scripts/convert_format.py --in /tmp/session.json --to markdown --auto-timestamps --out session.md
# plus any requested extras:
python3 scripts/convert_format.py --in /tmp/session.json --to fathom --auto-timestamps --out session.txt
```

- **markdown** *(always)* — Obsidian note with YAML frontmatter (persona id, modality, session
  position, synthetic flag) above the transcript.
- **fathom** — speaker-labeled, timestamped lines matching the Fathom/Granola export style, so the
  transcript flows through existing skills (`coaching-session-summarizer`, `transcript-analyzer`).
- **plain** — simple `Coach:` / `Client:` turn-taking markdown.
- **json** — the source itself: turns with `speaker`, `timestamp`, `text`, and eval tags
  (`technique`, `emotion`, `phase`); for evals, also the `ground_truth` block.

**Timestamps.** Do not hand-invent timestamps. Pass `--auto-timestamps` so the converter emulates
them from each turn's word count (~150 wpm + a short inter-turn gap), keeping timing internally
consistent. Tune pace with `--wpm`. See `assets/templates/` for a reference example of each format.

### Step 4 — (Optional) Case-conceptualization card with portrait

When the user wants a **card** summarizing the case (for demos, persona bibles, or eval context),
build it from the same session JSON and pair it with a generated portrait:

```bash
python3 scripts/make_card.py --in /tmp/session.json --out /tmp/card.md            # scaffold
python3 scripts/make_card.py --in /tmp/session.json --print-prompt                # portrait prompt
```

1. Run `make_card.py` to emit the card scaffold (modality-aware formulation skeleton + themes/goals
   pulled from `ground_truth` + a watermark + a ready portrait prompt).
2. Fill the `<!-- FILL: ... -->` blocks with the clinical formulation (model-authored).
3. Generate the portrait with the **`gpt-image-2` skill** using the prompt from `--print-prompt`.
   Keep it **illustrative, not photoreal** — a stylized image cannot be mistaken for a photo of a
   real person. Then re-run with `--image <path>` (or edit the card) to embed it.

### Step 4b — (Optional) Render the card as an HTML page via `tufte-report`

When the user wants a shareable **HTML page** of the case card (portrait + conceptualization), hand
the filled card to the **`tufte-report` skill**, which produces a standalone Tufte-style HTML file.

1. Build and fill the card (Step 4), including the embedded portrait.
2. Invoke the `tufte-report` skill with the card's conceptualization as the narrative content and the
   portrait as a figure. Map card sections to the report: **Snapshot/Presenting issue** → intro
   narrative; **Formulation** → the main 2-column narrative+data section; **Working themes** and
   **Goals & experiments** → a status/dashboard panel; **Emotional arc** → a sparkline or labelled
   sequence. Pass the portrait path so it renders as the hero figure.
3. **Keep the synthetic watermark visible** in the HTML (header or footer), and confirm the output
   path (default: current working directory) before writing the `.html`.

The portrait must remain the illustrative, non-photoreal image from Step 4 — the HTML page is for
demos and persona bibles, never presented as a real client record.

### Step 5 — Watermark and save

**Always** apply the synthetic watermark — this is non-negotiable. The scaffold script injects it;
verify it survived format conversion. Each output must carry, in a location appropriate to its
format (frontmatter, JSON metadata, or a header/footer comment):

```
⚠️ SYNTHETIC — AI-generated fictional session. Not a real person, not clinical advice.
```

**Confirm the save location before writing.** Ask the user where to save and state the default —
the **current working directory** (`.`). Only fall back to `/tmp/` for throwaway intermediate
scaffolds the user will not keep. Use clear filenames (e.g. `<persona>_<modality>_<position>.md`).
For eval batches, write one file per session into the chosen directory plus a manifest listing
personas, modalities, and label coverage.

## Limitations and Constraints

- **Synthetic only.** Never present output as a real session, real person, or clinical record. The
  watermark is mandatory and must never be stripped, even for demos (use the optional clean-body
  variant only when the user explicitly confirms, and keep provenance in metadata).
- **Not clinical guidance.** Generated dialogue is illustrative fiction; it must not be used as a
  source of therapeutic technique, diagnosis, or advice for real care. Do not reproduce real
  protocols verbatim or imply clinical validity.
- **No real PII.** Do not base personas on identifiable real individuals or copy details from real
  transcripts. If given a real transcript as a style reference, abstract patterns only — never names,
  specifics, or verbatim content (route true anonymization to `session-anonymizer`).
- **Portraits stay illustrative.** Generate card portraits as stylized illustrations, never
  photorealistic faces — a synthetic illustration cannot be mistaken for a photo of a real person.
  The card carries its own synthetic watermark; keep it.
- **Safety-sensitive content.** Crisis, self-harm, abuse, or risk scenarios may be depicted only when
  the use case clearly warrants it (e.g. red-team evals), must stay clearly fictional and watermarked,
  and must depict responsible practitioner handling — never operational harmful detail.
- **Stay in scope.** This skill generates; it does not analyze real sessions. Hand real-transcript
  summarization to `coaching-session-summarizer` and anonymization to `session-anonymizer`.
