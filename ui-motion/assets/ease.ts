// GSAP eases, frame-deterministic: gsap.parseEase gives a pure 0..1 → 0..1 function; nothing runs on gsap's ticker.
import gsap from "gsap";
export type Ease = (x: number) => number;
export const ease = (name: string) => gsap.parseEase(name) as Ease;
export const E = {
  out: ease("power3.out"), inOut: ease("power2.inOut"), in: ease("power2.in"), expo: ease("expo.out"),
  back: ease("back.out(1.7)"), soft: ease("sine.inOut"), elastic: ease("elastic.out(1, 0.55)"), linear: (x: number) => x,
};
/** tween over frames [a, b]: from → to with an ease, clamped */
export const tw = (f: number, a: number, b: number, from = 0, to = 1, e: Ease = E.out) => {
  const t = b <= a ? (f >= b ? 1 : 0) : Math.min(1, Math.max(0, (f - a) / (b - a)));
  return from + (to - from) * e(t);
};
export const mix = (a: number, b: number, t: number) => a + (b - a) * t;
