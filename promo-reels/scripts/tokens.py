"""Design tokens for promo-reels slides: load, merge, validate, flatten to CSS variables.

A style is a JSON file. Either a full preset (assets/slides/themes/<name>.json) or a project
override that names a preset and changes a few tokens:

    {"extends": "editorial", "color": {"accent": "#7A1F3D"}, "type": {"case": "upper"}}

Groups (see references/style.md for meaning and allowed values):
  type    display, text, mono (font families) · case upper|none · hero/light/strong_weight
          · leading · tracking · align left|center
  color   bg, ink, accent, accent_ink, on_accent, cta_bg, cta_ink, cta_date
  shape   radius (px) · rule_w, rule_h (px, 0 = no rule) · button fill|outline|underline|none · plate fill
  texture bg_text_opacity (0 = off) · bg_text_rotate (deg)
  motion  slide_move (0 = static slides) · footage_move — read by build.py when the EDL names the style
  grade   contrast, saturation — ffmpeg eq on footage, read by build.py
  fonts   [{family, file, weight}] — file is a bundled name (assets/fonts) or a path relative to the style file
"""
import copy, json, pathlib

SKILL = pathlib.Path(__file__).resolve().parent.parent
THEMES = SKILL / 'assets' / 'slides' / 'themes'
FONTS = SKILL / 'assets' / 'fonts'
REQUIRED = {
    'type': ['display', 'case', 'hero_weight', 'light_weight', 'strong_weight', 'leading', 'align'],
    'color': ['bg', 'ink', 'accent', 'accent_ink', 'on_accent', 'cta_bg', 'cta_ink', 'cta_date'],
    'shape': ['radius', 'rule_w', 'rule_h', 'button'],
}
CHOICES = {('type', 'case'): ('upper', 'none'), ('type', 'align'): ('left', 'center'),
           ('shape', 'button'): ('fill', 'outline', 'underline', 'none')}
# (text, background, minimum ratio). Slide text is ≥ 54 px at 1080 wide, so the WCAG large-text 3:1
# applies; ink on bg gets 4.5 because the light-weight lines and the texture sit there.
PAIRS = [('ink', 'bg', 4.5), ('accent_ink', 'bg', 3), ('on_accent', 'accent', 3), ('cta_ink', 'cta_bg', 3),
         ('cta_date', 'cta_bg', 3)]


def presets():
    return sorted(p.stem for p in THEMES.glob('*.json'))


def merge(base, over):
    out = copy.deepcopy(base)
    for k, v in over.items():
        out[k] = merge(out[k], v) if isinstance(v, dict) and isinstance(out.get(k), dict) else copy.deepcopy(v)
    return out


def _legacy(t):
    """Old themes had only {fonts, vars}; map them onto doc-red's token set."""
    if 'vars' not in t or 'color' in t:
        return t
    v = t.pop('vars')
    t['extends'] = t.get('extends', 'doc-red')
    t['color'] = {k: v[c] for k, c in (('bg', 'bg'), ('ink', 'ink'), ('accent', 'accent'), ('accent_ink', 'accent-ink'),
                                         ('on_accent', 'on-accent')) if c in v}
    return t


def load(arg, _seen=None):
    """arg = preset name or path to a style JSON. Returns the fully merged style with 'fonts' resolved to paths."""
    p = pathlib.Path(arg)
    if not p.is_file() and (THEMES / f'{arg}.json').is_file():  # a preset name wins over a folder of that name
        p = THEMES / f'{arg}.json'
    if not p.is_file():
        raise SystemExit(f'style not found: {arg} (presets: {", ".join(presets())})')
    p = p.resolve()
    _seen = (_seen or set()) | {p}
    t = _legacy(json.loads(p.read_text(encoding='utf-8')))
    for f in t.get('fonts', []):  # resolve font files relative to the file that names them
        if 'path' not in f:
            cand = [p.parent / f['file'], FONTS / f['file']]
            f['path'] = str(next((c for c in cand if c.exists()), cand[-1]))
    if t.get('extends'):
        parent = THEMES / f"{t['extends']}.json" if not t['extends'].endswith('.json') else p.parent / t['extends']
        if parent.resolve() in _seen:
            raise SystemExit(f'style extends itself: {p}')
        base = load(str(parent), _seen)
        fonts = t.pop('fonts', None)
        t = merge(base, {k: v for k, v in t.items() if k != 'extends'})
        if fonts:  # fonts accumulate: an override adds a brand font, the preset's stay available
            known = {f['family'] for f in fonts}
            t['fonts'] = fonts + [f for f in base.get('fonts', []) if f['family'] not in known]
    return t


def luminance(hexcolor):
    h = hexcolor.lstrip('#')
    if len(h) == 3:
        h = ''.join(c * 2 for c in h)
    rgb = [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    r, g, b = [c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4 for c in rgb]
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def contrast(a, b):
    la, lb = luminance(a), luminance(b)
    return (max(la, lb) + 0.05) / (min(la, lb) + 0.05)


def check(t):
    """List of problems (empty = usable). Contrast failures name the pair and the ratio."""
    issues = []
    for group, keys in REQUIRED.items():
        for k in keys:
            if k not in t.get(group, {}):
                issues.append(f'missing {group}.{k}')
    for (g, k), allowed in CHOICES.items():
        v = t.get(g, {}).get(k)
        if v is not None and v not in allowed:
            issues.append(f'{g}.{k} = {v!r}, expected one of {allowed}')
    c = t.get('color', {})
    for fg, bg, need in PAIRS:
        if fg in c and bg in c:
            try:
                r = contrast(c[fg], c[bg])
            except ValueError:
                issues.append(f'color.{fg}/{bg}: not a #hex colour'); continue
            if r < need:
                issues.append(f'contrast {fg} on {bg} = {r:.2f} < {need}')
    families = {f['family'] for f in t.get('fonts', [])}
    for f in t.get('fonts', []):
        if not pathlib.Path(f['path']).exists():
            issues.append(f"font file missing: {f['file']}")
    for k in ('display', 'text'):
        fam = t.get('type', {}).get(k)
        if fam and fam not in families:
            issues.append(f'type.{k} = {fam!r} has no entry in fonts[]')
    return issues


def css_vars(t):
    """Flatten tokens to the CSS custom properties the slide template reads."""
    v = {}
    for group in ('type', 'color', 'shape', 'texture'):
        for k, val in t.get(group, {}).items():
            v[f'{group}-{k}'] = val
    ty = t['type']
    for k in ('display', 'text', 'mono'):
        if ty.get(k):
            v[f'type-{k}'] = f"'{ty[k]}'"
    v.setdefault('type-text', v['type-display'])
    v['type-case'] = 'uppercase' if ty['case'] == 'upper' else 'none'
    v['type-align_self'] = 'center' if ty['align'] == 'center' else 'flex-start'
    v.setdefault('type-tracking', '0em')
    for k in ('radius', 'rule_w', 'rule_h'):
        v[f'shape-{k}'] = f"{t['shape'][k]}px"
    v.setdefault('texture-bg_text_opacity', 0); v.setdefault('texture-bg_text_rotate', 0)
    return {k: str(x) for k, x in v.items()}


def for_page(t):
    """Theme object for the page: fonts by file name only (slides.py copies them to _html/fonts)."""
    page = copy.deepcopy(t)
    page['fonts'] = [{k: f[k] for k in ('family', 'weight') if k in f} | {'file': pathlib.Path(f['path']).name}
                     for f in t.get('fonts', [])]
    return page
