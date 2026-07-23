---
version: alpha
name: "GSAP"
description: "Dark-canvas motion-library design language: cream type on near-black, five discipline hues, outlined-only controls."
colors:
  accent: "#fec5fb"
  background: "#0e100f"
  blue: "#00bae2"
  border: "#42433d"
  just-black: "#0e100f"
  light-green: "#abff84"
  lilac: "#9d95ff"
  muted: "#7c7c6f"
  off-black: "#191919"
  orangey: "#ff8709"
  pink: "#fec5fb"
  primary: "#0ae448"
  shockingly-green: "#0ae448"
  surface-25: "#42433d"
  surface-50: "#7c7c6f"
  surface-cream: "#fffce1"
  text: "#fffce1"
typography:
  body:
    fontFamily: "Mori"
    fontSize: "19px"
    fontWeight: "400"
    lineHeight: 1.15
  body-lg:
    fontFamily: "Mori"
    fontSize: "23px"
    fontWeight: "400"
    lineHeight: 1.38
    letterSpacing: "-0.23px"
  body-sm:
    fontFamily: "Mori"
    fontSize: "16px"
    fontWeight: "400"
    lineHeight: 1.15
  caption:
    fontFamily: "Mori"
    fontSize: "14px"
    fontWeight: "400"
    lineHeight: 1.4
    letterSpacing: "-0.14px"
  display:
    fontFamily: "Mori"
    fontSize: "224px"
    fontWeight: "600"
    lineHeight: 0.9
    letterSpacing: "-4.48px"
  heading:
    fontFamily: "Mori"
    fontSize: "66px"
    fontWeight: "600"
    lineHeight: 1.2
    letterSpacing: "-0.66px"
  heading-lg:
    fontFamily: "Mori"
    fontSize: "101px"
    fontWeight: "600"
    lineHeight: 1
    letterSpacing: "-1.11px"
  heading-sm:
    fontFamily: "Mori"
    fontSize: "44px"
    fontWeight: "600"
    lineHeight: 1.2
    letterSpacing: "-0.44px"
  subheading:
    fontFamily: "Mori"
    fontSize: "34px"
    fontWeight: "600"
    lineHeight: 1.2
    letterSpacing: "-0.34px"
rounded:
  button: "100px"
  card: "8px"
  pill: "9999px"
spacing:
  2xl: "76px"
  3xl: "96px"
  4xl: "108px"
  lg: "24px"
  md: "16px"
  sm: "12px"
  xl: "32px"
  xs: "8px"
---

# GSAP

## Overview

Dark-canvas motion-library design language: cream type on near-black, five discipline hues, outlined-only controls. (Token types without a DESIGN.md home are omitted from frontmatter: duration, fontFamily.)

## Colors

| Name | Value | Token | Role |
|---|---|---|---|
| accent | `#fec5fb` | `--color-accent` | — |
| background | `#0e100f` | `--color-background` | — |
| blue | `#00bae2` | `--color-blue` | UI category label and cool gradient endpoints |
| border | `#42433d` | `--color-border` | — |
| just-black | `#0e100f` | `--color-just-black` | Page canvas, footer surface, deep section backgrounds |
| light-green | `#abff84` | `--color-light-green` | Light green gradient endpoint and 'Other' category label |
| lilac | `#9d95ff` | `--color-lilac` | Text category label and thin illustrative strokes |
| muted | `#7c7c6f` | `--color-muted` | — |
| off-black | `#191919` | `--color-off-black` | Nested panels and code blocks, one step above the canvas |
| orangey | `#ff8709` | `--color-orangey` | SVG category label and orange-tool icon fills |
| pink | `#fec5fb` | `--color-pink` | Scroll category label and decorative splashes |
| primary | `#0ae448` | `--color-primary` | — |
| shockingly-green | `#0ae448` | `--color-shockingly-green` | GSAP brand green: links, tags, gradient-stroke CTA. Never a filled CTA color |
| surface-25 | `#42433d` | `--color-surface-25` | Hairline borders and dividers against the black canvas |
| surface-50 | `#7c7c6f` | `--color-surface-50` | Muted secondary text, icon fills at rest, disabled labels |
| surface-cream | `#fffce1` | `--color-surface-cream` | Primary text, outlined button borders, nav links; the default light used for ghost controls and headings |
| text | `#fffce1` | `--color-text` | — |

## Typography

