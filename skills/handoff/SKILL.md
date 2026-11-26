---
name: handoff
description: 'Hand a written brief to an ACP agent that works in its own git worktree as its own process, then check its work before anyone merges it. Writes a dated handoff doc, creates a beads epic when the repo has one, cuts a `handoff/<id>-<slug>` branch from the current branch, launches the agent detached through herdr''s `acp-run` script (default `cmd acp`), shows it in a herdr pane when herdr is running, can resume an agent that stopped, and later verifies commits, stray changes and the brief''s checks. Use when the user says "hand this off", "create a handoff", "start it in its own worktree", "give this to an agent", "launch an agent on this epic", or wants an epic or multi-step to-do worked on away from a shared checkout. Requires git, node and the `acp-run` script; herdr and beads are optional.'
---

# Handoff

A handoff is a dated doc plus, when the repo uses beads, an epic. The doc is the brief. A
session or agent starts only when the user says to start it. `scripts/handoff` does every
mechanical step; the agent's job is to write a good doc and report what the script prints.

## Commands

```bash
scripts/handoff new "Report importer"            # docs/YYYY-MM-DD-report-importer-handoff.md
scripts/handoff start DOC                        # epic + worktree + launch, detached
scripts/handoff start DOC --supervise            # wait for the agent, then collect
scripts/handoff start DOC --here                 # worktree, branch, brief and epic; no agent
scripts/handoff start DOC --agent "codex-acp"    # any ACP agent command
scripts/handoff start DOC --no-herdr             # no herdr watch pane even when herdr runs
scripts/handoff status ID                        # commits, dirty files, agent running/finished/stopped, log tail
scripts/handoff resume ID                        # relaunch a stopped agent in its worktree
scripts/handoff resume ID --force --note FILE     # send review findings back to a finished agent
scripts/handoff stop ID                          # stop a running agent; the worktree stays
scripts/handoff collect ID                       # verify and record the result on the epic
scripts/handoff collect ID --retry-failed        # rerun a failed check once; a pass is FLAKY
scripts/handoff close ID [--discard]             # remove the worktree once merged
scripts/handoff prune [--dry-run]                # remove every merged, stopped, clean handoff
scripts/handoff list
```

Run them from inside the target repository. State is kept in `<git-common-dir>/handoff/<id>/`
(`state.json`, `brief.md`, `run.log`, then `run2.log`… per resume), so nothing is added to the
working tree. Worktrees go to `~/.handoff/worktrees/<repo>/` (override with `HANDOFF_WORKTREES`).

## Herdr first, detached only after failure

For both `start` and `resume`, prefer Herdr supervision. If its socket does not answer, try
starting `herdr server` and wait up to thirty seconds for readiness. Open the handoff worktree and
its log watcher before launching the agent. Only fall back to detached-only mode after startup
or pane creation fails; report the actual failure and startup-log path. A failed first socket
probe alone is not a reason to give up. `--no-herdr` is an explicit user opt-out.

The ACP agent still owns a durable background process: the pane watches its log, and closing
the pane does not kill the job. This process ownership is separate from the Herdr-first UI
policy. Do not rerun an already-finished agent just to attach a watcher. `--here` creates only
the worktree/state and must not start Herdr or an agent. `close` removes the watcher workspace.

## Workflow

1. **Write the doc.** Use `handoff new "<title>"` or the project's own convention: look at existing
   handoff or spec docs first and match their folder and naming. Fill in problem, scope, what is
   out of scope and "done when". Put verification commands in a fenced block under a heading
   named `Checks` (or `Verify`): `collect` runs each line in the worktree.
2. **Stop and wait** until the user says to start it. Writing the doc is not consent to launch.
3. **Start.** `handoff start DOC` prints the base branch and commit it cuts from; relay that
   line, and any note that the source checkout has uncommitted changes the worktree won't have.
   Without `bd` or a `.beads/` folder the epic is skipped with a one-line note.
4. **Check in** with `handoff status ID`. Don't poll in a loop; use `--supervise` when the
   user wants to wait for it. If status says the agent stopped without finishing, run
   `handoff resume ID`: it relaunches the agent in the same worktree with a note to continue
   from what is already there.
5. **Collect.** `handoff collect ID` checks that the agent finished, the branch has commits, the
   worktree is clean, nothing new changed in the source checkout, and each brief check passes.
   It records the result as a comment on the epic and exits non-zero on any failure. Each check's
   full output is saved as `collect-N-check-K.log` in the handoff's state folder; a failure prints
   that path and its `FAILED` lines. A change in the source checkout fails only when it touches a
   file the handoff branch also changes and the checkout is still on the same branch; anything
   else is a WARN (another session's work, or the
   checkout moved to another branch, which is named). Files already dirty at start are compared
   by content, so a second edit still shows. `--retry-failed` reruns a failed check once: passing
   then is FLAKY, the verdict reads "PASS (with warnings)", and the first failure's log is kept so
   an issue can quote it.
6. **Merge is the user's call.** Report the verdict and the branch name, then stop.
7. **Close** after the merge: `handoff close ID` removes the worktree and workspace, deletes the
   merged branch and closes the epic. It refuses an unmerged branch unless `--discard`, which
   removes the worktree but always keeps the branch.
8. **Merged handoffs clean themselves up.** `new`, `start`, `status`, `collect` and `list` first
   remove every handoff whose branch is merged, whose agent has stopped and whose worktree has no
   uncommitted changes. "Merged" means contained in the branch it was cut from or, for a review-fix
   round cut from another handoff, in that handoff's base, or in the remote's default branch
   (`origin/HEAD`) when the base was itself merged onward. Anything else is left alone. Run
   `handoff prune --dry-run` to see what would go; `HANDOFF_NO_PRUNE=1` turns it off. A repo's
   post-merge hook can call `handoff prune --quiet` so the cleanup also happens right after a merge.

## What the agent is told

The doc is sent as the prompt with fixed rules appended: stay in the worktree, commit on the
handoff branch with explicit paths only, never merge, rebase, push or open a PR, don't touch
files outside the worktree, report blockers instead of working around them, and end with a short
report. `acp-run` enforces the path rule for permission requests and file reads and writes.

## Requirements and limits

- git, Python 3, node, and herdr's `acp-run` script (a standalone node ACP client; herdr itself
  need not run). The script looks for `acp-run`
  on `PATH`, next to this skill in a sibling `herdr` skill, and in the usual skill folders; set
  `HANDOFF_ACP_RUN` to override.
- Only ACP agents. The script never falls back to a TUI agent. Honor the requested agent and model: when Pi is requested, use a verified Pi ACP adapter with the model pinned. Never silently substitute CMD or another model/provider.
- The worktree is cut from committed history. Uncommitted changes, including an uncommitted
  doc, aren't in it; the brief still reaches the agent because it is passed as a file.
- "Nothing changed outside the worktree" compares the source checkout's `git status` with a
  snapshot from start time. In a checkout shared with other sessions a change there may be
  theirs, so `collect` names the files instead of guessing.
