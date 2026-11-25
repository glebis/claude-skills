# The kinetic components

All in KINETIC = `~/raea/showreel/projects/kinetic`. Its `README.md` has the full prop tables; this is the map of what
to reach for. Read a component's header comment before changing it.

| File | Reach for it when | Key exports |
|---|---|---|
| `components/tokens.ts` | always: everything reads it | `W H FPS BEAT BAR beats() bars()`, `SAFE`, margins `M` (left 84, right 164, top 250, bottom 460), `TEXT_W` 832, `C`, grounds `ON.ink/paper/red`, `HEAVY MONO SIZE TRACK SPACE`, `widthOf fit`, GSAP eases `E`, `tw prog`, `FEEL`, `CHAIN`, `CHAIN_LIVE`, `ZOOM`, `hash seedOf` |
| `components/type.tsx` | every slide | `Fonts`, `Bg`, `ZoomPlay` (push per 2 bars + beat swell), `Slam` (physics lines), `Stack` (chain title), `Tag` (mono slab), `MonoLines`, `Count`, `Cascade` |
| `components/kinetic.tsx` | letters that are alive, thrown, kicked on the beat; `release` to shatter | `Kinetic`, `FEEL` |
| `components/chain.ts` | a stack of rows that should move as a chain | `chain(rows, mid, len, feel)`. `CHAIN` is calm (near-critical damping); `CHAIN_LIVE` adds `tug` (solid row pulled each beat), `notchX` (sideways shove on the bottom rows) and `couple` (knocks travel both ways). Use `CHAIN_LIVE` when the person should *see* physics |
| `components/warp.tsx` | a word that bends (wave, bulge, twist, stretch, shear, meter, melt) yet reads | `Warp`, `warpPath`, `WARP.*`, `pulse(f, {rest, peak})` |
| `components/typeplay.tsx` | a word acting out its meaning | `Typewriter`, `LetterGrid`, `Bounce`, `BallLetter` (bouncing-ball exercise with spacing ghosts and a graph editor), `Meter`, `Slices`, `PinnedNumeral` (giant numeral holds, the word beside it rolls), `Accrue` (items thrown onto an elastic chain, docking into a list) |
| `components/transitions.tsx` | cuts between scenes | edges `ZoomThrough TypeMask ChainWhip SlabPush ElasticSplit InkLine Iris Wipe Swipe` in `EDGES`; scene-moves `Shatter`, `MatchLetter` |
| `components/world.tsx` | slides that continue one thought (hook → claim → steps; end card → facts) | `World`, `cell(col,row,layer)`, `Tile` (`hideBefore`, `clearAt`), `Stop` (`tile`, `arc`, `back`, `x`, `y`), `camAt`, `swell`, `GAP` 0 |
| `components/lens.tsx` | always on the edit root | `Lens({k})`: wide-angle bulge; drive `k` with `lensAt(f)` (edge windows + board xy speed) |
| `components/cursor.tsx` | a pointer that clicks | `ClickCursor({keys, clicks, size, physics, drift})`; `physics={1} size≈220` for the hero cursor |
| `components/space.tsx` | rarely: the 2.5D `Space`/`dolly` underneath `World`; its UI props are retired (type only) | `Space`, `dolly`, `FOCAL` |
| `compositions/glyphs.gen.ts` | generated: advances, cap height, counters, outlines of Manrope 800 | regenerate with `uv run -q --with fonttools --with brotli python3 -I tools/glyph_widths.py` after changing the font or adding characters (€ : – / @ × are in) |

## Newest pieces worth knowing

- **`Swipe`** (edge): thumb flick. The old frame drags back, then is flung off on an arc (pivot below the frame),
  stretching along the throw; the new one is thrown in from the other side on a back ease and lands upright. `dir`
  −1 | 1, `color` for the strip in the gap. Good into an end card; let the card's first line start under it.
- **`PosterLines`** (in the example composition, not a component yet): the end card. Each line `fit([text], 320)`
  to the column width, lines spaced to fill `M.top` to `H − M.bottom − 20` from cap heights, each line an
  overflow-hidden slot whose letters rise in 0.7-frame steps, lines 7 frames apart, a softtick per line, the top line
  red and pressed by the cursor. Promote it to `components/` the first time a second ad uses it.
- **`ClickCursor physics`**: stretch along velocity, lean into sideways moves, squash on press; `drift` keeps it moving
  between keys (it never freezes); the ring scales with `size`.
- **`CHAIN_LIVE`** with `Stack`: the date slide in the example (beat tugs, bottom shove that whips up the stack).

## Copy (default) vs shared

**Copy** (`scripts/scaffold.sh`): each project owns its components. Tune freely per ad; a fix in one ad doesn't reach
others; old ads keep rendering identically. When a fix is general (a trap, a bug), port it back to KINETIC by hand
and note it in KINETIC's README.

**Shared** (on request): raea workspaces have a `shared/` folder with the same five subfolders, and the projects'
`tsconfig.json` already maps `@shared/*` to `../../shared/*`. Move the components to
`<workspace>/shared/components/kinetic/` and `glyphs.gen.ts` beside them, change their `../compositions/glyphs.gen`
imports to `./glyphs.gen`, and import as `@shared/components/kinetic/tokens` (never by a relative path out of the
project). Fonts go to `shared/assets/fonts`. Risk: a change re-renders every older ad differently, so pin with a
version folder (`kinetic-v1/`) once an ad is delivered.

Either way, don't edit KINETIC's own files from a new project's session.
