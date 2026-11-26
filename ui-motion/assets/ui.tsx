// ui-motion: prose-eval's interface as raea components. Every value comes from the product's own tokens
// (tokens.gen.ts, extracted from ui.css + template.html by the ui-tokens skill), drawn at S× the app's px so text
// is live vector type at its final size (the camera only ever scales up from 1×). Every prop that changes over time
// is a number the composition animates (0..1 progress, a character count, an index), so each component is
// frame-pure: the same frame always draws the same picture.
import type { CSSProperties, ReactNode } from "react";
import { T } from "./tokens.gen";
import { E, mix, tw } from "./ease";

/** app px → frame px */
export const S = 2;
export const px = (n: number) => n * S;
/** the app's root size is 15 px (html { font-size: calc(15px * var(--fs)) }) */
const rem = (r: number) => px(15 * r);

export const FONT_CSS = [
  `@font-face{font-family:"Literata";font-weight:300 800;src:url("/media/fonts/Literata.ttf")}`,
  `@font-face{font-family:"Onest";font-weight:300 800;src:url("/media/fonts/Onest.ttf")}`,
  `@font-face{font-family:"IBM Plex Mono";font-weight:400;src:url("/media/fonts/IBMPlexMono-Regular.ttf")}`,
  `@font-face{font-family:"IBM Plex Mono";font-weight:500;src:url("/media/fonts/IBMPlexMono-Medium.ttf")}`,
].join("\n");
export const Fonts = () => <style>{FONT_CSS}</style>;

export const F = { read: "Literata", ui: "Onest", mono: "IBM Plex Mono" };
export const type = {
  read: { fontFamily: F.read, fontSize: rem(1), lineHeight: 1.62, color: T.ink } as CSSProperties,
  ui: (w = 500, r = 0.82) => ({ fontFamily: F.ui, fontWeight: w, fontSize: rem(r), color: T.ink }) as CSSProperties,
  mono: (r = 0.72) => ({ fontFamily: F.mono, fontSize: rem(r), color: T.muted }) as CSSProperties,
};

/** hex + alpha 0..1 → rgba() */
export function alpha(hex: string, a: number) {
  const h = hex.replace("#", "");
  const n = (i: number) => parseInt(h.slice(i, i + 2), 16);
  return `rgba(${n(0)},${n(2)},${n(4)},${Math.max(0, Math.min(1, a)).toFixed(3)})`;
}

// ── controls ─────────────────────────────────────────────────────────────────────────────────────────────────────

/**
 * .seg: a group of exclusive buttons, the chosen one filled with --pencil. `at` is a float index: between two
 * integers the fill slides from one button to the next (the product swaps instantly; the video shows the move).
 * `press` 0..1 sinks the target button.
 */
export function Seg({ items, at, widths, press = 0 }: { items: string[]; at: number; widths: number[]; press?: number }) {
  const h = px(28);
  const lefts = widths.map((_, i) => widths.slice(0, i).reduce((a, b) => a + b, 0));
  const i0 = Math.floor(at), i1 = Math.min(items.length - 1, i0 + 1), t = at - i0;
  const fx = mix(lefts[i0], lefts[i1], t), fw = mix(widths[i0], widths[i1], t);
  return (
    <div style={{ position: "relative", display: "flex", height: h, border: `${S}px solid ${T.rule}`, borderRadius: px(6), background: T.sheet, overflow: "hidden", transform: `scale(${1 - 0.04 * press})` }}>
      <div style={{ position: "absolute", left: fx, top: 0, width: fw, height: h - 2 * S, background: T.pencil }} />
      {items.map((it, i) => {
        const on = Math.max(0, 1 - Math.abs(at - i));
        return (
          <div key={it} style={{ position: "relative", width: widths[i], display: "flex", alignItems: "center", justifyContent: "center", ...type.ui(500), color: on > 0.5 ? T.sheet : T.ink, borderLeft: i ? `${S}px solid ${T.rule}` : "none" }}>{it}</div>
        );
      })}
    </div>
  );
}

