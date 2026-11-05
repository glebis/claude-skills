#!/usr/bin/env python3
"""Build an interactive app map from a hand-written map.json and the project's real tests.

Usage: app_map.py <map.json> [--repo DIR] [--out FILE] [--check-only]

Reads test names from the repo, classifies them by kind and state, checks the map
against what it found, renders sequence diagrams and writes one self-contained HTML page.
Exits 1 when the check finds errors; warnings never stop the build.
"""
import argparse, glob, hashlib, html, json, os, re, shutil, subprocess, sys, tempfile
from collections import Counter
from pathlib import Path

ASSETS = Path(__file__).resolve().parent.parent / 'assets'

# Order matters: the first state whose pattern matches wins
STATES = [
    ('refused', r'refus|reject|den(y|ied)|block|forbid|outside|unsafe|travers|unauthori|not.allowed|\bscope|guard|secret|redact|permission|withh|escape'),
    ('conflict', r'conflict|stale|\bchanged|mismatch|hash|drift|concurren|\brevision|newer|\brace\b|\blease|overwrit|\block'),
    ('missing', r'missing|not.installed|unavailable|absent|\binstall|offline|no.key|without.(a.)?key|dependenc|not.configured'),
    ('error', r'error|fail|crash|invalid|broken|corrupt|timeout|timed.out|\bsignal|malformed|exception|retry|recover'),
    ('empty', r'\bempty|nothing|blank|\bzero\b|no.(items|notes|sources|results)|first.(run|launch|time|open)|before.any'),
    ('progress', r'in.progress|progress.(bar|line|event|poll)|poll|pending|queue|running|\bundo|timer|commit|delay|loading|busy|resume|cancel|interrupt|waits?.for'),
]
EXT_KIND = {'.py': 'py', '.rs': 'rust', '.go': 'go', '.swift': 'swift', '.rb': 'ruby'}
JS_EXT = ('.js', '.cjs', '.mjs', '.ts', '.tsx', '.jsx')
SKIP_DIRS = re.compile(r'(^|/)(node_modules|target|dist|build|\.git|\.venv|venv|DerivedData)/')


def state_of(name):
    n = name.lower()
    return next((s for s, pat in STATES if re.search(pat, n)), 'happy')


def spaced(name):
    # test_empty_inbox / testEmptyInbox -> "empty inbox"
    name = re.sub(r'^(test_?|Test)', '', name)
    return re.sub(r'(?<=[a-z0-9])(?=[A-Z])', ' ', name).replace('_', ' ').strip().lower() or name


def test_names(path):
    src = path.read_text(errors='replace')
    if path.suffix == '.py':
        return [spaced(m) for m in re.findall(r'^\s*(?:async\s+)?def (test_?\w*)', src, re.M)]
    if path.suffix in JS_EXT:
        return [m[1] for m in re.findall(r"""\b(?:test|it)(?:\.\w+)?\(\s*(['"`])(.+?)\1""", src)]
    if path.suffix == '.rs':
        return [spaced(m) for m in re.findall(r'#\[(?:tokio::)?test[^\]]*\]\s*(?:#\[[^\]]*\]\s*)*(?:async\s+)?fn (\w+)', src)]
    if path.suffix == '.go':
        return [spaced(m) for m in re.findall(r'^func (Test\w+)\(', src, re.M)]
    if path.suffix == '.swift':
        return [spaced(m) for m in re.findall(r'func (test\w+)\(', src)] + re.findall(r'@Test\(\s*"([^"]+)"', src)
    if path.suffix == '.rb':
        return [m[1] for m in re.findall(r"""\b(?:it|test)\s+(['"])(.+?)\1""", src)]
    return []


def kind_of(rel, name, cfg, kinds):
    if 'mock' in kinds and re.search(r'mock|fake|stub', name.lower()):
        return 'mock'
    for rule in cfg.get('kinds', []):
        if re.search(rule['pattern'], rel):
            return rule['kind']
    suffix = Path(rel).suffix
    return 'js' if suffix in JS_EXT else EXT_KIND.get(suffix, 'other')


