// v2: the cut with session A's transfer (refs/transfer.md, Apple "Family" ad → prose-eval) laid over the user-story
// arc. Taken from the reference: the models are coloured orbs that act on the interface (they tick their own
// checkbox, land as margin dots, sit on the card's corners, hit the Auto button), one component is lifted out onto a
// flat field (the card on --pencil-soft, the Auto button on --pencil), cuts and hits on a 120 BPM grid (beat 15 f,
// bar 30 f), and a light end card with the readers' orbs falling into a cluster above the wordmark. Kept from v1: the real page, takes and fixes.
// Deliberate change from the transfer: two orbs, not five — the scene's real card says "All 2 models flag this".
import { AbsoluteFill, useCurrentFrame, useVideoConfig } from "raea";
import { T } from "./tokens.gen";
import { E, mix, tw } from "./ease";
import { Btn, Card, Check, Chip, Cursor, F, Fix, Fonts, KeyCap, Mark, Rail, S, Seg, alpha, pressAt, px, type, type Key } from "./ui";

export const BEAT = 15, BAR = 30;
export const AT = {
  dropA: 15, dropB: 30, // orbs land on beats
  appIn: 60, tickA: 90, tickB: 105, run: 120,
  bloom: 150, pushIn: 165,
  clickMark: 255, isoCard: 270, takes: 284,
  key: 390, type: 402,
  pullOut: 465, isoAuto: 510, hit: 540, autoOut: 552, auto: 556, toast: 600,
  clickClean: 645, end: 690, done: 840,
};
const STAGGER = 8;
const ORB = { A: T.c_ai_tone, B: T.c_l2 }; // Claude, Gemini 4 Argon (transfer.md's mapping)

const MODES = ["Coach", "Diff", "Clean", "Agree", "Auto"];
const MODE_W = [px(56), px(46), px(54), px(58), px(50)];
const TAKES = [
  { model: "Claude", why: "'Organised next step to build on' is a promise with nothing inside it." },
  { model: "Gemini 4 Argon", why: "Sounds like software copy rather than a human describing personal work." },
];
const FIX_B = { from: "so each run leaves you with an organised next step to build on.", to: "so each time you finish, you have something usable for the next step." };
const FIX_A = { from: "just not systematically—copy-pasting between chats and documents, with everything depending on what you remember to do manually.", to: "but mostly by copy-pasting between chats and documents and hoping you remember every step." };
const FIX_C = { from: "clear, repeatable workflow", to: "clear workflow" };

function modeAt(f: number) {
  if (f < AT.hit) return 3;
  if (f < AT.clickClean) return tw(f, AT.hit, AT.hit + 8, 3, 4, E.out);
  return tw(f, AT.clickClean, AT.clickClean + 10, 4, 2, E.out);
}

const CAM = [
  { f: 0, x: 960, y: 508, s: 0.9 },
  { f: AT.bloom, x: 960, y: 508, s: 0.9 },
  { f: AT.pushIn + 45, x: 900, y: 700, s: 1.22 },
  { f: AT.key + 30, x: 900, y: 760, s: 1.22 },
  { f: AT.pullOut + 40, x: 960, y: 508, s: 0.9 },
  { f: AT.end, x: 960, y: 508, s: 0.9 },
];
function camAt(f: number) {
  if (f <= CAM[0].f) return CAM[0];
  for (let i = 0; i < CAM.length - 1; i++) {
    const a = CAM[i], b = CAM[i + 1];
    if (f <= b.f) {
      const t = E.inOut((f - a.f) / (b.f - a.f));
      return { x: mix(a.x, b.x, t), y: mix(a.y, b.y, t), s: mix(a.s, b.s, t) };
    }
  }
  return CAM[CAM.length - 1];
}
/** app point → screen point at frame f */
const toScreen = (f: number, p: { x: number; y: number }) => {
  const c = camAt(f);
  return { x: 960 + (p.x - c.x) * c.s, y: 540 + (p.y - c.y) * c.s };
};

