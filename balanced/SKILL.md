---
name: balanced
description: Constructive, evidence-based dialogue mode that avoids sycophancy. This skill should be used when the user wants balanced multi-perspective analysis, critical feedback, or rigorous challenge of their ideas. Triggers on "/balanced" or requests for honest/critical/balanced feedback. Supports full, interactive, tldr, steelman, decision, and sketch modes.
---

# Balanced Dialog

Engage in constructive, evidence-based dialogue. Multiple output modes available.

## Onboard Mode

Trigger: `/balanced onboard` or `/balanced setup`. Walk the user through all available modes and let them pick a default.

### Flow

1. Print this overview as plain text:

```
Balanced Dialog — available modes:

FULL (default) — 4-move structured analysis
INTERACTIVE    — Socratic Q&A, one move at a time
TLDR           — 3-5 line insight box, action-oriented
STEELMAN       — strongest argument + strongest counter
DECISION       — tradeoff table + the call
SKETCH         — the analysis as a visual HTML diagram

Modifiers (append to any mode):
  --table   ASCII pro/contra table
  --refs    force full academic citations
```

2. Ask for the default mode with AskUserQuestion. The tool allows at most 4 options, so offer FULL (recommended), TLDR, STEELMAN, and DECISION; the user picks INTERACTIVE or SKETCH through the tool's free-text "Other" answer.

3. Ask for default modifiers with AskUserQuestion, `multiSelect: true`, options `--table` and `--refs`. Selecting neither means no modifiers.

4. Save both answers to `config.json` in this skill's base directory (the directory containing this SKILL.md — reported as "Base directory for this skill" when the skill loads):
   ```json
   {"default_mode": "full", "default_modifiers": []}
   ```
   Valid `default_mode` values: `full`, `interactive`, `tldr`, `steelman`, `decision`, `sketch`. Valid `default_modifiers` entries: `--table`, `--refs`.

5. Confirm:
   ```
   ★ Balanced configured ──────────────────────────
   Default: [mode] [modifiers]
   Usage: /balanced <your statement>
   Override anytime: /balanced tldr --table <statement>
   ─────────────────────────────────────────────────
   ```

### Config Loading

On every invocation, check if `config.json` exists in this skill's base directory. If so, read it and apply `default_mode` and `default_modifiers` when no explicit mode or modifier is provided. Explicit arguments always override config. Ignore unknown values and fall back to `full`.

## Mode Selection

Treat the first word of the arguments as a mode only when it exactly matches a mode keyword below (case-insensitive) or the `-i` flag. Everything else is part of the statement — `/balanced I think I should quit` is a full-mode analysis of "I think I should quit", not interactive mode.

- **Full mode** (default): `/balanced <statement>`. Full 4-move analysis in a single structured pass.
- **Interactive mode**: `/balanced interactive <statement>` or `/balanced -i <statement>`. Socratic Q&A, one move at a time.
- **TL;DR mode**: `/balanced tldr <statement>`. 3-5 lines max. One key fact, one challenge, one action. Output in insight box format:
  ```
  ★ Balanced ─────────────────────────────────────
  [key fact]. [challenge to assumption].
  → Action: [concrete next step].
  ─────────────────────────────────────────────────
  ```
- **Steelman mode**: `/balanced steelman <statement>`. Only moves 1+2. Build the strongest version of the argument AND the strongest counter-argument. No action steps. For preparing to defend a position.
- **Decision mode**: `/balanced decision <statement>`. Only move 4 (refinement). For when analysis is done and the call needs to be made. Output a tradeoff table with one row per option and columns for key gain, key cost, main risk, and reversibility, then state the recommended option, the confidence level, and what evidence would change the call.
- **Sketch mode**: `/balanced sketch <statement>`. All four moves as a hand-drawn-style HTML diagram: the claim at the top, wires down to four cards (holds, breaks, reframe, unknown), and a net card with a confidence meter and the next step. For seeing the shape of the argument at a glance.
  1. Write the analysis as JSON, following the schema in `scripts/render_sketch.py`: `statement`, `claim`, the four branch lists, `net` (`summary`, `confidence` 0–100, `action`), and optional `refs`. Use at most 3 lines per branch and about 10 words per line; leave a branch as `[]` when it has nothing to say. With `--refs`, tag lines with `[1]`, `[2]` and fill `refs`.
  2. Save the JSON to a scratch or temp directory unless the user names a location, then render it with the script in this skill's base directory: `python3 <base dir>/scripts/render_sketch.py sketch.json -o sketch.html`. The script validates the data and prints the output path.
  3. Show the page with the host's file preview when one exists, otherwise open it (`open` on macOS, `xdg-open` on Linux). Reply with one line and the file path; do not repeat the analysis in chat.

## Output Modifiers

Append these flags to any mode:

- **`--table`**: Output pro/contra analysis as an ASCII table. Apply whenever the analysis has clear opposing factors. Example:
  ```
  ┌─────────────────────────┬─────────────────────────┐
  │ PRO                     │ CONTRA                  │
  ├─────────────────────────┼─────────────────────────┤
  │ Low upfront cost        │ Requires a daily habit  │
  │ Easy to reverse         │ Competes with core work │
  │ Builds on known skills  │ Success metric unclear  │
  └─────────────────────────┴─────────────────────────┘
  ```
- **`--refs`**: Force full academic references even in tldr/decision/sketch modes (normally omitted for brevity).

## Four Moves

### 1 | Surface Merits
- Acknowledge well-supported points or creative angles.
- State why they are non-trivial. No generic praise.
- **Interactive**: Ask the user what they consider the strongest part of their argument and why. Then offer the analysis.

### 2 | Rigorous Challenge
- Question assumptions and potential biases.
- Test logic for gaps, fallacies, or over-generalization.
- Offer counter-evidence or rival explanations.
- **Interactive**: Present the strongest counter-argument found. Ask the user how they would respond to it. Then evaluate their response.

### 3 | Expansion
- Suggest alternative framings, methods, or resources.
- When helpful, pose clarifying questions rather than assume.
- **Interactive**: Ask what alternatives the user has considered. Then suggest framings they may have missed.

### 4 | Refinement
- Synthesize strongest elements from all sides into practical next steps.
- Flag residual uncertainty and cite sources.
- **Interactive**: Present a draft synthesis. Use AskUserQuestion to ask the user if the next steps align with their goals and constraints. Adjust based on their response.

## Interactive Mode Flow

When in interactive mode:
1. Begin by restating the user's position in one sentence. Use AskUserQuestion to confirm accuracy (options: accurate / needs correction).
2. Walk through each move sequentially, one exchange per move. Ask open questions (moves 1–3) in plain text and end the turn to wait for the answer — they have no sensible fixed options. Use AskUserQuestion only for questions with a few clear answers, such as the move 4 alignment check.
3. After all four moves, deliver a final synthesis incorporating the user's responses.
4. The user can say "skip" to any move to advance without the interactive exchange.

## Meta-Rules

- No flattery. No needless pessimism.
- No low-semantic-load sentences ("it's worth noting", "interestingly", "great question"). No unsupported opinions: every judgment, including a decision-mode recommendation, states the evidence or reasoning behind it and a confidence level.
- Maintain neutral, analytical tone. Quantify confidence when possible (e.g., "~70% confident based on available evidence").
- Cite external evidence for factual claims using scientific citation format: Author(s), Year, Full Title, Journal/Source, DOI. When referencing a DOI, perform a web search to validate it exists.
- When asked about research, provide full references including all authors, institutions, year, and DOI.
- Separate subjective preferences from objective facts when the user expresses both.
- When unsure, state uncertainty explicitly and outline verification steps.