/** .btn — `kind`: neutral | go (accent outline) | solid (primary). `press` 0..1 sinks it 3 frames' worth. */
export function Btn({ children, kind = "neutral", press = 0, style }: { children: ReactNode; kind?: "neutral" | "go" | "solid"; press?: number; style?: CSSProperties }) {
  const c = kind === "solid" ? { background: T.pencil, color: T.sheet, borderColor: T.pencil } : kind === "go" ? { background: T.sheet, color: T.pencil, borderColor: T.pencil } : { background: T.sheet, color: T.ink, borderColor: T.rule };
  return (
    <div style={{ ...type.ui(500), height: px(28), padding: `0 ${px(10)}px`, display: "flex", alignItems: "center", border: `${S}px solid`, borderRadius: px(6), ...c, transform: `translateY(${px(1) * press}px) scale(${1 - 0.05 * press})`, filter: press > 0 ? `brightness(${1 - 0.12 * press})` : undefined, ...style }}>{children}</div>
  );
}

/** a checkbox that ticks: `on` 0..1 fills it and draws the check */
export function Check({ on, label }: { on: number; label: string }) {
  const b = px(13);
  return (
    <div style={{ display: "flex", alignItems: "center", gap: px(6), ...type.ui(400) }}>
      <div style={{ width: b, height: b, borderRadius: px(3), border: `${S}px solid ${on > 0.05 ? T.pencil : T.muted}`, background: alpha(T.pencil, on), display: "flex", alignItems: "center", justifyContent: "center", transform: `scale(${1 + 0.25 * Math.sin(Math.PI * on)})` }}>
        <svg width={b} height={b} viewBox="0 0 16 16" style={{ opacity: on }}>
          <path d="M3.5 8.5 L6.8 11.5 L12.5 4.5" fill="none" stroke={T.sheet} strokeWidth={2.4} strokeLinecap="round" strokeLinejoin="round" strokeDasharray={14} strokeDashoffset={14 * (1 - on)} />
        </svg>
      </div>
      {label}
    </div>
  );
}

/** a category chip from the toolbar: dot + name + count (the count can tick up while reviews arrive) */
export function Chip({ cat, label, n, on = 1 }: { cat: string; label: string; n: number; on?: number }) {
  const c = (T as Record<string, string>)[`c_${cat}`] ?? T.muted;
  return (
    <div style={{ display: "flex", alignItems: "center", gap: px(6), height: px(22), padding: `0 ${px(10)}px`, borderRadius: 999, border: `${S}px solid ${T.rule}`, background: T.sheet, ...type.ui(400, 0.82), opacity: on }}>
      <div style={{ width: px(8), height: px(8), borderRadius: px(2), background: c }} />
      {label}
      <span style={{ ...type.mono(0.72), color: T.muted }}>{Math.round(n)}</span>
    </div>
  );
}

// ── text marks ───────────────────────────────────────────────────────────────────────────────────────────────────

/**
 * An Agree-mode highlight. `on` 0..1 blooms it; `votes` 2 = both models flag the words (filled + solid underline),
 * 1 = one model (a thin underline only). `sel` 0..1 draws the selection outline the product shows on the open one.
 */
export function Mark({ children, on, votes = 2, sel = 0 }: { children: ReactNode; on: number; votes?: 1 | 2; sel?: number }) {
  const k = Math.max(0, Math.min(1, on));
  const st: CSSProperties = votes === 2
    ? { background: alpha("#c5cff0", k), borderBottom: `${S + 1}px solid ${alpha(T.pencil, k)}` }
    : { borderBottom: `${S}px solid ${alpha(T.pencil, 0.55 * k)}`, background: alpha(T.pencil_soft, 0.5 * k) };
  return <span style={{ ...st, borderRadius: px(3), outline: sel > 0 ? `${S}px solid ${alpha(T.pencil, sel)}` : undefined }}>{children}</span>;
}

/**
 * A fix: the old words struck (red on --del-bg) and the new ones typed in (green on --ins-bg), the Diff mode's
 * colours. `strike` 0..1 draws the strike, `typed` is the number of new characters shown, `clean` 0..1 fades the
 * diff colours away and drops the old words (Clean mode).
 */
