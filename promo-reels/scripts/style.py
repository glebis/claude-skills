#!/usr/bin/env python3
"""Choose the look of the slides: presets, a reference image/site, or token-by-token dialogue.

    style.py list
    style.py preview SLIDES.json --out DIR [--styles a,b,c|all] [--slide hook] [--lang ru]
    style.py from-ref REF [REF…] --out style.json [--font serif|condensed|geometric|wide|mono]
                      [--case upper|none] [--align left|center] [--base PRESET] [--accent HEX]
    style.py set style.json KEY=VALUE [KEY=VALUE…]     e.g. color.accent=#7A1F3D type.case=none
    style.py check STYLE
    style.py calibrate STYLE [--lang ru,en] [--write]

preview  renders the project's real hook (or --slide) in each style → DIR/<style>.png, a contact
         sheet DIR/styles.jpg and DIR/choice.json: ready arguments for a picker (cenno `ask_user` with
         an ImageChoice, or plain `choices` for any question tool). Styles whose copy budget the hook
         breaks are still shown, marked "copy too long".
from-ref REF = image file(s) or an http(s) URL (screenshotted with headless Chrome). Extracts a
         palette (k-means in Lab), assigns roles (bg, ink, accent…), repairs contrast, writes an
         override style.json that extends the closest preset, plus DIR/ref_palette.png. Fonts cannot
         be read reliably from pixels: look at the reference and pass --font/--case/--align.
set      edits tokens in a project style file (creates {"extends": "doc-red"} if missing), repairs the
         colours that now fail contrast (text on the changed colour — never a colour set in this call),
         checks it and re-measures the copy budget.
calibrate measures type.fill_chars — how many letters a full-width line holds at ≥ 140 px in this
         style — so the copy is written for the font. The audit quotes it in REWRITE messages.
"""
import argparse, json, pathlib, sys, tempfile, urllib.parse
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import runlog, tokens  # noqa: E402

FONT_PRESET = {'condensed': 'doc-red', 'serif': 'editorial', 'wide': 'pop', 'geometric': 'minimal', 'mono': 'zine'}
PROBE = {'ru': 'наблюдение', 'en': 'rehearsals'}  # 10 letters of average width per language
FILL_MIN = 140


def show(t, path=''):
    ty, c = t['type'], t['color']
    return (f"{t.get('name', path):10} {ty['display']} · {ty['case']} · {ty['align']} · "
            f"bg {c['bg']} ink {c['ink']} accent {c['accent']} · button {t['shape']['button']}"
            + (f" · fill ≤{ty['fill_chars']}" if ty.get('fill_chars') else ''))


# ---------- calibrate ----------
def calibrate(style, langs=('ru', 'en')):
    import slides
    out = {}
    with tempfile.TemporaryDirectory() as d:
        for lang in langs:
            probe = PROBE.get(lang, PROBE['en'])
            spec = [{'name': f'probe_{lang}', 'type': 'hook', 'lines': [probe] * 3}]
            _, rows = slides.render(spec, d, style, lang, force=True, log=False, screenshot=False, quiet=True)
            px = min((r['font'] for r in rows if r.get('text', '').lower() == probe and 'font' in r), default=0)
            out[lang] = max(3, int(10 * px / FILL_MIN)) if px else None
    return out


def write_fill(path, budget):
    p = pathlib.Path(path)
    data = json.loads(p.read_text(encoding='utf-8'))
    data.setdefault('type', {})['fill_chars'] = budget
    p.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


# ---------- preview ----------
def sheet(items, out):
    import cv2, numpy as np
    tiles = []
    for name, png, note in items:
        img = cv2.imread(str(png)) if png.exists() else np.full((1920, 1080, 3), 200, np.uint8)
        img = cv2.resize(img, (360, 640), interpolation=cv2.INTER_AREA)
        bar = np.full((56, 360, 3), 255, np.uint8)
        cv2.putText(bar, name, (12, 26), cv2.FONT_HERSHEY_SIMPLEX, 0.75, (20, 20, 20), 2, cv2.LINE_AA)
        if note:
            cv2.putText(bar, note, (12, 48), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (40, 40, 200), 1, cv2.LINE_AA)
        tiles.append(np.vstack([img, bar]))
    cols = min(3, len(tiles))
    while len(tiles) % cols:
        tiles.append(np.full_like(tiles[0], 255))
    rows = [np.hstack(tiles[i:i + cols]) for i in range(0, len(tiles), cols)]
    cv2.imwrite(str(out), np.vstack(rows), [cv2.IMWRITE_JPEG_QUALITY, 88])


