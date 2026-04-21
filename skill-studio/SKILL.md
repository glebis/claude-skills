---
name: skill-studio
description: Interview-driven automation design tool. This skill should be used when the user wants to design a new skill, agent, automation, shortcut, or any other automatable workflow. Runs a coverage-driven JTBD interview (text or voice), then exports a one-page markdown spec plus an SVG design map.
---

# Skill Studio

## Purpose

Conduct a structured JTBD interview that captures what to build, for whom, and why — then emit a one-page `design.md` + `design.svg` spec. Sits between "should I automate this?" (automation-advisor) and "how do I package this as a skill?" (skill-creator).

## Architecture

This skill wraps an external CLI tool (`skill-studio`) installed via pip. The CLI handles session state, coverage tracking, and export. The skill orchestrates the CLI — it does not bundle scripts directly.

## When to use

Trigger on any of: "help me design...", "build a skill for...", "design an automation for...", "I want a bot/agent/workflow that...", "scope a new shortcut". Also trigger when the user describes a recurring pain and asks how to automate it.

## Prerequisites

- `skill-studio` CLI on PATH (`pip install -e .` inside the skill directory, or `skill-studio init` for guided setup)
- Python 3.11+
- Text mode needs no API key — the interview runs natively inside Claude Code
- Voice mode (`--voice`) needs `DAILY_API_KEY`, `GROQ_API_KEY`, `DEEPGRAM_API_KEY`, and an LLM provider key (`OPENROUTER_API_KEY` by default). If any key is missing, suggest text mode instead.

To verify the CLI is available, run `skill-studio --help`. If the command is not found, install it from the skill's base directory: `pip install -e <skill-studio-base-dir>`.

## Interview protocol (text mode)

Follow these steps in order.

### Step 0 — (Optional) Seed from a prior session

If the user provides a prior session (Claude Code transcript, another skill-studio session, or arbitrary transcript path), seed the interview instead of starting blank:

```bash
skill-studio propose-from-session <session_id>
# or: skill-studio propose-from-session --path <file>
# add --bundle-only to skip the LLM call and inspect the raw extract
```

This runs in two stages:
1. **Deterministic ingest** (no LLM) — regex-extracts models tried, cost events, prompt changes, pain snippets, and hashes. A 50k-token transcript compresses to ~30 lines of JSON.
2. **Single LLM call** — over that compact bundle only, proposes a partial DesignJSON patch with a `rationale` map citing which signals justified each field.

**The proposal is NOT applied automatically.** Present it to the user (with the rationale) and ask for approval. Offer: `approve as-is`, `edit inline`, `discard and start fresh`, `approve partial` (keep some fields, re-interview others).

`propose-from-session` does not create a session. After approval, run `new-session` (Step 1) to create one, then pipe the approved patch to `apply-patch`, and continue the interview loop from the next uncovered target.

### Step 1 — Start the session

Presets: `ai-agent` (default), `life-automation`, `knowledge-work`, `custom`.
Depth: `sprint` (0.60, ~5–7 questions), `standard` (0.80, ~15–20 questions, default), `deep` (0.92, ~25–35 questions).

Styles (shape how questions are phrased):
- `scenario-first` (default) — "Walk me through a specific time when..."
- `socratic` — "Why does that matter? What would happen if...?"
- `metaphor-first` — "If this automation were a [thing], what would it be?"
- `form` — One direct question per field, no preamble.

Run:

```bash
skill-studio new-session --preset <preset> --depth <depth> --style <style>
```

Output:

```
session_id: <uuid>
opening: <question text>
```

Store the `session_id`. Present the opening question to the user as a direct text message.

### Step 2 — Interview loop

For every user answer:

**a. Extract a JSON patch.** Emit a JSON object containing only the DesignJSON fields the answer addresses. Use only fields from the schema below — never hallucinate fields or values. If nothing schema-relevant was said, emit `{}`.

Example patch:

```json
{"jtbd.situation": "When I finish a coaching call and need to write up notes", "problem.what_hurts": "Manual note-taking takes 20 minutes and I lose details"}
```

Example with list fields:

```json
{"needs.functional": ["transcribe audio", "extract action items"], "guardrails": ["never send notes without review"]}
```

