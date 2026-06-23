# Process Budget & Size/Risk Triggers

Process scales to feature **size**, not just risk. When the process exceeds the feature, stop feeding the beast. This file expands step 2 of the loop.

## Size tiers → process
- **S** (<½ day, low-risk, no public API/migration): Goal Contract (can be informal) + TDD + run the repo's checks + merge. **No plan, no tracker, no adversarial review, no documents.**
- **M** (1–2 days, some UI/integration): + plan only if it grows · tracker if 2+ real tasks · visual evidence if UI changes · adversarial review only if non-trivial.
- **L** (multi-day; shared contracts, migrations, auth/billing/permissions, AI behavior, data retention): full gates — plan approval, adversarial review, rollback note; visual evidence per the change rule (matrix only if the Goal Contract or a known bug-variability requires it).
- **XL:** do not run whole — **split first.**

## Gates
- **Required:** Goal + Risk approval (cheap-to-change moment).
- **Conditional — Plan approval:** only if the feature is >1 day, **or** touches auth/billing/PII/permissions/prompts/model-behavior/data-retention/migrations/prod, **or** changes public API/UX, **or** has irreversible user-data effects.
- **Required:** Review + merge (irreversible moment).

## Audit — independent fresh-context review, scaled by size/risk
- **L (or shared-contracts / auth / data / R3+):** required at **both** touchpoints — plan audit before building, diff audit before merge.
- **M:** invoke when the diff is non-trivial.
- **S / trivial:** skip.
- Timeout-bound with a self-review fallback (never block on a hung validator); findings persisted in `evidence/audit-*.md` and folded back before proceeding. An audit informs the human gates; it does not replace goal/merge approval.

## Visual evidence — trigger by change, not by tier
- **Blocking** only when the change touches user-visible **layout, styling, onboarding, or auth/safety** flows.
- **Advisory** (informs review, doesn't block) for other user-visible behavior.
- **None** for pure backend/logic.
- Smallest representative evidence: the *changed flow* at **one primary viewport** by default. Widen to a device/orientation/theme matrix only when the Goal Contract says those surfaces matter or the bug is known to vary by them. Baseline-snapshot updates are approved in the diff/PR review, not as a separate gate.

## v0 budget (tripwire, not sacred)
Goal Contract ≈ 15–30 min · ≤3 core generated docs · visual ≤1 changed flow / 1 viewport by default · audit per the size/risk table (S/M: ≤once, timeout-bound; L: plan + diff) · human gates = goal approval + final merge (plan approval only if a trigger fires). When you exceed this for an S/M feature, that is the signal the process is outrunning the feature — cut, don't add.

## Human-only judgment (never automate to "truth")
Approve the Goal Contract wording · risk-classification sanity/override · judge whether a plan is too invasive · approve baseline-screenshot changes · review the final diff · decide whether the shipped slice is enough. A green suite is necessary, never sufficient.
