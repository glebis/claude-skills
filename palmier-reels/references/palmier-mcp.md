# Palmier Pro MCP — behaviour that matters for reels

Endpoint `http://127.0.0.1:19789/mcp` (streamable HTTP, SSE responses; `scripts/palmier.py` handles the session).
Always re-read `get_timeline` after structural edits: ids and track indexes shift.

## Tracks and clips
- Track 0 renders on top. `add_texts` / `add_clips` without `trackIndex` create a **new top** track (audio: new bottom audio track). Name it immediately (`manage_tracks set`).
- Clips on the **same track overwrite** each other when they overlap — anything that must coexist in time needs its own track (date label vs card word, two hits, etc.).
- Removing every clip of a track removes the track (indexes shift).
- `create_timeline {from}` duplicates (new ids) — the versioning primitive; never edit the approved timeline in place.
- Nesting: `add_clips {mediaRef: <timelineId>}` places a live nested timeline (used for the film-jitter master).
- Library `organize_media {deletes}` removes assets; importing a folder imports *everything* in it recursively (keep work folders clean).

## Text
- 1 canvas point ≈ **1.75 px** on a 1080-wide canvas (measured from exports). Wrap with PIL metrics × K.
- `transform.x` = left edge for left alignment, **centre** for the default centre alignment — always pass `alignment: left`.
- `transform.y` = vertical **centre** of the auto-fit box. Position keyframes use the **top-left**. Mixing static centre and keyframed top-left on consecutive clips causes a visible jump → never add position keyframes to word-reveal clips.
- `lineSpacing` is additive points. Natural line height differs per font (Manrope ≈ 1.42×, Helvetica Neue ≈ 1.22×): `lineSpacing = (target − natural) × pt`.
- Text animation presets (`wordReveal`, `wordSlide`, …) run at a **fixed 6 frames/word** — no control. For paced word reveal build cumulative prefix clips (words 0..j), alternate them on two tracks, overlap by the fade length, padding missing lines with NBSP so the box height never changes.
- Blur on an incoming prefix clip smears the identical earlier words underneath — fade opacity only; keep blur for the final exit.
- Fonts must be installed system-wide (`~/Library/Fonts`); a font lacking glyphs **silently falls back** (Futura Condensed/Medium, Gill Sans, Bodoni 72, Avenir Next Condensed lack Cyrillic). Render a sample before trusting a face.

## Images and motion
- `set_keyframes` position = top-left (0–1), scale = normalized width/height (not a factor), rotation degrees, opacity, blur, volumeDb. Frames are clip-relative. Interp per row: linear/hold/smooth — sample custom easings into linear segments.
- **Blend modes preview but do not render in export.** Knock paper backgrounds out to alpha (`scripts/art.py`).
- Mattes: `import_media {source:{matte:{hex}}}` → full-canvas colour cards.
- `swap_clip_media` keeps edits/keyframes — use it to upgrade placeholder art to final art.

## Audio
- `detect_beats` → downbeats in source seconds. Place music with `source: [start, end]`.
- Volume keyframes on the music clip survive rebuilds that keep the Music track — clear them when ducking is no longer wanted.

## Review and export
- `inspect_timeline` returns 288×512 composites with a grid; frames past the end render black.
- Do not export MP4 until the user approves in Palmier. Export is async: poll `manage_exports`. Verify with ffprobe + full decode + ebur128.
- Telegram: send videos with DocumentAttributeVideo(w,h,duration,supports_streaming) or they display square.
