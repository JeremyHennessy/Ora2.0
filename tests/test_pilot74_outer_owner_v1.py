"""Mocked Win32 owner-boundary regressions;zero native calls or Worlds."""
import sys
import unittest
from pathlib import Path
from unittest.mock import Mock, patch
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from experiments import digital_pilot74_outer_owner_v1 as o

REQUEST = dict(command=['D:/synthetic/python.exe', '-B', 'sealed-caller.py'], cwd='D:/synthetic')


@unittest.skipUnless(o.os.name == 'nt', 'Windows path and structure semantics;all kernel calls mocked')
class Outer(unittest.TestCase):
    def setup_boundary(self):
        k = Mock()
        k.GetTickCount64.side_effect = [100, 101, 102, 103, 104, 105]
        def attributes(*args):
            args[-1]._obj.value = 128
            return 1
        k.InitializeProcThreadAttributeList.side_effect = attributes
        k.UpdateProcThreadAttribute.return_value = 1
        def create(*args):
            self.assertFalse(args[4])
            self.assertEqual(args[5], 0x80000 | 0x4 | 0x8)
            pi = args[-1]._obj
            pi.process = 222
            pi.thread = 333
            pi.pid = 444
            return 1
        k.CreateProcessW.side_effect = create
        k.GetProcessId.return_value = 444
        def member(process, job, result):
            result._obj.value = True
            return 1
        k.IsProcessInJob.side_effect = member
        def image(process, flags, buffer, length):
            buffer.value = REQUEST['command'][0]
            return 1
        k.QueryFullProcessImageNameW.side_effect = image
        k.ResumeThread.return_value = 1
        k.WaitForSingleObject.return_value = 0
        k.CloseHandle.return_value = 1
        k.GetExitCodeProcess.return_value = 1
        job = Mock()
        job.handle = 999
        usage = dict(configured_memory_bytes=2048*o.MIB, configured_processes=4,
            configured_cpu_ticks=2400*10_000_000, flags=0x220c, active_before_close=0)
        job.usage.return_value = usage
        job.pids.return_value = []
        return k, job

    def invoke(self, k, job, admission=lambda r: True):
        with patch.object(o.win, 'kernel', return_value=k), patch.object(o.win, 'birth', return_value=555), patch.object(o.caps, 'Job', return_value=job):
            return o.launch(REQUEST, admission)

    def test_refusal_creates_no_job_or_process(self):
        k, job = self.setup_boundary()
        with self.assertRaises(ValueError):
            self.invoke(k, job, lambda r: False)
        k.CreateProcessW.assert_not_called()

    def test_absolute_deadline_includes_admission(self):
        k, job = self.setup_boundary()
        k.GetTickCount64.side_effect = [100, 3600100]
        with self.assertRaises(TimeoutError):
            self.invoke(k, job)
        k.CreateProcessW.assert_not_called()

    def test_suspended_atomic_assignment_and_aggregate_result(self):
        k, job = self.setup_boundary()
        result = self.invoke(k, job)
        self.assertTrue(result['closure_observed'])
        self.assertEqual(result['elapsed_ms'], 5)
        self.assertFalse(result['publication_accepted'])
        k.WaitForSingleObject.assert_called_once_with(222, 3599996)
        k.UpdateProcThreadAttribute.assert_called_once()

    def test_deadline_failure_terminates_outer_job_without_extension(self):
        k, job = self.setup_boundary()
        k.WaitForSingleObject.return_value = 258
        with self.assertRaises(TimeoutError) as raised:
            self.invoke(k, job)
        job.terminate.assert_called_once()
        self.assertTrue(raised.exception.guardian_failure_evidence['termination_requested'])
        self.assertFalse(raised.exception.guardian_failure_evidence['closure_observed'])
        waits = [call.args[1] for call in k.WaitForSingleObject.call_args_list]
        self.assertEqual(waits[0], 3599996)
        self.assertTrue(all(v == 0 for v in waits[1:]))

    def test_active_descendants_refused(self):
        k, job = self.setup_boundary()
        job.usage.return_value['active_before_close'] = 1
        with self.assertRaises(RuntimeError):
            self.invoke(k, job)
        job.terminate.assert_called_once()

    def test_breakaway_limit_readback_refused_before_resume(self):
        k, job = self.setup_boundary()
        job.usage.return_value['flags'] |= 0x800
        with self.assertRaises(ValueError):
            self.invoke(k, job)
        k.ResumeThread.assert_not_called()
        job.terminate.assert_called_once()

    def test_create_error_survives_termination_and_cleanup_errors(self):
        k, job = self.setup_boundary()
        first = RuntimeError('synthetic create')
        k.CreateProcessW.side_effect = first
        job.terminate.side_effect = OSError('synthetic termination')
        job.close.side_effect = OSError('synthetic cleanup')
        with self.assertRaises(RuntimeError) as raised:
            self.invoke(k, job)
        self.assertIs(raised.exception, first)
        self.assertTrue(any('cleanup' in n for n in first.__notes__))

    def test_diagnostic_failure_cannot_skip_termination(self):
        k, job = self.setup_boundary()
        first = RuntimeError('synthetic create')
        k.CreateProcessW.side_effect = first
        with patch.object(o, 'failure_observation', side_effect=MemoryError('synthetic diagnostic')):
            with self.assertRaises(RuntimeError) as raised:
                self.invoke(k, job)
        self.assertIs(raised.exception, first)
        job.terminate.assert_called_once()


if __name__ == '__main__':
    unittest.main()
