# CONFIDE plugin — v2 skills spec (rehydrate / audit / vault / annotate / view)

Extends SPEC.md. The plugin now has **eight** skills total — `confide:` **setup, anon, red,
rehydrate, view, audit, vault, annotate**. This v2 spec adds the five skills beyond the v1
trio (setup/anon/red): **rehydrate, view, audit, vault, annotate** + one change to
`confide:anon` (reversible map). All local-first; raw PII never leaves the machine.

## Change to `confide:anon` — emit a local reversible map (enables rehydrate)
Today `anon` writes typed placeholders `[PERSON]` (lossy — every person collapses to the same
token). For the round-trip we need **reversibility**:
- New mode (default ON, `--no-map` to disable): assign **unique, stable placeholders per
  distinct value** using a reserved sentinel grammar — `[CONFIDE_PERSON_0001]`,
  `[CONFIDE_PERSON_0002]`, `[CONFIDE_DATE_0001]`… (zero-padded 4 digits). The same EXACT surface
  value always maps to the same placeholder within a document (**not entity coreference**:
  this is exact-value matching, so inflected forms — e.g. RU "Марина" vs "Марины" — are
  SEPARATE placeholders; there is **no lemmatized merge**). The `CONFIDE_` sentinel is reserved:
  a real transcript will essentially never contain it, so there is no collision risk, and
  rehydrate never matches ordinary prose like "Person 1".
- Write `<name>.map.json` — a structured map: `{ "schema_version":1, "doc_id":…,
  "green_sha256":<sha256 of the green text>, "created":…, "entries":[{"placeholder":…,
  "type":…,"original":…}] }` **next to the green file, gitignored, never shipped**. This is the
  secret. Green file + map together = original. The `green_sha256` lets rehydrate `--verify-green`
  detect a wrong map for a document.
- Stats stay counts-only. The map is the ONLY artifact with original values, and it stays local.
- Back-compat: `--style typed_placeholder` (non-unique) still available for non-reversible use.

## `confide:rehydrate` (restore / unmask)
**Purpose:** put real values back into an analysis that was produced from the GREEN
(placeholder) text — locally. Completes the round-trip: redact → cloud-analyze the green →
get analysis full of `[CONFIDE_PERSON_0001]`/`[CONFIDE_DATE_0002]` → **rehydrate** → real analysis.
- **Triggers:** "rehydrate", "restore real names", "unmask the analysis", "put the names back",
  "de-redact this output", "reverse the placeholders".
- **Input:** the analysis/text containing placeholders + the `<name>.map.json` (or a dir).
- **Does:** replace every reserved-sentinel placeholder with its mapped original value.
  **Robust to LLM mangling** that STILL contains the full `CONFIDE_TYPE_NNNN` core:
  `[CONFIDE_PERSON_0001]`, `[CONFIDE PERSON 0001]`, `CONFIDE_PERSON_0001`,
  `confide_person_0001` → same map key. It does NOT match naked forms lacking the `CONFIDE`
  prefix (so ordinary prose "Person 1" is never touched), and `0001` never eats `0010`.
  Idempotent: rehydrating already-rehydrated text is a no-op. Optional `--verify-green <green>`
  warns if the map's `green_sha256` doesn't match the document. Report restored / unmatched
  (counts only).
- **Guardrails:** runs LOCALLY on the user's own map; the map never leaves the machine; never
  fetches or transmits. Warn if placeholders appear that aren't in the map (possible hallucination).
- **Output:** rehydrated text (written locally) + a restore summary (restored N, unmatched M).

## `confide:audit` (scan)
**Purpose:** corpus-scale, **stats-only** PII audit over a folder of real sessions → aggregate
report. "How much PII is across my corpus / is my redaction holding at scale?"
- **Triggers:** "audit my sessions", "scan folder for PII", "how much PII across these transcripts",
  "PII stats for my corpus", "is my redaction holding".
- **Does:** run the detector stack over each file (LOCAL), emit ONLY aggregates — counts by
  type + by layer, per-session redaction-rate distribution, doc lengths, a coarse residual
  proxy. NEVER prints/writes transcript text or PII values (the `real_session_eval` privacy
  contract). Writes an aggregate report (md/json) + optional Tufte HTML dashboard.
- **Output:** aggregate stats report. Can run on RED (raw) corpora or GREEN (redacted) to check
  residual.

## `confide:vault` (three locks)
**Purpose:** operationalize storage of RED (real) data behind the three locks
(device + encrypted store + per-file/isolation), with a checklist. Storage, not detection.
- **Triggers:** "set up confide vault", "encrypt my session data", "three locks", "secure store
  for transcripts", "sops/age for RED data".
