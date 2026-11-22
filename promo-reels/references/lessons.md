# Lessons (traps hit in production)

## Video
- **VFR phone footage**: a `.MOV` reported 30 fps but ran ~24 fps. Never compute times from frame index × nominal fps — use timestamps (`CAP_PROP_POS_MSEC`); `build.py` resamples with `fps=30`.
- **No `drawtext`** in Homebrew ffmpeg builds without freetype: all text is PNG from Chrome, overlaid.
- **zoompan jitter**: integer crop offsets wobble; zoom on a 2× upscaled canvas.
- **Per-shot rounding drifts off the beat**: snap the cumulative timeline to frames (done in `build.py`).
- **Bad moments look fine on the contact sheet** at 0.5 s steps: a subject walking out of frame or a smeared pan appears only in the rendered shot. Always run `verify.py` and read its sheet.

## Slides
- **Fonts must be loaded before measuring.** A mockup measured with a fallback font fit; the real font overflowed. Measure after `document.fonts.ready`, render in real Chrome.
- **Tight leading (<1) makes glyph boxes stick out of the line** — measure vertical overflow with element boxes, not glyph rects, or every slide "overflows".
- **Padded inline spans double-count lines** if you count rects of the element; count text-node rects only.
- **Shrink-until-fits loops crush everything to the minimum.** Use fill-to-width (one measurement, linear) + a modular scale + one common vertical factor, and fail long copy instead.
- Page zoom (`body.style.zoom`) breaks every measurement — never measure while zoomed.

## Audio
- **Rehearsal audio is rarely captionable.** Shouts and singing: Scribe tagged "[поёт]"/English "What?", Whisper hallucinated Russian sentences on singing. Two engines + a listen before quoting anything.
- **DeepFilterNet erases singing** (speech model) — use the ElevenLabs isolator for singing; DFN gives cleaner silence for speech.
- **DeepFilterNet via pipx breaks when its interpreter disappears** (conda upgrades). Reinstall on a fixed Python: `pipx reinstall --python /opt/homebrew/bin/python3.11 deepfilternet && pipx inject deepfilternet "torch==2.0.1" "torchaudio==2.0.2" "numpy<2"` (0.5.6 breaks with torchaudio ≥ 2.1).
- **Scribe language drift**: with `language_code=rus` it still returned English when the speaker said English words. Trust the detected language field.
- Strip the original audio from finals (room noise) unless the speech is the content.

## Learned in use
<!-- appended by scripts/learn.py — newest last -->

- **2026-11-14 · error** — Before editing, check free space in the project working directory and run a real Chrome slide smoke render with loaded fonts; finding the browser executable alone does not prove rendering works.
  _Evidence:_ The environment check passed, but slide rendering needed an approved retry and separately failed for lack of disk space.

- **2026-11-14 · error** — Review the start, middle and end of every shot and watch the rendered video in motion; compare narrative requirements with timeline positions and distinguish measured checks from visual assessment.
  _Evidence:_ Verification passed despite a visibly soft shot that needed an earlier in-point; the edit table placed a reaction pair after the first third despite the narrative requirement.
