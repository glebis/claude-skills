---
name: present
description: Generate interactive HTML presentations with professional ElevenLabs voiceover narration synced to slides. Supports dual article/slides mode, scroll-reveal animations, GPT Image 2 illustrations, and configurable detail levels. Use this skill when the user wants to create a presentation, slide deck, narrated briefing, research report with voiceover, or any content that should be presentable as both a readable article and a navigable slide deck. Also triggers on "make a presentation", "create slides", "present this", "narrated deck", "voiceover slides", "briefing with audio", or requests to turn research/notes into a shareable presentation. Works with any content — research findings, meeting summaries, proposals, educational material.
---

# Present — Narrated Interactive Presentations

Generate a self-contained HTML presentation with dual article/slides mode, ElevenLabs narration, optional GPT Image 2 illustrations, and scroll-reveal animations.

## What This Skill Produces

A single `index.html` file (plus audio and optional image assets) that can be:
- Opened locally in a browser
- Deployed to Vercel, Netlify, or any static host
- Shared as a folder

The output has two modes the viewer can toggle between:
1. **Article mode** — long-form scrollable report with Tufte-inspired typography
2. **Slides mode** — navigable presentation with keyboard/click navigation and narrated audio playback

## Quick Start

```
/present "AI adoption research for Arseny" --slides 12 --voice daniel --images risograph
```

Or with a file:
```
/present path/to/research.md --detail detailed --voice alice
```

## Parameters

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

### Detail Levels

- **`executive`** (5-7 slides): Key findings only. One stat slide, one recommendation slide, sources. Best for busy stakeholders who need the bottom line.
- **`standard`** (10-14 slides): Full narrative arc. Problem, evidence, analysis, recommendations, sources. The default for most presentations.
- **`detailed`** (15-20 slides): Deep dive. Includes methodology, multiple evidence sections, case studies, detailed recommendations with implementation steps.

### Voice Options

Uses ElevenLabs API. The key must be available in `~/claude-skills/elevenlabs-tts/.env` as `ELEVENLABS_API_KEY`.

Recommended voices for presentations:
- **daniel** — Steady Broadcaster, British, formal (default)
- **alice** — Clear Educator, British, professional
- **matilda** — Knowledgeable, American, upbeat
- **brian** — Deep Resonant, American, comforting
- **george** — Warm Storyteller, British, mature

### Image Styles

When `--images` is set, the skill generates illustrations for key slides using GPT Image 2 (`~/.claude/skills/gpt-image-2/scripts/gpt_image_2.py`). Available styles:

- `risograph` — Gerd Arntz isotype style, muted colors, sand texture
- `editorial` — Magazine photography style, dramatic lighting
- `blueprint` — Technical drawing aesthetic, white on blue
- `ink` — Black ink illustration, hand-drawn feel
- `constellation` — Data visualization aesthetic, dots and lines
- Custom: pass `--image-prompt "your style description"` to override

Images are generated in `--draft` mode first (~$0.006/image). The skill decides which slides benefit from illustration (typically 3-5 out of 12).

## Workflow

### Step 1: Content Analysis

Read the input content (a topic description, a markdown file, vault notes, meeting transcript, or research). Identify:
- The core argument or narrative
- Key data points and statistics
- Natural section breaks
- Quotable findings with sources

### Step 2: Slide Planning

Based on `--detail` and `--slides`, create a slide plan. Each slide needs:

```
Slide N: [Type] — [Title]
Content: [what appears on screen]
Narration: [what the voice says — always more than what's on screen]
Read time: [seconds for an average reader to absorb the visual content]
Image: [yes/no, with prompt if yes]
```

Slide types: `title`, `summary`, `stat`, `evidence`, `comparison`, `quote`, `framework`, `recommendation`, `case-study`, `sources`

The narration script should be conversational and add context beyond what's displayed. It should NOT just read the slide text aloud — it should explain, connect, and elaborate. Target 15-30 seconds of narration per slide.

### Step 3: Generate Audio