def read_tests(repo, m):
    """Link every test file to screens: named on a screen, matched by a link rule, or the default screen."""
    cfg, kinds = m.get('testing', {}), m['kinds']
    files, links, unscreened, missing = {}, {}, [], []

    def load(rel):
        if rel not in files:
            names = test_names(repo / rel)
            if not names:
                return False
            files[rel] = [[n, kind_of(rel, n, cfg, kinds), state_of(n)] for n in names]
        return True

    def link(sid, rel):
        if load(rel) and rel not in links.setdefault(sid, []):
            links[sid].append(rel)

    found = []
    for pat in cfg.get('globs', []):
        for full in sorted(glob.glob(str(repo / pat), recursive=True)):
            rel = os.path.relpath(full, repo)
            if os.path.isfile(full) and not SKIP_DIRS.search(rel + '/') and rel not in found:
                found.append(rel)
    by_base = {}
    for rel in found:
        by_base.setdefault(os.path.basename(rel), []).append(rel)
    named = set()
    for s in m['screens']:
        for t in s.get('t', []):
            hits = [t] if (repo / t).is_file() else by_base.get(os.path.basename(t), [])
            if not hits:
                missing.append(f"{s['id']}: {t}")
            for rel in hits:
                named.add(rel)
                link(s['id'], rel)
    ignore = cfg.get('ignore')
    for rel in found:
        hit = False
        for rule in cfg.get('links', []):
            if re.search(rule['pattern'], rel):
                hit = True
                for sid in rule['screens']:
                    link(sid, rel)
        if hit or rel in named or not load(rel):
            continue
        if ignore and re.search(ignore, rel):
            unscreened.append(rel)
            del files[rel]
        elif cfg.get('defaultScreen'):
            link(cfg['defaultScreen'], rel)
        else:
            unscreened.append(rel)
            del files[rel]
    # Checks that are not named tests, such as a screenshot pass or a live run
    for extra in cfg.get('extras', []):
        files[extra['file']] = [[n, extra['kind'], state_of(n)] for n in extra['names']]
        for sid in extra['screens']:
            links.setdefault(sid, []).append(extra['file'])

    def git(*a):
        return subprocess.run(['git', '-C', str(repo), *a], capture_output=True, text=True).stdout.strip()
    meta = {'commit': git('rev-parse', '--short', 'HEAD') or 'no git', 'date': git('log', '-1', '--format=%cd', '--date=format:%-d %b %Y'), 'unscreened': len(unscreened)}
    return {'files': files, 'screens': links, 'meta': meta}, missing, unscreened


def check(m, td, missing):
    errors, warns = [], []
    ids = [s['id'] for s in m['screens']]
    known, surfaces = set(ids), {s['id'] for s in m['surfaces']}
    stages = {s['id'] for s in m['stages']}
    scen_ids = [x['id'] for x in m.get('scenarios', [])]
    for label, seq in (('screen', ids), ('scenario', scen_ids)):
        errors += [f'duplicate {label} id {i}' for i, n in Counter(seq).items() if n > 1]
    guide, kinds = m.get('kindGuide', {}), m['kinds']
    if not guide:
        errors.append('kindGuide is empty: the hand-off prompts need at least one test kind')
    for k in guide:
        if k not in kinds:
            errors.append(f'kindGuide names unknown kind {k}')
    for s in m['surfaces']:
        for k in [s.get('kind'), *s.get('kinds', {}).values()]:
            if k and k not in guide:
                errors.append(f"surface {s['id']} suggests {k}, which has no kindGuide entry")
    if m.get('defaultKind') and m['defaultKind'] not in guide:
        errors.append(f"defaultKind {m['defaultKind']} has no kindGuide entry")
    for s in m['screens']:
        if s.get('s') not in surfaces:
            errors.append(f"{s['id']}: unknown surface {s.get('s')}")
        if s.get('c') not in ('ok', 'part', 'none', 'gap'):
            errors.append(f"{s['id']}: c must be ok, part, none or gap")
        for field in ('n', 'w', 'e', 'b'):
            if field not in s:
                errors.append(f"{s['id']}: missing {field}")
        errors += [f"{s['id']}: exit {x} is not a screen" for x in s.get('x', []) if x not in known]
        n = sum(len(td['files'].get(f, [])) for f in td['screens'].get(s['id'], []))
        if s.get('c') in ('none', 'gap') and n:
            warns.append(f"{s['id']} is marked {s['c']} but {n} tests are linked to it")
        if s.get('c') == 'ok' and not n:
            warns.append(f"{s['id']} is marked ok but no test is linked to it")
    for st in m['stages']:
        errors += [f"stage {st['id']}: {x} is not a screen" for x in st.get('sc', []) if x not in known]
    for x in m.get('scenarios', []):
        if x.get('st') not in stages:
            errors.append(f"{x['id']}: unknown stage {x.get('st')}")
        errors += [f"{x['id']}: {i} is not a screen" for i in x.get('sc', []) if i not in known]
        if not x.get('sc'):
            errors.append(f"{x['id']}: crosses no screens")
    for j in m.get('jobs', []):
        if j.get('src') not in ('code', 'people', 'cand'):
            errors.append(f"job {j.get('id')}: src must be code, people or cand")
        if j.get('ev') not in ('none', 'inferred', 'owner', 'user'):
            errors.append(f"job {j.get('id')}: ev must be none, inferred, owner or user")
        if j.get('fit') not in ('built', 'part', 'gap'):
            errors.append(f"job {j.get('id')}: fit must be built, part or gap")
        if len(j.get('stmt', [])) != 3:
            errors.append(f"job {j.get('id')}: stmt needs situation, want and outcome")
        errors += [f"job {j.get('id')}: {i} is not a screen" for i in j.get('sc', []) if i not in known]
    for g in m.get('gaps', []):
        if g.get('sc') not in scen_ids:
            errors.append(f"gap \"{g.get('t')}\" points at unknown scenario {g.get('sc')}")
    file_kinds = {t[1] for v in td['files'].values() for t in v}
    errors += [f'tests have kind {k}, which is not in kinds; add it or a testing.kinds rule' for k in sorted(file_kinds - set(kinds))]
    warns += [f'test file named on the map not found: {x}' for x in missing]
    return errors, warns


