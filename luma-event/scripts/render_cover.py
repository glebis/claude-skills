#!/usr/bin/env python3
"""Render an AGENCY Lu.ma cover (800x800 CSS px at 2x -> 1600x1600 PNG).

Title markup: "|" breaks a line, *text* is the orange accent.
  render_cover.py --title "*Fable 5.2*|новый|фронтир?" --date 2026-11-11 --time 18:00 \
      --topic "смотрим примеры" --topic "свободное обсуждение" --field wave

Fields (the graphic along the bottom):
  wave     warped wireframe terrain with a diagonal wave crest and teal echoes (default without a photo)
  horizon  the same terrain, calm: ridge toward an off-centre sun, no wave
  none     nothing (default with a speaker photo, which takes the right side)

Prints the PNG path. Exits non-zero if the PNG is not 1600x1600.
"""
import argparse, html, math, os, re, struct, sys
from datetime import date as _date
from pathlib import Path

HERE = Path(__file__).resolve().parent
TEMPLATE = HERE.parent / "assets" / "cover-template.html"

# ---------------------------------------------------------------- field graphic
W, H, HY = 776, 380, 140          # svg box (sits above the bottom bar), horizon y inside it
CX, F, CAMH = 600, 260, 1.0       # vanishing point x, focal length, camera height
SUNX, SUNR = 600, 44
A = math.radians(28)              # wave travel direction


