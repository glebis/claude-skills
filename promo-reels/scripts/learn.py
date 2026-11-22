#!/usr/bin/env python3
"""Grow the skill's references from real use.

    learn.py add --topic TOPIC --kind KIND --rule "what to do next time" \
                 --evidence "what happened" [--date YYYY-MM-DD]
    learn.py list [--topic TOPIC] [--last 20]
    learn.py topics

Appends a dated entry to references/<topic>.md under "## Learned in use" and indexes it
in references/learning-log.md. Kinds: error (something broke / a workaround was needed),
feedback (the user corrected or judged a result), scenario (a new input type, format or
use case), preference (the user's taste — goes to preferences.md).

The repo is public: entries must be generic. Paths under a home directory, e-mail
addresses, phone numbers and URLs with query strings are refused — rephrase them.
"""
import argparse, datetime, pathlib, re, sys

REF = pathlib.Path(__file__).resolve().parent.parent / 'references'
TOPICS = {
    'pacing': 'pacing.md', 'copy': 'copy.md', 'music': 'music.md', 'slides': 'copy.md',
    'video': 'lessons.md', 'audio': 'lessons.md', 'tooling': 'lessons.md', 'intake': 'preferences.md',
    'preference': 'preferences.md', 'delivery': 'preferences.md', 'style': 'style.md',
}
KINDS = ('error', 'feedback', 'scenario', 'preference')
PRIVATE = [
    (r'/Users/[^/\s]+|/home/[^/\s]+|~/', 'home-directory path'),
    (r'[\w.+-]+@[\w-]+\.[\w.]+', 'e-mail address'),
    (r'\+?\d[\d\s()-]{8,}\d', 'phone-like number'),
    (r'https?://\S+\?\S+', 'URL with query string'),
]
HEAD = '## Learned in use'


def check_draft(rule):
    if '<generalise>' in (rule or ''):
        sys.exit('refused: the rule is still a reflect.py draft — rewrite <generalise> into a concrete rule for next time')


def check_private(*texts):
    for t in texts:
        for pat, what in PRIVATE:
            if re.search(pat, t or ''):
                sys.exit(f'refused: contains a {what} — references are public, rephrase generically')


def add(a):
    if a.topic not in TOPICS:
        sys.exit(f'unknown topic; use one of: {", ".join(sorted(TOPICS))}')
    check_draft(a.rule); check_private(a.rule, a.evidence)
    f = REF / ('preferences.md' if a.kind == 'preference' else TOPICS[a.topic])
    text = f.read_text() if f.exists() else f'# {f.stem.capitalize()}\n'
    if HEAD not in text:
        text = text.rstrip() + f'\n\n{HEAD}\n<!-- appended by scripts/learn.py — newest last -->\n'
    date = a.date or datetime.date.today().isoformat()
    entry = f'\n- **{date} · {a.kind}** — {a.rule.strip()}\n  _Evidence:_ {a.evidence.strip()}\n'
    if a.rule.strip() in text:
        print('already recorded'); return
    f.write_text(text.rstrip() + '\n' + entry)
    log = REF / 'learning-log.md'
    lt = log.read_text() if log.exists() else '# Learning log\n\nIndex of lessons added by `scripts/learn.py`.\n\n| date | kind | topic | file | rule |\n|---|---|---|---|---|\n'
    short = a.rule.strip().replace('|', '/')[:110]
    log.write_text(lt.rstrip() + f'\n| {date} | {a.kind} | {a.topic} | {f.name} | {short} |\n')
    print(f'+ {f.name}: {short}')


def lst(a):
    log = REF / 'learning-log.md'
    if not log.exists():
        print('no lessons yet'); return
    rows = [l for l in log.read_text().splitlines() if l.startswith('| 2')]
    if a.topic:
        rows = [r for r in rows if f'| {a.topic} |' in r]
    print('\n'.join(rows[-a.last:]))


if __name__ == '__main__':
    ap = argparse.ArgumentParser(); sp = ap.add_subparsers(dest='cmd', required=True)
    p = sp.add_parser('add'); p.add_argument('--topic', required=True); p.add_argument('--kind', required=True, choices=KINDS)
    p.add_argument('--rule', required=True); p.add_argument('--evidence', required=True); p.add_argument('--date'); p.set_defaults(fn=add)
    p = sp.add_parser('list'); p.add_argument('--topic'); p.add_argument('--last', type=int, default=20); p.set_defaults(fn=lst)
    p = sp.add_parser('topics'); p.set_defaults(fn=lambda a: print('\n'.join(f'{k:11} → {v}' for k, v in TOPICS.items())))
    a = ap.parse_args(); a.fn(a)
