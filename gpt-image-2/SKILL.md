---
name: gpt-image-2
description: Generate and edit images using OpenAI's GPT Image 2 API. Supports style presets (including text-heavy ones like infographic/diagram/poster), platform-specific sizing (YouTube/slides/blog), thinking mode for complex compositions, variants with contact sheets, image editing, reference images for style transfer, cost estimation, and OpenRouter support. This skill should be used when the user requests image generation via OpenAI/GPT Image 2, or when high-quality text rendering in images is needed.
---

# GPT Image 2 — OpenAI Image Generation

Generate and edit images from text prompts via OpenAI's GPT Image 2 API.

## When to Use

- User requests image generation using OpenAI or GPT Image 2
- Creating images with readable text: infographics, diagrams, posters, slides, menus
- Editing existing images with text instructions
- Style-transfer: generate new images matching an aesthetic reference
- Creating illustrations for presentations, articles, thumbnails, social posts
- Batch variations of the same concept
- When text rendering quality matters more than cost (vs. nano-banana/Gemini)

## First-Time Setup

```bash
scripts/gpt_image_2.py init
```

Wizard checks dependencies (sops, age, magick), verifies the API key, and saves defaults to `~/.config/gpt-image-2/config.yaml`.

## Quick Start

```bash
# Simple generation
scripts/gpt_image_2.py "a minimalist illustration of a rocket" ./rocket.png

# With style preset
scripts/gpt_image_2.py --preset infographic "benefits of remote work" ./info.png

# With thinking mode for complex layouts
scripts/gpt_image_2.py --thinking high --preset diagram "OAuth 2.0 flow" ./oauth.png

# YouTube thumbnail (auto-cropped to 1280x720)
scripts/gpt_image_2.py --preset grain --platform youtube "coffee on desk" ./thumb.png

# Generate 4 variants + contact sheet
scripts/gpt_image_2.py --preset editorial "a crystal" ./crystal.png --n 4

# Edit existing image
scripts/gpt_image_2.py --edit ./old.png "make the background deep teal" ./new.png

# Style reference (match aesthetic of existing image)
scripts/gpt_image_2.py --reference ./style.png "a new mountain landscape" ./mountain.png

# Cost estimate without generating
scripts/gpt_image_2.py --estimate --thinking high "complex infographic" ./out.png

# Via OpenRouter instead of OpenAI direct
scripts/gpt_image_2.py --provider openrouter "a cat in space" ./cat.png

# Re-roll last prompt
scripts/gpt_image_2.py again

# View history
scripts/gpt_image_2.py history -n 10
```

## Requirements

- `OPENAI_API_KEY` — auto-decrypted from `secrets.enc.yaml` via SOPS + age. Fallback: `export OPENAI_API_KEY=...`
- `OPENROUTER_API_KEY` — required only when using `--provider openrouter`. Same decryption chain.
- `sops`, `age` — for key decryption
- `magick` (ImageMagick) — for platform fit + contact sheets
- `python3` with `pyyaml` (`pip3 install pyyaml`)

## Thinking Mode

GPT Image 2's unique feature: the model reasons about composition before rendering.

| Level | Use When | Cost Impact |
|-------|----------|-------------|
| `off` (default) | Simple subjects, speed matters | Base cost only |
| `low` | Moderate complexity, some text | +~20% reasoning tokens |
| `medium` | Multi-element scenes, diagrams | +~50% reasoning tokens |
| `high` | Dense infographics, precise layouts | +~100% reasoning tokens |

```bash
scripts/gpt_image_2.py --thinking high "detailed infographic about climate change" ./climate.png
```

## Style Presets

```bash
scripts/gpt_image_2.py list-presets
scripts/gpt_image_2.py --preset editorial "your subject" out.png
```

### Visual Presets (aesthetic-focused)

| Preset | Style |
|--------|-------|
| `editorial` | Thin lines on black, muted palette, technical diagram feel |
| `blueprint` | White/cyan lines on dark navy, engineering drawing |
| `ink` | Japanese sumi-e ink wash, organic brushstrokes, monochrome |
| `risograph` | Flat colors, grain, terracotta + sage, zine aesthetic |
| `wireframe` | 3D wireframe mesh, glowing edges on black |
| `constellation` | Star map dots connected by faint lines, celestial |
| `brutalist` | Bold shapes, thick borders, hard shadows, flat colors |
| `grain` | Film grain photo, high ISO, warm cinematic tones |

