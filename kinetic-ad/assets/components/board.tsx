// A Board: many slides seen at once, and the camera moves between them. Built on World (components/world.tsx).
//
//   moves  →  the camera: frame one slide, several, or the whole board; get there by a straight push (zoom in or
//             out), a pan (lifts a little mid-move so both slides show), or a leap (out far enough to see both, then
//             back in); `hold` keeps drifting in after arriving, so the camera never stops.
//   slides →  tiles on the grid (col, row, layer), edge to edge; an `enter` brings one onto the board while it is
//             being watched: slide in from the side, drop from above, rise from the layer behind, or pop forward.
//
// The moves resolve to plain x/y/z Stops (cached per moves array), so slides moving in never shift the camera, and
// the composition's lens can follow the same stops with camAt(f, boardStops(moves, slides), []).
// Space fades planes further than 6000 units: an overview frames at most ~5 slides across (or 3 rows down).
import { useCurrentFrame } from "raea";
import type { ReactNode } from "react";
import { FOCAL } from "./space";
import { E, H, W, tw } from "./tokens";
import { LAYER, World, cell, type Stop, type Tile } from "./world";

export type Enter = {
  /** board frame it starts entering (it isn't drawn before) */
  at: number;
  /** frames to arrive; default 18 (a beat) */
  len?: number;
  kind: "slide" | "drop" | "rise" | "pop";
  /** for "slide": -1 comes from the left, 1 from the right */
  dir?: -1 | 1;
};

export type Slide = {
  id: string;
  col: number;
  row?: number;
  layer?: number;
  bg?: string;
  /** what it shows; its frames count from `from` (board frame) */
  node: ReactNode;
  from?: number;
  enter?: Enter;
  hideBefore?: number;
  clearAt?: number;
};

export type Move = {
  /** board frame the camera arrives */
  at: number;
  /** a slide id, several ids framed together, or "all" (every slide on layer 0) */
  to: string | string[];
  /** how it gets there from the move before: "push" straight (zoom in/out), "pan" with a small lift, "leap" out to see
   *  both ends then back in. Default "push". */
  by?: "push" | "pan" | "leap";
  /** frames to keep drifting in after arriving (a slow push of 30 units), so it never holds still */
  hold?: number;
  /** for a set: 1 frames it exactly, < 1 crops in (the board runs past the frame's edges), > 1 leaves ground round it */
  frame?: number;
  /** world units added to the framing distance (negative pushes in) */
  back?: number;
};

const home = (s: Slide) => cell(s.col, s.row ?? 0, s.layer ?? 0);

/** The camera key that frames `to`. */
function framing(to: Move["to"], slides: Slide[], frame = 1) {
  const ids = to === "all" ? slides.filter((s) => (s.layer ?? 0) === 0).map((s) => s.id) : Array.isArray(to) ? to : [to];
  const set = ids.map((id) => {
    const s = slides.find((x) => x.id === id);
    if (!s) throw new Error(`Board: no slide "${id}"`);
    return home(s);
  });
  const xs = set.map((p) => p.x), ys = set.map((p) => p.y);
  const x0 = Math.min(...xs), x1 = Math.max(...xs), y0 = Math.min(...ys), y1 = Math.max(...ys);
  const k = set.length === 1 ? 1 : Math.max((x1 - x0 + W) / W, (y1 - y0 + H) / H) * frame;
  return { x: (x0 + x1) / 2, y: (y0 + y1) / 2, z: Math.min(...set.map((p) => p.z)) - FOCAL * k };
}

const STOPS = new WeakMap<Move[], Stop[]>();

/** The moves as World Stops (x/y/z, with arcs for pans and leaps). Same array in → same array out. */
export function boardStops(moves: Move[], slides: Slide[]): Stop[] {
  const hit = STOPS.get(moves);
  if (hit) return hit;
  const out: Stop[] = [];
  let prev: { x: number; y: number; z: number } | undefined;
  for (const m of moves) {
    const p = framing(m.to, slides, m.frame);
    const z = p.z - (m.back ?? 0);
    let arc = 0;
    if (prev && m.by === "pan") arc = 250;
    if (prev && m.by === "leap") arc = FOCAL * Math.max(Math.abs(p.x - prev.x) / W, Math.abs(p.y - prev.y) / H) * 1.1;
    out.push({ at: m.at, x: p.x, y: p.y, z, arc: arc || undefined });
    prev = { x: p.x, y: p.y, z };
    if (m.hold) {
      out.push({ at: m.at + m.hold, x: p.x, y: p.y, z: z + 30 });
      prev = { x: p.x, y: p.y, z: z + 30 };
    }
  }
  STOPS.set(moves, out);
  return out;
}

/** The slides as World tiles at board frame f, with any entering one on its way in. */
export function boardTiles(slides: Slide[], f: number): Tile[] {
  return slides.map((s) => {
    const p = home(s);
    const t: Tile = { id: s.id, ...p, bg: s.bg, node: s.node, from: s.from, hideBefore: s.hideBefore, clearAt: s.clearAt };
    const e = s.enter;
    if (!e) return t;
    const len = e.len ?? 18;
    t.hideBefore = Math.max(t.hideBefore ?? -Infinity, e.at);
    if (e.kind === "slide") t.x += (e.dir ?? 1) * W * tw(f, e.at, e.at + len, 1, 0, E.out);
    if (e.kind === "drop") t.y -= H * tw(f, e.at, e.at + len, 1, 0, E.back);
    if (e.kind === "rise") t.z += LAYER * tw(f, e.at, e.at + len, 1, 0, E.out);
    if (e.kind === "pop") t.z -= FOCAL * 0.45 * tw(f, e.at, e.at + len, 1, 0, E.back);
    return t;
  });
}

/** The board seen by the camera along the moves. `f` is the Board's own frame (its Sequence's). */
export function Board({ slides, moves, bg, punch }: { slides: Slide[]; moves: Move[]; bg?: string; punch?: number }) {
  const f = useCurrentFrame();
  return <World tiles={boardTiles(slides, f)} stops={boardStops(moves, slides)} bg={bg} punch={punch} />;
}
