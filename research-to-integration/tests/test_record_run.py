import json
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
                                           '--timeout', '1', '--', *command], capture_output=True)
                    report = json.loads((output/'run.json').read_text())
                    self.assertEqual(proc.returncode, code)
                    self.assertEqual(report['execution_status'], status)
                    self.assertEqual(report['quality_status'], 'not_evaluated')
            output = Path(tmp)/'success'
            self.assertEqual((output/'stdout.log').read_text().strip(), '42')
            proc = subprocess.run([sys.executable, str(RECORDER), '--output', str(output),
                                   '--', sys.executable, '-c', 'print(99)'], capture_output=True)
            self.assertNotEqual(proc.returncode, 0)
            self.assertEqual((output/'stdout.log').read_text().strip(), '42')

if __name__ == '__main__':
    unittest.main()