| Role | Family | Size | Weight | Line Height | Letter Spacing |
|---|---|---|---|---|---|
| body | Mori | 19px | 400 | 1.15 | — |
| body-lg | Mori | 23px | 400 | 1.38 | -0.23px |
| body-sm | Mori | 16px | 400 | 1.15 | — |
| caption | Mori | 14px | 400 | 1.4 | -0.14px |
| display | Mori | 224px | 600 | 0.9 | -4.48px |
| heading | Mori | 66px | 600 | 1.2 | -0.66px |
| heading-lg | Mori | 101px | 600 | 1 | -1.11px |
| heading-sm | Mori | 44px | 600 | 1.2 | -0.44px |
| subheading | Mori | 34px | 600 | 1.2 | -0.34px |

## Spacing

| Name | Value | Token |
|---|---|---|
| 2xl | 76px | `--space-2xl` |
| 3xl | 96px | `--space-3xl` |
| 4xl | 108px | `--space-4xl` |
| lg | 24px | `--space-lg` |
| md | 16px | `--space-md` |
| sm | 12px | `--space-sm` |
| xl | 32px | `--space-xl` |
| xs | 8px | `--space-xs` |

## Border Radius

| Name | Value |
|---|---|
| button | 100px |
| card | 8px |
| pill | 9999px |

## Motion

| Name | Value | Token | Role |
|---|---|---|---|
| hero | 1200ms | `--motion-hero` | Display-type entrances and gradient blob drifts on the hero |
| micro | 200ms | `--motion-micro` | Hover states on pills and nav links; opacity/border shifts only |
| reveal | 600ms | `--motion-reveal` | Default entrance for cards and copy blocks scrolling into view |
| stagger | 80ms | `--motion-stagger` | Per-item offset for staggered lists, chars, and card grids |

> Note: sections below the token tables extend the Google-Labs DESIGN.md alpha format (skill convention). The YAML frontmatter above remains standard.

## Essence

An animated chalkboard in a design studio: near-black wall, warm cream chalk, and five color-coded highlighters — one per animation discipline (green GSAP, orange SVG, pink Scroll, violet Text, blue UI). Color functions as taxonomy, not decoration; typography is the hero.

## Components

### Outlined Cream Pill Button
**Role:** Default interactive control

Transparent fill, 1px #fffce1 border, 100px radius, 15px/24px padding, Mori 18px 600. Never filled with color.

### Category Color Label
**Role:** Discipline taxonomy anchor

Single word in its discipline hue: Scroll #fec5fb, SVG #ff8709, Text #9d95ff, UI #00bae2, GSAP #0ae448. Never reuse a hue for a different discipline.

### Curly-Bracket Annotation
**Role:** Section eyebrow signature

16–19px Mori 400 cream text wrapped in literal `{ }` braces. No background, no border.

## Animation Recipes

### Hero Type Reveal
**Role:** Landing display headline entrance

Split the 224px headline into chars; rise from 100% y-offset with rotation settling to 0.

```js
gsap.from(SplitText.create("h1", { type: "chars" }).chars, {
  yPercent: 100, rotation: 6, opacity: 0,
  duration: 1.2,               // motion.hero
  stagger: 0.08,               // motion.stagger
  ease: "expo.out"
});
```

### Scroll Section Reveal
**Role:** Default entrance for cards and copy scrolling into view

Fade-up on enter, once, no scrub — content must settle fast.

```js
gsap.from(".card", {
  y: 40, opacity: 0,
  duration: 0.6,               // motion.reveal
  stagger: 0.08,
  ease: "power2.out",
  scrollTrigger: { trigger: ".cards", start: "top 80%" }
});
```

### Gradient Blob Drift
**Role:** Ambient motion on hero illustrations

Slow, endless, organic — never synchronized with user input.

```js
gsap.to(".blob", {
  x: "+=30", y: "-=20", rotation: 8,
  duration: 6, yoyo: true, repeat: -1,
  ease: "sine.inOut"
});
```

### Pill Hover
**Role:** Micro-interaction on outlined buttons

Border opacity shift only — no fill, no scale beyond 1.02.

```js
button.addEventListener("mouseenter", () =>
  gsap.to(button, { borderColor: "rgba(255,252,225,0.8)",
    scale: 1.02, duration: 0.2, ease: "power1.out" })  // motion.micro
);
```

### Pinned Tool Showcase
**Role:** Scroll-driven walkthrough of the four discipline blocks

Pin the section and scrub a timeline that swaps discipline labels/hues.

```js
gsap.timeline({
  scrollTrigger: { trigger: ".tools", pin: true, scrub: 1, end: "+=3000" }
})
  .to(".label--scroll", { color: "#fec5fb" })
  .to(".label--svg",    { color: "#ff8709" })
  .to(".label--text",   { color: "#9d95ff" })
  .to(".label--ui",     { color: "#00bae2" });
```

