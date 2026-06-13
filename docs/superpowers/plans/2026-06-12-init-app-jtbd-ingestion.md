# JTBD Ingestion Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add an optional JTBD-ingestion step to `init-tauri-app` that reads a `jtbd.json` and pre-populates the new project's product context (PRODUCT.md, an AGENTS.md product section, a guardrails checklist, and a root jtbd.json copy), with the mapping factored into reusable assets the future `init-xcode-app` can consume verbatim.

**Architecture:** New shared `assets/jtbd/` asset group (templates + mapping + fixture) plus a new optional procedure step (1.5) in SKILL.md. The skill renders the templates by substituting jtbd.json fields; ingestion is additive and fails soft (a missing/malformed artifact never aborts the scaffold).

**Tech Stack:** Claude Code skill (Markdown + template assets), JSON, bash for validation. Reference: `claude-skills/jtbd/references/superpowers_handoff.md`, schema `solopreneur-vault/references/jtbd-schema.md`.

**Spec:** `claude-skills/docs/superpowers/specs/2026-06-12-init-app-jtbd-ingestion-design.md`

**Testing note:** Content skill — verification is fixture-driven rendering, not unit tests. Template tasks validate via a small bash renderer + assertions on the output.

---

## File Structure

All new files under `~/ai_projects/claude-skills/init-tauri-app/`:

```
assets/jtbd/
  jtbd-map.md                         # field→destination mapping + rendering rules (human/agent ref)
  PRODUCT.md.template                 # full brief, {{placeholders}}
  agents-product-section.md.template  # AGENTS.md injection block
  guardrails-check.md.template        # manual pre-release checklist
  fixtures/sample-jtbd.json           # minimal valid artifact for tests
  fixtures/malformed-jtbd.json        # negative-test artifact
SKILL.md                              # +Step 1.5 (ingest), +input note (jtbd path)
scripts/render-jtbd.sh                # helper the skill/test uses to render templates from a jtbd.json
```

**Placeholder convention:** `{{field}}` for scalars; list sections use a marked block the renderer
expands per array item (documented in `jtbd-map.md`). The skill agent may also render directly when
running the procedure — `render-jtbd.sh` is the deterministic reference + test harness.

---

## Task 1: JTBD mapping reference

**Files:**
- Create: `assets/jtbd/jtbd-map.md`

- [ ] **Step 1: Write the mapping reference**

Create `assets/jtbd/jtbd-map.md` documenting exactly the spec §4 table plus rendering rules:

````markdown
# JTBD → project mapping

Shared by all `init-*` skills. Source schema: `solopreneur-vault/references/jtbd-schema.md`.

## Field → destination

| Source field(s) | Destination |
|---|---|
| `name`, `hook` | README tagline; PRODUCT.md title |
| `jtbd.{situation,motivation,outcome}` | PRODUCT.md "The Job"; AGENTS.md product section |
| `problem.{what_hurts,cost_today}` | PRODUCT.md "Problem" |
| `needs.{functional,emotional,social}` | PRODUCT.md "Needs" |
| `switch_forces.*` | PRODUCT.md "Switch forces" |
| `before_after.*` | PRODUCT.md "Before / After" |
| `scenarios[]` | PRODUCT.md "Scenarios" |
| `guardrails[]` | AGENTS.md "Must NOT do"; PRODUCT.md "Guardrails"; guardrails-check.md |
| `evidence.quotes[]` | PRODUCT.md "Evidence" |
| `open_questions[]` | PRODUCT.md "Open questions" |
| source path, `version` | PRODUCT.md + AGENTS.md footers (`Source JTBD: <path>`) |
| (whole file) | copied verbatim to project-root `jtbd.json` |

## Rendering rules
- Scalars: `{{field}}` (dotted, e.g. `{{jtbd.situation}}`).
- Arrays: a block delimited by `<!-- each:FIELD -->` ... `<!-- /each -->` containing one `{{item}}`
  line; the renderer repeats it per element. `scenarios[]` items are objects: use
  `{{item.title}}` and `{{item.vignette}}`.
