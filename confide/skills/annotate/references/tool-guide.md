# CONFIDE — annotation tools: how to use them

Two tools turn the codebook into measured gold:
- **`annotator.html`** — a browser tool annotators use to label PII (no install, offline).
- **`score_iaa.py`** — the coordinator's script: computes human IAA (Cohen's/Fleiss' κ,
  span-F1), lists disagreements, and drafts the adjudicated gold.

Read `ANNOTATION-CODEBOOK.md` first — it defines *what* to label; this defines *how* to drive
the tools. For any unfamiliar term (PII / ПДн, quasi-identifier, span, κ…), the bilingual
EN↔RU **[GLOSSARY.md](GLOSSARY.md)** gives a plain-language explanation in both languages.

---

## A. For annotators (no coding needed)

### 1. Open the tool
Double-click **`annotator.html`** (or open it in Chrome/Firefox/Safari). It runs entirely in
your browser — **nothing is uploaded**; your labels stay on your machine until you Export.

### 2. Set up
- Type your **annotator id** (your initials, e.g. `mk`) in the top-right box — always the same id.
- Click **"load transcript"** and pick the `.md`/`.txt` file you were given.

### 3. Label
- **Select** the text of an identifier (drag over it), then **click the type button** it
  belongs to (PERSON, LOCATION, …). The span is highlighted and added to the list.
- In the list on the right, adjust per span if needed: **class** (direct/quasi), **harm**,
  **role**, and **entity_id**. *Reuse the same `entity_id`* for every mention of the same
  person/thing (e.g. all "Marina"/"Ms. Volkova" → `marina`). This is important — it's how we
  score "every mention masked."
- Anything you're unsure about: type `QUESTION: …` in that span's **note**. It auto-goes to the
  adjudication queue — don't agonise, just flag it.
- To **remove** a span: click its highlight in the text, or the ✕ in the list.
- Defaults follow the codebook (e.g. PERSON→direct/high, MEDICATION→quasi/high) so usually you
  only set `entity_id`.

### 4. Work blind
Do **not** look at anyone else's labels or any existing answer key while annotating. Blindness
is what makes the agreement number meaningful.

### 5. Export & send back
- Click **"Export labels ⬇"** → it downloads `labels.<doc>.<yourid>.json`.
- Send that file back through the channel you were given. Repeat for each transcript.
- To pause and resume later: keep the exported file; next time use **"resume"** to reload it.

> Privacy: you only see synthetic or consented transcripts. Don't copy, screenshot, or
> re-share the transcript text — only your `labels.*.json` is collected.

---

## B. For the coordinator (computing IAA + adjudicating)

### 1. Collect
Put every annotator's exports for the pilot into one folder, e.g. `results/labels/`:
```
results/labels/labels.ru-a-s01.mk.json
results/labels/labels.ru-a-s01.av.json
results/labels/labels.ru-c-s02.mk.json
...
```
Filenames don't matter; the script groups by the `doc_id` + `annotator` inside each file.
Each doc needs **≥2 annotators** to score (3+ enables Fleiss' κ).

### 2. Score
```bash
cd eval
python3 score_iaa.py --labels-dir labels/ --out-prefix human-
```
Outputs:
- **`human-IAA-HUMAN-RESULTS.md`** / `human-iaa-results.json` — Cohen's κ (pairwise mean),
  Fleiss' κ, span-F1, per doc + overall. **Target κ ≥ 0.80.**
- **`human-iaa-disagreements.json`** — every span-cluster annotators disagreed on (with each
  annotator's vote) + everything flagged `QUESTION:`. This is the adjudication queue.
- **`human-adjudicated-gold-draft.json`** — one entry per span-cluster; unanimous ones are
  ready, contested ones carry `needs_review:true`.

### 3. Read the number honestly
- κ ≥ 0.80 → defensible gold; proceed.
- κ 0.6–0.8 → usable but the codebook has gaps — the disagreements show where. Sharpen the
  codebook (add rulings), and it's fine if a re-score after adjudication is higher.
- κ < 0.6 → the task/guideline is under-specified for those types; fix before scaling.

### 4. Adjudicate
- Go through `human-iaa-disagreements.json` with a senior adjudicator (or a consensus call).
- For each, decide the correct label; record the **ruling back into `ANNOTATION-CODEBOOK.md`**
  (so v2 is sharper and the next batch agrees more).
- Edit `human-adjudicated-gold-draft.json`: set the final `type`/span, flip `needs_review` to
  `false`. The result is the **adjudicated gold**.

### 5. Report both numbers
Quote **pre-adjudication κ** (the raw agreement — the credibility statistic) *and*
**post-adjudication κ** (after reconciliation). Update `IAA-HUMAN-RESULTS.md`; this set
**replaces** the old LLM-assisted consistency check as CONFIDE's IAA (R4).

### 6. Fold into the benchmark
Convert the adjudicated gold into the eval JSONL shape (`pii-eval-*.jsonl`) — a small loader
maps `{doc_id,start,end,type,entity_id,identifier_class,person_role,harm}` straight in. Then
re-run `score_bench.py` against the human gold and `check_artifacts.py`.

---

## C. Applying this to real data (T1: AnnoMI / JayGuard)

Same flow, different source text:
- **AnnoMI (EN)** — download the transcripts, drop each as a `.txt`, annotate with the codebook
  → first *real* EN therapy de-id gold.
- **JayGuard (RU, `just-ai/jayguard-ner-benchmark`)** — already has PERSON/GPE/address spans;
  load a slice, **extend** it with the full CONFIDE type set (MEDICATION/AGE/PROFESSION/DATE…)
  → first *real-text RU* slice. Keep its license terms.
Process real text **locally only** (`THREE-LOCKS.md`); only the span labels (no transcript
text) are pooled for scoring.

**One line for a volunteer:** open `annotator.html`, set your id, load the file, select text →
click a type, set `entity_id`, Export, send it back.
