# Universal content kit — one block library, any theme

A token-driven block system for **wikis, docs, presentations, and non-technical
demos**. The blocks are generic content (hero, section header, card grid, prose,
list-rows, callout, steps, pull-quote, code, table, figure, CTA) — nothing is tied
to a brand. The look is supplied entirely by which token file is in scope, so the
same `blocks.html` renders as a **light editorial wiki** or a **dark developer
site** with one toggle.

## Architecture — base + theme override + merge

| File | Role |
| --- | --- |
| `base.tokens.json` | **Theme-neutral base.** Roles (`surface`, `ink`, `accent`, `border`…) + structure (type scale, space, radius, layout, texture, motion). Defaults to the **paper / light** theme so it's usable standalone. |
| `theme-ink.tokens.json` | **Theme override** (skill convention: global base + project override). The *entire* ink theme delta — colours, the 3 `font.*` roles, texture density, glow. Everything else is inherited. |
| `paper.css` | `base` exported to `:root` — the default light theme. |
| `ink.css` | `base` ⊕ `theme-ink` merged, exported to `[data-theme="ink"]`. |
| `blocks.html` | The universal blocks. Links both CSS files; toggling `data-theme` on `<html>` swaps the whole look. |

The key move that keeps themes tiny: **type tokens carry size/weight/lineHeight
only** (no `fontFamily`); the face is applied in CSS from the `font.display` /
`font.body` / `font.mono` role tokens. So a theme overrides three font roles, not
nine type tokens.

## Regenerate

```sh
T=../../scripts/tokens
$T export-css base.tokens.json -o paper.css
$T merge base.tokens.json theme-ink.tokens.json -o /tmp/ink.json
$T export-css /tmp/ink.json --selector '[data-theme="ink"]' -o ink.css
$T serve . --port 8754          # then open blocks.html
```

## Add a theme (e.g. a client brand)

1. Copy `theme-ink.tokens.json` → `theme-<brand>.tokens.json`.
2. Override only what differs — the role **colours**, the three **font roles**, and
   optionally `texture.*` / `elevation.glow-opacity`. Leave the scale, spacing, and
   layout alone unless the brand truly demands it.
3. `merge base.tokens.json theme-<brand>.tokens.json` → export with
   `--selector '[data-theme="<brand>"]'`. Add a switch entry in `blocks.html`.

## What's a token vs a recipe (the line this kit draws)

- **Tokens (values):** colours, the type scale, space, radius, `layout.measure`,
  `layout.media-split`, `texture.gap/opacity`, `motion.*`. These live in the JSON.
- **Recipes (patterns):** the texture *kind* (ruled lines for paper, dots for ink),
  italic-hero-in-paper / upright-in-ink, small-caps section headers. These are
  per-theme CSS, documented as prose — not values, so not tokens.

## Not yet here

A dedicated **slide / presentation mode** (one block per viewport, key-driven
advance). The blocks are already presentation-friendly (large type, generous
rhythm); a slide harness would be the next override layer.
