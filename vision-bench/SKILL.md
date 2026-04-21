---
name: vision-bench
description: Score and compare images using vision LLMs as judges. YAML-defined criteria presets for 11 use cases (text-to-image, photorealism, document OCR, charts, UI, portrait, product, scientific, invoice, alt-text, artistic style). Supports OpenAI, Anthropic, Gemini, Mistral, and OpenRouter as judge providers. Keys auto-decrypted via SOPS + age.
---

# Vision Bench — LLM Image Evaluation

Compare images by scoring them with one or more vision LLM judges against structured rubric criteria.

## Quick Start

```bash
# Install dependencies
pip install pyyaml openai anthropic mistralai

# Score a single image
python bench.py image.png --criteria photorealism --judge gemini-2.5-flash

# Compare two AI-generated images
python bench.py img_a.png img_b.png \
  --criteria text_to_image \
  --prompt "a fox in a snowy forest" \
  --judge gpt-4o

# Multi-judge consensus
python bench.py img.png \
  --criteria portrait \
  --judges gpt-4o gemini-2.5-flash claude-opus-4-5-20251022

# OpenRouter models (any vision-capable model)
python bench.py img_a.png img_b.png \
  --criteria artistic_style \
  --judges "openrouter/meta-llama/llama-4-maverick" "openrouter/mistralai/pixtral-large-2411"

# List all presets
python bench.py --list-presets

# Save report to file
python bench.py img.png --criteria chart_analysis --save report.md
```

## Presets

| Preset | Use Case |
|--------|----------|
| `text_to_image` | Compare AI image generators (Midjourney, DALL-E, Flux) |
| `photorealism` | How convincingly an image looks like a photo |
| `artistic_style` | Style consistency, composition, color harmony |
| `portrait` | AI-generated portrait quality and realism |
| `product_photo` | E-commerce product image quality |
| `document_ocr` | Document text extraction and layout understanding |
| `chart_analysis` | Chart and data visualization comprehension |
| `invoice` | Financial document field extraction accuracy |
| `ui_screenshot` | App/web screenshot understanding |
| `scientific` | Scientific/medical image accuracy |
| `alt_text` | Accessibility image description quality |

Custom criteria: pass any `.yaml` file as `--criteria path/to/my.yaml`.

## Judge Providers

| Prefix | Provider | Example |
|--------|----------|---------|
| `gpt-`, `o1`, `o3`, `o4` | OpenAI | `gpt-4o` |
| `claude-` | Anthropic | `claude-sonnet-4-5-20251022` |
| `gemini-` | Google Gemini | `gemini-2.5-flash` |
| `pixtral-`, `mistral-`, `ministral-` | Mistral | `pixtral-12b-2409` |
| `openrouter/` | OpenRouter (any model) | `openrouter/meta-llama/llama-4-maverick` |

## API Keys

Keys are loaded from `secrets.enc.yaml` (SOPS + age encrypted) with fallback to environment variables.

Supported keys: `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, `GEMINI_API_KEY`, `OPENROUTER_API_KEY`

To encrypt your own keys:
```bash
sops --config .sops.yaml --encrypt --input-type yaml --output-type yaml secrets.yaml > secrets.enc.yaml
```

## Output Formats

`--output markdown` (default) · `--output json` · `--output table`

## Files

- `bench.py` — CLI entry point
- `judge.py` — Multi-provider LLM judge logic
- `report.py` — Report generation
- `vault.py` — SOPS secrets decryption
- `criteria/` — 11 YAML preset files
- `.sops.yaml` — Age key config for encryption
- `secrets.enc.yaml` — Encrypted API keys
