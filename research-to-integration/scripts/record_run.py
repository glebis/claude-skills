#!/usr/bin/env python3
"""Record an actual command execution, not a quality verdict. Standard library only."""
import argparse
import json
import os
from pathlib import Path
import platform
import signal
import subprocess
import sys
import time


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True, help='New run directory; must not exist')
    parser.add_argument('--cwd', type=Path, default=Path.cwd())
    parser.add_argument('--timeout', type=float, default=600)
    parser.add_argument('command', nargs=argparse.REMAINDER, help='Command after --; never include secrets')
    args = parser.parse_args()
    command = args.command[1:] if args.command[:1] == ['--'] else args.command
    if not command or args.timeout <= 0:
        parser.error('Provide a command and a positive timeout')
    cwd = args.cwd.resolve()
    if not cwd.is_dir():
        parser.error('cwd must be an existing directory')
    args.output.mkdir(parents=True, exist_ok=False)
    start = time.time()
    status, code, error = 'not_started', None, None
    with (args.output / 'stdout.log').open('wb') as stdout, (args.output / 'stderr.log').open('wb') as stderr:
        try:
            proc = subprocess.Popen(command, cwd=cwd, stdout=stdout, stderr=stderr,
                                    start_new_session=(os.name == 'posix'))
            try:
                code = proc.wait(timeout=args.timeout)
                status = 'completed' if code == 0 else 'failed'
            except subprocess.TimeoutExpired:
                if os.name == 'posix':
                    os.killpg(proc.pid, signal.SIGKILL)
                else:
                    proc.kill()
                proc.wait()
                status, code = 'timed_out', 124
        except OSError as exc:
            status, code, error = 'launch_failed', 127, str(exc)
    report = dict(command=command, cwd=str(cwd), started_unix=start,
                  elapsed_seconds=round(time.time()-start, 6), timeout_seconds=args.timeout,
                  execution_status=status, exit_code=code, error=error,
                  quality_status='not_evaluated', platform=platform.platform(),
                  python=sys.version, logs=['stdout.log', 'stderr.log'])
    (args.output / 'run.json').write_text(json.dumps(report, indent=2)+'\n', encoding='utf-8')
    print(json.dumps(report))
    return code if code is not None and 0 <= code <= 255 else 1


if __name__ == '__main__':
    sys.exit(main())
