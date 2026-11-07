import json
import os
import stat
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

RECORDER = Path(__file__).resolve().parents[1] / 'scripts' / 'record_run.py'

class RecorderTest(unittest.TestCase):
    def test_execution_states_and_no_overwrite(self):
        with tempfile.TemporaryDirectory() as tmp:
            cases = [('success', [sys.executable, '-c', 'print(42)'], 'completed', 0),
                     ('failure', [sys.executable, '-c', 'raise SystemExit(3)'], 'failed', 3),
                     ('timeout', [sys.executable, '-c', 'import time; time.sleep(10)'], 'timed_out', 124),
                     ('missing', [str(Path(tmp) / 'nonexistent-command')], 'launch_failed', 127)]
            for name, command, status, code in cases:
                with self.subTest(name=name):
                    output = Path(tmp) / name
                    proc = subprocess.run([sys.executable, str(RECORDER), '--output', str(output),
                                           '--timeout', '1', '--', *command], capture_output=True, shell=False)
                    report = json.loads((output/'run.json').read_text())
                    self.assertEqual(proc.returncode, code)
                    self.assertEqual(report['execution_status'], status)
                    self.assertEqual(report['quality_status'], 'not_evaluated')
            output = Path(tmp)/'success'
            self.assertEqual((output/'stdout.log').read_text().strip(), '42')
            proc = subprocess.run([sys.executable, str(RECORDER), '--output', str(output),
                                   '--', sys.executable, '-c', 'print(99)'], capture_output=True, shell=False)
            self.assertNotEqual(proc.returncode, 0)
            self.assertEqual((output/'stdout.log').read_text().strip(), '42')

    def test_finite_timeout_required(self):
        with tempfile.TemporaryDirectory() as tmp:
            for timeout in ['nan', 'inf', '-1', '0']:
                proc = subprocess.run([sys.executable, str(RECORDER), '--output', str(Path(tmp)/timeout),
                    '--timeout', timeout, '--', sys.executable, '-c', 'print(1)'], capture_output=True, shell=False)
                self.assertEqual(proc.returncode, 2)
                self.assertFalse((Path(tmp)/timeout).exists())

    def test_environment_permissions_and_literal_arguments(self):
        with tempfile.TemporaryDirectory() as tmp:
            env = dict(os.environ, RESEARCH_TEST_SECRET='synthetic-canary-123')
            def run(name, options):
                output = Path(tmp)/name
                marker = Path(tmp)/'should-not-exist'
                code = 'import os,sys; print(os.getenv("RESEARCH_TEST_SECRET", "absent")); print(sys.argv[1])'
                argument = '; touch '+str(marker)
                proc = subprocess.run([sys.executable, str(RECORDER), '--output', str(output), *options,
                    '--', sys.executable, '-c', code, argument], env=env, capture_output=True, shell=False)
                self.assertEqual(proc.returncode, 0, proc.stderr)
                self.assertFalse(marker.exists())
                if os.name == 'posix':
                    self.assertEqual(stat.S_IMODE(output.stat().st_mode), 0o700)
                    for filename in ['stdout.log', 'stderr.log', 'run.json']:
                        self.assertEqual(stat.S_IMODE((output/filename).stat().st_mode), 0o600)
                return output
            first = run('default', [])
            self.assertTrue((first/'stdout.log').read_text().startswith('absent\n'))
            second = run('explicit', ['--pass-env', 'RESEARCH_TEST_SECRET'])
            self.assertTrue((second/'stdout.log').read_text().startswith('synthetic-canary-123\n'))
            self.assertNotIn('synthetic-canary-123', (second/'run.json').read_text())

if __name__ == '__main__':
    unittest.main()
