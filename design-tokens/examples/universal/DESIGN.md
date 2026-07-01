# Design

Visual system for the universal content kit. Every value below resolves from a
token file (`base.tokens.json` + a theme override), exported to `paper.css`
(`:root`) and `ink.css` (`[data-theme="ink"]`). This document describes the
system; the tokens are the source of truth. Edit tokens, re-export, reload.

## Theme

Two polarities, chosen by scene, not by reflex.

- **Paper (default, light):** a reader at a desk in daylight, reading reference
  material on warm stock. Light, ruled, serif, restrained. This is the home theme.
- **Ink (dark):** a developer at a terminal at night. Near-black canvas, dotted
  grid, monospace. The same blocks, re-skinned by a four-group override.

Theme is a token delta, never a CSS fork. The ink override restates colours, the
three font roles, texture density, and glow; it inherits scale, spacing, type
sizes, and layout from the base.

## Color

Role-based, not literal. A role names a job; its value changes per theme.

| Role | Paper | Ink |
|---|---|---|
| surface | `#F5F1E8` warm paper | `#0D1117` near-black |
| surface-raised | `#ECE6D8` | `#11161D` |
| ink (text) | `#1B1A16` | `#FFFFFF` |
| ink-muted | `#6E6557` | `#B7BFC8` |
| accent | `#8A3324` sienna | `#F5B8A5` coral |
| accent-soft | `#B5654D` | `#BC9AFA` violet |
| border | `#2B2820` | `#2F353C` |
| rule | `#D8D0BE` | `#2F353C` |

Strategy: **restrained**. Tinted neutrals plus one accent used sparingly (links,
buttons, callout label, step numerals). Accent never carries large surface area.
Verify accent contrast as a link/text colour on both surfaces, not only on display
type (a known watch-item; AA for body text).

## Typography

Hierarchy through scale and face, not weight tricks. The type scale steps by
`scale.ratio` (1.5). Sizes are tokens; the face is applied from a font role, so a
theme swaps three roles, not the whole scale.

| Role token | Paper face | Ink face |
|---|---|---|
| display (h1/h2/h3, pull-quote) | Spectral, Georgia, serif | Monaspace Xenon |
| body (reading text) | Spectral, Georgia, serif | Monaspace Neon |
| mono (eyebrow, meta, code, nav) | IBM Plex Mono | Monaspace Argon |

- Sizes (px): h1 52, h2 30, h3 22, lead 21, body 17, small 14, code 14, caption/eyebrow 13.
- Body measure capped at `layout.measure` (680px, ~66ch). Never full-bleed text.
- Small-caps for section headers and the hero eyebrow (mono, uppercase, tracked).
- Display runs italic in paper, upright in ink (a per-theme recipe, not a token).

## Components

Generic content blocks, each token-driven:

- **Section header**: small-caps display label, a hairline rule filling the row.
- **Card grid**: bordered cards on `surface-raised`, `radius.sm`, a `№` index in
  mono, italic display title. Used for an index of domains, not for decoration.
- **Callout**: full 1px border plus a leading mono label. No side-stripe.
- **Steps**: large display numerals in accent, content in a two-column grid.
- **Pull-quote**: large italic display, mono cite, no quotation marks.
- **List-rows**: bordered rows, italic title, mono meta line.
- **Code / table / figure**: mono, hairline borders, mono captions and table heads.
- **Colophon** (closing): a strong top rule, left-aligned. Not a boxed CTA banner.

## Layout

- `layout.content-max` 1080px shell; reading blocks narrow to `layout.measure`.
- Section rhythm from `layout.rhythm` (72px); vary spacing for cadence, do not pad
  uniformly.
- Text + media rows split at `layout.media-split` (0.58) with `layout.media-gap`.
- Texture is a per-theme recipe: ruled horizontal lines (paper) or dots (ink),
  both sized by `texture.gap` at `texture.opacity`.

## Motion

- `motion.fast` (200ms) for hover/flash, `motion.base` (350ms) for theme/state,
  `motion.slow` (800ms) for any morph.
- Ease-out only; no bounce, no elastic. Never animate layout properties.
- Honour `prefers-reduced-motion`: transitions degrade to instant.

## Bans (enforced)

No side-stripe borders, no gradient text, no glassmorphism-by-default, no
hero-metric tiles, no identical icon-cards, no em dashes in copy, no `#000`/`#fff`
as literals where a tinted neutral belongs.
