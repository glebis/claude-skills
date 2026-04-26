# Claude Cognitive Toolkit

Evidence-based CBT and DBT intervention skills for AI assistants. Built for developers who want structured mental health support in their terminal workflow — without leaving the command line.

---

## CBT Thought Record Tool

A full 7-step cognitive restructuring workflow based on Aaron Beck's Cognitive Therapy and David Burns' *Feeling Good* methodology.

Steps:
1. Describe the situation
2. Identify automatic thoughts
3. Detect cognitive distortions (Burns' 10-category taxonomy)
4. Rate emotion intensity (0–100)
5. Generate a balanced alternative thought
6. Re-rate emotion after reframing
7. Export structured markdown with frontmatter

Distortion detection is automatic — the toolkit matches your thought against all 10 Burns categories and flags the most salient ones before asking you to reframe.

---

## DBT Skills Training

Skills from Marsha Linehan's Dialectical Behavior Therapy adapted for conversational AI delivery.

| Skill | Module | Status |
|---|---|---|
| Opposite Action | Emotion Regulation | ✅ Available |
| DEAR MAN | Interpersonal Effectiveness | 🔜 Wave 2 |
| TIPP | Crisis Survival | 🔜 Wave 2 |
| Wise Mind | Core Mindfulness | 🔜 Wave 3 |
| GIVE / FAST | Interpersonal Effectiveness | 🔜 Wave 4 |

**Opposite Action** guides you through identifying the action urge driven by an emotion, then choosing the behaviorally opposite response — evidence-based for breaking avoidance, shame spirals, and anger escalation.

**DEAR MAN** (Wave 2) includes roleplay: the AI plays the other person so you can rehearse assertive communication before the real conversation.

---

## Cognitive Distortion Detection

Automatic detection across all 10 Burns categories:

1. **All-or-Nothing Thinking** — seeing things in black/white, no middle ground
2. **Overgeneralization** — one negative event = a never-ending pattern of defeat
3. **Mental Filter** — dwelling on a single negative detail
4. **Disqualifying the Positive** — rejecting positive experiences as "not counting"
5. **Mind Reading** — assuming others' negative reactions without evidence
6. **Fortune Telling** — predicting things will turn out badly
7. **Magnification / Minimization** — catastrophizing or shrinking things inappropriately
8. **Emotional Reasoning** — "I feel it, therefore it must be true"
9. **Should Statements** — rigid rules that generate guilt and resentment
10. **Labeling and Mislabeling** — attaching a global negative label to yourself or others

---

## Anxiety Management

The toolkit features configurable pushback — the AI challenges negative thoughts with varying intensity based on your preference and current capacity.

### Configurable Pushback

| Level | Name | Description |
|---|---|---|
| 0 | Silent | Record only, no challenge |
| 1 | Gentle | Soft Socratic questions |
| 2 | Balanced | Moderate challenge + reframe (default) |
| 3 | Direct | Strong evidence-based confrontation |

Set `pushback_level: 2` in your skill config or pass `--pushback 3` at invocation.

---

## Developer Mental Health

Built by a developer for developers. Core design principles:

- **Terminal-native**: works inside Claude Code via `/cbt` slash command — no browser, no app switch
- **Structured data**: every session exports frontmatter-tagged markdown, importable into Obsidian or any PKM
- **Privacy-first**: all data stays local; no telemetry, no external API calls beyond your configured Claude
- **Composable**: integrates with HRV data, genome vault, and daily notes pipelines
- **Async-friendly**: start a record mid-debug session, pause, resume later

---

## HRV Biofeedback Integration

Optional physiological context enriches your thought records.

**Apple Health**: resting HRV, heart rate, sleep data pulled via local Health MCP or export.

**Aurora Ring**: overnight HRV trend, recovery score, and readiness index can be appended to session frontmatter.

**Genome Vault**: if you have a genome vault configured, CYP/BDNF/DRD2 pharmacogenomic context is available as a background note — relevant for interpreting mood patterns over time.

When HRV data is present, the toolkit adds a `hrv_context` block to output frontmatter and may adjust its framing (e.g., noting that low HRV days correlate with negative cognitive bias).

---

## Quick Start

### Claude Code

```bash
# 1. Copy skill file to your skills directory
cp cognitive-toolkit/skill.md ~/.claude/skills/cognitive-toolkit.md

# 2. Start a thought record
/cbt

# 3. Run opposite action
/opposite
```

### Telegram Bot

If you have a Telegram bot configured with this skill:

```
/record       — start a CBT thought record
/opposite     — run Opposite Action DBT skill
/checkin      — daily mood + distortion check-in
```

---

## Techniques

| Name | Type | Steps | Time | Status |
|---|---|---|---|---|
| Thought Record | CBT | 7 | 10–15 min | ✅ Available |
| Opposite Action | DBT | 5 | 5–10 min | ✅ Available |
| DEAR MAN | DBT | 7 | 15–20 min | 🔜 Wave 2 |
| TIPP | DBT | 4 | 5 min | 🔜 Wave 2 |
| Chain Analysis | DBT | 8 | 20–30 min | 🔜 Wave 3 |
| Behavioral Activation | CBT | 6 | 10–15 min | 🔜 Wave 3 |
| Wise Mind | DBT | 3 | 5–10 min | 🔜 Wave 3 |
| GIVE / FAST | DBT | 8 | 15–20 min | 🔜 Wave 4 |
| Affect Labeling | Neuroscience | 3 | 3–5 min | 🔜 Wave 4 |

---

## Health Data (Optional)

All health integrations are optional and off by default.

**Apple Health** — resting HRV, heart rate variability trends, sleep stages. Requires Apple Health MCP or manual CSV export.

**Aurora Ring** — overnight recovery score, readiness index, HRV baseline. Requires Aurora export or API token.

**Genome Vault** — pharmacogenomic markers (CYP1A2, BDNF Val66Met, DRD2, OPRM1). Requires a local genome vault at `~/Brains/genome/` or configurable path. Provides background context only — never diagnostic.

---

## Output

Each session produces a structured markdown file:

```markdown
---
type: thought-record
date: '[[20260426]]'
technique: thought_record
distortions: [all-or-nothing, fortune-telling]
emotion_before: 75
emotion_after: 40
pushback_level: 2
hrv_context: low  # if health data present
---

## Situation
...

## Automatic Thought
...

## Distortions Detected
- All-or-Nothing Thinking
- Fortune Telling

## Balanced Thought
...
```

Files are saved to `vault-output/` by default. Path is configurable in skill frontmatter.

---

## Not a Therapist

This toolkit is a **self-help tool** implementing publicly documented CBT and DBT techniques. It is not a substitute for professional mental health care.

- It does not diagnose conditions
- It does not replace a licensed therapist or psychiatrist
- It does not handle crisis situations — if you are in crisis, contact a mental health professional or crisis line

If you are experiencing a mental health emergency, please contact your local emergency services or a crisis hotline.

---

## License

MIT — see [LICENSE](LICENSE)

---

## Citation

If you reference this toolkit in academic or professional work, please cite it using the metadata in [CITATION.cff](CITATION.cff).
