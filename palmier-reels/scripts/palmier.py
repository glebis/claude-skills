"""Shared helpers for palmier-reels: Palmier MCP client, easing, text wrap, font resolution.

Import from other scripts:  sys.path.insert(0, <skill>/scripts); from palmier import *
"""
import json, os, re, subprocess, sys, urllib.request, base64

MCP_URL = os.environ.get('PALMIER_MCP', 'http://127.0.0.1:19789/mcp')
K = 1.75   # Palmier canvas point -> px on a 1080-wide canvas (calibrated; re-check with calibrate.py if fonts look off)
LOG = []

# ---------------------------------------------------------------- MCP client
class Palmier:
    """Minimal streamable-HTTP MCP client. Responses arrive as SSE; the last `data:` JSON line is the result."""
    def __init__(self, url=MCP_URL, log=LOG):
        self.url, self.sid, self.log, self._id = url, None, log, 0
        self._post({'jsonrpc': '2.0', 'id': 0, 'method': 'initialize',
                    'params': {'protocolVersion': '2025-03-26', 'capabilities': {}, 'clientInfo': {'name': 'palmier-reels', 'version': '1'}}})
        self._post({'jsonrpc': '2.0', 'method': 'notifications/initialized'})

    def _post(self, body):
        req = urllib.request.Request(self.url, data=json.dumps(body).encode(), method='POST', headers={
            'Content-Type': 'application/json', 'Accept': 'application/json, text/event-stream',
            **({'Mcp-Session-Id': self.sid} if self.sid else {})})
        with urllib.request.urlopen(req, timeout=900) as r:
            self.sid = self.sid or r.headers.get('Mcp-Session-Id')
            raw = r.read().decode()
        last = None
        for line in raw.splitlines():
            if line.startswith('data: {'): last = line[6:]
        if last is None and raw.strip().startswith('{'): last = raw
        return json.loads(last) if last else None

    def raw(self, tool, args=None):
        self._id += 1
        d = self._post({'jsonrpc': '2.0', 'id': self._id, 'method': 'tools/call', 'params': {'name': tool, 'arguments': args or {}}})
        res = d.get('result', {})
        if d.get('error') or res.get('isError'):
            txt = ''.join(c.get('text', '') for c in res.get('content', []))
            self.log.append({'tool': tool, 'args': args, 'error': txt or str(d.get('error'))})
            raise RuntimeError(f'{tool} failed: {txt or d.get("error")}')
        return res.get('content', [])

    def call(self, tool, args=None):
        """Call a tool; return parsed JSON text when possible, else the text."""
        content = self.raw(tool, args)
        txt = ''.join(c.get('text', '') for c in content if c.get('type') == 'text')
        self.log.append({'tool': tool, 'args': args, 'result': txt[:1200]})
        try: return json.loads(txt)
        except (ValueError, TypeError): return txt

    def images(self, tool, args, prefix):
        """Call a tool that returns images (inspect_timeline) and save them as prefix-NN.jpg."""
        out = []
        for i, c in enumerate(x for x in self.raw(tool, args) if x.get('type') == 'image'):
            fn = f'{prefix}-{i:02d}.jpg'; open(fn, 'wb').write(base64.b64decode(c['data'])); out.append(fn)
        return out

    def tools(self):
        self._id += 1
        return self._post({'jsonrpc': '2.0', 'id': self._id, 'method': 'tools/list'})['result']['tools']

    # convenience
    def timeline(self): return self.call('get_timeline', {})
    def top_track(self, tl=None):
        tl = tl or self.timeline(); return [t for t in tl['tracks'] if t['index'] == 0][0]
    def track(self, name, tl=None):
        tl = tl or self.timeline(); return next((t for t in tl['tracks'] if t.get('name') == name), None)
    def name_top(self, name): self.call('manage_tracks', {'set': [{'index': 0, 'name': name}]})
    def media(self):
        return {a['name']: a['id'] for a in self.call('get_media', {})['assets']}
    def import_path(self, path, folder, name=None):
        return self.call('import_media', {'source': {'path': os.path.abspath(path)}, 'folder': folder, **({'name': name} if name else {})})['mediaRef']
    def import_matte(self, hex_, folder='Mattes'):
        return self.call('import_media', {'source': {'matte': {'hex': hex_}}, 'folder': folder, 'name': f'matte-{hex_.lstrip("#")}'})['mediaRef']


# ---------------------------------------------------------------- easing
def bezier_ease(p1x, p1y, p2x, p2y):
    """CSS cubic-bezier(p1x,p1y,p2x,p2y) as a function u -> eased u."""
    b = lambda t, a, c: 3 * (1 - t) ** 2 * t * a + 3 * (1 - t) * t * t * c + t ** 3
    def f(u):
        lo, hi = 0.0, 1.0
        for _ in range(40):
            mid = (lo + hi) / 2
            if b(mid, p1x, p2x) < u: lo = mid
            else: hi = mid
        return b((lo + hi) / 2, p1y, p2y)
    return f

