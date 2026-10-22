"""Real Windows Job containment for new service slice launcher; no Worlds."""
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from experiments.ora_native_slice_v1 import run_slice, Limits
from experiments.ora_supervised_service_v1 import supervise
from experiments.process_limits import Job


@unittest.skipUnless(os.name=='nt','Windows Job enforcement')
class NativeService(unittest.TestCase):
    def test_exited_root_after_waited_descendant_can_settle(self):
        original=Job.usage; original_pids=Job.pids; injected=[]; starts=[]
        def pids(job):
            if injected and not injected[-1].get('read'):
                injected[-1]['read']=True; return [starts[0]['pid']]
            return [] if injected else original_pids(job)
        def usage(job):
            value=original(job)
            if value['started_processes']>1 and not injected:
                injected.append({}); return dict(value,active_before_close=1)
            return dict(value,active_before_close=0) if injected else value
        with patch.object(Job,'usage',usage),patch.object(Job,'pids',pids):
            result=run_slice(lambda *unused:[sys.executable,'-B','-c',
                'import subprocess,sys; subprocess.run([sys.executable,"-c","pass"],check=True)'],ROOT,
                Limits(memory_bytes=128*1024**2,cpu_seconds=2,processes=3,wall_seconds=3),on_start=starts.append)
        self.assertTrue(injected)
        self.assertFalse(result['descendant_leak'])
        self.assertTrue(result['exit_observation']['single_root_grace_used'])
        self.assertTrue(result['post_close_processes_exited'])

    def test_nested_accounting_with_missing_root_or_multiple_active_is_rejected(self):
        for count in (1,2):
            original=Job.usage; original_pids=Job.pids; injected=[]; starts=[]
            def usage(job):
                value=original(job)
                if value['started_processes']>1 and value['active_before_close']==0 and not injected:
                    injected.append(True); return dict(value,active_before_close=count)
                return value
            def pids(job):
                if injected: return [] if count==1 else [starts[0]['pid']]
                return original_pids(job)
            with patch.object(Job,'usage',usage),patch.object(Job,'pids',pids):
                result=run_slice(lambda *unused:[sys.executable,'-B','-c',
                    'import subprocess,sys; subprocess.run([sys.executable,"-c","pass"],check=True)'],ROOT,
                    Limits(memory_bytes=128*1024**2,cpu_seconds=2,processes=3,wall_seconds=3),on_start=starts.append)
            self.assertTrue(injected)
            self.assertTrue(result['descendant_leak'])
            self.assertFalse(result['exit_observation']['single_root_grace_used'])

    def test_accounting_that_never_settles_is_not_accepted(self):
        original=Job.usage
        def usage(job):
            value=original(job)
            return dict(value,active_before_close=1) if value['started_processes']==1 else value
        with patch.object(Job,'usage',usage):
            with self.assertRaisesRegex(RuntimeError,'Job closure unknown'): self.run_code('pass')

    def test_signaled_only_process_with_one_stale_accounting_read_settles(self):
        original=Job.usage; injected=[]
        def usage(job):
            value=original(job)
            if value['started_processes']==1 and value['active_before_close']==0 and not injected:
                injected.append(True); return dict(value,active_before_close=1)
            return value
        with patch.object(Job,'usage',usage): result=self.run_code('pass')
        self.assertTrue(injected)
        self.assertFalse(result['descendant_leak'])
        self.assertTrue(result['exit_observation']['single_root_grace_used'])
        self.assertTrue(result['post_close_processes_exited'])

    def test_genuine_live_child_gets_no_single_root_grace(self):
        result=self.run_code('import subprocess,sys; subprocess.Popen([sys.executable,"-c","import time; time.sleep(30)"])')
        self.assertGreater(result['exit_observation']['initial_usage']['started_processes'],1)
        self.assertFalse(result['exit_observation']['single_root_grace_used'])
        self.assertTrue(result['descendant_leak']); self.assertTrue(result['post_close_processes_exited'])

    def test_rejected_worker_receipt_is_retained_and_hold_prevents_retry(self):
        for flag in ('descendant_leak','output_limit_exceeded'):
            with tempfile.TemporaryDirectory() as directory:
                root=Path(directory)
                result=dict(output='failed-worker-output',descendant_leak=False,output_limit_exceeded=False,
                    post_close_processes_exited=True,capture_eof=True,exit_code=0,exit_observation={'initial_pids':[123]})
                result[flag]=True
                with patch('experiments.ora_supervised_service_v1.run_slice',return_value=result) as native:
                    with self.assertRaisesRegex(RuntimeError,flag+'=True'): supervise(root,seconds=1)
                    saved=json.loads((root/'service-safety-hold.json').read_text())
                    self.assertTrue(saved['native'][flag]); self.assertEqual(saved['native']['exit_observation']['initial_pids'],[123])
                    self.assertEqual((root/'service-output-0.log').read_text(),'failed-worker-output')
                    self.assertTrue((root/'supervisor-last-attempt.json').exists())
                    with self.assertRaisesRegex(RuntimeError,'no worker started'): supervise(root,seconds=1)
                    self.assertEqual(native.call_count,1)

    def test_native_exception_is_saved_as_hold(self):
        with tempfile.TemporaryDirectory() as directory:
            with patch('experiments.ora_supervised_service_v1.run_slice',side_effect=RuntimeError('closure unknown')):
                with self.assertRaisesRegex(RuntimeError,'closure unknown'): supervise(directory,seconds=1)
            value=json.loads((Path(directory)/'service-safety-hold.json').read_text())
            self.assertEqual(value['kind'],'native-launch-or-closure-error')

    def run_code(self,code,wall=3):
        return run_slice(lambda *unused:[sys.executable,'-B','-c',code],ROOT,
            Limits(memory_bytes=128*1024**2,cpu_seconds=2,processes=3,wall_seconds=wall))

    def test_success_and_outside_wall_stop(self):
        result=self.run_code('print("bounded")')
        self.assertEqual(result['exit_code'],0)
        self.assertEqual(result['output'].strip(),'bounded')
        self.assertEqual(result['usage']['active_before_close'],0)
        stopped=self.run_code('import time; time.sleep(30)',.2)
        self.assertEqual(stopped['reason'],'wall-limit')
        self.assertTrue(stopped['post_close_processes_exited'])

    def test_explicit_child_environment_and_cpu_hard_rate(self):
        starts=[]
        result=run_slice(lambda *unused:[sys.executable,'-B','-c','import os; print(os.environ["ORA_TEST_ENV"])'],ROOT,
            Limits(memory_bytes=128*1024**2,cpu_seconds=2,processes=2,wall_seconds=5),
            environment={'ORA_TEST_ENV':'private-child-environment'},cpu_rate=2000,on_start=starts.append)
        self.assertEqual(result['exit_code'],0)
        self.assertEqual(result['output'].strip(),'private-child-environment')
        self.assertEqual(result['cpu_rate'],dict(flags=5,rate=2000))
        self.assertEqual(starts[0]['cpu_rate'],result['cpu_rate'])
        self.assertNotIn('ORA_TEST_ENV',os.environ)

    def test_descendant_cannot_survive_leader_exit(self):
        result=self.run_code('import subprocess,sys; subprocess.Popen([sys.executable,"-c","import time; time.sleep(30)"])')
        self.assertTrue(result['descendant_leak'])
        self.assertEqual(result['usage']['active_before_close'],0)
        self.assertTrue(result['capture_eof'])

    def test_output_flood_is_capped(self):
        result=self.run_code('import os; os.write(1,b"x"*(2*1024**2))')
        self.assertTrue(result['output_limit_exceeded'])
        self.assertEqual(result['retained_bytes'],1024**2)
        self.assertEqual(result['usage']['active_before_close'],0)

    def test_supervisor_renews_slices_and_stops_retrying_errors(self):
        with tempfile.TemporaryDirectory() as folder:
            result=supervise(folder,seconds=30,slice_seconds=.5,max_restarts=0,max_attempts=2)
            self.assertEqual(len(result['attempts']),2)
            self.assertEqual(result['reason'],'attempt-bound')
            self.assertTrue(result['all_attempts_closed'])
            self.assertEqual(result['crash_failures'],0)
            self.assertTrue((Path(folder)/'backups/snapshot-0.sqlite3').exists())
            self.assertTrue((Path(folder)/'backups/snapshot-1.sqlite3').exists())
        with tempfile.TemporaryDirectory() as folder:
            (Path(folder)/'inbox.json').write_text('not valid json')
            result=supervise(folder,seconds=5,slice_seconds=1,max_restarts=1)
            self.assertEqual(result['reason'],'retry-bound')
            self.assertEqual(result['crash_failures'],2)
            self.assertEqual(len(result['attempts']),2)


if __name__=='__main__': unittest.main()
