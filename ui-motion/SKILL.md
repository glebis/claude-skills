---
name: ui-motion
description: Build interface animations from a product's real screens and real UX as raea components — panels, segmented toggles, buttons with a press, checkboxes that tick, a cursor that glides and clicks, typing, remarks/highlights blooming, cards growing from their top edge, diff strikes and insertions, keycaps — drawn as live DOM at 2× the app's px from the product's extracted tokens, never screenshots pasted in. Use when a product video or demo needs the app's UI to move ("animate the interface", "make the UI components move", "rebuild this screen in raea", "cursor clicks the button"), as step three of the interface-to-video chain (ui-tokens → user-journeys → ui-motion → raea-animate).
---

# ui-motion

The product's interface, rebuilt as raea components that animate. Faithful to the app (its tokens, its copy, its
controls) and readable on video (type at its final size, motion slowed enough to read at 30 fps).

**Inputs:** `tokens.ts` from `ui-tokens`, the video arc from `user-journeys` (each story: action → result), 2–3
screenshots of the real screens, the real copy (the product's data files, reviews, history: never invented text).

## Rules

1. **Live DOM at 2×, never pictures of the UI.** `S = 2`: every app px is drawn at 2 px, so 15 px body text is 30 px
   in a 1920×1080 frame. The camera scales between 0.9 and 1.3; never put live text under 0.6×.
2. **Every value from tokens.** `import { T } from "./tokens.gen"`: colours (`T.pencil`, `T.del_bg`…), radii, fonts.
   A value not in tokens.json goes there first (ui-tokens step 5).
3. **Every prop that moves is a number.** Progress 0..1 (`on`, `open`, `strike`, `press`), a float index (`Seg at=3.4`
   slides the fill between Agree and Auto), a character count (`typed`). The composition owns the clock; only the
   cursor and keycap take the frame `f` themselves.
4. **Eases from GSAP, frame-pure.** `ease.ts`: `gsap.parseEase("power3.out")` evaluated per frame;
   `tw(f, a, b, from, to, ease)`. Never GSAP timelines or the ticker (not deterministic per frame).
5. **Exaggerate what the app does instantly, keep its order.** The product's own transitions (ui-tokens
   `motion.durationsMs`, e.g. `.par { transition: background .4s }`) are kept and named in a comment; instant swaps
   (a mode toggle, a press) get 6–10 frames; presses sink 2 frames and spring back over 5.
6. **Real copy.** Quotes, model takes and fixes come from the product's data (for prose-eval `reviews/*.jsonl`,
   `out/edited/*.md`). Trim to the first sentence; never paraphrase into marketing.
7. **Fonts.** `@font-face` from `assets/fonts/` via a `compositions/media -> ../assets` link; variable TTFs need
   `font-weight: 300 800`.

## The kit (`assets/ui.tsx`, `assets/ease.ts`)

Copy both into the project's `components/` next to `tokens.gen.ts` (the extractor's `tokens.ts`, renamed). Adapt the
components to the product's real controls; prose-eval's are the worked example:

| component | props that animate | what it shows |
|---|---|---|
| `Seg` | `at` (float index), `press` | segmented mode toggle, the fill slides |
| `Btn` | `press` | `.btn` neutral / go / solid |
| `Check` | `on` | checkbox fill and the check stroke drawn on |
| `Chip` | `n` (count ticks up), `on` | category chip with its colour dot |
| `Mark` | `on`, `votes`, `sel` | a highlight blooming (solid = 2 models agree, underline = 1) |
| `Fix` | `strike`, `typed`, `clean`, `mark` | Diff: old words struck red, new ones typed in green; Clean fades both |
| `Card` | `open`, `takes`, `apply` | a card growing from its top edge, takes rising in one by one |
| `Rail` | dots with `at` / `gone` | margin dots pop in (back ease) and leave |
| `Cursor` | `keys`, `clicks` | a macOS arrow on a Catmull-Rom path, a dip and a ring per click |
| `KeyCap` | `at` | a one-key action (a = apply) popping up, pressed, leaving |

## Steps

1. Pick 2–3 screenshots for the arc's stories. List each control on them and the component it maps to.
2. Copy the kit, build the page layout (flex, the app's px × S), drop in the real copy.
3. Probe first: a one-frame composition with one paragraph, one highlight and one strike
   (`raea render compositions/probe.tsx -o out/test --at 0`) checks fonts, inline backgrounds and `line-through`.
   Inline `dashed` borders don't render: use a lighter underline for "one model".
4. Measure cursor targets from a still (screen px → app px: `(x - 960) / s + cam.x`) and write them in `TARGET`.
5. Frame strip for review and the deck: `raea render FILE.tsx -o DIR --at F1,…,F8`, then
   `ffmpeg -pattern_type glob -i 'DIR/frame-*.png' -vf "scale=640:-1,tile=4x2:padding=8:color=white" -frames:v 1 strip.png`.

## Traps

- `cp -R` of a node_modules package that is a symlink (raea installs `gsap -> .raea/gsap@…`) copies a dead link: use
  `cp -RL`. raea caches a refusal until the file changes: touch the composition after fixing a dependency.
- `raea check` flags text that is off-frame during a push-in as low contrast; look at the frame before chasing it.

Worked example: `~/raea/showreel/projects/prose-video/components/ui.tsx` (prose-eval).
