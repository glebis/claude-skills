"""Resolve a reel style: a preset (assets/styles/<name>.json) optionally overlaid with DTCG design tokens.

python3 style.py <preset|path.json> [--tokens design.tokens.json]   -> prints the resolved style JSON
"""
import argparse, json, os, sys
sys.path.insert(0, os.path.dirname(__file__))
from palmier import installed_fonts

SKILL = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WEIGHT_NAMES = {100: ['Thin', 'Hairline'], 200: ['ExtraLight', 'UltraLight'], 300: ['Light'], 400: ['Regular', 'Book', 'Roman', ''],
                500: ['Medium'], 600: ['SemiBold', 'DemiBold'], 700: ['Bold'], 800: ['ExtraBold', 'Heavy'], 900: ['Black']}

def deep_merge(a, b):
    out = dict(a)
    for k, v in b.items():
        out[k] = deep_merge(out[k], v) if isinstance(v, dict) and isinstance(out.get(k), dict) else v
    return out

def ps_name(family, weight=400, italic=False, have=None):
    """Find the installed PostScript name for family + CSS weight (+ italic)."""
    have = have or installed_fonts()
    fam = family.replace(' ', '')
    cands = []
    for wn in WEIGHT_NAMES.get(int(weight), ['Regular']):
        if italic:
            cands += [f'{fam}-{wn}Italic', f'{fam}Italic-{wn}', f'{fam}-Italic' if wn in ('Regular', '') else None]
        else:
            cands += [f'{fam}-{wn}' if wn else fam, fam if wn in ('Regular', '') else None]
    for c in cands:
        if c and c in have: return c
    return None

def tokens_overlay(tok):
    """Map common DTCG token names onto the style schema. Unknown tokens are ignored."""
    v = lambda *path: _get(tok, path)
    o = {'color': {}, 'fonts': {}, 'type': {}, 'motion': {}}
    for src, dst in [('background', 'paper'), ('text', 'ink'), ('primary', 'accent'), ('on-primary', 'on_accent'), ('muted', 'muted')]:
        if v('color', src): o['color'][dst] = v('color', src)
    fam = lambda key: (v('font', key) or [None])[0] if isinstance(v('font', key), list) else v('font', key)
    w = lambda key, d: v('weight', key) or d
    if fam('display'):
        o['fonts']['context'] = {'family': fam('display'), 'weight': w('display', 400)}
        o['fonts']['card'] = {'family': fam('display'), 'weight': w('wordmark', 600)}
    if fam('editorial'): o['fonts']['quote'] = {'family': fam('editorial'), 'weight': 400, 'italic': True}
    if fam('label'): o['fonts']['label'] = {'family': fam('label'), 'weight': w('regular', 400)}
    if v('lineHeight', 'heading'): o['type']['context_line_height'] = v('lineHeight', 'heading')
    ez = v('motion', 'easing') or _find_easing(tok)
    if isinstance(ez, str) and ez.startswith('cubic-bezier'):
        o['motion']['easing'] = [float(x) for x in ez[ez.index('(') + 1:-1].split(',')]
    for key, dst in [('hero', 'hero_ms'), ('reveal', 'reveal_ms'), ('header', 'header_ms')]:
        m = v('motion', key)
        if isinstance(m, dict) and 'value' in m: o['motion'][dst] = m['value']
    return o

def _find_easing(tok):
    for ext in tok.get('$extensions', {}).values():
        if isinstance(ext, dict) and isinstance(ext.get('motion'), dict) and 'easing' in ext['motion']:
            return ext['motion']['easing']

def _get(d, path):
    for p in path:
        if not isinstance(d, dict) or p not in d: return None
        d = d[p]
    return d['$value'] if isinstance(d, dict) and '$value' in d else d

def load_style(preset, tokens=None):
    path = preset if preset.endswith('.json') else os.path.join(SKILL, 'assets', 'styles', preset + '.json')
    st = json.load(open(path))
    if tokens:
        st = deep_merge(st, tokens_overlay(json.load(open(tokens))))
        st['tokens_source'] = os.path.abspath(tokens)
    have = installed_fonts(); missing = []
    for role, f in st['fonts'].items():
        if 'ps' not in f or f['ps'] not in have:
            f['ps'] = ps_name(f['family'], f.get('weight', 400), f.get('italic', False), have)
            if not f['ps']: missing.append(f"{role}: {f['family']} {f.get('weight', 400)}{' italic' if f.get('italic') else ''}")
    st['missing_fonts'] = missing
    return st

if __name__ == '__main__':
    ap = argparse.ArgumentParser(); ap.add_argument('preset'); ap.add_argument('--tokens')
    a = ap.parse_args(); st = load_style(a.preset, a.tokens)
    print(json.dumps(st, ensure_ascii=False, indent=1))
    if st['missing_fonts']: print('MISSING FONTS:', st['missing_fonts'], file=sys.stderr); sys.exit(2)
