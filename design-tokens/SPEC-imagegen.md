# Spec: image-generation upgrade for /design-tokens (v2 of the prompt door)

Agreed scope (2026-07-21, interview with Gleb). Test sets: `ai-design/design.tokens.json`
and `templates/monaspace.tokens.json`. Research budget ~€5, existing OpenAI/Gemini keys only.

## Phase 1 — research (deep + tested) — DONE (references/providers.md, prompt-fidelity-notes.md)

- Docs research: Recraft, Ideogram, Flux (fal/Replicate), Midjourney, plus current
  gpt-image / Nano Banana reference-image semantics. Output: `references/providers.md`
  with parameter names, palette/style controls, per-reference-image role support, pricing.
- Tested part (existing keys only): comparative draft-quality runs on gpt-image-2 and
  nano-banana measuring **brand fidelity** — does the output actually use the token hexes,
  fonts, shape language? Try 2–3 prompt formulations (hex-in-subject vs structured
  palette clause vs style-block) per model on both test token sets. Output:
  `references/prompt-fidelity-notes.md` with the winning formulation per model.

## Phase 2 — `$extensions` brand-style tokens — DONE

- Skill convention (labelled, not DTCG): a `$extensions["community.design-tokens.brand"]`
  block at file root: mood, imagery style (photography/illustration/3d/flat…), voice,
  subject-matter dos/don'ts, negative prompt fragments.
- `brand_summary.py` picks it up; `brand_clause()` weaves it into prompts.
- Validate leniently: unknown keys warn, never fail (DTCG says tools must preserve
  `$extensions` they don't understand).

## Phase 3 — more generator targets

Extend `export_prompt.py` `_IMAGE_TARGETS` (paste-only targets have no script):
- **recraft**: API JSON body (has first-class `controls.colors` exact-palette + custom styles).
- **ideogram**: API JSON body (color palette param + style codes; best text-in-image).
- **flux**: fal.ai/Replicate request examples incl. reference/LoRA options.
- **midjourney**: paste-ready prompt lines with `--sref` / `--cref` / params.
Prompt formulation per provider comes from Phase 1 findings.

## Phase 4 — actually generate

- New CLI command `generate <file> [--target ...] [--preset ...] [--subject S] [--refs DIR]`
  that shells out to the gpt-image-2 / nano-banana skill scripts (draft quality by default,
  cost printed up front). Other providers stay prompt-only until keys exist.

## Phase 5 — multi-reference images with per-image roles — annotator + refs.json DONE (`annotate` command); provider consumption pending

- **Sidecar manifest** `refs.json` next to the images is the source of truth:
  `[{"file": "a.png", "take": ["palette", "mood"], "ignore": ["subject"], "note": "…"}]`.
  Roles vocabulary: style, palette, composition/layout, subject, texture, typography, mood.
- **HTML annotator** (generated, served like previews): single page showing ALL images,
  per-image role checkboxes + free-text note, plus voice input via Groq Whisper
  (mic → whisper-large-v3 endpoint, key via SOPS; degrade to text-only without key).
  "Save" POSTs back to the local server which writes `refs.json`. Accessible, highly
  readable, no build step (stdlib server + vanilla JS, same pattern as `serve.py`).
- Interactive fallback: when no manifest exists and no browser, Claude asks per image
  what to take and writes the manifest.
- `generate`/`prompt` consume the manifest and translate roles into each provider's
  mechanism (nano-banana `--reference`, provider-specific fields per Phase 1 research).

## Non-goals (this round)

Recraft/Ideogram/fal API keys and live tests on them; Midjourney automation;
LoRA training; video.
