#!/usr/bin/env python3
"""Read-only Wispr capture into a separate Obsidian folder for each talk."""
import argparse
import tempfile
import fcntl
import hashlib
import json
import re
import sqlite3
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

DB = Path.home() / 'Library/Application Support/Wispr Flow/flow.sqlite'

def now():
    return datetime.now(timezone.utc).isoformat()

def atomic(path, text):
    tmp = path.with_name(path.name + '.tmp')
    tmp.write_text(text, encoding='utf-8')
    tmp.replace(path)

def rows(db):
    with sqlite3.connect(db.resolve().as_uri() + '?mode=ro', uri=True, timeout=2) as c:
        c.row_factory = sqlite3.Row
        # Scan IDs and timestamps, including older dictations still processing.
        # Only records admitted after session start are read for their text.
        return [dict(r) for r in c.execute('SELECT transcriptEntityId,timestamp FROM History')]

def content(db, ident):
    with sqlite3.connect(db.resolve().as_uri() + '?mode=ro', uri=True, timeout=2) as c:
        c.row_factory = sqlite3.Row
        r = c.execute('SELECT transcriptEntityId,timestamp,status,asrText,formattedText,duration FROM History WHERE transcriptEntityId=?', (ident,)).fetchone()
        return dict(r) if r else None

def active_meetings(db):
    with sqlite3.connect(db.resolve().as_uri() + '?mode=ro', uri=True, timeout=2) as c:
        c.row_factory = sqlite3.Row
        return [dict(r) for r in c.execute('SELECT id,title,createdAt,finalized,endedAt FROM Meetings WHERE isDeleted=0 AND finalized=0 AND endedAt IS NULL ORDER BY createdAt DESC')]

def meeting_segments(path):
    if not path.is_file():
        return []
    # Ignore only the final incomplete line, then retry it on the next poll.
    data = path.read_bytes()
    lines = data.split(b'\n')[:-1]
    latest = {}
    for line in lines:
        if not line.strip():
            continue
        record = json.loads(line)
        if 'meta' in record or isinstance(record.get('marker'), str):
            continue
        if not isinstance(record.get('id'), str) or not isinstance(record.get('text'), str):
            raise ValueError('Unexpected live transcript schema; capture stopped')
        latest[record['id']] = record
    return [{'transcriptEntityId': r['id'], 'timestamp': str(r.get('timestamp') or r.get('startEpochMs', '')), 'status': 'live-segment', 'asrText': r['text'], 'formattedText': None, 'duration': (r['endEpochMs'] - r['startEpochMs']) / 1000 if r.get('endEpochMs') is not None and r.get('startEpochMs') is not None else None} for r in latest.values()]

def create_session(vault, title):
    stamp = datetime.now(ZoneInfo('Europe/Berlin')).strftime('%Y-%m-%d-%H%M%S')
    slug = re.sub(r'[^\w-]+', '-', title.lower()).strip('-')[:70] or 'talk'
    root = vault / 'Talks' / (stamp + '-' + slug + '-' + uuid.uuid4().hex[:6])
    root.mkdir(parents=True, exist_ok=False)
    (root / '.live').mkdir()
    title = title.replace('\n', ' ')
    props = f'---\ntype: source\ntitle: {json.dumps(title, ensure_ascii=False)}\ncreated_date: {json.dumps(now())}\nstatus: live\nsource: wispr-flow\n---\n\n'
    props = props.replace('status: live', f'talk: {json.dumps(root.name)}\nstatus: live')
    note = props + f'# {title} — source\n\n## Capture notes\n\n## Transcript\n\n<!-- WISPR TRANSCRIPT START -->\n<!-- WISPR TRANSCRIPT END -->\n'
    atomic(root / 'Source.md', note)
    return root

