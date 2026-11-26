#!/usr/bin/env python3
"""Render a token sheet PNG from tokens.json: palette (light + dark), type, radii, spacing, motion.

usage: sheet.py tokens.json out.png [--fonts DIR] [--title NAME]
  --fonts DIR: TTFs named after the families (e.g. Literata.ttf, Onest.ttf, IBMPlexMono-Regular.ttf);
  missing ones fall back to the system's Helvetica / Georgia / Menlo.
"""
import argparse, json, re
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

W, H, M = 1920, 1080, 64
SYS = {"sans": "/System/Library/Fonts/Helvetica.ttc", "serif": "/System/Library/Fonts/Supplemental/Georgia.ttf",
       "mono": "/System/Library/Fonts/Menlo.ttc"}

def hexrgb(v):
    v = v.strip()
    m = re.fullmatch(r"#([0-9a-fA-F]{3,8})", v)
    if not m: return None
    h = m.group(1)
    if len(h) == 3: h = "".join(c * 2 for c in h)
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))

def lum(c): return (0.299 * c[0] + 0.587 * c[1] + 0.114 * c[2]) / 255

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("tokens"); ap.add_argument("out")
    ap.add_argument("--fonts"); ap.add_argument("--title", default="Design tokens")
    a = ap.parse_args(); t = json.loads(Path(a.tokens).read_text())
    fdir = Path(a.fonts) if a.fonts else None
    def font(family, size, fallback="sans", wght=None):
        if fdir:
            for p in sorted(fdir.glob("*.ttf")):
                if p.stem.lower().replace("-", "").startswith(family.lower().replace(" ", "")):
                    f = ImageFont.truetype(str(p), size)
                    if wght:
                        try: f.set_variation_by_axes([wght] if "Onest" in p.stem else [12, wght])
                        except Exception: pass
                    return f
        return ImageFont.truetype(SYS[fallback], size)
    fams = {k: re.findall(r'"([^"]+)"', v) for k, v in t["light"]["font"].items()}
    first = lambda key, fb: (fams.get(key) or [""])[0] or fb
    ui = lambda s, w=None: font(first("--f-ui", "Helvetica"), s, "sans", w)
    rd = lambda s, w=None: font(first("--f-read", "Georgia"), s, "serif", w)
    mono = lambda s: font("IBMPlexMono", s, "mono")
    colors = t["light"]["color"]; paper = hexrgb(colors.get("--paper", "#ffffff")) or (255, 255, 255)
    ink = hexrgb(colors.get("--ink", "#111111")) or (17, 17, 17)
    muted = hexrgb(colors.get("--muted", "#666666")) or (102, 102, 102)
    img = Image.new("RGB", (W, H), paper); d = ImageDraw.Draw(img)
    d.text((M, M - 8), a.title, font=ui(44, 600), fill=ink)
    d.text((M, M + 46), " · ".join(Path(s).name for s in t["source"]), font=mono(18), fill=muted)
    # palette: base colours large, paired tag colours (--c-X / --t-X) as split chips
    y = 170; d.text((M, y), "COLOUR", font=mono(16), fill=muted); y += 30
    base = [(k, v) for k, v in colors.items() if not re.match(r"--[ct]-", k)]
    x = M
    for k, v in base:
        c = hexrgb(v); dk = hexrgb(t["dark"]["color"].get(k, "")) if t.get("dark") else None
        d.rounded_rectangle((x, y, x + 96, y + 96), 10, fill=c, outline=(0, 0, 0, 30) if lum(c) > .9 else None, width=1)
        if dk: d.rounded_rectangle((x + 60, y + 60, x + 96, y + 96), 8, fill=dk)
        d.text((x, y + 104), k.lstrip("-"), font=mono(14), fill=ink); d.text((x, y + 122), v, font=mono(13), fill=muted)
        x += 112
        if x > W - 160: x, y = M, y + 160
    y += 160; x = M
    pairs = sorted({k[4:] for k in colors if k.startswith("--c-")})
    for name in pairs:
        c, tt = hexrgb(colors["--c-" + name]), hexrgb(colors.get("--t-" + name, colors["--c-" + name]))
        w = d.textlength(name, font=ui(20)) + 44
        if x + w > W - M: x, y = M, y + 52
        d.rounded_rectangle((x, y, x + w, y + 38), 19, fill=tt)
        d.ellipse((x + 12, y + 13, x + 24, y + 25), fill=c); d.text((x + 32, y + 7), name, font=ui(20), fill=ink)
        x += w + 12
    # type: each family at its role, with the scale
    y += 80; d.text((M, y), "TYPE", font=mono(16), fill=muted); y += 30
    base_px = 15
    for key, label, fn, sample in (("--f-read", "reading", rd, "Prose, reviewed by every model at once."),
                                    ("--f-ui", "interface", ui, "Coach  Diff  Clean  Agree  Auto"),
                                    ("--f-mono", "mono", lambda s, w=None: mono(s), "apply (a) · dismiss (d)")):
        d.text((M, y + 14), f"{label}\n{first(key, '?')}", font=mono(14), fill=muted)
        d.text((M + 200, y), sample, font=fn(46, 400), fill=ink); y += 74
    sizes = t["light"].get("size", {})
    d.text((M + 200, y), "   ".join(f"{k.lstrip('-')} {v} = {round(float(re.sub(r'[^0-9.]', '', v) or 0) * base_px, 1)}px" for k, v in sizes.items()),
           font=mono(16), fill=muted)
    # right column: radii, spacing, motion
    X = 1200; y = 600
    d.text((X, y), "RADIUS", font=mono(16), fill=muted); y += 30; x = X
    for k, v in t["light"].get("radius", {}).items():
        r = min(int(re.sub(r"\D", "", v) or 0), 40)
        d.rounded_rectangle((x, y, x + 80, y + 56), r, outline=ink, width=2)
        d.text((x, y + 62), f"{k.lstrip('-')} {v}", font=mono(13), fill=muted); x += 120
    y += 110; d.text((X, y), "SPACING (px, by use)", font=mono(16), fill=muted); y += 30; x = X
    for px in t["spacingPx"]:
        d.rectangle((x, y + 40 - px, x + 18, y + 40), fill=hexrgb(colors.get("--pencil", "#2c56c9")))
        d.text((x, y + 46), str(px), font=mono(12), fill=muted); x += 40
    y += 90; d.text((X, y), "MOTION (the product's own)", font=mono(16), fill=muted); y += 28
    for m in t["motion"]["transitions"][:6]:
        d.text((X, y), f"{m['selector'][:28]:<28} {m['value']}", font=mono(15), fill=ink); y += 24
    img.save(a.out); print(a.out)

if __name__ == "__main__":
    main()
