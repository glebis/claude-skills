# Mode: cross-validate

Two layers: adversarial code review (every experiment) and external
model review (major claims). Both earned their place by finding killers
that internal passes missed.

## Layer 1 — adversarial code review (mandatory per experiment batch)

Use an independent code-review agent (e.g. Codex CLI read-only):

```
echo "<review prompt>" | codex exec --skip-git-repo-check --sandbox read-only -C <repo> 2>/dev/null
```

Prompt template: name the files; direct focus to (1) statistical
correctness — permutation universe, lag alignment through data gaps,
BH family handling, residualization validity; (2) data handling —
timezones, zero-vs-missing, cache staleness, category matching, silent
drops; (3) selection bias. Ask for numbered findings with severity and
one-line fixes; forbid edits.

Triage discipline: fix mechanical bugs; for methodological findings that
do not flip conclusions (e.g. anti-conservative approximations under a
null), add a disclosure note to the results JSON instead of
re-architecting. Re-run affected experiments after fixes. Track
findings-fixed counts in the report footer.

## Layer 2 — external model review (major claims / program reviews)

An external frontier model (e.g. ChatGPT Pro via browser automation, or
any strong model with code execution) reviews the program with FULL
methods and AGGREGATE results — never raw personal text/audio.

Archive packaging rules:
- include: experiment scripts, results JSONs (statistics), verdicts,
  pre-registration prompts, a dense pipeline summary (read-first file);
- exclude: transcripts, dictation/diary text, audio, embeddings caches;
- scan before upload: flag any string value >240 chars with >25 spaces
  (sentence detector) — methodology prose is fine, quoted data is not.

Ask for four deliverables in order: (1) adversarial review naming
fragile claims and uncontrolled confounds; (2) literature mapping to
computable measures; (3) analyses it can run itself on the included
aggregates; (4) N prioritized, concretely executable follow-up goals
(hypothesis, data, method, power, priority each).

Treat its kills seriously: an external exact recompute of a flagship
result (impossible p=0.0005 at n=19) is what triggered the audit layer.

## Layer 3 — convergence as validation

The strongest evidence in observational self-data is CROSS-CHANNEL
convergence: two independent instruments (different sources, different
methods) agreeing on the same construct (e.g. diary embedding axis ↔
dictation lexicon, r≈0.21, q≈0.03). Prefer designs that admit a
convergence test; a channel that converges with nothing after ~200
shared days is suspect.
