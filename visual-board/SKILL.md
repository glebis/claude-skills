---
name: visual-board
description: Assemble a visual reference board as one PNG (plus per-section PNGs and optional HTML) that puts a reference video's stills, the product's real screens, its design tokens and the storyboard frames (reference move next to product moment) side by side. Use when the user asks for a "mood board", "reference board", "visual board", "storyboard sheet", "put the reference and our screens side by side", or a single picture for a deck that shows where a product video's look comes from. Follows ref-transfer and ui-tokens in the interface-to-video chain (ref-transfer → ui-tokens → user-journeys → ui-motion → raea-animate).
---

# visual-board

One deterministic script renders a JSON spec. Choosing what goes on the board is the agent's part.

## Inputs to gather
- **Reference stills**: `lecture/ref-transfer/stills/shot-NN.jpg` from the `ref-transfer` skill (or any stills).
  Pick 6–8 that show the moves the transfer borrows, and label each with the move, not the content.
- **Product screens**: real screenshots or frames from screen recordings (`video.webm@SECONDS`). Never generated images.
- **Design tokens**: `tokens.json` from the `ui-tokens` skill (colour swatches, type, spacing, radii and motion are
  drawn from it); if it is missing, a `fallback` image (a token sheet) or nothing.
- **Motion and rhythm** (optional): a `figure` section, one full-width image. Use `rhythm.png` from ref-transfer's
  `motion.py`, which shows a filmstrip of frames over the speed curve, beats, hits, cuts and easing:
  `{"kind": "figure", "title": "Motion and rhythm", "path": "../ref-transfer/rhythm.png"}`. Put it between the
  reference stills and the product screens.
- **Storyboard**: one frame per shot of the transfer plan (`refs/transfer.md`): `ref` still, `product` screen cropped to
  the one component the shot isolates (`screen.png#x,y,w,h` in source pixels), label `N · start–end s`,
  `text` = the on-screen line, `note` = the motion in a few words.

To find crop boxes, overlay a grid:
`ffmpeg -i screen.png -vf "drawgrid=w=128:h=90:c=red@0.5" grid.png`, then read the coordinates off it.

## Run
```bash
python3 ~/.claude/skills/visual-board/scripts/board.py lecture/visual-board/board.json -o lecture/visual-board --html
```
Spec format: see the docstring at the top of `scripts/board.py`. Paths are relative to the spec.
Output: `board.png` (3200 px wide), `part-NN-*.png` (each section alone, for slides), `board.html`, `frames/`
(extracted video frames and crops).

## Check
Read `board.png` back. Fix crops that miss the component, and labels that overflow their cell. Keep the reference
labelled "analysis only" when the board leaves the team.
