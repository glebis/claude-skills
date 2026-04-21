# Contributing to skill-studio

Thanks for considering a contribution! This project is intentionally small and opinionated. Here's how to move fast without stepping on toes.

## Quick start

```bash
git clone https://github.com/<your-org>/skill-studio.git
cd skill-studio
python -m venv .venv
source .venv/bin/activate
pip install -e ".[test]"
pytest -q
```

All 142 tests should pass before you start touching code.

## Development workflow

1. **Open an issue first** for anything larger than a bug fix or a one-line tweak. A quick "is this in scope?" thread saves everyone time.
2. **Branch from `main`** — short, descriptive names (`fix/sops-cwd`, `feat/milkshake-framework`).
3. **Write a failing test first** when adding behavior. The repo is test-heavy on purpose — the interview loop has too many moving parts to iterate blind.
4. **Keep PRs focused.** One logical change per PR. Refactors and feature work go in separate PRs.
5. **Run `pytest -q` locally** before pushing. CI will rerun it, but don't burn CI time.

## What to contribute

Good first issues:
- **New JTBD frameworks** in `src/skill_studio/interview/frameworks/` — drop a YAML file with `questions:` for each phase.
- **New exporters** in `src/skill_studio/exporters/` — implement the `Exporter` protocol, register in `registry.py`.
- **New presets** in `src/skill_studio/presets/` — YAML with weights across schema fields.
- **Better tests for the voice pipeline** — current coverage is ~32% because Pipecat services are tricky to mock.

Things we'll usually push back on:
- Adding cloud/SaaS dependencies. Local-first is a core value.
- Swapping sops for another secrets tool. The sops integration is deliberate.
- Touching `schema.py` without a plan — `design.json` is the single source of truth across text/voice/exporters and schema changes ripple everywhere.

## Code style

- Python 3.11+ only. Use `from __future__ import annotations`.
- Prefer small, pure functions. Tests mock the LLM seam (`llm.ask`), not deeper.
- No unnecessary comments. Let names carry the meaning.
- Path resolution goes through `skill_studio.paths` — never hard-code a user path.
- User-visible strings stay in English; the interview itself auto-detects language.

## Secrets and path safety

Never commit:
- Plaintext `.env*` files (the `.gitignore` guards against it, but double-check).
- Absolute paths under `/Users/...` or `/home/...` in code, tests, or docs. Use `skill_studio.paths` helpers or document the env-var override.
- Session fixtures containing real PII. Use synthetic data in tests.

## Releasing

Maintainers: tag from `main`, push the tag, CI picks it up. No pre-release channel yet.

## Code of Conduct

Be kind, be specific, assume good faith. No formal CoC document — if someone's behavior is making the project worse to work on, open an issue and we'll talk.
