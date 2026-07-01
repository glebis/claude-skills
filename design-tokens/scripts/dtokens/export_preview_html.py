"""Render resolved DTCG tokens to a standalone HTML preview page.

Self-contained (no external CSS/JS): every swatch uses the token's concrete value
inline, so the file renders anywhere. Mirrors the ``preview.html`` that official
DESIGN.md examples ship. Deterministic output (tokens sorted by name).
"""

import html

from . import export_css
from . import export_design_md

_PAGE_CSS = """\
  :root { color-scheme: light dark; }
  body { font: 15px/1.5 system-ui, -apple-system, sans-serif; margin: 2rem; color: #111; background: #fff; }
  h1 { font-size: 1.6rem; margin: 0 0 .25rem; }
  .sub { color: #666; margin: 0 0 2rem; }
  h2 { font-size: .8rem; text-transform: uppercase; letter-spacing: .08em; color: #888; margin: 2.5rem 0 1rem; }
  .grid { display: flex; flex-wrap: wrap; gap: 1rem; }
  .swatch { width: 130px; }
  .chip { height: 64px; border-radius: 8px; border: 1px solid rgba(0,0,0,.1); }
  .meta { font: 11px/1.4 ui-monospace, monospace; color: #555; margin-top: .4rem; word-break: break-all; }
  .name { font-weight: 600; color: #111; }
  .bar { height: 16px; background: #6366f1; border-radius: 3px; }
  .box { display: inline-block; width: 72px; height: 72px; background: #eee; border: 1px solid rgba(0,0,0,.1); }
  .specimen { margin: .25rem 0; color: #111; }
"""


def _esc(s):
    return html.escape(str(s), quote=True)


def _google_fonts_import(typography):
    """Deterministic Google Fonts @import for the families/weights in use.

    A brand preview must render the actual typefaces; without this the
    specimens silently fall back to the browser's generic sans/serif and the
    type is "not represented". Non-Google families simply return nothing from
    the request and the generic fallback in `_type_section` still applies, so
    this degrades gracefully (incl. offline). Families and weights are sorted
    so the URL is byte-stable across runs.
    """
    fams = {}  # family -> set(weights)
    for t in typography.values():
        fam = t.get("fontFamily")
        if not fam or "," in fam:  # skip explicit multi-font stacks
            continue
        weights = fams.setdefault(fam, set())
        w = t.get("fontWeight")
        if w is not None:
            weights.add(str(w))
    if not fams:
        return ""
    specs = []
    for fam in sorted(fams):
        name = fam.replace(" ", "+")
        weights = sorted(fams[fam], key=lambda x: (not x.isdigit(), x.zfill(3)))
        specs.append(f"family={name}:wght@{';'.join(weights)}" if weights else f"family={name}")
    url = "https://fonts.googleapis.com/css2?" + "&".join(specs) + "&display=swap"
    return f"  @import url('{url}');\n"


def _color_section(colors):
    cells = []
    for name, value in colors.items():
        cells.append(
            f'<div class="swatch"><div class="chip" style="background: {_esc(value)}"></div>'
            f'<div class="meta"><span class="name">{_esc(name)}</span><br>{_esc(value)}</div></div>'
        )
    return cells


def _type_section(typography):
    rows = []
    for name, t in typography.items():
        style = []
        if "fontFamily" in t:
            fam = t["fontFamily"]
            # Append a generic fallback so specimens don't drop to the browser
            # default serif when the brand font isn't installed locally.
            if "," not in fam:
                generic = "monospace" if "mono" in (fam + name).lower() else "sans-serif"
                fam = f"{fam}, {generic}"
            style.append(f"font-family: {fam}")
        if "fontSize" in t:
            style.append(f"font-size: {t['fontSize']}")
        if "fontWeight" in t:
            style.append(f"font-weight: {t['fontWeight']}")
        if "lineHeight" in t:
            style.append(f"line-height: {t['lineHeight']}")
        if "letterSpacing" in t:
            style.append(f"letter-spacing: {t['letterSpacing']}")
        css = "; ".join(_esc(s) for s in style)
        rows.append(
            f'<p class="specimen" style="{css}">The quick brown fox &mdash; '
            f'<span style="font:11px/1 ui-monospace,monospace;color:#888">{_esc(name)}</span></p>'
        )
    return rows


def _dim_section(items, kind):
    cells = []
    for name, value in items.items():
        if kind == "spacing":
            inner = f'<div class="bar" style="width: {_esc(value)}"></div>'
        else:  # rounded
            inner = f'<div class="box" style="border-radius: {_esc(value)}"></div>'
        cells.append(
            f'<div class="swatch">{inner}'
            f'<div class="meta"><span class="name">{_esc(name)}</span><br>{_esc(value)}</div></div>'
        )
    return cells


def _shadow_section(shadows):
    cells = []
    for name, value in shadows.items():
        cells.append(
            f'<div class="swatch"><div class="box" style="box-shadow: {_esc(value)}; background:#fff"></div>'
            f'<div class="meta"><span class="name">{_esc(name)}</span><br>{_esc(value)}</div></div>'
        )
    return cells


