#!/usr/bin/env python3
"""Read this project's Beads and optionally refresh date/context projections.

Never opens monitored sources, initializes Beads, or mutates task records.
"""
import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import subprocess
import sys
from zoneinfo import ZoneInfo


def read_issues(project, ready=False):
    args = ['bd', '-C', str(project), '--sandbox', '--readonly', '--json',
            'list', '--limit', '0', '--ready' if ready else '--all']
    env = dict(os.environ, BEADS_DIR=str(project / '.beads'))
    proc = subprocess.run(args, env=env, text=True, capture_output=True, timeout=60)
    if proc.returncode:
        raise RuntimeError(proc.stderr.strip() or 'Beads read failed')
    rows = json.loads(proc.stdout)
    if not isinstance(rows, list):
        raise ValueError('Expected a Beads issue list')
    return rows


def meta(row):
    value = row.get('metadata') or {}
    if isinstance(value, str):
        value = json.loads(value)
    if not isinstance(value, dict):
        raise ValueError('Invalid metadata on ' + row['id'])
    return value


def created(row):
    value = row.get('created_at')
    if not value:
        raise ValueError('Missing created_at on ' + row['id'])
    stamp = datetime.fromisoformat(value.replace('Z', '+00:00'))
    if stamp.tzinfo is None:
        raise ValueError('Timezone missing on ' + row['id'])
    return stamp.astimezone(timezone.utc), row['id']


def context(row):
    return meta(row).get('primary_context') or 'unclassified'


def sanitize(row):
    fields = ('id', 'title', 'issue_type', 'status', 'assignee', 'priority', 'created_at',
              'updated_at', 'closed_at', 'parent', 'labels', 'dependencies')
    out = {key: row[key] for key in fields if key in row}
    # Keep the fields needed to classify/trace proposals, not arbitrary private metadata.
    fields = ('proposal_key', 'primary_context', 'contexts', 'source_systems',
              'evidence_refs', 'evidence_window', 'review_state')
    out['metadata'] = {key: meta(row)[key] for key in fields if key in meta(row)}
    return out


def cell(value):
    return str(value).replace('|', '\\|').replace('\n', ' ')


def table(rows, ready_ids):
    lines = ['| Created (Europe/Berlin) | ID | Type | Status | Context | Title |',
             '|---|---|---|---|---|---|']
    for row in rows:
        stamp = created(row)[0].astimezone(ZoneInfo('Europe/Berlin')).isoformat(timespec='seconds')
        status = row['status']
        if status == 'open' and row['id'] not in ready_ids:
            status += ' (not ready; inspect blockers/defer state)'
        values = (stamp, row['id'], row.get('issue_type', '?'), status,
                  context(row), row['title'])
        lines.append('| ' + ' | '.join(cell(x) for x in values) + ' |')
    if not rows:
        lines += ['| — | — | — | — | — | No issues |']
    return lines


def write_views(project, snapshot):
    reports = project / 'reports'
    reports.mkdir(exist_ok=True)
    by_date = snapshot['by_created']
    by_context = snapshot['by_context']
    assert {r['id'] for r in by_date} == {r['id'] for r in by_context}
    common = ['Snapshot: ' + snapshot['snapshot_at'] + '.', '',
              'Source of record: this project’s Beads. These are derived views, not separate task lists.', '',
              'Created means the original Beads creation time; evidence periods are separate metadata.', '']
    date_lines = ['# Systemic backlog — by creation date', ''] + common + [
        '[By context](systemic-backlog-by-context.md) · [JSON](systemic-backlog.json)', '',
        'Oldest first, then ID. Includes closed tasks and epics.', '']
    date_lines += table(by_date, set(snapshot['ready_ids']))
    context_lines = ['# Systemic backlog — by primary context', ''] + common + [
        '[By creation date](systemic-backlog-by-created.md) · [JSON](systemic-backlog.json)', '']
    for name in sorted({context(r) for r in by_context}):
        context_lines += ['## ' + name, '']
        context_lines += table([r for r in by_context if context(r) == name], set(snapshot['ready_ids'])) + ['']
    (reports / 'systemic-backlog-by-created.md').write_text('\n'.join(date_lines) + '\n')
    (reports / 'systemic-backlog-by-context.md').write_text('\n'.join(context_lines) + '\n')
    (reports / 'systemic-backlog.json').write_text(json.dumps(snapshot, ensure_ascii=False, indent=2) + '\n')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--project', type=Path, required=True)
    parser.add_argument('--write-views', action='store_true', help='Write only derived reports; no task mutations')
    args = parser.parse_args()
    project = args.project.expanduser().resolve()
    for path in ('AGENTS.md', 'README.md', 'src/index.prose.md', '.beads'):
        if not (project / path).exists():
            raise ValueError('Not a configured Work Reflection project: missing ' + path)
    contract = (project / 'src/index.prose.md').read_text()
    if 'name: work-reflection' not in contract or 'kind: responsibility' not in contract:
        raise ValueError('Contract identity is not work-reflection; do not guess another database')
    rows = [sanitize(r) for r in read_issues(project)]
    ids = [row['id'] for row in rows]
    if len(ids) != len(set(ids)):
        raise ValueError('Duplicate Beads IDs')
    ready = read_issues(project, ready=True)
    ready_ids = {r['id'] for r in ready}
    if not ready_ids.issubset(set(ids)):
        raise ValueError('Backlog changed during reads; rerun before choosing a task')
    candidates = [r for r in rows if r['id'] in ready_ids
                  and r.get('issue_type') != 'epic' and r['status'] == 'open']
    candidates.sort(key=lambda r: (r.get('priority', 2), created(r)))
    snapshot = dict(snapshot_at=datetime.now(timezone.utc).isoformat(), project_root=str(project),
                    next_task_id=candidates[0]['id'] if candidates else None,
                    in_progress_task_ids=sorted(r['id'] for r in rows if r['status'] == 'in_progress'),
                    ready_ids=sorted(ready_ids),
                    by_created=sorted(rows, key=created),
                    by_context=sorted(rows, key=lambda r: (context(r), created(r))))
    if args.write_views:
        write_views(project, snapshot)
    print(json.dumps(dict(project_root=str(project), snapshot_at=snapshot['snapshot_at'],
                         next_task_id=snapshot['next_task_id'], ready_ids=snapshot['ready_ids'],
                         in_progress_task_ids=snapshot['in_progress_task_ids'],
                         issue_count=len(rows), views_written=args.write_views,
                         by_created=[dict(id=r['id'], title=r['title'], status=r['status'],
                                          primary_context=context(r), created_at=r['created_at'])
                                     for r in snapshot['by_created']]), ensure_ascii=False, indent=2))


if __name__ == '__main__':
    try:
        main()
    except (OSError, ValueError, RuntimeError, subprocess.SubprocessError) as error:
        print('systemic: ' + str(error), file=sys.stderr)
        raise SystemExit(1)
