# X/Twitter Launch Monitor: SDK v2 Beta

**Window:** Last 24 hours
**Scope:** `@exampledev`, "SDK v2", "exampledev beta", "migration guide", excluding hiring and giveaway terms
**Hermes Tweet status:** Available for read-only sweeps

## Query Pack

| Family | Query | Purpose |
|---|---|---|
| Owned | `from:exampledev "SDK v2"` | Find launch replies and quote posts |
| Problem | `"SDK v2" "migration guide"` | Catch setup friction and missing docs |
| Intent | `"alternative to ExampleDev" OR "trying ExampleDev"` | Find evaluation and switching signals |
| Community | `"ExampleDev" "open source"` | Find maintainer and ecosystem reactions |
| Noise filters | `-"giveaway" -"airdrop" -"job"` | Remove unrelated campaign traffic |

## Signal Triage

| Type | Link | Why it matters | Recommended owner | Next step |
|---|---|---|---|---|
| Question | post-1001 | User asks whether v1 config still works | DevRel | Reply with migration guide section after verifying link |
| Bug report | post-1002 | Reports CLI install failure on Windows | SDK engineering | Reproduce before public reply |
| Praise | post-1003 | Maintainer highlights faster setup | DevRel | Thank publicly if action gates are enabled |
| Competitive comparison | post-1004 | Evaluator compares docs against another SDK | Product marketing | Add to positioning notes |

## Response Queue

| Priority | Link | Suggested response posture | Draft needed? |
|---|---|---|---|
| High | post-1002 | Acknowledge, ask for version details, route to issue tracker | Yes |
| Medium | post-1001 | Answer with verified docs link | Yes |
| Low | post-1003 | Short thanks, no pitch | Optional |

## Risks & Gaps

- Windows install report needs reproduction before any public claim.
- The migration guide link should be checked before drafting replies.
- No security or privacy issues surfaced in this sweep.
