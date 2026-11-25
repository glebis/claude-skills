# Checklist before every render

Each line came from a round of feedback or a failed render on the first kinetic ad.

## Design

- [ ] **Type only.** No UI windows, illustrated props or debris. If something must be shown, a word acts it out
      (typeplay) or is styled as the thing (a button, a playhead).
- [ ] **Precise, not gestural.** A word about a craft uses that craft's real move (ANIMATION does the bouncing-ball
      exercise with spacing and a graph editor; a "curve" was "too primitive").
- [ ] **No visible gutters or back layers.** `GAP` 0; deeper tiles `hideBefore` the dive; small pan arcs.
- [ ] **Visible physics.** Chains get a beat tug and a nudge on the bottom row that travels up (`CHAIN_LIVE`);
      landings knock what's above them. Physics resting in a spring reads as nothing.
- [ ] **Nothing lingers, nothing freezes.** Fact slides ~1 bar; hook ~1 bar; something always moves (zoom, material,
      cursor drift).
- [ ] **Hook on frame 0.** The first frame is the thumbnail: the hero word already landed, camera tight.
- [ ] **End card = one block of large type,** each line fit to the column, filling the safe area, built line by
      line; the ask (SIGN UP) in red; "LINK IN BIO", no URL.
- [ ] **Hero cursor exaggerated:** ~220 px, `physics={1}`, clicks visibly (dip + ring + click SFX), never holds.
- [ ] **One red accent per frame;** alternate grounds between cut slides.
- [ ] **Word space** `SPACE` 0.42 em (one-letter words stay words).
- [ ] **Edges used at most twice,** chosen by meaning; lens swell on cuts and pans.
- [ ] **Facts traceable** to the source; on-screen language agreed.
- [ ] **Light SFX,** one per action; nothing harsh.

## raea traps

- [ ] `clip-path: inset(%)` does nothing: use px insets or draw a rect.
- [ ] Perspective-transformed elements are rasterised at their own size into an 8192 px atlas: keep 3D boxes narrow
      (the lens uses w+1 px slices). "Drawn without N of its images" = atlas overflow.
- [ ] `Fisheye`/`LensDistortion` are 3D only; use `Lens` for 2D.
- [ ] Lens frames: the checker reads every slice's copy of the text. Triage by frame range (`lensAt` > 0) and look by
      eye; then look at every flagged frame *outside* those windows. Don't ship with unseen flags.
- [ ] Known checker misreads: fast shatter letters, contrast mid-pan, transient labels under a pull-back. Keep a list
      per version; anything new gets looked at.
- [ ] No `-webkit-text-stroke`, no `mix-blend-mode`.
- [ ] Hooks before any early return (`const early = useEarly(...)`, then `if (early) return null`).
- [ ] Events in a scene's first `len/2` frames are hidden under its In edge.
- [ ] Changed a scene length? Re-run `kick.py --drop=<new cut>`; SFX and lens follow automatically only if they are
      derived from `TIMELINE`.
- [ ] Last frame checked too (the end camera's final push-in can push type into a safe zone).
- [ ] Audio: render `.wav`, remux to 320k AAC; ElevenLabs ≥ 0.5 s; every clip levelled; −14 LUFS.
- [ ] Determinism: no state, timers or unseeded randomness; physics steps from frame 0 at fixed 1/60 s.
- [ ] Shell: absolute paths (no `cd ../..`), `trash` not `rm`, no foreground `sleep`, filter check JSON before
      printing it.