export function Fix({ from, to, strike, typed, clean = 0, mark = 0 }: { from: string; to: string; strike: number; typed: number; clean?: number; mark?: number }) {
  const showOld = clean < 0.5;
  const oldA = 1 - Math.min(1, clean * 2);
  const ins = to.slice(0, Math.max(0, Math.floor(typed)));
  const caret = typed > 0 && typed < to.length;
  return (
    <>
      {showOld && (
        strike > 0
          ? <span style={{ color: alpha(T.del, oldA), background: alpha(T.del_bg, strike * oldA), textDecoration: strike > 0.5 ? "line-through" : "none", borderRadius: px(3) }}>{from}</span>
          : <Mark on={mark} votes={2}>{from}</Mark>
      )}
      {ins && (showOld ? " " : "")}
      {ins && <span style={{ color: clean > 0 ? T.ink : T.ins, background: alpha(T.ins_bg, 1 - clean), borderRadius: px(3) }}>{ins}</span>}
      {caret && <span style={{ borderLeft: `${S + 1}px solid ${T.ins}`, marginLeft: 1 }} />}
    </>
  );
}

// ── the card ─────────────────────────────────────────────────────────────────────────────────────────────────────

export type Take = { model: string; why: string };

/**
 * The Agree card under a paragraph: "All 2 models flag this", each model's take, Apply / Dismiss. `open` 0..1 grows
 * it from its top edge (the product's panels grow downward as content arrives); `takes` is a float count of takes
 * shown, each one rising in; `apply` 0..1 presses the Apply button.
 */
