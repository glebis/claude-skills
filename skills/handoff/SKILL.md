---
name: handoff
description: 'Hand a written brief to an ACP agent that works in its own git worktree and herdr workspace, then check its work before anyone merges it. Writes a dated handoff doc, creates a beads epic when the repo has one, cuts a `handoff/<id>-<slug>` branch from the current branch, launches the agent through herdr''s `acp-run` (default `cmd acp`), and later verifies commits, stray changes and the brief''s checks. Use when the user says "hand this off", "create a handoff", "start it in its own worktree", "give this to an agent", "launch an agent on this epic", or wants an epic or multi-step to-do worked on away from a shared checkout. Requires git and a running herdr; beads is optional.'
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
scripts/handoff status ID                        # commits, dirty files, agent exit, log tail
scripts/handoff collect ID                       # verify and record the result on the epic
scripts/handoff close ID [--discard]             # remove the worktree once merged
scripts/handoff list
```

Run them from inside the target repository. State is kept in `<git-common-dir>/handoff/<id>/`
(`state.json`, `brief.md`, `run.log`), so nothing is added to the working tree.

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
   user wants to wait for it.
5. **Collect.** `handoff collect ID` checks that the agent finished, the branch has commits, the
   worktree is clean, nothing new changed in the source checkout, and each brief check passes.
   It records the result as a comment on the epic and exits non-zero on any failure.
6. **Merge is the user's call.** Report the verdict and the branch name, then stop.
7. **Close** after the merge: `handoff close ID` removes the worktree and workspace, deletes the
   merged branch and closes the epic. It refuses an unmerged branch unless `--discard`, which
   removes the worktree but always keeps the branch.

## What the agent is told

The doc is sent as the prompt with fixed rules appended: stay in the worktree, commit on the
handoff branch with explicit paths only, never merge, rebase, push or open a PR, don't touch
files outside the worktree, report blockers instead of working around them, and end with a short
report. `acp-run` enforces the path rule for permission requests and file reads and writes.

## Requirements and limits

- git, Python 3, a running herdr, and herdr's `acp-run` script. The script looks for `acp-run`
  on `PATH`, next to this skill in a sibling `herdr` skill, and in the usual skill folders; set
  `HANDOFF_ACP_RUN` to override.
- Only ACP agents. The script never falls back to a TUI agent.
- The worktree is cut from committed history. Uncommitted changes, including an uncommitted
  doc, aren't in it; the brief still reaches the agent because it is passed as a file.
- "Nothing changed outside the worktree" compares the source checkout's `git status` with a
  snapshot from start time. In a checkout shared with other sessions a change there may be
  theirs, so `collect` names the files instead of guessing.
