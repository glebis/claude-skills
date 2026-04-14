---
name: nano-banana
description: Generate and edit images using Google's Gemini image generation models (Nano Banana family). Supports style presets, platform-specific sizing (YouTube/slides/blog), variants, image editing via inlineData, reference images for style transfer, and organized output with metadata. Default model is Nano Banana 2 (gemini-3.1-flash-image-preview). Key is auto-decrypted via SOPS.
---

# Nano Banana - Gemini Image Generation

Generate and edit images from text prompts via Google's Gemini image generation API.

## When to Use

- User requests image generation, creation, or production from a text description
- Editing existing images with text instructions
- Style-transfer: generate new images that match the aesthetic of a reference
- Creating illustrations for presentations, articles, thumbnails, social posts
- Batch variations of the same concept

## First-Time Setup

```bash
scripts/nano_banana.py init
```

Wizard checks dependencies (sops, age, magick), verifies the API key, and saves defaults to `~/.config/nano-banana/config.yaml`.

## Quick Start

```bash
# Simple generation
scripts/nano_banana.py "a minimalist illustration of a rocket" ./rocket.png

# With style preset
scripts/nano_banana.py --preset editorial "interconnected nodes" ./nodes.png

# YouTube thumbnail (auto-cropped to 1280x720)
scripts/nano_banana.py --preset grain --platform youtube "coffee on desk" ./thumb.png

# Generate 4 variants + contact sheet
scripts/nano_banana.py --preset wireframe "a crystal" ./crystal.png --n 4

# Edit existing image
scripts/nano_banana.py --edit ./old.png "make the background deep teal" ./new.png

# Style reference (match aesthetic of existing image)
scripts/nano_banana.py --reference ./style.png "a new mountain landscape" ./mountain.png

# Re-roll last prompt
scripts/nano_banana.py again

# View history
scripts/nano_banana.py history -n 10
```

## Requirements

- `GEMINI_API_KEY` — auto-decrypted from `secrets.enc.yaml` via SOPS + age. Fallback: `export GEMINI_API_KEY=...`
- `sops`, `age` — for key decryption
- `magick` (ImageMagick) — for platform fit + contact sheets
- `python3` with `pyyaml`

## Models

| Model | Alias | Nano Banana Name | Use When |
|-------|-------|-----------------|----------|
| `gemini-3.1-flash-image-preview` (default) | `flash` | **Nano Banana 2** | Best instruction following, fast |
| `gemini-3-pro-image-preview` | `pro` | **Nano Banana Pro** | Highest quality, text in images |
| `gemini-2.5-flash-image` | `flash-2.5` | **Nano Banana** (original) | Legacy |

Use via `--model flash|pro|flash-2.5` or full ID.

## Style Presets

```bash
scripts/nano_banana.py list-presets
scripts/nano_banana.py --preset editorial "your subject" out.png
```

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

Defined in `presets.yaml` — edit to add your own.

## Platform Presets

```bash
scripts/nano_banana.py list-platforms
scripts/nano_banana.py --platform youtube "your subject" out.png
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
`--n N` generates N variants in parallel and assembles them into a contact sheet:
```bash
scripts/nano_banana.py --preset ink "mountain" ./mt.png --n 6
# Creates mt-01.png ... mt-06.png + mt-contact.png
```

### Edit Mode
Pass an existing image and the prompt becomes the edit instruction:
```bash
scripts/nano_banana.py --edit ./thumb.png "remove the watermark, warmer colors" ./clean.png
```

### Reference Images (Style Anchor)
Use one or more reference images to guide the aesthetic without editing them:
```bash
scripts/nano_banana.py --reference ./episode1.png --reference ./episode2.png \
  "episode 3: data drift" ./ep3.png
```

### Projects + Metadata
Organize outputs by project:
```bash
scripts/nano_banana.py --project lab-04/meeting-02 --preset editorial "MCP loops" ./overlay.png
# Saves to ~/nano-banana/outputs/lab-04/meeting-02/20260414-<subject>.png + .json sidecar
```

### Re-roll + History
```bash
scripts/nano_banana.py again              # rerun last prompt
scripts/nano_banana.py history -n 20      # show last 20 generations
scripts/nano_banana.py history --project lab-04
```

### Dry Run
Preview the composed prompt without calling the API:
```bash
scripts/nano_banana.py --preset editorial --platform youtube "subject" --dry-run
```

## Transient Errors & Retry

The API occasionally returns `500/INTERNAL` or empty candidates. The script retries up to 4 times with exponential backoff (2s, 4s, 8s, 16s). Permanent errors (4xx, safety violations) fail fast without retry.

## Prompt Tips

- Specify visual style: "photograph", "flat illustration", "watercolor", "3D render"
- Include composition: "centered", "white background", "wide shot"
- Name colors: "blue and white color scheme", "warm earth tones"
- For text rendering, use `--model pro` and quote exact text: `'with the text "Hello"'`

See `references/api_reference.md` for full API documentation.

## Files

- `scripts/nano_banana.py` — main CLI (Python)
- `scripts/generate_image.sh` — thin bash wrapper (back-compat)
- `presets.yaml` — style presets
- `platforms.yaml` — platform sizing presets
- `secrets.enc.yaml` — encrypted API key (SOPS + age)
- `~/.config/nano-banana/config.yaml` — user defaults (from `init`)
- `~/.config/nano-banana/history.jsonl` — generation log
- `~/.config/nano-banana/last.json` — last run (for `again`)
