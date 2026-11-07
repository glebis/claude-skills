#!/usr/bin/env python3
"""Diagnose the pii-pdf engine and prove it works end to end. Never installs or changes anything.

Stages (NDJSON events on stdout):
  1. setup_plan  - bundled-source integrity + missing install steps (setup.py --plan)
  2. cli_doctor  - dependency/model check inside the runtime (pii-pdf doctor)
  3. smoke       - redact a synthetic 2-page PDF (native text + image scan) and check that
                   the fake PII is gone and the non-PII controls survived, on every page
Then a `diagnosis` event lists each problem with the exact repair step.

Exit codes: 0 healthy | 3 not installed/broken (repair via setup) | 4 smoke test flagged the
detector | 5 doctor itself failed. Exit 0 means the fixture passed, not that real documents
will be anonymised.
"""
import argparse
import datetime
import json
import os
import subprocess
import sys
import tempfile
import uuid
from pathlib import Path

HERE = Path(__file__).resolve().parent
RUN_ID = str(uuid.uuid4())
SEQ = 0
SETUP_APPLY = 'python3 "$SKILL_DIR/scripts/setup.py" --apply'


def emit(event, **fields):
    global SEQ
    SEQ += 1
    print(json.dumps(dict(schema_version='1.0', event=event, ts=datetime.datetime.now(datetime.timezone.utc).isoformat(), run_id=RUN_ID, seq=SEQ, **fields)), flush=True)


def call(command, timeout=600):
    try:
        r = subprocess.run([str(c) for c in command], capture_output=True, text=True, timeout=timeout)
    except (OSError, subprocess.TimeoutExpired) as exc:
        return None, [], type(exc).__name__
    events = []
    for line in r.stdout.splitlines():
        try:
            events.append(json.loads(line))
        except ValueError:
            pass
    return r.returncode, events, r.stderr[-800:]


def last(events, name):
    return next((e for e in reversed(events) if e.get('event') == name), None)


def stage_setup_plan(venv, findings):
    code, events, err = call([sys.executable, HERE / 'setup.py', '--plan', '--venv', venv])
    error = last(events, 'error')
    plan = last(events, 'plan')
    done = last(events, 'complete')
    if error or code != 0 or not plan:
        msg = (error or {}).get('message') or err or 'setup.py --plan failed'
        if 'checksum' in msg or 'manifest' in msg or 'bundled source' in msg.lower():
            fix = 'The bundled CLI source differs from source.sha256. Restore it with git (git diff pii-pdf/assets) or, if the edit is intentional, regenerate source.sha256, then run setup --apply.'
        else:
            fix = 'Run setup.py --plan directly and resolve the reported error.'
        findings.append({'stage': 'setup_plan', 'problem': msg, 'fix': fix, 'severity': 'blocking'})
        emit('stage', name='setup_plan', ok=False)
        return False
    if plan.get('system_problem'):
        findings.append({'stage': 'setup_plan', 'problem': 'System dependency missing.', 'fix': plan['system_problem'], 'severity': 'blocking'})
    if plan.get('commands'):
        findings.append({'stage': 'setup_plan', 'problem': f"{len(plan['commands'])} install step(s) pending.", 'fix': SETUP_APPLY, 'pending': [' '.join(c) for c in plan['commands']], 'severity': 'blocking'})
    ready = bool(done and done.get('ready'))
    emit('stage', name='setup_plan', ok=ready, packages=plan.get('packages'), tesseract_ok=plan.get('tesseract_ok'), english_data_ok=plan.get('english_data_ok'))
    return ready


def stage_cli_doctor(venv, findings):
    code, events, err = call([sys.executable, HERE / 'run.py', '--runtime', venv, 'doctor'], timeout=180)
    report = last(events, 'doctor')
    if not report:
        e = last(events, 'error') or {}
        findings.append({'stage': 'cli_doctor', 'problem': e.get('message') or err or 'pii-pdf doctor produced no report.', 'fix': SETUP_APPLY, 'severity': 'blocking'})
        emit('stage', name='cli_doctor', ok=False)
        return False
    hints = {
        'PyMuPDF': 'PyMuPDF missing or outside >=1.26.7,<1.27: ' + SETUP_APPLY,
        'spacy': 'spaCy missing: ' + SETUP_APPLY,
        'tesseract': 'Tesseract not on PATH (macOS: brew install tesseract), then rerun doctor.',
        'model': 'spaCy model missing: ' + SETUP_APPLY,
    }
    for name, check in report.get('checks', {}).items():
        if not check.get('available'):
            findings.append({'stage': 'cli_doctor', 'problem': f'{name} unavailable.', 'fix': hints.get(name, SETUP_APPLY), 'severity': 'blocking'})
    emit('stage', name='cli_doctor', ok=bool(report.get('ok')), checks=report.get('checks'))
    return bool(report.get('ok'))


