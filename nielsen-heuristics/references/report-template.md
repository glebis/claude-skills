# Report Template

The canonical output format. Keep it stable across runs — consistency is the deliverable. Two variants: **Evaluation mode** (scored) and **Design-risk mode** (unscored). A worked example finding is at the bottom to anchor severity calibration.

---

## Evaluation mode template

```markdown
# Heuristic Evaluation — <artifact name/URL>

**Mode:** Evaluation · **Input type:** <screenshot | live URL | codebase>
**Inventory examined:** <list of screens / elements / flows / files walked>

## Findings by heuristic

### H1 — Visibility of system status · rollup: <max severity, e.g. Sev 3>
- **[Sev 3]** <finding>. *Evidence:* <locator>. *Fix:* <concrete fix>.
- **[Sev 1]** <finding>. *Evidence:* <locator>. *Fix:* <fix>.

### H2 — Match between system and real world · rollup: <Sev / None / N/A>
- <findings, or "Checked X, Y, Z — no issues.", or "N/A — <reason>">

... (repeat H3–H10; every heuristic appears, even if None or N/A) ...

## Top 3 prioritized fixes
1. **<heuristic>** — <fix> (Sev 4) — <why highest leverage>
2. ...
3. ...

## Verdict
**<Blockers present | Major issues | Minor issues only | No blockers found in heuristic inspection>**
<one-line justification>
_Caveat: a single evaluator finds only ~1/3 of usability problems; 3–5 evaluators are recommended for confidence. This is not a "ready to ship" sign-off._
```

---

## Design-risk mode template

```markdown
# Heuristic Design-Risk Review — <spec/JTBD name>

**Mode:** Design-risk review · **Input type:** <interface description | JTBD/spec doc>
**Sections reviewed:** <list of spec sections / described flows>

> These are UNSCORED risk flags for an interface that does not yet exist. No severities are assigned.

## Risk flags by heuristic

### H1 — Visibility of system status
- **[Risk]** <what the design direction puts at risk>. *Evidence:* "<quoted spec sentence>" or <named gap>. *De-risk by:* <what to specify>.

... (repeat H2–H10; note "No risk identified" or "Not addressed by spec" where apt) ...

## Risk summary
- **Highest-risk heuristics:** <e.g. H5, H9 — no error states specified>
- **What to specify next to de-risk:** <concrete additions to the spec>
_No scored verdict: there is no running system to inspect. Re-run in Evaluation mode once a build or prototype exists._
```

---

## Worked example finding (calibration anchor)

For a checkout page (live URL):

> ### H5 — Error prevention · rollup: Sev 4
> - **[Sev 4]** The "Delete account" button executes immediately on click with no confirmation; the account and its order history are unrecoverable. *Evidence:* clicked `button.danger#delete-account` on `/settings` — page navigated straight to a "Deleted" state, no dialog. *Fix:* add a typed-confirmation dialog ("type DELETE to confirm") and a 30-day soft-delete grace period.
> - **[Sev 2]** The phone field accepts free text with no format mask, so users submit unparseable numbers. *Evidence:* `input#phone` on `/checkout` accepted "call me". *Fix:* add an input mask and inline validation.

Why Sev 4 vs Sev 2: the delete is **catastrophic** (data loss, irreversible, high impact) → 4. The phone field is a recoverable, low-frequency slip → 2. This gap is the calibration reference — do not inflate minor cosmetic issues toward the top of the scale.
