# White-paper audit checklist (v1)

Research-grounded criteria (sources: Gopen & Swan; Nielsen Norman; Tufte; IEEE ProComm &
AU plain-language guidance; white-paper practice guides — full list in
`internal/research_report_20260603_201802.md` of the originating session, summarized at
bottom). Each criterion is an **operational rule** with an example and counterexample,
tagged `[script]` (checked by `scripts/check_doc.py`) or `[judge]` (LLM judge via
`references/audit-prompt.md`), with default severity. Severity is always
**impact × confidence**; the judge may move a finding ±1 level with stated rationale.

## A. Structure & flow

| id | Rule | Lane | Default |
|---|---|---|---|
| `structure` (abstract) | A labeled abstract / executive summary (~150–250 words) exists and states problem + key finding + recommendation. | script (presence) + judge (content) | P1 |
| `buried-lede` | The single most important finding appears in the abstract/intro, not only in §5+. *Bad:* headline result first stated on page 9. *OK:* abstract states it, body elaborates. | judge | P0 if the core claim is absent up front; else P1 |
| `problem-first` | The intro defines a concrete problem and its impact before methods/solutions. *Bad:* opens with architecture. *OK:* opens with who is harmed and how. | judge | P1 |
| `flow` | Sections follow problem → background → approach → evidence → conclusions; transitions don't jump. | judge | P2 |

## B. Clarity & readability

| id | Rule | Lane | Default |
|---|---|---|---|
| `readability` | FK grade per section ≤ target (default 13; practitioner papers aim 10–12). Trend-level metric — see severity gating in DESIGN.md. | script | P2 (P1 in abstract/intro if > target+3) |
| `acronym-undefined` | Every acronym is defined at/before first use (`Full Term (ABC)` or reverse) or in a glossary. Allowlist for universal ones (PDF, URL…). | script | P1 |
| `jargon-undefined` | Field jargon (non-acronym terms of art) is glossed on first use for the stated audience. *Bad:* "our ablation shows…" with no gloss for practitioners. *OK:* "we measured every layer alone and in combination (the *ablation*)". Soft finding — the script can't judge audience fit. | judge | P1 (low/medium confidence) |
| `sentence-length` | Average sentence ≲20–25 words; flag walls of dense text. | script (via readability) + judge | P2 |
| `scannability` | Headings are informative; lists used for series; key terms emphasized. | judge | P2 |

## C. Evidence & rigor

| id | Rule | Lane | Default |
|---|---|---|---|
| `unsupported-claim` | Every factual/quantitative claim is supported by data in the doc, a citation, or an explicit hedge. The judge flags **"apparent overclaim / unsupported claim"** and "needs verification" — it does NOT adjudicate external truth (no retrieval in v1). *Bad:* "this guarantees GDPR compliance." *OK:* "benchmark success is not GDPR certification." | judge | P0 when stated as fact; P1 when hedged but thin |
| `inconsistent-number` | The same quantity must match everywhere it appears (abstract vs body vs tables). *Bad:* abstract says 0.88, §5 says 0.78 for the same metric. | judge | P0 |
| `uncertainty-reported` | Quantitative results carry uncertainty (CIs, "directional", N) where the underlying data is small/noisy. | judge | P1 |
| `limitations-present` | A limitations section exists **and** is substantive (covers scope, sample size, biases — not a fig leaf). | script (presence) + judge (substance) | P0 (presence) / P1 (substance) |
| `marketing-tone` | No hype: superlatives ("revolutionary", "unprecedented"), buzzwords, or sales-pitch framing in technical claims. Nielsen: removing "marketese" measurably improves comprehension. *Bad:* "our groundbreaking stack." *OK:* "the stack reaches 0.88 coverage recall (CI 0.85–0.90)." | judge | P0 if a claim rests on hype; else P2 |
| `consistent-units` | Same units/terms throughout; no silent unit switches. | judge | P1 |

## D. Tables & figures

| id | Rule | Lane | Default |
|---|---|---|---|
| `table-standalone` | Tables/figures are numbered or clearly captioned, columns labeled with units, readable without hunting through text. | judge | P2 |
| `table-clutter` | Minimal ruling/decoration (Tufte): data, not chartjunk. | judge | P2 |

## E. Audience fit (practitioner focus)

| id | Rule | Lane | Default |
|---|---|---|---|
| `audience-fit` | Explanations work for the *stated* audience (e.g. final-year school reader): concepts built up, examples concrete, no leaps that require unstated background. | judge | P1 |
| `concrete-examples` | Abstract concepts are illustrated with tangible scenarios. *Good:* the quasi-identifier cascade with population fractions. | judge | P2 |
| `actionable-close` | Conclusions give the reader specific next steps, not just "more research needed". | judge | P2 |

## F. Trust & transparency

| id | Rule | Lane | Default |
|---|---|---|---|
| `structure` (date/version, author) | Publication date or version + author/affiliation visible near the top. | script | P1 |
| `links` | All links resolve (relative paths exist; http(s) reachable). Severity by materiality: claim-supporting link broken → P1; footer nicety → P2. | script + judge (materiality) | P1/P2 |
| `disclosure` | Funding/sponsor/conflict disclosed if any; data/code availability stated for empirical claims. | judge | P1 |
| `currency` | Citations and benchmarks not stale for a fast-moving field (~5 y rule of thumb). | judge | P2 |

## Severity reference (impact × confidence)

- **P0 — trust-breaking:** apparent overclaim stated as fact · internally inconsistent
  number · missing/hollow limitations in an empirical doc · core claim absent from abstract.
- **P1 — comprehension-breaking:** acronym/jargon undefined at first use · claim-supporting
  broken link · missing date/author · uncertainty absent on small-N results · audience misfit.
- **P2 — polish:** tone nits · long sentences in non-critical sections · table formatting ·
  dead footer links · staleness.

Low-confidence + high-impact ⇒ report at the lower severity with a "verify" note — never
silently promote.