## Do's and Don'ts

### Do

- Use the five-discipline color mapping for every category label
- Render every button as a 100px-radius ghost pill with a 1px cream border
- Introduce every section with a `{ }` curly-bracket annotation
- Let the hero headline bleed to the viewport edge at lh 0.9

### Don't

- Don't add filled CTA buttons — outlined-only system
- Don't use pure #ffffff text or #000000 background
- Don't apply drop shadows — depth comes from gradients and surface steps
- Don't scrub entrance animations — reveals fire once and settle

## Surfaces

| Level | Name | Value | Purpose |
|---|---|---|---|
| 0 | Canvas | `#0e100f` | Page background, single dark stage |
| 1 | Nested Panel | `#191919` | Footer and code blocks, one step lifted |
| 2 | Cream Surface | `#fffce1` | Rare light callout cards |

## Elevation

- **cards:** `none — separation via 8px radius and 24px gaps, not box-shadow`
- **illustrations:** `none — depth from internal multi-stop gradients`

## Imagery

Soft 3D organic shapes — pills, domes, liquid blobs — lit from within by multi-stop gradients in the discipline accent colors, loosely contained and overlapping adjacent type. No photography, no drop shadows.

## Layout

Full-bleed dark canvas, ~1280px content max-width, 80–120px section gaps. Repeating section pattern: curly-bracket eyebrow, then a centered headline or a two-column row (organic illustration left, category label + subhead + body + pill button right), separated by 1px #42433d hairlines.

## Similar Brands

- **Framer** — single dark canvas, massive display type, ghost controls
- **Linear** — dark UI with category-level color coding
- **Spline** — soft 3D organic shapes lit by internal gradients

## Quick Start

### CSS Custom Properties

```css
:root {
  --color-accent: #fec5fb;
  --color-background: #0e100f;
  --color-blue: #00bae2;
  --color-border: #42433d;
  --color-just-black: #0e100f;
  --color-light-green: #abff84;
  --color-lilac: #9d95ff;
  --color-muted: #7c7c6f;
  --color-off-black: #191919;
  --color-orangey: #ff8709;
  --color-pink: #fec5fb;
  --color-primary: #0ae448;
  --color-shockingly-green: #0ae448;
  --color-surface-25: #42433d;
  --color-surface-50: #7c7c6f;
  --color-surface-cream: #fffce1;
  --color-text: #fffce1;
  --font-mori: Mori, Inter Tight, DM Sans, sans-serif;
  --motion-hero: 1200ms;
  --motion-micro: 200ms;
  --motion-reveal: 600ms;
  --motion-stagger: 80ms;
  --radius-button: 100px;
  --radius-card: 8px;
  --radius-pill: 9999px;
  --space-2xl: 76px;
  --space-3xl: 96px;
  --space-4xl: 108px;
  --space-lg: 24px;
  --space-md: 16px;
  --space-sm: 12px;
  --space-xl: 32px;
  --space-xs: 8px;
  --type-body-font-family: Mori;
  --type-body-font-size: 19px;
  --type-body-font-weight: 400;
  --type-body-line-height: 1.15;
  --type-body-lg-font-family: Mori;
  --type-body-lg-font-size: 23px;
  --type-body-lg-font-weight: 400;
  --type-body-lg-line-height: 1.38;
  --type-body-sm-font-family: Mori;
  --type-body-sm-font-size: 16px;
  --type-body-sm-font-weight: 400;
  --type-body-sm-line-height: 1.15;
  --type-caption-font-family: Mori;
  --type-caption-font-size: 14px;
  --type-caption-font-weight: 400;
  --type-caption-line-height: 1.4;
  --type-display-font-family: Mori;
  --type-display-font-size: 224px;
  --type-display-font-weight: 600;
  --type-display-line-height: 0.9;
  --type-heading-font-family: Mori;
  --type-heading-font-size: 66px;
  --type-heading-font-weight: 600;
  --type-heading-line-height: 1.2;
  --type-heading-lg-font-family: Mori;
  --type-heading-lg-font-size: 101px;
  --type-heading-lg-font-weight: 600;
  --type-heading-lg-line-height: 1;
  --type-heading-sm-font-family: Mori;
  --type-heading-sm-font-size: 44px;
  --type-heading-sm-font-weight: 600;
  --type-heading-sm-line-height: 1.2;
  --type-subheading-font-family: Mori;
  --type-subheading-font-size: 34px;
  --type-subheading-font-weight: 600;
  --type-subheading-line-height: 1.2;
}
```
