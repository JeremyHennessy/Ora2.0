"""Synthetic one-shot disk custody tests; all launches mocked, zero Worlds."""
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from experiments import digital_pilot74_durable_supervisor_v1 as s

PIN = 'a' * 64
SPEC = dict(path='synthetic-only', extent=1, sha256=PIN)


class Custody(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name) / 'new-attempt'

    def attempt(self):
        value = s.Attempt(self.root, PIN)
        self.addCleanup(value.close)
        return value

    def test_preallocated_started_and_no_repeat(self):
        value = self.attempt()
        self.assertEqual((self.root / 'terminal.slot').stat().st_size, s.SLOT_BYTES)
        self.assertEqual(s.read_slot(self.root / 'started.slot')['status'], 'STARTED')
        with self.assertRaises(FileExistsError):
            s.Attempt(self.root, PIN)
        with self.assertRaises(ValueError):
            s.read_slot(self.root / 'terminal.slot')

    def test_admission_refusal_never_launches(self):
        value = self.attempt()
        with patch('experiments.digital_pilot74_guardian_v1.launch_guardian') as launch:
            with self.assertRaises(ValueError):
                value.run(SPEC, PIN, lambda *args: False)
            launch.assert_not_called()
        self.assertEqual(s.read_slot(self.root / 'terminal.slot')['status'], 'FAILED')

    def test_exact_pin_required(self):
        value = self.attempt()
        with self.assertRaises(ValueError):
            value.run(SPEC, 'b' * 64, lambda *args: True)

    def test_success_retains_transport_not_acceptance(self):
        value = self.attempt()
        with patch('experiments.digital_pilot74_guardian_v1.launch_guardian', return_value={'exit_code': 0}) as launch:
            self.assertEqual(value.run(SPEC, PIN, lambda *args: True), {'exit_code': 0})
            launch.assert_called_once()
        receipt = s.read_slot(self.root / 'terminal.slot')
        self.assertFalse(receipt['publication_accepted'])
        with self.assertRaises(ValueError):
            value.run(SPEC, PIN, lambda *args: True)

    def test_original_error_and_native_facts_retained(self):
        value = self.attempt()
        first = RuntimeError('first')
        first.guardian_failure_evidence = {'termination_requested': True, 'closure_observed': False}
        with patch('experiments.digital_pilot74_guardian_v1.launch_guardian', side_effect=first):
            with self.assertRaises(RuntimeError) as raised:
                value.run(SPEC, PIN, lambda *args: True)
        self.assertIs(raised.exception, first)
        self.assertEqual(s.read_slot(self.root / 'terminal.slot')['guardian'], first.guardian_failure_evidence)

    def test_failed_retention_preserves_first_and_started(self):
        value = self.attempt()
        first = RuntimeError('first')
        with patch('experiments.digital_pilot74_guardian_v1.launch_guardian', side_effect=first), patch.object(value, 'write', side_effect=OSError('disk')) as write:
            with self.assertRaises(RuntimeError) as raised:
                value.run(SPEC, PIN, lambda *args: True)
            self.assertEqual(write.call_count, 1)
        self.assertIs(raised.exception, first)
        self.assertEqual(s.read_slot(self.root / 'started.slot')['status'], 'STARTED')

    def test_success_receipt_failure_never_rewrites_terminal(self):
        value = self.attempt()
        with patch('experiments.digital_pilot74_guardian_v1.launch_guardian', return_value={}), patch.object(value, 'write', side_effect=OSError('disk')) as write:
            with self.assertRaises(OSError):
                value.run(SPEC, PIN, lambda *args: True)
            self.assertEqual(write.call_count, 1)

    def test_oversized_evidence_not_truncated(self):
        value = self.attempt()
        with self.assertRaises(ValueError):
            value.write('terminal', {'large': 'x' * s.SLOT_BYTES})
        with self.assertRaises(ValueError):
            s.read_slot(self.root / 'terminal.slot')

    def test_corrupt_receipt_not_accepted(self):
        value = self.attempt()
        value.close()
        with (self.root / 'started.slot').open('r+b') as handle:
            handle.seek(40)
            handle.write(b'!')
        with self.assertRaises(ValueError):
            s.read_slot(self.root / 'started.slot')

    def test_post_fsync_extent_change_is_refused(self):
        value = self.attempt()
        path, handle, unused = value.handles['terminal']
        with patch.object(s.os, 'fsync', side_effect=lambda fd: handle.truncate(s.SLOT_BYTES - 1)):
            with self.assertRaises(ValueError):
                value.write('terminal', {'small': True})

    def test_exception_notes_and_chain_retained(self):
        first = ValueError('first')
        first.add_note('operator evidence')
        later = RuntimeError('later')
        later.__cause__ = first
        result = s.diagnostic(later)
        self.assertTrue(result['complete'])
        self.assertEqual(result['exceptions'][1]['notes'], ['operator evidence'])

    def test_bad_exception_representation_is_incomplete(self):
        class BadRepr(RuntimeError):
            def __repr__(self):
                raise MemoryError('synthetic formatting failure')
        result = s.diagnostic(BadRepr('first'))
        self.assertFalse(result['complete'])
        self.assertFalse(result['exceptions'][0]['representation_available'])

    def test_cleanup_failure_prevents_success(self):
        value = self.attempt()
        close = value.close
        def failed_close():
            close()
            value.cleanup_errors.append('synthetic close error')
        with patch('experiments.digital_pilot74_guardian_v1.launch_guardian', return_value={}), patch.object(value, 'close', side_effect=failed_close):
            with self.assertRaises(OSError):
                value.run(SPEC, PIN, lambda *args: True)

    def test_cleanup_failure_keeps_primary(self):
        value = self.attempt()
        first = RuntimeError('first')
        close = value.close
        def failed_close():
            close()
            value.cleanup_errors.append('synthetic close error')
        with patch('experiments.digital_pilot74_guardian_v1.launch_guardian', side_effect=first), patch.object(value, 'close', side_effect=failed_close):
            with self.assertRaises(RuntimeError) as raised:
                value.run(SPEC, PIN, lambda *args: True)
        self.assertIs(raised.exception, first)


if __name__ == '__main__':
    unittest.main()
