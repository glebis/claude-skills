# Work Reflection project locator

Use this file for discovery, not as a frozen copy of project state.

Default local project root:

`/Users/glebkalinin/Documents/Codex/2026-10-25/x20-pibot-claude-code-x20/outputs/work-reflection`

The user's explicit project path takes precedence. If this root no longer exists, locate the moved project narrowly rather than replacing it.

## Owning artifacts

- `src/index.prose.md`: canonical OpenProse responsibility, named `work-reflection`.
- `AGENTS.md` and `README.md`: project rules and entry points.
- `.beads/`: canonical task store, with `wr-` IDs. Always use this root explicitly; do not use Pibot's Beads, an ancestor database, or the global database.
- `reports/2026-10-25-source-inventory.md` and `reports/inventory-metadata.json`: original inventory; its limitations and original period remain part of the evidence.
- `reports/<task-id>/report.md` and optional `evidence.json`: task outcomes. Read fresh task notes for report locations.
- `runs/` and `state/`: existing OpenProse execution artifacts. Do not overwrite prior receipts while continuing an unrelated task.
- `work/`: scratch and draft programs, not a second backlog.

The baseline investigation period was the 168-hour interval `2026-10-18T12:41:50.018481+02:00` to `2026-10-25T11:41:50.018481+01:00` (end exclusive). This is a historical period, not “the last seven days” forever. Future periods must come from the current task/request.

## Read only when the corresponding source is in scope

- Pibot: `reports/wr-97n.1/report.md`. The first inventory missed a still-active legacy session path referenced by `sessions/index.json`; service events and in-memory sessions are not the same as chat transcripts. Consult the report before rediscovering this issue. Do not copy that historical routing assumption to every agent.
- Hermes: `reports/wr-97n.2/report.md`. Current model history, display history, and physical audit rows have different semantics; UID duplicates may preserve different payload versions. Consult the evidence before counting compressed history.
- Other task outcomes: discover them through current Beads notes and the specific task folder. Do not read all reports or all source archives by default.

## Optional visual board

A Beads UI instance was previously started on `http://127.0.0.1:4319/#/board`, with workspace `work-reflection`. Its current availability is not guaranteed. When asked to open it, verify the selected project and actual task cards. Runtime files were placed in `<project-root>/work/beads-ui-runtime`; package cache in `work/npm-cache`.

Use an existing compatible UI before installing another. A browser view is a live presentation of Beads, not an extra task database. Do not replace it with a misleading static snapshot or change task states just to populate columns.
