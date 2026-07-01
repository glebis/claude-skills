# Goal Contract — CSV export for the invoices list

> Filled example (M-size feature) showing the expected calibration: terse bullets,
> solution-independent outcomes, every outcome mapped to evidence. The conditional
> section is omitted entirely — no trigger fired. Do not copy the content; copy the altitude.

## Core

### Current state (≤3)
- Users can only view invoices in the web list; getting them into a spreadsheet means copy-paste.
- Support gets ~2 requests/week for "send me my invoices as a file".

### Desired future state (≤3)
- A signed-in user can download their currently filtered invoice list as a CSV in one click.

### Desired outcomes (solution-independent, measurable; ≤5)
- Exported file opens cleanly in Excel/Numbers/Sheets (UTF-8 BOM, correct delimiters).
- Export respects the active filters — the file contains exactly the rows shown.
- Export of 10k rows completes without a request timeout.

### Smallest shippable slice   <!-- required -->
Export button on the invoices list → CSV of the visible columns, current filters applied. No column picker, no XLSX, no scheduling.

### Stop condition   <!-- required -->
If export requires touching the auth/permissions layer or a background-job queue, stop and re-scope with the human.

### Success evidence (≤5)
- Unit tests: CSV escaping (commas, quotes, newlines, unicode) — maps to "opens cleanly".
- Integration test: filtered request returns exactly the filtered rows — maps to "respects filters".
- Test with a seeded 10k-row dataset completing under the server timeout — maps to "10k rows".
- `evidence/verify.log` from the repo's real test/lint/typecheck commands.

### Risk classification
R2 user-facing low-stakes (user exports their own data; no new data exposure).
EU AI Act (or jurisdiction equivalent): Art 5 prohibited use? N/A · Art 50 labelling? N/A

### Tracker
none — single task, no decomposition.

---
**Fail rule:** if a goal can't produce evidence, it's a wish with better formatting — it doesn't pass.