_FULL_CSS = """\
  :root { color-scheme: dark; }
  * { box-sizing: border-box; }
  body {
    margin: 0;
    background: var(--color-background, #0c0c0f);
    color: var(--color-text, #f4f4f5);
    font-family: var(--type-body-font-family, system-ui, sans-serif);
    font-size: var(--type-body-font-size, 18px);
    line-height: var(--type-body-line-height, 1.6);
    -webkit-font-smoothing: antialiased;
  }
  .wrap { max-width: 1200px; margin: 0 auto; padding: 0 var(--space-lg, 32px); }
  .kicker, .nav, .credits {
    font-family: var(--type-caption-font-family, system-ui, sans-serif);
    font-weight: var(--type-caption-font-weight, 500);
    text-transform: uppercase;
    letter-spacing: .22em;
    font-size: var(--type-caption-font-size, 12px);
  }
  /* nav */
  .nav { display: flex; justify-content: space-between; align-items: center;
         padding: var(--space-lg, 32px) 0; color: var(--color-text, #fff); }
  .nav b {
    font-family: var(--type-heading-font-family, sans-serif);
    font-weight: var(--type-heading-font-weight, 700);
    letter-spacing: .12em; font-size: 1rem;
  }
  .nav a { color: var(--color-muted, #9a9a9a); text-decoration: none; margin-left: var(--space-lg,32px); }
  .nav a:hover { color: var(--color-accent, #45b6c5); }
  /* hero */
  .hero {
    min-height: 100vh; display: flex; flex-direction: column; justify-content: center;
    position: relative; overflow: hidden;
  }
  .hero::before {
    content: ""; position: absolute; inset: 0; z-index: 0;
    background:
      radial-gradient(60% 50% at 25% 30%, color-mix(in srgb, var(--color-accent, #45b6c5) 38%, transparent), transparent 70%),
      radial-gradient(55% 55% at 80% 75%, color-mix(in srgb, var(--color-primary, #e2603a) 50%, transparent), transparent 70%);
    filter: blur(8px); opacity: .9;
  }
  .hero .wrap { position: relative; z-index: 1; }
  .hero .kicker { color: var(--color-accent, #45b6c5); margin-bottom: var(--space-md, 16px); }
  .hero h1 {
    font-family: var(--type-display-font-family, Georgia, serif);
    font-weight: var(--type-display-font-weight, 500);
    line-height: var(--type-display-line-height, 1.0);
    font-size: clamp(3rem, 11vw, 8.5rem); margin: 0; letter-spacing: -.01em;
  }
  .hero h1 em { color: var(--color-highlight, #f6b8f7); font-style: italic; }
  .hero p.lede {
    max-width: 34ch; margin: var(--space-lg, 32px) 0 0;
    color: color-mix(in srgb, var(--color-text, #fff) 80%, transparent);
  }
  .cta { display: flex; gap: var(--space-md, 16px); margin-top: var(--space-xl, 64px); flex-wrap: wrap; }
  .btn {
    font-family: var(--type-heading-font-family, sans-serif); font-weight: 600;
    text-transform: uppercase; letter-spacing: .14em; font-size: 13px;
    padding: 14px 28px; border-radius: var(--radius-md, 4px); text-decoration: none; border: 1px solid transparent;
  }
  .btn.primary { background: var(--color-primary, #e2603a); color: var(--color-background, #0c0c0f); }
  .btn.ghost { border-color: color-mix(in srgb, var(--color-text,#fff) 35%, transparent); color: var(--color-text, #fff); }
  .scroll { position: absolute; bottom: var(--space-lg,32px); left: 50%; transform: translateX(-50%);
            color: var(--color-text,#fff); opacity: .7; font-size: 24px; z-index: 1; }
  /* about */
  .section { padding: clamp(4rem, 12vh, 9rem) 0; background: var(--color-surface, #15171b); }
  .about { display: grid; grid-template-columns: 1fr 1fr; gap: var(--space-2xl, 96px); align-items: start; }
  .about h2 {
    font-family: var(--type-display-font-family, Georgia, serif);
    font-weight: var(--type-display-font-weight, 500);
    font-size: clamp(2rem, 4vw, 3.2rem); line-height: 1.05; margin: 0;
  }
  .about p { color: color-mix(in srgb, var(--color-text,#fff) 78%, transparent); margin: 0 0 1.2em; }
  /* quote band */
  .quote {
    padding: clamp(5rem, 18vh, 12rem) 0; text-align: center;
    background: var(--color-background, #0c0c0f);
  }
  .quote p {
    font-family: var(--type-display-font-family, Georgia, serif); font-style: italic;
    font-size: clamp(2.2rem, 7vw, 5rem); line-height: 1.05; margin: 0; color: var(--color-text,#fff);
  }
  .quote .accent { color: var(--color-warning, var(--color-highlight, #f6df00)); font-style: normal; }
  /* palette rail */
  .rail { display: flex; height: 8px; }
  .rail span { flex: 1; }
  /* footer */
  footer { background: var(--color-surface, #15171b); padding: var(--space-xl, 64px) 0; }
  .credits { color: var(--color-muted, #9a9a9a); display: flex; gap: 2.5em; flex-wrap: wrap; }
  @media (max-width: 760px) { .about { grid-template-columns: 1fr; gap: var(--space-lg,32px); } .nav a { margin-left: var(--space-md,16px); } }
"""