- **Does (check + optional init):**
  - **Lock 1 device:** check FileVault (`fdesetup status`), screen-lock — report.
  - **Lock 2 store:** offer/init a dedicated encrypted store (encrypted APFS volume or
    `hdiutil` AES-256 image) for RED; verify it's excluded from iCloud/Dropbox.
  - **Lock 3 per-file:** check `sops`+`age` present; help generate an age key (kept separate),
    and show the `sops --encrypt/--decrypt` recipe; confirm processing happens locally.
  - Print the THREE-LOCKS storage **checklist** with current ✓/✗ status.
- **Output:** lock-status report + checklist + the exact commands to fix any ✗. No data moved
  without explicit confirmation.

## `confide:annotate` (gold + IAA) — annotators are first-class
**Purpose:** build/verify a PII gold set with human annotators — launch the browser annotator,
follow the codebook, compute inter-annotator agreement + draft adjudicated gold.
- **Triggers:** "annotate PII", "label this transcript", "build a gold set", "inter-annotator
  agreement", "review annotations", "adjudicate labels".
- **Bundled:** `assets/annotator.html` (zero-install browser tool, EN/RU), `references/codebook.md`,
  `scripts/score_iaa.py`, `scripts/gold_to_labels.py`.
- **Does:**
  1. Open `annotator.html` for the annotator(s) → they label spans per the codebook, export
     `labels.<doc>.<annotator>.json` (local, names stay in the browser/file).
  2. `gold_to_labels.py` — turn an existing gold into a reference annotator (test the loop solo).
  3. `score_iaa.py` — Cohen's/Fleiss' κ + disagreement queue + draft adjudicated gold from the
     collected label files.
  - **Annotator-first:** clear instructions FOR the annotator (what to label, privacy: only
    synthetic/consented data, nothing re-shared), and FOR the coordinator (collect → κ →
    adjudicate). Target κ ≥ 0.8.
- **Output:** IAA results (κ, F1) + disagreement list + draft adjudicated gold. Stats/labels
  only; transcript text stays local.

## `confide:view` (visual diff — what de-id & rehydrate do)
**Purpose:** produce a **self-contained interactive HTML** that lets you *see* the
de-identification and restoration — original ↔ redacted ↔ rehydrated, with color-coded PII
spans and toggles. LOCAL only (it contains original text, like a vault artifact).
- **Triggers:** "show me what was redacted", "visualize the de-id", "compare original and
  redacted", "highlight the PII", "view redaction diff", "see what rehydrate restored".
- **Input:** original text + its `<name>.map.json` (and optionally a rehydrated analysis).
- **Renders (one standalone .html, no server):**
  - The transcript with every PII span **highlighted, colored by type** (PERSON/DATE/…), each
    showing original value ↔ its placeholder on hover.
  - **Interactive state toggle:** **All** (fully redacted, placeholders shown) · **None**
    (original, nothing masked) · **Selected** (mask only chosen types — checkboxes per type),
    so the user sees exactly what each layer/type removes.
  - A legend + counts by type; optional side-by-side original vs green.
- **Privacy:** the HTML embeds real values → written locally, gitignored, never shipped; a
  banner marks it private. (Same posture as the relationship-graph HTML.)
- **Output:** `<name>.view.html` — opened in the browser. Built so it renders with **zero JS
  errors** (browser-tested in evals, like the relationship graph).
- Reuses the span data from `anon` (the map + span offsets); a thin renderer, no new detection.

## Evals (created + run)
- **rehydrate round-trip:** anon (reversible) a fixture → simulate a cloud analysis that uses the
  placeholders (incl. mangled variants) → rehydrate → assert real values restored, restored-count
  correct, unmatched flagged. Negative: a placeholder not in the map → reported as unmatched.
- **anon reversibility:** same EXACT value → same placeholder (inflected forms are distinct —
  no lemmatized merge); map round-trips (rehydrate(green,map)==original for the masked spans);
  map JSON has the originals, green does NOT.
- **audit:** folder of fixtures → aggregate report with correct per-type counts, NO PII in output.
- **vault:** lock-status checker returns a structured dict (filevault/sops/age/store booleans) under mocked system calls; checklist renders.
- **annotate:** score_iaa on mock label files → κ computed, disagreements flagged (reuse existing tests); gold_to_labels produces a valid reference annotator.
- **trigger evals:** each new skill's description carries its trigger phrasings.

## TDD plan
Tests-first per script. Reversible-map + rehydrate are the core new logic — test exact-match,
coreference, and mangled-placeholder robustness. vault/annotate system+browser parts mocked.

## Deploy
Update plugin (eight skills: setup, anon, red, rehydrate, view, audit, vault, annotate),
re-run full eval suite, register/refresh marketplace, commit + push.

## Site + illustrations
- Update the skills site to reflect the CONFIDE toolkit (all skills).
- Generate one illustration per tool in the site's existing illustration style.
