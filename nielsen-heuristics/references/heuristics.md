# The 10 Usability Heuristics + Severity Rubric

Reference for Step 3 of the evaluation. Each heuristic lists a definition, "what to look for" probes, and common violations. The severity rubric is at the bottom.

---

## H1 — Visibility of system status

**Definition:** The system should always keep users informed about what is going on, through appropriate feedback within reasonable time.

**Probes:**
- Is there immediate feedback for every action (hover, click, submit, save)?
- Are loading, processing, and background states shown (spinners, progress, skeletons)?
- Is current location/state visible (active nav item, step in a wizard, selected filters)?
- Are results of an action confirmed (toast, updated count, success state)?

**Common violations:** silent submits with no spinner; no confirmation after save; unclear which tab/step is active; actions that appear to do nothing.

---

## H2 — Match between the system and the real world

**Definition:** Speak the users' language with familiar words, phrases, and concepts. Follow real-world conventions; information appears in a natural and logical order.

**Probes:**
- Is the vocabulary the user's, not the system's/engineer's (no raw codes, DB field names, jargon)?
- Do icons and metaphors map to real-world expectations?
- Is information ordered the way the user thinks about the task?
- Are dates, numbers, and units in the user's conventions?

**Common violations:** error codes instead of plain language; internal terminology in the UI; unfamiliar icons without labels; illogical field ordering.

---

## H3 — User control and freedom

**Definition:** Users often perform actions by mistake. They need a clearly marked "emergency exit" to leave the unwanted state — support undo and redo.

**Probes:**
- Can the user cancel, go back, or undo without penalty?
- Are destructive actions reversible or at least confirmable?
- Is there an obvious close/exit from modals, wizards, and flows?
- Can in-progress work be abandoned cleanly?

**Common violations:** no undo after delete; modal with no visible close; multi-step flow that can't be exited; forced completion.

> On a **static screenshot** this is often **N/A** — undo/back behavior can't be observed without interaction.

---

## H4 — Consistency and standards

**Definition:** Users should not have to wonder whether different words, situations, or actions mean the same thing. Follow platform and industry conventions (internal + external consistency).

**Probes:**
- Are the same words, colors, and components used for the same meaning throughout?
- Do primary actions look/behave consistently across screens?
- Does it follow platform conventions (iOS/Android/web patterns, standard icons)?
- Are interaction patterns predictable?

**Common violations:** two names for the same thing; inconsistent button styles for the same action; non-standard controls that violate platform norms.

---

## H5 — Error prevention

**Definition:** Even better than good error messages is a careful design that prevents problems from occurring in the first place. Eliminate error-prone conditions or check for them and present a confirmation.

**Probes:**
- Are invalid states prevented (disabled buttons, constrained inputs, sensible defaults)?
- Is inline validation present before submission?
- Are destructive/high-cost actions guarded with confirmation?
- Are slips designed out (formatting masks, pickers instead of free text)?

**Common violations:** free-text where a picker belongs; no confirmation before irreversible action; validation only after submit; easy to lose data.

---

## H6 — Recognition rather than recall

**Definition:** Minimize memory load by making elements, actions, and options visible. The user should not have to remember information from one part of the interface to another.

**Probes:**
- Are options visible rather than requiring the user to recall them?
- Is needed information carried forward (not re-entered)?
- Are instructions/hints visible at the point of need?
- Are recently used / suggested items surfaced?

**Common violations:** requiring codes/IDs to be remembered across screens; hidden options behind unlabeled icons; help buried away from the task.

---

## H7 — Flexibility and efficiency of use

**Definition:** Shortcuts — unseen by the novice — may speed up interaction for the expert. Allow users to tailor frequent actions. Serve both inexperienced and experienced users.

**Probes:**
- Are there accelerators for frequent tasks (keyboard shortcuts, bulk actions, saved views)?
- Can power users move faster without penalizing novices?
- Is personalization/customization available where it matters?
- Are common paths short?

**Common violations:** no bulk operations for repetitive tasks; no keyboard support; every user forced down the beginner path.

---

## H8 — Aesthetic and minimalist design

**Definition:** Interfaces should not contain information that is irrelevant or rarely needed. Every extra unit of information competes with the relevant units and diminishes their relative visibility.

**Probes:**
- Is every element earning its place, or is there visual/content clutter?
- Is the primary action clearly dominant in the visual hierarchy?
- Is content prioritized (most important first, progressive disclosure for the rest)?
- Is signal-to-noise high?

**Common violations:** competing calls-to-action; dense walls of text; decorative noise; no clear hierarchy.

---

## H9 — Help users recognize, diagnose, and recover from errors

**Definition:** Error messages should be expressed in plain language (no codes), precisely indicate the problem, and constructively suggest a solution.

**Probes:**
- Are error messages in plain language, not codes?
- Do they say exactly what went wrong AND how to fix it?
- Are errors shown next to the source (inline, not just a top banner)?
- Is recovery a clear next action, not a dead end?

**Common violations:** "Error 500" with no guidance; generic "Something went wrong"; error far from its cause; no path to recovery.

> On a **static screenshot** this is often **N/A** unless an error state is captured.

---

## H10 — Help and documentation

**Definition:** It's best if the system doesn't need documentation, but it may be necessary to provide help. Help should be easy to search, focused on the user's task, list concrete steps, and not be too large.

**Probes:**
- Is contextual help available where needed (tooltips, inline hints, empty-state guidance)?
- Is documentation findable and task-focused?
- Are empty states used to teach the next action?
- Is help concise and actionable?

**Common violations:** no onboarding or empty-state guidance; help that's generic and not task-oriented; no way to get unstuck in-context.

---

## Severity rubric (Nielsen 0–4) — rate each FINDING, not each heuristic

Severity is a combined judgment of **frequency × impact × persistence** (how often it's hit, how badly it hurts when hit, and whether users can get past it once they learn it).

| Score | Label | Meaning |
|-------|-------|---------|
| **0** | Not a problem | Do not report as a finding. |
| **1** | Cosmetic | Fix only if extra time is available. |
| **2** | Minor | Low priority to fix. |
| **3** | Major | Important to fix; high priority. |
| **4** | Catastrophe | Imperative to fix before release. |

A single heuristic can yield findings at several severities at once, or none. The report groups findings by heuristic and shows a **max-severity rollup** per heuristic — it does not assign one score to the whole heuristic.

**Design-risk mode:** do NOT use this scale. There is no running system to observe, so findings are unscored **risk flags** ("potential, unverified"). Report which heuristics the design direction puts at risk and what to specify to de-risk them.
