---
name: gpt-image-2
description: Generate and edit images using OpenAI's GPT Image 2 API. Interactive skill that guides users through image creation with style presets, cost-aware draft/final workflow, thinking mode, carousels, and photo editing. This skill should be used when the user requests image generation via OpenAI/GPT Image 2, wants to create social media carousels, edit photos into artistic styles, or needs images with readable text (infographics, diagrams, posters).
---

# GPT Image 2 — Interactive Image Generation

Generate and edit images via OpenAI's GPT Image 2 API with an interactive, guided workflow.

## Interactive Flow

When the user invokes this skill, guide them through these steps using AskUserQuestion. Do not skip steps — the interactive flow is the core experience.

### Step 1: What are we making?

Ask the user what they want to create. Offer these options:

- **Single image** — one image from a text prompt
- **Photo edit** — transform an existing photo into a style
- **Carousel** — 5-10 cohesive slides for LinkedIn/Instagram
- **Variants** — multiple versions of the same concept
- **Quick generate** — skip questions, just run the prompt

If the user already provided a clear prompt (e.g. "generate an editorial image of a rocket"), skip to Step 3.

### Step 2: Style selection

Show the user available presets grouped by category. Read `presets.yaml` and present them:

**Visual styles** (no text in image):
editorial, blueprint, ink, risograph, wireframe, constellation, brutalist, grain

**Text-heavy** (leverages GPT Image 2 text rendering):
infographic, slide, diagram, poster, menu, manga

**Community favorites:**
trading-card, pixar, app-mockup, isometric, action-figure, cinematic, panorama

**Custom** — user describes their own style

Ask: "Which style? Or describe your own."

### Step 3: Platform & sizing

Ask where this will be used:
- YouTube thumbnail (1280×720)
- Instagram square (1080×1080)
- Slides/presentation (1920×1080)
- Blog hero (1200×630)
- X/Twitter (1600×900)
- Story (1080×1920)
- Custom size
- No resize (use API default)

### Step 4: Draft first, then final

**Always generate a draft first** unless the user says "skip draft" or uses `--draft false`.

1. Generate with `--draft` (quality=low, ~$0.006/image)
2. Show the image to the user using the Read tool
3. Ask: "Like this direction? I can: (a) generate final quality, (b) adjust the prompt, (c) try a different style, (d) regenerate with a new seed"
4. If approved, generate final with `--quality high` (~$0.21/image)
5. Use `--seed` from the draft to maintain composition when upgrading to final

This draft→final flow saves ~97% on iteration costs.

### Step 5: Show result and offer next actions

After generation, always:
1. Show the image using the Read tool
2. Open it with `open <path>` for full-resolution preview
3. Report the cost
4. Offer: "Want to (a) generate variants, (b) edit this further, (c) use as reference for more images, (d) done?"

## Carousel Workflow

When the user wants a carousel (5-10 slides):

### 1. Story arc
Ask: "What's the story? Give me the key message and I'll draft a 10-slide arc."

Then propose a slide-by-slide plan like:
```
Slide 1: [Cover] — hook headline + hero image
Slide 2: [Problem] — bold statement
Slide 3: [Context] — illustration + explanation
...
Slide 10: [CTA] — call to action with URL
```

Ask the user to approve or modify the plan.

### 2. Style consistency
Use the same preset + seed range across all slides. For carousels:
- Pick one visual style for all slides
- Use `--seed` to lock composition patterns
- Include pagination dots in prompts (e.g., "10 small dots at bottom, third dot highlighted orange")
- Maintain consistent color palette and typography

### 3. Draft batch
Generate all slides as drafts first ($0.006 × 10 = $0.06 total). Show them all to the user as a contact sheet or one by one. Ask which ones to regenerate or adjust.

### 4. Final batch
Only generate finals for approved slides. Offer to generate all at once with `-y` flag.

## Photo Edit Workflow

When the user wants to transform a photo:

1. Ask for the source image (file path or clipboard)
2. For clipboard: save with `osascript` to a temp file
3. Show available styles and ask which to try
4. Generate a draft edit first
5. Show result, ask if they want adjustments
6. Generate final when approved

Use `--edit <path>` for the API call.

## Cost Awareness

Always communicate costs before generating:

| Quality | Per image | 10-slide carousel |
|---------|-----------|-------------------|
| `--draft` (low) | $0.006 | $0.06 |
| medium | $0.05 | $0.50 |
| high (default) | $0.21 | $2.10 |
| high + thinking | $0.25-0.42 | $2.50-4.20 |

Thinking mode adds 20-100% cost. Only suggest it for text-heavy or complex compositions.

The script auto-confirms when cost < $0.50. Above that, it prompts the user.

## Prompt Engineering Tips

When helping users write prompts, apply these patterns:

1. **Structure**: Scene → Subject → Detail → Lighting → Constraint
2. **Front-load the subject**: put the main thing first
3. **For text in images**: quote exact text with single quotes: `'with the headline "Hello World"'`
4. **Character consistency**: maintain a 5-tuple: age + appearance + hairstyle + distinctive features + clothing
5. **Style tags at end**: append tags like `editorial-magazine`, `studio-product` to converge batches
6. **Use `--seed` for iteration**: lock composition, vary only the prompt details

## CLI Reference

```bash
# Basic generation
scripts/gpt_image_2.py "prompt" output.png

# With preset and platform
scripts/gpt_image_2.py --preset editorial --platform square "subject" out.png

# Draft mode (~$0.006/image)
scripts/gpt_image_2.py --draft "prompt" out.png

# With thinking for complex layouts
scripts/gpt_image_2.py --thinking medium --preset diagram "OAuth flow" out.png

# Seed for reproducibility
scripts/gpt_image_2.py --seed 42 "prompt" out.png

# Edit existing photo
scripts/gpt_image_2.py --edit photo.png "transform into constellation style" out.png

# Variants with contact sheet
scripts/gpt_image_2.py --n 4 --preset ink "mountain" out.png

# Cost estimate
scripts/gpt_image_2.py --estimate --n 10 --quality high "batch test"

# Skip confirmation
scripts/gpt_image_2.py -y --n 10 "batch" out.png

# Dry run (show prompt without API call)
scripts/gpt_image_2.py --dry-run --preset editorial "test" out.png
```

## Files

- `scripts/gpt_image_2.py` — main CLI (Python, requires PyYAML)
- `presets.yaml` — 21 style presets (visual + text-heavy + community)
- `platforms.yaml` — 8 platform sizing presets
- `references/api_reference.md` — full API documentation
- `~/.config/gpt-image-2/config.yaml` — user defaults
- `~/.config/gpt-image-2/history.jsonl` — generation log
- `~/.config/gpt-image-2/last.json` — last run (for `again`)