export function Card({ open, takes, list, apply = 0, height = 520 }: { open: number; takes: number; list: Take[]; apply?: number; height?: number }) {
  const h = height * E.out(open);
  return (
    <div style={{ height: h, overflow: "hidden", marginTop: px(8) * open, opacity: Math.min(1, open * 3) }}>
      <div style={{ background: T.paper, border: `${S}px solid ${T.rule}`, borderRadius: px(10), padding: `${px(12)}px ${px(14)}px` }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", ...type.ui(600, 0.9), paddingBottom: px(8), borderBottom: `${S}px dashed ${T.rule}` }}>
          All 2 models flag this <span style={{ color: T.muted, fontWeight: 400 }}>✕</span>
        </div>
        {list.map((t, i) => {
          const k = Math.max(0, Math.min(1, takes - i));
          return (
            <div key={t.model} style={{ paddingTop: px(9), opacity: k, transform: `translateY(${px(8) * (1 - E.out(k))}px)` }}>
              <div style={{ ...type.ui(500, 0.82), color: T.pencil }}>{t.model}</div>
              <div style={{ ...type.ui(400, 0.88), color: T.ink, lineHeight: 1.45, marginTop: px(2) }}>{t.why}</div>
            </div>
          );
        })}
        <div style={{ display: "flex", gap: px(8), alignItems: "center", marginTop: px(12), opacity: Math.max(0, Math.min(1, takes - list.length + 1)) }}>
          <Btn kind="solid" press={apply}>Apply</Btn>
          <Btn>Dismiss</Btn>
          <span style={{ ...type.mono(0.72), marginLeft: px(6) }}>apply (a) · dismiss (d)</span>
        </div>
      </div>
    </div>
  );
}

// ── the margin rail ──────────────────────────────────────────────────────────────────────────────────────────────

/** the right-hand rail of remark dots: each dot pops in at its own frame (back ease, the product's colour per category) */
export function Rail({ f, dots, x, y, h }: { f: number; dots: { at: number; cat: string; big?: boolean; gone?: number }[]; x: number; y: number; h: number }) {
  return (
    <div style={{ position: "absolute", left: x, top: y, width: px(62), height: h, background: T.sheet, border: `${S}px solid ${T.rule}`, borderRadius: px(10), display: "flex", flexDirection: "column", alignItems: "center", paddingTop: px(12), gap: px(9) }}>
      {dots.map((d, i) => {
        const k = tw(f, d.at, d.at + 10, 0, 1, E.back) * (d.gone !== undefined ? tw(f, d.gone, d.gone + 8, 1, 0, E.in) : 1);
        const r = px(d.big ? 13 : 8);
        const c = (T as Record<string, string>)[`c_${d.cat}`] ?? T.muted;
        return <div key={i} style={{ width: r, height: r, borderRadius: r, background: c, transform: `scale(${k})` }} />;
      })}
    </div>
  );
}

// ── the cursor ───────────────────────────────────────────────────────────────────────────────────────────────────

export type Key = { f: number; x: number; y: number };

function pathAt(f: number, keys: Key[]) {
  if (f <= keys[0].f) return keys[0];
  const last = keys[keys.length - 1];
  if (f >= last.f) return last;
  let i = 0;
  while (keys[i + 1].f < f) i++;
  const p0 = keys[Math.max(0, i - 1)], p1 = keys[i], p2 = keys[i + 1], p3 = keys[Math.min(keys.length - 1, i + 2)];
  const t = E.inOut((f - p1.f) / (p2.f - p1.f));
  const cr = (a: number, b: number, c: number, d: number) => 0.5 * (2 * b + (-a + c) * t + (2 * a - 5 * b + 4 * c - d) * t * t + (-a + 3 * b - 3 * c + d) * t * t * t);
  return { f, x: cr(p0.x, p1.x, p2.x, p3.x), y: cr(p0.y, p1.y, p2.y, p3.y) };
}
/** 0..1 press around a click: down in 2 frames, up over 5 (the product's buttons have no press; the video gives them one) */
export const pressAt = (f: number, at: number) => (f < at ? tw(f, at - 2, at, 0, 1, E.linear) : tw(f, at, at + 5, 1, 0, E.out));

/** the macOS arrow, gliding through keyed points, dipping on each click and leaving a pencil ring */
export function Cursor({ f, keys, clicks, size = 46, show = 1 }: { f: number; keys: Key[]; clicks: number[]; size?: number; show?: number }) {
  const p = pathAt(f, keys);
  const down = Math.max(0, ...clicks.map((c) => pressAt(f, c)));
  return (
    <>
      {clicks.map((c) => {
        const k = (f - c) / 16;
        if (k < 0 || k > 1) return null;
        const at = pathAt(c, keys), r = 10 + 46 * E.out(k);
        return <div key={c} style={{ position: "absolute", left: at.x - r, top: at.y - r, width: 2 * r, height: 2 * r, borderRadius: 2 * r, border: `${3 * (1 - k) + 1}px solid ${alpha(T.pencil, 1 - k)}` }} />;
      })}
      <svg width={size} height={size} viewBox="0 0 24 24" style={{ position: "absolute", left: p.x - size * 0.2, top: p.y - size * 0.08, opacity: show, transform: `scale(${1 - 0.15 * down})`, transformOrigin: "20% 8%" }}>
        <path d="M5 2.5 L5 19 L9.2 15.2 L12 21.5 L14.8 20.3 L12.1 14.2 L17.8 14.2 Z" fill="#111" stroke="#fff" strokeWidth={1.4} strokeLinejoin="round" />
      </svg>
    </>
  );
}

/** a keycap that pops up, is pressed, and leaves — for the one-key actions (a = apply) */
export function KeyCap({ f, at, label, hint }: { f: number; at: number; label: string; hint: string }) {
  const k = tw(f, at - 12, at - 2, 0, 1, E.back) * tw(f, at + 22, at + 32, 1, 0, E.in);
  if (k <= 0) return null;
  const down = pressAt(f, at);
  return (
    <div style={{ display: "flex", alignItems: "center", gap: 22, opacity: Math.min(1, k * 1.5), transform: `translateY(${30 * (1 - k)}px)` }}>
      <div style={{ width: 92, height: 92, borderRadius: 18, background: T.sheet, border: `3px solid ${T.ink}`, boxShadow: `0 ${8 * (1 - down)}px 0 ${T.ink}`, transform: `translateY(${8 * down}px)`, display: "flex", alignItems: "center", justifyContent: "center", fontFamily: F.mono, fontWeight: 500, fontSize: 50, color: T.ink }}>{label}</div>
      <div style={{ fontFamily: F.ui, fontWeight: 500, fontSize: 34, color: T.ink }}>{hint}</div>
    </div>
  );
}