- Missing optional field → render an empty string; an empty array → omit the whole `each` block.
- Required fields (`name`, `hook`, `jtbd`) — if absent, ingestion is skipped entirely (see SKILL.md 1.5).
````

- [ ] **Step 2: Verify it has no placeholders left vague**

Run: `grep -nE "TBD|TODO|FIXME" ~/ai_projects/claude-skills/init-tauri-app/assets/jtbd/jtbd-map.md`
Expected: no matches.

- [ ] **Step 3: Commit** — SKIP if the controller said no-commit; otherwise:

```bash
git -C ~/ai_projects/claude-skills add init-tauri-app/assets/jtbd/jtbd-map.md
git -C ~/ai_projects/claude-skills commit -m "feat(init-tauri-app): jtbd mapping reference"
```

---

## Task 2: Templates (PRODUCT.md, AGENTS.md section, guardrails checklist)

**Files:**
- Create: `assets/jtbd/PRODUCT.md.template`, `assets/jtbd/agents-product-section.md.template`, `assets/jtbd/guardrails-check.md.template`

- [ ] **Step 1: Create `PRODUCT.md.template`**

```markdown
# {{name}} — Product Brief

> {{hook}}

## The Job
- **When** {{jtbd.situation}}
- **I want to** {{jtbd.motivation}}
- **So I can** {{jtbd.outcome}}

## Problem
- **What hurts:** {{problem.what_hurts}}
- **Cost today:** {{problem.cost_today}}

## Needs
**Functional**
<!-- each:needs.functional -->
- {{item}}
<!-- /each -->

**Emotional**
<!-- each:needs.emotional -->
- {{item}}
<!-- /each -->

**Social**
<!-- each:needs.social -->
- {{item}}
<!-- /each -->

## Switch forces
- **Push:** {{switch_forces.push}}
- **Pull:** {{switch_forces.pull}}
- **Habit:** {{switch_forces.habit}}
- **Anxiety:** {{switch_forces.anxiety}}

## Before / After
- **Before:** {{before_after.before}}
- **After:** {{before_after.after}}

## Scenarios
<!-- each:scenarios -->
- **{{item.title}}** — {{item.vignette}}
<!-- /each -->

## Guardrails (must NOT do)
<!-- each:guardrails -->
- {{item}}
<!-- /each -->

## Evidence
<!-- each:evidence.quotes -->
- {{item}}
<!-- /each -->

## Open questions
<!-- each:open_questions -->
- {{item}}
<!-- /each -->

---
Source JTBD: {{__source_path__}} (schema v{{version}})
```

- [ ] **Step 2: Create `agents-product-section.md.template`**

```markdown
## Product context

> {{hook}}

**For** {{jtbd.situation}} — **so that** {{jtbd.outcome}}.

**Must NOT do (from JTBD guardrails):**
<!-- each:guardrails -->
- {{item}}
<!-- /each -->

Full brief: [docs/PRODUCT.md](./docs/PRODUCT.md) · Source JTBD: {{__source_path__}}
```

- [ ] **Step 3: Create `guardrails-check.md.template`**

```markdown
# Guardrails review checklist

Manual pre-release pass. One box per JTBD guardrail — confirm the release does not violate it.

<!-- each:guardrails -->
- [ ] {{item}}
<!-- /each -->

Source JTBD: {{__source_path__}}
```

- [ ] **Step 4: Verify all three templates exist and use only known placeholders**

Run:
```bash
cd ~/ai_projects/claude-skills/init-tauri-app/assets/jtbd
grep -hoE "\{\{[a-zA-Z0-9_.]+\}\}" *.template | sort -u
```
Expected: only `name`, `hook`, `jtbd.*`, `problem.*`, `needs.*`, `switch_forces.*`, `before_after.*`,
`item`, `item.title`, `item.vignette`, `version`, `__source_path__`. No unexpected tokens.

- [ ] **Step 5: Commit** — SKIP if no-commit; else `git ... -m "feat(init-tauri-app): jtbd render templates"`.

---

## Task 3: Renderer + fixtures