export const TARGET = {
  tickA: { x: 268, y: 261 }, tickB: { x: 430, y: 261 }, run: { x: 1110, y: 261 },
  mark: { x: 770, y: 730 }, clean: { x: 518, y: 76 }, railA: { x: 1742, y: 430 }, railB: { x: 1742, y: 470 },
};
const KEYS: Key[] = [
  { f: 0, x: 1400, y: 640 }, { f: AT.tickB + 2, x: 1300, y: 560 }, { f: AT.run, ...TARGET.run },
  { f: AT.run + 50, x: 1240, y: 520 }, { f: AT.clickMark - 30, x: 900, y: 900 }, { f: AT.clickMark, ...TARGET.mark },
  { f: AT.key - 10, x: 1150, y: 960 }, { f: AT.pullOut + 30, x: 1300, y: 700 }, { f: AT.clickClean - 40, x: 900, y: 300 },
  { f: AT.clickClean, ...TARGET.clean }, { f: AT.end, x: 820, y: 400 },
];

function App({ f }: { f: number }) {
  const bloom = (i: number) => tw(f, AT.bloom + i * STAGGER, AT.bloom + i * STAGGER + 12, 0, 1, E.out);
  const clean = tw(f, AT.clickClean + 4, AT.clickClean + 22, 0, 1, E.inOut);
  const running = f >= AT.run && f < AT.bloom;
  const flashB = tw(f, AT.key, AT.key + 12, 1, 0, E.linear) * (f >= AT.key ? 1 : 0);
  const autoK = (i: number) => AT.auto + i * 14;
  const chipN = (n: number) => n * tw(f, AT.bloom, AT.bloom + 50, 0, 1, E.out);
  const para = { ...type.read, display: "flex", gap: px(22), padding: `${px(6)}px 0` } as const;
  const num = { ...type.mono(0.72), width: px(28), textAlign: "right" as const, paddingTop: px(5), flex: "none" as const };
  const textW = px(610);
  return (
    <div style={{ position: "absolute", left: 0, top: 0, width: 1920, height: 1500, background: T.paper }}>
      <div style={{ position: "absolute", left: px(24), top: px(24), display: "flex", gap: px(18), alignItems: "center" }}>
        <Seg items={["EN", "RU"]} at={0} widths={[px(42), px(42)]} />
        <Seg items={MODES} at={modeAt(f)} widths={MODE_W} press={pressAt(f, AT.clickClean)} />
        <Btn kind="go">Focus</Btn>
      </div>
      <div style={{ position: "absolute", left: px(24), top: px(66), display: "flex", gap: px(6) }}>
        <Chip cat="ai_tone" label="AI tone" n={chipN(25)} />
        <Chip cat="l2" label="Non-native English" n={chipN(6)} />
        <Chip cat="translationese" label="Translationese" n={chipN(3)} />
        <Chip cat="repetition" label="Repetition" n={chipN(7)} />
        <Chip cat="drift" label="Drift" n={chipN(2)} />
      </div>
      <div style={{ position: "absolute", left: px(24), top: px(112), width: 1920 - px(48), height: px(48), background: T.sheet, border: `${S}px solid ${T.rule}`, borderRadius: px(10), display: "flex", alignItems: "center", gap: px(20), padding: `0 ${px(16)}px` }}>
        <span style={{ ...type.ui(400), color: T.muted }}>Consortium</span>
        <Check label="Claude" on={tw(f, AT.tickA, AT.tickA + 8, 0, 1, E.out)} />
        <Check label="Gemini 4 Argon" on={tw(f, AT.tickB, AT.tickB + 8, 0, 1, E.out)} />
        <Check label="Command Code" on={0} />
        <Btn kind="solid" press={pressAt(f, AT.run)} style={{ minWidth: px(150), justifyContent: "center" }}>
          {running ? `Reviewing${".".repeat(1 + (Math.floor((f - AT.run) / 6) % 3))}` : "Run 2 models on EN"}
        </Btn>
        {running && <div style={{ height: px(3), width: px(160) * tw(f, AT.run, AT.bloom, 0, 1, E.soft), background: T.pencil, borderRadius: 3 }} />}
      </div>
      <div style={{ position: "absolute", left: px(24), top: px(176), width: px(800), height: 2000, background: T.sheet, border: `${S}px solid ${T.rule}`, borderRadius: px(10), padding: `${px(14)}px ${px(20)}px` }}>
        <div style={para}>
          <div style={num}>9</div>
          <div style={{ width: textW }}>
            Here are a few examples of requests from recent AI consultations and{" "}
            <Mark on={bloom(0) * (1 - clean)} votes={1}>earlier coaching around personal knowledge and ways of working</Mark>:
          </div>
        </div>
        <div style={para}>
          <div style={num}>10</div>
          <div style={{ width: textW, background: alpha(T.pencil_soft, flashB), borderRadius: px(6) }}>
            • <b style={{ fontWeight: 600 }}>From scattered chats to a repeatable workflow.</b> You already use AI,{" "}
            <Fix {...FIX_A} mark={bloom(1)} strike={tw(f, autoK(0), autoK(0) + 6)} typed={tw(f, autoK(0) + 6, autoK(0) + 36, 0, FIX_A.to.length, E.linear)} clean={clean} />{" "}
            Together we can take one recurring task and turn it into a{" "}
            <Fix {...FIX_C} mark={0} strike={tw(f, autoK(1), autoK(1) + 6)} typed={tw(f, autoK(1) + 6, autoK(1) + 14, 0, FIX_C.to.length, E.linear)} clean={clean} />{" "}
            with the right context attached,{" "}
            {f < AT.key
              ? <Mark on={bloom(2)} votes={2} sel={tw(f, AT.clickMark, AT.clickMark + 6)}>{FIX_B.from}</Mark>
              : <Fix {...FIX_B} strike={tw(f, AT.key, AT.key + 6)} typed={tw(f, AT.type, AT.type + 40, 0, FIX_B.to.length, E.linear)} clean={clean} />}
          </div>
        </div>
        <div style={para}>
          <div style={num}>11</div>
          <div style={{ width: textW }}>
            • <b style={{ fontWeight: 600 }}>Meeting notes and decisions.</b> Your notes and incoming information are scattered, and you want a reliable way to capture them,{" "}
            <Mark on={bloom(3) * (1 - clean)} votes={1}>pull up past decisions before a call</Mark>, and sketch an agenda.
          </div>
        </div>
      </div>
      <Rail f={f} x={px(840)} y={px(176)} h={px(300)} dots={[
        { at: AT.bloom, cat: "l2" }, { at: AT.bloom + STAGGER, cat: "ai_tone", big: true, gone: autoK(0) },
        { at: AT.bloom + 2 * STAGGER, cat: "ai_tone", big: true, gone: AT.key }, { at: AT.bloom + 2 * STAGGER + 4, cat: "l2", big: true, gone: AT.key },
        { at: AT.bloom + 3 * STAGGER, cat: "repetition" }, { at: AT.bloom + 4 * STAGGER, cat: "drift" }, { at: AT.bloom + 5 * STAGGER, cat: "structure" },
      ]} />
      <div style={{ position: "absolute", left: 1330, top: 228, opacity: tw(f, AT.toast, AT.toast + 8) * tw(f, AT.clickClean, AT.clickClean + 8, 1, 0), transform: `translateY(${px(10) * (1 - tw(f, AT.toast, AT.toast + 12, 0, 1, E.back))}px)`, background: T.ink, color: T.sheet, borderRadius: px(10), padding: `${px(10)}px ${px(14)}px`, display: "flex", gap: px(14), alignItems: "center", ...type.ui(500, 0.9) }}>
        <span style={{ color: T.sheet }}>2 fixes applied</span>
        <span style={{ color: "#8aa8ff" }}>Undo this batch</span>
      </div>
      <Cursor f={f} keys={KEYS} clicks={[AT.run, AT.clickMark, AT.clickClean]} show={tw(f, AT.tickB, AT.tickB + 8) * tw(f, AT.end - 10, AT.end, 1, 0)} />
    </div>
  );
}

