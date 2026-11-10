# Optional: cenno mode (panel-driven elicitation)

Run the diagnostic through cenno panels instead of chat when cenno is available and the user prefers it (or asks to "ask me in panels"). The LLM still owns the logic; cenno only collects the structured inputs, which are piped into `scripts/score_constraints.py` and `scripts/recommend_rung.py` exactly as in chat mode. If cenno isn't running, fall back to chat — never block.

Use the `cenno` skill's `ask_user` / `ask_sequence` MCP tools (preferred) or the `cenno ask` CLI. Load the cenno skill for setup/availability. Honor the cenno skill config defaults (`~/.claude/skills/cenno/config.json`).

## Control mapping (the appropriate widget per input)

| Diagnostic input | cenno control | Returns | Notes |
|---|---|---|---|
| Step 0 — goal + throughput | `text` | string | one panel; free text |
| Step 0 — "is throughput a *rate* tied to the goal?" | `confirm` | bool | gate; if no, re-ask the text |
| Step 1 — every ordinal 0–3 + `necessary_condition` / `policy_gate`, per candidate step | `a2ui` `StepScore`, one per step via `ask_sequence` | JSON object per step, keyed like the scorer | preferred; see below |
| Step 1 — fallback on older cenno: each ordinal | `choice` `["0","1","2","3"]` | the digit as a string | cast to int for the scorer |
| Step 1 — fallback on older cenno: the two flags | `confirm` | bool | per candidate step |
| Step 1 — verdict `ambiguous` → re-scope | `choice` | string | offer narrower scopes / time windows |
| Step 4 — the 7 rung facts | `confirm` ×7 via `ask_sequence` | bools | maps 1:1 to `recommend_rung.py` flags |
| Final — accept the recommended automation? | `confirm` | bool | before writing the Goal |

Batch related questions with `ask_sequence` (keeps one panel up, advances instantly, auto-fills progress dots). Only hand-roll single `ask_user` calls when the next question depends on the previous answer (e.g. skip a step's scores once it's clearly disqualified).

## Best: one `StepScore` panel per step

cenno's `StepScore` control (cenno builds after 0.4.1) scores **one** candidate step on every ordinal plus the two flags in a single panel: the decisive sensitivity question leads full width, the other four sit on an aligned 0–3 grid, and `necessary` / `policy gate` are toggle chips beside the Next button. Next stays disabled until every ordinal is scored — 0 is a real "none", never a default. Send one `StepScore` question **per step** through `ask_sequence` (all steps in one panel do not fit cenno's 560px panel; the sequence keeps one panel up and fills the progress dots).

Use the **scorer's own keys** as the dimension/flag `value`s, so each answer is already a `score_constraints.py` row minus its `name`:

```json
{"questions": [
  {"title": "Score this step (0 none · 3 high)", "flow": "question", "timeout_s": 300,
   "a2ui": [
    { "version": "v0.9", "createSurface": { "surfaceId": "main", "catalogId": "cenno:catalog/v1" } },
    { "version": "v0.9", "updateComponents": { "surfaceId": "main", "components": [
      { "id": "root", "component": "Column", "children": ["s"] },
      { "id": "s", "component": "StepScore", "step": "Audience",
        "dimensions": [
          { "value": "throughput_sensitivity", "label": "If this step were 2× faster, would throughput rise?", "decisive": true },
          { "value": "wait_before", "label": "wait before" },
          { "value": "downstream_starvation", "label": "starves next" },
          { "value": "capacity_gap", "label": "capacity gap" },
          { "value": "annoyance", "label": "annoyance" } ],
        "flags": [ { "value": "necessary_condition", "label": "necessary" },
                   { "value": "policy_gate", "label": "policy gate" } ],
        "value": { "path": "/score" }, "doneLabel": "Next",
        "selectAction": { "event": { "name": "submit-score",
          "context": { "value": { "path": "/score" }, "via": "choice" } } } }
    ] } },
    { "version": "v0.9", "updateDataModel": { "surfaceId": "main", "path": "/", "value": { "score": {} } } }
   ]},
  {"title": "Score this step (0 none · 3 high)", "a2ui": ["… same envelope, \"step\": \"Offer & landing\" …"]}
]}
```

Each entry of `answers` is JSON text for one step, in the order sent — `"{\"throughput_sensitivity\":3,\"wait_before\":2,\"downstream_starvation\":3,\"capacity_gap\":2,\"annoyance\":1,\"necessary_condition\":false,\"policy_gate\":false}"`. `JSON.parse` it, add `"name"` from the step you sent, and pipe the array to `score_constraints.py` unchanged. Fewer answers than steps means a step timed out — re-ask that step rather than scoring it as zeros. Keep labels short (≤ ~12 characters) except the decisive one; to re-open a step, seed `/score` with its prior object.

**Fallback:** a cenno build without `StepScore` (≤ 0.4.1) cannot render it and falls back to a plain prompt, so an answer that does not parse as a JSON object means "old cenno" — switch to the per-step `choice` flow below for the remaining steps. Never block on the widget.

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