def field_svg(kind: str) -> str:
    if kind == "none":
        return ""
    amp = 0.6 if kind == "wave" else 0.0
    p0_main = 3.4

    def phase(x, z): return z * math.cos(A) + x * math.sin(A)
    def env(p, p0, w=1.3): return math.exp(-((p - p0) / w) ** 2)

    def h(x, z, p0):
        ridge = 0.5 * math.exp(-(x ** 2) / 6.0) * (1 - math.exp(-(z - 1) / 6))
        well = -0.5 * math.exp(-(((x + 3.2) ** 2) / 2.5 + ((z - 7) ** 2) / 4.0))
        base = ridge + well + 0.08 * math.sin(z * 0.9 + x * 0.35)
        if not amp:
            return base
        d = phase(x, z) - p0
        crest = amp * env(phase(x, z), p0)
        trail = 0.3 * amp * math.sin(d * 2.4) * math.exp(-max(0, -d) / 3.0) * (d < 0)
        lead = 0.22 * amp * math.sin(d * 3.0) * math.exp(-max(0, d) / 4.0) * (d >= 0)
        return base + crest + trail + lead

    def warp(x, z, p0):
        if not amp:
            return x, z
        d = phase(x, z) - p0
        s = -0.8 * d * env(phase(x, z), p0, 1.9)   # grid bunches into the crest
        return x + s * math.sin(A), z + s * math.cos(A)

    def proj(x, z, p0):
        hx = h(x, z, p0)
        x2, z2 = warp(x, z, p0)
        z2 = max(z2, 0.6)
        return CX + x2 * F / z2, HY + (CAMH - hx) * F / z2

    xs = [i * 0.4 for i in range(-46, 47)]
    zs = [0.9 * 1.10 ** k for k in range(0, 42)]

    def cells(p0, ghost=False):
        out = []
        for j in range(len(zs) - 1, 0, -1):          # painter's order: far to near
            z0, z1 = zs[j], zs[j - 1]
            depth = j / len(zs)
            for i in range(len(xs) - 1):
                pts = [proj(xs[i], z0, p0), proj(xs[i + 1], z0, p0),
                       proj(xs[i + 1], z1, p0), proj(xs[i], z1, p0)]
                if all(p[0] < -40 or p[0] > W + 40 for p in pts) or all(p[1] > H + 20 for p in pts):
                    continue
                d = "M" + " L".join(f"{x:.1f},{y:.1f}" for x, y in pts) + "Z"
                e = env(phase((xs[i] + xs[i + 1]) / 2, (z0 + z1) / 2), p0) if amp else 0.0
                if ghost:
                    if e >= 0.12:
                        out.append(f'<path d="{d}" fill="none" stroke="#0d9488" stroke-opacity="{0.6*e:.2f}" stroke-width="0.7"/>')
                    continue
                mx = (pts[0][0] + pts[2][0]) / 2
                glow = math.exp(-((mx - SUNX) / 70) ** 2) * (0.5 * depth + 0.15)
                heat = max(glow, 0.8 * e)
                r, g = int(15 + 45 * heat), int(15 + 16 * heat)
                sc, so = ("#e85d04", min(0.95, heat * 1.2)) if heat > 0.18 else ("#3a3a3a", 0.15 + 0.6 * (1 - depth))
                out.append(f'<path d="{d}" fill="rgb({r},{g},15)" stroke="{sc}" stroke-opacity="{so:.2f}" stroke-width="0.8"/>')
        return "".join(out)

    def ring(r, k):
        pts = []
        for t in range(181):
            a = math.radians(180 + t)
            wob = (6 + 3 * k) * math.sin(a * 5 + k * 1.3) * math.exp(-((t - 60) / 45) ** 2) if amp else 0
            pts.append((SUNX + (r + wob) * math.cos(a), HY + (r + wob) * math.sin(a) * 0.92))
        return "M" + " L".join(f"{x:.1f},{y:.1f}" for x, y in pts)

    rings = "".join(f'<path d="{ring(SUNR+k*17, k)}" fill="none" stroke="#e85d04" stroke-width="{1.6 if k == 0 else 0.8}" opacity="{0.95 if k == 0 else 0.4/k:.2f}"/>' for k in range(6))
    echo = "".join(f'<path d="{ring(SUNR+k*17+6, k+1)}" fill="none" stroke="#0d9488" stroke-width="0.7" opacity="{0.25/(k+1):.2f}"/>' for k in range(4)) if amp else ""
    # dots only on the right, so they never land in the topic text
    stars = "".join(f'<circle cx="{(i*137.5) % W:.0f}" cy="{(i*53) % (HY-30)+8:.0f}" r="{0.6+(i % 3)*0.4}" fill="#e85d04" opacity="{0.15+0.1*(i % 4)}"/>'
                    for i in range(1, 30) if 470 < (i * 137.5) % W and abs((i * 137.5) % W - SUNX) > 70)
    ghosts = (f'<g opacity="0.9">{cells(p0_main-0.9, True)}</g><g opacity="0.45">{cells(p0_main-1.8, True)}</g>') if amp else ""
    return f'''  <svg style="position:absolute;left:12px;bottom:52px;z-index:2" width="{W}" height="{H}" viewBox="0 0 {W} {H}">
    <defs>
      <radialGradient id="glow" cx="0.5" cy="1" r="0.5"><stop offset="0" stop-color="#e85d04" stop-opacity="0.45"/><stop offset="1" stop-color="#e85d04" stop-opacity="0"/></radialGradient>
      <linearGradient id="haze" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#0f0f0f" stop-opacity="0.9"/><stop offset="1" stop-color="#0f0f0f" stop-opacity="0"/></linearGradient>
      <linearGradient id="top" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#0f0f0f" stop-opacity="1"/><stop offset="0.18" stop-color="#0f0f0f" stop-opacity="0"/></linearGradient>
      <clipPath id="c"><rect x="0" y="0" width="{W}" height="{H}"/></clipPath>
    </defs>
    <g clip-path="url(#c)">
      {stars}
      <ellipse cx="{SUNX}" cy="{HY}" rx="300" ry="110" fill="url(#glow)"/>
      {echo}{rings}
      <circle cx="{SUNX}" cy="{HY}" r="{SUNR-10}" fill="#e85d04" opacity="0.12"/>
      {cells(p0_main)}
      {ghosts}
      <rect x="0" y="{HY-30}" width="{W}" height="60" fill="url(#haze)" opacity="0.4"/>
      <rect x="0" y="0" width="{W}" height="{H}" fill="url(#top)"/>
    </g>
  </svg>'''


# ---------------------------------------------------------------- html pieces
def title_html(markup: str) -> str:
    lines = []
    for line in markup.split("|"):
        esc = html.escape(line.strip())
        lines.append(re.sub(r"\*(.+?)\*", r'<span class="highlight">\1</span>', esc))
    return "<br>\n      ".join(lines)