**Files:**
- Create: `scripts/render-jtbd.sh`, `assets/jtbd/fixtures/sample-jtbd.json`, `assets/jtbd/fixtures/malformed-jtbd.json`

- [ ] **Step 1: Create `fixtures/sample-jtbd.json`** (minimal valid artifact)

```json
{
  "name": "tidepool",
  "hook": "Capture a fleeting idea by voice and get a buildable spec before the moment fades.",
  "jtbd": {
    "situation": "a founder has an idea away from their desk",
    "motivation": "articulate it clearly enough for agents to act on",
    "outcome": "a structured spec exists within minutes, no re-explaining"
  },
  "problem": { "what_hurts": "static tools don't feed forward", "cost_today": "hours of re-explanation per project" },
  "needs": {
    "functional": ["voice-friendly capture", "structured JSON output"],
    "emotional": ["feel like talking to a sharp thinker"],
    "social": ["share a credible one-pager"]
  },
  "switch_forces": {
    "push": "the gap between idea and spec kills momentum",
    "pull": "specs that feed forward into code",
    "habit": "Figma/Docs muscle memory",
    "anxiety": "trusting an AI-framed spec over real empathy"
  },
  "before_after": { "before": "idea lives in your head", "after": "a spec that IS the handoff" },
  "scenarios": [ { "title": "Bike commute", "vignette": "speaks the idea while riding; parks with a spec" } ],
  "guardrails": ["one project per session", "never fabricate switch forces"],
  "evidence": { "source": "interview", "quotes": ["\"I want to do it while riding the bike.\""], "weaknesses": [] },
  "open_questions": ["is /plan needed between brainstorm and code?"],
  "version": 1
}
```

- [ ] **Step 2: Create `fixtures/malformed-jtbd.json`** (negative test — missing required fields + bad JSON-ish)

```json
{ "hook": "no name or jtbd block here", "needs": { "functional": ["x"] }
```

- [ ] **Step 3: Write the renderer `scripts/render-jtbd.sh`**

```bash
#!/usr/bin/env bash
# Render a jtbd template by substituting fields from a jtbd.json.
# Usage: render-jtbd.sh <jtbd.json> <template> <source_path_label>
# Prints the rendered text to stdout. Exit 3 = invalid/missing required fields.
set -euo pipefail
JSON="$1"; TPL="$2"; SRC="${3:-$1}"
node - "$JSON" "$TPL" "$SRC" <<'NODE'
const fs = require('fs');
const [json, tpl, src] = process.argv.slice(2);
let data;
try { data = JSON.parse(fs.readFileSync(json, 'utf8')); }
catch (e) { console.error('invalid JSON'); process.exit(3); }
if (!data.name || !data.hook || !data.jtbd) { console.error('missing required fields'); process.exit(3); }
data.__source_path__ = src;
const get = (obj, path) => path.split('.').reduce((o,k)=> (o==null?undefined:o[k]), obj);
let t = fs.readFileSync(tpl, 'utf8');
// expand each-blocks
t = t.replace(/<!-- each:([\w.]+) -->\n([\s\S]*?)<!-- \/each -->\n?/g, (_, field, body) => {
  const arr = get(data, field);
  if (!Array.isArray(arr) || arr.length === 0) return '';
  return arr.map(el => body.replace(/\{\{item(?:\.([\w]+))?\}\}/g,
    (_, k) => String(k ? (el?.[k] ?? '') : el))).join('');
});
// scalars
t = t.replace(/\{\{([\w.]+)\}\}/g, (_, f) => { const v = get(data, f); return v==null ? '' : String(v); });
process.stdout.write(t);
NODE
```

- [ ] **Step 4: Render the sample against all three templates and assert content**

