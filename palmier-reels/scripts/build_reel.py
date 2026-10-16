"""Build (or rebuild) a vertical narrative reel in Palmier from a spec + style.

python3 build_reel.py spec.json [--style godard-riso] [--tokens design.tokens.json] [--timeline-id ID] [--dry-run]

Idempotent: on an existing timeline it removes every track except `Paper` and `Music` and rebuilds.
Writes <workdir>/plan.json, media.json, build-log.json, timeline.json.
See references/spec-format.md for the spec, references/palmier-mcp.md for the API behaviour this relies on.
"""
import argparse, json, math, os, sys
sys.path.insert(0, os.path.dirname(__file__))
from palmier import Palmier, LOG, K, NBSP, bezier_ease, make_tween, wrap, pil_font, log_dump
from style import load_style

ap = argparse.ArgumentParser()
ap.add_argument('spec'); ap.add_argument('--style'); ap.add_argument('--tokens')
ap.add_argument('--timeline-id'); ap.add_argument('--dry-run', action='store_true')
A = ap.parse_args()
SPEC = json.load(open(A.spec)); SPEC_DIR = os.path.dirname(os.path.abspath(A.spec))
rel = lambda p: p if os.path.isabs(os.path.expanduser(p)) else os.path.join(SPEC_DIR, p)
WORK = rel(SPEC.get('workdir', 'reel-work')); os.makedirs(WORK, exist_ok=True)
ST = load_style(A.style or SPEC.get('style', 'godard-riso'), A.tokens or (rel(SPEC['tokens']) if SPEC.get('tokens') else None))
if ST['missing_fonts']: sys.exit(f"missing fonts: {ST['missing_fonts']} — run scripts/fonts.py")
LANG = SPEC.get('lang', 'ru')

FPS = ST['canvas']['fps']; CW, CH = ST['canvas']['width'], ST['canvas']['height']
C = ST['color']; F = {r: f['ps'] for r, f in ST['fonts'].items()}; TY = ST['type']; LY = ST['layout']; MO = ST['motion']
fr = lambda ms: round(ms / 1000 * FPS)
EASE = bezier_ease(*MO['easing']); tween, ease_in, linear = make_tween(EASE)
CARDS = ST['cards']['enabled']; HOLD = fr(MO['card_hold_ms']) if CARDS else 0
X0 = LY['x']; MAXW = LY['measure_px'] * CW / 1080
F_CTX, F_Q, F_CARD = pil_font(F['context']), pil_font(F['quote']), pil_font(F['card'])
scenes = SPEC['scenes']; N = len(scenes)

# ------------------------------------------------------------------ connect, timeline
P = Palmier()
if SPEC.get('project'):
    lst = P.call('manage_project', {'action': 'list'})
    hit = [p for p in lst['projects'] if p['name'] == SPEC['project']]
    if hit: P.call('manage_project', {'action': 'open', 'id': hit[0]['id']})
    else:
        P.call('manage_project', {'action': 'create', 'name': SPEC['project']})
        P.call('set_project_settings', {'width': CW, 'height': CH, 'fps': FPS})
if A.timeline_id:
    P.call('set_active_timeline', {'timelineId': A.timeline_id})
else:
    P.call('create_timeline', {'name': SPEC.get('timeline', f"Reel — {ST['name']}")})
TL_ID = P.timeline()['id']

# ------------------------------------------------------------------ media (cached by path+mtime)
MEDIA_CACHE = os.path.join(WORK, 'media.json')
cache = json.load(open(MEDIA_CACHE)) if os.path.exists(MEDIA_CACHE) else {}
lib_ids = set(P.media().values())
def imp(path, folder):
    path = os.path.abspath(rel(path)); key = f'{path}|{os.path.getmtime(path)}'
    if key in cache and cache[key] in lib_ids: return cache[key]
    cache[key] = P.import_path(path, folder); json.dump(cache, open(MEDIA_CACHE, 'w'), indent=1); return cache[key]
def matte(hex_):
    key = f'matte|{hex_}'
    if key in cache and cache[key] in lib_ids: return cache[key]
    cache[key] = P.import_matte(hex_); json.dump(cache, open(MEDIA_CACHE, 'w'), indent=1); return cache[key]