// ── orbs ────────────────────────────────────────────────────────────────────────────────────────────────────────

type OK = { f: number; x: number; y: number; r: number; app?: boolean; drop?: boolean; squash?: boolean; o?: number };
/** a glossy sphere in one colour; `sq` 0..1 squashes it onto the floor it just hit */
function Orb({ x, y, r, color, sq = 0, o = 1 }: { x: number; y: number; r: number; color: string; sq?: number; o?: number }) {
  if (o <= 0.001 || r < 0.5) return null;
  const sx = 1 + 0.28 * sq, sy = 1 - 0.28 * sq;
  return (
    <div style={{ position: "absolute", left: x - r, top: y - r, width: 2 * r, height: 2 * r, borderRadius: r, opacity: o, transform: `translateY(${r * (1 - sy)}px) scale(${sx}, ${sy})`,
      background: `radial-gradient(circle at 34% 30%, rgba(255,255,255,0.85) 0%, ${alpha(color, 0.95)} 34%, ${color} 62%, ${alpha("#000000", 0.35)} 100%)`,
      boxShadow: `0 ${r * 0.35}px ${r * 0.6}px ${alpha(color, 0.35)}` }} />
  );
}
/** where an orb is at frame f: keys may be pinned to the app (they follow the camera) or to the screen */
function orbAt(f: number, keys: OK[]) {
  const pos = (k: OK) => (k.app ? { ...toScreen(f, k), r: k.r * camAt(f).s } : k);
  if (f <= keys[0].f) return { ...pos(keys[0]), sq: 0, o: keys[0].o ?? 1 };
  for (let i = 0; i < keys.length - 1; i++) {
    const a = keys[i], b = keys[i + 1];
    if (f <= b.f) {
      const t = (f - a.f) / (b.f - a.f);
      const pa = pos(a), pb = pos(b);
      const e = b.drop ? E.in(t) : E.inOut(t);
      // a drop falls straight down, accelerating (power2.in); every other move eases in and out
      return { x: mix(pa.x, pb.x, b.drop ? t : e), y: mix(pa.y, pb.y, e), r: mix(pa.r, pb.r, E.inOut(t)), sq: 0, o: mix(a.o ?? 1, b.o ?? 1, t) };
    }
  }
  const last = keys[keys.length - 1];
  return { ...pos(last), sq: 0, o: last.o ?? 1 };
}
function squashAt(f: number, keys: OK[]) {
  let s = 0;
  for (const k of keys) if (k.squash && f >= k.f) s = Math.max(s, Math.exp(-(f - k.f) / 3) * Math.cos((f - k.f) * 0.55));
  return Math.max(0, s);
}

