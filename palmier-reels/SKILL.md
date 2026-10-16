---
name: palmier-reels
description: This skill should be used when creating a vertical narrative reel (Instagram/Telegram, 1080×1920) from scratch in Palmier Pro through its local MCP — turning a script, quotes or lesson notes into a beat-cut timeline with editable typography, word-by-word text, generated art, card transitions, film jitter and ElevenLabs sound — in any visual style (bundled presets or a project's design tokens). Triggers on "make a reel in Palmier", "reel from these quotes", "Godard-style text animation", "apply our design tokens to the reel", "export the reel for Telegram".
---

# Palmier Reels

Build a reel as code: a **spec** (story, scenes, art, music) + a **style** (preset or design tokens) → `scripts/build_reel.py` rebuilds the whole Palmier timeline idempotently. Iterate by editing the spec/style and re-running, not by hand-editing clips.

## Workflow

1. **Connect & inspect.** Palmier must be running (MCP `http://127.0.0.1:19789/mcp`). List projects, read the active timeline, never edit an approved timeline in place (duplicate or build a new one).
2. **Story first.** Draft scene copy as a causal chain: card word → editorial `context` line → `text` (emphasis or verbatim quote). Apply `references/perception.md` (≤ ~2.5 words/s, quotes verbatim with at most one […], ≥ 0.6 s cards). Show the user the copy table before building when content matters.
3. **Style.** Pick a preset from `assets/styles/` or overlay tokens: `python3 scripts/style.py <preset> --tokens design.tokens.json`. Then `python3 scripts/fonts.py check <preset> [--tokens …]`; install missing fonts (`fonts.py install <dir>`, e.g. a repo's self-hosted OFL fonts) and render a sample — Palmier silently falls back on missing glyphs. See `references/styles.md`.
4. **Art.** One distinct concept image per scene, matching the brief (generate via Codex/ChatGPT image tools or gpt-image skill when authorized; ask for plain white backgrounds, no text). Knock out to alpha: `python3 scripts/art.py knockout *.png --out art/` (blend modes do not export).
5. **Spec.** Write `spec.json` (`references/spec-format.md`, example `assets/examples/small-habits.json`). Music: cuts snap to downbeats from Palmier `detect_beats`.
6. **Sound (optional).** `python3 scripts/sfx.py spec.json` → ElevenLabs kit + per-scene Foley, measured for placement (`references/sound.md`).
7. **Build.** `python3 scripts/build_reel.py spec.json --dry-run` (prints wraps/cuts), then without `--dry-run`. Rebuild an existing timeline with `--timeline-id ID`. Outputs land in `<workdir>/` (plan, timeline, build log, media cache).
8. **Verify.** `python3 scripts/inspect_frames.py <frames…> --out strip.png` and read the strip: wraps, overlaps with art, safe areas, card holds, first/last word of each reveal. `python3 scripts/mixcheck.py <workdir>` → loudness/peaks + an audio-only preview for the user to listen to.
9. **Film master (optional).** `python3 scripts/jitter.py <timeline-id>` nests the edit with gate weave (`--flicker` only if the style allows animating art opacity).
10. **Review gate.** Hand the timeline to the user in Palmier. Do **not** export until they approve.
11. **Export.** `python3 scripts/export.py <timeline-id> <out-basename> [--telegram-mb 15]` → MP4 + .palmier, verified (probe, decode, ebur128). For Telegram, send with the telegram skill (it attaches video dimensions; resolve chats by id, not fuzzy name).

## Rules of thumb
- Read `references/palmier-mcp.md` before touching tracks, text or keyframes — it lists the traps (same-track overwrite, text box anchors, fixed 6-frame word presets, blur smear, font fallback, blend modes not exported).
- Keep every quote verbatim; editorial lines carry the narrative. Distinguish participants' expectations from results.
- Brand tokens override preset habits; surface conflicts (e.g. grain vs "no texture behind long text") instead of silently picking.
- Report what was verified by frames/measurements vs what needs human eyes/ears (SFX, pronunciation, final feel).