# paper with grain, generated from the style
def paper_png():
    import numpy as np
    from PIL import Image
    path = os.path.join(WORK, f"paper-{C['paper'].lstrip('#')}-{ST['paper']['grain_sd']}.png")
    if not os.path.exists(path):
        rgb = np.array([int(C['paper'][i:i + 2], 16) for i in (1, 3, 5)], float)
        sd = ST['paper']['grain_sd']; rng = np.random.default_rng(7)
        g = rng.normal(0, sd, (CH, CW)) if sd else np.zeros((CH, CW))
        if sd: g = (g + np.roll(g, 1, 0) + np.roll(g, 1, 1)) / 3 * 1.6
        Image.fromarray(np.clip(rgb[None, None] + g[..., None], 0, 255).astype('uint8')).save(path)
    return path

# ------------------------------------------------------------------ music -> cuts on downbeats
def words(s): return len(s.split()) if s else 0
def plan_cuts():
    mus = SPEC.get('music')
    est = [HOLD / FPS + words(sc.get('context')) / 3.2 + words(sc.get('text')) / 2.4 + 1.3 for sc in scenes]
    if not mus:
        per = SPEC.get('scene_seconds', 6); cuts = [0]
        for e in est: cuts.append(cuts[-1] + round(max(per, e) * FPS))
        return cuts, None, None
    mid = imp(mus['path'], 'Music')
    db = P.call('detect_beats', {'mediaRef': mid})['downbeats']
    bar = sorted(b - a for a, b in zip(db, db[1:]))[len(db) // 2]
    bars = SPEC.get('bars') or [max(2, min(4, math.ceil(e / bar))) for e in est]
    maxd = SPEC.get('max_seconds', 50)
    while sum(bars) * bar > maxd and max(bars) > 2:          # trim the longest scenes until it fits
        bars[bars.index(max(bars))] -= 1
    need = sum(bars)
    start = mus.get('start')
    if start is None:                                          # latest downbeat that still leaves room (skips quiet intros)
        ok = [i for i in range(len(db)) if i + need < len(db) and db[i] >= mus.get('min_start', 0)]
        i0 = ok[0] if ok else 0
    else:
        i0 = min(range(len(db)), key=lambda i: abs(db[i] - start))
    idx = [i0]
    for b in bars: idx.append(idx[-1] + b)
    times = [db[i] if i < len(db) else db[i0] + (i - i0) * bar for i in idx]
    cuts = [round((t - times[0]) * FPS) for t in times]
    return cuts, mid, (times[0], times[-1], bars, bar)
CUTS, MUSIC_ID, MUSIC_INFO = plan_cuts()
TOTAL = CUTS[-1]
END = SPEC.get('end_card')
END_F = fr(END.get('ms', 1200)) if END else 0

# ------------------------------------------------------------------ text layout per scene
plan = []
for k, sc in enumerate(scenes):
    s, e = CUTS[k], CUTS[k + 1]
    cpt = TY['context_pt']; long_ = words(sc.get('text')) > TY['long_quote_words']
    qpt = TY['quote_pt_long'] if long_ else TY['quote_pt_short']
    cl = wrap(sc['context'], F_CTX, cpt, MAXW, LANG) if sc.get('context') else []
    ql = wrap(sc['text'], F_Q, qpt, MAXW, LANG) if sc.get('text') else []
    clh = cpt * K * TY['context_line_height'] / CH; qlh = qpt * K * 1.12 / CH
    top = LY['top']; ch = len(cl) * clh; qtop = top + ch + (LY['gap'] if cl else 0)
    plan.append(dict(k=k, s=s, e=e, D=e - s, cpt=cpt, qpt=qpt, cl=cl, ql=ql, top=top, ch=ch, qtop=qtop, qh=len(ql) * qlh))
json.dump({'cuts': CUTS, 'music': MUSIC_INFO, 'style': ST['name'], 'scenes': plan}, open(os.path.join(WORK, 'plan.json'), 'w'), ensure_ascii=False, indent=1)
for p in plan: print(p['k'], p['s'], p['e'], p['cl'], p['ql'])
if A.dry_run: sys.exit(0)

# ------------------------------------------------------------------ reset timeline: keep Paper + Music
tl = P.timeline()
for t in tl['tracks']:
    if t.get('name') not in ('Paper', 'Music'):
        P.call('manage_tracks', {'remove': [{'trackId': t['trackId']}]})
tl = P.timeline()
if not P.track('Paper', tl):
    P.call('add_clips', {'entries': [{'mediaRef': imp(paper_png(), 'Paper'), 'startFrame': 0, 'endFrame': TOTAL}]}); P.name_top('Paper')
else:
    pc = P.track('Paper', tl)['clips'][0]
    P.call('swap_clip_media', {'clipId': pc['id'], 'mediaRef': imp(paper_png(), 'Paper')})
    P.call('set_clip_properties', {'clipIds': [pc['id']], 'durationFrames': TOTAL})
if MUSIC_ID:
    mt = P.track('Music')
    if mt:
        for c in mt.get('clips', []): P.call('remove_clips', {'clipIds': [c['id']]})
    t0, t1 = MUSIC_INFO[0], MUSIC_INFO[1]
    P.call('add_clips', {'entries': [{'mediaRef': MUSIC_ID, 'startFrame': 0, 'source': [round(t0, 3), round(t0 + TOTAL / FPS, 3)]}]})
    tl = P.timeline(); at = [t for t in tl['tracks'] if t['type'] == 'audio'][-1]
    P.call('manage_tracks', {'set': [{'index': at['index'], 'name': 'Music'}]})
    P.call('set_clip_properties', {'clipIds': [at['clips'][0]['id']], 'volumeDb': SPEC['music'].get('volume_db', -3),
                                   'fadeInFrames': 6, 'fadeOutFrames': fr(1500), 'fadeOutInterpolation': 'smooth'})

def add_layer(entries, name, texts=False):
    if not entries: return []
    P.call('add_texts' if texts else 'add_clips', {'entries': entries}); P.name_top(name)
    return sorted(P.top_track()['clips'], key=lambda c: c['frames'][0])

# ------------------------------------------------------------------ art
CHAOTIC = [(0.63, 0.71, 0.86, -9, -5, (1, 0)), (0.36, 0.76, 1.18, 7, 3, (0, 1)), (0.72, 0.73, 0.98, -15, -10, (1, 0)),
           (0.70, 0.77, 0.96, -7, -4, (1, 0)), (0.50, 0.76, 1.40, -6, -2, (1, 1)), (0.47, 0.77, 0.80, 11, 6, (0, 1)),
           (0.56, 0.73, 1.02, -24, 8, (0, 0))]
CALM = [(0.5, 0.68, 0.70, 0, 0, (0, 1))]
art_entries, art_meta = [], []
for p, sc in zip(plan, scenes):
    if not sc.get('art'): continue
    a0 = p['s'] + max(0, HOLD - 2)
    art_entries.append({'mediaRef': imp(sc['art'], 'Art'), 'startFrame': a0, 'endFrame': p['e']})
    art_meta.append((p, sc))
for c, (p, sc) in zip(add_layer(art_entries, 'Art'), art_meta):
    k = p['k']; L = c['frames'][1] - c['frames'][0]
    lay = sc.get('art_layout') or {}
    base = (CHAOTIC if ST['art']['layout'] == 'chaotic' else CALM)
    cx, cy, w, r0, r1, d = base[k % len(base)] if not (ST['art']['layout'] == 'chaotic' and k == N - 1) else CHAOTIC[-1]
    cx, cy, w = lay.get('cx', cx), lay.get('cy', cy), lay.get('w', w)
    r0, r1 = lay.get('rot', [r0, r1]); d = tuple(lay.get('from', d))
    asp = sc.get('art_aspect', 1.0)                      # height/width of the image
    h = w * CW / CH * asp
    qb = p['qtop'] + p['qh'] + 0.02
    cy = max(cy, qb + h / 2 + 0.005)
    while cy + h / 2 > 1.10: w *= 0.95; h = w * CW / CH * asp; cy = max(lay.get('cy', cy), qb + h / 2 + 0.005)
    IN = fr(MO['hero_ms']); OUT = MO['exit_frames'] + 1
    x, y = cx - w / 2, cy - h / 2
    if d == (0, 0):            # grow
        sc_k = tween(0, IN, (w * 0.3, h * 0.3), (w, h)) + [[L - 1, round(w * 1.06, 4), round(h * 1.06, 4), 'linear']]
        P.call('set_keyframes', {'clipId': c['id'], 'property': 'scale', 'keyframes': sc_k})
        P.call('set_keyframes', {'clipId': c['id'], 'property': 'position', 'keyframes': [[r[0], round(cx - r[1] / 2, 5), round(cy - r[2] / 2, 5), 'linear'] for r in sc_k]})
    else:
        off = 0.75 if ST['art']['entrance'] == 'slide' else 0.06
        dx, dy = d
        kf = (tween(0, IN, (x + dx * off, y + dy * off * 0.6), (x, y))
              + [[L - OUT, round(x - dx * 0.03, 5), round(y - dy * 0.015, 5), 'linear']]
              + (tween(L - OUT + 1, L - 1, (x - dx * 0.03, y - dy * 0.015), (x - dx * 0.9, y), fn=ease_in, n=4) if ST['art']['entrance'] == 'slide' else []))
        P.call('set_keyframes', {'clipId': c['id'], 'property': 'position', 'keyframes': kf})
        P.call('set_keyframes', {'clipId': c['id'], 'property': 'scale', 'keyframes': [[0, round(w, 4), round(h, 4), 'linear'], [L - 1, round(w * 1.03, 4), round(h * 1.03, 4), 'linear']]})
    if r0 or r1:
        rs = r0 - 6 * (1 if r1 >= r0 else -1)
        P.call('set_keyframes', {'clipId': c['id'], 'property': 'rotation', 'keyframes': tween(0, IN, (rs,), (r0,)) + [[L - 1, r1, 'linear']]})
    if ST['art']['entrance'] != 'slide':     # calm: dissolve art in/out (styles that allow art opacity)
        P.call('set_clip_properties', {'clipIds': [c['id']], 'fadeInFrames': fr(MO['reveal_ms']), 'fadeOutFrames': MO['exit_frames'] + 3, 'fadeInInterpolation': 'smooth', 'fadeOutInterpolation': 'smooth'})

# ------------------------------------------------------------------ context lines
ctx_entries = [{'startFrame': p['s'] + HOLD, 'endFrame': p['e'], 'content': '\n'.join(p['cl']),
                'style': {'fontName': F['context'], 'fontSize': p['cpt'], 'color': C['ink'], 'alignment': 'left',
                          'lineSpacing': round((TY['context_line_height'] - TY['natural_line_height']) * p['cpt'], 1)},
                'transform': {'x': X0, 'y': round(p['top'] + p['ch'] / 2, 4)}} for p in plan if p['cl']]
for c, p in zip(add_layer(ctx_entries, 'Context', texts=True), [p for p in plan if p['cl']]):
    L = c['frames'][1] - c['frames'][0]; y = round(p['top'], 4); IN = fr(MO['reveal_ms']); last = p['k'] == N - 1
    if ST['context']['entrance'] == 'slide':
        kf = tween(0, IN, (-0.9, y), (X0, y)) + ([[L - 1, X0, y, 'linear']] if last else tween(L - MO['exit_frames'], L - 1, (X0, y), (-1.0, y), fn=ease_in, n=4))
        P.call('set_keyframes', {'clipId': c['id'], 'property': 'position', 'keyframes': kf})
    else:
        P.call('set_keyframes', {'clipId': c['id'], 'property': 'opacity', 'keyframes': tween(0, IN, (0,), (1,)) + tween(L - MO['exit_frames'], L - 1, (1,), (0,), fn=ease_in, n=4)})
    if last and END: P.call('set_clip_properties', {'clipIds': [c['id']], 'fadeOutFrames': 20, 'fadeOutInterpolation': 'smooth'})

# ------------------------------------------------------------------ quote / emphasis: word-by-word, silent reading pace
# Prefix clips (words 0..j) alternate between two tracks and overlap; identical earlier words coincide,
# so only the new word fades in. Never use position keyframes here (box top estimate != static centre -> jump).
qA, qB, meta = [], [], []
QCOL = C[ST['quote']['color']]
for p in plan:
    if not p['ql']: continue
    units = [w for line in p['ql'] for w in line.split(' ')]; line_of = [i for i, l in enumerate(p['ql']) for _ in l.split(' ')]
    n = len(units)
    q0 = p['s'] + HOLD + 6 + min(32, max(14, 6 * words(scenes[p['k']].get('context'))))
    reveal_end = p['s'] + int(p['D'] * 0.72)
    step = max(8, min(15, (reveal_end - q0) / n))
    T = [q0 + round(j * step) for j in range(n)]
    Fd = [fr(MO['reveal_ms']) // 2] + [max(1, min(fr(MO['reveal_ms']), (T[j + 1] - T[j]) if j + 1 < n else fr(MO['reveal_ms']))) for j in range(1, n)]
    p['word_step'] = round(step, 1)
    for j in range(n):
        lines = [[] for _ in p['ql']]
        for w, li in zip(units[:j + 1], line_of[:j + 1]): lines[li].append(w)
        end = min(T[j + 1] + Fd[j + 1], p['e']) if j + 1 < n else p['e']
        e = {'startFrame': T[j], 'endFrame': end, 'content': '\n'.join(' '.join(l) if l else NBSP for l in lines),
             'style': {'fontName': F['quote'], 'fontSize': p['qpt'], 'color': QCOL, 'alignment': 'left', 'lineSpacing': TY['quote_line_spacing']},
             'transform': {'x': X0, 'y': round(p['qtop'] + p['qh'] / 2, 4)}}
        (qA if j % 2 == 0 else qB).append(e); meta.append((T[j], j == n - 1, p, Fd[j]))
add_layer(qA, 'QuoteA', texts=True); add_layer(qB, 'QuoteB', texts=True)
tl = P.timeline()
qclips = {c['frames'][0]: c for t in tl['tracks'] if t.get('name') in ('QuoteA', 'QuoteB') for c in t['clips']}
for t0, last, p, f_in in meta:
    c = qclips[t0]; L = c['frames'][1] - c['frames'][0]; f_in = max(1, min(f_in, L - 1))
    op = tween(0, f_in, (0,), (1,), n=min(6, f_in))
    if last and not (p['k'] == N - 1 and END and CARDS):
        X = MO['exit_frames'] + 1
        op += tween(L - X, L - 1, (1,), (0,), fn=ease_in, n=4)
        if ST['quote']['exit'] == 'blur':
            P.call('set_keyframes', {'clipId': c['id'], 'property': 'blur', 'keyframes': [[0, 0, 'linear']] + tween(L - X, L - 1, (0,), (16,), fn=ease_in, n=4)})
    P.call('set_keyframes', {'clipId': c['id'], 'property': 'opacity', 'keyframes': op})

# ------------------------------------------------------------------ cards (+ words, label) and end card
card_cols = ST['cards'].get('colors', ['accent', 'ink'])
if CARDS:
    H_ = fr(MO['header_ms']); ents, info = [], []
    for p, sc in zip(plan, scenes):
        k = p['k']; col = card_cols[k % len(card_cols)]
        a = 0 if k == 0 else p['s'] - 6
        ents.append({'mediaRef': matte(C[col]), 'startFrame': a, 'endFrame': p['s'] + HOLD + H_ + 3}); info.append((k, col))
    if END:
        ents.append({'mediaRef': matte(C[card_cols[0]]), 'startFrame': TOTAL - END_F, 'endFrame': TOTAL}); info.append(('end', card_cols[0]))
    for c, (k, col) in zip(add_layer(ents, 'Cards'), info):
        L = c['frames'][1] - c['frames'][0]
        wipe = ST['cards'].get('wipes', 'alternate')
        horiz = wipe == 'horizontal' or (wipe == 'alternate' and k != 'end' and k % 2 == 1)
        if k == 0: kf = [[0, 0, 0, 'linear']] + tween(L - 1 - H_ - 2, L - 1, (0, 0), (1.0, 0), fn=ease_in, n=4)
        elif k == 'end': kf = tween(0, H_ + 2, (1.0, 0), (0, 0)) + [[L - 1, 0, 0, 'linear']]
        elif wipe == 'cut': kf = [[0, 0, 0, 'linear']]
        elif horiz: kf = tween(0, 6, (-1.0, 0), (0, 0)) + tween(L - 1 - H_ - 2, L - 1, (0, 0), (1.0, 0), fn=ease_in, n=4)
        else: kf = tween(0, 6, (0, -1.0), (0, 0)) + tween(L - 1 - H_ - 2, L - 1, (0, 0), (0, 1.0), fn=ease_in, n=4)
        P.call('set_keyframes', {'clipId': c['id'], 'property': 'position', 'keyframes': kf})
        P.call('set_keyframes', {'clipId': c['id'], 'property': 'scale', 'keyframes': [[0, 1, 1, 'linear']]})
    word_on = ST['cards'].get('word_on', {})
    cw, lab = [], []
    def card_text(txt, a, b, col, k):
        t = txt.upper() if TY.get('card_case') == 'upper' else txt
        pt = min(TY['card_max_pt'], int(0.84 * CW / (F_CARD.getlength(t) * K / 100)))
        return {'startFrame': a, 'endFrame': b, 'content': t,
                'style': {'fontName': F['card'], 'fontSize': pt, 'color': C[word_on.get(col, 'paper')], 'alignment': 'left'},
                'transform': {'x': 0.08, 'y': 0.5, **({'rotation': -3 if k % 2 else 2} if isinstance(k, int) and ST['name'] != 'calm-editorial' else {})}}
    for p, sc in zip(plan, scenes):
        col = card_cols[p['k'] % len(card_cols)]
        if sc.get('card'): cw.append(card_text(sc['card'], p['s'], p['s'] + HOLD, col, p['k']))
        if sc.get('label'):
            lab.append({'startFrame': p['s'], 'endFrame': p['s'] + HOLD, 'content': sc['label'],
                        'style': {'fontName': F['label'], 'fontSize': TY['label_pt'], 'color': C[word_on.get(col, 'paper')], 'alignment': 'left', 'tracking': 1},
                        'transform': {'x': 0.09, 'y': 0.565}})
    if END: cw.append(card_text(END['text'], TOTAL - END_F + 6, TOTAL, card_cols[0], 'end'))
    add_layer(cw, 'CardWords', texts=True); add_layer(lab, 'CardLabel', texts=True)
elif END:   # no cards: end title fades in on paper
    add_layer([{'startFrame': TOTAL - END_F, 'endFrame': TOTAL, 'content': END['text'],
                'style': {'fontName': F['card'], 'fontSize': 90, 'color': C['ink'], 'alignment': 'left'}, 'transform': {'x': X0, 'y': 0.5}}], 'EndTitle', texts=True)

# ------------------------------------------------------------------ sound effects (generated by sfx.py into <workdir>/sfx)
SFXDIR = os.path.join(WORK, 'sfx'); man_path = os.path.join(SFXDIR, 'manifest.json')
if ST['sfx']['enabled'] and os.path.exists(man_path):
    man = json.load(open(man_path)); have = lambda n: n in man
    sid = lambda n: imp(os.path.join(SFXDIR, n + '.wav'), 'SFX')
    on = lambda n: round(man[n]['onset'] * FPS); pk = lambda n: round(man[n]['peak'] * FPS)
    hits, swish, foley = [], [], []
    for p in plan:
        k, s0 = p['k'], p['s']
        if k == 0:
            if have('opening'): swish.append(('opening', 0, -14))
            if CARDS and have('hit-accent'): hits.append(('hit-accent', 0, -9))
        elif CARDS:
            if have('whoosh'): swish.append(('whoosh', s0 - 6 - pk('whoosh'), -13))
            col = card_cols[k % len(card_cols)]
            h = 'hit-accent' if col == card_cols[0] else 'hit-ink'
            if have(h): hits.append((h, s0 - on(h), -9 if h == 'hit-accent' else -10))
            if have('card-out'): swish.append(('card-out', s0 + HOLD, -17))
        if k == N - 1 and have('riser'): foley.append(('riser', s0 - pk('riser'), -13))
        n_ = f'scene-{k}'
        if have(n_): foley.append((n_, s0 + HOLD + 4 - on(n_), -16))
    if END and have('end'): hits.append(('end', TOTAL - END_F, -8))
    for group, name in ((hits, 'SFX-Hits'), (swish, 'SFX-Swish'), (foley, 'SFX-Foley')):
        group = sorted([g for g in group if g[1] < TOTAL], key=lambda g: g[1])
        # same-track clips must not overlap: drop any that would
        keep, last_end = [], -1
        for n_, a, db in group:
            a = max(0, a); dur = round(man[n_]['seconds'] * FPS)
            if a >= last_end: keep.append((n_, a, db)); last_end = a + dur
        if not keep: continue
        P.call('add_clips', {'entries': [{'mediaRef': sid(n_), 'startFrame': a} for n_, a, _ in keep]})
        tl = P.timeline(); t = [t for t in tl['tracks'] if t['type'] == 'audio'][-1]
        P.call('manage_tracks', {'set': [{'index': t['index'], 'name': name}]})
        for c, (n_, a, db) in zip(sorted(t['clips'], key=lambda c: c['frames'][0]), keep):
            P.call('set_clip_properties', {'clipIds': [c['id']], 'volumeDb': db, 'fadeOutFrames': min(4, c['frames'][1] - c['frames'][0] - 1)})

# ------------------------------------------------------------------ outputs
json.dump({'timeline_id': TL_ID, 'cuts': CUTS, 'music': MUSIC_INFO, 'style': ST['name'], 'scenes': plan}, open(os.path.join(WORK, 'plan.json'), 'w'), ensure_ascii=False, indent=1)
json.dump(P.timeline(), open(os.path.join(WORK, 'timeline.json'), 'w'), ensure_ascii=False, indent=1)
log_dump(os.path.join(WORK, 'build-log.json'))
print(json.dumps({'timeline_id': TL_ID, 'frames': TOTAL, 'seconds': TOTAL / FPS, 'calls': len(LOG)}))
