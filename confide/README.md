# CONFIDE (plugin)

Local-first de-identification toolkit for session transcripts. Three skills:

- **`confide:setup`** — install deps + Ollama model, write the optimal-default config.
- **`confide:anon`** — redact PII from a transcript/folder locally → a GREEN copy + counts-only stats.
- **`confide:red`** — residual re-identification **risk check** on redacted output (defensive; own data only).

Privacy-first: everything runs locally; raw text never leaves the machine. Built from the
[CONFIDE benchmark](https://github.com/glebis/confide). See `SPEC.md`; run `evals/run_evals.sh`.

Install: `/plugin install confide@glebis-skills` → then run `confide:setup`.
