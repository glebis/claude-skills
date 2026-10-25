# Choosing a format

Pick by the shape of the question, not by habit. State the choice and the reason in one line.

| Signal | Format | Agents | Rounds |
|---|---|---|---|
| Diff under ~300 lines, one module, "is this right?" | pingpong | 2 | 3–4 (each round is one turn) |
| Feature spanning several modules, or "what's wrong with X?" | panel | 2–3 | 3 |
| Spec or design before code; scope or premise unclear | roles | 3–4 | 3 |
| Security- or data-loss-sensitive change | panel + `qa` role agent | 3 | 3, `--min-rounds 3` |
| User wants it fast and cheap | pingpong | codex + cmd | 2 |

## How each format runs

**pingpong**: round 1, agent A audits alone. Round 2, agent B gets the brief and A's audit, audits and critiques. Then they alternate, each answering the other's latest reply. Cheapest; good when one agent's blind spots are the main risk.

**panel**: round 1, every agent audits in parallel without seeing the others. From round 2, every agent sees every other agent's latest reply (snapshotted before the round starts) and critiques. Independent first takes avoid anchoring.

**roles**: panel, plus a lens per agent from `--roles` (default order: auditor, devils-advocate, architect, qa). Use when the risk is "we built the wrong thing", which plain audits rarely catch.

## Choosing agents

- Model diversity beats agent count: codex + cmd + claude is three different stacks; two Claude-based agents add little.
- `claude` as a participant is a separate ACP session, not you. Add it when you want a Claude perspective in the debate while you stay neutral.
- Each extra agent multiplies cost and time by about the round count. Three is usually the ceiling worth paying for.
