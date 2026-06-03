---
name: annotate
description: Build and verify a PII gold set with HUMAN annotators (first-class). Launch the browser annotator, label spans per the codebook, export per-annotator label files, then compute inter-annotator agreement (Cohen's/Fleiss' kappa) and draft an adjudicated gold. Use when the user says "annotate PII", "label this transcript", "build a gold set", "inter-annotator agreement", "review annotations", "adjudicate labels", or wants to measure/defend a de-identification gold standard. Local-only: synthetic or consented data only; annotators' names and transcript text stay on the machine — only labels/stats are collected, nothing PII is re-shared.
---

# confide:annotate — human PII gold set + inter-annotator agreement

Humans label PII spans in a transcript; you measure how much they agree (κ) and draft an
adjudicated gold from their labels. Annotators are first-class here — most of this skill is
plain instructions FOR a person doing the labelling, plus a coordinator path to score it.

## Privacy invariants (do not violate)
- **Synthetic or consented data only.** Never load a real client transcript the person did not
  consent to share. When in doubt, anonymize first (`confide:anon`) and annotate the GREEN copy.
- **Names stay local.** The annotator's labels (which contain real surface text spans) live in
  their browser and the exported JSON file on their own machine. Collect label files locally.
- **Nothing PII is re-shared.** Only κ / F1 / disagreement *clusters* travel between people if
  needed. The transcript text and the original PII are never re-distributed by this skill.

## Bundled assets
- `assets/annotator.html` — zero-install browser annotation tool (EN/RU, runs offline).
- `references/codebook.md` — the labelling rulebook (10 PII types, direct/quasi, harm).
- `references/tool-guide.md` — how to drive the tool + scorer step by step.
- `scripts/score_iaa.py` — Cohen's/Fleiss' κ, span-F1, disagreement queue, draft gold (stdlib).
- `scripts/gold_to_labels.py` — turn an existing gold into a "reference annotator" to test solo.

---

## FOR THE ANNOTATOR (no coding needed)

1. **Open the tool.** Double-click `assets/annotator.html` (or open it in Chrome/Firefox/
   Safari). It runs entirely in your browser — nothing is uploaded; labels stay on your
   machine until you Export.
2. **Read the rules.** Open `references/codebook.md` first. It defines the 10 types
   (PERSON, LOCATION, ORG, PHONE, EMAIL, ID, DATE, MEDICATION, AGE, PROFESSION), what counts as
   a span (the *minimal* identifying text), and direct vs. quasi-identifier.
3. **Set your annotator id and load the transcript** in the tool (e.g. `A`, `B`, or your name).
   Use only synthetic or consented text.
4. **Label every PII span.** Select the minimal text that identifies a real person (the client
   or third parties they mention) and assign its type. Record direct/quasi, entity id, role,
   and harm as the codebook describes. **Do not rewrite or redact — only label.**
5. **When unsure, log it — don't guess silently.** Add a note starting with `QUESTION:` on the
   span (e.g. `QUESTION: gym or city?`). These flow straight into the adjudication queue.
6. **Export.** Click Export → you get `labels.<doc>.<annotator>.json`
   (schema: `{doc_id, annotator, text, spans:[{start,end,text,type,...}]}`). Keep it local and
   hand only this file to the coordinator. Two+ people should label the *same* doc independently
   (blind) for a meaningful κ.

## FOR THE COORDINATOR (measure + adjudicate)

1. **Collect** every `labels.<doc>.<annotator>.json` into one folder, e.g. `labels/`.
2. **Score IAA:**
   ```bash
   python3 skills/annotate/scripts/score_iaa.py --labels-dir labels/ --out-dir results/
   ```
   It writes (per doc + overall): **Cohen's κ** (pairwise), **Fleiss' κ** (3+ annotators),
   **span-F1**, a **disagreement queue** (`*-iaa-disagreements.json`: every cluster annotators
   don't fully agree on, plus any `QUESTION:` spans), and a **draft adjudicated gold**
   (`*-adjudicated-gold-draft.json`: majority span per overlap-cluster, ties/questions marked
   `needs_review:true`). Character-level κ sidesteps tokenization disputes.
3. **Target κ ≥ 0.80** = a defensible gold. Lower usually means an unclear codebook rule, not a
   careless annotator — fix the rule and re-label, don't just discard.
4. **Adjudicate.** Walk the disagreement queue with a human adjudicator; resolve each
   `needs_review` cluster. The resulting label set is the published gold; report
   post-adjudication κ too. Nothing is ever auto-finalised.

## Test the loop solo (no second person yet)
Treat an existing gold JSONL as one "reference annotator", label the same doc yourself in
`annotator.html` as another, then score the pair:
```bash
python3 skills/annotate/scripts/gold_to_labels.py --gold GOLD.jsonl --name gold --out-dir labels/
# label the same doc yourself in annotator.html as "me" -> drop labels.<doc>.me.json into labels/
python3 skills/annotate/scripts/score_iaa.py --labels-dir labels/ --out-dir results/
```
(`--sessions-dir DIR` lets `gold_to_labels.py` read transcript text from disk so char offsets
match the gold exactly.)

## Output
IAA results (κ, F1) + a disagreement list + a draft adjudicated gold — labels/stats only.
Transcript text and original PII stay local; only what's needed to adjudicate is shared.
