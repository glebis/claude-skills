#!/usr/bin/env python3
"""Render text slides (1080x1920 PNG) with headless Chrome and audit the text fit.

    slides.py SLIDES.json --out DIR [--style NAME|style.json] [--lang ru] [--force]

Style: --style (preset name or a style JSON), else style.json next to SLIDES.json, else doc-red.
Tokens and presets: scripts/tokens.py, assets/slides/themes/, references/style.md.

SLIDES.json is a list of slides; each has "name" and "type" (hook | cta | caption):
  hook:    lines[≤10 chars each], title, date, venue, action, bg_text (optional texture)
  cta:     kicker, title, date_big, action
  caption: text (≤60 chars), label (optional), max_lines (default 4) — transparent PNG overlay

Per slide: Chrome --dump-dom reads the audit JSON, then --screenshot writes DIR/<name>.png.
Exit code 2 when any slide has issues (REWRITE = copy too long; fix the copy, not the CSS).
--force renders anyway.
"""
import argparse, glob, json, os, pathlib, platform, shutil, subprocess, sys, html, re
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent)); import runlog, tokens  # noqa: E402

HERE = pathlib.Path(__file__).resolve().parent.parent / 'assets' / 'slides'
FONTS = HERE.parent / 'fonts'


def chrome_candidates():
    """$CHROME first, then macOS apps, Linux binaries on PATH, then Playwright's bundled Chromium."""
    yield os.environ.get('CHROME', '')
    yield from ('/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
                '/Applications/Google Chrome Beta.app/Contents/MacOS/Google Chrome Beta',
                '/Applications/Chromium.app/Contents/MacOS/Chromium')
    for name in ('google-chrome', 'google-chrome-stable', 'chromium', 'chromium-browser', 'chrome', 'headless_shell'):
        yield shutil.which(name) or ''
    home = pathlib.Path.home()
    for pat in ('.cache/ms-playwright/chromium*/chrome-linux*/chrome',
                '.cache/ms-playwright/chromium_headless_shell*/chrome-linux*/headless_shell',
                'Library/Caches/ms-playwright/chromium*/chrome-mac*/Chromium.app/Contents/MacOS/Chromium'):
        yield from sorted(glob.glob(str(home / pat)), reverse=True)


def chrome():
    for c in chrome_candidates():
        if c and pathlib.Path(c).exists():
            return c
    sys.exit('Chrome/Chromium not found. Install one (e.g. `pip install playwright && playwright install chromium`) '
             'or set CHROME=/path/to/chrome. Run scripts/doctor.py for a full check.')


def resolve_style(arg, spec):
    """--style wins; else the project's style.json beside the slides spec; else the doc-red preset."""
    if arg:
        return arg
    local = pathlib.Path(spec).resolve().parent / 'style.json'
    return str(local) if local.exists() else 'doc-red'


def render(slides, out, style, lang='ru', force=False, log=True, screenshot=True, quiet=False):
    """Render slide dicts with a style → (number of problems, audit rows). Used by slides.py and style.py."""
    out = pathlib.Path(out).resolve(); out.mkdir(parents=True, exist_ok=True)
    build = out / '_html'; build.mkdir(exist_ok=True)
    for f in ('fit.js', 'audit.js'):
        shutil.copy(HERE / f, build / f)
    theme = tokens.load(style)
    problems = tokens.check(theme)
    if problems:
        if not quiet:
            print('✗ style: ' + '; '.join(problems))
        if log:
            runlog.signal('error', 'style', 'style check failed', style=str(style), issues=problems)
        if not force:
            return len(problems), []
    (build / 'fonts').mkdir(exist_ok=True)
    for f in theme.get('fonts', []):
        shutil.copy(f['path'], build / 'fonts' / pathlib.Path(f['path']).name)
    page_theme, css = tokens.for_page(theme), tokens.css_vars(theme)
    template = (HERE / 'template.html').read_text()
    exe = chrome()
    base = [exe, '--headless=new', '--disable-gpu', '--hide-scrollbars', '--force-device-scale-factor=1',
            '--window-size=1080,1920', '--virtual-time-budget=15000', '--allow-file-access-from-files']
    if platform.system() == 'Linux':  # containers run as root: Chrome refuses to start without these
        base += ['--no-sandbox', '--disable-dev-shm-usage']
    bad, rows = 0, []
    for s in slides:
        # JSON inside <script type=application/json>: only "</" needs escaping
        data = json.dumps({'theme': page_theme, 'vars': css, 'lang': lang, 'slide': s}, ensure_ascii=False).replace('</', '<\\/')
        page = build / f"{s['name']}.html"
        page.write_text(template.replace('__DATA__', data))
        url = page.as_uri()
        dom = subprocess.run([*base, '--dump-dom', url], capture_output=True, text=True).stdout
        m = re.search(r'<pre id="audit-result"[^>]*>(.*?)</pre>', dom, re.S)
        if not m:
            print(f"✗ {s['name']}: audit did not run (fonts or JS failed to load)"); bad += 1
            if log:
                runlog.signal('error', 'tooling', 'slide audit did not run', slide=s['name'], chrome=exe)
            continue
        report = json.loads(html.unescape(m.group(1)))
        rows += report
        issues = [r for r in report if r['issues']]
        for r in report:
            if not r['issues'] and 'font' in r and not quiet:
                print(f"  {s['name']:14} {r['text'][:30]:30} {r['font']:4}px {r['lines']}L")
        for r in issues:
            if not quiet:
                print(f"✗ {s['name']:14} {r['text'][:30]:30} {'; '.join(r['issues'])}")
            bad += 1
            if log:
                runlog.signal('error', 'tooling' if r['text'] == 'FONT' else 'copy', 'slide audit issue', slide=s['name'],
                              type=s['type'], text=r['text'], issues=r['issues'], style=theme.get('name'))
        if (issues and not force) or not screenshot:
            continue
        extra = ['--default-background-color=00000000'] if s['type'] == 'caption' else []
        png = out / f"{s['name']}.png"
        subprocess.run([*base, *extra, f'--screenshot={png}', url], capture_output=True)
        if not quiet:
            print(f"✓ {png}" if png.exists() else f"✗ {s['name']}: screenshot failed")
    return bad, rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('spec')
    ap.add_argument('--out', required=True)
    ap.add_argument('--style', '--theme', dest='style')
    ap.add_argument('--lang', default='ru', help='hyphenation/locale of the copy')
    ap.add_argument('--force', action='store_true')
    a = ap.parse_args()
    runlog.init(pathlib.Path(a.spec).resolve().parent)
    style = resolve_style(a.style, a.spec)
    print(f'style: {style}')
    bad, _ = render(json.loads(pathlib.Path(a.spec).read_text()), a.out, style, a.lang, a.force)
    sys.exit(2 if bad and not a.force else 0)


if __name__ == '__main__':
    main()
