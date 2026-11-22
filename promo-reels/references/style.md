# Style: picking the look of the slides

The look is a set of **design tokens** in one JSON file. Slides never hardcode a colour, font or
shape — `template.html` reads only tokens, so any style renders through the same fit and audit.
A project keeps its choice in `style.json` next to `slides.json`; `slides.py` picks it up by itself.

## Three ways in (ask once, at intake)

1. **Preset** — the user picks from previews of *their own hook* in each style (default path).
2. **From a reference** — a poster, a screenshot, a brand page, the venue's site: palette is
   extracted, roles assigned, contrast repaired, then refined in dialogue.
3. **Brand file** — the user already has a `style.json` or brand colours/fonts: write the override
   directly with `style.py set`.

All three end the same way: one preview of hook + CTA in the chosen style, a yes, then `slides.py`.

## The dialogue

At most four questions. Each one maps to tokens; each answer is applied with `style.py set` and
followed by a fresh preview, so the user always judges a picture, not a hex code.

| # | question | widget | answer → tokens |
|---|---|---|---|
| 1 | "Which look for the slides?" | image choice over `preview/*.png` (+ "from a reference") | preset name → `{"extends": name}`; "from a reference" → ask for it, run `from-ref` |
| 2 | "Accent colour?" (only if the user wants to change it, or `from-ref` found >1 candidate) | choice of up to 4 swatches/hex + free text | `color.accent=#…` (dependent colours follow and repair themselves) |
| 3 | "Capital letters or as written?" | choice: CAPS / As written | `type.case=upper\|none` |
| 4 | "Left or centred?" | choice | `type.align=left\|center` |

Skip any question the reference or the user already answered. Stop when they say "good" — the
other tokens (weights, radius, button style, texture, motion, grade) are changed only on request,
via `style.py set` with the names in the table below.

### Asking: use the best question tool the agent has

- **cenno** (`ask_user` tool present, macOS): `style.py preview` writes `preview/choice.json` —
  ready `ask_user` arguments with an `a2ui` ImageChoice of the rendered previews. Pass it as is.
  Q2–Q4 are plain `input.kind: "choice"`; the four can go in one `ask_sequence` when nothing depends
  on an earlier answer. A timeout is "no decision": keep the current value, don't loop.
- **A built-in question tool** (e.g. a multiple-choice prompt): use `choices` from `choice.json`
  and show `preview/styles.jpg` first.
- **Plain chat** (any agent, ChatGPT, Codex): show `preview/styles.jpg` (the contact sheet, style
  names under each tile) and ask for a name. Accept loose answers ("the dark one", "as #2 but blue")
  and translate them to tokens.

The script never asks anything itself — it renders and writes files; the agent asks.

## From a reference

```bash
python3 scripts/style.py from-ref poster.jpg [more.jpg | https://site] --out style.json \
        --font condensed --case upper [--align left] [--accent '#C43F2F']
```

Look at the reference before running it and decide the three things pixels can't tell reliably:
- `--font` archetype: `condensed` (narrow grotesque, posters) · `serif` (editorial, classical) ·
  `geometric` (neutral sans, tech) · `wide` (extended/rounded display, pop) · `mono` (typewriter).
  This also picks the base preset whose shapes and weights are inherited.
- `--case`: are headlines in capitals? `--align`: centred composition?

Then check `ref_palette.png` (top row: area palette and accent candidates; bottom row: roles)
next to the reference. Accents are found among saturated pixels, ranked so small brand marks
(dots, underlines, a button) win over large grey areas — but photos in a reference are saturated
too. When the script prints more than one candidate, ask the user (Q2) with the candidates.

A URL needs network (headless Chrome screenshots it). Offline, ask for a screenshot instead.
A specific brand font: put the TTF/OTF in the project, add it to `fonts` in `style.json`
(`{"family": "Brand Sans", "file": "BrandSans.ttf", "weight": "100 900"}` — path relative to the
style file) and set `type.display`. Check its licence allows embedding in video; it must contain
the copy's alphabet (Cyrillic!) — a missing glyph falls back silently to another font.

## Tokens

| group | token | values | effect |
|---|---|---|---|
| type | display, text, mono | font family (must be in `fonts`) | headlines / background texture / mono details |
| | case | `upper` · `none` | capitals or the copy as written (write it in proper sentence case then) |
| | hero_weight, light_weight, strong_weight | 100–900 | first hook line & titles / other hook lines / date, buttons |
| | leading | ~0.9–1.1 | line height; wide or tall faces need ≥ 1.05 or lines touch |
| | tracking | em, e.g. `-0.02em` | letter-spacing |
| | align | `left` · `center` | |
| | fill_chars | `{"ru": n, "en": n}` — **measured** | letters per full-width line at ≥ 140 px; written by `calibrate`/`set` |
| color | bg, ink | hex | hook background and text |
| | accent, on_accent | hex | button, rule, caption plate / text on them |
| | accent_ink | hex | date on the hook (accent, darkened until it reads on bg) |
| | cta_bg, cta_ink, cta_date | hex | CTA slide background, text, big date |
| shape | radius | px (999 = pill) | button corners |
| | rule_w, rule_h | px (`rule_h` 0 = none) | the accent bar under the hook lines |
| | button | `fill` · `outline` · `underline` · `none` | action on the hook |
| texture | bg_text_opacity, bg_text_rotate | 0–0.12, degrees | faint documentary text behind the hook (0 = off) |
| motion | slide_move, footage_move | 0–0.06 | push-in on slides (0 = static) / on footage — used by `build.py` when the EDL has `"style"` |
| grade | contrast, saturation | ~0.8–1.15 | ffmpeg colour grade of footage |

`style.py check` enforces contrast: ink/bg ≥ 4.5; every other text pair ≥ 3 (all slide text is
≥ 54 px, WCAG "large text"). `set` repairs a failing pair by changing the *text* colour, never one
the user just set; changing `accent` also moves `cta_bg`/`cta_date` (if they were the accent) and
`accent_ink` with it.

## Presets

| preset | font | look | mood (match the brief) | fill (ru/en) |
|---|---|---|---|---|
| `doc-red` | Roboto Condensed caps | grey, red accent, transcript texture | documentary, theatre, activist | 10 / 11 |
| `editorial` | Playfair Display, as written, centred | cream, deep green, outline button | literary, classical, lecture, premium | 10 / 12 |
| `minimal` | Inter, as written | white, one blue, outline button, static slides | tech, workshop, conference, course | 10 / 12 |
| `night` | Inter Black caps | black, acid lime | music, club, concert, sport | 8 / 9 |
| `pop` | Unbounded caps | yellow, hot pink, pills | comedy, kids, festival, launch | 6 / 7 |
| `zine` | PT Mono caps | newsprint, orange, underline | DIY, indie, community, reading | 10 / 10 |

**Copy follows the style.** Write hook lines within the style's `fill_chars`, not a fixed 10:
in `pop` "выдуманной" (10 letters) drops to 93 px and the audit asks for a rewrite. When the user
picks a style their copy breaks, say so with the preview ("copy too long" under the tile) and
offer shorter lines — don't swap the style silently.

Add a preset: copy one in `assets/slides/themes/`, change it, run
`style.py calibrate NAME --write`, `style.py preview` to see it next to the others.

## Learned in use
<!-- appended by scripts/learn.py — newest last -->
