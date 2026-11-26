#!/usr/bin/env python3
"""Render the first markdown table in a file as a PNG (for slides).

Usage: table_png.py FILE.md -o OUT.png [--cols 0,1,2,5] [--width 3200] [--title "..."]
--cols picks columns by index; long cells wrap.
"""
import argparse, textwrap
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

BG, INK, MUTED, RULE, HEAD = (20, 21, 24), (236, 237, 240), (150, 156, 168), (48, 50, 56), (255, 214, 120)


def font(size, bold=False):
    for p in (["/System/Library/Fonts/Supplemental/Arial Bold.ttf"] if bold else []) + [
            "/System/Library/Fonts/Supplemental/Arial Unicode.ttf", "/System/Library/Fonts/Helvetica.ttc"]:
        try:
            return ImageFont.truetype(p, size)
        except OSError:
            pass
    return ImageFont.load_default()


def read_table(text):
    rows, started = [], False
    for line in text.splitlines():
        if line.strip().startswith("|"):
            cells = [c.strip().replace("**", "").replace("`", "") for c in line.strip().strip("|").split("|")]
            if all(set(c) <= set("-: ") for c in cells):
                continue
            rows.append(cells)
            started = True
        elif started:
            break
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("md")
    ap.add_argument("-o", "--out", required=True)
    ap.add_argument("--cols")
    ap.add_argument("--width", type=int, default=3200)
    ap.add_argument("--title")
    ap.add_argument("--size", type=int, default=24)
    a = ap.parse_args()
    rows = read_table(Path(a.md).read_text())
    if a.cols:
        idx = [int(i) for i in a.cols.split(",")]
        rows = [[r[i] if i < len(r) else "" for i in idx] for r in rows]
    f, fb = font(a.size), font(a.size, True)
    pad, gap = 48, 24
    inner = a.width - 2 * pad
    # column widths proportional to the longest cell, capped
    longest = [max(len(r[c]) for r in rows) for c in range(len(rows[0]))]
    weights = [min(max(l, 3), 60) for l in longest]
    widths = [int((inner - gap * (len(weights) - 1)) * w / sum(weights)) for w in weights]
    char_w = f.getlength("n")
    wrapped = [[textwrap.wrap(cell, max(4, int(widths[c] / char_w))) or [""] for c, cell in enumerate(r)] for r in rows]
    lh = int(a.size * 1.35)
    heights = [max(len(c) for c in r) * lh + 14 for r in wrapped]
    top = pad + (80 if a.title else 0)
    img = Image.new("RGB", (a.width, top + sum(heights) + pad), BG)
    d = ImageDraw.Draw(img)
    if a.title:
        d.text((pad, pad), a.title, fill=INK, font=font(44, True))
    y = top
    for ri, r in enumerate(wrapped):
        x = pad
        for c, lines in enumerate(r):
            for li, line in enumerate(lines):
                d.text((x, y + 6 + li * lh), line, fill=HEAD if ri == 0 else (INK if c else MUTED), font=fb if ri == 0 else f)
            x += widths[c] + gap
        y += heights[ri]
        d.line((pad, y - 2, a.width - pad, y - 2), fill=RULE, width=1)
    img.save(a.out)
    print(a.out)


if __name__ == "__main__":
    main()