### Text-Heavy Presets (leverage GPT Image 2's text rendering)

| Preset | Style |
|--------|-------|
| `infographic` | Data-rich visual explainer with labels, clean typography, structured layout |
| `slide` | Presentation-ready with title + subtitle, minimal background |
| `diagram` | Labeled technical diagram, boxes and arrows, clean lines |
| `poster` | Event poster with headline + details, bold typography |
| `menu` | Print-ready menu/card layout, elegant type pairing |
| `manga` | Comic panel layout with speech bubbles and SFX text |

Defined in `presets.yaml` — edit to add custom presets.

## Platform Presets

```bash
scripts/gpt_image_2.py list-platforms
scripts/gpt_image_2.py --platform youtube "your subject" out.png
```

Generated image is automatically resized + center-cropped to target dimensions.

| Platform | Size |
|----------|------|
| `youtube` | 1280×720 |
| `youtube-short` | 1080×1920 |
| `slides` | 1920×1080 |
| `blog` | 1200×630 |
| `x` | 1600×900 |
| `square` | 1080×1080 |
| `story` | 1080×1920 |
| `pinterest` | 1000×1500 |

## Features

### Variants + Contact Sheet
`--n N` generates N variants (up to 10 natively) and assembles a contact sheet:
```bash
scripts/gpt_image_2.py --preset ink "mountain" ./mt.png --n 6
# Creates mt-01.png ... mt-06.png + mt-contact.png
```

### Edit Mode
Pass an existing image and the prompt becomes the edit instruction:
```bash
scripts/gpt_image_2.py --edit ./thumb.png "remove the watermark, warmer colors" ./clean.png
```

### Reference Images (Style Anchor)
Use one or more reference images to guide the aesthetic without editing them:
```bash
scripts/gpt_image_2.py --reference ./episode1.png --reference ./episode2.png \
  "episode 3: data drift" ./ep3.png
```

### Cost Estimation
Preview estimated cost before generating (token-based pricing is complex):
```bash
scripts/gpt_image_2.py --estimate --thinking high --n 4 "complex scene" ./out.png
# Estimated cost: ~$1.52 (4 images × ~$0.38/image with high thinking)
```

### OpenRouter Support
Route through OpenRouter for unified billing or provider fallback:
```bash
scripts/gpt_image_2.py --provider openrouter "subject" ./out.png
```

### Projects + Metadata
Organize outputs by project:
```bash
scripts/gpt_image_2.py --project lab-05/meeting-01 --preset diagram "MCP loops" ./overlay.png
# Saves to ~/gpt-image-2/outputs/lab-05/meeting-01/20260423-<subject>.png + .json sidecar
```

### Re-roll + History
```bash
scripts/gpt_image_2.py again              # rerun last prompt
scripts/gpt_image_2.py history -n 20      # show last 20 generations
scripts/gpt_image_2.py history --project lab-05
```

### Dry Run
Preview the composed prompt without calling the API:
```bash
scripts/gpt_image_2.py --preset infographic --platform slides "subject" --dry-run
```

## Transient Errors & Retry

The API occasionally returns 500/502 errors. The script retries up to 4 times with exponential backoff (2s, 4s, 8s, 16s). Permanent errors (4xx, safety violations) fail fast without retry.

## Prompt Tips

- GPT Image 2 excels at text — quote exact text: `'with the headline "Hello World"'`
- Use `--thinking medium` or `high` for multi-element compositions
- Specify layout: "left-aligned title, three columns below"
- For CJK text, specify the language: "Japanese menu with items in kanji"
- For infographics, describe the data structure: "bar chart showing 5 categories"

See `references/api_reference.md` for full API documentation.

## Files

- `scripts/gpt_image_2.py` — main CLI (Python, stdlib only)
- `presets.yaml` — style presets (visual + text-heavy)
- `platforms.yaml` — platform sizing presets
- `secrets.enc.yaml` — encrypted API keys (SOPS + age)
- `~/.config/gpt-image-2/config.yaml` — user defaults (from `init`)
- `~/.config/gpt-image-2/history.jsonl` — generation log
- `~/.config/gpt-image-2/last.json` — last run (for `again`)
