"""NEW offline failure-state checks: no current_birth or native/World calls."""
import importlib.util
from pathlib import Path
import unittest
from unittest.mock import Mock, patch

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('first_failure_candidate', ROOT/'tools/eka1_native_owner_candidate.py')
source = importlib.util.module_from_spec(spec)
spec.loader.exec_module(source)


class FirstFailureChecks(unittest.TestCase):
    def owner(self, ledger_error=None, fd=73):
        # Bypass constructor deliberately: pure state fixture, not owner proof.
        obj = object.__new__(source.NativeOwnerCandidate)
        obj._closed = False; obj._failed = None; obj._cleanup_errors = []
        obj._fd = fd; obj._ledger = Mock()
        obj._ledger.close.side_effect = ledger_error
        source._active = obj
        return obj

    def tearDown(self): source._active = None

    def test_first_cause_survives_later_refusal(self):
        obj = self.owner()
        with patch.object(source.os, 'close') as close:
            obj._fail(ValueError('original mismatch'))
            obj._fail(RuntimeError('owner already closed'))
        self.assertEqual(obj._failed, 'ValueError: original mismatch')
        self.assertEqual(obj._cleanup_errors, [])
        close.assert_called_once_with(73)
        obj._ledger.close.assert_called_once()

    def test_both_cleanup_failures_retained_without_replacing_primary(self):
        obj = self.owner(OSError('ledger close'))
        with patch.object(source.os, 'close', side_effect=OSError('fd close')) as close:
            obj._fail(ValueError('primary'))
            obj._fail(RuntimeError('later'))
        self.assertEqual(obj._failed, 'ValueError: primary')
        self.assertEqual(obj._cleanup_errors, ['OSError: ledger close', 'OSError: fd close'])
        self.assertEqual(obj._fd, 73)  # Unknown physical closure, no fake success.
        self.assertTrue(obj._closed); self.assertIsNone(source._active)
        close.assert_called_once()

    def test_direct_close_raises_first_cleanup_after_attempting_both(self):
        obj = self.owner(OSError('first cleanup'))
        with patch.object(source.os, 'close', side_effect=OSError('second cleanup')):
            with self.assertRaisesRegex(OSError, 'first cleanup'): obj.close()
        self.assertEqual(len(obj._cleanup_errors), 2)
        self.assertIsNone(obj._failed)  # No invented earlier execution failure.

    def test_failed_ledger_close_still_attempts_owner_fd_once(self):
        obj = self.owner(OSError('ledger'))
        with patch.object(source.os, 'close') as close:
            obj._fail(TimeoutError('deadline'))
            obj.close()
        self.assertEqual(obj._failed, 'TimeoutError: deadline')
        self.assertEqual(obj._cleanup_errors, ['OSError: ledger'])
        self.assertIsNone(obj._fd); close.assert_called_once_with(73)

    def test_constructor_failure_without_ledger_or_fd(self):
        obj = self.owner(fd=None); obj._ledger = None
        with patch.object(source.os, 'close') as close:
            obj._fail(OSError('open refused'))
        self.assertEqual(obj._failed, 'OSError: open refused')
        self.assertEqual(obj._cleanup_errors, []); close.assert_not_called()


if __name__ == '__main__': unittest.main()