def preview(a):
    import slides
    spec = json.loads(pathlib.Path(a.spec).read_text(encoding='utf-8'))
    pick = next((s for s in spec if s['name'] == a.slide or s['type'] == a.slide), spec[0])
    styles = tokens.presets() if a.styles in (None, 'all') else a.styles.split(',')
    local = pathlib.Path(a.spec).resolve().parent / 'style.json'
    if a.styles is None and local.exists():
        styles = [str(local)] + styles
    out = pathlib.Path(a.out).resolve(); out.mkdir(parents=True, exist_ok=True)
    items, options = [], []
    for st in styles:
        label = pathlib.Path(st).stem if st.endswith('.json') else st
        bad, rows = slides.render([{**pick, 'name': label}], out / '_render', st, a.lang, force=True, log=False, quiet=True)
        png = out / f'{label}.png'
        src = out / '_render' / f'{label}.png'
        if src.exists():
            src.replace(png)
        too_long = any('REWRITE' in i for r in rows for i in r['issues'])
        other = [i for r in rows for i in r['issues'] if 'REWRITE' not in i]
        note = 'copy too long' if too_long else ('; '.join(other)[:40] if other else '')
        t = tokens.load(st)
        print(f"{'!' if note else '✓'} {label:10} {note or 'fits'} — {t.get('description', '')[:90]}")
        items.append((label, png, note))
        options.append({'value': label, 'label': label + (f' ({note})' if note else ''), 'image': str(png)})
    sheet(items, out / 'styles.jpg')
    choice = {
        'title': 'Which look for the slides?',
        'body_md': 'Your hook in each style. Pick the closest — colours, font and details can be tuned next.',
        'input': {'kind': 'choice'}, 'choices': [o['value'] for o in options] + ['from a reference'],
        'a2ui': [{'id': 'root', 'component': 'Column', 'children': ['ic']},
                 {'id': 'ic', 'component': 'ImageChoice', 'variant': 'mutuallyExclusive', 'fit': 'contain',
                  'options': options, 'value': {'path': '/pick'},
                  'selectAction': {'event': {'name': 'submit-image', 'context': {'value': {'path': '/pick'}, 'via': 'choice'}}}}],
    }
    (out / 'choice.json').write_text(json.dumps(choice, ensure_ascii=False, indent=2), encoding='utf-8')
    print(f'→ {out / "styles.jpg"}  (contact sheet)\n→ {out / "choice.json"}  (picker arguments)')


# ---------- from-ref ----------
def grab_url(url, out):
    import slides, subprocess
    png = out / 'ref_url.png'
    exe = slides.chrome()
    subprocess.run([exe, '--headless=new', '--disable-gpu', '--hide-scrollbars', '--window-size=1280,1600',
                    f'--screenshot={png}', url], capture_output=True, timeout=90)
    if not png.exists():
        sys.exit(f'could not screenshot {url} (no network?) — save a screenshot and pass the image instead')
    return png


