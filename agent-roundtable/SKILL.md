---
name: agent-roundtable
description: Run a multi-agent audit of a feature, PR/diff, or task spec in which Codex, Command Code (cmd), Gemini, OpenCode and Claude debate over ACP for a configurable number of rounds and converge on a final spec, a prioritized task list and improvements. Claude moderates and synthesizes; every other agent gets a final veto. Use when the user says "roundtable", "agent roundtable", "audit this with codex", "have the agents discuss/debate this", "get a second (third) opinion from other agents", "multi-agent review", "council", or wants several coding agents to agree on a spec.
---

# Agent Roundtable

A moderated debate between coding agents that ends in one agreed spec. You (Claude, the orchestrating session) are the **moderator and synthesizer**, not a debater. The runner `scripts/roundtable.mjs` talks to the debating agents over ACP (Agent Client Protocol), keeps one live session per agent across rounds, and falls back to each agent's headless CLI when ACP fails.

## 0. First question: how involved does the user want to be?

Before anything else, ask through cenno (`mcp__cenno__ask_user`, choice):

- **Hands-on**: they review the disagreements after every round and steer. Run with `--mode active`.
- **Result only**: they get the final spec and are only asked if the agents deadlock or the budget runs out. Run with `--mode auto`.

The answer decides what you ask next. For **result only**, ask nothing else that has a sensible default: pick format, agents, rounds and output yourself and state the choices in one line. For **hands-on**, confirm the format and agents in one `mcp__cenno__ask_sequence`.

## 1. Detect the target and write the brief

| Input | How to recognize it | What the brief contains |
|---|---|---|
| Feature in a repo | paths, a module or feature name | entry points, key files, how to run its tests |
| PR / diff / branch | PR number or URL, branch name, "my changes" | `git diff base...head --stat`, the base ref, the PR description |
| Task / spec | a doc, ticket or pasted text, no code yet | the spec text, constraints, what "done" means |

Write `brief.md` in the run directory with: **Target**, **Type**, **Goal of the audit**, **Scope** (in and out), **How to verify** (test commands), and **Known context** the agents cannot discover (business constraints, user intent). Keep it under ~150 lines and point to files instead of pasting them; the agents can read the repo.

## 2. Pick the format (suggest, the user can override)

Read `references/formats.md`. Short version:

- **pingpong**: 2 agents taking turns. Narrow diffs, one focused question.
- **panel**: N agents audit in parallel, then cross-critique. Broad features, default.
- **roles**: like panel, but each agent gets a lens (auditor, devil's advocate, architect, QA). Specs and designs where the premise itself is in doubt.

Default agents: `codex,cmd`. Add `claude` (a separate Claude via ACP, so model diversity stays the same but you keep a neutral seat) or `opencode`/`gemini` when they pass `doctor`.

## 3. Check the agents

```bash
node ~/.claude/skills/agent-roundtable/scripts/roundtable.mjs doctor
```

Drop agents whose ACP **and** headless both fail, and tell the user which and why. Known traps: `gemini` ACP needs a working Google OAuth login (`gemini` interactively once); `opencode` connects but fails at the first prompt when its API key is expired. First install: `cd ~/.claude/skills/agent-roundtable/scripts && npm install`.

## 4. Run the debate (in the background)

```bash
node ~/.claude/skills/agent-roundtable/scripts/roundtable.mjs run \
  --brief RUN/brief.md --run-dir RUN --cwd TARGET_REPO \
  --agents codex,cmd --format panel --rounds 3 --mode auto
```

Use `RUN = <target repo>/docs/roundtable/<slug>-<YYYY-MM-DD>/` when the user wants a handoff doc, otherwise the scratchpad. Start it with `run_in_background: true` and watch `RUN/state.json` with Monitor (an until-loop on its `status` field), never with bare sleeps.

Options: `--rounds` (default 3), `--min-rounds` (default 2), `--turn-timeout` seconds per agent turn (900), `--budget-min` wall clock for the debate (60), `--transport auto|acp|headless`, `--roles a,b` for the roles format, `--no-veto`.

Agents may read files and run tests and commands. ACP permission requests for `edit`/`delete`/`move` are rejected automatically; the runner also compares `git status` before and after each round and records a warning in `state.json` if the tree changed. Report any such warning to the user.

### Run directory

| File | Written by | Meaning |
|---|---|---|
| `state.json` | runner | `status`: starting, debating, awaiting_moderator, awaiting_synthesis, veto, done, failed; `waitingFor` names the file it wants |
| `rounds/rN-<agent>.md` | runner | each agent's reply; `.prompt.md` is what it was sent |
| `rounds/rN.summary.json` | runner | parsed status blocks and the consensus verdict |
| `moderator/rN.md` | **you** | note injected into round N+1. First line `STOP` ends the debate |
| `synthesis.md` | **you** | your merged draft; triggers the veto round |
| `veto/<agent>.md`, `veto.json` | runner | each agent's approve/object on the draft |
| `events.log` | runner | transport choices, tool calls, permission decisions, failures |

## 5. Moderate

When `status` is `awaiting_moderator` (active mode), read the round's replies and summary, then:

1. Show the user the **disagreements only** (finding id, who holds what, the evidence) through cenno and ask how to steer.
2. Write their direction plus your own procedural notes to `moderator/rN.md`. Moderate the process (which disagreements to settle, what evidence is missing), do not argue a side.

In auto mode, write `moderator/rN.md` only when you see a deadlock (the same blocking ids two rounds in a row); if it needs a human call, ask through cenno first.

## 6. Synthesize, then get the veto

When `status` is `awaiting_synthesis`, write `synthesis.md` using `references/output-template.md`. Rules that keep your bias in check:

- Every finding that any agent still holds as blocking appears in **Open disagreements**, with each agent's position in their own terms. Never resolve a disagreement by leaving it out.
- Attribute findings to the agent ids that raised them.
- Do not add findings of your own in the main lists; put them under "Moderator notes" so the agents can veto them.

The runner sends the draft to every agent. If `veto.json` has an objection, fix what it points to (or move it into Open disagreements), write a short note of what changed, and finalize. Do not run a second veto round unless the user asks.

## 7. Deliver

Ask (or, in result-only mode, use what the user said earlier) where the result goes:

- **Handoff document**: the final `synthesis.md` saved as `RUN/final.md` in the target repo, linked in your reply.
- **Chat**: the final spec, task list and open disagreements in the reply itself.

Always end with: agents and transports used, rounds run and why it stopped (`state.stopReason`), veto results, and any warnings.

## Configuration

- Agents live in `agents.json` (ACP command, headless fallback, optional `authMethod`). Add an ACP agent by adding an entry.
- The consensus rule is `scripts/consensus.mjs`, `assessConsensus(statuses, ctx)`.
- Prompt templates and the `roundtable-status` block format are in `scripts/prompts.mjs`.
