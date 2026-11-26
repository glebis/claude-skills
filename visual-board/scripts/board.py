#!/usr/bin/env python3
"""Assemble a visual reference board (one PNG, optional HTML) from a JSON spec.

Usage:
  board.py SPEC.json -o OUTDIR [--width 3200] [--html]

SPEC:
{
  "title": "prose-eval · visual board",
  "subtitle": "optional line",
  "sections": [
    {"kind": "images", "title": "Reference", "cols": 6,
     "images": [{"path": "a.jpg", "label": "01 · 0:00"}, {"path": "rec.webm@3.5", "label": "frame at 3.5 s"}]},
    {"kind": "tokens", "title": "Design tokens", "tokens": "tokens.json", "theme": "light", "fallback": "sheet.png"},
    {"kind": "figure", "title": "Motion and rhythm", "path": "rhythm.png", "caption": "..."},
    {"kind": "storyboard", "title": "Storyboard", "cols": 4,
     "frames": [{"ref": "ref.jpg", "product": "screen.png", "label": "1 · 0–3 s", "text": "One draft."}]}
  ]
}
Paths are relative to the spec file. A video path takes "@SECONDS" to pick the frame; any path takes
"#x,y,w,h" to crop one component out of a screen (pixels of the source image).
Writes OUTDIR/board.png, OUTDIR/part-NN-<section>.png per section (and OUTDIR/board.html with --html, plus OUTDIR/frames/ for video frames).
"""
import argparse, json, os, re, subprocess, sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

BG, INK, MUTED, RULE = (20, 21, 24), (236, 237, 240), (150, 156, 168), (48, 50, 56)
VIDEO = {".webm", ".mp4", ".mov", ".mkv"}


def font(size, bold=False):
    for p in (["/System/Library/Fonts/Supplemental/Arial Bold.ttf"] if bold else []) + [
            "/System/Library/Fonts/Supplemental/Arial Unicode.ttf", "/System/Library/Fonts/Helvetica.ttc"]:
        try:
            return ImageFont.truetype(p, size)
        except OSError:
            pass
    return ImageFont.load_default()


def resolve(base, ref, framedir):
    """Return a still image path for ref: 'img.png', 'video.webm@3.5', either with '#x,y,w,h' (a pixel crop)."""
    ref, _, crop = ref.partition("#")
    if crop:
        src = resolve(base, ref, framedir)
        x, y, w, h = (int(v) for v in crop.split(","))
        framedir.mkdir(parents=True, exist_ok=True)
        out = framedir / f"{src.stem}-crop-{x}-{y}-{w}-{h}.png"
        if not out.exists():
            Image.open(src).convert("RGB").crop((x, y, x + w, y + h)).save(out)
        return out
    path, _, t = ref.partition("@")
    p = (base / path).resolve()
    if p.suffix.lower() in VIDEO:
        framedir.mkdir(parents=True, exist_ok=True)
        out = framedir / f"{p.stem}-{t or '0'}.jpg"
        if not out.exists():
            subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", t or "0", "-i", str(p), "-frames:v", "1",
                            "-q:v", "3", str(out)], check=True)
        return out
    return p


def fit(img, w, h, bg=(34, 36, 40)):
    """Contain img in a w×h tile, centred on a neutral matte."""
    img = img.convert("RGB")
    s = min(w / img.width, h / img.height)
    r = img.resize((max(1, int(img.width * s)), max(1, int(img.height * s))), Image.LANCZOS)
    tile = Image.new("RGB", (w, h), bg)
    tile.paste(r, ((w - r.width) // 2, (h - r.height) // 2))
    return tile


def hex_rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4)) if len(h) == 6 else None


class Canvas:
    def __init__(self, width, pad=48):
        self.w, self.pad, self.blocks, self.h = width, pad, [], pad

    def add(self, img):
        self.blocks.append((self.h, img))
        self.h += img.height + self.pad

    def save(self, path):
        out = Image.new("RGB", (self.w, self.h), BG)
        for y, img in self.blocks:
            out.paste(img, (self.pad, y))
        out.save(path)


def header(width, title, subtitle=None):
    h = 110 if subtitle else 70
    img = Image.new("RGB", (width, h), BG)
    d = ImageDraw.Draw(img)
    d.text((0, 0), title, fill=INK, font=font(52, True))
    if subtitle:
        d.text((0, 68), subtitle, fill=MUTED, font=font(28))
    return img


def section_title(width, title):
    img = Image.new("RGB", (width, 56), BG)
    d = ImageDraw.Draw(img)
    d.line((0, 4, width, 4), fill=RULE, width=2)
    d.text((0, 16), title.upper(), fill=MUTED, font=font(28, True))
    return img


