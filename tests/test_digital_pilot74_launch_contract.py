"""Exercise actual drafted launch orchestration with fake kernel and Job.

No Ora imports, native process creation, VM or world. Real anonymous pipes only.
"""
import ast
import ctypes
from ctypes import wintypes as wt
import os
from pathlib import Path
import struct
import sys
from types import ModuleType, SimpleNamespace
import unittest
from unittest.mock import Mock, patch

SOURCE = Path(__file__).resolve().parents[1] / 'experiments/digital_pilot74_guardian_v1.py'
tree = ast.parse(SOURCE.read_bytes())
function = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == 'launch_guardian')


class LaunchContract(unittest.TestCase):
    def setup_launch(self, resume=1):
        calls = []
        closed = []
        k = SimpleNamespace()
        def create(app, cmd, pa, ta, inherit, flags, env, cwd, start, pi):
            calls.append(dict(flags=flags, inherit=inherit, command=cmd.value))
            pi._obj.process = 101; pi._obj.thread = 102; pi._obj.pid = 103
            return 1
        k.CreateProcessW = Mock(side_effect=create)
        k.InitializeProcThreadAttributeList = Mock(return_value=1)
        k.UpdateProcThreadAttribute = Mock(return_value=1)
        k.SetHandleInformation = Mock(return_value=1)
        k.GetTickCount64 = Mock(return_value=4000000)
        k.ResumeThread = Mock(return_value=resume)
        k.WaitForSingleObject = Mock(return_value=0)
        k.GetExitCodeProcess = Mock(return_value=1)
        k.CloseHandle = Mock(side_effect=lambda h: closed.append(h) or 1)
        k.DeleteProcThreadAttributeList = Mock()
        k.TerminateProcess = Mock(return_value=1)
        job = SimpleNamespace(handle=100, close=Mock())
        caps = ModuleType('experiments.process_limits')
        caps.Limits = lambda **kw: kw
        caps.Job = lambda limits: job
        package = ModuleType('experiments'); package.process_limits = caps
        registration = dict(guardian=dict(artifact=dict(path='D:/fixture.exe')),
                            source_root='D:/fixture')
        def checked(ok):
            if not ok:
                raise OSError('injected native failure')
        ns = dict(ctypes=ctypes, wt=wt, os=os, struct=struct, MIB=1024**2,
                  validate_host_registration=lambda *a: registration,
                  _kernel=lambda: k, checked=checked, _birth=lambda *a: 42)
        exec(compile(ast.Module(body=[function], type_ignores=[]), str(SOURCE), 'exec'), ns)
        return ns['launch_guardian'], k, calls, closed, caps, package, job

    def test_root_is_detached_suspended_and_explicitly_job_bound(self):
        launch, k, calls, closed, caps, package, job = self.setup_launch()
        with patch.dict(sys.modules, {'experiments': package, 'experiments.process_limits': caps}):
            result = launch(dict(path='D:/registration.json', extent=2, sha256='a'*64), 'a'*64)
        self.assertEqual(calls[0]['flags'], 0x80000 | 0x4 | 0x8)
        self.assertTrue(calls[0]['inherit'])
        attributes = [call.args[2] for call in k.UpdateProcThreadAttribute.call_args_list]
        self.assertEqual(attributes, [0x2000D, 0x20002])
        self.assertEqual(result['creation_filetime_decimal'], '42')
        self.assertFalse(result['publication_accepted'])
        self.assertFalse(result['live_attachment'])
        self.assertIn(101, closed); self.assertIn(102, closed)

    def test_resume_failure_is_not_success_and_closes_original_handles(self):
        launch, k, calls, closed, caps, package, job = self.setup_launch(resume=0)
        with patch.dict(sys.modules, {'experiments': package, 'experiments.process_limits': caps}):
            with self.assertRaises(AssertionError):
                launch(dict(path='D:/registration.json', extent=2, sha256='a'*64), 'a'*64)
        self.assertIn(101, closed); self.assertIn(102, closed)
        job.close.assert_called_once()
        k.DeleteProcThreadAttributeList.assert_called_once()

    def test_partial_birth_handoff_never_resumes_child(self):
        launch, k, calls, closed, caps, package, job = self.setup_launch()
        with patch.dict(sys.modules, {'experiments': package, 'experiments.process_limits': caps}):
            with patch.object(os, 'write', return_value=3):
                with self.assertRaisesRegex(OSError, 'Partial external birth'):
                    launch(dict(path='D:/registration.json', extent=2, sha256='a'*64), 'a'*64)
        k.ResumeThread.assert_not_called()
        self.assertIn(101, closed); self.assertIn(102, closed)
        job.close.assert_called_once()

    def test_failed_creation_never_hands_off_or_resumes(self):
        launch, k, calls, closed, caps, package, job = self.setup_launch()
        k.CreateProcessW.side_effect = lambda *args: 0
        with patch.dict(sys.modules, {'experiments': package, 'experiments.process_limits': caps}):
            with self.assertRaisesRegex(OSError, 'injected native'):
                launch(dict(path='D:/registration.json', extent=2, sha256='a'*64), 'a'*64)
        k.ResumeThread.assert_not_called()
        self.assertNotIn(101, closed)
        job.close.assert_called_once()

    def test_unknown_deadline_closure_never_returns_success(self):
        launch, k, calls, closed, caps, package, job = self.setup_launch()
        k.WaitForSingleObject.return_value = 258
        with patch.dict(sys.modules, {'experiments': package, 'experiments.process_limits': caps}):
            with self.assertRaisesRegex(RuntimeError, 'closure UNKNOWN'):
                launch(dict(path='D:/registration.json', extent=2, sha256='a'*64), 'a'*64)
        k.TerminateProcess.assert_called_once_with(101, 125)
        self.assertIn(101, closed); self.assertIn(102, closed)


if __name__ == '__main__':
    unittest.main()
