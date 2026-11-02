# <Target> — roundtable result

Date · Agents (transport) · Format · Rounds run · Stop reason · Full/degraded outcome

## Summary
Three to five sentences: what was audited, the overall verdict, the biggest risk. Name restarted, switched or dropped participants. Degraded convergence is never full consensus.

## Final specification
What the feature/change should be after the fixes. Behaviour, interfaces, constraints, acceptance criteria. Write it so someone who did not read the debate can build or verify it.

## Tasks
Ordered by priority. One line each, with the finding ids it closes and how to verify.

| # | Priority | Task | Closes | Verify with |
|---|---|---|---|---|
| 1 | blocker | ... | CODEX-2, CMD-1 | `pytest tests/test_x.py` |

## Improvements
Non-blocking improvements the agents agreed are worth doing, with ids.

## Open disagreements
For each: the question, each agent's position and evidence, and what would settle it. Retain dropped participants’ last unresolved objections and label them as last known positions; exclusion from the voting set does not resolve them. Empty only if no agent still holds a blocking objection.

## Refuted or dropped findings
Findings withdrawn during the debate and why, one line each, so nobody raises them again.

## Moderator notes
Your own observations, clearly marked as yours. Subject to the agents' veto.

## Veto
Each agent: approve / objection, and what changed in response.

## Run evidence and limitations
Transports used and recovery stages/failures; surviving and dropped participants; edit-detection coverage and exclusions (Gitignored content is excluded), scan errors and warnings. Separate passing fake-agent acceptance tests from live transport checks; mark untested live native-resume behavior unverified.
