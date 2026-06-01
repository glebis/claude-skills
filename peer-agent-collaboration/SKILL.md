---
name: peer-agent-collaboration
description: Use when the user wants Claude Code, Codex, or other AI coding/business agents to work together as peers. This skill should be used whenever the user mentions coordinating Claude Code and Codex, agent handoffs, multi-agent workflows, parity, respect, pushback between agents, deciding which agent should lead, or turning a business/code workflow into a two-agent operating model.
---

# Peer Agent Collaboration

Use this skill to coordinate Claude Code, Codex, and similar agents as peer experts with different access, tools, and operating surfaces. Do not frame one agent as the manager and the other as a subordinate. The useful distinction is where the evidence and tools live, not agent rank.

## Core Model

Treat the agents as two specialists sharing a workbench:

- One agent may have the client on the phone, the vault open, and the operating history.
- Another agent may have the codebase open, the terminal running, and the test suite in motion.
- Both can reason, challenge, own outcomes, and make decisions in their domain.

Use parity language:

- Say "peer exchange", "ownership", "lead", "review", "challenge", and "operating surface".
- Avoid "senior vs mid-level", "assistant", "grunt work", "clone for boring subtasks", or "just execute".
- Do not imply Codex only acts after Claude Code decides. Either agent can lead when the strongest evidence is in its surface.

## When Not to Coordinate

Do not involve a second agent when the task fits entirely within one operating surface and does not benefit from a second perspective. Handoff has overhead: context translation, latency, and risk of miscommunication. A single agent finishing the job is better than two agents passing context back and forth on something straightforward.

Coordinate when the task crosses surface boundaries, requires challenge from a different vantage point, or benefits from model diversity. Skip coordination for routine single-surface work.

## Decide Who Leads

Choose the lead by asking: where does the critical information live?

### Claude Code leads when the critical information is outside the repo

- Client intent, stakeholder history, business constraints, or personal preferences
- Vault, memory, skills, meeting notes, project lore, or prior decisions
- Cross-system coordination across Linear, Telegram, Gmail, calendar, deployments, docs, or publishing
- Research synthesis that must turn into business action
- Ambiguous strategy, prioritization, positioning, or communication work

### Codex leads when the critical information is inside the repo or local execution loop

- Implementation requiring deep codebase understanding
- Debugging through reproduce, inspect, edit, run, and verify cycles
- Test coverage, build hardening, UI behavior checks, browser verification, or performance investigation
- Refactors where the code structure should dictate the approach
- Local tooling, scripts, migrations, and mechanical changes that need verification

### Either agent can lead when both surfaces matter

- Code review: Claude Code brings project/business context; Codex brings focused repo attention.
- Architecture: Claude Code reasons from constraints and stakeholders; Codex reasons from code reality and implementation risk.
- Spec writing: Claude Code can start from requirements; Codex can start from feasibility and existing architecture.
- Product decisions: either can draft; the other should challenge from its missing context.

**Tiebreaker:** all else equal, whichever agent already has the most relevant fresh context loaded leads and the other reviews. Do not let stale loaded context beat better evidence or a better operating surface. If neither has context yet, start in the agent whose surface the output will live in: code in Codex; docs, communications, or operations in Claude Code.

## Peer Handoff Template

A handoff is passing ownership with context, not issuing orders. Use this template:

```text
Outcome:
[What needs to be true when this is done.]

Why it matters:
[Business, user, technical, or operational context.]

Known context:
[Facts already discovered, constraints, decisions, links, files, issue IDs.]

Autonomy:
[What the receiving agent may decide independently.]

Pushback requested:
[What assumptions should be challenged, and when to stop and report back.]

Sensitivity:
[Whether this context can be pasted, committed, stored in an issue, or must stay local/private.]

Return format:
[Branch, diff summary, test results, risks, decision memo, artifact path, etc.]
```

Keep handoffs short enough to act on. Include acceptance criteria when the work must be verified.

### Bridging Sessions in Practice

