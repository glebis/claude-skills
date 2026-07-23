# Brand/style controls across image-gen systems (researched mid-2026)

**Headline for the multi-reference feature:** no API exposes structured per-reference *role*
parameters ("palette from image A, composition from image B") as typed JSON fields. Role
assignment happens either (a) in natural language in the prompt referencing "the first/second
image" (Flux 2, gpt-image, Gemini/Nano Banana), or (b) via separate typed flags per role
(Midjourney `--sref` style / `--cref`/`--oref` subject / plain image URL = composition).
Only Midjourney and Recraft/Ideogram give a dedicated channel for one specific role.
**Implication:** emit typed params where they exist (color palette, style ref) and otherwise
compose a role-annotated NL prompt + ordered image array.

## Recraft (external.api.recraft.ai/v1/images/generations)

Models: `recraftv4`, `recraftv4_pro` (4MP), `recraftv4_vector`, `recraftv4_pro_vector`; V3 still up.

- **Exact hex — best-in-class.** `controls.colors`: array of RGB triples, a real palette *lock*.
  Also `controls.background_color`.
  ```json
  {"prompt":"...","style":"digital_illustration",
   "controls":{"colors":[{"rgb":[41,98,255]},{"rgb":[255,255,255]},{"rgb":[20,20,20]}]}}
  ```
- **Brand style:** `style_id` custom styles — POST brand images to `/v1/styles` with a base
  `style`, reuse the returned id per generation. Strongest no-finetune "trained brand style".
  Built-in styles: `realistic_image`, `digital_illustration`, `vector_illustration`, `icon` (+substyles).
- **Refs:** style captured via the custom-style upload (set → one style_id); no per-call per-role refs.
- **Text-in-image:** strong; can emit true SVG (`"response_format":"svg"`).
- **Pricing:** ~$0.04 raster, ~$0.08 vector, $0.25 creative upscale.
- Custom style: `curl -X POST .../v1/styles -H "Authorization: Bearer $RECRAFT_API_TOKEN" -F style=digital_illustration -F file=@brand-ref.png`
- Docs: recraft.ai/docs

## Ideogram (developer.ideogram.ai, Generate v3 / 4.0)

- **Hex:** `color_palette` = `{"name": PRESET}` or `{"members":[{"color_hex":"#RRGGBB","color_weight":0.05–1.0},…]}`
  (≤~16 colors in 4.0; a *steer*, not a lock; weights descend high→low).
- **Style:** `style_codes` (8-char hex, reusable), `style_type` AUTO/GENERAL/REALISTIC/DESIGN/FICTION,
  `style_preset` (50+). Constraint: `style_codes` can't combine with `style_reference_images` or `style_type`.
- **Refs:** `style_reference_images` — multiple, ≤10MB total, style-only channel.
- **Text-in-image:** flagship strength (best typography).
- `rendering_speed`: FLASH/TURBO/DEFAULT/QUALITY. Pricing ~ a few cents, tier-dependent.
- Docs: developer.ideogram.ai/api-reference/api-reference/generate-v3

## Flux family (fal.ai + Replicate)

FLUX.2 (32B). Endpoints: `fal-ai/flux-2-pro[/edit]`, `fal-ai/flux-2/turbo`, `fal-ai/flux-pro/kontext`,
`fal-ai/flux-lora`; Replicate `black-forest-labs/flux-2-pro`.

- **Hex:** no palette param — prompt-stated hex or a color reference image (weakest palette lock).
- **Style:** LoRA finetune is the real mechanism (`replicate/flux-pro-trainer`, `fal-ai/flux-lora`;
  fal can merge multiple LoRAs). Kontext-LoRA for character/style consistency.
- **Refs:** FLUX.2 multi-reference edit: up to ~8–10 images into one 4MP output; roles expressed in
  the NL instruction ("color scheme from the first image, layout of the second").
- **Text:** much improved in FLUX.2, a notch below Ideogram/Recraft for dense text.
- **Pricing:** FLUX.2 [pro] ~$0.03/MP (in+out), ≈$0.03 per 1024².
  ```bash
  curl https://fal.run/fal-ai/flux-2-pro/edit -H "Authorization: Key $FAL_KEY" \
   -d '{"prompt":"…palette from the first image, composition from the second","image_urls":["…","…"]}'
  ```

## Midjourney (prompt syntax only — no API)

The one system with **flag-typed role channels**:
- `--sref <url|code>` style (palette + aesthetic; no composition bleed in v7+); `--sw 0–1000` (default 100);
  `--sref random` → reusable code; needs `--sv 4|6`.
- `--cref <url>` character identity (`--cw 0–100`); `--oref`/`--ow` omni/subject ref (v7/8.1).
- `--p <code>` personalization profile.
- Plain leading image URL(s) = image prompt (composition/content).
- No exact-hex parameter. Integrate as prompt-string assembly only.

## OpenAI gpt-image (gpt-image-2 / 1.5)

- Edit endpoint: **up to 16 input images**; roles expressed in prompt text ("logo from image 1,
  palette from image 2…"). No typed role field. No palette param (prompt hex ≈ decent adherence).
- Strong long-text rendering. Billed by tokens; refs raise input cost.
- Docs: developers.openai.com/api/reference/resources/images/methods/edit

## Google Gemini image (Nano Banana 2 = gemini-3.1-flash-image-preview; Pro = gemini-3-pro-image)

- Multiple input images; identity preservation across ≤5 subjects; roles in NL prompt ordering.
- No palette field; prompt hex adherence decent. Pro = better text + creative control.
- Pricing: NB2 ~$0.067/img @1K (batch $0.034), $0.045–0.151 by resolution; Pro $0.134 (2K)–$0.24 (4K).

## Decision matrix

| System | Exact hex param | Reusable style token | Style-only ref channel | Multi-ref | Per-ref role via |
|---|---|---|---|---|---|
| Recraft V4 | ✅ `controls.colors` (lock) | ✅ `style_id` | via style upload | set→1 style | n/a |
| Ideogram 3/4 | ✅ `color_palette` (steer) | ✅ `style_codes` | ✅ `style_reference_images` | multi | style channel |
| Flux 2 | ❌ | ✅ LoRA | ❌ | ~8–10 | NL prompt |
| Midjourney | ❌ | ✅ `--sref`/`--p` | ✅ `--sref` | flags | **flag-typed** |
| gpt-image-2 | ❌ | ❌ | ❌ | ≤16 | NL prompt |
| Gemini NB2/Pro | ❌ | ❌ | ❌ | multi | NL prompt |
