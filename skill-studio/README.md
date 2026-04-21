# skill-studio

Interview-driven automation design tool. Captures *what you want to build, for whom, and why* via a coverage-driven JTBD interview (text or voice), then exports a one-page markdown spec and an SVG design map.

Fits between two sibling tools:
- **`automation-advisor`** — should I automate this?
- **`skill-studio`** — *what should this automation actually do?* ← you are here
- **`skill-creator`** — how do I package this as a skill?

## Status

- v1: text + voice interview, md + SVG exporter, session ingest — **shipping**
- v1.5: carousel / presentation / multi-target exports — planned

## Installation

```bash
git clone https://github.com/<your-org>/skill-studio.git
cd skill-studio
python -m venv .venv
source .venv/bin/activate
pip install -e ".[test]"
pytest                      # 165 passing
```

Prerequisites:
- Python 3.11+
- [`sops`](https://github.com/getsops/sops) + a registered age key (optional — the `init` wizard falls back to a plaintext 0600 dotenv if sops is unavailable)
- Voice mode only: Daily, Groq, and Deepgram API keys

## First-run setup

```bash
skill-studio init
```

Interactive wizard: checks prerequisites, picks a data home + env-file path, chooses sops vs plaintext, collects LLM and (optional) voice keys, prints the shell `export` lines, and offers to run the test suite.

For narrow key-rotation (assumes sops is already configured), skip straight to `skill-studio setup`.

## Configuration (env vars)

All paths are overridable — no hard-coded user directories.

| Variable | Default | Purpose |
|----------|---------|---------|
| `SKILL_STUDIO_HOME` | `~/.skill-studio` | Data root; sessions live under `$HOME/sessions/` |
| `SKILL_STUDIO_ENV_FILE` | `~/.env.skill-studio` | Sops-encrypted (or 0600 plaintext) provider keys |
| `SKILL_STUDIO_PIPECAT_ENV` | `~/.env.pipecat` | Voice-mode secrets (Daily / Groq / Deepgram) |
| `SKILL_STUDIO_IMPORT_ENV` | unset | Optional dotenv to import `OPENROUTER_API_KEY` from during setup |
| `SKILL_STUDIO_GROUNDWORK_ROOT` | unset | Optional groundwork root; feature disabled if unset |
| `LLM_PROVIDER` | `openrouter` | `openrouter` \| `anthropic` |
| `OPENROUTER_MODEL` | `anthropic/claude-opus-4` | Any OpenRouter model slug |
| `DEEPGRAM_VOICE` | `aura-asteria-en` | Voice-mode TTS voice |
| `SKILL_STUDIO_QUIET` | unset | Set `=1` to silence Pipecat debug logs |

## Usage

### Text mode (runs natively inside Claude Code — zero provider keys)

```
/skill-studio new --preset ai-agent --depth sprint
```

Claude Code conducts the interview via `AskUserQuestion`. The Python CLI handles state ops only (`new-session`, `apply-patch`, `next-target`, `done`) — no LLM key needed for the interview loop.

**Presets:** `ai-agent`, `life-automation`, `knowledge-work`, `custom`
**Depth modes:** `sprint` (~5–7 Q, 60% coverage), `standard` (~15–20 Q, 80%), `deep` (~25–35 Q, 92%)
**Styles:** `scenario-first` (default), `socratic`, `metaphor-first`, `form`

### Voice mode (Daily + Groq + Deepgram + OpenRouter)

```
skill-studio new --voice --preset ai-agent --depth sprint
```

Pipecat pipeline: Daily transport → Groq Whisper STT → Silero VAD → interview loop → Deepgram TTS. A Daily room is created and auto-opens in your browser. Every turn is persisted; the session auto-exports when you leave the room.

### Seed an interview from a prior transcript

If you already talked through the problem in another session, skip re-asking the basics:

```bash
skill-studio propose-from-session <claude-code-session-id>
# or
skill-studio propose-from-session --path /path/to/transcript.jsonl
# or inspect the compact bundle without calling the LLM:
skill-studio propose-from-session <id> --bundle-only
```

Two stages:
1. **Deterministic ingest** — pure regex extracts models tried, cost events, prompt changes, and pain snippets. A 50k-token transcript compresses to ~30 lines of JSON.
2. **Single LLM call** — over that compact bundle, proposes a partial DesignJSON patch with a `rationale` map citing which signals justified each field.

The proposal is **never applied automatically**. Claude Code presents it to you for approval/edits, then pipes the approved subset through `apply-patch` — the interview then continues from the next uncovered target. Typical cost savings vs. feeding the raw transcript to an LLM: 100×.

### Resume

`skill-studio new` (text or voice) **auto-resumes** the most recent session whose coverage is below its depth threshold. Explicit flags: `--resume <id>` or `--fresh`.

### Other commands

- `skill-studio list` — all sessions
- `skill-studio export <id> md-svg` — regenerate `design.md` + `design.svg`
- `skill-studio coverage <id>` — per-field confidence JSON
- `skill-studio next-target <id>` — ask-this-next hint
- `skill-studio done <id>` — export and close out
- `skill-studio init` — full first-run wizard
- `skill-studio setup` — narrow key-rotation flow (sops-only)

## Sessions

Each interview writes to `$SKILL_STUDIO_HOME/sessions/<uuid>/`:

- `design.json` — canonical schema (single source of truth)
- `transcript.md` — full Q&A log, appended per turn
- `design.md` — human-readable one-pager
- `design.svg` — one-page visual design map
- `summary.md` — LLM-synthesized "what emerged" recap (voice mode only; written on session end)

## Architecture

```
┌─────────────────────────────────────────┐
│  Claude Code (text interview)           │
│  or Pipecat pipeline (voice interview)  │
└──────────────┬──────────────────────────┘
               │ JSON patches
               ▼
┌─────────────────────────────────────────┐
│  state-ops CLI (Python)                 │
│  new-session / apply-patch /            │
│  next-target / coverage / done /        │
│  propose-from-session                   │
└──────────────┬──────────────────────────┘
               │ reads/writes
               ▼
┌─────────────────────────────────────────┐
│  design.json   (Pydantic-validated)     │
│  transcript.md                          │
└──────────────┬──────────────────────────┘
               │ render
               ▼
┌─────────────────────────────────────────┐
│  md + SVG exporter (Jinja2, assets/)    │
└─────────────────────────────────────────┘
```

**Key design choices:**
- `design.json` is the single source of truth. One schema across text/voice/ingest/exporters.
- **Coverage-driven loop:** next field picked by `weight × (1 − confidence)`; stops when the depth-mode threshold is met.
- **Narrative-arc director:** phases (Opening → Pain → Moment → Cost → After → Shape → Guardrails → Close) driven by a per-subject landing criterion rather than raw coverage.
- **JTBD frame auto-detection:** regex on transcript picks between Forces / FSE / Outcomes / Job Story; user can override.
- **Pluggable exporters** (Protocol-based): v1 ships `md-svg`. Add a file in `src/skill_studio/exporters/`, register in `registry.py`.
- **Pluggable LLM provider** (voice side): `OpenRouterProvider` (default) or `AnthropicProvider`. Text mode uses Claude Code natively.
- **Deterministic ingest** (`src/skill_studio/ingest/`): regex compresses transcripts before any LLM touches them; the proposer then makes a single targeted call.

### Groundwork integration (optional)

If `SKILL_STUDIO_GROUNDWORK_ROOT` is set and points at a directory containing a `sessions/` subdirectory, each completed voice session automatically:
1. Renders `design.md` + `design.svg` to the session folder
2. Generates a "what emerged" synthesis
3. Writes `summary.md` alongside the transcript
4. Drops a session log into `$SKILL_STUDIO_GROUNDWORK_ROOT/sessions/`

When unset, this feed is silently skipped.

## Development

```bash
pytest -q                                         # 165 tests
coverage run -m pytest && coverage report --include="src/skill_studio/*"
```

Current coverage: **82%** overall (schema / interview / exporters / ingest ≥ 89%; voice pipeline ~31% due to live-service deps that aren't unit-testable).

Layout:
```
src/skill_studio/
  cli.py             — argparse entry point
  ingest/            — deterministic transcript extractor + LLM proposer
  interview/         — coverage, director, question picker, frameworks (YAML)
  exporters/         — md-svg renderer (Protocol-based registry)
  voice/             — Pipecat pipeline (Daily → Groq → Silero VAD → Deepgram)
  paths.py           — all env-var-overridable paths
  init_wizard.py     — first-run setup
  setup.py           — key-only rotation
assets/              — Jinja templates for the md-svg exporter
references/          — schema + presets/modes docs
tests/               — 165 tests
```

See [CONTRIBUTING.md](CONTRIBUTING.md) for contribution guidelines.

## Troubleshooting

- **`preflight: missing env files`** — voice mode needs `$SKILL_STUDIO_PIPECAT_ENV` to exist. Either create the file or point the env var at your existing one: `export SKILL_STUDIO_PIPECAT_ENV=/path/to/.env.pipecat`.
- **sops "config file not found"** — encrypt/decrypt run with `cwd=path.parent` so sops locates the nearest `.sops.yaml`. Verify one exists alongside (or above) your env file.
- **Voice: no transcription after speaking** — check DEBUG logs (enabled by default; silence with `SKILL_STUDIO_QUIET=1`). Silero VAD thresholds (`min_volume=0.15`, `confidence=0.5`) can be tuned in `voice/pipecat_interview.py` for quiet mics.
- **Voice: bot speaks to empty room** — greeting is queued in `on_first_participant_joined`. Check browser mic permission.

## License

MIT — see [LICENSE](LICENSE).