DG_BASE = {'fontFamily': 'ui-sans-serif, system-ui, -apple-system, sans-serif', 'fontSize': '14px'}
DG = {
    'light': dict(DG_BASE, background='#fbfaf6', primaryColor='#fbfaf6', primaryTextColor='#090909', primaryBorderColor='#83817d', lineColor='#57534c', actorBkg='#eeeae1', actorBorder='#83817d', actorTextColor='#090909', actorLineColor='#83817d', signalColor='#090909', signalTextColor='#090909', labelBoxBkgColor='#eeeae1', labelBoxBorderColor='#83817d', labelTextColor='#090909', loopTextColor='#090909', noteBkgColor='#e9e2cf', noteBorderColor='#83817d', noteTextColor='#090909', activationBkgColor='#e6e2d9', activationBorderColor='#83817d'),
    'dark': dict(DG_BASE, darkMode=True, background='#1c1b18', primaryColor='#232220', primaryTextColor='#f1eee7', primaryBorderColor='#6d6a64', lineColor='#a8a39a', actorBkg='#232220', actorBorder='#6d6a64', actorTextColor='#f1eee7', actorLineColor='#6d6a64', signalColor='#f1eee7', signalTextColor='#f1eee7', labelBoxBkgColor='#232220', labelBoxBorderColor='#6d6a64', labelTextColor='#f1eee7', loopTextColor='#f1eee7', noteBkgColor='#2e2b23', noteBorderColor='#6d6a64', noteTextColor='#f1eee7', activationBkgColor='#2a2926', activationBorderColor='#6d6a64'),
}
CHROMES = ['/Applications/Google Chrome.app/Contents/MacOS/Google Chrome', '/Applications/Google Chrome Beta.app/Contents/MacOS/Google Chrome Beta', '/usr/bin/chromium', '/usr/bin/google-chrome']


def render_svg(src, theme, cache):
    """Draw one diagram with mmdc, cached by content. Returns SVG text, or None when it can't be drawn."""
    key = hashlib.sha1((src + theme).encode()).hexdigest()[:16]
    out = cache / f'{key}.svg'
    if out.exists():
        return out.read_text()
    if not shutil.which('mmdc'):
        return None
    cache.mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory() as d:
        (Path(d) / 'in.mmd').write_text(src)
        (Path(d) / 'cfg.json').write_text(json.dumps({'theme': 'base', 'themeVariables': DG[theme]}))
        cmd = ['mmdc', '-i', f'{d}/in.mmd', '-o', str(out), '-c', f'{d}/cfg.json', '-b', 'transparent']
        chrome = next((c for c in CHROMES if os.path.exists(c)), None)
        if chrome:
            (Path(d) / 'pp.json').write_text(json.dumps({'executablePath': chrome, 'headless': 'new'}))
            cmd += ['-p', f'{d}/pp.json']
        r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode or not out.exists():
        print('diagram failed:', r.stderr[-300:], file=sys.stderr)
        return None
    return out.read_text()


def namespaced(svg, prefix):
    # Sequence markers share plain ids across diagrams; a reference into a hidden copy draws nothing, so each copy gets its own
    for x in set(re.findall(r'\bid="([^"]+)"', svg)):
        svg = svg.replace(f'id="{x}"', f'id="{prefix}-{x}"').replace(f'url(#{x})', f'url(#{prefix}-{x})').replace(f'href="#{x}"', f'href="#{prefix}-{x}"').replace(f'#{x} ', f'#{prefix}-{x} ').replace(f'#{x}{{', f'#{prefix}-{x}{{')
    return svg


