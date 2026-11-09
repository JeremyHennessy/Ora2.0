"""Probe the actual isolated worker without a World or scientific context."""
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
from tempfile import TemporaryDirectory
from unittest import TestCase


class WorkerClosureTests(TestCase):
    def setUp(self):
        temp = TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name).resolve()
        self.repo = Path(__file__).resolve().parents[1]
        self.worker = self.root / 'experiments/al02_one_pair_worker.py'
        self.worker.parent.mkdir()
        self.python = Path(getattr(sys, '_base_executable', sys.executable))
        self.manifest = self.root / 'probe.json'
        paths = (
            '__init__', 'al02_one_pair_worker', 'al02_one_pair', 'executed_heredity',
            'al02_depletion_checkpoint', 'al02_depletion_producer',
            'al02_depletion_projection', 'al02_depletion_suffix', 'al02_selection_referee',
            'al02_selection_request', 'causal_genealogy_audit',
        )
        self.files = [self.python]
        for name in paths:
            relative = Path('experiments') / (name + '.py')
            path = self.root / relative
            shutil.copyfile(self.repo / relative, path)
            self.files.append(path)
        self.pins = {str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in self.files}

    def probe(self, options=('-I', '-S', '-B')):
        self.manifest.write_text(json.dumps(dict(cwd=str(self.root), pins=self.pins)))
        return subprocess.run([str(self.python), *options, str(self.worker),
                               str(self.manifest), '--probe'], cwd=self.root,
                              capture_output=True, timeout=10, check=False)

    def test_actual_isolated_imports(self):
        result = self.probe()
        self.assertEqual(result.returncode, 0, result.stderr.decode())
        observed = set(json.loads(result.stdout))
        self.assertTrue(set(self.pins) <= observed)
        self.assertIn(str(self.root / 'experiments/al02_selection_referee.py'), observed)

    def test_reject_substitution_and_unlisted_import(self):
        target = self.root / 'experiments/al02_selection_request.py'
        target.write_bytes(target.read_bytes() + b'\nimport experiments.unlisted\n')
        result = self.probe()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn(b'Pinned source mismatch', result.stderr)
        self.pins[str(target)] = hashlib.sha256(target.read_bytes()).hexdigest()
        result = self.probe()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn(b'Unapproved project import', result.stderr)

    def test_direct_invocation_cannot_use_forged_release_journal(self):
        from experiments.al02_one_pair_worker import CONSENT
        driver = self.root / 'experiments/al02_one_pair.py'
        driver.write_bytes(driver.read_bytes() +
                           b'\ndef produce(*args): raise AssertionError("inert guard tripped")\n')
        self.pins[str(driver)] = hashlib.sha256(driver.read_bytes()).hexdigest()
        probe = self.probe()
        self.assertEqual(probe.returncode, 0, probe.stderr.decode())
        pins = {p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
                for p in json.loads(probe.stdout)}
        command = [str(self.python), '-I', '-S', '-B', str(self.worker),
                   str(self.manifest), CONSENT]
        pending = json.dumps(dict(
            cwd=str(self.root), pins=pins, command=command, consent=CONSENT,
            evidence_tier='LOW_ASSURANCE_EXPLORATORY',
            context='71bb1e2c35ff536900807c5c0ee86d30c13722b85291a8e8f086c0c62dc934b8',
            environment_sha256=hashlib.sha256(json.dumps(
                dict(os.environ), sort_keys=True).encode()).hexdigest())).encode()
        self.manifest.write_bytes(pending)
        verified = json.dumps(dict(pending_sha256=hashlib.sha256(pending).hexdigest(), bootstrap_pid=os.getpid())).encode()
        (self.root / '01-verified.json').write_bytes(verified)
        (self.root / '02-release-intent.json').write_text(json.dumps(
            dict(verified_sha256=hashlib.sha256(verified).hexdigest())))
        result = subprocess.run(command, cwd=self.root, stdin=subprocess.DEVNULL, capture_output=True, timeout=10)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn(b'Release requires a live Job stdin pipe', result.stderr)
        self.assertEqual(result.stdout, b'')

    def test_requires_isolated_no_site_startup(self):
        result = self.probe(('-S', '-B'))
        self.assertNotEqual(result.returncode, 0)
        self.assertIn(b'Require isolated', result.stderr)