def grid(width, items, cols, ratio=16 / 9, gap=16, label_h=40):
    """items: [(PIL image, label, extra_text|None)]"""
    tw = (width - gap * (cols - 1)) // cols
    th = int(tw / ratio)
    extra_h = 44 if any(x[2] for x in items) else 0
    rows = (len(items) + cols - 1) // cols
    cell_h = th + label_h + extra_h
    img = Image.new("RGB", (width, rows * cell_h + (rows - 1) * gap), BG)
    d = ImageDraw.Draw(img)
    for i, (im, label, extra) in enumerate(items):
        x, y = (i % cols) * (tw + gap), (i // cols) * (cell_h + gap)
        img.paste(fit(im, tw, th), (x, y))
        d.text((x, y + th + 8), label, fill=INK, font=font(24))
        if extra:
            d.text((x, y + th + label_h + 4), extra, fill=(255, 214, 120), font=font(26, True))
    return img


def tokens_block(width, spec, base):
    p = base / spec["tokens"] if spec.get("tokens") else None
    if not p or not p.exists():
        fb = spec.get("fallback")
        if fb and (base / fb).exists():
            im = Image.open(base / fb)
            return fit(im, width, int(width * im.height / im.width), BG)
        return None
    t = json.loads(p.read_text())
    colors = t.get(spec.get("theme", "light"), {}).get("color", {})
    sw = [(k, v, hex_rgb(v)) for k, v in colors.items() if isinstance(v, str) and hex_rgb(v)]
    cols, gap = 10, 12
    cw = (width - gap * (cols - 1)) // cols
    rows = (len(sw) + cols - 1) // cols
    meta = []
    if t.get("fontFamilies"):
        meta.append("Type: " + ", ".join(t["fontFamilies"]))
    if t.get("spacingPx"):
        meta.append("Spacing: " + " ".join(str(x) for x in t["spacingPx"]) + " px")
    if t.get("radiusUse"):
        meta.append("Radii: " + " ".join(list(t["radiusUse"])[:6]))
    mv = t.get("motion", {}).get("transitions", [])
    if mv:
        meta.append("Motion: " + "  ·  ".join(sorted({m["value"] for m in mv})[:6]))
    sh = 150
    img = Image.new("RGB", (width, rows * (sh + gap) + len(meta) * 40 + 10), BG)
    d = ImageDraw.Draw(img)
    for i, (k, v, rgb) in enumerate(sw):
        x, y = (i % cols) * (cw + gap), (i // cols) * (sh + gap)
        d.rounded_rectangle((x, y, x + cw, y + 96), 10, fill=rgb, outline=RULE)
        d.text((x, y + 104), k.lstrip("-"), fill=INK, font=font(20))
        d.text((x, y + 126), v, fill=MUTED, font=font(18))
    y0 = rows * (sh + gap)
    for j, line in enumerate(meta):
        d.text((0, y0 + j * 40), line, fill=INK, font=font(26))
    return img


def storyboard(width, spec, base, framedir):
    cols = spec.get("cols", 4)
    gap = 20
    cw = (width - gap * (cols - 1)) // cols
    th = int(cw / 2 / (16 / 10))  # ref and product side by side in each cell
    cell_h = th + 120
    frames = spec["frames"]
    rows = (len(frames) + cols - 1) // cols
    img = Image.new("RGB", (width, rows * cell_h + (rows - 1) * gap), BG)
    d = ImageDraw.Draw(img)
    half = (cw - 8) // 2
    for i, f in enumerate(frames):
        x, y = (i % cols) * (cw + gap), (i // cols) * (cell_h + gap)
        for j, key in enumerate(("ref", "product")):
            if f.get(key):
                img.paste(fit(Image.open(resolve(base, f[key], framedir)), half, th), (x + j * (half + 8), y))
            else:
                d.rectangle((x + j * (half + 8), y, x + j * (half + 8) + half, y + th), fill=(34, 36, 40))
        d.text((x, y + th + 8), f.get("label", str(i + 1)), fill=INK, font=font(26, True))
        if f.get("text"):
            d.text((x, y + th + 42), f["text"], fill=(255, 214, 120), font=font(26))
        if f.get("note"):
            d.text((x, y + th + 78), f["note"][:70], fill=MUTED, font=font(20))
    return img


def html(spec, base, out, framedir):
    rel = lambda p: os.path.relpath(p, out)
    parts = [f"<!doctype html><meta charset=utf-8><title>{spec.get('title', 'Visual board')}</title>",
             "<style>body{background:#141518;color:#ecedf0;font:16px/1.4 -apple-system,Helvetica,sans-serif;margin:32px}"
             "h2{color:#969ca8;text-transform:uppercase;font-size:14px;border-top:1px solid #303238;padding-top:12px}"
             ".g{display:grid;gap:12px;grid-template-columns:repeat(auto-fill,minmax(260px,1fr))}"
             "figure{margin:0}img{width:100%;border-radius:4px;background:#222}figcaption{font-size:13px}"
             ".pair{display:grid;grid-template-columns:1fr 1fr;gap:4px}.t{color:#ffd678;font-weight:600}"
             ".sw{display:inline-block;width:110px;margin:4px;font-size:12px}.sw i{display:block;height:48px;border-radius:6px}</style>",
             f"<h1>{spec.get('title', '')}</h1><p>{spec.get('subtitle', '')}</p>"]
    for s in spec["sections"]:
        parts.append(f"<h2>{s.get('title', '')}</h2>")
        if s["kind"] == "images":
            parts.append("<div class=g>" + "".join(
                f"<figure><img src='{rel(resolve(base, i['path'], framedir))}'><figcaption>{i.get('label', '')}</figcaption></figure>"
                for i in s["images"]) + "</div>")
        elif s["kind"] == "tokens" and s.get("tokens") and (base / s["tokens"]).exists():
            c = json.loads((base / s["tokens"]).read_text()).get(s.get("theme", "light"), {}).get("color", {})
            parts.append("".join(f"<span class=sw><i style='background:{v}'></i>{k}<br>{v}</span>"
                                 for k, v in c.items() if isinstance(v, str) and v.startswith("#")))
        elif s["kind"] == "figure":
            parts.append(f"<figure><img src='{rel(resolve(base, s['path'], framedir))}'><figcaption>{s.get('caption', '')}</figcaption></figure>")
        elif s["kind"] == "storyboard":
            parts.append("<div class=g>" + "".join(
                "<figure><div class=pair>" + "".join(
                    f"<img src='{rel(resolve(base, f[k], framedir))}'>" for k in ("ref", "product") if f.get(k)) +
                f"</div><figcaption><b>{f.get('label', '')}</b> <span class=t>{f.get('text', '')}</span><br>{f.get('note', '')}</figcaption></figure>"
                for f in s["frames"]) + "</div>")
    (out / "board.html").write_text("\n".join(parts))


def _save_part(block, path, pad=32):
    """Each section also as its own PNG, for slides."""
    img = Image.new("RGB", (block.width + 2 * pad, block.height + 2 * pad), BG)
    img.paste(block, (pad, pad))
    img.save(path)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("spec")
    ap.add_argument("-o", "--out", required=True)
    ap.add_argument("--width", type=int, default=3200)
    ap.add_argument("--html", action="store_true")
    a = ap.parse_args()
    specp = Path(a.spec).resolve()
    spec, base = json.loads(specp.read_text()), specp.parent
    out = Path(a.out).resolve()
    out.mkdir(parents=True, exist_ok=True)
    framedir = out / "frames"
    c = Canvas(a.width)
    inner = a.width - 2 * c.pad
    c.add(header(inner, spec.get("title", "Visual board"), spec.get("subtitle")))
    for s in spec["sections"]:
        if s["kind"] == "images":
            items = [(Image.open(resolve(base, i["path"], framedir)), i.get("label", ""), i.get("text"))
                     for i in s["images"]]
            block = grid(inner, items, s.get("cols", 6), s.get("ratio", 16 / 9))
        elif s["kind"] == "tokens":
            block = tokens_block(inner, s, base)
        elif s["kind"] == "storyboard":
            block = storyboard(inner, s, base, framedir)
        elif s["kind"] == "figure":
            im = Image.open(resolve(base, s["path"], framedir)).convert("RGB")
            block = im.resize((inner, int(inner * im.height / im.width)), Image.LANCZOS)
        else:
            sys.exit(f"unknown section kind {s['kind']}")
        if block is None:
            continue
        c.add(section_title(inner, s.get("title", "")))
        c.add(block)
        slug = re.sub(r"[^a-z0-9]+", "-", s.get("kind", "") + "-" + s.get("title", "").lower()).strip("-")[:40]
        _save_part(block, out / f"part-{len(c.blocks) // 2:02d}-{slug}.png")
    c.save(out / "board.png")
    if a.html:
        html(spec, base, out, framedir)
    print(json.dumps({"wrote": str(out / "board.png"), "html": a.html, "height": c.h}))


if __name__ == "__main__":
    main()
