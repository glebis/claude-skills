---
name: agent-roundtable
description: Run a multi-agent audit of a feature, PR/diff, or task spec in which Codex, Command Code (cmd), Gemini, OpenCode and Claude debate over ACP for a configurable number of rounds and converge on a final spec, a prioritized task list and improvements. Claude moderates and synthesizes; every other agent gets a final veto. Use when the user says "roundtable", "agent roundtable", "audit this with codex", "have the agents discuss/debate this", "get a second (third) opinion from other agents", "multi-agent review", "council", or wants several coding agents to agree on a spec.
---

# Agent Roundtable

A moderated debate between coding agents that ends in one agreed spec. You (Claude, the orchestrating session) are the **moderator and synthesizer**, not a debater. The runner `scripts/roundtable.mjs` keeps one continuous conversation per debating agent, over one of two equal transports, and recovers an agent that dies or hangs.

| Transport | How a turn runs | Memory across rounds | Default for |
|---|---|---|---|
| **ACP** (Agent Client Protocol) | one live session per agent; one reader per turn | the ACP session | `cmd`, `claude`, `gemini`, `opencode` |
| **headless** | one CLI call per turn, prompt over stdin | native resume by explicit session id (`codex exec resume <id>`, `cmd --resume <id>`, `claude -p --resume <id>`) | `codex` (with `--sandbox read-only`) |

`cmd` and `claude` run headless with `--permission-mode plan`. `gemini` and `opencode` have no headless adapter, because their CLIs can't resume a session by id. The runner never resumes "the latest session".

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

Default agents: `codex,cmd`. Add `claude` when a third view helps: it is a separate Claude session with its own context, but the same model family as you, so it adds no model diversity. Add `opencode`/`gemini` only when they pass `doctor`.

## 3. Check the agents

```bash
node ~/.claude/skills/agent-roundtable/scripts/roundtable.mjs doctor
```

`doctor` starts every agent over its default transport and sends a one-line prompt, so expired keys and failed logins show up here, not in round 1. The other transport is only started. Drop agents whose default transport fails and whose other transport doesn't start, and tell the user which and why. Known traps: `gemini` ACP needs a working Google OAuth login (`gemini` interactively once); `opencode` connects but fails at the first prompt when its API key is expired. First install: `cd ~/.claude/skills/agent-roundtable/scripts && npm install`.

## 4. Run the debate (in the background)

```bash
node ~/.claude/skills/agent-roundtable/scripts/roundtable.mjs run \
  --brief RUN/brief.md --run-dir RUN --cwd TARGET_REPO \
  --agents codex,cmd --format panel --rounds 3 --mode auto
```

Use `RUN = <target repo>/docs/roundtable/<slug>-<YYYY-MM-DD>/` when the user wants a handoff doc, otherwise the scratchpad. `RUN` must be fresh: the runner refuses a directory that already has `state.json`, `moderator/` or `synthesis.md`. Start it with `run_in_background: true` and watch `RUN/state.json` with Monitor (an until-loop on its `status` field), never with bare sleeps.