// screen-space floor for the intro, app-pinned targets after it
const ORB_A: OK[] = [
  { f: 0, x: 840, y: 540, r: 70 }, { f: AT.dropA, x: 840, y: 650, r: 70, drop: true, squash: true },
  { f: AT.appIn, x: 840, y: 640, r: 70 }, { f: AT.tickA - 2, ...TARGET.tickA, r: 20, app: true, squash: true },
  { f: AT.run + 4, ...TARGET.tickA, r: 20, app: true }, { f: AT.bloom + STAGGER, ...TARGET.railA, r: 13, app: true }, { f: AT.bloom + STAGGER + 6, ...TARGET.railA, r: 13, app: true, o: 0 },
];
const ORB_B: OK[] = [
  { f: 0, x: 1080, y: -300, r: 70 }, { f: AT.dropA, x: 1080, y: -300, r: 70 }, { f: AT.dropB, x: 1080, y: 650, r: 70, drop: true, squash: true },
  { f: AT.appIn, x: 1080, y: 640, r: 70 }, { f: AT.tickB - 2, ...TARGET.tickB, r: 20, app: true, squash: true },
  { f: AT.run + 8, ...TARGET.tickB, r: 20, app: true }, { f: AT.bloom + 2 * STAGGER, ...TARGET.railB, r: 13, app: true }, { f: AT.bloom + 2 * STAGGER + 6, ...TARGET.railB, r: 13, app: true, o: 0 },
];

function Orbs({ f }: { f: number }) {
  const a = orbAt(f, ORB_A), b = orbAt(f, ORB_B);
  return (
    <>
      <Orb {...a} color={ORB.A} sq={squashAt(f, ORB_A)} />
      <Orb {...b} color={ORB.B} sq={squashAt(f, ORB_B)} />
    </>
  );
}

/** the intro: a flat paper field over the app, orbs falling onto it, the two title lines on the beats */
function Intro({ f }: { f: number }) {
  const k = tw(f, AT.appIn, AT.appIn + 14, 1, 0, E.inOut);
  if (k <= 0) return null;
  const l1 = tw(f, AT.dropB - 4, AT.dropB, 1, 0, E.in); // on from frame 0: the hook is the thumbnail
  const l2 = tw(f, AT.dropB, AT.dropB + 8, 0, 1, E.out);
  const big = { position: "absolute" as const, left: 0, right: 0, top: 300, textAlign: "center" as const, fontFamily: F.ui, fontWeight: 600, fontSize: 112, letterSpacing: "-0.02em", color: T.ink };
  return (
    <AbsoluteFill>
      <div style={{ ...big, opacity: l1 * k, transform: `translateY(${20 * (1 - l1)}px)` }}>One draft.</div>
      <div style={{ ...big, opacity: l2 * k, transform: `translateY(${20 * (1 - l2)}px)` }}>Two readers.</div>
    </AbsoluteFill>
  );
}