Run:
```bash
cd ~/ai_projects/claude-skills/init-tauri-app
chmod +x scripts/render-jtbd.sh
F=assets/jtbd/fixtures/sample-jtbd.json
bash scripts/render-jtbd.sh "$F" assets/jtbd/PRODUCT.md.template "~/jtbd/tidepool/jtbd.json" | tee /tmp/p.md | grep -q "Capture a fleeting idea" && echo HOOK_OK
grep -q "one project per session" /tmp/p.md && echo GUARDRAIL_OK
grep -q "Bike commute" /tmp/p.md && echo SCENARIO_OK
bash scripts/render-jtbd.sh "$F" assets/jtbd/agents-product-section.md.template "x" | grep -q "Must NOT do" && echo AGENTS_OK
bash scripts/render-jtbd.sh "$F" assets/jtbd/guardrails-check.md.template "x" | grep -q "\- \[ \] one project per session" && echo CHECK_OK
```
Expected: `HOOK_OK`, `GUARDRAIL_OK`, `SCENARIO_OK`, `AGENTS_OK`, `CHECK_OK`.

- [ ] **Step 5: Assert the malformed fixture fails soft (exit 3, no output)**

Run:
```bash
bash scripts/render-jtbd.sh assets/jtbd/fixtures/malformed-jtbd.json assets/jtbd/PRODUCT.md.template x; echo "exit=$?"
```
Expected: prints `invalid JSON` (or `missing required fields`) on stderr and `exit=3`.

- [ ] **Step 6: Commit** — SKIP if no-commit; else `git ... -m "feat(init-tauri-app): jtbd renderer + fixtures"`.

---

## Task 4: SKILL.md — input note + Step 1.5 (Ingest JTBD)

**Files:**
- Modify: `init-tauri-app/SKILL.md`

- [ ] **Step 1: Add the jtbd path to the inputs (Step 1)**

In "### 1. Gather inputs", append a bullet after the Modules bullet:

```markdown
- **JTBD artifact (optional):** a path to a `jtbd.json`. If not given, the skill auto-discovers
  `./jtbd.json` then `~/jtbd/<name>/jtbd.json`. See Step 1.5.
```

- [ ] **Step 2: Insert Step 1.5 between "1. Gather inputs" and "2. Scaffold base"**

```markdown
### 1.5 Ingest JTBD (optional, additive)
1. **Resolve** the artifact, first hit wins: explicit path → `./jtbd.json` → `~/jtbd/<name>/jtbd.json`.
   If none found, skip this whole step (the scaffold proceeds with empty product context — no error).
2. **Confirm:** echo the artifact's `hook` and ask the user to confirm before using it. On decline, skip.
3. **Validate:** the artifact must parse and have `name`, `hook`, `jtbd`. If not, warn and skip
   ingestion (never abort the scaffold). `render-jtbd.sh` exits 3 on invalid input — treat that as "skip".
4. **Pre-fill:** if valid, default the app name to `name` and identifier to `com.glebkalinin.<name>`
   (still confirm with the user in Step 1 if not already chosen).
5. The artifacts are written during Step 3 (core layer) — see the JTBD block there.
```

- [ ] **Step 3: Add the JTBD render block to "3. Apply core layer"**

After the core file-copy table in Step 3, add:

```markdown
**If a JTBD artifact was confirmed in Step 1.5, also:**
- Render `assets/jtbd/PRODUCT.md.template` → `docs/PRODUCT.md` via
  `scripts/render-jtbd.sh <artifact> assets/jtbd/PRODUCT.md.template <artifact-path>`.
- Render `assets/jtbd/guardrails-check.md.template` → `docs/internal/guardrails-check.md`.
- Render `assets/jtbd/agents-product-section.md.template` and **insert it into `AGENTS.md`
  immediately after the first heading** (so product context leads the file).
- Copy the artifact verbatim to project-root `jtbd.json` (never modify the source).
- Field→destination details: `assets/jtbd/jtbd-map.md`.
```

- [ ] **Step 4: Verify SKILL.md is coherent**

Run:
```bash
grep -nE "1\.5 Ingest JTBD|JTBD artifact \(optional\)|render-jtbd.sh" ~/ai_projects/claude-skills/init-tauri-app/SKILL.md
grep -nE "TBD|FIXME" ~/ai_projects/claude-skills/init-tauri-app/SKILL.md || true
```
Expected: the three anchors present; no `TBD`/`FIXME`.

