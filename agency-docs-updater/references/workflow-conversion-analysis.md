# Should `agency-docs-updater` become a dynamic Workflow?

**Recommendation: No — keep it a Skill.** This pipeline is close to the textbook
anti-fit for a [dynamic workflow](https://code.claude.com/docs/en/workflows.md). The
parts of the workflow feature that justify its cost (massive subagent fan-out, context
offloading, a rerunnable orchestration with adversarial verification) don't apply here,
while the parts that hurt (no mid-run sign-off, multi-agent token overhead, resume only
within one session, research-preview status) hit exactly the places this pipeline is
fragile.

This doc records the reasoning so the question doesn't get re-litigated.

---

## What a Workflow actually is (Opus 4.8, research preview)

Per the [official docs](https://code.claude.com/docs/en/workflows.md), a dynamic workflow
is **a JavaScript script Claude writes that orchestrates subagents at scale**. The runtime
executes it in the background; intermediate results live in script variables instead of
Claude's context window. Triggered by the word `workflow` in a prompt, by `/effort
ultracode`, or by running a saved/bundled command like `/deep-research`. Saved to
`.claude/workflows/` (project) or `~/.claude/workflows/` (personal).

The doc's own "when to use" guidance — *who holds the plan*:

| | Subagents | Skills | Workflows |
|---|---|---|---|
| What it is | A worker Claude spawns | Instructions Claude follows | A script the runtime executes |
| Who decides next | Claude, turn by turn | Claude, following the prompt | The script |
| Intermediate results | Claude's context | Claude's context | Script variables |
| What's repeatable | The worker definition | The instructions | The orchestration itself |
| Scale | A few per turn | Same | **Dozens to hundreds of agents per run** |
| Interruption | Restarts the turn | Restarts the turn | Resumable in the same session |

> "Reach for a workflow when a task needs more agents than one conversation can
> coordinate, or when you want the orchestration codified as a script you can read and
> rerun." Canonical examples: a codebase-wide bug sweep, a 500-file migration,
> cross-checked research, drafting a hard plan from several independent angles.

The value is **fan-out + a repeatable quality pattern** (independent agents adversarially
reviewing each other), not "running steps in order."

---

## Why this pipeline is a poor fit

`agency-docs-updater` is a **linear, single-subject publishing pipeline**: 8 sequential
steps, one lab meeting at a time, run ~weekly. Match it against what workflows are for:

| Workflow earns its cost via… | …does `agency-docs-updater` have it? |
|---|---|
| Dozens–hundreds of parallel agents | **No.** One subject per run; at most a 2-way split (Step 3 upload ∥ Step 4 summary). |
| Context-window pressure to offload | **No.** Intermediate state is a handful of paths/IDs (`VIDEO_ID`, `MEETING_NUMBER`, URLs) — tiny. |
| Adversarial cross-checking across many passes | **Marginal.** Only Step 4's fact-check, which a single `claude-code-guide` subagent already covers. |
| Orchestration worth codifying as a rerunnable script | **Already true.** The plan is already scripted — SKILL.md plus `update_meeting_doc.py`, `process_video.py`, `zoom_meetings.py`. |

So the upside column is mostly empty. Now the downsides, which land on this pipeline's
known-fragile spots (see `learnings.md`):

1. **No mid-run user input.** The docs are explicit: *"Only agent permission prompts can
   pause a run. For sign-off between stages, run each stage as its own workflow."* This
   pipeline publishes to **public YouTube and a public Vercel site** and has documented
   failure modes that need a human/operator's judgment to recover:
   - videos that upload "successfully" then get silently deleted by YouTube (Step 3a exists
     precisely for this),
   - MDX that breaks the Vercel build (`<!-- -->`, bare `<`, `{`),
   - ambiguous meeting-number detection (`-n NN` override),
   - Vercel deploy failures (Step 7).
   A skill lets the operator step in with judgment at any of these. A workflow can't pause
   for sign-off — it can only block on a permission prompt.

2. **Multi-agent token cost for no parallelism benefit.** Workflows pay for scale. With
   ~no fan-out here, you'd take the orchestration overhead of spawned agents and get none
   of the speedup that pays for it.

3. **Resume is single-session only.** *"If you exit Claude Code while a workflow is
   running, the next session starts the workflow fresh."* This pipeline has long unattended
   waits — Zoom processing (~15 min), YouTube upload/processing (10–30 min), Vercel deploy.
   The skill already survives these across sessions via **idempotent step-skipping**
   (`--resume-from upload`, "skip if MP4 > 1MB exists", placeholder-MDX detection). A
   workflow would lose that cross-session resilience.

4. **The script can't touch the filesystem/shell directly** — *"Agents read, write, and
   run commands. The script coordinates the agents."* Every bash/python call would route
   through a spawned agent, adding indirection over today's direct execution.

5. **Research preview.** Pinning a production publishing pipeline to a preview feature
   (v2.1.154+, behavior may change) is avoidable risk for no offsetting gain.

### Automation-advisor lens

Scoring with the repo's own `automation-advisor` matrix — Frequency ~weekly (3), Time
30–120+ min manual (4), Error cost annoying→high / public artifacts (3), Longevity years
(5) → well above the "automate now" threshold. **It already is automated** — as a skill.
The matrix says *automate*; it does **not** say *use the workflow primitive*. The override
checks (high external-dependency variability + high error cost → keep a validation layer /
human-in-loop) actively argue **against** the unattended, no-sign-off shape of a workflow.

---

## Where Workflows *would* pay off in this domain

The single-meeting pipeline is the wrong target, but adjacent **fan-out** jobs are exactly
what workflows are built for, and the skill doesn't cover them today:

- **Backfill / bulk repair** — re-publish or fix every past lab meeting in one run (one
  agent per meeting). Classic fan-out.
- **Repo-wide MDX audit** — check every meeting MDX across all labs for broken YouTube
  embeds, dead links, and MDX-compile hazards, with findings cross-checked. This is
  literally the docs' "codebase-wide bug sweep" example.
- **Bulk thumbnail regeneration** — re-render branded thumbnails across all past meetings.

These earn the multi-agent cost; the weekly single-meeting publish does not.

---

## Bottom line

| | Convert to Workflow | Keep as Skill (recommended) |
|---|---|---|
| Parallelism payoff | None — sequential pipeline | n/a |
| Token cost | Higher (multi-agent overhead) | Lower |
| Human sign-off at fragile steps | **Lost** (no mid-run input) | Preserved |
| Cross-session resilience | Lost (resume = same session) | Preserved (idempotent skips) |
| Maturity | Research preview | Stable |
| Effort to migrate | Non-trivial rewrite | Zero |

Keep `agency-docs-updater` as a Skill. If we want to use the workflow feature in this area,
build a **separate** workflow for the batch/audit jobs above — don't reshape the
publish-one-meeting pipeline into one.

---

*Sources: [Orchestrate subagents at scale with dynamic
workflows](https://code.claude.com/docs/en/workflows.md) ·
[Skills](https://code.claude.com/docs/en/skills.md) ·
[Subagents](https://code.claude.com/docs/en/sub-agents.md) · this skill's `SKILL.md` and
`references/learnings.md`.*
