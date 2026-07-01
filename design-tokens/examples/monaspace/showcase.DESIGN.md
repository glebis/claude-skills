---
version: alpha
name: "Monaspace (showcase)"
description: "Nine-block superfamily showcase — DTCG values + a labelled composition layer."
colors:
  accent: "#BC9AFA"
  argon: "#F1E170"
  argon-dark: "#7D6E2F"
  background: "#0D1117"
  border: "#2F353C"
  canvas: "#0D1117"
  ink: "#FFFFFF"
  krypton: "#BC9AFA"
  krypton-dark: "#3B2772"
  muted: "#B7BFC8"
  neon: "#F5B8A5"
  neon-dark: "#86412E"
  panel: "#11161D"
  panel-2: "#0B0F14"
  primary: "#F5B8A5"
  radon: "#82D2CF"
  radon-dark: "#3B5E60"
  success: "#B6D162"
  text: "#FFFFFF"
  warning: "#F1E170"
  xenon: "#B6D162"
  xenon-dark: "#4D5C2A"
typography:
  body:
    fontFamily: "Monaspace Neon"
    fontSize: "16px"
    fontWeight: "300"
    lineHeight: 1.5
  caption:
    fontFamily: "Monaspace Neon"
    fontSize: "13px"
    fontWeight: "300"
    lineHeight: 1.4
  code:
    fontFamily: "Monaspace Argon"
    fontSize: "14px"
    fontWeight: "400"
    lineHeight: 1.6
  eyebrow:
    fontFamily: "Monaspace Krypton"
    fontSize: "13px"
    fontWeight: "500"
    lineHeight: 1.2
  h1:
    fontFamily: "Monaspace Xenon"
    fontSize: "64px"
    fontWeight: "700"
    lineHeight: 1.05
  h2:
    fontFamily: "Monaspace Xenon"
    fontSize: "40px"
    fontWeight: "700"
    lineHeight: 1.1
  h3:
    fontFamily: "Monaspace Xenon"
    fontSize: "32px"
    fontWeight: "700"
    lineHeight: 1.1
  lead:
    fontFamily: "Monaspace Neon"
    fontSize: "20px"
    fontWeight: "300"
    lineHeight: 1.5
rounded:
  lg: "16px"
  md: "8px"
  sm: "4px"
  xl: "24px"
spacing:
  glow-blur: "40px"
  glow-spread: "0px"
  content-max: "1080px"
  gutter: "72px"
  media-gap: "32px"
  rhythm: "96px"
  feather: "64px"
  radius: "24px"
  lg: "24px"
  md: "16px"
  sm: "8px"
  xl: "48px"
  xs: "4px"
  dot-gap: "22px"
  dot-size: "1px"
---

# Monaspace (showcase)

## Overview

Nine-block superfamily showcase — DTCG values + a labelled composition layer. (Token types without a DESIGN.md home are omitted from frontmatter: duration, fontFamily, number.)

## Colors

- **accent** (`#BC9AFA`)
- **argon** (`#F1E170`)
- **argon-dark** (`#7D6E2F`)
- **background** (`#0D1117`)
- **border** (`#2F353C`)
- **canvas** (`#0D1117`)
- **ink** (`#FFFFFF`)
- **krypton** (`#BC9AFA`)
- **krypton-dark** (`#3B2772`)
- **muted** (`#B7BFC8`)
- **neon** (`#F5B8A5`)
- **neon-dark** (`#86412E`)
- **panel** (`#11161D`)
- **panel-2** (`#0B0F14`)
- **primary** (`#F5B8A5`)
- **radon** (`#82D2CF`)
- **radon-dark** (`#3B5E60`)
- **success** (`#B6D162`)
- **text** (`#FFFFFF`)
- **warning** (`#F1E170`)
- **xenon** (`#B6D162`)
- **xenon-dark** (`#4D5C2A`)

## Typography

- **body** — Monaspace Neon 16px/1.5 300
- **caption** — Monaspace Neon 13px/1.4 300
- **code** — Monaspace Argon 14px/1.6 400
- **eyebrow** — Monaspace Krypton 13px/1.2 500
- **h1** — Monaspace Xenon 64px/1.05 700
- **h2** — Monaspace Xenon 40px/1.1 700
- **h3** — Monaspace Xenon 32px/1.1 700
- **lead** — Monaspace Neon 20px/1.5 300

## Layout

Spacing scale: glow-blur 40px, glow-spread 0px, content-max 1080px, gutter 72px, media-gap 32px, rhythm 96px, feather 64px, radius 24px, lg 24px, md 16px, sm 8px, xl 48px, xs 4px, dot-gap 22px, dot-size 1px.

## Shapes

Corner radii: lg 16px, md 8px, sm 4px, xl 24px.

---

## Composition recipes (Tier 3 — patterns, not tokens)

These are how the nine blocks *behave*. They reference token values but are not
themselves values, so they live here as prose (skill convention), not in the
`.tokens.json`. This is the line the showcase draws: **values → tokens, patterns → here.**

- **Text + illustration row.** Text takes `layout.media-split` (0.58) of the width,
  the illustration the remainder, separated by `layout.media-gap`. Recipe: text sits
  **left**, media **right**, and media may bleed off the dotted grid toward the edge.
  *(Tokenized: the ratio + gap. Prose: which side, the bleed.)*
- **Header scale.** Headers step the `type.*` scale by `scale.ratio` (1.5):
  eyebrow → caption → body → lead → h3 → h2 → h1. Pick by altitude, never by eye.
  *(Fully tokenized — this is the "how large is the header" answer.)*
- **Accent-glow treatment.** Glow = `box-shadow: 0 0 elevation.glow-blur
  elevation.glow-spread` in the **block's own accent** at `elevation.glow-opacity`.
  Each block sets `--block-accent`; the blur/spread/opacity are shared.
  *(Tokenized: blur/spread/opacity. Prose: "the colour comes from the block, not the token.")*
- **Mask treatment.** Media is masked at `mask.radius`, and full-bleed media fades
  to the canvas over `mask.feather`. Hero/404 mask media with the **wordmark
  outline**. *(Tokenized: radius + feather. Prose: the wordmark-outline mask, the edge fade.)*
- **Dotted-grid backdrop.** `radial-gradient` dots of `texture.dot-size` at
  `texture.dot-opacity`, tiled every `texture.dot-gap`. Toggleable per block.
- **Section rhythm.** Every block breathes `layout.rhythm` top and bottom, divided
  by a `color.border` hairline.
- **Motion.** Hover/flash = `motion.fast`, state changes = `motion.base`,
  texture-healing morph = `motion.slow`. *(Easing curve is prose — not a v1 token type.)*
- **Syntax → family map.** In code samples, roles map to families/accents:
  keyword → krypton, function → radon, string → xenon, number → neon, comment → muted.
  *(The families/colours are tokens; the mapping is the recipe.)*
