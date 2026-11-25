# Music and sound effects

Both tools are copied into the project by `scaffold.sh` and run **from the project root** (they use relative
`assets/...` paths).

## Music: lock, kick, drop, master — `tools/kick.py`

The picture runs at 100 bpm (beat 0.6 s). The track must sit on that grid.

1. **Measure, don't trust a beat tracker.** `raea song FILE --plot` and librosa onsets give the note period; triplet
   arpeggios read at 1.5× (a 99.06 bpm piece reads 148.6). Find the true period (`STEP0`) and first note (`PHASE0`).
2. **Lock.** `kick.py` speeds the track by `STEP0 / 0.2` with ffmpeg `atempo` (pitch kept) and verifies the 0.2 s grid
   fit after the stretch (prints `R`; near 1 is locked). For a new track, set `SRC`, `STEP0`, `PHASE0` at the top of
   the copied `kick.py` (the grid constant 0.2 s assumes the note is a triplet of a 0.6 s beat; adjust if not).
3. **Kick.** Synthesised four on the floor, one per beat, voices `deep` (sine 110→45 Hz, the chosen one), `punch`,
   `sub`, `eleven` (an ElevenLabs sample). Audition with `--preview` (12 s over the track into `out/`) and let the
   person pick; play previews with `raea show` or cenno's `audio`, never QuickTime.
4. **Drop on a cut.** `--drop=FRAME` brings the kick in at that edit frame after a one-bar high-pass build
   (20→700 Hz), with sidechain ducking of the track under each kick. FRAME must be a cut from `TIMELINE`
   (`cutOf("…")`): print it from the composition or compute bars × 72. **Re-run whenever a scene length before the
   drop changes.**
5. **Master.** Track + kick ×0.45, high-pass 28 Hz, EQ, glue `acompressor`, `alimiter` 0.89 →
   `assets/music/music-master.wav`. The composition plays it with `startFrom` = first-note frame and `Mix lufs={-14}`.

```bash
uv run -q --with numpy --with soundfile --with librosa python3 -I tools/kick.py deep --preview
uv run -q --with numpy --with soundfile --with librosa python3 -I tools/kick.py deep --drop=576
```

No track? The kick alone (with a short build) works for a 20 s piece; generating music is a separate ask (raea's
`gen` or ElevenLabs music), not a default.

## SFX: ElevenLabs — `tools/eleven_sfx.py`

- `SFX` dict: name → (prompt, seconds). Prompts are short, dry, single-event, "no music, no reverb". Minimum 0.5 s
  (0.4 returns 400). Light choices that were liked: `swish` (soft brush across paper), `softtick` (muted wooden tick).
- Existing files are kept; to remake one, `trash` it first.
- Every clip is trimmed of leading silence and **levelled** (peak > −1 dBFS → −3; peak < −20 → −9): ElevenLabs returns
  some clips already clipped and some near silent. `--level` re-levels existing files.
- Key from SOPS (`ELEVENLABS_API_KEY` in `~/.claude/skills/secrets.enc.yaml`). Run as:

```bash
OPENAI_API_KEY="" SOPS_AGE_KEY_FILE=$HOME/.config/sops/age/keys.txt python3 -I tools/eleven_sfx.py
```

If the key still comes back empty or 401, ask via the osascript hidden-answer dialog.

`scaffold.sh --with-sfx` copies the 14 already-levelled clips from KINETIC (click, whoosh, dive, shatter, key, pop,
whip, tick, impact, zoom, tear, kick-eleven, swish, softtick), which cover a whole ad; generate only what's new.

## Mix check

The full `raea check` on the 320k file reports integrated loudness (target −14 LUFS), true peak (< −1 dBTP) and
clipping. Clipping at a frame almost always means an unlevelled SFX clip there.