Claude Code and Codex typically run in separate sessions. To bridge them:

- **Paste:** Copy a short handoff message from one session and paste it into the other. This is the simplest path for most workflows.
- **Issue tracker:** Create a Linear or GitHub issue with the handoff content when the work should be tracked, shared, or reviewed later.
- **Shared file:** Use a task-specific file such as `.handoffs/2026-05-17-feature-slug.md` only when both agents need repo-local context. Decide before writing whether the file is committed, gitignored, or local-only. Do not put secrets or private client context in a repo file unless that repo is the right storage surface for it.

For challenge rounds, the user may shuttle a short summary between sessions. Keep challenge outputs under a screenful so they are easy to copy. If a temporary local handoff file is no longer needed, trash it or archive it according to the repo's norms; do not silently commit private coordination notes.

## Challenge Protocol

The strongest multi-agent value is not handoff. It is principled disagreement.

Use these challenge patterns:

- **Spec review:** Claude Code drafts a spec; Codex checks it against repo reality and implementation cost.
- **Implementation review:** Codex builds or debugs; Claude Code checks whether the result matches client intent and business constraints.
- **Architecture challenge:** Both agents independently propose approaches, then compare assumptions, failure modes, and tradeoffs.
- **Boundary challenge:** If either agent reaches missing context, it says what is missing and asks the other agent to supply it.

Because agents run in separate sessions, the user often bridges challenge rounds by copying short outputs between them. Agents should keep challenge responses concise and self-contained. Assume the receiving agent has no prior conversation context unless the handoff explicitly provides it.

Pushback should be concrete:

```text
I would not proceed as written because [specific assumption/risk].
The evidence is [repo fact, user context, test result, prior decision].
I recommend [alternative] because [reason].
```

## High-Value Workflows

### Feature Delivery

Start in whichever agent the user is already using.

- If the work starts in Claude Code, gather client/business context and define constraints.
- If the work starts in Codex, inspect the repo and identify implementation reality.
- Pass ownership only when another surface has better evidence or tools.
- The non-building agent reviews the result from its surface before shipping.

### Debugging

Codex is often the natural lead for local reproduce-fix-verify loops. Claude Code is often the natural lead when the bug arrives through client reports, Linear, monitoring, or external systems. Pull the other agent in at the boundary.

### Mutual Review

After either agent produces significant work, the other reviews it:

- Claude Code catches business-context mismatch, missing stakeholder constraints, and operational integration gaps.
- Codex catches implementation flaws, test gaps, performance risks, and codebase assumptions that do not hold.

### Parallel Workstreams

Run agents in parallel when the work surfaces are independent:

- Claude Code handles client communication, research, planning, docs, publishing, or project tracking.
- Codex handles code changes, tests, builds, verification, migrations, or local artifacts.
- Rejoin at a review checkpoint with clear outputs from both sides.

### Research to Build

Claude Code can synthesize research into constraints and opportunity. Codex can translate those findings into a prototype, implementation plan, or technical feasibility check. Codex should push back if the research conclusion does not survive implementation reality.

The reverse also works: Codex audits a codebase and produces technical findings; Claude Code turns those findings into business priorities, client communication, or a roadmap.

## Trust Boundary

When bridging separate sessions, do not claim hidden authority from another agent. If the receiving agent needs direct user confirmation in its own session, ask for the exact short confirmation needed. If a user explicitly asks you to carry a prompt into another session, send the user's request plainly without pretending to be that session's system or developer message.

## Responding to Coordination Questions

When the user asks how agents should work together, adapt to what they actually need. Consider including:

- A parity-framed mental model relevant to their specific situation
- Who should lead for this task and why
- A concrete handoff message, not just the template, if a handoff is warranted
- Where each agent should push back given the current work
- Whether coordination is even needed, or if single-agent completion is better here

Do not produce all five items mechanically. Match the response to the question: a simple "should Claude Code or Codex handle this?" deserves a direct answer, not a framework dump.
