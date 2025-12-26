---
name: brand-agency
description: Applies Agency brand colors and typography to artifacts including presentations, SVG graphics, documents, and web interfaces. This skill should be used when brand colors, visual formatting, neobrutalism style, or Agency design standards apply. Keywords - branding, corporate identity, visual identity, styling, brand colors, typography, visual formatting, visual design, neobrutalism.
---

# Agency Brand Styling

## Overview

To access Agency's official brand identity and style resources, use this skill. The style is based on neobrutalism aesthetic with bold colors, hard shadows, and strong typography.

## Brand Guidelines

### Colors

**Main Colors:**

- Background Light: `#ffffff` - Light backgrounds
- Foreground Dark: `#000000` - Primary text and dark elements
- Muted: `#e5e5e5` - Subtle backgrounds, secondary elements

**Primary Palette:**

- Primary (Orange): `#e85d04` - Main accent, CTAs, highlights
- Secondary (Yellow): `#ffd60a` - Secondary accent, warnings, attention
- Accent (Blue): `#3a86ff` - Links, interactive elements, info

**Chart/Extended Colors:**

- Chart Green: `#38b000` - Success states, positive indicators
- Chart Red: `#d62828` - Error states, destructive actions

### Typography

**Font Stack:**

- **Headings**: Geist ExtraBold (weight 800), fallback: Arial
- **Body Text**: EB Garamond, fallback: Georgia
- **Monospace/Code**: Geist Mono, fallback: Courier New

**Google Fonts Import:**
```css
@import url('https://fonts.googleapis.com/css2?family=EB+Garamond:ital,wght@0,400;0,500;0,600;1,400&family=Geist:wght@800&family=Geist+Mono:wght@400;500&display=swap');
```

**CSS Variables:**
```css
:root {
  --font-body: 'EB Garamond', Georgia, serif;
  --font-heading: 'Geist', Arial, sans-serif;
  --font-mono: 'Geist Mono', 'Courier New', monospace;
}
```

### Neobrutalism Style

**Shadows:**
- Hard shadow offset: `4px 4px 0px 0px #000000`
- No blur (stdDeviation: 0)
- CSS: `box-shadow: 4px 4px 0px 0px #000000;`
- SVG filter: `<feDropShadow dx="4" dy="4" stdDeviation="0" flood-color="#000000"/>`

**Borders:**
- Width: 3px
- Color: `#000000`
- Style: solid
- Border radius: 0 (no rounded corners)

**Key Principles:**
- High contrast between elements
- Bold, saturated colors
- No gradients (flat colors only)
- Strong black outlines
- Offset hard shadows
- Zero border radius

## Application Guidelines

### SVG Graphics

To create SVG in Agency brand style:

```xml
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 400 400">
  <defs>
    <filter id="shadow" x="-20%" y="-20%" width="150%" height="150%">
      <feDropShadow dx="4" dy="4" stdDeviation="0" flood-color="#000000" flood-opacity="1"/>
    </filter>
  </defs>

  <circle cx="200" cy="200" r="80"
    fill="#e85d04"
    stroke="#000000"
    stroke-width="3"
    filter="url(#shadow)"/>
</svg>
```

### Presentations (Marp/PowerPoint)

**Slide backgrounds by type:**
- Title slides: Primary Orange `#e85d04`
- Content slides: Light `#ffffff` or Muted `#e5e5e5`
- Accent slides: Secondary Yellow `#ffd60a`, Accent Blue `#3a86ff`
- Dark slides: Foreground `#000000`

**Text colors:**
- On light backgrounds: `#000000`
- On dark/colored backgrounds: `#ffffff`

### Web/HTML

```css
:root {
  /* Colors */
  --color-background: #ffffff;
  --color-foreground: #000000;
  --color-primary: #e85d04;
  --color-secondary: #ffd60a;
  --color-accent: #3a86ff;
  --color-success: #38b000;
  --color-error: #d62828;
  --color-muted: #e5e5e5;

  /* Typography */
  --font-body: 'EB Garamond', Georgia, serif;
  --font-heading: 'Geist', Arial, sans-serif;
  --font-mono: 'Geist Mono', 'Courier New', monospace;

  /* Shadows */
  --shadow: 4px 4px 0px 0px #000000;
  --shadow-sm: 2px 2px 0px 0px #000000;
}

/* Headings */
h1, h2, h3, h4, h5, h6 {
  font-family: var(--font-heading);
  font-weight: 800;
}

/* Body */
body {
  font-family: var(--font-body);
  color: var(--color-foreground);
  background: var(--color-background);
}

/* Buttons */
.btn {
  background: var(--color-primary);
  color: white;
  border: 3px solid var(--color-foreground);
  box-shadow: var(--shadow);
  border-radius: 0;
  font-family: var(--font-heading);
  font-weight: 800;
}

/* Cards */
.card {
  background: var(--color-background);
  border: 3px solid var(--color-foreground);
  box-shadow: var(--shadow);
  border-radius: 0;
}

/* Code */
code, pre {
  font-family: var(--font-mono);
  background: var(--color-foreground);
  color: white;
  border: 3px solid var(--color-foreground);
}
```

## Color Usage Quick Reference

| Context | Color | Hex |
|---------|-------|-----|
| Primary action | Orange | `#e85d04` |
| Secondary action | Yellow | `#ffd60a` |
| Links/Info | Blue | `#3a86ff` |
| Success | Green | `#38b000` |
| Error/Danger | Red | `#d62828` |
| Text (light bg) | Black | `#000000` |
| Text (dark bg) | White | `#ffffff` |
| Muted/Disabled | Gray | `#e5e5e5` |

## Assets

**Logo:** `assets/logo.svg` - Agency logo in neobrutalism style (terminal window with code symbols and geometric shapes)

## Social Media Templates

ASCII-art style HTML templates for social media using Geist Mono font. Render to PNG using Playwright.

### Available Templates

| Template | Size | Platform |
|----------|------|----------|
| `instagram/story-announcement` | 1080x1920 | IG Story |
| `instagram/story-quote` | 1080x1920 | IG Story |
| `instagram/post-title` | 1080x1350 | IG Post |
| `instagram/post-tips` | 1080x1350 | IG Post |
| `instagram/post-event` | 1080x1350 | IG Post |
| `youtube/thumbnail` | 1280x720 | YT Thumbnail |
| `youtube/shorts-cover` | 1080x1920 | YT Shorts |
| `social/cover-banner` | 1584x396 | LinkedIn/FB |
| `social/tiktok` | 1080x1920 | TikTok |
| `social/twitter-post` | 1200x675 | X/Twitter |
| `social/pinterest-pin` | 1000x1500 | Pinterest |

### Usage

```bash
# Render all templates
node scripts/render-templates.js

# Render specific template
node scripts/render-templates.js --template instagram/story-announcement

# Custom output path
node scripts/render-templates.js -t youtube/thumbnail -o my-thumbnail.png

# List available templates
node scripts/render-templates.js --list
```

### ASCII Style Elements

Templates use ASCII box-drawing characters for decoration:

```
Frames:   ┌─────┐  ╔═════╗  ┏━━━━━┓
          │     │  ║     ║  ┃     ┃
          └─────┘  ╚═════╝  ┗━━━━━┛

Lines:    ─ │ ═ ║ ━ ┃

Arrows:   → ← ↑ ↓ ▶ ◀ ▲ ▼

Shapes:   ● ○ ■ □ ▲ △ ★ ☆ ◆ ◇

Blocks:   █ ▓ ▒ ░
```

### Template Files

Located in: `assets/templates/`
