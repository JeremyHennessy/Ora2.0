"""New process-boundary persistence integration, authored software fixture only."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
FILES = ['__init__.py', 'digital_budgeted_transfer_v1.py',
         'digital_budgeted_transfer_referee_v1.py', 'digital_budgeted_transfer_replay_v1.py',
         'digital_context90_access_v2.py', 'digital_context90_crossed_engine_v1.py']


def enc(v):
    return json.dumps(v, sort_keys=True, separators=(',', ':'), ensure_ascii=True, allow_nan=False).encode('ascii')


class LearningRestartIntegration(unittest.TestCase):
    def test_committed_acquired_memory_survives_real_crash_and_orphans(self):
        with tempfile.TemporaryDirectory(prefix='ora-software-restart-') as directory:
            root = Path(directory)
            package = root / 'source/learning/experiments'; package.mkdir(parents=True)
            pins = {}
            for name in FILES:
                raw = (ROOT / 'experiments' / name).read_bytes()
                (package / name).write_bytes(raw)
                pins['experiments/' + name] = dict(extent=len(raw), sha256=hashlib.sha256(raw).hexdigest())
            worker = ROOT / 'experiments/digital_learning_restart_fixture_v1.py'
            config = dict(schema='ORA-LEARNING-RESTART-SOFTWARE-v1', root=str(root),
                          source_pins=pins, source_sha256=hashlib.sha256(enc(pins)).hexdigest(),
                          primary_admission=False)
            raw = enc(config); path = root / 'config.json'; path.write_bytes(raw)
            for role in ('reference', 'crash', 'recover', 'tamper'):
                result = subprocess.run([sys.executable, '-B', str(worker), role, str(path),
                                         hashlib.sha256(raw).hexdigest()],
                                        capture_output=True, timeout=10, check=False)
                self.assertEqual(result.returncode, 78 if role == 'crash' else 0,
                                 result.stdout.decode(errors='replace') + result.stderr.decode(errors='replace'))
                self.assertLess(len(result.stdout) + len(result.stderr), 65536)
            recovery = json.loads((root / 'recovery.json').read_bytes())
            self.assertTrue(recovery['acquired_memory_retained'])
            self.assertTrue(recovery['exact_checkpoint'])
            self.assertTrue(recovery['exact_final_state'])
            self.assertTrue(recovery['exact_decisions_and_costs'])
            self.assertFalse(recovery['orphan_promoted'])
            self.assertEqual(recovery['discarded_uncommitted_steps'], 3)
            self.assertTrue(json.loads((root / 'tamper.json').read_bytes())['corruption_refused_before_restore'])


if __name__ == '__main__':
    unittest.main()