class Watcher:
    def __init__(self, db, root, deadline=30, meeting_id=None):
        self.db, self.root, self.deadline = db, root, deadline
        self.meeting_id = meeting_id
        self.meeting_file = db.parent / "meetings" / meeting_id / "live.ndjson" if meeting_id else None
        self.state_path = root / '.live/state.json'
        if self.state_path.exists():
            self.state = json.loads(self.state_path.read_text())
            if self.state.get('meeting_id') != meeting_id:
                raise ValueError('Resume source differs from original talk source')
        else:
            self.state = {'started_at': now(), 'baseline': [] if meeting_id else [r['transcriptEntityId'] for r in rows(db)], 'meeting_id': meeting_id, 'records': {}, 'events': [], 'status': {}}
            self.save()
        self.state.setdefault('events', [])
        self.state.setdefault('status', {})
    def save(self):
        atomic(self.state_path, json.dumps(self.state, ensure_ascii=False, indent=2))
    def tick(self):
        baseline = set(self.state['baseline'])
        events = []
        snapshot = meeting_segments(self.meeting_file) if self.meeting_file else rows(self.db)
        for metadata in snapshot:
            ident = metadata['transcriptEntityId']
            if ident in baseline:
                continue
            r = metadata if self.meeting_file else content(self.db, ident)
            if not r:
                continue
            record = self.state['records'].setdefault(ident, {'first_seen': time.time(), 'revision': 0})
            text = r['formattedText'] or r['asrText']
            if not text:
                if time.time() - record['first_seen'] >= self.deadline and not record.get('timeout'):
                    events.append({'kind': 'transcription_timeout', 'id': ident, 'revision': record['revision'], 'observed_at': now(), 'status': r['status']})
                    record['timeout'] = True
                continue
            digest = hashlib.sha256(text.encode()).hexdigest()
            if record.get('digest') == digest:
                continue
            record.update(digest=digest, revision=record['revision'] + 1, text=text, source_timestamp=r['timestamp'], observed_at=now(), status=r['status'])
            event = {'kind': 'transcript', 'id': ident, 'revision': record['revision'], 'source_timestamp': r['timestamp'], 'observed_at': record['observed_at'], 'status': r['status'], 'text': text, 'duration_seconds': r['duration']}
            events.append(event)
        transcript = ''
        for ident, r in sorted(self.state['records'].items(), key=lambda pair: pair[1]['first_seen']):
            if r.get('text'):
                fence = '`' * max(3, max((len(run) for run in re.findall(r'`+', r['text'])), default=0) + 1)
                literal = re.sub(r'(?m)^(<!-- WISPR TRANSCRIPT (?:START|END) -->)$', r'\\\1', r['text'])
                transcript += f'### {ident}\n\nSource timestamp: {r["source_timestamp"]}  \nRevision: {r["revision"]} · observed: {r["observed_at"]}\n\n{fence}text\n{literal}\n{fence}\n\n'
        note_path = self.root / 'Source.md'
        note = note_path.read_text(encoding='utf-8')
        start_marker, end_marker = '<!-- WISPR TRANSCRIPT START -->', '<!-- WISPR TRANSCRIPT END -->'
        start = note.index(start_marker) + len(start_marker)
        end = note.index(end_marker, start)
        atomic(note_path, note[:start] + '\n' + transcript + note[end:])
        self.state['events'].extend(events)
        self.state['status'] = {'running': True, 'last_poll_at': now(), 'last_source_change_at': max((r.get('observed_at', '') for r in self.state['records'].values()), default=None), 'source_kind': 'meeting' if self.meeting_file else 'dictation', 'source_file_exists': self.meeting_file.is_file() if self.meeting_file else self.db.is_file(), 'capture_target_seconds': self.deadline, 'pending_count': sum(not r.get('text') for r in self.state['records'].values()), 'observed_timeouts': sum(bool(r.get('timeout')) for r in self.state['records'].values()), 'source_count': sum(bool(r.get('text')) for r in self.state['records'].values())}
        self.save()
        return events

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--mode', choices=['live'], default='live')
    p.add_argument('--db', type=Path, default=DB)
    p.add_argument('--vault', type=Path)
    p.add_argument('--source', choices=['meeting','dictation'], default='meeting')
    p.add_argument('--meeting-id')
    p.add_argument('--list-meetings', action='store_true')
    p.add_argument('--talk', default='Untitled talk')
    p.add_argument('--resume', type=Path, help='Resume exactly this talk folder; a new run otherwise creates a new talk.')
    p.add_argument('--poll-seconds', type=float, default=5)
    p.add_argument('--timeout-seconds', type=float, default=30)
    p.add_argument('--duration-seconds', type=float, default=0, help='0 runs until interrupted')
    p.add_argument('--once', action='store_true')
    p.add_argument('--voice-commands', action='store_true', help='Arm explicit agent-prefixed controls for newly observed speech')
    a = p.parse_args()
    if not 0 < a.poll_seconds <= 30 or a.timeout_seconds <= 0 or a.duration_seconds < 0:
        p.error('poll must be >0 and <=30 seconds; timeout must be positive; duration cannot be negative')
    if a.list_meetings:
        print(json.dumps(active_meetings(a.db), ensure_ascii=False, indent=2))
        return
    if not a.vault and not a.resume:
        p.error('--vault is required for a new talk')
    if not a.db.is_file():
        p.error('Wispr database not found')
    if a.resume and not (a.resume / '.live/state.json').is_file():
        p.error('--resume must name an existing live talk folder')
    # Resolve the same source on resume; never silently switch recordings.
    if a.resume:
        previous = json.loads((a.resume / '.live/state.json').read_text())
        a.meeting_id = previous.get('meeting_id')
        a.source = 'meeting' if a.meeting_id else 'dictation'
    elif a.source == 'meeting' and not a.meeting_id:
        candidates = active_meetings(a.db)
        if len(candidates) != 1:
            p.error('Use --list-meetings and --meeting-id to select a recording; expected exactly one active meeting')
        a.meeting_id = candidates[0]['id']
    if a.meeting_id and (not re.fullmatch(r'[a-zA-Z0-9-]+', a.meeting_id) or a.source != 'meeting'):
        p.error('invalid meeting ID or source combination')
    # Validate source schema before creating output files.
    if a.source == 'meeting':
        meeting_segments(a.db.parent / 'meetings' / a.meeting_id / 'live.ndjson')
    else:
        rows(a.db)
    root = a.resume.resolve() if a.resume else create_session(a.vault.resolve(), a.talk)
    lock_path = Path(tempfile.gettempdir()) / ('wispr-capture-' + hashlib.sha256(str(root).encode()).hexdigest()[:24] + '.lock')
    lock = lock_path.open('a')
    try:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError:
        p.error('This talk already has an active capture process')
    watcher = Watcher(a.db, root, a.timeout_seconds, a.meeting_id)
    print(json.dumps({'talk_folder': str(root), 'poll_seconds': a.poll_seconds, 'timeout_seconds': a.timeout_seconds}), flush=True)
    gate = None
    if a.voice_commands:
        from voice_commands import CommandGate
        watcher.tick()  # baseline existing speech before arming controls
        gate = CommandGate(root, watcher.state['records'])
    start = time.monotonic()
    try:
        while True:
            try:
                events = watcher.tick()
                if gate:
                    gate.apply(events)
                for event in events:
                    # Do not echo private speech into terminal logs.
                    print(json.dumps({k: v for k, v in event.items() if k != 'text'}), flush=True)
            except (sqlite3.Error, OSError) as e:
                print(json.dumps({'kind': 'capture_error', 'at': now(), 'error': str(e)}), flush=True)
            if a.once or (a.duration_seconds and time.monotonic() - start >= a.duration_seconds):
                break
            time.sleep(a.poll_seconds)
    except KeyboardInterrupt:
        pass
    finally:
        watcher.state['status'].update(running=False, stopped_at=now())
        watcher.save()
        lock.close()

if __name__ == '__main__':
    main()
