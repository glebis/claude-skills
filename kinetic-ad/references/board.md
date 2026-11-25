# Board: many slides at once, and moves between them

`assets/components/board.tsx` (copied to `components/board.tsx` by `scaffold.sh`) sits on top of `World`. Write the
slides and a list of camera moves, and it computes the stops. `assets/examples/board-demo.tsx` (copied to
`compositions/board-demo.tsx`) uses every move and every entry once in 6 bars; render it before designing a board.

Use a board when slides continue one thought (a list, steps, facts around an ask, a before and after) and the viewer
should see that they belong together. A cut with an edge says "new thought"; the board says "same surface, look over
here".

## Slides

```ts
const SLIDES: Slide[] = [
  { id: "ask", col: 0, row: 0, bg: C.ink, node: <EndCard /> },
  { id: "date", col: -1, row: 0, bg: C.red, node: <Fact word="26 NOV" /> },
  { id: "price", col: 1, row: 0, bg: C.paper, node: <Fact word="€50" />, enter: { at: 150, kind: "drop" } },
];
```

- A grid of `col`, `row` (any integers, 0 is anywhere you like) and `layer` (1 = behind, for dives). Slides butt edge
  to edge: no gutters.
- **Grounds in a Latin square**: no two neighbours share a ground (3×3: red/paper/ink, paper/ink/red,
  ink/red/paper). Same-colour neighbours merge into one slab in an overview.
- `enter` brings a slide onto the board while it's being watched, so time it inside an overview's `hold`:
  `slide` (from the side, `dir`), `drop` (from above, landing with a lip), `rise` (forward from the layer behind),
  `pop` (forward and back into place). `len` defaults to a beat. Start entries on beats, a beat or two apart.
- An entering slide on an **ink** ground can't be seen against the empty ink board until it lands. Give the big
  travels (slide, drop, rise) to red or paper slides; an ink slide pops.
- `from` offsets a slide's own frames (its animation starts when the camera gets there, not at frame 0).

## Moves

```ts
const MOVES: Move[] = [
  { at: 0, to: "ask", hold: 30 },                          // open tight; drift in
  { at: 54, to: "date", by: "pan", hold: 18 },             // to the neighbour, lifting a little mid-move
  { at: 108, to: "price", by: "leap" },                    // out far enough to see both, back in
  { at: 162, to: "all", by: "push", hold: 90 },            // the whole board; entries land here
  { at: 300, to: ["ask", "price"], by: "push", frame: 0.9 },  // a pair, cropped in a little
  { at: 360, to: "ask", by: "push" },                      // back to the ask
];
```

| `by` | The camera | Says |
|---|---|---|
| `push` (default) | straight line: zooms in to a slide, out to a set, or between them | "look closer", "step back" |
| `pan` | sideways with a 250-unit lift mid-move, so both slides show | "and next to it" |
| `leap` | out until both ends are in frame, then in | "over there, on the same board" |

- `to`: a slide id, an array of ids (framed together, their bounding box), or `"all"` (every slide on layer 0).
- `frame`: for sets, 1 frames the set exactly, < 1 crops in (the board runs on past the edges, as in the kinetic
  end card's pull-back, about 0.8), > 1 leaves ground around it.
- `hold`: keep drifting in for that many frames after arriving. Use it on every move that the viewer reads: the
  camera never stops.
- `back`: extra distance (negative pushes in).
- A dive is a push `to` a slide on `layer: 1`. Give the front slide `clearAt` to see through it, and the layer-1
  slides `hideBefore` the dive (no back layers on show).

Timing: arrive on beats, and give a read slide at least a bar of `hold`. Use an overview for 1–2 bars at most. Keep
the camera moving faster than a pan only into the payoff.

## Wiring it into the edit

As a scene: `{ id: "end", bars: 3, world: true, draw: () => <Board slides={SLIDES} moves={MOVES} punch={30} /> }`
(`world: true` skips `ZoomPlay`, since the board camera punches on the beat itself).

Lens: add the board to `lensAt`'s sideways-speed term with `boardStops(MOVES, SLIDES)` and an empty tiles array:
`camAt(lf ± 1, boardStops(MOVES, SLIDES), [], 0)` (the demo's `lensAt` shows it). Pushes and leaps in depth get no lens.

SFX: a whoosh on each pan and leap (−11 dB, on the move's start), a soft swish or tick on each entry landing, and
nothing on pushes in (they're the calm moves).

## Limits

- `Space` fades planes beyond 6000 units. An overview reaches about 5 slides across or 3 rows down; beyond that,
  frame a subset.
- Everything in the overview is tiny. The quick check flags overview frames for text running off the frame and
  for safe areas, because edge slides cross the safe lines. That's inherent to a board shot: read those frames by
  eye. What must be read lives in a slide you push into, not in the overview.
- Moves resolve to fixed x/y/z (cached by the `MOVES` array identity): keep `MOVES` and `SLIDES` as module
  constants, not arrays built inside a component.
