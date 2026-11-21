#!/usr/bin/env python3
"""Build a standalone photography open-call catalogue (one HTML file, images embedded).

Never publishes. Standard library only.

Project folder (the data) holds:
  calls.json            full researched records
  catalog-meta.json     compact display fields, keyed by stable record id
  snapshot.json         {"date", "label", "minimumDeadline"}
  profile.json          selection criteria shown on the page and the region list
  assets/manifest.json  image metadata; assets/previews/<id>.webp preferred
  template.html         optional; overrides the skill's assets/template.html

Usage:
  python3 build.py --project /path/to/project --output /abs/path/catalogue.html
"""
import argparse
import base64
import html
import json
import re
from datetime import date
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
SKILL_TEMPLATE = SCRIPT_DIR.parent / 'assets' / 'template.html'


def default_project():
    # A copy of build.py that sits inside a project folder builds that project.
    if (SCRIPT_DIR / 'calls.json').exists():
        return SCRIPT_DIR
    return Path.cwd()


def inline_md(text):
    """Escape text, then turn **bold** into <b>bold</b>."""
    return re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', html.escape(text, quote=False))


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument('--project', type=Path, default=None, help='Project folder with calls.json (default: this folder or the current one).')
    parser.add_argument('--output', type=Path, help='Write the HTML here instead of <project>/dist/index.html.')
    parser.add_argument('--template', type=Path, help='Template to use (default: <project>/template.html, else the skill template).')
    args = parser.parse_args()

    root = (args.project or default_project()).expanduser().resolve()
    output = args.output.expanduser().resolve() if args.output else root / 'dist' / 'index.html'
    if output.suffix.lower() not in {'.html', '.htm'}:
        parser.error('--output must name an .html or .htm file')
    template_path = args.template or (root / 'template.html' if (root / 'template.html').exists() else SKILL_TEMPLATE)

    calls = json.loads((root / 'calls.json').read_text())
    meta = json.loads((root / 'catalog-meta.json').read_text())
    snapshot = json.loads((root / 'snapshot.json').read_text())
    profile_path = root / 'profile.json'
    profile = json.loads(profile_path.read_text()) if profile_path.exists() else {}
    manifest_path = root / 'assets' / 'manifest.json'
    assets = json.loads(manifest_path.read_text()) if manifest_path.exists() else []
    asset_map = {a['id']: a for a in assets}

    ids = [c['id'] for c in calls]
    assert len(set(ids)) == len(ids), 'Duplicate call id'
    assert set(meta) == set(ids), 'catalog-meta.json ids must match calls.json ids'

    regions = [r for r in profile.get('regions', []) if r != 'Other countries'] + ['Other countries']
    for c in calls:
        c.update(meta[c['id']])
        if isinstance(c['formats'], str):
            c['formats'] = [c['formats']]
        c['region'] = c.get('group') if c.get('group') in regions else 'Other countries'
        a = dict(asset_map.get(c['id'], {}))
        src = None
        if a.get('local_path'):
            preview = root / 'assets' / 'previews' / (c['id'] + '.webp')
            image_path = preview if preview.exists() else root / a['local_path']
            if image_path.exists():
                mime = 'image/webp' if image_path.suffix == '.webp' else a.get('mime', 'image/jpeg')
                src = 'data:' + mime + ';base64,' + base64.b64encode(image_path.read_bytes()).decode()
        a['src'] = src or a.get('image_url')
        c['image'] = {k: a.get(k) for k in ['src', 'source_url', 'type', 'caption', 'credit', 'image_url']}
        c['image']['shortCredit'] = a.get('short_credit') or '—'

    def long_date(iso):
        d = date.fromisoformat(iso)
        return f'{d.day} {d:%B %Y}'

    min_deadline = long_date(snapshot['minimumDeadline'])
    criteria = profile.get('criteria', [])
    criteria_html = ''.join('<span>' + inline_md(item.replace('{minDeadline}', min_deadline)) + '</span>' for item in criteria)

    template = template_path.read_text()
    payload = json.dumps(calls, ensure_ascii=False, separators=(',', ':')).replace('</', '<\\/')
    replacements = {
        '__CALL_DATA__': payload,
        '__REGIONS__': json.dumps(regions, ensure_ascii=False),
        '__CRITERIA_HTML__': criteria_html,
        '__COUNT__': str(len(calls)),
        '__SNAPSHOT_ISO__': snapshot['date'],
        '__SNAPSHOT_LABEL__': snapshot['label'],
        '__SNAPSHOT_DATE__': long_date(snapshot['date']),
        '__MIN_DEADLINE__': min_deadline,
    }
    page = template
    for key, value in replacements.items():
        page = page.replace(key, value)
    leftover = sorted(set(re.findall(r'__[A-Z_]{4,}__', page)) - {'__SNAPSHOT_ISO__'})
    assert not leftover, f'Unresolved placeholders: {leftover}'

    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(page, encoding='utf-8')
    embedded = sum(bool(c['image'].get('src') and c['image']['src'].startswith('data:')) for c in calls)
    print(json.dumps({'output': str(output), 'template': str(template_path), 'calls': len(calls), 'embedded_images': embedded, 'html_bytes': len(page.encode())}))


if __name__ == '__main__':
    main()
