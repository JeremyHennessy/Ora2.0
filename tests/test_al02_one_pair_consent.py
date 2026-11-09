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
        self.worker.write_text('print("inert")\n', encoding='ascii')
        self.python = getattr(sys, '_base_executable', sys.executable)
        self.command = [self.python, '-I', '-S', '-B', str(self.worker),
                        str(self.attempt / '00-pending.json'), consent.CONSENT]
        self.pins = {str(p): custody.digest(p) for p in
                     (self.python, self.worker, custody.__file__, consent.__file__,
                      job.__file__, Path(job.__file__).with_name('process_limits.py'))}
        scope = patch.multiple(consent, WORKTREE=self.root, ATTEMPT=self.attempt,
                               WORKER=self.worker, STOP=self.root / 'STOP')
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
            self.assertEqual(self.run_inert(), 'inert')
            with self.assertRaises(FileExistsError):
                self.run_inert()
        self.assertTrue((self.attempt / '04-terminal.json').exists())

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

    def test_stop_refuses_even_the_inert_pin(self):
        consent.STOP.touch()
        with patch.object(consent, 'APPROVED_WORKER_SHA256', self.pins[str(self.worker)]):
            with self.assertRaisesRegex(ValueError, 'STOP'):
                self.run_inert()
        self.assertFalse(self.attempt.exists())
