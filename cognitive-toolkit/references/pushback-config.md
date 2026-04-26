# Pushback Configuration

Central authority on therapeutic pushback behavior — the bot's ability to hold the frame when users skip uncomfortable steps.

---

## Principles

1. **Never coercive** — always yields eventually. The user is in control.
2. **Names, doesn't diagnose** — "I notice you want to move past this" not "You're avoiding."
3. **Step-aware** — only activates within a technique, never when switching techniques.
4. **Skips are recorded** — logged in session output for longitudinal tracking.

---

## Level 0: Off

No pushback. "next" / "skip" immediately advances.

**Use case:** Experienced practitioners who know the techniques and self-direct.

---

## Level 1: Gentle

One soft redirect, then yields.

**Example:** "This step often matters most — want to give it a try?"

If user insists → yield, advance, log skip.

---

## Level 2: Moderate (default)

Names avoidance, offers alternative framing, yields after 2 attempts.

**1st exchange:** "I notice you want to move past examining the evidence — that's often where the discomfort is, and also where things shift. What if we try just one piece of counter-evidence?"

**2nd exchange:** "Sometimes it helps to approach it differently. Instead of evidence against your thought, what would you say to a friend who had this same thought?"

**3rd insistence** → yield, advance, log skip.

---

## Level 3: Firm

Names avoidance, explores resistance, up to 3 exchanges, yields with explicit note.

**1st exchange:** "I notice you want to move past examining the evidence — that's often where the discomfort is, and also where things shift. What if we try just one piece of counter-evidence?"

**2nd exchange:** "What's making this hard to sit with?" *(explores resistance itself — this IS therapeutic work)*

**3rd exchange:** If user engages, work with it then redirect; if user insists → "OK. I want to note that we're skipping the evidence examination — that's a pattern worth watching over time. Let's continue."

---

## Pushback Zones

Not all steps are equal. Each technique reference marks steps as:

- **Core** — pushback applies fully. The therapeutic work happens here.
- **Supportive** — always gentle (max 1 exchange). Setup and context steps.
- **Closing** — no pushback ever. Summary and re-rating.

### Example: Thought Record

| Step | Name | Zone |
|------|------|------|
| 1 | Situation | Supportive |
| 2 | Automatic Thought | Supportive |
| 3 | Emotion | Supportive |
| 4 | Evidence For | **Core** |
| 5 | Evidence Against | **Core** |
| 6 | Balanced Thought | **Core** |
| 7 | Re-rate Emotion | Closing |

Steps 4–5 are where cognitive restructuring happens. Step 6 consolidates it. Step 7 is measurement only — never push.

---

## Mid-Session Adjustment

Users can shift the level during a session:

- **"harder"** → increase by 1 (cap at 3). Acknowledge: "Got it, I'll push a bit more."
- **"softer"** → decrease by 1 (floor at 0). Acknowledge: "OK, lighter touch."

Applies for current session only. Default in `config.md` unchanged.

---

## Longitudinal Pattern Tracking

Over multiple sessions, skip patterns tell a story:

- Always skipping Evidence Against? May indicate difficulty with self-compassion.
- Always skipping Emotion Rating? May indicate alexithymia or emotional avoidance.
- Same step skipped across techniques? Cross-technique pattern worth surfacing.

Skip data accumulates in session output logs. The `cognitive-toolkit/patterns/` directory is reserved for weekly and monthly reviews.

**Wave 1 scope:** Skip logging only. Pattern analysis is not implemented yet — the infrastructure is being laid now.