def make_tween(ease_out):
    ease_in = lambda u: 1 - ease_out(1 - u)
    linear = lambda u: u
    def tween(f0, f1, v0, v1, fn=None, n=6):
        """Keyframe rows [frame, *values, 'linear'] sampling an eased curve from f0..f1 (v0/v1 tuples)."""
        fn = fn or ease_out; rows = []
        for j in range(n + 1):
            u = j / n; f = round(f0 + (f1 - f0) * u); e = fn(u)
            r = [f] + [round(a + (bb - a) * e, 5) for a, bb in zip(v0, v1)] + ['linear']
            if rows and rows[-1][0] == f: rows[-1] = r
            else: rows.append(r)
        return rows
    return tween, ease_in, linear


# ---------------------------------------------------------------- typography
NBSP = ' '

def bind(text, lang='ru'):
    """Typesetting glue: no line starts with a dash; short words stick to the next word (ru)."""
    text = re.sub(r' (—|–)', NBSP + r'\1', text)
    if lang == 'ru':
        text = re.sub(r'(?<![\w«])((?:«)?(?:[а-яёА-ЯЁ]{1,2}|AI)) ', r'\1' + NBSP, text)
        text = re.sub(r'\b(чтобы) ', r'\1' + NBSP, text)
    elif lang == 'en':
        text = re.sub(r'\b(a|an|the|to|of|in|on|at|by|I) ', r'\1' + NBSP, text)
    return text

def wrap(text, font, pt, max_px, lang='ru'):
    """Greedy wrap measured with a PIL font at 100 px (font.getlength) scaled by Palmier's K."""
    lines, cur = [], ''
    for w in bind(text, lang).split(' '):
        t = (cur + ' ' + w).strip()
        if font.getlength(t) * pt * K / 100 <= max_px or not cur: cur = t
        else: lines.append(cur); cur = w
    lines.append(cur)
    return lines

FONT_DIRS = ['/System/Library/Fonts', '/System/Library/Fonts/Supplemental', '/Library/Fonts', os.path.expanduser('~/Library/Fonts')]
_FONT_INDEX = None
def font_index():
    """PostScript name -> (file, ttc index), built once from the font folders and cached in ~/.cache."""
    global _FONT_INDEX
    if _FONT_INDEX is not None: return _FONT_INDEX
    cache = os.path.expanduser('~/.cache/palmier-reels-fonts.json')
    stamp = [max((os.path.getmtime(d) for d in FONT_DIRS if os.path.isdir(d)), default=0)]
    if os.path.exists(cache):
        c = json.load(open(cache))
        if c.get('stamp') == stamp: _FONT_INDEX = c['fonts']; return _FONT_INDEX
    from fontTools.ttLib import TTFont, TTCollection
    idx = {}
    for d in FONT_DIRS:
        if not os.path.isdir(d): continue
        for fn in os.listdir(d):
            p = os.path.join(d, fn); ext = fn.lower().rsplit('.', 1)[-1]
            try:
                fonts = TTCollection(p, lazy=True).fonts if ext == 'ttc' else [TTFont(p, lazy=True)] if ext in ('ttf', 'otf') else []
                for i, f in enumerate(fonts):
                    n = f['name'].getDebugName(6)
                    if n: idx.setdefault(n, [p, i])
            except Exception:
                pass
    os.makedirs(os.path.dirname(cache), exist_ok=True); json.dump({'stamp': stamp, 'fonts': idx}, open(cache, 'w'))
    _FONT_INDEX = idx; return idx

def font_file(ps_name):
    """(path, ttc index) for an installed PostScript name, or None."""
    return font_index().get(ps_name)

def pil_font(ps_name):
    from PIL import ImageFont
    hit = font_file(ps_name)
    if not hit: raise SystemExit(f'font {ps_name} not installed — see scripts/fonts.py')
    return ImageFont.truetype(hit[0], 100, index=hit[1])

def installed_fonts():
    import AppKit
    return set(str(n) for n in AppKit.NSFontManager.sharedFontManager().availableFonts())

def cyrillic_ok(ps_name):
    """True when the font itself covers basic Cyrillic. Palmier silently falls back otherwise."""
    hit = font_file(ps_name)
    if not hit: return False
    from fontTools.ttLib import TTFont
    cm = TTFont(hit[0], fontNumber=hit[1], lazy=True).getBestCmap()
    return all(c in cm for c in range(0x410, 0x450))

def log_dump(path):
    json.dump(LOG, open(path, 'w'), ensure_ascii=False, indent=1)