def flows_html(m, cache):
    e, parts, undrawn = html.escape, [], 0
    if m.get('rules'):
        rules = ''.join(f"<div class=\"rule\"><h3>{e(r['t'])}</h3><p>{e(r['d'])}</p></div>" for r in m['rules'])
        parts.append(f'<section style="display:flex;flex-direction:column;gap:10px"><h2>Rules every screen must keep</h2><div class="rules">{rules}</div></section>')
    if m.get('layers'):
        rows = ''
        for l in m['layers']:
            items = ''.join(f'<span>{e(i)}</span>' for i in l.get('items', []))
            note = f"<p class=\"muted\">{e(l['note'])}</p>" if l.get('note') else ''
            rows += f"<div class=\"layer\"><h3>{e(l['n'])}</h3><div class=\"lay-body\"><div class=\"lay-items\">{items}</div>{note}</div></div>"
        parts.append(f'<section class="diagram"><h2>Layers</h2><div class="layers">{rows}</div></section>')
    for i, q in enumerate(m.get('sequences', [])):
        copies = {t: render_svg(q['mermaid'], t, cache) for t in DG}
        if all(copies.values()):
            body = ''.join(f'<div class="dg dg-{t}">{namespaced(s, f"dg{i}{t}")}</div>' for t, s in copies.items())
        else:
            undrawn += 1
            body = f"<pre class=\"prompt\">{e(q['mermaid'])}</pre>"
        parts.append(f"<section class=\"diagram\"><h2>{e(q['t'])}</h2>{body}</section>")
    return '\n'.join(parts), undrawn


def json_tag(tag_id, data):
    # Project text may hold anything: with no literal < it can't close the tag or trip the parser's comment handling
    text = json.dumps(data, separators=(',', ':'), ensure_ascii=False).replace('<', '\\u003c')
    return f'<script type="application/json" id="{tag_id}">{text}</script>'


def build(m, td, out, cache):
    p = m['project']
    flows, undrawn = flows_html(m, cache)
    page_data = {k: v for k, v in m.items() if k not in ('layers', 'rules', 'sequences')}
    page_data['hasFlows'] = bool(flows)
    kind_css = ''.join(f'.k-{k}{{background:var(--kc{i % 7})}}' for i, k in enumerate(m['kinds']))
    page = (ASSETS / 'template.html').read_text()
    fills = {'{{TITLE}}': html.escape(f"{p['name']} App Map"), '{{H1}}': html.escape(f"{p['name']} app map"),
             '{{SUB}}': html.escape(p.get('sub', f"Every screen in {p['name']}, the scenarios that cross it and the tests that cover it")),
             '{{KIND_CSS}}': kind_css, '{{FLOWS}}': flows, '{{FOOTER}}': html.escape(p.get('footer', '')),
             '{{DATA}}': json_tag('mapdata', page_data) + '\n' + json_tag('testdata', td), '{{ENGINE}}': (ASSETS / 'engine.js').read_text()}
    # One pass, so a placeholder inside project data stays plain text
    page = re.sub('|'.join(re.escape(k) for k in fills), lambda x: fills[x.group(0)], page)
    out.write_text(page)
    return undrawn


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('map')
    ap.add_argument('--repo', default='.')
    ap.add_argument('--out')
    ap.add_argument('--check-only', action='store_true')
    a = ap.parse_args()
    map_path, repo = Path(a.map).resolve(), Path(a.repo).resolve()
    m = json.loads(map_path.read_text())
    td, missing, unscreened = read_tests(repo, m)
    errors, warns = check(m, td, missing)
    tests = [t for v in td['files'].values() for t in v]
    print(f"{len(m['screens'])} screens, {len(m.get('scenarios', []))} scenarios, {len(m.get('jobs', []))} jobs, {len(tests)} tests in {len(td['files'])} files, {len(unscreened)} files outside the map")
    print('kinds', dict(Counter(t[1] for t in tests)), 'states', dict(Counter(t[2] for t in tests)))
    for w in warns:
        print('warning:', w)
    for e in errors:
        print('error:', e)
    if errors:
        sys.exit(1)
    if a.check_only:
        return
    out = Path(a.out).resolve() if a.out else map_path.with_name('app-map.html')
    undrawn = build(m, td, out, map_path.parent / '.app-map-cache')
    if undrawn:
        print(f'warning: {undrawn} sequence diagrams show as source; install @mermaid-js/mermaid-cli (mmdc) to draw them')
    print('wrote', out)


if __name__ == '__main__':
    main()
