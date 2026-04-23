# Granularity Fixes

Applied when the Granularity Gate in `SKILL.md` scores any dimension at 0. One rewrite pass, then accept and flag weaknesses in `evidence.weaknesses[]` — don't interrogate.

---

## Actor specificity

**Fail (0):** "users," "people," "customers," "everyone," "someone"
**Fix:** Ask one of:
- "Which user specifically? Give me their role or title."
- "Can you name one real person who has this problem?"
- "Is this the buyer, the operator, or the affected party?"

**Pattern:** `Junior PMs preparing their first launch readiness doc` beats `users getting ready to ship`.

---

## Context / trigger

**Fail (0):** "always," "in general," "whenever they need to," or no context
**Fix:** Ask one of:
- "Walk me through the last time this happened. What were they doing right before?"
- "What event causes them to stop and try to solve this?"
- "Is this a daily thing, a launch thing, or a fire-drill thing?"

**Pattern:** `At the end of a customer call, when the CRM notes are already cold` beats `when taking notes`.

---

## Current workaround

**Fail (0):** "nothing," "they don't," "various tools," "whatever they have"
**Fix:** Ask one of:
- "If they can't use your thing, what do they do instead? Even if it's ugly?"
- "Spreadsheets? Slack threads? Another person doing it manually?"
- "What did they do yesterday?"

**Pattern:** `They paste the transcript into ChatGPT, copy out tasks, and manually paste them into Linear — takes 8 minutes, loses context` beats `they use AI tools`.

---

## Measurable outcome

**Fail (0):** "better," "improved," "more efficient," "good"
**Fix:** Ask one of:
- "Better by how much?"
- "If you measured it — time, money, error rate, calls saved — what would you expect?"
- "What's the threshold where this becomes worth doing vs. not worth doing?"

**Pattern:** `Cut the doc-prep from 90 minutes to under 15` beats `save time`.

Accept directional metrics ("should drop by at least half") as score 1. Quantified targets with a real number = score 2.

---

## Evidence quote

**Fail (0):** no quote, no paraphrase, pure hypothesis
**Fix:** Ask one of:
- "Who told you this? What did they actually say?"
- "Have you heard this in a customer call or just inferred it?"
- "Can you pull one sentence from a Slack thread, review, or transcript that captures this?"

**Pattern:** `"I spend my entire Sunday rebuilding the readiness doc because nobody updated the tracker" — PM at a Series B SaaS` beats `PMs find this painful`.

Paraphrase without attribution = score 1. Verbatim with source = score 2. Pure inference with no user contact = score 0.

---

## After rewrite

Re-score the same dimensions. If still 0, flag in `evidence.weaknesses[]` and move on. Do not loop more than once — the user's signal that they genuinely don't know is itself a useful finding.

## One heuristic

If the rewritten version could be copy-pasted into a pitch deck and feel specific (not generic), it passes. If it could describe any B2B tool ever built, it fails.
