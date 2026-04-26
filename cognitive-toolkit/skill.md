---
name: cognitive-toolkit
description: Evidence-based CBT and DBT intervention skills — guided thought records, opposite action, DEAR MAN roleplay, crisis skills with optional HRV biofeedback. Configurable therapeutic pushback. Triggers on "/cbt", "/dbt", "/thought-record", "/record", "/opposite", "/opposite-action", "I need to work through something", "help me with a thought", "cognitive distortion", "I'm spiraling", "can we do a thought record".
---

# Cognitive Toolkit

Interactive CBT and DBT guided exercises with configurable therapeutic pushback and optional health data integration.

## Usage

```
/cbt                        # start with check-in → technique recommendation
/cbt thought-record         # jump directly to thought record
/cbt opposite-action        # jump directly to opposite action
/cbt --pushback firm        # override pushback level for this session
/cbt --no-health            # skip health data pull even if available
```

## How it works

1. Read `references/thought-record.md` — thought record protocol (ABC model, cognitive distortion taxonomy, reframe scaffold)
2. Read `references/opposite-action.md` — opposite action + DEAR MAN + TIPP crisis skills
3. Read `references/pushback-config.md` — pushback levels, triggers, and mid-session override commands
4. Read `references/health-integration.md` — HRV/sleep pull, biofeedback interpretation, skip logic

## Session Flow

**Without technique argument** (full flow):
1. Check-in — mood (0–10), brief situation summary
2. Recommend — match presenting issue to technique based on check-in
3. Load technique — read the relevant reference file
4. Protocol — run the full guided exercise
5. Close — summary, insight, one takeaway
6. Save — write session to vault output

**With technique argument** (direct jump):
1. Brief mood check (0–10, one line)
2. Load technique — read the relevant reference file
3. Protocol — run the full guided exercise
4. Close — summary, insight, one takeaway
5. Save — write session to vault output

## Available Techniques

| Command | Technique | Reference | Wave |
|---|---|---|---|
| `thought-record` | Thought Record (ABC + reframe) | `references/thought-record.md` | 1 |
| `opposite-action` | Opposite Action (DBT emotion regulation) | `references/opposite-action.md` | 1 |
| `dear-man` | DEAR MAN assertiveness roleplay | `references/opposite-action.md` | 2 |
| `tipp` | TIPP crisis/distress tolerance | `references/opposite-action.md` | 2 |
| `chain` | Chain Analysis (behavior chain) | `references/thought-record.md` | 3 |
| `activation` | Behavioral Activation (depression) | `references/thought-record.md` | 3 |
| `wise-mind` | Wise Mind (emotion vs. reason) | `references/opposite-action.md` | 3 |

## Pushback

See `references/pushback-config.md` for full configuration.

- Defaults loaded from `references/pushback-config.md` (default: `gentle`)
- Per-session override: `/cbt --pushback [gentle|moderate|firm]`
- Mid-session commands: `softer`, `harder`, `no pushback` adjust level in real time
- Pushback is Socratic, not confrontational — "What evidence supports that?" not "That's wrong"

## Health Data

See `references/health-integration.md` for full integration logic.

- Optional: pulled from health MCP if available at session start
- Surfaces HRV, sleep quality, resting HR as contextual framing only
- Skip silently if health data unavailable or if `--no-health` flag passed
- Never gate a session on health data — it's context, not gatekeeper

## Telegram Entry Points

| Command | Maps to |
|---|---|
| `/record` | `thought-record` |
| `/opposite` | `opposite-action` |
| `/dear` | `dear-man` |
| `/tipp` | `tipp` |
| `/checkin` | full check-in flow |
| `/wise` | `wise-mind` |
| `/settings` | adjust pushback level and health toggle |

## Anti-patterns

- NOT a diagnostic tool — never assess, label, or diagnose
- NOT a therapist replacement — this is a practice tool for between sessions
- Frame suggestions as "research suggests" not "you should"
- If user expresses emergency, suicidal ideation, or acute crisis: stop the technique immediately, acknowledge, and provide crisis resources (e.g., Telefonseelsorge 0800 111 0 111 in Germany, international directory at findahelpline.com)

## Vault Output

Sessions saved to: `~/Brains/brain/cognitive-toolkit/sessions/YYYYMMDD-[technique]-NN.md`

Format: frontmatter with date, technique, mood-before, mood-after + full session transcript.
