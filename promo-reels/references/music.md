# Music

## Modes
- **none** — deliver silent; the user adds a track inside Instagram (licensed there).
- **generate** — ElevenLabs Music (`music.py`), instrumental, length = reel + 1 s, 2 takes.
- **licensed <track>** — never embed (Instagram mutes it). Build on its tempo, deliver silent + click preview, say where in the song to start.
- **file <path>** — the user's own/licensed file: `beats.py` it, cut on detected beats.

## Prompt pattern (generate)
`Instrumental <era/genre> cue for <what the reel promotes>, <mood words>. <Lead instrument> carries the melody; <rhythm section>; <colour instruments>. <Recording texture>. <Feel> around <BPM> BPM, starts on the downbeat, ends with a clear final button.`

Worked for a documentary comedy theatre show:
- 1970s comedy film cue: xylophone lead, swinging brushed drums, walking bass, muted trumpet + clarinet, warm analog tape, laid-back shuffle ~112 BPM, ends on a gentle chord.
- Accordion bittersweet waltz, pizzicato, toy piano, 126 BPM.
- 90s lo-fi: Casio melody, drum machine, 120 BPM.

## Checks
- **Key is not obeyed.** In testing 3 of 3 takes missed a requested D minor (C major, E minor, Eb major), even with the key first and a chord progression in the prompt. `music.py --key` detects the key and transposes takes in the right mode (phase vocoder, tempo kept); wrong-mode takes need another generation.
- **Tempo** from `beats.py`; the requested BPM is approximate (asked 128/112, got ~117/112).
- **Loudness**: `mix.py` targets −14 LUFS and corrects a missed single-pass loudnorm (one cue came out at −12.7).
- Downbeat detection is heuristic (strongest phase of 4); check that cuts feel on "1".

## Licensed tracks
Published tempos disagree (e.g. one 1972 single listed at 101, 103 and 130 BPM; live drums drift). Use the most-cited value with `grid.py --bpm`, render `mix.py --click BPM` for a timing preview, and offer to re-grid from the real file.

## Learned in use
<!-- appended by scripts/learn.py — newest last -->
