# Monaspace — page broken into block prompts

A worked decomposition of the **live** demo at
[monaspace.githubnext.com](https://monaspace.githubnext.com/) — far richer than the
single-page template in `examples/monaspace/monaspace.html`. The real page is one
long scrollytelling document (~14,100px) that scroll-jacks through a pinned
texture-healing animation, so it does **not** yield to a single full-page
screenshot; it was captured and read block-by-block instead (hero, superfamily,
and playground visually; all nine via DOM + page text).

This file is a **prompt-door artifact** (skill convention, not DTCG): each logical
block is rephrased as a ready-to-paste build/generation prompt with the Monaspace
tokens baked in, plus variations. The last section adds a few **unique** blocks
that are *not* on the original page — demo material showing the same token
language pushed somewhere new.

## Token palette baked into every prompt

Resolved from `templates/monaspace.tokens.json`. Use these literals verbatim.

| Role | Hex | Font (role) |
| --- | --- | --- |
| background / canvas | `#0D1117` | — |
| text / ink | `#FFFFFF` | — |
| muted | `#B7BFC8` | — |
| border | `#2F353C` | — |
| **Neon** — primary | `#F5B8A5` (dark `#86412E`) | Monaspace Neon · neo-grotesque sans/mono |
| **Argon** — warning | `#F1E170` (dark `#7D6E2F`) | Monaspace Argon · humanist sans |
| **Xenon** — display | `#B6D162` (dark `#4D5C2A`)¹ | Monaspace Xenon · slab serif |
| **Radon** — handwriting | `#82D2CF` (dark `#3B5E60`) | Monaspace Radon · cursive/handwriting |
| **Krypton** — accent | `#BC9AFA` (dark `#3B2772`) | Monaspace Krypton · mechanical sans |

¹ Xenon's accent is the green `#B6D162` (success role); the display *face* is Xenon
slab serif. Treat colour-role and font-role independently.

Shape: corner-radius scale `4 / 8 / 16 / 24px` (soft). Texture: faint dotted grid,
`radial-gradient(rgba(201,209,217,.05) 1px, transparent 1px)` at `22px` spacing,
over the `#0D1117` canvas. Body weight is light (300); display headlines are
mono and heavy.

---

## The nine blocks

Each block: **role** · **what's on the page** · **prompt** · **variations**.

### 1 · Nav + Hero

- **Role:** masthead + first impression. The wordmark *is* the pitch.
- **On the page:** thin sticky nav (`/ Monaspace`, GitHub mark). Below it the word
  "monaspace" rendered as **font outlines with every Bézier control point exposed**
  (open contours + node handles), a struck-through `v1.400` version tag in Neon
  coral, the tagline "An innovative superfamily of fonts for code", Download +
  Learn more buttons, and a "code rain" of real snippets fading in below — each
  line in a different family glowing its own accent (Neon coral, Argon yellow,
  Xenon green, Radon teal). All over the dotted-grid canvas.

> **Prompt.** Build a full-bleed hero on a `#0D1117` canvas dusted with a faint
> 22px dotted grid (`rgba(201,209,217,.05)`). Centerpiece: the product name set
> huge in a heavy mono display face, rendered as **glyph outlines with visible
> Bézier nodes and handles** — a typeface caught mid-design, not filled type.
> Trail a small version badge in Neon `#F5B8A5`. Tagline in white `#FFFFFF`,
> light weight. Two buttons: a solid white primary and a `#2F353C`-bordered ghost,
> both `8px` radius. Below the fold, fade in 4–5 lines of real code, each line in
> a different Monaspace family and glowing its accent (Neon `#F5B8A5`, Argon
> `#F1E170`, Xenon `#B6D162`, Radon `#82D2CF`), low opacity, drifting upward.

- **Variations:**
  - *Filled wordmark* — solid glyphs in white instead of outlines, accent glow behind.
  - *Single-language rain* — all code in one family/accent for a calmer, focused hero.
  - *Light canvas* — flip to `#FFFFFF` bg / `#0D1117` ink; accents stay, grid darkens.
  - *Typing cursor* — wordmark types itself glyph by glyph with a blinking caret.

### 2 · Superfamily intro — "One superfamily. Five fonts. Three variable axes."

- **Role:** the thesis + the cast.
- **On the page:** three-line mono headline (huge, white). Two columns of light
  prose on the history of monospaced code type, ending on a Neon-coral highlight
  line ("Monaspace offers a more expressive palette…"). Below: **five
  periodic-table-style cards** — `Ne Ar Xe Rn Kr` set large in each family,
  glowing its accent, with full name + classification ("Neo-grotesque sans",
  "Humanist sans", "Slab serif", "Handwriting", "Mechanical sans"). The selected
  card carries a coral border.

> **Prompt.** A section header set in three stacked lines of heavy mono display,
> white on `#0D1117`. Beneath it, a two-column light-weight body passage; pull the
> closing sentence out in Neon `#F5B8A5`. Then a row of **five "periodic element"
> cards** on `#11161d` panels with `16px` radius and a `#2F353C` hairline border.
> Each card shows a two-letter symbol set large in its family and glowing its
> accent — `Ne` Neon `#F5B8A5`, `Ar` Argon `#F1E170`, `Xe` Xenon `#B6D162`,
> `Rn` Radon `#82D2CF`, `Kr` Krypton `#BC9AFA` — with the family name and a
> typographic classification below. Give the active card a 1px accent-coloured border.

- **Variations:**
  - *Hover-to-glow* — cards are inert until hovered, then the accent blooms.
  - *Axis diagram* — replace cards with three labelled sliders (weight/width/slant)
    showing the same letter morphing along each axis.
  - *Vertical stack* — on mobile, cards become a single scroll-snap column.

### 3 · Font playground

- **Role:** hands-on proof. Let the visitor drive the fonts.
- **On the page:** a two-pane interactive block. Left: a numbered, syntax-highlighted
  code editor (language tabs: JavaScript / HTML / CSS / Java / Python / C++ / PHP / F#).
  Right: a control column — **Font size**, **Weight** (200–800), **Width** (100–125),
  **Slant** (0 to −11°) sliders; **Texture healing / Ligatures / Grid** checkboxes;
  a **Theme** `<select>` (Atom One Dark, Dracula, Darcula, GitHub Dark, GitHub Light,
  VS Code Dark, Xcode Dark/Light). Changing a control re-renders the live code.

> **Prompt.** Build an interactive type playground, two columns on `#0D1117`.
> Left pane: a line-numbered code editor with realistic syntax highlighting,
> a row of language tabs across the top, rendered in a Monaspace mono face.
> Right pane: a control stack — labelled range sliders for Font size, Weight
> (200–800), Width (100–125), Slant (0 to −11°) with the live value pinned to the
> right in muted `#B7BFC8`; three checkboxes (Texture healing, Ligatures, Grid)
> with Neon `#F5B8A5` checked states; and a Theme dropdown (`8px` radius,
> `#2F353C` border). Every control mutates the editor's CSS variable font-settings
> in real time. Light body weight, `16px` radius on the editor panel.

- **Variations:**
  - *Variable-axis lab* — drop the editor, show one giant letter morphing as you
    drag the three axes; trace the design space live.
  - *Diff playground* — split the editor; left healing OFF, right healing ON,
    synced scroll.
  - *Preset chips* — replace sliders with "Light / Regular / Bold · Normal / Italic"
    chips for a simpler casual mode.

### 4 · Mix & Match — "What if?"

- **Role:** the imaginative leap — fonts as a semantic palette.
- **On the page:** a `Mix & Match` pill tag, huge mono "What if?" headline, prose
  on why monospaced fonts normally *can't* mix and why Monaspace can. A **"Shuffle
  font combination"** control that re-rolls the family per line. Worked examples:
  *"What if tentative ideas looked handwritten?"* (Radon), *"What if docstrings
  looked authoritative?"* (Xenon slab), and a **Copilot before/after** — the same
  `useState` line shown twice, the AI-suggested part typographically marked in the
  "After".

> **Prompt.** A provocation section: small accent pill tag ("Mix & Match") above a
> huge mono "What if?" headline, white on `#0D1117`. Light-weight body explaining
> that Monaspace's five families share metrics so they mix on one grid. Then a
> demo where a single block of code mixes families to carry *meaning*: comments and
> tentative code in Radon handwriting `#82D2CF`, docstrings in Xenon slab serif
> `#B6D162` looking authoritative, AI-suggested spans tinted Krypton `#BC9AFA`.
> Add a "Shuffle font combination" button that re-rolls which family renders which
> role, animating each glyph's swap. Show a Copilot-style before/after of one line.

- **Variations:**
  - *Semantic legend* — a small key mapping each family to a role (human / machine /
    docs / draft) shown alongside.
  - *Live diff voice* — AI spans literally fade in "after the fact" in Krypton.
  - *Single-line shuffler* — minimal: one sentence, shuffle button, nothing else.

### 5 · Feature: Texture healing (scrollytelling)

- **Role:** the signature feature, taught through motion.
- **On the page:** `Feature` tag + "Texture healing" headline, prose on the uneven
  density problem of monospaced type since the Teletype era. A pinned, scroll-driven
  sequence animates the word **"calming"** and walks through sidebearings, narrow
  letters (`l`, `i`) with exaggerated serifs, wide letters (`m`, `w`) crammed and
  distorted — then a big **TEXTURE HEALING OFF → ON** comparison on a sample word,
  explaining the OpenType `calt` (contextual alternates) mechanism.

> **Prompt.** A pinned scrollytelling feature on `#0D1117`. Open with a `Feature`
> accent tag and a heavy mono headline "Texture healing", then a light-weight
> explainer of uneven monospace density. As the reader scrolls, animate a single
> word at display size: highlight each glyph's sidebearings as faint Neon `#F5B8A5`
> guides, show narrow `l`/`i` over-spaced and wide `m`/`w` cramped, then crossfade
> a large **OFF vs ON** pair where alternate glyphs slide into place to even the
> rhythm. Label states in mono caps with muted `#B7BFC8` keylines. Keep everything
> on the monospace grid — the payoff is that healing never breaks the columns.

- **Variations:**
  - *Hover instead of scroll* — heal on hover for embed contexts where pinning is rude.
  - *Side-by-side static* — no animation; two columns, OFF and ON, for print/PDF.
  - *Density heatmap* — overlay a red→green density map that flattens as healing applies.

### 6 · Step by step — "calming" healed glyph-by-glyph

- **Role:** slow-motion mechanism reveal (the closer of the healing arc).
- **On the page:** "Step by step — Let's unpack how texture healing is applied."
  A frame-by-frame walkthrough of the word **"calming"**: the `l` cedes space and
  shifts left, the `m` extends to fill, then a second pair heals in the opposite
  direction — narration in short lines synced to each swap, ending "The resulting
  text still obeys the monospaced grid."

> **Prompt.** A step sequence on `#0D1117` titled "Step by step", light intro line.
> Render the word "calming" once, large, in a mono face on a visible faint grid.
> Step through ~8 captioned states: identify a healable pair, narrow the
> space-giving glyph and shift it, extend its neighbour to fill, repeat for the
> next pair in the opposite direction. Each step: one short mono caption left,
> the morphing word right, the changed glyphs briefly outlined in Neon `#F5B8A5`.
> End on the fully healed word with the grid lines drawn to prove columns held.

- **Variations:**
  - *Scrubber* — a draggable timeline replaces auto-advance.
  - *Your word* — let the reader type a word and watch it heal.
  - *Annotation-free* — pure animation loop for a social/GIF cut.

### 7 · Styles — "640k styles ought to be enough for anyone"

- **Role:** the catalogue — every named weight/width/slant.
- **On the page:** "Styles" tag + the wry headline. Prose on the three axes with
  inline tables: **weight** 200–800 (Extra Light → ExtraBold), **slant** 0/−5.5°/−11°
  (the midpoint swaps obliques for true italics), **width** 100/112.5/125
  (Normal / Semiwide / Wide). Then a **horizontal scroll-snap carousel** of
  eight-letter words, one track per family, each track labelled `MONASPACE NEON`,
  `… ARGON`, `… XENON`, `… RADON`, `… KRYPTON`, with an **Italic** toggle.

> **Prompt.** A specimen catalogue on `#0D1117`. Header "640k styles ought to be
> enough for anyone" in heavy mono. Three compact spec tables for the variable
> axes — weight (200→800 named steps), slant (0 / −5.5° / −11°), width
> (100 / 112.5 / 125) — labels muted `#B7BFC8`, values white. Below, five
> horizontal scroll-snapping carousels, one per family, each rendering rows of
> real eight-letter words ("verbatim", "nimblest", "foothill"…) in that family
> and tinted its accent (Neon `#F5B8A5` … Krypton `#BC9AFA`), each track captioned
> with the family name in mono caps. A single Italic toggle slants every track at once.

- **Variations:**
  - *Weight ramp* — one word repeated down the 200→800 ladder to show the ramp.
  - *Pangram mode* — swap word lists for per-family pangrams.
  - *Grid of swatches* — replace carousels with a static specimen grid for export.

### 8 · Feature: Code ligatures (stylistic sets)

- **Role:** the developer-facing payoff — copy-paste config.
- **On the page:** `Feature` tag + "Code ligatures" headline, prose on stylistic
  sets `ss01`–`ss10` (each tuned to a language family — ss01 JavaScript, ss05 F#)
  plus `calt` (texture healing) and `liga` (repeat-char spacing like `///`, `||`).
  A **VS Code** card with a `editor.fontLigatures` settings line and **Copy to
  clipboard**. Then a long animated reference: per set, each raw sequence
  (`===`, `!==`, `->`, `<=>`, `|>`, `###`…) **morphs into its ligature** across a
  dotted leader.

> **Prompt.** A ligature reference on `#0D1117`. Header "Code ligatures" with a
> `Feature` accent tag. Light intro on stylistic sets ss01–ss10 (each scoped to a
> language) plus calt and liga utilities. A "Visual Studio Code" panel
> (`16px` radius, `#2F353C` border) containing a `editor.fontLigatures` settings
> string and a "Copy to clipboard" button with a Neon `#F5B8A5` confirm flash.
> Below, grouped by set, list operator sequences twice across a dotted leader —
> raw on the left, **ligated** on the right — and animate the raw glyphs sliding
> together into the ligature on scroll-in. Counts per set in muted `#B7BFC8`.

- **Variations:**
  - *Toggle per set* — checkboxes that live-rebuild the settings string and the preview.
  - *Language preset* — "JavaScript / F# / Haskell" buttons that select the right sets.
  - *Compact table* — drop the animation; two-column glyph table for docs.

### 9 · Contributors + Footer CTA

- **Role:** credit + conversion.
- **On the page:** "Made with ♥ — Contributors" with the GitHub Next × Lettermatic
  origin story and a repo link. Then a full-bleed footer banner: **"What will you
  make with Monaspace?"** huge mono headline, a solid **Download** button, and the
  `© 2026 GitHub` line.

> **Prompt.** Two closing blocks on `#0D1117`. First: a credits section, small
> heart-tag, heavy mono "Contributors" headline, a short light-weight origin
> paragraph, and an underlined repo link in Neon `#F5B8A5`. Second: a full-bleed
> CTA banner with a subtle accent-tinted glow at the edges, a huge centered mono
> question "What will you make with [Product]?", a solid white Download button
> (`8px` radius) and a muted copyright line beneath.

- **Variations:**
  - *Animated wordmark footer* — the outline-node wordmark from the hero returns, filled.
  - *Contributor avatars* — a wrapped grid of avatar chips on `#11161d` panels.
  - *Newsletter CTA* — swap Download for an email field + "Get updates".

---

## Unique demo variations — blocks NOT on the original page

Same token language, pushed somewhere new. The first three are **frontend build
prompts**; the last two are **image-gen CLI lines** you can run straight from the
skill's prompt-door tooling (exact hex/fonts already baked in, matching
`examples/monaspace/resolved/image-prompts.md`).

### A · "Terminal in the wild" — a faux desktop scene

> **Prompt.** A hero alternative: a single floating terminal window, `16px` radius,
> `#11161d` chrome with three muted dots, on a `#0D1117` dotted-grid desktop.
> Inside, a live session types a build log line by line — prompts in Krypton
> `#BC9AFA`, success lines in Xenon green `#B6D162`, warnings in Argon `#F1E170`,
> errors in Neon `#F5B8A5` — all set in Monaspace Neon. A blinking block caret.
> The whole window casts a soft accent-tinted shadow. Sells "this is your daily
> driver" without a word of marketing copy.

### B · Accent legend — the full periodic table

> **Prompt.** Extend block 2's five cards into a full "periodic table of the
> superfamily": a 5-wide grid where each family is an element tile (symbol, name,
> classification, a one-line specimen) on a `#11161d` panel, plus a second row of
> *role* tiles mapping each accent to its semantic job — primary/Neon, warning/Argon,
> success/Xenon, info/Radon, accent/Krypton — so designers read colour-role and
> font-role at a glance. Dotted-grid canvas, `16px` radius, `#2F353C` borders.

### C · 404 / ghost-text page

> **Prompt.** A 404 page on `#0D1117`: a giant "404" set in outline glyphs with
> visible Bézier nodes (echoing the hero), the message half-rendered as Krypton
> `#BC9AFA` "ghost text" the way an AI suggestion appears, with a Neon `#F5B8A5`
> "accept" affordance to "complete" the route back home. Playful, on-brand,
> reuses the wordmark-outline motif.

### D · Type-specimen poster (image-gen)

```
scripts/gpt_image_2.py --preset poster --platform portrait --quality high -y \
  "type specimen poster for a code superfamily, five vertical columns each set in a different monospaced family with one large eight-letter specimen word per column glowing its accent, color palette: column accents #F5B8A5 #F1E170 #B6D162 #82D2CF #BC9AFA, text #FFFFFF, background #0D1117, faint dotted grid texture, typography Monaspace Neon mono, soft 16px rounded panels, no logos" \
  monaspace-specimen-poster.png
```

### E · Texture-healing explainer card (image-gen, in-image text)

```
scripts/nano_banana.py --preset editorial --platform landscape --model pro \
  "an editorial diagram titled TEXTURE HEALING showing the word calming twice: OFF above with uneven spacing, ON below evened out on a visible monospace grid, the two healed glyph pairs highlighted with thin Neon outlines, color palette: primary #F5B8A5, accent #BC9AFA, text #FFFFFF, background #0D1117, muted #B7BFC8, typography Monaspace Neon monospace, legible in-image labels, soft rounded panels" \
  monaspace-healing-explainer.png
```

---

*Method: live page captured at `monaspace.githubnext.com` (hero, superfamily, and
playground via screenshot; all nine blocks via DOM section map + extracted page
text). The page scroll-jacks through a pinned texture-healing animation, so a
single full-page screenshot isn't attainable — block-by-block is the faithful
capture. Tokens resolved from `templates/monaspace.tokens.json`.*
