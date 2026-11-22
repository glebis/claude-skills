# Pacing presets

All presets: hook slide first, CTA slide last, 30 fps, every footage shot with a slight push-in/out.

| preset | footage shots | shot length | cuts/min | transitions | move | use when |
|---|---|---|---|---|---|---|
| **dynamic** | 18–22 | 0.6–1.2 s | 50–60 | hard cuts | 6 % | silent footage, comedy, no music decided |
| **calm** | 8–9 | 1 bar (~2 s) | 20–25 | 0.3 s dissolves | 4 % | slower music, nostalgic tone, longer gestures |
| **music-grid** | 10–12 | 1 bar → ½ bar in the "chorus" → 1 bar | 30–35 | hard cuts on beats | 5 % | a known track (generated or licensed) |

Brief floor: "≥ 20 scene changes per minute". Reels under ~25 s are fine and get watched to the CTA more often; don't stretch thin material by repeating shots.

## Slide timing
- Hook: 1.8 s (dynamic), up to the first downbeat ≈ 3 s (calm), 1 bar (grid). It must be readable: 3 short lines + title/date/button ≈ 1.8 s minimum.
- CTA: 2.6–3 s, or 1.5 bars; land the CTA on the music's final chord/button when there is one.

## Shot-order recipe
1. Open on movement (gesture, laugh) — not a static wide.
2. Within the first third: the best joke as a pair — action (grimace) → reaction (deadpan partner) as separate close-ups cut from the same moment.
3. Alternate sources/locations every shot; alternate framing (wide → close → medium).
4. Middle: wides to reset the eye, a camera move (whip pan) as a natural cut point.
5. Last footage shot: a gesture toward camera/up ("look here") that hands over to the CTA.

## Framing from one clip
`zoom` 1.0 full frame · 1.2–1.5 medium · 1.7–1.9 close-up (720p sources get soft past 1.9).
`c` = crop centre in source fractions; read it off `analyze.py grab` (each grid cell = 0.1). The crop is clamped to the frame, so a face at the very top can't be centred — choose a lower zoom instead.

## Music grid
- Durations in whole beats (`"beats": 4` = 1 bar in 4/4). `grid.py` converts to seconds; `build.py` snaps the cumulative timeline to frames (≤ ½ frame error).
- Calm: 1 shot per bar. Grid: verse 1 bar/shot, chorus 2 beats/shot, release 1 bar, CTA 6 beats.
- With a real file prefer `--beats` (follows drift) over `--bpm`. A fixed grid at a wrong tempo drifts ~0.4 s by 20 s for a 2 BPM error.

## Learned in use
<!-- appended by scripts/learn.py — newest last -->
