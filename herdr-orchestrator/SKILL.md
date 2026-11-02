---
name: herdr-orchestrator
description: Coordinate multiple CLI agents in herdr with scoped briefs, verified startup, permission handling, independent review, and monitored handoffs. Use for parallel agent work or observer/evaluator supervision in herdr.
---

# herdr orchestrator

Use the installed `herdr` skill for CLI mechanics. Locate and read its `SKILL.md` and `scripts/herdr-task` before controlling terminals. This skill adds coordination and acceptance discipline; it does not grant terminal access or additional task authority.

## Establish scope

- Check `HERDR_ENV`. The base skill stops outside a managed pane. Continue outside it only when the human explicitly overrides that restriction for the current session; record the scope of that permission. Historical overrides are not universal permission.
- Keep the coordinator in the user's chosen role. In observer/evaluator mode, delegate implementation and send corrections to the responsible worker; write only briefs, reviews, and tracking evidence yourself unless the user changes that role.
- Use the CLI agent the user names (`--agent cmd` for cmd). When unspecified, resolve the configured/default agent and pass it explicitly; the helper defaults to `claude`. Inherit model/provider settings unless the user chooses otherwise.
- Inspect project instructions, tracker dependencies, dirty state, existing workers, and available usage/capacity before adding workers. Read only assigned agents' output. Do not repurpose unrelated tabs.

## Divide and brief

Choose independent, tracker-ready issues in priority order. Dependent work waits until its blocker is independently accepted. Bound fanout by available capacity and host/provider usage; do not launch a wave into known exhausted capacity or silently substitute models/providers. Assign disjoint files or modules; give shared builders, schemas, Git metadata mutations, and integration points one owner. Workers must know they share the checkout and must preserve others' edits.

Use [references/brief-template.md](references/brief-template.md) for each worker. Save durable briefs and results in an issue-specific work directory. Record the exact project path, role, ownership, exclusions, dependencies, baseline, checks, and handoff marker. A child receives none of the coordinator's context implicitly.

Choose checkout fidelity deliberately:

- A shared dirty checkout permits disjoint edits but requires a baseline and drift checks. Do not clean, reset, stash, or overwrite existing work.
- A worktree begins from a Git revision, excluding uncommitted inputs. Record its ref and required input provenance. Do not silently replace a requested current-checkout review with a clean-HEAD review.
- If a disposable snapshot is needed, record its input manifest and any omitted files. Any temporary Git commit belongs only to that disposable repository; it does not integrate the original checkout.

Default test briefs to local synthetic/offline checks and unique temporary outputs. This does not prohibit the chosen CLI agent's normal authorized model use. Separate live evaluation/provider calls, private data access, credential operations, external messages, installation, publication, deployment, and destructive cleanup need task authority. Use trash for approved disposal; avoid permanent scratch cleanup.

## Launch and verify

Keep a run registry with a run ID, issue, unique tab label, checkout, owner, brief/report paths, current IDs, and acceptance state. Enumerate workspaces, then tabs and panes in the selected workspace. Resolve exact unique labels to current opaque IDs before acting, especially after closures: IDs compact. On a missing or duplicate label, reconcile the mapping before sending input.

Prefer the base skill's helper with a durable absolute brief:

```bash
<herdr-skill>/scripts/herdr-task --agent cmd --workspace <current-workspace-id> \
  --label <unique-issue-label> --detach --file /absolute/path/brief.md
```

Use the requested agent in place of `cmd`. Do not use `--close-when-done`: completion still needs review. The helper's settle delay and second Enter do not prove successful startup. Read the assigned pane and confirm the intended agent loaded and began reading the brief. A prompt may be lost while a TUI starts.

For follow-up, send a short instruction pointing to saved feedback, then read the pane. If the text remains unsubmitted, send Enter in a later call and verify progress. Do not send blind repeated keys or duplicate a task already running. If startup, authentication, CLI availability, or dispatch fails, preserve diagnostics and stop that dispatch; resolve the specific cause without bypass modes or repeated launches.

## Monitor and approve

Use bounded waits or an authorized heartbeat monitor rather than tight polling. Monitor only owned labels; retain the issue/label/report mapping, role, permissions, acceptance state, and outstanding blockers in the monitor prompt. Stay quiet on unchanged progress and routine approvals. Notify on material findings, failure, completion, or required human action.

Inspect the actual permission dialog and proposed operation each time. Serialize approvals when agents share permission settings. A requested “option 2” applies only when its displayed grant fits the authorized scope, such as an inspected exact command. “Allow all edits this session” is broader than a review-only assignment: choose a single authorized report/support-file edit instead. Never infer option numbers from memory, grant generic host/provider permissions, or retry a rejected broad grant through another route. Verify execution resumed after approval.

Pause affected work on ownership overlap, unexplained source drift, unexpected private/live access, unclear destructive commands, or a scope-changing permission request. Save evidence and route corrections to the owner. Continue independent work that remains valid. A changed input invalidates only conclusions that depend on it; record the change rather than silently combining incompatible runs.

## Evaluate and integrate evidence

At handoff, read the result, actual scoped diff, command manifest, and logs. Independently rerun meaningful focused checks or spot-check concrete claims once; avoid repeated unchanged broad suites. Capture real exit codes before displaying filtered output. A green tail or agent `done` status is not acceptance.

Send concrete necessary corrections to the same worker, naming evidence and expected behavior. Keep issues open until their acceptance criteria are met; record partial acceptance and remaining blockers honestly. Separate synthetic fixtures from genuine recordings, simulated runs from live behavior, and deterministic passing tests from a reviewed golden set or calibrated grader.

After parallel work, assign a combined-checkout review when the requested outcome needs integration evidence. Preserve original generated reports by running mutating checks in a disposable copy. Verify imports, source/bundle consistency, relevant full checks, and artifacts as applicable. Distinguish actual-HEAD release readiness from a successful manifest-pinned disposable snapshot build. Offline checks do not prove live UI, host, model, or golden-set quality. Review-only workers report failures and continue independent checks; they do not patch source to make checks green.

## Finish

Save the observer review, accepted evidence, unresolved limits, and tracker updates within authority. Confirm the worker is idle/done, its reports are saved, and no correction is pending before closing its exact refreshed tab. Close only assigned tabs the human authorized you to close. Do not discard needed worktrees or archive the chat implicitly. Delete an owned monitor when all its work has been evaluated and no ongoing action remains; retained open issues may represent explicit future scope rather than active worker work.
