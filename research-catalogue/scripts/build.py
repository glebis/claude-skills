#!/usr/bin/env python3
"""Build a standalone research catalogue (one HTML file, data and images embedded).

Never publishes. Standard library only.

Project folder (the data) holds:
  catalogue.json        what the collection is: title, nouns, facets, card rows,
                        table columns, detail fields, optional date (any kind),
                        measures (any numbers) and verification blocks
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
RESERVED = {'sort', 'direction', 'view', 'q', 'favorites', 'item', 'call', 'date', 'name'}
DATE_KINDS = {'deadline', 'event', 'published', 'other'}
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
    'list': 'List',
    'thisWeek': 'This week',
    'lastWeek': 'Last week',
    'confirmedSummary': '{n} of {total} confirmed at the original source.',
    'stillOpen': 'Still open:',
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
    'byMeasure': 'By {label}',
    'today': 'Today',
    'and': 'and',
    'more': '{n} more',
    'status': 'Status',
    'verification': 'Verification',
    'checked': 'checked {date}',
    'confidence': '{level} confidence',
    'notChecked': 'not yet checked',
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

# Date wording depends on what the date means. Project "strings" still win.
DATE_STRINGS = {
    'deadline': {
        'dateLabel': 'Deadline', 'timeline': 'Deadline timeline', 'byDate': 'By deadline',
        'next': 'Next to close', 'closed': 'Closed', 'leftToday': 'Closes today', 'leftOne': '1 day left', 'leftMany': '{n} days left',
        'allPast': 'Every deadline in this edition has passed.', 'rangeOne': 'Deadline {date}', 'rangeMany': 'Deadlines {from} – {to}',
    },
    'event': {
        'dateLabel': 'Date', 'timeline': 'Event timeline', 'byDate': 'By date',
        'next': 'Next up', 'closed': 'Past', 'leftToday': 'Today', 'leftOne': 'Tomorrow', 'leftMany': 'In {n} days',
        'allPast': 'Every event in this edition has passed.', 'rangeOne': 'Date {date}', 'rangeMany': 'Dates {from} – {to}',
    },
    'published': {
        'dateLabel': 'Published', 'timeline': 'Publication timeline', 'byDate': 'Newest first',
        'latest': 'Most recent', 'ageFuture': 'Forthcoming', 'ageToday': 'Today', 'ageOne': 'Yesterday', 'ageDays': '{n} days ago',
        'ageMonth': '1 month ago', 'ageMonths': '{n} months ago', 'ageYear': '1 year ago', 'ageYears': '{n} years ago',
        'rangeOne': 'Published {date}', 'rangeMany': 'Published {from} – {to}',
    },
    'other': {
        'dateLabel': 'Date', 'timeline': 'Timeline', 'byDate': 'By date',
        'rangeOne': 'Date {date}', 'rangeMany': 'Dates {from} – {to}',
    },
}

DEFAULT_STATUSES = [
    ['verified', 'Verified', 'ok'],
    ['unverified', 'Unverified', 'warn'],
    ['conflicting', 'Conflicting sources', 'alert'],
    ['outdated', 'Needs re-check', 'warn'],
]


def lower_first(text):
    return text[:1].lower() + text[1:]


def normalise_measures(schema, strings):
    """Turn the legacy single "cost" block into the first measure and fill measure defaults."""
    measures = [dict(m) for m in schema.get('measures', [])]
    if 'cost' in schema:
        c = schema['cost']
        measures.insert(0, {
            'key': 'cost', 'field': c['field'], 'label': c.get('label', 'Price'), 'sortLabel': c.get('sortLabel'),
            'sortChip': strings.get('byCost'), 'format': 'currency', 'currency': c.get('currency', 'EUR'),
            'note': c.get('note'), 'tableNote': c.get('tableNote'), 'approxIf': c.get('approxIf', []),
            'zeroLabel': strings['free'], 'zeroFilter': c.get('freeFilter'), 'zeroKey': 'free', 'detail': c.get('detail'),
        })
    for m in measures:
        m.setdefault('key', m['field'])
        m.setdefault('format', 'number')
        m.setdefault('better', 'low')
        m['sortLabel'] = m.get('sortLabel') or m['label']
        m['sortChip'] = m.get('sortChip') or fill(strings['byMeasure'], {'label': lower_first(m['label'])})
        if m.get('zeroFilter'):
            m.setdefault('zeroKey', m['key'] + '-zero')
        if m['format'] == 'currency' and m.get('zeroLabel') is None:
            m['zeroLabel'] = strings['free']
    keys = [m['key'] for m in measures] + [m['zeroKey'] for m in measures if m.get('zeroFilter')]
    assert len(set(keys)) == len(keys), 'Measure keys must be unique'
    return measures


def normalise_verification(schema, strings):
    v = schema.get('verification')
    if not v:
        return None
    v = {'field': 'status', 'checked': 'checked', 'confidence': 'confidence', 'note': 'verificationNote', 'filter': True, **v}
    values = v.get('values') or DEFAULT_STATUSES
    v['values'] = [list(x) + [''] * (3 - len(x)) for x in values]
    if v['filter']:
        schema.setdefault('facets', []).append({
            'key': 'status', 'field': v['field'], 'label': strings['status'], 'counts': True,
            'options': [[value, label] for value, label, _ in v['values']],
        })
    return v


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
    language = schema.get('language', 'en')
    locale = schema.get('locale') or ('en-GB' if language == 'en' else language)
    date_block = dict(schema['date']) if 'date' in schema else None
    if date_block:
        date_block.setdefault('kind', 'deadline')
        assert date_block['kind'] in DATE_KINDS, f'date.kind must be one of {sorted(DATE_KINDS)}'
    strings = {**DEFAULT_STRINGS, **DATE_STRINGS[date_block['kind'] if date_block else 'other'], **schema.get('strings', {})}
    if date_block:
        date_block.setdefault('label', strings['dateLabel'])
    measures = normalise_measures(schema, strings)
    verification = normalise_verification(schema, strings)

    for item in items:
        item.update(meta.get(item['id'], {}))
        if date_block:
            value = item.get(date_block['field'])
            assert value in (None, '') or ISO.fullmatch(value), f'{item["id"]}: date must be YYYY-MM-DD, got {value!r}'
        for m in measures:
            value = item.get(m['field'])
            assert value is None or isinstance(value, (int, float)), f'{item["id"]}: {m["field"]} must be a number or null, got {value!r}'
        if verification and item.get(verification['checked']):
            assert ISO.fullmatch(item[verification['checked']]), f'{item["id"]}: checked date must be YYYY-MM-DD'

    taken = {m['key'] for m in measures} | {m['zeroKey'] for m in measures if m.get('zeroFilter')} | {s['key'] for s in schema.get('sorts', [])}
    for facet in schema.get('facets', []):
        assert facet['key'] not in taken, f'Facet key "{facet["key"]}" clashes with a measure or sort key'
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
        **{k: v for k, v in schema.items() if k not in {'strings', 'dek', 'description', 'title', 'pageTitle', 'cost', 'date', 'measures', 'verification'}},
        'date': date_block,
        'measures': measures,
        'verification': verification,
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