For each slide, generate narration using ElevenLabs:

```bash
python3 ~/.claude/skills/elevenlabs-tts/scripts/elevenlabs_tts.py \
  --voice <voice_name> \
  --text "<narration>" \
  --output <output_dir>/audio/slide-<N>.mp3
```

Or use the direct API via the script at `scripts/generate_audio.py` in this skill.

Also generate a transition sound (Rhodes chord) for slide-to-slide transitions.

After generation, get durations with ffprobe to calculate slide timing.

### Step 4: Generate Images (if enabled)

For slides that benefit from illustration, generate images using GPT Image 2:

```bash
python3 ~/.claude/skills/gpt-image-2/scripts/gpt_image_2.py --draft --size 1536x1024 \
  "<style prefix> <slide-specific prompt>" \
  <output_dir>/images/<name>.png
```

Typically generate 3-5 images for a 12-slide deck. Choose slides where a visual metaphor strengthens the point — stat slides, concept slides, and the title slide are good candidates. Don't illustrate every slide.

### Step 5: Build HTML

Use the template at `assets/template.html` as the base. The template includes:

- **Typography**: EB Garamond (body) + DM Sans (labels/numbers)
- **Color palette**: Configurable via CSS variables in `:root`
- **Article mode**: Tufte-inspired layout with executive summary box, stat cards, two-column sections, data tables
- **Slides mode**: Full-viewport slides with fade transitions, keyboard navigation (arrows, space), dot indicators
- **Audio engine**: Single reusable `<audio>` element, slide-synced playback with progress bar, transition sounds between slides
- **Auto-hide controls**: Top bar (mode switcher + audio) appears when cursor enters top 20% of viewport. Bottom nav appears in bottom 20%. Shift+. toggles always-show/always-hide/zone mode.
- **Scroll-reveal animations**: Intersection Observer-based fade-up for sections, staggered stat cards, animated counters, h2 rule-draw effect
- **`prefers-reduced-motion`**: All animations disabled when user prefers reduced motion

Populate the template by replacing placeholder sections with the actual slide and article content.

### Step 6: Test

Open in browser using `/real-browser` or `open <path>`. Verify:
- [ ] Article mode renders correctly, images load
- [ ] Slides mode: all slides navigable, text fits within viewport
- [ ] Audio plays when play button is clicked
- [ ] Audio syncs to slide advancement (each slide waits for narration + read time)
- [ ] Transition sounds play between slides
- [ ] Auto-hide works for top and bottom bars
- [ ] Keyboard navigation (arrows, space) works in slide mode

### Step 7: Deploy (if requested)

If `--deploy` is set, copy output to the target project's `public/` folder and deploy:

```bash
cp -r <output_dir>/* <project_path>/public/<slug>/
cd <project_path> && vercel deploy --prod --yes
```

## HTML Architecture

### Audio Sync Model

Each slide has three timing properties:
- `data-audio="slide-name"` — maps to audio file
- `data-read-time="N"` — seconds for reading the visual content

The audio engine calculates: `slide_duration = max(audio_duration + 2s, read_time)`. After narration ends, it waits for any remaining read time, plays a transition sound (1.8s), then advances to the next slide.

### Avoiding AI-Looking Formatting

The following patterns read as AI-generated and should be avoided:
- Colored left-bar + bold heading + description blocks (finding cards)
- Large italic pull quotes with colored left border
- Uniform card grids with icon + heading + description
- Gradient text on metrics

Instead use:
- Natural prose paragraphs with inline emphasis
- Definition lists (`<dl>`) for structured points
- Tables for comparisons
- Direct statements woven into flowing text

### Image Paths

Use absolute paths from the deployment root: `/slug/images/name.png`, not relative paths. Relative paths break when URLs load without trailing slashes.

## Files

- `SKILL.md` — This file
- `scripts/generate_audio.py` — ElevenLabs TTS batch generator
- `assets/template.html` — Base HTML template with all CSS/JS
- `references/slide-types.md` — Detailed slide type specifications and examples
