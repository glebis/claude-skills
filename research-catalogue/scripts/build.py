#!/usr/bin/env python3
"""Build a standalone research catalogue (one HTML file, data and images embedded).

Never publishes. Standard library only.

Project folder (the data) holds:
  catalogue.json        what the collection is: title, nouns, facets, card rows,
                        table columns, detail fields, optional date and cost blocks
  items.json            full researched records (array, each with a stable "id")
  items-meta.json       optional compact display fields keyed by id, merged in
  snapshot.json         {"date", "label", ...} of the last research run
  profile.json          optional selection criteria shown on the page
  assets/manifest.json  optional image metadata; assets/previews/<id>.webp preferred
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
RESERVED = {'sort', 'direction', 'view', 'q', 'free', 'favorites', 'call'}
ISO = re.compile(r'\d{4}-\d{2}-\d{2}')

# Interface copy. A project overrides any of these under "strings" in catalogue.json.
DEFAULT_STRINGS = {
    'skip': 'Skip to results',
    'timeline': 'Date timeline',
    'filtersLabel': 'Catalogue filters',
    'filters': 'Filters & sorting',
    'search': 'Search',
    'searchPlaceholder': 'Name, place or keyword',
    'favourites': 'Favourites',
    'all': 'All',
    'order': 'Order',
    'byDate': 'By date',
    'byCost': 'By price',
    'byName': 'By name',
    'criteria': 'Selection criteria',
    'viewLabel': 'Catalogue view',
    'cards': 'Cards',
    'table': 'Table',
    'reset': 'Reset filters',
    'download': 'Download HTML',
    'print': 'Print',
    'tableRegion': 'Comparison table; scroll right if needed',
    'nameColumn': 'Name',
    'close': 'Close',
    'researched': 'Full details as researched on {date}',
    'count': '{n} of {total} {noun}',
    'active': '{n} active',
    'noMatches': 'No matching {noun}',
    'emptyEdition': 'No {noun} in this edition yet',
    'emptyMessage': 'Entries will appear after the research is updated.',
    'details': 'Full details & sources',
    'detailsShort': 'Details',
    'source': 'Official page →',
    'addFavourite': 'Add to favourites',
    'removeFavourite': 'Remove from favourites',
    'imageAndDetails': 'Image and details',
    'noImage': 'No image confirmed',
    'noImageLong': 'No official image has been confirmed.',
    'imageFailed': 'Image could not load · source in details',
    'credit': 'Credit',
    'creatorCredit': 'Creator / credit',
    'imageSource': 'Official image source',
    'free': 'Free',
    'closed': 'Closed',
    'leftToday': 'Closes today',
    'leftOne': '1 day left',
    'leftMany': '{n} days left',
    'today': 'Today',
    'next': 'Next to close',
    'and': 'and',
    'more': '{n} more',
    'allPast': 'Every date in this edition has passed.',
    'rangeOne': 'Date {date}',
    'rangeMany': 'Dates {from} – {to}',
    'sortAsc': 'sort ascending',
    'sortedAsc': 'ascending; switch to descending',
    'sortedDesc': 'descending; switch to ascending',
    'ascending': 'ascending',
    'descending': 'descending',
    'themeDark': 'Switch to dark theme',
    'themeLight': 'Switch to light theme',
    'snapshot': 'Snapshot: {date}.',
}
DEFAULT_FIELDS = {'name': 'name', 'short': 'short', 'subtitle': 'place', 'url': 'url', 'sources': 'extra'}


def default_project():
    # A copy of build.py that sits inside a project folder builds that project.
    if (SCRIPT_DIR / 'catalogue.json').exists():
        return SCRIPT_DIR
    return Path.cwd()


def read_json(path, default=None):
    if path.exists():
        return json.loads(path.read_text())
    if default is None:
        raise SystemExit(f'Missing {path}')
    return default


def first_existing(root, *names):
    for name in names:
        if (root / name).exists():
            return root / name
    return root / names[0]


def inline_md(text):
    """Escape text, then turn **bold** into <b>bold</b>."""
    return re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', html.escape(text, quote=False))


def fill(text, values):
    return re.sub(r'\{(\w+)\}', lambda m: str(values.get(m.group(1), m.group(0))), text)


def long_date(iso, locale):
    d = date.fromisoformat(iso)
    return f'{d.day} {d:%B %Y}' if locale.startswith('en') else iso


def as_list(value):
    if isinstance(value, list):
        return value
    return [] if value in (None, '') else [value]


def resolve_facets(schema, items):
    """Give every item a list under each facet key and every facet a full option list."""
    for facet in schema.get('facets', []):
        key = facet['key']
        assert key not in RESERVED, f'Facet key "{key}" is reserved for page state'
        field = facet.get('field', key)
        allowed, other = facet.get('values'), facet.get('other')
        for item in items:
            values = as_list(item.get(field))
            if allowed is not None:
                values = [v if v in allowed else other for v in values] or ([other] if other else [])
                values = [v for v in dict.fromkeys(values) if v]
            item[key] = values
        if 'options' in facet:
            facet['options'] = [o if isinstance(o, list) else [o, o] for o in facet['options']]
        elif allowed is not None:
            facet['options'] = [[v, v] for v in allowed + ([other] if other and other not in allowed else [])]
        else:
            seen = dict.fromkeys(v for item in items for v in item[key])
            facet['options'] = [[v, v] for v in seen]


def attach_images(root, items, manifest):
    by_id = {a['id']: a for a in manifest}
    for item in items:
        a = dict(by_id.get(item['id'], {}))
        src = None
        preview = root / 'assets' / 'previews' / (item['id'] + '.webp')
        local = root / a['local_path'] if a.get('local_path') else None
        image_path = preview if preview.exists() else local
        if image_path and image_path.exists():
            mime = 'image/webp' if image_path.suffix == '.webp' else a.get('mime', 'image/jpeg')
            src = 'data:' + mime + ';base64,' + base64.b64encode(image_path.read_bytes()).decode()
        a['src'] = src or a.get('image_url')
        item['image'] = {k: a.get(k) for k in ['src', 'source_url', 'type', 'caption', 'credit']}
        item['image']['shortCredit'] = a.get('short_credit')


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument('--project', type=Path, default=None, help='Project folder with catalogue.json (default: this folder or the current one).')
    parser.add_argument('--output', type=Path, help='Write the HTML here instead of <project>/dist/index.html.')
    parser.add_argument('--template', type=Path, help='Template to use (default: <project>/template.html, else the skill template).')
    args = parser.parse_args()

    root = (args.project or default_project()).expanduser().resolve()
    output = args.output.expanduser().resolve() if args.output else root / 'dist' / 'index.html'
    if output.suffix.lower() not in {'.html', '.htm'}:
        parser.error('--output must name an .html or .htm file')
    template_path = args.template or (root / 'template.html' if (root / 'template.html').exists() else SKILL_TEMPLATE)

    schema = read_json(root / 'catalogue.json')
    items = read_json(first_existing(root, 'items.json', 'calls.json'))
    meta = read_json(first_existing(root, 'items-meta.json', 'catalog-meta.json'), {})
    snapshot = read_json(root / 'snapshot.json')
    profile = read_json(root / 'profile.json', {})
    manifest_path = root / 'assets' / 'manifest.json'
    manifest = read_json(manifest_path, [])

    ids = [i['id'] for i in items]
    assert len(set(ids)) == len(ids), 'Duplicate item id'
    if meta:
        assert set(meta) == set(ids), 'items-meta.json ids must match items.json ids'
    for item in items:
        item.update(meta.get(item['id'], {}))
        if 'date' in schema:
            value = item.get(schema['date']['field'])
            assert value in (None, '') or ISO.fullmatch(value), f'{item["id"]}: date must be YYYY-MM-DD, got {value!r}'
        if 'cost' in schema:
            value = item.get(schema['cost']['field'])
            assert value is None or isinstance(value, (int, float)), f'{item["id"]}: cost must be a number, got {value!r}'

    language = schema.get('language', 'en')
    locale = schema.get('locale') or ('en-GB' if language == 'en' else language)
    strings = {**DEFAULT_STRINGS, **schema.get('strings', {})}
    resolve_facets(schema, items)
    images = schema.get('images', manifest_path.exists())
    if images:
        attach_images(root, items, manifest)

    snapshot_long = long_date(snapshot['date'], locale)
    tokens = {'snapshot': snapshot.get('label', snapshot_long)}
    for key, value in snapshot.items():
        if isinstance(value, str) and ISO.fullmatch(value):
            tokens[key] = long_date(value, locale)
    if 'minimumDeadline' in tokens:
        tokens.setdefault('minDeadline', tokens['minimumDeadline'])

    criteria = profile.get('criteria', [])
    criteria_block = ''
    if criteria:
        label = html.escape(strings['criteria'])
        spans = ''.join('<span>' + inline_md(fill(line, tokens)) + '</span>' for line in criteria)
        criteria_block = f'<details class="selection-criteria"><summary>{label}</summary><section class="criteria" aria-label="{label}">{spans}</section></details>'

    title = schema.get('title', {})
    title_html = html.escape(title.get('lead', '')) + (f' <em>{html.escape(title["accent"])}</em>' if title.get('accent') else '')
    description = ' '.join(filter(None, [schema.get('description', ''), fill(strings['snapshot'], {'date': tokens['snapshot']})]))
    page_title = schema.get('pageTitle') or ' '.join(filter(None, [title.get('lead'), title.get('accent')])) or 'Research catalogue'

    page_schema = {
        **{k: v for k, v in schema.items() if k not in {'strings', 'dek', 'description', 'title', 'pageTitle'}},
        'fields': {**DEFAULT_FIELDS, **schema.get('fields', {})},
        'noun': schema.get('noun', {'one': 'entry', 'many': 'entries'}),
        'storageKey': schema.get('storageKey', 'research-catalogue'),
        'locale': locale,
        'images': images,
        'strings': strings,
        'snapshot': {'date': snapshot['date'], 'label': tokens['snapshot']},
    }

    def script_json(value):
        return json.dumps(value, ensure_ascii=False, separators=(',', ':')).replace('</', '<\\/')

    replacements = {
        '__LANG__': html.escape(language),
        '__PAGE_TITLE__': html.escape(page_title),
        '__DESCRIPTION__': html.escape(description),
        '__TITLE_HTML__': title_html,
        '__DEK__': inline_md(fill(schema.get('dek', ''), tokens)),
        '__CRITERIA_BLOCK__': criteria_block,
        '__RESEARCHED_NOTE__': html.escape(fill(strings['researched'], {'date': snapshot_long})),
        '__SCHEMA__': script_json(page_schema),
        '__ITEM_DATA__': script_json(items),
    }
    page = template_path.read_text()
    page = re.sub(r'\{\{s:(\w+)\}\}', lambda m: html.escape(strings[m.group(1)]), page)
    for key, value in replacements.items():
        page = page.replace(key, value)
    leftover = sorted(set(re.findall(r'__[A-Z_]{4,}__|\{\{s:\w+\}\}', page)))
    assert not leftover, f'Unresolved placeholders: {leftover}'

    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(page, encoding='utf-8')
    embedded = sum(str((i.get('image') or {}).get('src') or '').startswith('data:') for i in items)
    print(json.dumps({'output': str(output), 'template': str(template_path), 'items': len(items), 'embedded_images': embedded, 'html_bytes': len(page.encode())}))


if __name__ == '__main__':
    main()