def palette(paths, k=6):
    import cv2, numpy as np
    px = []
    for p in paths:
        img = cv2.imread(str(p))
        if img is None:
            sys.exit(f'cannot read image {p}')
        h, w = img.shape[:2]; s = 400 / max(h, w)
        img = cv2.resize(img, (max(1, int(w * s)), max(1, int(h * s))), interpolation=cv2.INTER_AREA)
        px.append(cv2.cvtColor(img, cv2.COLOR_BGR2LAB).reshape(-1, 3))
    lab = np.vstack(px).astype(np.float32)
    _, labels, centers = cv2.kmeans(lab, k, None, (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 30, 0.5), 4,
                                    cv2.KMEANS_PP_CENTERS)
    share = np.bincount(labels.ravel(), minlength=k) / len(labels)
    pal = sorted(_entries(centers, share), key=lambda c: -c['share'])
    # Pass 2 — brand accents are small (dots, underlines, a button) and drown in area clusters:
    # cluster only strongly saturated pixels, rank by count × chroma.
    chroma = np.hypot(lab[:, 1] - 128, lab[:, 2] - 128)
    sat = lab[chroma >= 40]
    accents = []
    if len(sat) >= max(30, len(lab) * 0.0005):
        k2 = min(4, len(sat))
        _, l2, c2 = cv2.kmeans(sat, k2, None, (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 30, 0.5), 3,
                               cv2.KMEANS_PP_CENTERS)
        accents = sorted(_entries(c2, np.bincount(l2.ravel(), minlength=k2) / len(lab)),
                         key=lambda c: -(c['share'] ** 0.5 * c['chroma']))
    return pal, accents


def _entries(centers, share):
    import cv2, numpy as np
    k = len(centers)
    rgb = cv2.cvtColor(centers.reshape(1, k, 3).astype(np.uint8), cv2.COLOR_LAB2RGB).reshape(k, 3)
    return [{'hex': '#%02X%02X%02X' % tuple(int(v) for v in rgb[i]), 'share': float(share[i]),
             'chroma': float(np.hypot(centers[i][1] - 128, centers[i][2] - 128)), 'L': float(centers[i][0]) / 2.55}
            for i in range(k)]


def shade(hexcolor, toward, steps=20):
    """Move a colour toward black/white until it reaches 3:1 against `toward`'s opposite."""
    h = hexcolor.lstrip('#'); rgb = [int(h[i:i + 2], 16) for i in (0, 2, 4)]
    target = 0 if toward == 'dark' else 255
    for s in range(steps + 1):
        f = s / steps
        yield '#%02X%02X%02X' % tuple(round(c + (target - c) * f) for c in rgb)


def assign(pal, accents, accent=None):
    C = tokens.contrast
    bg = pal[0]['hex']
    ink = max((c['hex'] for c in pal[1:]), key=lambda h: C(h, bg), default='#111111')
    if C(ink, bg) < 4.5:
        ink = max(('#111111', '#F5F5F5'), key=lambda h: C(h, bg))
    if not accent:
        accent = accents[0]['hex'] if accents else ink  # no saturated colour at all → monochrome style
    dark_bg = tokens.luminance(bg) < 0.2
    accent_ink = next((x for x in shade(accent, 'light' if dark_bg else 'dark') if C(x, bg) >= 3), ink)
    on_accent = max([bg, ink, '#FFFFFF', '#111111'], key=lambda h: (C(h, accent) >= 4.5 and h in (bg, ink), C(h, accent)))
    cta_date = next((h for h in (ink, bg, accent_ink) if h != on_accent and C(h, accent) >= 3), on_accent)
    return {'bg': bg, 'ink': ink, 'accent': accent, 'accent_ink': accent_ink, 'on_accent': on_accent,
            'cta_bg': accent, 'cta_ink': on_accent, 'cta_date': cta_date}, dark_bg


def swatch(pal, colors, out):
    import cv2, numpy as np
    img = np.full((220, 120 * max(len(pal), len(colors)), 3), 255, np.uint8)
    for i, c in enumerate(pal[:len(colors)]):
        h = c['hex'].lstrip('#'); img[:90, i * 120:(i + 1) * 120] = [int(h[j:j + 2], 16) for j in (4, 2, 0)]
        cv2.putText(img, f"{c['share']*100:.0f}%", (i * 120 + 8, 108), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 0, 0), 1)
    for i, (role, hx) in enumerate(colors.items()):
        h = hx.lstrip('#'); img[120:190, i * 120:(i + 1) * 120] = [int(h[j:j + 2], 16) for j in (4, 2, 0)]
        cv2.putText(img, role[:12], (i * 120 + 6, 210), cv2.FONT_HERSHEY_SIMPLEX, 0.42, (0, 0, 0), 1)
    cv2.imwrite(str(out), img)


def _round(c):
    return {k: (round(v, 4) if isinstance(v, float) else v) for k, v in c.items()}


