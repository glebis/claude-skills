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
