#!/usr/bin/env python3
"""Reflection / self-improvement: turn what happened in a run into proposed lessons.

    reflect.py [PROJECT] [--all] [--peek]

Reads PROJECT/.promo-reels/runlog.jsonl (written by every script; PROJECT defaults to the
current folder) — by default only events since the last reflection — and prints:
  1. what ran (scripts, crashes, builds, verify results, mixes, environment)
  2. signals the scripts logged (errors, warnings, fixes, new scenarios), grouped
  3. hand fixes: shots that changed between consecutive builds of the same EDL
  4. draft `learn.py add` commands — drafts, to be generalised and confirmed by the user
  5. questions only the conversation can answer (corrections, preferences, praise)
It also saves the report to PROJECT/.promo-reels/reflection-<time>.md and marks the log, so the
next reflection starts after this one (--peek: don't mark). --all: the whole log.
Nothing is written to the skill's references here — that happens only via learn.py after a yes.
"""
import argparse, collections, datetime, json, pathlib, re, shlex, sys

SKILL = pathlib.Path(__file__).resolve().parent.parent
REFS = SKILL / 'references'


def load(log, everything):
    ev = [json.loads(l) for l in log.read_text(encoding='utf-8').splitlines() if l.strip()]
    if not everything:
        last = max((i for i, e in enumerate(ev) if e.get('event') == 'reflect'), default=-1)
        ev = ev[last + 1:]
    return ev


def already_known(what):
    tag = f'(signal: {what})'
    return any(tag in p.read_text(encoding='utf-8') for p in REFS.glob('*.md'))


def shot_key(s):
    return s.get('slide') or f"{s.get('src')}"


def hand_fixes(builds):
    """Diff consecutive builds of the same EDL → list of human-readable changes."""
    out = []
    by_edl = collections.defaultdict(list)
    for b in builds:
        by_edl[b['edl']].append(b)
    for edl, bs in by_edl.items():
        for prev, cur in zip(bs, bs[1:]):
            p, c = prev['shots'], cur['shots']
            if len(p) != len(c):
                out.append({'edl': edl, 'change': f'shot list {len(p)} → {len(c)} shots', 'kind': 'pacing'})
                continue
            for i, (a, b) in enumerate(zip(p, c), 1):
                diffs = [f'{k} {a.get(k)} → {b.get(k)}' for k in ('src', 'in', 'zoom', 'c', 'move', 'dur', 'beats', 'caption', 'slide')
                         if a.get(k) != b.get(k)]
                if diffs:
                    kind = 'pacing' if all(d.startswith(('dur', 'beats')) for d in diffs) else 'video'
                    out.append({'edl': edl, 'shot': i, 'note': b.get('note', ''), 'change': '; '.join(diffs), 'kind': kind})
            if prev.get('xfade') != cur.get('xfade'):
                out.append({'edl': edl, 'change': f"xfade {prev.get('xfade')} → {cur.get('xfade')}", 'kind': 'pacing'})
    return out


