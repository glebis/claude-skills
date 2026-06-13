# Eval results

## 2026-06-03 · judge = Claude Opus 4.8 subagents (fresh context) · prompt v1

| Criterion | Result |
|---|---|
| planted-defects.md: `inconsistent-number` P0 | ✅ found, exact severity, correct location |
| planted-defects.md: `unsupported-claim` P0 | ✅ found, exact severity, correct location |
| planted-defects.md: `jargon-undefined` P1 | ✅ found (medium confidence, correct location) |
| missing-limitations.md: `limitations-present` P0 | ✅ found, exact severity |
| clean-control.md FP budget (0 P0, ≤1 P1, ≤3 P2) | ✅ zero findings of any severity |
| Schema validity (all findings) | ✅ verbatim quotes verified |

**Overall: PASS** (100% planted-P0 recall at exact severity; planted P1 found; clean
control clean).

### Notes

- The judge additionally flagged the planted doc's title ("Revolutionary") as
  `marketing-tone` P0 — this was a deliberate part of the overclaim plant and is a
  correct catch, not an FP.
- The judge found **genuine, unintended defects** in `missing-limitations.md`: the
  summary's "range 1.8–2.9×" contradicts the table's 1.1× row, and the stated median
  2.3× doesn't match the table median 2.2×. These are now **accepted as additional
  plants** (they are real `inconsistent-number` defects); future runs should expect them.
  Evidence of judge sharpness: it caught defects the eval author didn't notice planting.
- Lane-1 FP profile observed on a real document (CONFIDE white paper): caps taxonomy
  labels in tables (EMAIL/DATE/ORG…), caps emphasis (NOT), and prose-defined metrics
  (F1, AUC — glossed in text but not in a parenthetical pattern). Candidate v1.1
  refinement: dictionary-word filter + prose-definition pattern (`ABC is/means …`).
