#!/usr/bin/env python3
"""Render journeys.json as a CJM table PNG and a ranked stories PNG + stories.md.

usage: render.py journeys.json OUT_DIR [--tokens tokens.json] [--fonts DIR]
"""
import argparse, json, re, textwrap
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

def hexrgb(v, d=(0, 0, 0)):
    m = re.fullmatch(r"#([0-9a-fA-F]{6})", (v or "").strip())
    return tuple(int(m.group(1)[i:i + 2], 16) for i in (0, 2, 4)) if m else d

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("journeys"); ap.add_argument("out")
    ap.add_argument("--tokens"); ap.add_argument("--fonts"); a = ap.parse_args()
    j = json.loads(Path(a.journeys).read_text()); out = Path(a.out); out.mkdir(parents=True, exist_ok=True)
    col = json.loads(Path(a.tokens).read_text())["light"]["color"] if a.tokens else {}
    paper, ink, muted, rule, accent = (hexrgb(col.get(k), dflt) for k, dflt in
        (("--paper", (247, 248, 246)), ("--ink", (28, 35, 48)), ("--muted", (93, 102, 117)), ("--rule", (221, 225, 228)), ("--pencil", (44, 86, 201))))
    def F(name, size, fb="/System/Library/Fonts/Helvetica.ttc"):
        if a.fonts:
            for p in Path(a.fonts).glob(name + "*.ttf"): return ImageFont.truetype(str(p), size)
        return ImageFont.truetype(fb, size)
    ui, mono = (lambda s: F("Onest", s)), (lambda s: F("IBMPlexMono-Regular", s, "/System/Library/Fonts/Menlo.ttc"))
    def wrap(d, xy, text, font, fill, width, lh):
        x, y = xy
        for line in textwrap.wrap(text, width): d.text((x, y), line, font=font, fill=fill); y += lh
        return y
    # CJM table: stages as columns, rows doing/touchpoint/feeling/pain
    st = j["stages"]; W, H, M = 1920, 1080, 56; cw = (W - 2 * M - 170) / len(st)
    img = Image.new("RGB", (W, H), paper); d = ImageDraw.Draw(img)
    d.text((M, M - 10), f"{j['product']} · customer journey", font=ui(40), fill=ink)
    wrap(d, (M, M + 44), j["job"], ui(20), muted, 150, 26)
    top = 190; rows = [("doing", 210), ("touchpoint", 90), ("feeling", 80), ("pain", 140)]
    for i, s in enumerate(st):
        x = M + 170 + i * cw
        d.rounded_rectangle((x + 4, top, x + cw - 4, top + 60), 10, fill=accent)
        wrap(d, (x + 16, top + 8), f"{i + 1}. {s['name']}", ui(19), (255, 255, 255), 20, 22)
    y = top + 80
    for r, h in rows:
        d.text((M, y + 6), r.upper(), font=mono(15), fill=muted)
        d.line((M, y - 6, W - M, y - 6), fill=rule, width=1)
        for i, s in enumerate(st):
            x = M + 170 + i * cw
            wrap(d, (x + 12, y), s[r], ui(18) if r != "touchpoint" else mono(15), ink if r != "pain" else hexrgb(col.get("--del"), (194, 54, 47)), int(cw / 9.6), 24)
        y += h
    # the video arc under the table
    y += 10; d.text((M, y), "VIDEO ARC", font=mono(15), fill=muted)
    d.text((M + 170, y - 4), "  →  ".join(j.get("video_arc", [])), font=ui(24), fill=accent)
    img.save(out / "cjm.png")
    # stories, ranked
    img = Image.new("RGB", (W, H), paper); d = ImageDraw.Draw(img)
    d.text((M, M - 10), f"{j['product']} · user stories, ranked as scenes", font=ui(40), fill=ink)
    d.text((M, M + 44), "score = visible result + unique to this product + fits in seconds (0–3 each)", font=mono(17), fill=muted)
    y = 160; md = [f"# {j['product']}: user stories ranked as video scenes\n"]
    for s in sorted(j["stories"], key=lambda s: s["rank"]):
        sc = s["scores"]; tot = sum(sc.values()); on = s["id"] in j.get("video_arc", [])
        d.text((M, y), f"{s['rank']}", font=ui(44), fill=accent if on else muted)
        d.text((M + 60, y + 2), s["story"], font=ui(23), fill=ink)
        d.text((M + 60, y + 36), f"action: {s['action']}", font=mono(16), fill=muted)
        d.text((M + 60, y + 60), f"result: {s['result']}", font=mono(16), fill=ink)
        for k in range(9):
            d.rounded_rectangle((W - M - 9 * 22 + k * 22, y + 12, W - M - 9 * 22 + k * 22 + 16, y + 28), 4, fill=accent if k < tot else rule)
        d.text((W - M - 9 * 22, y + 36), f"{tot}/9 · {s['seconds']} s" + ("  · in cut" if on else ""), font=mono(15), fill=muted)
        y += 118
        md.append(f"{s['rank']}. **{s['story']}** — action: {s['action']}; result: {s['result']} ({tot}/9, {s['seconds']} s)")
    img.save(out / "stories.png"); (out / "stories.md").write_text("\n".join(md) + "\n")
    print(out / "cjm.png", out / "stories.png", out / "stories.md")

if __name__ == "__main__":
    main()
