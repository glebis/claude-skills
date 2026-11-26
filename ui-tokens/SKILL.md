---
name: ui-tokens
description: Extract a product's design tokens — colours (light and dark), type families and scale, spacing, radii, shadows and the product's own transitions and keyframes — from its code (CSS, HTML <style>, Google Fonts links) and screens, into tokens.json, a tokens.ts that raea components import, and a token sheet PNG. Use before animating or making a video of existing software ("extract the tokens", "what's this app's palette", "token sheet", "make the video in the product's own look"), and as step one of the interface-to-video chain (ui-tokens → user-journeys → ui-motion → raea-animate).
---

# ui-tokens

A product video looks like the product only if it is built from the product's own values, not from a screenshot's
guessed colours. This skill reads them out of the code and checks them against the screens.

## Steps

1. **Find the sources.** Grep the repo for `:root`, `--` custom properties, `@font-face`, `fonts.googleapis`,
   `transition`, `@keyframes`, `animation`. Usually one shared CSS file plus inline `<style>` in the page templates.
   Tailwind or CSS-in-JS: read the theme config instead and write tokens.json by hand in the same shape.
2. **Extract.**
   `python3 ~/.claude/skills/ui-tokens/scripts/extract.py OUT_DIR FILE.css FILE.html ...`
   writes `OUT_DIR/tokens.json` (light/dark grouped by kind: color, font, size, radius, height, shadow, other;
   `fontFamilies`; `spacingPx` by use; `radiusUse`; `motion.transitions`, `motion.keyframes`, `motion.durationsMs`)
   and `OUT_DIR/tokens.ts` (`T`, `DARK`, `MOTION_MS` — names with dashes become underscores: `--pencil-soft` → `T.pencil_soft`).
3. **Fonts.** If the families aren't installed, ask before downloading (OFL fonts from
   `raw.githubusercontent.com/google/fonts/main/ofl/<name>/`) into the video project's `assets/fonts/`.
4. **Sheet.** `python3 ~/.claude/skills/ui-tokens/scripts/sheet.py OUT_DIR/tokens.json OUT_DIR/token-sheet.png --fonts assets/fonts --title "NAME · design tokens"`
   (1920×1080: base colours with their dark twin in the corner, paired category colours as chips, the type families
   at their roles, the rem scale in px, radii, spacing bars, the product's own transitions).
5. **Check against the screens.** Open one real screenshot next to the sheet. Anything on screen that isn't in the
   sheet (a hard-coded hex, a one-off radius) goes into tokens.json by hand with a `"note"`.
6. **Read the motion.** The product's own durations (e.g. 150–400 ms opacity/background) set the floor for the
   video's UI motion: the video may slow and exaggerate them for reading at 30 fps, but keeps what moves and in what
   order. Say this in one line in the hand-off.

## Output contract (what later skills rely on)

- `tokens.ts` is imported by the ui-motion components: never paste hex values into components.
- `rem` sizes are converted with the page's root size (read `html { font-size }`); note it in tokens.json if not 16 px.