Example with object-list field (`scenarios`):

```json
{"scenarios": [{"title": "Post-coaching rush", "vignette": "Call ends at 14:00, next meeting at 14:15 — I scribble three bullet points and lose the rest by evening."}]}
```

**DesignJSON fields:**

| Field | Type | Notes |
|-------|------|-------|
| `hook` | str | One-sentence pitch of the automation |
| `problem.what_hurts` | str | Specific pain |
| `problem.cost_today` | str | What the pain costs right now |
| `needs.functional` | list[str] | What it must do |
| `needs.emotional` | list[str] | How the user wants to feel |
| `needs.social` | list[str] | Relational / status needs |
| `jtbd.situation` | str | When this happens |
| `jtbd.motivation` | str | What the user wants |
| `jtbd.outcome` | str | So they can... |
| `before_after.before_external` | str | Visible state before |
| `before_after.before_internal` | str | Felt state before |
| `before_after.after_external` | str | Visible state after |
| `before_after.after_internal` | str | Felt state after |
| `scenarios` | list[{title, vignette}] | Concrete day-in-the-life stories |
| `trigger.type` | `manual` / `scheduled` / `event` | |
| `trigger.detail` | str | e.g. "7:45am weekdays" |
| `inputs` | list[str] | Data / services consumed |
| `capabilities` | list[str] | What it does |
| `outputs` | list[str] | What it produces |
| `guardrails` | list[str] | Safety rails; negative-space rules |
| `cta` | str | Next action at end of design |
| `concept_imagery.metaphor` | str | Visual / verbal handle |

**b. Apply the patch.**

```bash
echo '<patch_json>' | skill-studio apply-patch <session_id>
```

Output:

```
coverage: 0.42
next_target: jtbd.situation
```

**c. Check stop conditions.** End the loop if either:
- `coverage >= threshold` (sprint=0.60, standard=0.80, deep=0.92)
- User says "done", "wrap up", or "stop"

**d. Ask the next question.** Target the `next_target` field, in the active style. Never re-ask a field already past 0.5 coverage. Present the question as direct text to the user.

### Step 3 — Export

```bash
skill-studio done <session_id>
```

Prints the paths to `design.md` and `design.svg`. Present both paths to the user.

## Voice mode

For voice interviews, skip the manual loop and delegate to the built-in pipeline:

```bash
skill-studio new --voice --preset <preset> --depth <depth>
```

This spins up a Daily room (auto-opens in the browser), runs Groq Whisper STT -> interview loop -> Deepgram TTS, and auto-exports on session end.

If voice mode fails due to missing API keys, fall back to text mode and inform the user. To configure keys, run `skill-studio init`.

## Other commands

- `skill-studio list` — list all sessions
- `skill-studio export <id> md-svg` — regenerate `design.md` + `design.svg`
- `skill-studio coverage <id>` — per-field confidence JSON
- `skill-studio next-target <id>` — ask-this-next hint
- `skill-studio init` — full first-run wizard (prereq checks + keys + paths)
- `skill-studio setup` — narrower key-rotation flow (sops-only)

## Sessions

Each interview writes to `$SKILL_STUDIO_HOME/sessions/<uuid>/` (default: `~/.skill-studio/sessions/<uuid>/`):

- `design.json` — canonical schema (single source of truth)
- `transcript.md` — full Q&A log
- `design.md`, `design.svg` — exported artifacts

## Troubleshooting

- **`skill-studio: command not found`** — Run `pip install -e <skill-studio-base-dir>` and retry.
- **`apply-patch` returns an error** — Verify the JSON patch is valid (keys must match schema fields above). Run `skill-studio coverage <session_id>` to inspect current state.
- **Session not found** — Always run `new-session` before the first `apply-patch`. There is no implicit session creation. Run `skill-studio list` to check existing sessions.
- **Voice mode key errors** — Run `skill-studio init` to configure missing keys, or fall back to text mode.

## Notes

- The interview loop runs entirely inside Claude Code for text mode. No Anthropic API key is required.
- Voice mode LLM provider is swappable via `LLM_PROVIDER=anthropic` (default is `openrouter`).