Options: `--rounds` (default 3), `--min-rounds` (default 2), `--turn-timeout` seconds per agent turn (900), `--budget-min` wall clock for the debate (60), `--transport auto|acp|headless` (`auto` = each agent's default), `--roles a,b` for the roles format, `--no-veto`, `--drain-timeout` (30) and `--kill-grace` (5) seconds, `--registry` for another `agents.json`.

**Read-only is best effort.** Agents may read anything and run commands. The ACP permission rule decides by path, never by the tool's title:

- allowed: `read`, `search`, `fetch`, `think`, `execute` anywhere; `edit`/`delete`/`move`/`other` when every location is outside the target and the run dir (scratch files in `/tmp` are fine);
- denied: any change with a location inside the target or the run dir, `edit`/`delete`/`move` without locations, a missing or unknown kind, `switch_mode`.

Headless agents run under their CLI's own guard (codex `--sandbox read-only`, cmd and claude `--permission-mode plan`). After every round and after the veto the runner compares a content fingerprint of the target (tracked diff plus untracked files, run dir excluded; gitignored files are not covered) and adds a warning to `state.json` if it changed. Report any such warning to the user.

**Failed turns and degraded runs.** A turn fails when the agent crashes, hangs, times out, or stops with anything other than `end_turn`. On a timeout the runner cancels the turn and waits up to 30 s for it to stop; otherwise it kills the agent, so a late reply can't leak into the next turn. Each agent gets 3 failed attempts over the whole run:

1. restart on the same transport, with its context rebuilt from its completed `rounds/` replies, and re-run the turn;
2. switch to headless with native resume, bootstrapped the same way;
3. drop the agent.

A failed agent's vote is cleared at once. A switch or a drop makes the run **degraded**: `state.result` is `degraded`, `state.degraded` names who and what, and the consensus reason says so. Never present a degraded run as full consensus.

### Run directory

| File | Written by | Meaning |
|---|---|---|
| `state.json` | runner | `status`: starting, debating, awaiting_moderator, awaiting_synthesis, veto, done, failed; `waitingFor` names the file it wants and `waitingReason` why; `result`: consensus, no_consensus, degraded, failed; `agents.<id>`: `{ok, live, transport, lastError, failedTurns, nativeSessionId}`; `turns`: every attempt with transport, duration, outcome, `stopReason`; `degraded`, `deadlocks`, `warnings` |
| `rounds/rN-<agent>.md` | runner | each agent's reply; `.prompt.md` is what it was sent |
| `rounds/rN.summary.json` | runner | parsed status blocks and the consensus verdict |
| `moderator/rN.md` | **you** | note injected into the next round (each note is read once). First line `STOP` ends the debate |
| `synthesis.md` | **you** | your merged draft; triggers the veto round |

Write every file you hand to the runner atomically: write `moderator/rN.md.tmp` (or `synthesis.md.tmp`), then `mv` it to the final name. The runner reads only the final name.
| `veto/<agent>.md`, `veto.json` | runner | each agent's approve/object on the draft |
| `events.log` | runner | transport choices, tool calls, permission decisions, failures |

## 5. Moderate

When `status` is `awaiting_moderator` (active mode), read the round's replies and summary, then:

1. Show the user the **disagreements only** (finding id, who holds what, the evidence) through cenno and ask how to steer.
2. Write their direction plus your own procedural notes to `moderator/rN.md`. Moderate the process (which disagreements to settle, what evidence is missing), do not argue a side.

In auto mode the runner detects deadlock itself: when the same set of blocking ids holds two rounds running, it switches to `awaiting_moderator` (with `waitingReason: deadlock …`) even in auto mode. Read the two rounds, ask the user through cenno if it needs a human call, and write `moderator/rN.md`: which disagreement to settle and what evidence would settle it, or `STOP`. You may also drop a note in auto mode without being asked; it is picked up at the start of the next round.

## 6. Synthesize, then get the veto

When `status` is `awaiting_synthesis`, write `synthesis.md` using `references/output-template.md`. Rules that keep your bias in check:

- Every finding that any agent still holds as blocking appears in **Open disagreements**, with each agent's position in their own terms. Never resolve a disagreement by leaving it out.
- Attribute findings to the agent ids that raised them.
- Do not add findings of your own in the main lists; put them under "Moderator notes" so the agents can veto them.
- If the run is degraded, name the switched or dropped agents and say what that means for the result (a dropped agent did not vote on the final picture).

The runner sends the draft to every live agent, together with every agent's final-round status and a short summary of its last reply, so a veto is judged against where the debate actually ended. If `veto.json` has an objection, fix what it points to (or move it into Open disagreements), write a short note of what changed, and finalize. Do not run a second veto round unless the user asks.

## 7. Deliver

Ask (or, in result-only mode, use what the user said earlier) where the result goes:

- **Handoff document**: the final `synthesis.md` saved as `RUN/final.md` in the target repo, linked in your reply.
- **Chat**: the final spec, task list and open disagreements in the reply itself.

Always end with: agents and transports used (and any switch or drop), `state.result`, rounds run and why it stopped (`state.stopReason`), veto results, and any warnings.

## Configuration

- Agents live in `agents.json`: default `transport`, `acp` command, `headless.start`/`headless.resume` argv with `{out}`, `{cwd}`, `{session}`, `{promptFile}` placeholders, `input` (stdin or file) and `output` (codex-jsonl, json), optional `authMethod` (used only when `session/new` fails with the auth-required code and the agent advertises that method). Add an ACP agent by adding an entry.
- Tests: `cd scripts && npm test`. They drive the real ACP SDK against a fake agent (`scripts/test/fake-agent.mjs`) and a fake resumable CLI.
- The consensus rule is `scripts/consensus.mjs`, `assessConsensus(statuses, ctx)`.
- Prompt templates and the `roundtable-status` block format are in `scripts/prompts.mjs`.
