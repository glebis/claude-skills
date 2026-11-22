"""Run log shared by all promo-reels scripts — the evidence `reflect.py` reflects on.

Every script calls `runlog.init()` at start. It appends JSON lines to
<project>/.promo-reels/runlog.jsonl: start (argv), signals (`runlog.signal(...)`),
exit code, and crashes with the last traceback line. Project = $PROMO_REELS_PROJECT,
else the hint a script passes (e.g. the EDL's folder), else the current directory.
Logging never breaks a run: every write is best-effort.
"""
import atexit, datetime, json, os, pathlib, platform, sys, traceback

_state = {'file': None, 'script': pathlib.Path(sys.argv[0]).stem, 'exited': False}


def init(project=None):
    root = pathlib.Path(os.environ.get('PROMO_REELS_PROJECT') or project or os.getcwd()).resolve()
    try:
        d = root / '.promo-reels'; d.mkdir(parents=True, exist_ok=True)
        _state['file'] = d / 'runlog.jsonl'
    except OSError:
        return
    _write('start', argv=sys.argv[1:], platform=f'{platform.system()} {platform.machine()}',
           python=platform.python_version())

    real_exit = sys.exit

    def exit_logged(code=0):
        _state['exited'] = True
        msg = code if isinstance(code, str) else None
        _write('exit', code=1 if msg else (code or 0), message=msg)
        real_exit(code)
    sys.exit = exit_logged

    real_hook = sys.excepthook

    def hook(t, v, tb):
        _state['exited'] = True
        _write('crash', error=f'{t.__name__}: {v}', where=traceback.format_tb(tb)[-1].strip()[:300] if tb else '')
        real_hook(t, v, tb)
    sys.excepthook = hook
    atexit.register(lambda: _state['exited'] or _write('exit', code=0))


def signal(kind, topic, what, **data):
    """Something reflect.py should look at. kind: error | warning | fix | scenario | metric."""
    _write('signal', kind=kind, topic=topic, what=what, **data)


def _write(event, **data):
    if not _state['file']:
        return
    rec = {'ts': datetime.datetime.now().isoformat(timespec='seconds'), 'script': _state['script'], 'event': event, **data}
    try:
        with open(_state['file'], 'a', encoding='utf-8') as f:
            f.write(json.dumps(rec, ensure_ascii=False, default=str) + '\n')
    except OSError:
        pass


REMINDER = ('\nNEXT — reflection: run `python3 {skill}/scripts/reflect.py` in this project folder and show the user '
            'its proposals before calling the job done.')


def remind():
    print(REMINDER.format(skill=pathlib.Path(__file__).resolve().parent.parent))
