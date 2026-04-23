# Superpowers Handoff — jtbd.json → brainstorm → plan → code

How the JTBD output feeds into the superpowers pipeline.

## The contract

`jtbd.json` is the handoff artifact. When a brainstorming session starts and a `jtbd.json` exists in the project root or `~/jtbd/<slug>/`, the brainstorming skill should:

1. **Read it first** — before asking any clarifying questions.
2. **Skip questions the JSON already answers:**
   - "What is this?" → `hook`
   - "Who is it for?" → `jtbd.situation` (actor + trigger)
   - "What's the problem?" → `problem.what_hurts`
   - "What does success look like?" → `jtbd.outcome`
   - "What are the constraints?" → `guardrails[]`
3. **Use Switch forces for approach selection** — the forces tell you which tradeoffs matter:
   - Strong Push + weak Pull → positioning problem (the approach should address "why switch?")
   - Strong Habit → needs migration path, not greenfield
   - Strong Anxiety → needs reversibility, trial mode, guarantees
4. **Surface open_questions[]** — these are the things the JTBD interview couldn't resolve. Ask them during brainstorming.
5. **Include ODI outcomes if present** — `odi.outcomes[]` with opportunity scores directly inform what to build first.

## What brainstorming still needs to do

The JTBD interview captures the *what* and *why*. Brainstorming still owns:
- **How** — architecture, components, data flow
- **Approach selection** — 2-3 options with tradeoffs
- **Technical constraints** — framework, language, infra
- **Scope** — MVP vs. full, what to cut
- **Design doc** — the written spec that goes to writing-plans

## Invocation patterns

### Pattern 1: Explicit handoff
```
User: "brainstorm my jtbd-skill project"
Claude: reads ~/jtbd/jtbd-skill/jtbd.json, presents the job summary, asks:
  "I see you've already done a JTBD interview for this. Here's what I'm working with:
   [hook]. The main pain is [what_hurts]. Want me to use this as the starting point,
   or do you want to revisit any of it?"
```

### Pattern 2: Path argument
```
User: "brainstorm from ~/jtbd/jtbd-skill/jtbd.json"
Claude: reads JSON, skips Pass 1 questions, goes straight to approach exploration.
```

### Pattern 3: In-project discovery
```
User: "brainstorm adding voice support"
Claude: during "explore project context" step, finds ./jtbd.json in project root.
  Uses it as context without being told to.
```

## Field mapping to brainstorming questions

| Brainstorming question | jtbd.json field | Skip if present? |
|---|---|---|
| What are you building? | `hook` | Yes |
| Who is it for? | `jtbd.situation` | Yes |
| What problem does it solve? | `problem.what_hurts` | Yes |
| What does success look like? | `jtbd.outcome` | Yes |
| What should it NOT do? | `guardrails[]` | Yes |
| What are they using today? | `switch_forces.habit` | Yes |
| What worries you? | `switch_forces.anxiety` | Revisit briefly |
| What's the priority? | `odi.outcomes[]` | Yes, if scored |
| How should it feel? | `needs.emotional[]` | Yes |
| Technical constraints? | — | Still ask |
| Architecture preference? | — | Still ask |
| Scope / MVP? | — | Still ask |

## After brainstorming

The spec doc written by brainstorming should reference the source `jtbd.json` path so the planning agent can also access it. Include a line at the top of the spec:

```
Source JTBD: ~/jtbd/<slug>/jtbd.json
```

This lets any agent in the chain trace decisions back to the original interview evidence.
