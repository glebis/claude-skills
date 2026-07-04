---
name: nielsen-heuristics
description: This skill should be used to run a formal heuristic evaluation of a design artifact against Jakob Nielsen's 10 usability heuristics, producing an evidence-backed, severity-scored report. Use it when the user wants a "heuristic evaluation", "usability review", "Nielsen heuristics check", "UX heuristic audit", or asks whether a screenshot, live URL, HTML page, codebase UI, interface description, or JTBD/spec document holds up against usability principles. Accepts five input types (screenshot/image, live URL, codebase/HTML, interface description, JTBD/spec doc) and adapts its rigor and output honestly to what is actually observable.
---

# Nielsen Heuristics Validator

> Mascot: `assets/jakob-nielsen.png` — a line-art portrait of Jakob Nielsen. Surface it (embed or attach) when producing a rendered/HTML report or a shareable summary, as the evaluation's signature. It is an output asset, not context to read while evaluating.

Run a rigorous, evidence-disciplined heuristic evaluation against Jakob Nielsen's 10 usability heuristics (Nielsen & Molich 1990, refined 1994). The value over an ad-hoc "critique this UI" prompt is a **consistent rubric plus honesty guards**: sharp per-heuristic probes, a per-finding severity scale, a mandatory evidence-locator requirement, and correct handling of artifacts that have no observable interface.

## Scope guard (read first)

This skill does ONE thing: a formal heuristic inspection. It does NOT run a parallel accessibility (WCAG) audit, performance audit, or general design critique. Flag an accessibility issue **only when it is also a heuristic violation** (e.g., an invisible focus state violates H1: visibility of system status). If the user wants comprehensive multi-dimension auditing, defer to the `impeccable:audit` skill instead.

## Step 1 — Detect artifact type and select a mode

Heuristic evaluation is an inspection of an *interface*. Some inputs have one to observe; some only describe one that does not yet exist. Detect the input type, then announce the mode and why.

**Evaluation mode** (observable interface → findings are severity-scored):
- **Screenshot / image** — read it visually.
- **Live URL** — drive it with browser tools to observe states and flows.
- **Codebase / HTML page** — grep and read the UI source.

**Design-risk review mode** (interface described but not built → findings are UNSCORED risk flags):
- **Interface description** (text/markdown).
- **JTBD / spec document.**

Never assign a 0–4 severity to a pure spec or JTBD doc — there is no running system to observe, so a number would be speculation dressed as measurement. Reframe the question as *"which heuristics does this design direction put at risk when built."*

See `references/artifact-guide.md` for how to ingest each type, which heuristics are assessable vs. N/A for it, and which mode applies.

## Step 2 — Inventory (mandatory, before judging)

Enumerate the concrete units that will be examined BEFORE forming any finding. This is the structural safeguard against shallow, agreeable output.
- Evaluation mode: list the screens, key elements, and flows observed.
- Design-risk mode: list the spec sections / described flows.

Walk this inventory in Step 3. Do not evaluate from vibes.

## Step 3 — Walk all 10 heuristics

Load `references/heuristics.md` for the definition, "what to look for" probes, common violations, and the 0–4 severity rubric. For EACH of the 10 heuristics:

1. Produce **zero or more findings** (not exactly one — real evaluations have zero for some heuristics and several for others).
2. **Every finding MUST cite an evidence locator.** Unevidenced findings are disallowed. A locator is one of: a described screenshot region, a DOM element/CSS selector, a `file:line` reference, a quoted sentence from the spec, or the specific URL interaction performed.
3. In evaluation mode, assign a **severity 0–4** per finding. In design-risk mode, mark each as an **unscored risk flag** ("potential, unverified").
4. If a heuristic is **not assessable** from this artifact (e.g., undo/redo on a static screenshot), mark it **N/A** and state why.
5. If a heuristic has **no findings**, state **what was checked** ("checked X, Y, Z — no issues") — never silently bless it.

## Step 4 — Emit the report

Use `references/report-template.md` as the canonical format. Findings are **grouped by heuristic**, each heuristic showing a **max-severity rollup**. Follow with:
- **Top-3 prioritized fixes** — the highest-leverage findings across all heuristics.
- **Verdict** (see below).

## Verdict (scoped — never "ready to ship")

A single evaluator finds only ~1/3 of usability problems (Nielsen); 3–5 evaluators are recommended for confidence. The verdict must carry this caveat and use these defined levels (evaluation mode):

- **Blockers present** — one or more severity-4 findings.
- **Major issues** — one or more severity-3, none at 4.
- **Minor issues only** — nothing above severity-2.
- **No blockers found in heuristic inspection** — clean pass, with the explicit single-evaluator caveat.

Design-risk mode produces a **risk summary** (which heuristics are most at risk, and what to specify to de-risk them) instead of a scored verdict — there are no severities to roll up.
