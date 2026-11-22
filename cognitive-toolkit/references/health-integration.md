# Health Integration Reference

> Optional context. The toolkit works fully without any health data, and health data never decides whether or how well a session went.

---

## When to use

Only if a health MCP is available in the session and `--no-health` was not passed. If it is unavailable or a call fails, skip silently and do not mention it.

Tool names depend on the installed health MCP. Typical ones:

| Tool | Data |
|------|------|
| `mcp__health__latest_vitals` | HRV, resting HR |
| `mcp__health__sleep_analysis` | Sleep duration, stages |

Check what is actually available rather than assuming these names.

---

## HRV: baseline-relative, start of session only

HRV differs several-fold between healthy people, and devices report different measures (Apple Watch reports SDNN, most rings report RMSSD). An absolute cutoff is therefore meaningless. Only compare a person's reading with **their own recent readings from the same device**.

At check-in:

1. Get the latest HRV reading and its timestamp. If it is older than 12 hours, ignore HRV for this session.
2. Get the readings from the previous 14–30 days if the MCP exposes them. With fewer than 7 readings there is no baseline — ignore HRV for this session.
3. Classify the latest reading against that baseline:
   - below the 25th percentile → `below-baseline`
   - above the 75th percentile → `above-baseline`
   - otherwise → `within-baseline`
4. Store the label as `hrv_context` in the session frontmatter.

**How to use the label:**

- `below-baseline` → mention it once, lightly, and let the user decide: *"Your HRV is lower than your usual range today — bodies have rougher days. Want to start with a couple of slow breaths, or go straight in?"* Nothing else changes.
- `within-baseline` / `above-baseline` → say nothing; just log it.

---

## What not to do

- **No pre/post HRV comparison within a session.** Wearables sample HRV sporadically, so a second reading ten minutes later is usually the same sample or an unrelated one. A within-session "delta" is noise. Never tell the user their HRV improved because of the exercise.
- **No absolute thresholds** ("HRV under 30 is low").
- **No readiness or recovery scores as a gate.** A low score is never a reason to refuse or water down a technique the user asked for.
- **No correlation claims** ("low HRV days go with negative thinking") unless a review of this user's own saved sessions has actually shown it.
- **Never invent or estimate a value.** If something is missing, omit the field.

---

## Sleep

If last night's sleep is available and clearly short for this user (again relative to their own recent nights), it may be mentioned once as context at check-in, in the same light tone. It does not change technique selection.

---

## Genetic data

Not used. Candidate-gene findings do not support adjusting the pacing or choice of a psychological technique for an individual, so the toolkit does not read a genome vault and does not record genetic fields.

---

## Failure Modes

| Situation | Behaviour |
|-----------|-----------|
| Health MCP unreachable | Skip silently |
| Latest reading stale (> 12 h) | Ignore HRV this session |
| No baseline (< 7 readings) | Ignore HRV this session |
| Partial data | Use what is available, omit the rest |