- [ ] **Step 5: Commit** — SKIP if no-commit; else `git ... -m "feat(init-tauri-app): jtbd ingestion step in SKILL.md"`.

---

## Task 5: End-to-end ingestion smoke

**Files:**
- Create: `init-tauri-app/scripts/smoke-jtbd.sh` (test harness; not shipped to scaffolded projects)

- [ ] **Step 1: Write the harness**

```bash
#!/usr/bin/env bash
# Verifies JTBD ingestion renders the right artifacts into a throwaway project dir.
set -euo pipefail
SKILL=~/ai_projects/claude-skills/init-tauri-app
TMP="$(mktemp -d)"; cd "$TMP"
mkdir -p proj/docs/internal proj/.claude
printf '# proj\n\nA Tauri app.\n' > proj/AGENTS.md   # stand-in for the core AGENTS.md
F="$SKILL/assets/jtbd/fixtures/sample-jtbd.json"
bash "$SKILL/scripts/render-jtbd.sh" "$F" "$SKILL/assets/jtbd/PRODUCT.md.template" "$F" > proj/docs/PRODUCT.md
bash "$SKILL/scripts/render-jtbd.sh" "$F" "$SKILL/assets/jtbd/guardrails-check.md.template" "$F" > proj/docs/internal/guardrails-check.md
SECTION="$(bash "$SKILL/scripts/render-jtbd.sh" "$F" "$SKILL/assets/jtbd/agents-product-section.md.template" "$F")"
# insert after first heading
awk -v s="$SECTION" 'NR==1{print; print ""; print s; next} {print}' proj/AGENTS.md > proj/AGENTS.md.new && mv proj/AGENTS.md.new proj/AGENTS.md
cp "$F" proj/jtbd.json
# assertions
grep -q "Capture a fleeting idea" proj/docs/PRODUCT.md
grep -q "Must NOT do" proj/AGENTS.md
grep -q "one project per session" proj/docs/internal/guardrails-check.md
test -f proj/jtbd.json
echo "JTBD_SMOKE_PASS dir=$TMP"
```

- [ ] **Step 2: Run it**

Run: `bash ~/ai_projects/claude-skills/init-tauri-app/scripts/smoke-jtbd.sh`
Expected: `JTBD_SMOKE_PASS dir=...`.

- [ ] **Step 3: Clean up the temp dir**

Use `trash` (per user rule) on the printed dir; do not `rm`.

- [ ] **Step 4: Commit** — SKIP if no-commit; else `git ... -m "test(init-tauri-app): jtbd ingestion smoke"`.

---

## Self-Review

**Spec coverage:** §2 source contract → Task 1 map + Task 3 fixture. §3.1 resolve/confirm + §3.2
validate + §3.3 pre-fill → Task 4 Step 1.5. §4 mapping + four outputs → Task 2 templates + Task 3
renderer + Task 4 Step 3 (render block). §5 reusable assets (`assets/jtbd/*`) → Tasks 1-3 (all under
`assets/jtbd/`, skill-agnostic; only the AGENTS.md insertion point is named in SKILL.md). §6 error
handling (fail soft, exit 3, never mutate source) → Task 3 renderer + Task 4 Step 1.5 + Task 5 copy.
§7 testing (fixture + smoke + negative) → Task 3 Steps 4-5 + Task 5. §8 non-goals → respected (no
module inference, no /jtbd auto-run, no source mutation, checklist is manual).

**Placeholder scan:** No vague TODOs. The `{{...}}` tokens are intentional template syntax, validated
against a closed allowlist in Task 2 Step 4. The only "SKIP if no-commit" notes are explicit
controller instructions, not gaps.

**Type consistency:** Placeholder names are consistent across templates, renderer, and map:
`{{item}}`/`{{item.title}}`/`{{item.vignette}}` for arrays; `{{__source_path__}}` for the source
path everywhere; the each-block delimiters `<!-- each:FIELD -->`/`<!-- /each -->` match between
templates (Task 2) and the renderer regex (Task 3 Step 3). `render-jtbd.sh` arg order
(`<json> <template> <source>`) is identical in Task 3, Task 4, and Task 5.
