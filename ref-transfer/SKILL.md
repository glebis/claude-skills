---
name: ref-transfer
description: Break a reference video (an ad, a launch film, a YouTube link or a local file) into a measured shot list, a scenario and a board of stills, then transfer its moves onto the user's own product as a 25–30 s shot plan with a user story and the real interface moment for each shot. Use when the user says "analyse this ad", "break down this reference", "shot list from this video", "make our video like this one", "steal the structure of this film", "transfer this reference to my app", or gives a video link as a model for a product video. Step zero of the interface-to-video chain (ref-transfer → design-tokens → user-journeys → ui-motion → animate). Uses raea media/song and ffmpeg.
---

# ref-transfer

The reference is for analysis only. Never put a clip of it into the deliverable.

## 1. Get the reference
- A link the user gave is approval to download it. Keep it under the project's `refs/`:
  `yt-dlp -f "bv*[height<=1080]+ba/b" --merge-output-format mp4 -o "refs/<name>.%(ext)s" URL`
- If YouTube's bot check blocks it: add `--cookies-from-browser chrome:"Chrome Beta"` (or the user's browser)
  and make sure `deno --version` is ≥ 2.9, since yt-dlp uses it as the JS challenge solver.

## 2. Measure it (deterministic)
```bash
raea song refs/<name>.mp4 -o refs/<name>.song.json --srt none --plot refs/<name>.song.png
python3 ~/.claude/skills/ref-transfer/scripts/shots.py refs/<name>.mp4 -o lecture/ref-transfer --song refs/<name>.song.json
```
`shots.py` writes `shots.json` (start, duration, transition, motion, beats per shot, cut-to-beat offset, song hits),
`shots.md` (a table with empty description columns), `stills/shot-NN.jpg` and `board.png`.
Tune with `--threshold` (drop weak cuts; morph-heavy ads need 0.15–0.2), `--merge` (fold a transition's cluster of
cuts into one) and `--min-shot`.

Then measure the motion and rhythm (dense optical flow, OpenCV):
```bash
python3 ~/.claude/skills/ref-transfer/scripts/motion.py refs/<name>.mp4 -o lecture/ref-transfer \
  --song refs/<name>.song.json --shots lecture/ref-transfer/shots.json
```
It writes `motion.json` and `rhythm.png`. Per frame it records speed, pan/tilt, zoom, the share of the frame moving
and a motion kind. Each motion event gets attack, decay, an easing label and an overshoot flag. It also compares
onsets, peaks and cuts with the beats and hits *against chance*. Report what the numbers say: pulse length,
how much of the time things hold still, spring vs linear, where the energy is, and whether motion is beat-locked
or phrase-led. Caveat: flat, textureless backgrounds hide camera moves from optical flow.

## 3. Watch and describe (the agent's part)
Read `board.png`, and for long shots (> 6 s) a denser grid:
`ffmpeg -i REF -vf "fps=1/2,scale=320:-1,tile=8x9" -frames:v 1 grid.png`.
Fill `shot-list.md` from `shots.md` (add a Motion and rhythm section from `motion.json`): per shot, **what the shot does** (its job in the story), **camera**
(push, pan, whip, static, continuous take), **type / UI motion** (what moves and how), **sound** (cut on beat,
hits, stops and drops from the song JSON). Say when a description is read from stills rather than playback.
Add the **scenario**: 4–6 story beats with time ranges, and **patterns worth stealing** (3–5 lines).

## 4. Transfer to the product
Read the product's docs and its real screens (screenshots, screen recordings). Write `refs/transfer.md`:
1. **The moves**: the 4–6 devices the reference relies on (characters, framing, cutting, pacing, end card).
2. **Mapping table**: reference element → product element (who plays the characters, what replaces each UI moment).
3. **User story**: one sentence, "As a … I want … so I can …".
4. **Shot plan**: 6–8 shots, 25–30 s, at a tempo that puts cuts on bar lines. Columns: #, time, dur, ref shot,
   what the viewer sees, interface moment (a real screen file), motion, on-screen text (≤ 6 words, the video's language).
5. **Rules carried over**: real UI only, one component per shot, cut timing.
Copy `transfer.md` into `lecture/ref-transfer/` too, and tell whoever builds the video where it is.

## Slides
`scripts/table_png.py FILE.md -o OUT.png [--cols 0,1,3] [--title …]` renders the first markdown table of a file as a PNG
(the shot list, the mapping, the shot plan).

## Output
`lecture/ref-transfer/`: `shot-list.md` + `shot-list.png`, `shots.json`, `motion.json` + `rhythm.png`, `board.png`, `stills/`, `song.png`,
`transfer.md` + `transfer-mapping.png` + `transfer-shot-plan.png`.
For a single picture that sets reference and product side by side, run the `visual-board` skill next.
