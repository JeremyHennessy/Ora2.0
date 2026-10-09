import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from unittest.mock import Mock

from experiments import isolation_capability as isolation
from experiments.isolation_capability_audit import audit


class IsolationPolicyTests(unittest.TestCase):
    def test_termination_race_requires_signaled_process(self):
        kernel=Mock()
        kernel.TerminateProcess.return_value=False
        kernel.WaitForSingleObject.return_value=0
        with patch.object(isolation.c,'get_last_error',return_value=5,create=True):
            isolation.terminate_and_wait(kernel,123)
            kernel.WaitForSingleObject.return_value=258
            with self.assertRaisesRegex(RuntimeError,'Cannot establish process exit'):
                isolation.terminate_and_wait(kernel,123)
        with patch.object(isolation.c,'get_last_error',return_value=6,create=True),patch.object(isolation.c,'WinError',return_value=OSError('invalid handle'),create=True):
            with self.assertRaisesRegex(OSError,'invalid handle'):
                isolation.terminate_and_wait(kernel,123)

    def test_non_windows_cannot_start_command(self):
        with patch.object(isolation.os, 'name', 'posix'):
            with self.assertRaisesRegex(OSError, 'no command started'):
                isolation.libraries()

    def test_missing_evidence_is_rejected(self):
        # Windows laboratory harness supplies a D: temporary root.
        with tempfile.TemporaryDirectory(dir=os.environ.get('ORA_TEST_TEMP')) as folder:
            with self.assertRaises(OSError):
                audit(folder, folder, '0'*40)

    @unittest.skipUnless(os.name == 'nt', 'Native layout requires Windows wchar/DWORD ABI')
    def test_native_64_bit_layout(self):
        import ctypes
        self.assertEqual(ctypes.sizeof(isolation.Startup), 104)
        self.assertEqual(ctypes.sizeof(isolation.StartupEx), 112)
        self.assertEqual(ctypes.sizeof(isolation.Capabilities), 24)
        self.assertEqual(ctypes.sizeof(isolation.Process), 24)
