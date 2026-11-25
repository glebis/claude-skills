---
name: kinetic-ad
description: This skill should be used when making a short vertical (9:16, 1080×1920) kinetic-type promo or ad video in raea in the ink/paper/red style — Manrope 800 uppercase with IBM Plex Mono, physics letters, elastic chains, warped vector type, a 2.5D board camera, wide-angle lens cuts, all on a 100 bpm beat grid with a synthesised kick and ElevenLabs SFX. Triggers on "make a kinetic ad", "kinetic type promo", "another ad like the workshop one", "vertical ad in raea in the kinetic style", "reel for my event/workshop/launch in that style", or when starting a new raea project from the kinetic components.
---

# Kinetic ad (raea)

A 20–45 s vertical ad where type carries every fact and never stops moving. The motion system lives in a reference
raea project, `~/raea/showreel/projects/kinetic` (call it KINETIC). Its `README.md` documents every component and
transition, `METHOD.md` the slide-design method, and `compositions/workshop-ad.tsx` is a complete worked example.
Read those rather than re-deriving anything; this skill says how to use them for a new piece.

Load the `raea` skill too: it owns the CLI, workspaces, `raea check`, `raea render` and `raea show`.

## When to use

- A promo, launch, event or workshop ad, 9:16, mostly or entirely type, with a hard beat.
- The person wants the "kinetic" look: ink #090909 / paper #f3f0e8 / red #d01920, Manrope 800 uppercase at −0.045 em,
  IBM Plex Mono 500 labels, physics and chain motion.
- Not for footage-led edits, narrated explainers or horizontal pieces (the margins and safe areas are 9:16 only).
  A different palette or font is fine: change `components/tokens.ts` (and regenerate glyphs for a new font), nothing else.

## Workflow

Work in frames. Grid: 30 fps, 100 bpm, `BEAT` 18 frames, `BAR` 72. Every scene starts on a bar line.

1. **Project.** Settle the workspace and project per the raea skill (`raea project new NAME`). Then copy the system in:
   `bash ~/.claude/skills/kinetic-ad/scripts/scaffold.sh <project dir> [--with-sfx]` (copies components, tools, fonts,
   glyph tables, package.json, tsconfig; links `compositions/media`; npm install). Copying is the default: each ad
   owns its components, so tuning one never breaks another. See `references/components.md` for the shared-folder
   alternative.
2. **Brief.** Write `brief.ts`: who it's for, the one thing the viewer should believe, what it is not doing.
   Ask up front: type only, or with illustrations? (Default and strong recommendation: type only.) Language on screen?
   Is there a music track, or should the kick carry it alone?
3. **Facts.** List every fact with its source (listing, page, the person's words): dates, times with timezone, price,
   what's included, the call to action. Never invent one. No URL on screen: "LINK IN BIO". Show the list for a yes.
4. **Scene table on the bar grid.** One fact per slide, the shortest true line, a hero word and a mono support. Fact
   slides 1 bar; 2 bars only when something plays out. Hook lands on frame 0 (it is the thumbnail). End card 3 bars.
   Write it as a table (bars, scene, material, how it enters) and show it before building. Pattern from the example:
   board (hook → claim → detail dive) · date · numeral · extras · end card.
5. **Components.** Build `compositions/<name>.tsx` on the example's skeleton (`SCENES` → `TIMELINE` → `Edit` with
   `Lens`, `SFX` table, `Mix`). Pick materials and edges with `METHOD.md` §3 and §6; make each word act out its
   meaning (`typeplay`). `references/composition.md` has the skeleton and the moving parts.
6. **Stills sheets.** `raea render FILE.tsx --at F1,F2,...` at each scene's beat peak and rest and at every cut, tile
   them, and read every word by eye. Show the sheet before the first full render of a new scene.
7. **Quick check.** `raea check --quick FILE.tsx` (safe areas, clipped text). Include the very last frame.
8. **Music and SFX** (`references/audio.md`): lock the track to 100 bpm, place the kick drop on a cut computed from
   `TIMELINE`, master; generate and level SFX; place them in the `SFX` table.
9. **Render.** `raea render FILE.tsx -o out/NAME-vN.mp4 --manifest out/NAME-vN.render.json` and the same to `.wav`;
   remux to 320 kbps AAC (raea's own AAC is ~127k):
   `ffmpeg -y -i out/NAME-vN.mp4 -i out/NAME-vN.wav -map 0:v -map 1:a -c:v copy -c:a aac -b:a 320k out/NAME-vN-320.mp4`
10. **Full check.** `raea check out/NAME-vN-320.mp4 --manifest out/NAME-vN.render.json`. Expect −14 LUFS, true peak
    under −1 dBTP. Errors inside lens windows are the checker reading each slice's copy: look at those frames by eye,
    and look at every flagged frame outside them. Filter the JSON instead of printing it whole (context fills fast).
11. **Post.** `raea show out/NAME-vN-320.mp4 --project WORKSPACE/ID` (later versions add `--replaces ITEM`). Commit
    with explicit paths after checking the branch and other sessions' changes. Never open QuickTime.

Iterate from the person's comments; one version per round, each rule below applied before they have to ask.

## The rules

`references/checklist.md` is the checklist to run before every render: design rules (type only, no gutters or back
layers, physics with a visible nudge, slides don't linger, poster end card, exaggerated cursor, light levelled SFX)
and the raea traps (`clip-path` %, the 8192 px atlas, lens copies in the checker, the 0.5 s ElevenLabs minimum,
events hidden under an edge, drop retiming). Each rule came from a real round of feedback.

## Files

- `scripts/scaffold.sh` — copy the system from KINETIC into a new project.
- `references/components.md` — what each component is for, where it lives, copy vs shared.
- `references/composition.md` — the composition skeleton: scene table, timeline, edges, lens, SFX table, mix.
- `references/audio.md` — BPM lock, synthesised kick, drop on a cut, master; ElevenLabs SFX and levelling.
- `references/checklist.md` — design rules and raea traps.
