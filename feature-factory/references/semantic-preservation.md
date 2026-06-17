# Semantic Preservation Guard

Use when any edit, LLM rewrite, optimizer pass, or "tidy-up" touches the Goal Contract template, the risk rubric, the verify checks, or this skill itself. Automated/polishing edits reward generic prose and quietly delete the exact constraints that make the method work.

## The rule
A rewrite is acceptable **only when it is both** better for the task **and** semantically preserving of operational constraints. If they conflict, **preserve operational utility first** and improve wording second.

## Load-bearing anchors to preserve
Treat each as a hard fact that must survive a rewrite:

- **Required Goal Contract fields:** Smallest shippable slice, Stop condition (the `<!-- required -->` markers).
- **Caps:** `≤3`, `≤5` limits — they are the guard against waterfall-in-markdown. Removing them is a regression even if prose reads cleaner.
- **Fail rule:** "if a goal can't produce evidence, it's a wish with better formatting."
- **Risk classification:** R0–R4 ladder; R4 = STOP; EU AI Act Art 5 (prohibited) and Art 50 (labelling) screens.
- **Evidence mapping:** every desired outcome maps to concrete evidence.
- **No silent rewrites:** agents propose Goal Amendments, never overwrite the goal.
- **No engine/config abstraction:** the "do not build" list (telemetry, GEPA, pipeline.config, executor, adapter layers). A rewrite that introduces an abstraction "for flexibility" is the failure mode, not an improvement.
- **Determinism / flake rules:** no timing-based tests; flake = failure not retry.
- **Single focused loop:** no swarm / parallel fan-out for the coding phase.
- **Negative constraints in general:** any `must` / `never` / `only` / `do not` / `stop` sentence.

## Acceptance check (before keeping a rewrite)
1. Extract every sentence in the baseline containing a strong cue word: `must`, `required`, `never`, `do not`, `only`, `stop`, `before`, `after`, `cap`, `fail rule`.
2. Confirm each survives the candidate (rephrasing is fine; deletion is not). Rough threshold: ~60% content-word overlap per anchor, a few misses allowed for long docs.
3. Reject the candidate if too many anchors are dropped — **even if it reads better or scored higher.**

## Why this is here at N=1
This guard is cheap and immediately useful: it is just a checklist for not deleting the beams. It is the one piece of the "evolutionary" idea worth keeping now — the actual optimizer (GEPA-style template evolution) is deferred until a real corpus of 5–10 features exists, and may only ever propose diffs, never mutate live templates.
