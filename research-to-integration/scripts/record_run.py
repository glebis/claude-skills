#!/usr/bin/env python3
"""Record inspected, authorized commands. This helper is not a sandbox."""
import argparse
import json
import math
import os
from pathlib import Path
import platform
import signal
import subprocess
import sys
import time

# Required platform/runtime settings only. Credentials and HOME are not forwarded.
BASE_ENV = ('PATH', 'LANG', 'LC_ALL', 'LC_CTYPE', 'TZ', 'SYSTEMROOT', 'WINDIR',
            'TMP', 'TEMP', 'TMPDIR', 'SSL_CERT_FILE', 'SSL_CERT_DIR')


def private_file(path):
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, 'O_NOFOLLOW', 0)
    return os.fdopen(os.open(path, flags, 0o600), 'wb')


def stop(proc):
    if os.name == 'posix':
        try:
            os.killpg(proc.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
    else:
        proc.kill()
    proc.wait()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True, help='New private run directory; must not exist')
    parser.add_argument('--cwd', type=Path, default=Path.cwd())
    parser.add_argument('--timeout', type=float, default=600)
    parser.add_argument('--pass-env', action='append', default=[], metavar='NAME',
                        help='Explicitly forward one environment variable; never log its value')
    parser.add_argument('command', nargs=argparse.REMAINDER, help='Inspected argv after --; never include secrets')
    args = parser.parse_args()
    command = args.command[1:] if args.command[:1] == ['--'] else args.command
    if not command or not math.isfinite(args.timeout) or args.timeout <= 0:
        parser.error('Provide a command and a finite positive timeout')
    cwd = args.cwd.resolve()
    if not cwd.is_dir():
        parser.error('cwd must be an existing directory')
    for name in args.pass_env:
        if not name.isidentifier() or name not in os.environ:
            parser.error('Each --pass-env must name a present environment variable')
    child_env = {name: os.environ[name] for name in (*BASE_ENV, *args.pass_env) if name in os.environ}
    args.output.mkdir(parents=True, exist_ok=False, mode=0o700)
    start, clock = time.time(), time.monotonic()
    status, code, error = 'not_started', None, None
    with private_file(args.output/'stdout.log') as stdout, private_file(args.output/'stderr.log') as stderr:
        try:
            proc = subprocess.Popen(command, cwd=cwd, stdout=stdout, stderr=stderr,
                                    shell=False, env=child_env, close_fds=True,
                                    start_new_session=(os.name == 'posix'))
            try:
                code = proc.wait(timeout=args.timeout)
                status = 'completed' if code == 0 else 'failed'
            except subprocess.TimeoutExpired:
                stop(proc)
                status, code = 'timed_out', 124
            except KeyboardInterrupt:
                stop(proc)
                status, code = 'interrupted', 130
        except OSError as exc:
            status, code, error = 'launch_failed', 127, str(exc)
    report = dict(command=command, cwd=str(cwd), started_unix=start,
                  elapsed_seconds=round(time.monotonic()-clock, 6), timeout_seconds=args.timeout,
                  execution_status=status, exit_code=code, error=error,
                  quality_status='not_evaluated', platform=platform.platform(),
                  python=sys.version, environment_names=sorted(child_env),
                  logs=['stdout.log', 'stderr.log'])
    with private_file(args.output/'run.json') as stream:
        stream.write((json.dumps(report, indent=2)+'\n').encode('utf-8'))
    print(json.dumps(report))
    return code if code is not None and 0 <= code <= 255 else 1


if __name__ == '__main__':
    sys.exit(main())
