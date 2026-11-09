from hashlib import sha256
import json
import os
from pathlib import Path
import sys
from tempfile import TemporaryDirectory
from unittest import TestCase
from unittest.mock import patch

from experiments import al02_one_pair_consent as consent
from experiments import al02_one_pair_custody as custody
from experiments import al02_one_pair_job as job


class LimitedConsentTests(TestCase):
    def setUp(self):
        temporary = TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name).resolve()
        self.attempt = self.root / 'attempt'
        self.worker = self.root / 'inert.py'
        self.worker.write_text(
            'import json, os, sys\n'
            'from pathlib import Path\n'
            'event = {"kind": "fixture", "event_id": 0}\n'
            'checkpoint = json.dumps({"state": {"events": [event]}})\n'
            'journal = {"phase": "prefix", "event": event}\n'
            'if os.environ.get("ORA_FIXTURE_MISMATCH"): journal["event"]["event_id"] = False\n'
            '(Path(sys.argv[1]).parent / "partial.jsonl").write_bytes(json.dumps(journal, sort_keys=True, separators=(",", ":")).encode() + b"\\n")\n'
            'print(json.dumps({"checkpoint": checkpoint, "branches": '
            '{"accessible": {"events": []}, "sequestered": {"events": []}}}))\n',
            encoding='ascii')
        self.python = getattr(sys, '_base_executable', sys.executable)
        self.command = [self.python, '-I', '-S', '-B', str(self.worker),
                        str(self.attempt / '00-pending.json'), consent.CONSENT]
        self.pins = {str(p): custody.digest(p) for p in
                     (self.python, self.worker, custody.__file__, consent.__file__,
                      job.__file__, Path(job.__file__).with_name('process_limits.py'))}
        self.dependency = self.root / 'dependency.py'
        self.dependency.write_text('# inert dependency', encoding='ascii')
        self.pins[str(self.dependency)] = custody.digest(self.dependency)
        binding = self.root / 'binding.json'
        raw = json.dumps(dict(command=self.command, relay_argv=job.relay_argv(self.python, self.command),
                              context=consent.CONTEXT, seed=consent.SEED, pins=self.pins)).encode()
        binding.write_bytes(raw)
        scope = patch.multiple(consent, WORKTREE=self.root, ATTEMPT=self.attempt,
                               WORKER=self.worker, STOP=self.root / 'STOP',
                               BINDING=binding, BINDING_SHA256=sha256(raw).hexdigest(),
                               APPROVED_WORKER_SHA256=None)
        scope.start()
        self.addCleanup(scope.stop)

    def run_inert(self, **changes):
        params = dict(command=self.command, cwd=self.root, pins=self.pins,
                      expected_account=consent.OWNER, context=consent.CONTEXT,
                      consent=consent.CONSENT, referee=lambda raw: raw.decode().strip())
        params.update(changes)
        return custody.transaction(self.attempt, **params)

    def test_inert_consent_release_and_duplicate(self):
        with patch.object(consent, 'APPROVED_WORKER_SHA256', self.pins[str(self.worker)]):
            self.assertIn('fixture', self.run_inert())
            with self.assertRaises(FileExistsError):
                self.run_inert()
        self.assertTrue((self.attempt / '04-terminal.json').exists())

    def test_mismatched_partial_journal_blocks_referee(self):
        with patch.object(consent, 'APPROVED_WORKER_SHA256', self.pins[str(self.worker)]), \
             patch.dict(os.environ, ORA_FIXTURE_MISMATCH='1'):
            with self.assertRaisesRegex(ValueError, 'does not match'):
                self.run_inert(referee=lambda raw: self.fail('Referee received invalid evidence'))
        failure = json.loads((self.attempt / '99-failed.json').read_bytes())
        self.assertTrue(failure['release_intent'])
        self.assertIn('sha256', failure['partial'])

    def test_scope_and_unqualified_worker_fail_before_attempt(self):
        for changes, reason in [
            ({'context': 'other'}, 'scope'),
            ({'command': self.command + ['extra']}, 'scope'),
            ({'admission_check': lambda: True}, 'mixed'),
            ({'consent': 'other'}, 'Unrecognized'),
            ({}, 'No reviewed scientific worker'),
        ]:
            with self.subTest(changes=changes), self.assertRaisesRegex(ValueError, reason):
                self.run_inert(**changes)
            self.assertFalse(self.attempt.exists())

    def test_approved_binding_rejects_missing_pin_and_modified_bytes(self):
        with patch.object(consent, 'APPROVED_WORKER_SHA256', self.pins[str(self.worker)]):
            missing = dict(self.pins)
            del missing[str(self.dependency)]
            with self.assertRaisesRegex(ValueError, 'required closure'):
                self.run_inert(pins=missing)
            consent.BINDING.write_bytes(b'{}')
            with self.assertRaisesRegex(ValueError, 'binding manifest differs'):
                self.run_inert()
        self.assertFalse(self.attempt.exists())

    def test_stop_refuses_even_the_inert_pin(self):
        consent.STOP.touch()
        with patch.object(consent, 'APPROVED_WORKER_SHA256', self.pins[str(self.worker)]):
            with self.assertRaisesRegex(ValueError, 'STOP'):
                self.run_inert()
        self.assertFalse(self.attempt.exists())