def stage_smoke(venv, workdir, findings):
    python = Path(venv) / ('Scripts/python.exe' if os.name == 'nt' else 'bin/python')
    fixture_dir, out_dir = workdir / 'fixture', workdir / 'redacted'
    code, events, err = call([python, '-I', HERE / 'smoke_fixture.py', 'build', fixture_dir], timeout=120)
    if code != 0:
        findings.append({'stage': 'smoke', 'problem': 'Could not build the synthetic fixture: ' + err.strip()[-300:], 'fix': 'Check PyMuPDF in the runtime: ' + SETUP_APPLY, 'severity': 'blocking'})
        emit('stage', name='smoke', ok=False)
        return False
    code, events, err = call([sys.executable, HERE / 'run.py', '--runtime', venv, 'redact', fixture_dir / 'fixture.pdf', '--output', out_dir, '--json'])
    summary = last(events, 'summary') or {}
    detections = sum(e.get('detections', 0) for e in events if e.get('event') == 'file_result')
    redacted = out_dir / 'fixture.pdf'
    if code not in (0, 4) or not redacted.is_file():
        e = last(events, 'error') or {}
        findings.append({'stage': 'smoke', 'problem': f"redact exited {code}: {e.get('message') or err.strip()[-300:]}", 'fix': 'Rerun the redact command on a test PDF to see the full error; if it is a dependency error, ' + SETUP_APPLY, 'severity': 'blocking'})
        emit('stage', name='smoke', ok=False, redact_exit=code)
        return False
    code, events, err = call([python, '-I', HERE / 'smoke_fixture.py', 'verify', redacted], timeout=300)
    verdict = events[-1] if events else None
    if code != 0 or not verdict:
        findings.append({'stage': 'smoke', 'problem': 'Could not verify the redacted fixture: ' + err.strip()[-300:], 'fix': 'Check Tesseract (tesseract --list-langs must include eng).', 'severity': 'blocking'})
        emit('stage', name='smoke', ok=False)
        return False
    for page in verdict['pages']:
        where = f"page {page['page']} ({page['kind']})"
        if not page['ocr_checked']:
            findings.append({'stage': 'smoke', 'problem': f'OCR verification did not run on {where}.', 'fix': 'Check that tesseract runs and has eng data.', 'severity': 'blocking'})
        if page['leaked']:
            findings.append({'stage': 'smoke', 'problem': f"Fake {', '.join(page['leaked'])} still readable on {where} after redaction.", 'fix': 'Detector regression or misconfiguration: do not trust redactions until fixed. Rerun with --keep and inspect the redacted fixture; for scans, try --dpi 400 or another --psm.', 'severity': 'detector'})
        if page['missing_controls']:
            findings.append({'stage': 'smoke', 'problem': f"Non-PII text ({', '.join(page['missing_controls'])}) deleted on {where}.", 'fix': 'Over-redaction (known: OCR block reordering labels headings as PERSON). Inspect the output before relying on table structure.', 'severity': 'detector'})
    emit('stage', name='smoke', ok=verdict['ok'], redact_exit=summary.get('exit_code'), detections=detections, pages=verdict['pages'])
    return verdict['ok']


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument('--runtime', default='~/.local/share/pii-pdf/venv', help='Runtime venv to diagnose.')
    p.add_argument('--no-smoke', action='store_true', help='Only diagnose; skip the synthetic redaction test.')
    p.add_argument('--keep', action='store_true', help='Keep the fixture and redacted copy for inspection (only fake data).')
    args = p.parse_args(argv)
    venv = str(Path(args.runtime).expanduser().absolute())
    global SETUP_APPLY
    if venv != str(Path('~/.local/share/pii-pdf/venv').expanduser().absolute()):
        SETUP_APPLY += ' --venv "' + venv + '"'
    findings = []
    emit('doctor_started', runtime=venv, smoke=not args.no_smoke)
    installed = stage_setup_plan(venv, findings)
    healthy = stage_cli_doctor(venv, findings) and installed
    smoke_ok = None
    kept = None
    if args.no_smoke:
        pass
    elif not healthy:
        emit('stage', name='smoke', ok=None, skipped='Repair the blocking findings first.')
    else:
        workdir = Path(tempfile.mkdtemp(prefix='pii-pdf-doctor-')) if args.keep else None
        if workdir:
            smoke_ok = stage_smoke(venv, workdir, findings)
            kept = str(workdir)
        else:
            with tempfile.TemporaryDirectory(prefix='pii-pdf-doctor-') as tmp:
                smoke_ok = stage_smoke(venv, Path(tmp), findings)
    exit_code = 3 if not healthy else 4 if smoke_ok is False else 0
    emit('diagnosis', ok=exit_code == 0, findings=findings, kept_workdir=kept,
         note='A passing smoke test covers one synthetic fixture only; it does not validate real documents.')
    return exit_code


if __name__ == '__main__':
    try:
        sys.exit(main())
    except Exception as exc:  # doctor must always report, never traceback
        emit('error', ok=False, message='Doctor failed: ' + type(exc).__name__ + ': ' + str(exc), exit_code=5)
        sys.exit(5)
