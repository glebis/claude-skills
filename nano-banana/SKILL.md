---
name: nano-banana
description: This skill generates images using Google's Gemini image generation models (Nano Banana). It should be used when the user needs to create, generate, or produce images from text prompts -- for presentations, articles, concepts, illustrations, or any visual content. Default model is Nano Banana 2 (gemini-3.1-flash-image-preview). Also supports Nano Banana Pro (gemini-3-pro-image-preview) for highest quality and original Nano Banana (gemini-2.5-flash-image).
---

# Nano Banana - Gemini Image Generation

Generate images from text prompts via Google's Gemini image generation API.

## When to Use

- User requests image generation, creation, or production from a text description
- Creating illustrations or visuals for presentations, articles, or documents
- Generating concept art, mockups, diagrams, or placeholder images
- Editing existing images with text instructions

## Requirements

- `GEMINI_API_KEY` — auto-decrypted from `secrets.enc.yaml` via SOPS + age. No env var needed if sops and age key are configured. Fallback: `export GEMINI_API_KEY=...` (get from https://ai.google.dev/)

## Quick Start

Generate an image using the bundled script:

```bash
scripts/generate_image.sh "a minimalist flat illustration of a rocket" ./output.png
```

The script accepts three arguments:
1. **Prompt** (required) -- text description of the image
2. **Output path** (optional, default: `./generated_image.png`)
3. **Model** (optional, default: `gemini-3.1-flash-image-preview`)

## Models

| Model | Nano Banana Name | Use When |
|-------|-----------------|----------|
| `gemini-3.1-flash-image-preview` (default) | **Nano Banana 2** | Best instruction following, fast, most tasks |
| `gemini-3-pro-image-preview` | **Nano Banana Pro** | Highest quality, text in images, complex scenes |
| `gemini-2.5-flash-image` | **Nano Banana** (original) | Legacy, fast iteration |

## Presets

Style presets wrap your subject in a curated prompt template for consistent visual output.

```bash
scripts/generate_image.sh --list-presets           # show available presets
scripts/generate_image.sh --preset editorial "network of nodes" ./out.png
scripts/generate_image.sh --preset ink "a mountain" ./mountain.png
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

Presets are defined in `presets.yaml` -- add your own by copying the pattern.

## Workflow

### Basic Generation

1. Craft a descriptive prompt (style + subject + composition + colors)
2. Run: `scripts/generate_image.sh "prompt" ./path/to/output.png`
3. Open result: `open ./path/to/output.png`

### High-Quality Generation

For important or text-heavy images, specify the Pro model:

```bash
scripts/generate_image.sh "diagram showing..." ./diagram.png gemini-3-pro-image-preview
```

### Image Editing

To edit an existing image, use the API directly with an input image. See `references/api_reference.md` for the request format including `inlineData` with base64-encoded source image.

### Batch Generation

To generate multiple images, run the script in a loop:

```bash
for prompt in "prompt one" "prompt two" "prompt three"; do
  scripts/generate_image.sh "$prompt" "./output_$(date +%s).png"
done
```

## Prompt Tips

- Specify visual style: "photograph", "flat illustration", "watercolor", "3D render"
- Include composition: "centered", "wide shot", "white background"
- Name colors: "blue and white color scheme", "warm earth tones"
- For text rendering, use Pro model and quote exact text: 'with the text "Hello"'

See `references/api_reference.md` for comprehensive prompt engineering guidance.

## Resources

- `scripts/generate_image.sh` -- Main generation script. Handles API call, error reporting, base64 decoding, and file output.
- `references/api_reference.md` -- Full API documentation: endpoints, request/response formats, models, prompt tips, error codes.
