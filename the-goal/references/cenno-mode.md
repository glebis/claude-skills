# Optional: cenno mode (panel-driven elicitation)

Run the diagnostic through cenno panels instead of chat when cenno is available and the user prefers it (or asks to "ask me in panels"). The LLM still owns the logic; cenno only collects the structured inputs, which are piped into `scripts/score_constraints.py` and `scripts/recommend_rung.py` exactly as in chat mode. If cenno isn't running, fall back to chat — never block.

Use the `cenno` skill's `ask_user` / `ask_sequence` MCP tools (preferred) or the `cenno ask` CLI. Load the cenno skill for setup/availability. Honor the cenno skill config defaults (`~/.claude/skills/cenno/config.json`).

## Control mapping (the appropriate widget per input)

| Diagnostic input | cenno control | Returns | Notes |
|---|---|---|---|
| Step 0 — goal + throughput | `text` | string | one panel; free text |
| Step 0 — "is throughput a *rate* tied to the goal?" | `confirm` | bool | gate; if no, re-ask the text |
| Step 1 — each ordinal 0–3 (sensitivity, wait, starvation, capacity, annoyance) | `choice` `["0","1","2","3"]` | the digit as a string | robust default; cast to int for the scorer |
| Step 1 — `necessary_condition`, `policy_gate` | `confirm` | bool | per candidate step |
| Step 1 — verdict `ambiguous` → re-scope | `choice` | string | offer narrower scopes / time windows |
| Step 4 — the 7 rung facts | `confirm` ×7 via `ask_sequence` | bools | maps 1:1 to `recommend_rung.py` flags |
| Final — accept the recommended automation? | `confirm` | bool | before writing the Goal |

Batch related questions with `ask_sequence` (keeps one panel up, advances instantly, auto-fills progress dots). Only hand-roll single `ask_user` calls when the next question depends on the previous answer (e.g. skip a step's scores once it's clearly disqualified).

## Best: the `ScoreMatrix` control (one panel)

If the installed cenno build has the `ScoreMatrix` catalog component, score the whole matrix in a single panel. Send a raw `a2ui` payload; the control renders stacked per-step cards (sensitivity full-width + decisive, the other four reflowing 1-col on iPhone / 2-col on Mac, plus `necessary`/`policy_gate` chips), and the Score button returns the matrix as a JSON string.

```json
{
  "title": "Score the constraint",
  "flow": "question",
  "timeout_s": 600,
  "a2ui": [
    { "version": "v0.9", "createSurface": { "surfaceId": "main", "catalogId": "cenno:catalog/v1" } },
    { "version": "v0.9", "updateComponents": { "surfaceId": "main", "components": [
      { "id": "root", "component": "ScoreMatrix",
        "steps": ["Audience", "Offer & landing", "Conversion", "Delivery", "Retention"],
        "legend": "0 none · 3 high",
        "value": { "path": "/matrix" },
        "submitAction": { "event": { "name": "submit-matrix",
          "context": { "value": { "path": "/matrix" }, "via": "choice" } } } }
    ] } },
    { "version": "v0.9", "updateDataModel": { "surfaceId": "main", "path": "/", "value": {} } }
  ]
}
```

The answer comes back as a JSON string at `/matrix`: an array of `{name, sensitivity, wait, starve, cap, annoy, necessary, policy_gate}`. Map keys to the scorer (`sensitivity→throughput_sensitivity`, `wait→wait_before`, `starve→downstream_starvation`, `cap→capacity_gap`, `annoy→annoyance`, `necessary→necessary_condition`) and pipe to `score_constraints.py`. Defaults (`dimensions`, `flags`) are built in; pass them only to override. Seed `value` with prior scores to re-open a matrix.

**Fallback:** if the build lacks `ScoreMatrix` (older cenno), the renderer drops unknown components — detect an empty/failed panel and fall back to the per-step `choice` flow below. Never block on the widget.

## Per-step scoring — fallback options (no custom control)

**Default (robust): `choice` 0–3.** For each candidate step, run an `ask_sequence` of choice questions, one per dimension:

```json
{"questions": [
  {"title": "Audience — if 2x faster, would sales/launch rise? (throughput-sensitivity)",
   "input": {"kind": "choice"}, "choices": ["0", "1", "2", "3"], "flow": "question"},
  {"title": "Audience — does work pile up / wait before it?",
   "input": {"kind": "choice"}, "choices": ["0", "1", "2", "3"]},
  {"title": "Audience — must it be adequate but already is? (necessary condition)",
   "input": {"kind": "confirm"}}
]}
```

**Nicer (custom 0–3 slider): `a2ui` Scale.** When a real slider reads better, send a rich `a2ui` payload with a `Scale` (`"min": 0, "max": 3`, endpoint labels "none"/"strongly"). See the cenno skill's "Custom scales via a2ui" section for the three-message envelope; reuse it with `min:0, max:3`.

## Assembling and running

Collect answers, cast choice strings to ints, build the scorer input, and run as usual:

```bash
echo '[{"name":"Audience","throughput_sensitivity":3,"wait_before":3,"downstream_starvation":3,"capacity_gap":3,"necessary_condition":false,"annoyance":2}, ...]' \
  | python3 scripts/score_constraints.py
```

Then for the rung, feed the seven confirmed booleans:

```bash
python3 scripts/recommend_rung.py --json '{"recurring":true,"fixed_steps":true,"unattended_timing":true}'
```

## Output data

When the user wants the result persisted (or cenno logging is on):
- Render the constraint analysis from `assets/constraint-analysis-template.md` and save to the user's drafts folder (e.g. `Claude-Drafts/YYYYMMDD-constraint-analysis-<system>.md`).
- Optionally show the final recommendation back in a cenno `confirm` panel ("Build this as a Goal?") before proceeding.
- If the cenno skill config has `log_answers: true`, the raw answers are already appended to its log file; the saved analysis is the durable artifact.