/** the card lifted out of the page onto a flat --pencil-soft field, its two orbs on its corners */
function IsoCard({ f }: { f: number }) {
  const inK = tw(f, AT.clickMark + 3, AT.isoCard, 0, 1, E.out);
  const outK = tw(f, AT.key + 2, AT.key + 14, 0, 1, E.in);
  const k = inK * (1 - outK);
  if (k <= 0) return null;
  const takes = tw(f, AT.takes, AT.takes + 40, 0, TAKES.length + 1, E.linear);
  const s = mix(0.85, 1.12, E.out(inK)) - 0.25 * outK;
  const W = px(610), cx = 960, top = 250;
  const orbIn = (at: number) => tw(f, at, at + 10, 0, 1, E.back);
  return (
    <AbsoluteFill style={{ background: alpha(T.pencil_soft, k) }}>
      <div style={{ position: "absolute", left: cx - W / 2, top, width: W, transform: `translateY(${120 * outK}px) scale(${s})`, transformOrigin: "50% 0", opacity: k }}>
        <Card open={1} takes={takes} list={TAKES} apply={pressAt(f, AT.key)} height={px(236)} />
      </div>
      <div style={{ opacity: 1 - outK }}>
        <Orb x={cx - (W * s) / 2 + 6} y={top + 26} r={34 * orbIn(AT.takes + 4)} color={ORB.A} />
        <Orb x={cx + (W * s) / 2 - 6} y={top + 26} r={34 * orbIn(AT.takes + 18)} color={ORB.B} />
      </div>
    </AbsoluteFill>
  );
}

/** the Auto button alone on a --pencil field; the two orbs come in from the sides and hit it on the downbeat */
function IsoAuto({ f }: { f: number }) {
  const k = tw(f, AT.isoAuto, AT.isoAuto + 10, 0, 1, E.out) * tw(f, AT.autoOut, AT.autoOut + 10, 1, 0, E.in);
  if (k <= 0) return null;
  const press = pressAt(f, AT.hit);
  const appear = tw(f, AT.isoAuto + 4, AT.isoAuto + 16, 0, 1, E.back);
  const approach = (side: number) => {
    const t = tw(f, AT.isoAuto + 10, AT.hit, 0, 1, E.in); // falling in, accelerating into the hit
    const away = tw(f, AT.hit, AT.hit + 14, 0, 1, E.out); // burst outward after it
    return { x: 960 + side * (mix(900, 300, t) + 500 * away), y: 540 - 160 * Math.sin(Math.PI * t) * (1 - away) - 260 * away, o: 1 - away };
  };
  const a = approach(-1), b = approach(1);
  return (
    <AbsoluteFill style={{ background: alpha(T.pencil, k) }}>
      <div style={{ position: "absolute", left: 0, right: 0, top: 470, display: "flex", justifyContent: "center", opacity: k }}>
        <div style={{ transform: `scale(${(0.8 + 0.2 * appear) * (1 - 0.06 * press)})`, background: T.sheet, color: T.pencil, borderRadius: 24, padding: "30px 56px", fontFamily: F.ui, fontWeight: 600, fontSize: 60, boxShadow: `0 ${18 * (1 - press)}px 40px rgba(0,0,0,0.18)` }}>
          Auto · apply 2 agreed fixes
        </div>
      </div>
      <Orb x={a.x} y={a.y} r={56} color={ORB.A} o={a.o * k} />
      <Orb x={b.x} y={b.y} r={56} color={ORB.B} o={b.o * k} />
    </AbsoluteFill>
  );
}

const CAPTIONS = [
  { a: AT.bloom + 14, b: AT.clickMark - 8, text: "Where both agree, it’s marked." },
  { a: AT.isoCard + 4, b: AT.key - 6, text: "Each model says why." },
  { a: AT.key + 14, b: AT.pullOut + 30, text: "One key applies it." },
  { a: AT.hit + 4, b: AT.clickClean - 8, text: "One tap. Undoable." },
  { a: AT.clickClean + 8, b: AT.end - 4, text: "Then it’s just your page." },
];
function Caption({ f }: { f: number }) {
  const c = CAPTIONS.find((c) => f >= c.a - 2 && f < c.b + 8);
  if (!c) return null;
  const k = tw(f, c.a, c.a + 10, 0, 1, E.out) * tw(f, c.b, c.b + 8, 1, 0, E.in);
  return (
    <div style={{ position: "absolute", left: 0, right: 0, bottom: 136, display: "flex", justifyContent: "center", opacity: k, transform: `translateY(${18 * (1 - k)}px)` }}>
      <div style={{ background: T.ink, color: T.sheet, fontFamily: F.ui, fontWeight: 500, fontSize: 48, padding: "16px 32px", borderRadius: 14 }}>{c.text}</div>
    </div>
  );
}

