# Synthetic Session Generator

Generate realistic, **persona-consistent** synthetic coaching & therapy session transcripts for
evals, demos, and training data — fictional but believable, and always watermarked as synthetic.

## Why

Real session transcripts are sensitive and scarce. This skill produces convincing stand-ins for
three jobs:

- **Eval datasets** — labelled transcripts (with a `ground_truth` block) to benchmark summarizers and analyzers
- **Product demos** — realistic sessions without exposing any real client data
- **Training / prompt examples** — few-shot material for a coaching or therapy assistant

Realism rests on two disciplines: **persona consistency** (the client speaks the same way and
carries the same history across a session arc) and **modality fidelity** (the practitioner uses the
techniques and pacing of the chosen framework).

## Features

- 🧩 **4 modalities** — ICF/GROW coaching, CBT, IFS parts-work, ACT/Motivational Interviewing, each with a technique cheat-sheet
- 👤 **Persona bible** — reusable personas (Maya, Diego, Priya, …) so a session series stays in voice; invent-and-persist new ones
- 📄 **4 output formats** — Fathom/Granola style, plain dialogue, structured JSON (with eval tags), Obsidian markdown — markdown always rendered
- ⏱️ **Timestamp emulation** — timing computed from turn length (~150 wpm), never hand-faked
- 🌍 **Setup mode** — persist defaults for language (8 languages), modality, and session duration
- 🖼️ **Case-conceptualization card** — modality-aware formulation + an illustrative portrait via the `gpt-image-2` skill
- 📊 **HTML case page** — render the card (portrait + conceptualization) as a Tufte-style page via `tufte-report`
- ⚠️ **Always watermarked** — every artifact is marked synthetic; never presentable as a real clinical record
- ✅ **Hardened** — validated across 8 Codex audit rounds (malformed input, encoding, pipe handling, etc.); `VERDICT: ALL CLEAR`

## Architecture

```
synthetic-session-generator/
├── SKILL.md                  # setup → spec → scaffold → author → render → card → HTML → save
├── references/
│   ├── modalities.md         # ICF/GROW, CBT, IFS, ACT-MI cheat-sheets + eval labels
│   ├── personas.md           # persona bible + template
│   └── realism_guide.md      # disfluency, resistance, arc-by-position, anti-patterns
└── scripts/
    ├── _common.py            # shared watermark, config, validation, timestamps, frontmatter
    ├── setup_config.py       # setup mode (language / modality / duration)
    ├── scaffold_session.py   # spec → JSON skeleton (phases, beats, turn budget)
    ├── convert_format.py     # JSON → fathom / plain / markdown / json (+ --auto-timestamps)
    └── make_card.py          # session JSON → case-conceptualization card + portrait prompt
```

## Quick start

```bash
# Copy to skills directory
cp -r synthetic-session-generator ~/.claude/skills/

# Configure defaults (optional)
/synthetic-session-generator setup        # choose language / modality / duration

# Generate a session
/synthetic-session-generator               # asks for persona, modality, position, format

# Under the hood
python3 scripts/scaffold_session.py --modality ifs --persona maya --position mid-arc --out s.json
# ...author the dialogue into s.json's "turns"...
python3 scripts/convert_format.py --in s.json --to markdown --auto-timestamps --out session.md
python3 scripts/make_card.py --in s.json --out card.md
```

## Safety & scope

Output is **fictional illustration, not clinical advice**. Personas are composites, never real
people; portraits are stylized illustrations, never photoreal. The skill *generates* — it does not
analyze real sessions (that's `coaching-session-summarizer`) or anonymize real data (that's
`session-anonymizer`).