def from_ref(a):
    out = pathlib.Path(a.out).resolve(); out.parent.mkdir(parents=True, exist_ok=True)
    paths = []
    for r in a.refs:
        paths.append(grab_url(r, out.parent) if urllib.parse.urlparse(r).scheme in ('http', 'https') else pathlib.Path(r))
    pal, accents = palette(paths)
    colors, dark = assign(pal, accents, a.accent)
    base = a.base or (FONT_PRESET.get(a.font) if a.font else ('night' if dark else 'doc-red'))
    style = {'extends': base, 'name': out.stem, 'description': f'From reference: {", ".join(pathlib.Path(str(p)).name for p in paths)}',
             'color': colors, 'source': {'refs': [str(r) for r in a.refs], 'palette': [_round(c) for c in pal],
                                          'accent_candidates': [_round(c) for c in accents[:3]]}}
    ty = {k: v for k, v in (('case', a.case), ('align', a.align)) if v}
    if ty:
        style['type'] = ty
    if a.font and a.base and FONT_PRESET[a.font] != a.base:  # font archetype differs from the base preset: borrow its fonts
        donor = tokens.load(FONT_PRESET[a.font])
        style['type'] = {**style.get('type', {}), 'display': donor['type']['display'], 'text': donor['type']['text']}
        style['fonts'] = [{k: f[k] for k in ('family', 'file', 'weight') if k in f} for f in donor['fonts']]
    out.write_text(json.dumps(style, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    budget = calibrate(str(out)); write_fill(out, budget)
    swatch(pal + accents[:3], colors, out.parent / 'ref_palette.png')
    t = tokens.load(str(out)); issues = tokens.check(t)
    print('palette: ' + '  '.join(f"{c['hex']} {c['share']*100:.0f}%" for c in pal))
    print('accent candidates (saturated, small areas count): ' + ('  '.join(f"{c['hex']} {c['share']*100:.2f}%" for c in accents[:3]) or 'none — monochrome'))
    print('roles:   ' + '  '.join(f'{k}={v}' for k, v in colors.items()))
    if len(accents) > 1 and not a.accent:
        print('  → photos in a reference also produce saturated pixels: confirm the accent with the user '
              '(rerun with --accent HEX to pick another candidate)')
    print(show(t, out.stem)); print('check:', 'OK' if not issues else '; '.join(issues))
    print(f'→ {out}\n→ {out.parent / "ref_palette.png"}  (palette and roles — look at it next to the reference)')
    runlog.signal('scenario', 'style', 'style from reference', base=base, font=a.font, dark=dark)


# ---------- set / check ----------
def follow_accent(old, new, keep):
    """Roles derived from the accent in the old style move with it: cta_bg (when it was the accent),
    accent_ink (the accent, or a shade of it that reads on bg), cta_date (when it was the accent)."""
    if 'accent' not in keep or old['accent'] == new['accent']:
        return {}
    out, C = {}, tokens.contrast
    if 'cta_bg' not in keep and old['cta_bg'] == old['accent']:
        out['cta_bg'] = new['accent']
    if 'cta_date' not in keep and old['cta_date'] == old['accent']:
        out['cta_date'] = new['accent']
    if 'accent_ink' not in keep:
        dark = tokens.luminance(new['bg']) >= 0.2
        out['accent_ink'] = next((x for x in shade(new['accent'], 'dark' if dark else 'light') if C(x, new['bg']) >= 3),
                                 new['ink'])
    return out


def repair(t, keep):
    """Fix colour pairs that fail contrast by changing the dependent colour (the text colour),
    never one the user just set (`keep`). Returns {role: new} for the roles changed."""
    C, c, fixed = tokens.contrast, t['color'], {}
    for fg, bg, need in tokens.PAIRS:
        if fg in keep or C(c[fg], c[bg]) >= need:
            continue
        if fg == 'accent_ink':
            dark = tokens.luminance(c['bg']) >= 0.2
            new = next((x for x in shade(c['accent'], 'dark' if dark else 'light') if C(x, c[bg]) >= need), c['ink'])
        else:
            pool = [c['bg'], c['ink'], c['cta_ink'], '#FFFFFF', '#111111']
            new = max(pool, key=lambda h: (C(h, c[bg]) >= max(need, 4.5) and h in (c['bg'], c['ink']), C(h, c[bg])))
        if C(new, c[bg]) >= need:
            c[fg] = fixed[fg] = new
    return fixed


def coerce(v):
    try:
        return json.loads(v)
    except ValueError:
        return v


def set_tokens(a):
    p = pathlib.Path(a.style)
    data = json.loads(p.read_text(encoding='utf-8')) if p.exists() else {'extends': 'doc-red'}
    for kv in a.pairs:
        key, _, val = kv.partition('=')
        if not _:
            sys.exit(f'expected KEY=VALUE, got {kv!r}')
        *groups, leaf = key.split('.')
        node = data
        for g in groups:
            node = node.setdefault(g, {})
        node[leaf] = coerce(val)
    keep = {k.split('=')[0].split('.', 1)[1] for k in a.pairs if k.startswith('color.')}
    if not a.no_repair:
        before = tokens.load(str(p)) if p.exists() else tokens.load(data.get('extends', 'doc-red'))
        p.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
        t = tokens.load(str(p))
        linked = follow_accent(before['color'], t['color'], keep)
        if linked:
            data.setdefault('color', {}).update(linked); t['color'].update(linked)
            print('follow the accent: ' + ', '.join(f'{k} → {v}' for k, v in linked.items()))
        fixed = repair(t, keep)
        if fixed:
            data.setdefault('color', {}).update(fixed)
            print('repaired for contrast: ' + ', '.join(f'{k} → {v}' for k, v in fixed.items()))
    p.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    if not any(k.startswith('type.fill_chars') for k in a.pairs):
        write_fill(p, calibrate(str(p)))
    t = tokens.load(str(p)); issues = tokens.check(t)
    print(show(t, p.stem)); print('check:', 'OK' if not issues else '; '.join(issues))
    sys.exit(1 if issues else 0)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest='cmd', required=True)
    sub.add_parser('list')
    p = sub.add_parser('preview'); p.add_argument('spec'); p.add_argument('--out', required=True)
    p.add_argument('--styles'); p.add_argument('--slide', default='hook'); p.add_argument('--lang', default='ru')
    p = sub.add_parser('from-ref'); p.add_argument('refs', nargs='+'); p.add_argument('--out', default='style.json')
    p.add_argument('--font', choices=sorted(FONT_PRESET)); p.add_argument('--case', choices=('upper', 'none'))
    p.add_argument('--align', choices=('left', 'center')); p.add_argument('--base', choices=tokens.presets())
    p.add_argument('--accent', help='#hex — override the detected accent (e.g. another candidate)')
    p = sub.add_parser('set'); p.add_argument('style'); p.add_argument('pairs', nargs='+')
    p.add_argument('--no-repair', action='store_true', help="don't adjust dependent colours that fail contrast")
    p = sub.add_parser('check'); p.add_argument('style')
    p = sub.add_parser('calibrate'); p.add_argument('style'); p.add_argument('--lang', default='ru,en')
    p.add_argument('--write', action='store_true')
    a = ap.parse_args()
    runlog.init()
    if a.cmd == 'list':
        for n in tokens.presets():
            t = tokens.load(n)
            print(show(t)); print(f"{'':10} {t['description']}\n{'':10} mood: {', '.join(t.get('mood', []))}")
    elif a.cmd == 'preview':
        preview(a)
    elif a.cmd == 'from-ref':
        from_ref(a)
    elif a.cmd == 'set':
        set_tokens(a)
    elif a.cmd == 'check':
        t = tokens.load(a.style); issues = tokens.check(t)
        print(show(t, a.style)); print('check:', 'OK' if not issues else '\n  '.join([''] + issues))
        sys.exit(1 if issues else 0)
    elif a.cmd == 'calibrate':
        b = calibrate(a.style, a.lang.split(','))
        print(f'fill_chars: {b}  (letters per full-width line at ≥ {FILL_MIN} px)')
        if a.write:
            p = pathlib.Path(a.style) if pathlib.Path(a.style).exists() else tokens.THEMES / f'{a.style}.json'
            write_fill(p, b); print(f'→ {p}')


if __name__ == '__main__':
    main()
