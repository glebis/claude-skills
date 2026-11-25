// Board demo: nine slides on one board, every camera move and every entry once. 6 bars at 100 bpm (14.4 s), no sound.
// Copy into a scaffolded project's compositions/ (it imports ../components/board) and render stills to see each move:
//   raea render compositions/board-demo.tsx --at 0,40,81,135,170,200,230,262,300,360,420
import { AbsoluteFill, Composition, registerRoot, useCurrentFrame } from "raea";
import { Board, boardStops, type Move, type Slide } from "../components/board";
import { Lens } from "../components/lens";
import { BAR, BEAT, C, H, HEAVY, M, ON, W, fit, type Ground } from "../components/tokens";
import { Fonts, Tag } from "../components/type";
import { camAt } from "../components/world";

const TOTAL = 6 * BAR; // 432

function Card({ word, note, on }: { word: string; note: string; on: Ground }) {
  const size = fit([word], 300);
  return (
    <AbsoluteFill>
      <Tag text={note} top={M.top} on={on} />
      <div style={{ position: "absolute", left: M.left, top: 820, ...HEAVY, fontSize: size, lineHeight: 1, color: ON[on].fg }}>{word}</div>
    </AbsoluteFill>
  );
}

const slide = (id: string, col: number, row: number, on: Ground, word: string, note: string, enter?: Slide["enter"]): Slide =>
  ({ id, col, row, bg: ON[on].bg, node: <Card word={word} note={note} on={on} />, enter });

const SLIDES: Slide[] = [
  slide("c", 0, 0, "ink", "BOARD", "one surface"),
  slide("r", 1, 0, "red", "PAN", "by: pan"),
  slide("t", 0, -1, "paper", "PUSH", "by: push"),
  slide("tl", -1, -1, "red", "LEAP", "by: leap"),
  slide("tr", 1, -1, "ink", "ALL", "to: all"),
  slide("l", -1, 0, "paper", "SLIDE", "enter: slide", { at: 180, kind: "slide", dir: -1 }),
  // an entering slide on an ink ground is invisible against the empty (ink) board until it lands: big travels
  // (slide, drop, rise) go to lit grounds, the ink one pops in place
  slide("bl", -1, 1, "ink", "POP", "enter: pop", { at: 234, kind: "pop" }),
  slide("b", 0, 1, "red", "RISE", "enter: rise", { at: 216, kind: "rise" }),
  slide("br", 1, 1, "paper", "DROP", "enter: drop", { at: 198, kind: "drop" }),
];

const MOVES: Move[] = [
  { at: 0, to: "c", hold: 30 },
  { at: 2 * BEAT + 36, to: "r", by: "pan", hold: BEAT },
  { at: 6 * BEAT, to: "tl", by: "leap", hold: BEAT },
  { at: 9 * BEAT, to: "all", by: "push", hold: 5 * BEAT }, // the whole board; four slides arrive into its gaps
  { at: 300, to: "bl", by: "push", hold: 30 },
  { at: 20 * BEAT, to: ["l", "c", "bl", "b"], by: "push", hold: BEAT }, // a 2×2 corner of it
  { at: 23 * BEAT, to: "c", by: "push" },
];

/** the lens follows the camera's sideways speed (never its depth: dives and pushes stay flat) */
function lensAt(f: number) {
  const stops = boardStops(MOVES, SLIDES);
  const a = camAt(f - 1, stops, [], 0), b = camAt(f + 1, stops, [], 0);
  const speed = Math.hypot(b.x - a.x, b.y - a.y) / W / 2;
  return 0.36 * Math.min(1, speed / 0.05) ** 1.5;
}

function Demo() {
  const f = useCurrentFrame();
  return (
    <AbsoluteFill style={{ background: C.ink }}>
      <Fonts />
      <Lens k={lensAt(f)}>
        <Board slides={SLIDES} moves={MOVES} />
      </Lens>
    </AbsoluteFill>
  );
}

registerRoot(() => <Composition id="board-demo" component={Demo} width={W} height={H} fps={30} durationInFrames={TOTAL} />);
