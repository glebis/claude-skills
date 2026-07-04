# Tufte HTML Report Preset

How to render a heuristic evaluation as a Tufte-style standalone HTML report by delegating to the `tufte-report` skill. The `tufte-report` skill already has every block needed — do NOT modify it. This preset just specifies how to compose those blocks for a heuristic evaluation.

## Procedure

1. **Produce the structured findings first** (Steps 1–4 of SKILL.md). The evaluation must be complete before rendering — the HTML is a presentation layer, not a new analysis.
2. **Invoke the `tufte-report` skill** with the section plan below. Because the data is already in hand (the findings), skip tufte-report's data-source onboarding — state up front: "data source = the heuristic findings below; primary question = 'How usable is <artifact>?'; output = standalone HTML."
3. **Pass `assets/jakob-nielsen.png`** (this skill's mascot) as the report hero/masthead image.

## Section plan (maps onto tufte-report blocks)

| Report element | tufte-report block | Content |
|----------------|-------------------|---------|
| Masthead / hero | Section Header + image | Title "Heuristic Evaluation — <artifact>", the Nielsen mascot, mode + date |
| Verdict banner | Status Strip (4-col dashboard) | Verdict level · # findings · max severity · heuristics assessed / N/A |
| Severity distribution | Strip Chart (horizontal bars) | Count of findings at each severity 0–4 |
| Coverage | Summary Card row | Heuristics with findings · clean · N/A |
| Findings by heuristic | Flyout callouts, one per finding | Severity badge, evidence locator, fix — grouped under H1…H10 headers |
| Top-3 fixes | Data Table | Rank · heuristic · fix · severity |
| Caveat footer | State Line (italic) | The single-evaluator (~1/3 coverage) caveat |

## Rules carried over (do not drop them in HTML)

- Severity badges are **per finding**, not per heuristic; show the max-severity rollup on each heuristic header.
- Every finding still shows its **evidence locator** — it is a column/line in the flyout, never omitted for visual tidiness.
- Heuristics with no findings appear as "checked — no issues"; N/A heuristics appear as "N/A — <reason>". Do not silently drop them.
- **Design-risk mode:** replace the severity strip-chart and verdict dashboard with a "risk flags by heuristic" list and a "highest-risk heuristics" status strip — there are no severities to chart. Never render a 0–4 axis for a spec/JTBD input.
- Respect tufte-report's scope limits (max 8 sections). The plan above is 7 elements — keep it there; do not add decorative charts.
