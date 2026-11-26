---
name: raea-animate
description: Assemble a short product video in raea from the outputs of the interface-to-video chain — tokens (ui-tokens), the story arc (user-journeys), the UI components (ui-motion) and, if there is one, a reference transfer (ref-transfer) — into one frame-pure composition with a single clock, a camera, GSAP eases (gsap.parseEase), isolation fields, captions, an end card and a synthesised Tone score on a BPM grid; then render, raea check, post with raea show, and export lecture/deck stills. Use for "assemble the video", "animate it in raea", "put the product video together", "render the product demo from these components". Named raea-animate because `animate` is already a different (web UI motion) skill. Reuses the raea, demo-cut and kinetic-ad skills instead of repeating them.
---

# raea-animate

The last step of the chain: everything before it decided *what* is on screen; this decides *when*, and makes it one
render that passes the checks.

**Load first:** the `raea` skill (workspace/project, `raea context .`, render/check/show). Read `demo-cut`'s
`references/rules.md` (the floor: flat DOM, one thing on stage, no dead holds, presses are physical). For a 9:16
type-led ad, `kinetic-ad` instead.

## Inputs

| from | file | used for |
|---|---|---|
| ui-tokens | `components/tokens.gen.ts` | every colour, radius, font |
| user-journeys | `lecture/user-journeys/journeys.json` → `video_arc` | the scenes, in journey order |
| ui-motion | `components/ui.tsx`, `ease.ts` | the moving UI |
| ref-transfer (optional) | `refs/transfer.md` | moves to borrow: characters, isolation, grid, end card |

## Build

1. **One clock.** `AT = { … }` in the cut file: every event is a frame. With music, put events on the grid
   (120 BPM at 30 fps: `BEAT = 15`, `BAR = 30`); hits (a click, an orb landing) on beats, scene changes on bars.
   Everything (picture, captions, sound) reads `AT`, so retiming is one edit.
2. **Layers, bottom to top** (`assets/cut.example.tsx`):
   app layer under a camera (`translate/scale` from keyed `CAM` with `power2.inOut`) → intro → characters in screen
   space (`toScreen(f, appPoint)` so they can ride the camera) → isolation fields (one component alone on a flat token
   colour) → keycaps → captions → end card.
3. **Camera.** Wide at 0.9 (keeps the top 120 px and left 60 px clear for platform UI), push to 1.2–1.3 on the
   detail, back out for the batch. Never below 0.6 with live text.
4. **Captions.** ≤ 6 words, English, one at a time, ink pill, bottom 136 px (clear of the bottom UI zone).
5. **Hook on frame 0.** The first frame is the thumbnail: the title is on at frame 0, not fading in.
6. **End card.** The product name, one line, the facts (e.g. the agents it ships with). It keeps growing slightly to
   the last frame; no dead hold.
7. **Sound** (`assets/score.example.tsx`): Tone synths at module level, `Transport.start()` at top level (without it
   the track is silent, −70 LUFS), a soft kick per beat + a chord per bar, one small sound per UI event read from
   `AT` (key clicks, pings on blooms, a thud on landings, a whoosh into each isolation field), `<Mix lufs={-14}
   ceiling={-1.5} />`. Keep transients low (kick −20 dB, thud −12 dB) or the master's limiter flat-tops them.
8. **Composition file** (`assets/composition.example.tsx`): `registerRoot` once; `<Cut />` plus `{score()}`.
   Versions are `compositions/NAME-v2.tsx`; keep v1 rendering.

## Render, check, post

```bash
raea render compositions/NAME-vN.tsx -o out/stills --at 0,…   # stills sheet at every scene, read each by eye
raea render compositions/NAME-vN.tsx -o out/NAME-vN.mp4 --manifest out/NAME-vN.render.json
raea check out/NAME-vN.mp4 --manifest out/NAME-vN.render.json > out/check-vN.txt; grep -E "^\s*error" out/check-vN.txt
ffmpeg -nostats -i out/NAME-vN.mp4 -af ebur128=peak=true -f null - 2>&1 | grep -E "I:|Peak:"   # −14 LUFS, peak < −1
raea show out/NAME-vN.mp4 --title "…" --project WORKSPACE/PROJECT     # later: --replaces ITEM
```

Fix every check error or look at the frame and record why it's a false positive (off-frame text during a push-in;
text inside a card scaled by an isolation field). Footage from screen recordings: `ffprobe` first; raea refuses VP9
in .webm/.mov, AV1 and HLG, so transcode to H.264.

## Lecture/deck exports

```bash
ffmpeg -y -i out/NAME-vN.mp4 -vf scale=540:-2 -c:v libx264 -crf 23 -pix_fmt yuv420p -c:a aac -b:a 128k -movflags +faststart lecture/animate/NAME-540.mp4
raea render compositions/NAME-vN.tsx -o DIR --at <one frame per scene>   # then tile=3x3 → lecture/animate/final-stills.png
```

Worked example: `~/raea/showreel/projects/prose-video` (prose-eval, 28 s, `compositions/prose-v2.tsx`).