def draft(topic, kind, rule, evidence, what):
    ev = f'{evidence} (signal: {what})'
    return f'python3 {SKILL}/scripts/learn.py add --topic {topic} --kind {kind} --rule {shlex.quote(rule)} --evidence {shlex.quote(ev)}'


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('project', nargs='?', default='.')
    ap.add_argument('--all', action='store_true'); ap.add_argument('--peek', action='store_true')
    a = ap.parse_args()
    proj = pathlib.Path(a.project).resolve(); log = proj / '.promo-reels' / 'runlog.jsonl'
    if not log.exists():
        sys.exit(f'no run log at {log} — run the scripts from the project folder (or set PROMO_REELS_PROJECT), '
                 'then reflect. You can still reflect from the conversation: answer section 5 below by hand.')
    ev = load(log, a.all)
    if not ev:
        sys.exit('nothing logged since the last reflection — `reflect.py --all` for the whole log, '
                 'or reflect from the conversation (section 5 questions) if the work happened outside the scripts')
    L = []; p = L.append

    # 1. what ran
    p('# Reflection — promo-reels run\n')
    starts = collections.Counter(e['script'] for e in ev if e['event'] == 'start')
    crashes = [e for e in ev if e['event'] == 'crash']
    fails = [e for e in ev if e['event'] == 'exit' and e.get('code')]
    builds = [e for e in ev if e['event'] == 'build']
    verifies = [e for e in ev if e['event'] == 'verify']
    mixes = [e for e in ev if e['event'] == 'mix']
    env = next((e for e in reversed(ev) if e['event'] == 'start'), {})
    doctor = next((e for e in reversed(ev) if e['event'] == 'doctor'), None)
    p('## 1. What ran')
    p(f"- events: {len(ev)} ({'whole log' if a.all else 'since last reflection'}); platform {env.get('platform', '?')}, python {env.get('python', '?')}")
    p('- scripts: ' + (', '.join(f'{k}×{v}' for k, v in starts.most_common()) or 'none'))
    if not doctor:
        p('- doctor.py was not run this time — environment problems may be unlogged')
    elif not doctor.get('core'):
        p(f"- doctor: core pipeline NOT available (ffmpeg missing {doctor.get('ffmpeg_missing')}, chrome {doctor.get('chrome')})")
    for e in crashes:
        p(f"- CRASH {e['script']}: {e['error']}  at {e.get('where', '')}")
    for e in fails:
        p(f"- exit {e['code']} {e['script']}" + (f": {e['message']}" if e.get('message') else ' (see its signals below)'))
    for b in builds:
        p(f"- build {b['name']}: {b['total']}s, {b['cuts']} cuts, xfade {b['xfade']}")
    for v in verifies:
        p(f"- verify {v['edl']}: {'OK' if not v['bad'] else str(v['bad']) + ' problems'}, blur flags {v['blur_flags']}, sheet {v['sheet']}")
    for m in mixes:
        p(f"- mix {m['video']} + {m['track']}: {m['lufs']} LUFS")
    if builds and not verifies:
        p('- ⚠ built but never verified — run verify.py before delivering')

    # 2. signals
    sig = [e for e in ev if e['event'] == 'signal']
    groups = collections.OrderedDict()
    for s in sig:
        groups.setdefault((s['topic'], s['kind'], s['what']), []).append(s)
    p('\n## 2. Signals from the scripts')
    if not groups:
        p('- none')
    for (topic, kind, what), items in groups.items():
        extra = {k: v for k, v in items[-1].items() if k not in ('ts', 'script', 'event', 'kind', 'topic', 'what')}
        known = ' — already in references' if already_known(what) else ''
        p(f'- [{topic} · {kind}] {what} ×{len(items)}{known}  {json.dumps(extra, ensure_ascii=False)[:300]}')

    # 3. hand fixes
    fixes = hand_fixes(builds)
    p('\n## 3. Hand fixes between builds')
    if not fixes:
        p('- none detected' + (' (only one build)' if len(builds) < 2 else ''))
    for f in fixes:
        p(f"- {f['edl']}" + (f" shot {f['shot']} ({f['note']})" if 'shot' in f else '') + f": {f['change']}")

    # 4. drafts
    drafts = []
    learn_kind = {'error': 'error', 'warning': 'error', 'fix': 'error', 'scenario': 'scenario', 'metric': 'feedback'}
    for (topic, kind, what), items in groups.items():
        if already_known(what):
            continue
        last = items[-1]
        if what == 'slide audit issue':
            rule = f"<generalise> {last.get('type')} copy failed the fit audit ({'; '.join(last.get('issues', []))[:80]}) — write it shorter before rendering"
        elif what == 'low-sharpness shots':
            rule = '<generalise> which moments render soft (fast gestures, zoom ≥ 1.7 on 720p) and how to pick instead'
        else:
            rule = f'<generalise> what to do next time when: {what}'
        drafts.append(draft(topic, learn_kind.get(kind, 'error'), rule, f'{len(items)}× in a run', what))
    for f in fixes:
        what = f"hand fix: {f['change'].split(' ')[0]}"
        rule = (f"<generalise> why shot '{f.get('note', '')}' needed {f['change']} — and how to spot it before building"
                if 'shot' in f else f"<generalise> why the edit needed {f['change']}")
        drafts.append(draft(f['kind'], 'error', rule, f"{f['edl']}: {f['change']}", what))
    p('\n## 4. Draft lessons (rewrite <generalise> into a rule for next time; drop what is one-off)')
    p('```bash'); L.extend(drafts or ['# no script signals — see section 5']); p('```')

    # 5. conversation
    p('\n## 5. Answer from the conversation (the scripts cannot see these)')
    for q in ('Did the user correct, reject or redo anything? (copy, pacing, framing, music, captions) → kind feedback',
              'Did the user state a taste or default likely to repeat? (number of reels, slide order, tone, music mode) → topic preference',
              'Was any input or request new for this skill? (format, language, platform, CTA type, licensed track) → kind scenario',
              'Did you do anything by hand or work around a script, that no signal above shows? → kind error + propose a script fix',
              'Did the user praise something? Keep it as a rule so it survives → kind feedback',
              'Which reference was wrong or missing when you needed it?'):
        p(f'- {q}')
    p('\n## Next')
    p('Show the user at most 5 proposals as `topic · kind · rule · evidence` and ask which to keep. '
      'Run `learn.py add` only for the confirmed ones. If the skill folder is read-only here, give the user the commands instead. '
      'A lesson repeated ≥ 2 times or a script crash → also propose a change to the script itself.')

    text = '\n'.join(L) + '\n'
    print(text)
    out = proj / '.promo-reels' / f"reflection-{datetime.datetime.now():%Y%m%d-%H%M}.md"
    out.write_text(text, encoding='utf-8'); print(f'→ saved {out}')
    if not a.peek:
        with open(log, 'a', encoding='utf-8') as f:
            f.write(json.dumps({'ts': datetime.datetime.now().isoformat(timespec='seconds'), 'script': 'reflect',
                                'event': 'reflect', 'signals': len(sig), 'fixes': len(fixes)}) + '\n')


if __name__ == '__main__':
    main()
