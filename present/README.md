# Present

Generate interactive HTML presentations with professional voiceover narration synced to slides.

## What it does

Takes content (research, notes, a topic) and produces a self-contained HTML presentation with:

- **Dual mode** — Article (scrollable long-form) and Slides (navigable deck)
- **ElevenLabs narration** — Professional voiceover synced to slide transitions
- **GPT Image 2 illustrations** — Optional risograph/editorial/custom style images
- **Scroll-reveal animations** — Intersection Observer-based, counter animations, rule-draw effects
- **Auto-hide controls** — Zone-triggered UI (top 20% / bottom 20%), Shift+. toggle
- **Keyboard navigation** — Arrow keys, spacebar, dot indicators
- **Reduced motion** — Full `prefers-reduced-motion` support

## Usage

```
/present "Topic or content" --slides 12 --voice daniel --images risograph
```

### Parameters

| Parameter | Values | Default | Description |
|-----------|--------|---------|-------------|
| `--slides` | 5-20 | 12 | Number of slides |
| `--detail` | `executive`, `standard`, `detailed` | `standard` | Content depth |
| `--voice` | ElevenLabs voice name | `daniel` | Narrator voice |
| `--images` | style name or `none` | `none` | Image generation style |
| `--image-prompt` | custom string | auto | Override image prompt prefix |
| `--output` | path | `./presentation/` | Output directory |
| `--deploy` | vercel project or `none` | `none` | Auto-deploy target |
| `--title` | string | auto | Presentation title |
| `--no-audio` | flag | false | Skip audio generation |

### Detail levels

- **executive** (5-7 slides) — Key findings only
- **standard** (10-14 slides) — Full narrative arc
- **detailed** (15-20 slides) — Deep dive with methodology and case studies

### Voices

- `daniel` — British broadcaster (default)
- `alice` — British educator
- `matilda` — American professional
- `brian` — American, deep and resonant
- `george` — British storyteller

### Image styles

- `risograph` — Gerd Arntz isotype, muted colors, sand texture
- `editorial` — Magazine photography
- `blueprint` — Technical drawing, white on blue
- `ink` — Black ink illustration
- `constellation` — Data viz aesthetic
- Custom: `--image-prompt "your style"`

## Requirements

- ElevenLabs API key in `~/claude-skills/elevenlabs-tts/.env`
- Python `requests` library
- GPT Image 2 skill (for `--images`)
- ffprobe (for audio duration detection)

## Architecture

```
present/
├── SKILL.md              — Skill instructions
├── README.md             — This file
├── scripts/
│   └── generate_audio.py — ElevenLabs batch TTS + transition sound generator
├── assets/
│   └── template.html     — Base HTML template (CSS + JS + placeholders)
└── references/
    └── slide-types.md    — Slide type specs with HTML examples
```

### Template placeholders

The template uses these placeholders that get replaced during generation:

- `{{TITLE}}` — Page title
- `{{ARTICLE_CONTENT}}` — Full article HTML (hero + sections)
- `{{SLIDE_CONTENT}}` — All slide divs
- `{{AUDIO_BASE}}` — Path prefix for audio files
- `{{AUDIO_DURATIONS}}` — JSON object of slide-id → duration in seconds

### Audio sync model

Each slide has `data-audio` (file ID) and `data-read-time` (seconds). The engine calculates `slide_duration = max(audio_duration + 2s, read_time)`, ensuring the viewer has enough time to read even if narration finishes early.

## License

MIT
