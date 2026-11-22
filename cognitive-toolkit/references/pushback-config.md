# Pushback Configuration

The single source of truth for pushback: the level names, the default, and how many times the toolkit holds the frame when a user wants to skip an uncomfortable step. Other files point here instead of restating levels.

---

## Principles

1. **Never coercive** — always yields. The user is in control.
2. **Names, doesn't diagnose** — "I notice you want to move past this", not "You're avoiding". No interpretation of *why* the user wants to skip.
3. **Step-aware** — only inside a technique step, never when switching techniques or stopping.
4. **Safety and accuracy switch it off** — no pushback during a safety response, TIPP, the thought record's Accuracy Check, a justified check about real danger, or a need for rest in Behavioral Activation, whatever the level.
5. **Skips are recorded** — logged in `steps_skipped` in the saved session.

---

## Levels

One naming scheme everywhere: flags, mid-session commands, and the `pushback_level` frontmatter field all use these names.

| # | Name | Behavior | Exchanges before yielding |
|---|---|---|---|
| 0 | `off` | No pushback. `next` / `skip` advances at once. | 0 |
| 1 | `gentle` | One soft redirect. | 1 |
| 2 | `moderate` | Names the wish to skip, offers a different angle. | 2 |
| 3 | `firm` | As moderate, plus one question about what makes the step hard. | 3 |

**Default: `moderate` (2).** It is set here and nowhere else. There is no separate config file.

### Level 1: gentle

"This step often matters most — want to give it a try?"

If the user insists → yield, advance, log skip.

### Level 2: moderate (default)

**1st exchange:** "I notice you want to move past examining the evidence — that's often where the discomfort is, and also where things shift. What if we try just one piece of counter-evidence?"

**2nd exchange:** "Sometimes it helps to approach it differently. Instead of evidence against your thought, what would you say to a friend who had this same thought?"

**3rd insistence** → yield, advance, log skip.

### Level 3: firm

**1st exchange:** same as moderate.

**2nd exchange:** "What's making this hard to sit with?" If the user engages, work with what they say, then return to the step once.

**3rd exchange:** if the user still wants to skip → "OK, we'll skip the evidence step. Let's continue." Log the skip. Do not comment on what the skip means.

Technique files may give step-specific wording for each level. Their wording replaces the examples above; the number of exchanges per level does not change.

---

## Pushback Zones

Each technique marks its steps:

- **Core** — the level applies fully. The therapeutic work happens here.
- **Supportive** — at most one gentle exchange, whatever the level. Setup and context steps.
- **Closing** — no pushback ever. Summary and re-rating.

### Thought Record

| Step | Name | Zone |
|------|------|------|
| 1 | Situation | Supportive |
| 2 | Automatic Thought | Supportive |
| 3 | Emotion | Supportive |
| 4 | Evidence For | **Core** |
| 5 | Evidence Against | **Core** |
| — | Accuracy Check | none |
| 6 | Balanced Thought | **Core** |
| 7 | Re-rate Emotion | Closing |

Zones for every other technique are listed in that technique's own file.

---

## Changing the Level

- **At start:** `/cbt --pushback [off|gentle|moderate|firm]`
- **"harder"** → up by one (cap at `firm`). "Got it, I'll push a bit more."
- **"softer"** → down by one (floor at `off`). "OK, lighter touch."
- **"no pushback"** → `off`. "OK, no pushback."

Changes last for the current session only.

---

## Skip Tracking

Skips are logged per session in `steps_skipped`. Reviewing them across sessions (for example, always skipping Evidence Against) is not implemented yet — there is no review skill and no `patterns/` output. Do not tell the user that patterns are being analysed.