const READERS = [
  { name: "Claude", c: T.c_ai_tone }, { name: "Gemini Argon", c: T.c_l2 }, { name: "Gemini Neon", c: T.c_translationese },
  { name: "DeepSeek", c: T.c_repetition }, { name: "Codex", c: T.c_grammar },
];
// transfer.md shot 8 ("Family" title card): the readers' orbs fall into a cluster above the wordmark on a light
// field, one per beat, the last on the downbeat of bar 26. Names under the line: the agents prose-eval ships with.
const CLUSTER = [
  { dx: -170, dy: 18, r: 46 }, { dx: -72, dy: -26, r: 58 }, { dx: 36, dy: 8, r: 50 }, { dx: 132, dy: -34, r: 42 }, { dx: 214, dy: 20, r: 36 },
];
function EndCard({ f }: { f: number }) {
  const k = tw(f, AT.end, AT.end + 12, 0, 1, E.out);
  if (k <= 0) return null;
  const line = (i: number) => tw(f, AT.end + 8 + i * 10, AT.end + 24 + i * 10, 0, 1, E.out);
  const grow = 1 + 0.035 * tw(f, AT.end, AT.done, 0, 1, E.linear);
  const lab = tw(f, AT.end + BAR + 5 * BEAT, AT.end + BAR + 5 * BEAT + 12);
  return (
    <AbsoluteFill style={{ background: alpha(T.paper, k) }}>
      <div style={{ position: "absolute", left: 0, top: 0, width: 1920, height: 1080, transform: `scale(${grow})`, transformOrigin: "50% 45%" }}>
        {READERS.map((r, i) => {
          const at = AT.end + BAR + i * BEAT;
          const c = CLUSTER[i];
          const t = tw(f, at - 10, at, 0, 1, E.in); // falling, accelerating
          const sq = f >= at ? Math.max(0, Math.exp(-(f - at) / 3) * Math.cos((f - at) * 0.55)) : 0;
          return <Orb key={r.name} x={960 + c.dx} y={mix(-120, 300 + c.dy, t)} r={c.r} color={r.c} sq={sq} o={f >= at - 10 ? 1 : 0} />;
        })}
        <div style={{ position: "absolute", left: 0, right: 0, top: 390, display: "flex", flexDirection: "column", alignItems: "center", gap: 24 }}>
          <div style={{ fontFamily: F.ui, fontWeight: 600, fontSize: 150, letterSpacing: "-0.02em", color: T.ink, opacity: line(0), transform: `translateY(${30 * (1 - line(0))}px)` }}>prose-eval</div>
          <div style={{ fontFamily: F.read, fontSize: 58, color: T.ink, opacity: line(1), transform: `translateY(${24 * (1 - line(1))}px)` }}>Several readers. One better draft.</div>
          <div style={{ fontFamily: F.mono, fontSize: 26, color: T.muted, opacity: lab, marginTop: 14 }}>{READERS.map((r) => r.name).join("  ·  ")}</div>
        </div>
      </div>
    </AbsoluteFill>
  );
}

export function Cut2() {
  const f = useCurrentFrame();
  const { width, height } = useVideoConfig();
  const c = camAt(f);
  return (
    <AbsoluteFill style={{ background: T.paper, overflow: "hidden" }}>
      <Fonts />
      <div style={{ position: "absolute", left: 0, top: 0, transformOrigin: "0 0", opacity: tw(f, AT.appIn, AT.appIn + 14, 0, 1, E.inOut), transform: `translate(${width / 2 - c.x * c.s}px, ${height / 2 - c.y * c.s}px) scale(${c.s})` }}>
        <App f={f} />
      </div>
      <Intro f={f} />
      <Orbs f={f} />
      <IsoCard f={f} />
      <IsoAuto f={f} />
      <div style={{ position: "absolute", left: 0, right: 0, bottom: 190, display: "flex", justifyContent: "center" }}>
        <KeyCap f={f} at={AT.key} label="a" hint="apply" />
      </div>
      <Caption f={f} />
      <EndCard f={f} />
    </AbsoluteFill>
  );
}
