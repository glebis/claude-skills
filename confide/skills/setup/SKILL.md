---
name: setup
description: Set up, install, and configure CONFIDE local de-identification — installs Python deps (natasha, scrubadub, phonenumbers, pymorphy2), ensures Ollama + pulls the default qwen2.5:3b model, detects optional llama.cpp, and writes the optimal-default config so confide:anon and confide:red work with zero further config. Everything is local-first; raw text never leaves the machine. Use when the user says "set up confide", "install confide", "configure confide de-id", "confide setup", or "get confide ready".
---

# confide:setup

One-shot installer + optimal-default config writer for the CONFIDE local de-identification
toolkit. After running this, `confide:anon` (redact a transcript) and `confide:red` (residual
re-identification risk check) work with no further configuration.

**Local-first:** all detection and redaction run on the user's machine. Readiness checks and
config writing never read, print, or transmit any transcript text or PII — only booleans and
the config path.

## When to use
Trigger phrasings: "set up confide", "install confide", "configure confide de-id",
"confide setup", "get confide ready to anonymize".

## How to run

The entrypoint is `scripts/setup.py`. It imports the shared core (`shared/confide_core.py`)
for the canonical `DEFAULTS` — do not redefine preferences here.

1. **Check readiness (default, no install):**
   ```bash
   python3 skills/setup/scripts/setup.py --check
   ```
   Prints a ✓/✗ table: Python deps importable (natasha, scrubadub, phonenumbers, pymorphy2),
   Ollama reachable (`GET ollama_host/api/tags`), the `anon_model` pulled, llama.cpp on PATH
   (optional), and whether the config exists. Booleans only — no PII.

2. **Install everything (best-effort, tolerates failures):**
   ```bash
   python3 skills/setup/scripts/setup.py --install            # core deps + ollama pull
   python3 skills/setup/scripts/setup.py --install --with-presidio   # + optional EN baseline
   ```
   - pip-installs: `natasha scrubadub phonenumbers pymorphy2 pymorphy2-dicts-ru "setuptools<81"`
     (`setuptools<81` supplies `pkg_resources` for pymorphy2). Optional `presidio-analyzer` behind
     `--with-presidio`.
   - If `ollama` is on PATH, runs `ollama pull qwen2.5:3b`.
   - Each step reports ✓/✗; a failed step never aborts the others.

3. **Write the optimal-default config (idempotent):**
   ```bash
   python3 skills/setup/scripts/setup.py --write-config   # writes only if absent
   python3 skills/setup/scripts/setup.py --reconfigure    # overwrites with defaults
   python3 skills/setup/scripts/setup.py --show           # print current config
   ```
   On first run with no config present, the script writes the defaults automatically.
   `--write-config` will **not** clobber an existing (user-customized) config; use
   `--reconfigure` to force-reset.

Config lives at `~/.config/confide/config.json`.

## Chosen optimal preferences (from SPEC.md)

Written from `confide_core.DEFAULTS`:

| Key | Value | Why |
|---|---|---|
| `engine` | `ollama` | zero-config, Metal-accelerated, handles long docs (llama.cpp 400s on long RU) |
| `anon_model` | `qwen2.5:3b` | fast local LLM layer for quasi-PII |
| `red_attacker_model` | `qwen2.5:3b` | local default; it is a **floor** — a stronger attacker is the true ceiling |
| `languages` | `["ru", "en"]` | bilingual corpus |
| `layers` | `["regex", "natasha", "llm"]` | deterministic → RU NER → quasi-PII |
| `redaction_style` | `typed_placeholder` | `[PERSON]`, `[DATE]`, … (reversible map kept locally, never shipped) |
| `privacy.local_only` | `true` | raw text never leaves the machine |
| `privacy.cloud_apis` | `false` | cloud disabled by default |
| `privacy.cloud_only_on_synthetic` | `true` | cloud attacker only opt-in on synthetic/consented data |
| `ollama_host` | `http://localhost:11434` | local Ollama |

## Notes
- llama.cpp is **optional** (reproducible engine) — detected and recorded if present, never required.
- The bigger attacker model for `confide:red` is optional; the local 3b default under-reports risk.
- Importable functions for programmatic / tested use: `readiness()`, `ensure_config(reconfigure=False)`,
  `install(with_presidio=False)`, `show_config()`.
