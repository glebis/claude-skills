# Worker brief

Replace bracketed fields before dispatch. Keep the brief self-contained; omit inapplicable sections.

## Assignment

- Issue and priority: [tracker ID, summary, dependency state]
- Role: [implementation / review only]
- Project and working checkout: [absolute paths]
- Objective and acceptance criteria: [observable outcome]
- Required reading: [absolute instruction/spec paths]

## Ownership and boundaries

You are not alone in this checkout. Preserve existing dirty/untracked work and other agents' changes. Do not revert or overwrite them.

- Owned files/modules: [explicit paths and allowed changes]
- Shared integration owner: [owner; route requests here]
- Excluded files/data: [paths; include read-only references]
- Allowed evidence outputs: [absolute issue work directory]
- Allowed operations: [tests, loopback, disposable copies, etc.]
- Prohibited operations: [unrelated edits, private data, separate live evaluation/provider calls, credential operations, external fetch/install, messages, deployment/publication, source Git mutation, as applicable; distinguish these from the CLI agent's normal authorized model use]
- Disposal: use fresh temporary targets; do not permanently delete scratch data.

For review-only work, own reports/support files and disposable copies only. Do not fix implementation, change tracker status, or integrate worktrees.

## Inputs and verification

- Input baseline: [Git ref, dirty source manifest, required uncommitted inputs]
- Stop and report: [unexpected input drift, ownership collision, unavailable dependency, scope/permission mismatch]
- Required checks: [commands, cwd, timeout, expected scope]
- Evidence: capture exact command, cwd, relevant input identity, start/end, real exit code, counts/skips, log path, and simulated/live status. Preserve failures and continue independent checks. Do not mask status with a trailing display command or rerun unchanged checks repeatedly.
- Temporary outputs: [unique location; preserve original generated artifacts]
- Known limits: [unverified host/UI/provider behavior, missing recordings/golden labels, etc.]

## Handoff

Write [absolute result.md] containing changed files, findings with exact file/line evidence, checks and logs, unresolved risks, and any ownership/integration requests. Write [command manifest path] for structured execution evidence. Do not claim all acceptance criteria are met when only a subset was exercised.

Stop at the bounded handoff and print [unique ready-for-review marker]. Leave the issue open for coordinator acceptance. Do not close your tab or keep polishing after handoff unless asked.