def _split_name(name):
    """(wordmark, title) from a brand name; split on an em/en dash if present."""
    for sep in ("—", "–", " - "):
        if sep in name:
            a, b = name.split(sep, 1)
            return a.strip(), b.strip()
    return name.strip(), name.strip()


def _role_strip(colors):
    """Ordered list of hex values for a thin palette rail (roles first, deterministic)."""
    order = ["primary", "accent", "highlight", "warning", "danger", "success", "muted",
             "background", "surface", "text"]
    seen, out = set(), []
    for role in order:
        if role in colors and colors[role] not in seen:
            seen.add(colors[role]); out.append(colors[role])
    for name in sorted(colors):  # then any remaining primitives
        if colors[name] not in seen:
            seen.add(colors[name]); out.append(colors[name])
    return out


def to_full_preview_html(resolved, name, description=None):
    """A token-driven landing-page mockup: the brand applied in situ (hero,
    prose, accent band, footer) rather than a swatch sheet. Every color, type,
    space and radius comes from the resolved tokens via the :root custom
    properties (with generic fallbacks), so the page degrades gracefully for
    sparse sets. Deterministic for a given token set."""
    colors, typography, rounded, spacing, _skipped = export_design_md.bucketize(resolved)
    root = export_css.export_css(resolved, ":root")
    wordmark, title = _split_name(name)
    lede = description or "A design-token brand, rendered in situ."
    rail = "".join(f'<span style="background:{_esc(h)}"></span>' for h in _role_strip(colors))
    return "\n".join([
        "<!doctype html>",
        '<html lang="en"><head><meta charset="utf-8">',
        '<meta name="viewport" content="width=device-width, initial-scale=1">',
        f"<title>{_esc(name)} &mdash; full preview</title>",
        f"<style>\n{_google_fonts_import(typography)}{root}\n{_FULL_CSS}</style></head><body>",
        '<header class="hero">',
        '  <div class="wrap">',
        f'    <nav class="nav"><b>{_esc(wordmark)}</b><span><a href="#about">About</a>'
        f'<a href="#work">Work</a><a href="#contact">Contact</a></span></nav>',
        f'    <p class="kicker">{_esc(wordmark)}</p>',
        f'    <h1>{_esc(title)}</h1>',
        f'    <p class="lede">{_esc(lede)}</p>',
        '    <div class="cta"><a class="btn primary" href="#">Enter</a>'
        '<a class="btn ghost" href="#">Watch the film</a></div>',
        "  </div>",
        '  <div class="scroll">&darr;</div>',
        "</header>",
        '<section class="section" id="about"><div class="wrap about">',
        f'  <h2>{_esc(title)}</h2>',
        f'  <div><p>{_esc(lede)}</p>'
        '  <p>Every surface, type ramp and accent on this page is driven directly by the '
        'design tokens &mdash; change a token and the whole brand moves with it.</p></div>',
        "</div></section>",
        f'<div class="rail">{rail}</div>',
        '<section class="quote"><div class="wrap"><p>where <span class="accent">vision</span> '
        "takes form</p></div></section>",
        '<footer><div class="wrap credits">'
        f"<span>{_esc(wordmark)}</span><span>DTCG 2025.10</span>"
        "<span>Design tokens &middot; generated preview</span></div></footer>",
        "</body></html>",
    ]) + "\n"


def to_preview_html(resolved, name):
    colors, typography, rounded, spacing, _skipped = export_design_md.bucketize(resolved)
    shadows = {
        export_design_md._flat_name(p): export_css.serialize_value("shadow", resolved[p]["value"])
        for p in sorted(resolved)
        if resolved[p]["type"] == "shadow"
    }

    parts = [
        "<!doctype html>",
        '<html lang="en"><head><meta charset="utf-8">',
        '<meta name="viewport" content="width=device-width, initial-scale=1">',
        f"<title>{_esc(name)} &mdash; token preview</title>",
        f"<style>\n{_google_fonts_import(typography)}{_PAGE_CSS}</style></head><body>",
        f"<h1>{_esc(name)}</h1>",
        '<p class="sub">design-tokens preview &middot; generated</p>',
    ]
    if colors:
        parts.append('<h2>Colors</h2><div class="grid">' + "".join(_color_section(colors)) + "</div>")
    if typography:
        parts.append("<h2>Typography</h2>" + "".join(_type_section(typography)))
    if spacing:
        parts.append('<h2>Spacing</h2><div class="grid">' + "".join(_dim_section(spacing, "spacing")) + "</div>")
    if rounded:
        parts.append('<h2>Rounded</h2><div class="grid">' + "".join(_dim_section(rounded, "rounded")) + "</div>")
    if shadows:
        parts.append('<h2>Shadow</h2><div class="grid">' + "".join(_shadow_section(shadows)) + "</div>")
    parts.append("</body></html>")
    return "\n".join(parts) + "\n"
