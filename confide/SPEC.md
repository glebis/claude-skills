# CONFIDE plugin — specification

A local-first de-identification toolkit for session transcripts, packaged as a Claude Code
plugin with three namespaced skills. Built from the CONFIDE benchmark
(github.com/glebis/confide); this plugin is the **tool** facet (run on your own data),
not the scored benchmark.

## Goals
- One install path that sets up everything and picks sensible defaults: **`confide:setup`**.
- Anonymize a transcript / folder locally before any cloud use: **`confide:anon`**.
- Verify what an attacker could still infer/link after redaction: **`confide:red`**.
- Privacy-first: everything runs **locally** by default; raw text never leaves the machine.

## Skills

### `confide:setup`
**Purpose:** download + install all required packages and write an optimal default
preference file, so `anon`/`red` work with zero further config.
- **Triggers on:** "set up confide", "install confide de-id", "configure confide".
- **Does:**
  1. Installs Python deps: `natasha`, `scrubadub`, `phonenumbers`, `pymorphy2` (+ `pymorphy2-dicts-ru`), `setuptools<81` (pkg_resources for pymorphy2). Optional: `presidio-analyzer` (EN baseline).
  2. Checks **Ollama** is installed/running; pulls the default model (`qwen2.5:3b`). Notes the optional bigger attacker model for `red`.
  3. Detects optional **llama.cpp** (reproducible engine) — records if present, never required.
  4. Writes `~/.config/confide/config.json` with the **optimal default preferences** (below),
     unless one exists (then `--show` / `--reconfigure`).
- **Output:** a readiness report (deps ✓/✗, model ✓, engine, config path) — no PII.

### `confide:anon`
**Purpose:** redact PII from a session transcript (or folder) locally.
- **Triggers on:** "anonymize this transcript", "redact PII", "de-identify session", "make safe to share".
- **Does:** runs the layered local stack per config — regex (emails/URLs/phones/IDs/dates) →
  Natasha (RU NER) → local LLM (quasi-PII) — interval-merges spans, writes a **GREEN** redacted
  copy with typed placeholders (`[PERSON]`, `[DATE]`, …) + a stats summary (counts by type/layer,
  redaction rate). Never prints PII values.
- **I/O:** input path (file/dir) → `<name>.green.md` + stats JSON. Stays fully local.

### `confide:red`
**Purpose:** residual re-identification **risk check** on already-redacted output (defensive).
- **Triggers on:** "check residual re-id risk", "red-team my redaction", "what can an attacker still infer", "is this safe to share".
- **Reframe:** no ground truth on real input → surfaces *what an attacker could infer / single
  out / link* (GDPR Art-29: inference / singling-out / linkability), **qualitatively**, not a recall score.
- **Guardrails (dual-use):** runs only on the **user's own/redacted** input; refuses to be used
  as an attack on third-party data; emits risk **categories**, not a re-identification recipe;
  local attacker by default; cloud attacker only opt-in on synthetic/consented data.
- **Output:** residual-risk report — surviving quasi-identifiers, inferable attributes, linkable
  pairs — + the honest caveat that *absence of a finding ≠ safety*.

## Optimal default preferences (chosen)
Written to `~/.config/confide/config.json`:
```json
{
  "engine": "ollama",                 // zero-config, Metal, handles long docs; llama.cpp optional
  "anon_model": "qwen2.5:3b",         // fast local LLM layer
  "red_attacker_model": "qwen2.5:3b", // local default; WARN it's a floor (weak attacker under-reports)
  "languages": ["ru", "en"],
  "layers": ["regex", "natasha", "llm"],
  "redaction_style": "typed_placeholder",  // [PERSON], [DATE] … (reversible map kept locally, never shipped)
  "privacy": { "local_only": true, "cloud_apis": false, "cloud_only_on_synthetic": true },
  "ollama_host": "http://localhost:11434"
}
```
Rationale: local-only + Ollama + qwen2.5:3b is the robust zero-config baseline (the benchmark
showed Ollama handles long RU docs where llama.cpp 400s; 3b is fast). `red` defaults local but
flags that a stronger attacker is the true ceiling.

## Architecture
- `shared/confide_core.py` — config load/defaults, the layered detectors (regex/Natasha/LLM,
  engine-agnostic transport), span merge, redaction. Reused by `anon` + `red`.
- Each skill: `SKILL.md` (imperative, triggers in description) + thin `scripts/` entrypoint.

## Evals (created + run)
`evals/` — behavior + trigger checks, runnable offline where possible:
1. **anon redacts known PII** — synthetic fixture with planted PII → assert each type masked, no leakage.
2. **anon stats-only** — output JSON has no PII values; redacted file has no original PII substrings.
3. **red surfaces residual risk** — a deliberately under-redacted fixture → assert it flags surviving quasi-IDs; a well-redacted one → fewer/no findings.
4. **setup writes valid config** — produces parseable config with the optimal defaults; idempotent.
5. **trigger phrasings** — table of utterances → expected skill (documented; manual/LLM-judged).

## TDD plan
For every script: write the failing test first (`tests/` per skill or `evals/`), implement to green.
- `shared/confide_core.py`: tests for regex detectors, span merge, redaction, config defaults.
- `setup`: test config generation + idempotency + dep-check logic (mock installs).
- `anon`: test end-to-end redaction on fixtures (no network — regex/Natasha path; LLM layer mocked or skipped offline).
- `red`: test the risk-surfacing logic on fixtures (attacker LLM mocked).

## Deploy
- Plugin dir `confide/` in `glebis/claude-skills`; register in `.claude-plugin/marketplace.json`.
- Commit + push. Installable via the marketplace (`/plugin install confide@glebis-skills`).
