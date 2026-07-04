# Artifact Guide — ingestion, mode, and assessability per input type

Consult during Step 1. For each input type: how to ingest it, which mode it uses, and which heuristics are typically assessable vs. N/A. This is per-artifact-type guidance, not a rigid 10×5 matrix — use judgment.

---

## 1. Screenshot / image  → Evaluation mode

**Ingest:** Read the image directly. Describe what is visible; do not invent off-screen behavior.

**Assessable:** H1 (visible status shown at this moment), H2, H4, H6, H8 (hierarchy, clutter), and H9 *only if* an error state is captured.

**Typically N/A** (no interaction to observe): H3 (undo/back), H5 (confirmation flows), H7 (shortcuts/accelerators), H10 (contextual help behavior). Mark these N/A with the reason "not observable in a static image" unless the screenshot happens to show the relevant affordance (e.g., a visible "Undo" button counts toward H3).

**Watch out for:** rating a single frame as if it were the whole flow. State clearly that only one state was inspected.

---

## 2. Live URL  → Evaluation mode (most complete)

**Ingest:** Drive the page with browser tools. Actually perform interactions — hover, submit an empty form, trigger a validation error, open and close a modal, navigate the flow. Observe real states.

**Assessable:** all 10 heuristics — this is the richest input. Flow heuristics (H3, H5, H9) become observable because states can be triggered.

**Watch out for:** stopping at the first screen. Exercise at least one full task path and at least one error path so H5/H9 are evidenced, not guessed.

---

## 3. Codebase / HTML page  → Evaluation mode

**Ingest:** Grep and read the UI source (components, templates, handlers, error/validation logic, aria/labels, copy strings). Evidence locators are `file:line`.

**Assessable:** H2 (copy/terminology in source), H4 (component reuse/consistency, shared vs. divergent styles), H5 (validation logic, confirm dialogs, disabled states), H6 (state carried in props/store), H9 (error message strings and handling), H10 (help/empty-state components). H1, H7, H8 are partially assessable from markup but are more reliably judged on a rendered view — note the limitation.

**Watch out for:** accessibility creep. Contrast values, ARIA, and keyboard handling are greppable and tempting — only report them when they are also a heuristic violation (per the scope guard). Do not conduct a WCAG pass.

---

## 4. Interface description (text/markdown)  → Design-risk review mode

**Ingest:** Read the description. Treat it as an account of intended behavior, not an observed one.

**Output:** UNSCORED risk flags per heuristic. Evidence locator = a quoted sentence from the description. Reframe each heuristic as "does the described design put this at risk?" — e.g., "description mentions no loading/feedback for the async import → H1 risk when built."

**Watch out for:** assigning 0–4 severities. There is no system to observe; a number would be false precision.

---

## 5. JTBD / spec document  → Design-risk review mode

**Ingest:** Read the spec/JTBD. A pure JTBD statement ("When I ___, I want to ___, so I can ___") describes a *goal*, not an interface — the heuristic lens applies to the *design direction implied*, not to the words.

**Output:** UNSCORED risk flags. For each heuristic, ask: "if this were built as specified, which usability principle is most likely to be violated, and what does the spec fail to specify that would prevent it?" Evidence locator = quoted spec sentence or a named gap ("spec defines no error states → H5/H9 risk").

**Watch out for:** the category error of scoring goals. Also avoid inventing interface details the spec doesn't contain — flag the *absence* as a risk instead ("no help/empty-state defined → H10 risk").

---

## Quick mode selector

| Input | Mode | Findings |
|-------|------|----------|
| Screenshot / image | Evaluation | Scored 0–4 (subset of heuristics; rest N/A) |
| Live URL | Evaluation | Scored 0–4 (all heuristics assessable) |
| Codebase / HTML | Evaluation | Scored 0–4 (source-evidenced) |
| Interface description | Design-risk | Unscored risk flags |
| JTBD / spec doc | Design-risk | Unscored risk flags |