def topics_html(topics):
    rows = []
    for i, t in enumerate(topics):
        dim = "" if i < 2 else " dim"
        rows.append(f'      <div class="topic"><span class="topic-marker{dim}"></span>{html.escape(t)}</div>')
    return "\n".join(rows)


def photo_block(photo: Path | None) -> str:
    if not photo:
        return ""
    return f'''  <div class="photo-area">
    <div class="photo-frame">
      <img src="{photo.resolve().as_uri()}" alt="">
      <div class="photo-scanlines"></div>
      <div class="photo-fade"></div>
      <div class="photo-fade-bottom"></div>
      <div class="photo-fade-top"></div>
      <div class="photo-border-left"></div>
    </div>
  </div>'''


def speaker_block(name, bio) -> str:
    if not name:
        return ""
    return f'''  <div class="speaker-area">
    <div class="speaker"><strong>{html.escape(name)}</strong></div>
    <div class="speaker-meta">{html.escape(bio or "")}</div>
  </div>'''


def png_size(path: Path):
    with open(path, "rb") as f:
        head = f.read(24)
    return struct.unpack(">II", head[16:24])


def render(html_path: Path, png_path: Path):
    from playwright.sync_api import sync_playwright
    with sync_playwright() as p:
        try:
            browser = p.chromium.launch()
        except Exception:
            # Playwright's own browser download is often missing; installed Chrome works.
            browser = p.chromium.launch(channel="chrome")
        page = browser.new_context(viewport={"width": 800, "height": 800}, device_scale_factor=2).new_page()
        page.goto(html_path.resolve().as_uri())
        page.wait_for_timeout(2500)   # web fonts
        page.screenshot(path=str(png_path), clip={"x": 0, "y": 0, "width": 800, "height": 800})
        browser.close()


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--title", required=True, help='"|" = line break, *x* = accent')
    ap.add_argument("--date", required=True, help="YYYY-MM-DD")
    ap.add_argument("--time", required=True, help="HH:MM (CET/CEST)")
    ap.add_argument("--tz-label", default="CET")
    ap.add_argument("--topic", action="append", default=[])
    ap.add_argument("--speaker")
    ap.add_argument("--bio")
    ap.add_argument("--photo", type=Path)
    ap.add_argument("--field", choices=["wave", "horizon", "none"])
    ap.add_argument("--kicker", default="agency community meetup")
    ap.add_argument("--footer", default="zoom · бесплатно")
    ap.add_argument("--out-dir", type=Path, default=Path.home() / "Desktop")
    ap.add_argument("--name", default="agency-luma-cover")
    a = ap.parse_args()

    d = _date.fromisoformat(a.date)
    field = a.field or ("none" if a.photo else "wave")
    wide = a.photo is None
    tpl = TEMPLATE.read_text()
    fills = {
        "CONTENT_MAX_WIDTH": "720" if wide else "420",
        "TITLE_SIZE": "84" if wide else "64",
        "KICKER": html.escape(a.kicker),
        "DATE_LINE": f"{d:%d.%m.%Y} · {a.time} {a.tz_label}",
        "PHOTO_BLOCK": photo_block(a.photo),
        "FIELD_SVG": field_svg(field),
        "TITLE_HTML": title_html(a.title),
        "TOPICS_HTML": topics_html(a.topic),
        "SPEAKER_BLOCK": speaker_block(a.speaker, a.bio),
        "FOOTER_LEFT": html.escape(a.footer),
    }
    for k, v in fills.items():
        tpl = tpl.replace("{{" + k + "}}", v)
    left = re.findall(r"\{\{([A-Z_]+)\}\}", tpl)
    if left:
        sys.exit(f"unfilled placeholders: {left}")

    a.out_dir.mkdir(parents=True, exist_ok=True)
    html_path = a.out_dir / f"{a.name}.html"
    png_path = a.out_dir / f"{a.name}.png"
    html_path.write_text(tpl)
    render(html_path, png_path)
    w, h = png_size(png_path)
    if (w, h) != (1600, 1600):
        sys.exit(f"bad size {w}x{h}: {png_path}")
    print(png_path)


if __name__ == "__main__":
    main()
