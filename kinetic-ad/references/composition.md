# The composition skeleton

Copy the structure of KINETIC `compositions/workshop-ad.tsx`; don't copy its scenes. The moving parts:

## Scene table → TIMELINE

```ts
type Edge = { kind: keyof typeof EDGES; len: number; props?: Record<string, unknown> };
type Scene = { id: string; bars: number; draw: (len: number) => ReactNode; into?: Edge; world?: boolean };
const SCENES: Scene[] = [ /* one entry per row of the scene table */ ];
const TOTAL = Math.round(BARS * BAR);  // BARS = sum of scene bars
```

`TIMELINE` (copy it verbatim) turns scenes into Sequences: `cut` is the scene's bar line; a scene with `into` starts one
beat early (`seqFrom = cut − BEAT`) and runs half the next edge past its own end. The In edge gets
`delay = BEAT − len/2`, so it is centred on the cut. Derive every other frame from it: `seqOf(id)`, `cutOf(id)`.
Never hard-code an edit frame that depends on scene lengths (SFX, the kick drop, lens windows).

Edge lengths are 12, 18, 24 or 36 frames. Each edge at most twice per piece. Pick by meaning (METHOD.md §6):
`Swipe` into an end card, `Iris` out of a button or a +, `ChainWhip` for a hard section change, `SlabPush` "and then"
with a label (`hold` 0.4 keeps the label up ~1 s), `InkLine` a calm turn, `ZoomThrough` "go inside". `TypeMask` read
as creepy once: avoid unless the word really opens onto the next thing.

## Boards

A `World` scene holds slides that continue one thought. `cell(col, row, layer)` places tiles edge to edge; `Stop`s
key the camera (`back` pulls back, `arc` pulls back mid-pan, a tile on layer 1 is a dive). Rules: tiles of a deeper
layer get `hideBefore` (they don't exist until the dive), no debris, small arcs (~250), and the first stop opens tight
on the hook so frame 0 reads as a thumbnail. `World` scenes skip `ZoomPlay` (the camera already punches each beat).

## Edit root

```tsx
<AbsoluteFill style={{ background: C.ink }}>
  <Fonts />
  <Mix lufs={-14} ceiling={-1.5} />
  <Sequence from={0} durationInFrames={TOTAL} layout="none"><Audio src={staticFile("music/music-master.wav")} startFrom={3} bus="music" fadeOut={1.6} /></Sequence>
  {SFX.map(([at, name, gainDb], i) => <Sequence key={i} from={at} durationInFrames={45} layout="none"><Audio src={staticFile(`sounds/sfx/${name}.wav`)} bus="sfx" gainDb={gainDb} /></Sequence>)}
  <Lens k={lensAt(f)}>{/* TIMELINE map: ZoomPlay unless world, Out edge of next, In edge of this */}</Lens>
</AbsoluteFill>
```

`startFrom` is the frame of the music file's first note (3 in the example; measure it for a new track).

## lensAt

`k = max(LENS_EDGE · sin(π·t) over each edge window, LENS_MOVE · min(1, boardSpeed/0.05)^1.5 over each World)`, with
`LENS_EDGE` 0.42, `LENS_MOVE` 0.36, and `boardSpeed` from `camAt` in **x/y only** (z speed blacks out dives). Copy it
from the example; list every `World` scene in its `boards` array.

## SFX table

`const SFX: [frame, name, gainDb][]`, every frame from `seqOf`/`cutOf`/the scene's own constants. One sound per
visible action: click on a press (−2 dB, one frame early), whoosh on pans and edges (−9…−14), dive, shatter on a
release, key per typed letter, softtick per poster line (−10), swish/impact for landings (−14…−16). Lighter is better;
harsh hits were rejected.

## Timing rules of thumb

- Entrances on beat lines (multiples of 18 from the scene's cut), letters staggered 1–6 frames.
- A scene's first event that must be seen comes after its In edge clears (`cut + len/2`); anything earlier is under
  the edge. Starting under the edge on purpose (the poster's first line rising as the Swipe lands) avoids an empty
  arrival.
- Reading time ≥ 1 s for anything read (~0.3 s a word). Fact slides 1 bar.
