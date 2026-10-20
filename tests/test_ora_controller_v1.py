"""Controller failure budgets, simulated boot change, rotation and native STOP.

Boot-token unit cases are not evidence of a physical Windows reboot.
"""
import json
import os
from pathlib import Path
import sys
import tempfile
import threading
import unittest
from unittest.mock import patch,MagicMock

ROOT=Path(__file__).resolve().parents[1]; sys.path.insert(0,str(ROOT))
from experiments.ora_controller_v1 import resume_state,identity,atomic,controller
from experiments.ora_owned_ollama_v1 import OwnedOllama
from experiments.ora_native_slice_v1 import run_slice,Limits


class Controller(unittest.TestCase):
    def test_new_service_hold_ends_controller_without_model_renewal(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory); context=MagicMock(); model=context.__enter__.return_value
            model.start={'pid':123,'creation_filetime_decimal':'1'}
            def native(builder,*args,**kwargs):
                command=builder()
                failed='experiments.ora_supervised_service_v1' in command
                if failed: atomic(root/'service-safety-hold.json',{'kind':'fixture'})
                return dict(exit_code=1 if failed else 0,reason='exit',output='failed fixture' if failed else '{}',
                    post_close_processes_exited=True,descendant_leak=False,output_limit_exceeded=False)
            with patch('experiments.ora_controller_v1.OwnedOllama',return_value=context) as owned,patch(
                'experiments.ora_controller_v1.boot_token',return_value='fixture'),patch(
                'experiments.ora_controller_v1.run_slice',side_effect=native):
                result=controller(root,seconds=160,epoch_seconds=10,practice=0)
            self.assertEqual(result['reason'],'service-safety-hold')
            self.assertEqual(result['failures'],1); self.assertEqual(owned.call_count,1)
            self.assertTrue((root/'controller-service-result.json').exists())

    def test_saved_service_hold_refuses_before_model_launch(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory); (root/'service-safety-hold.json').write_text('{}')
            with patch('experiments.ora_controller_v1.OwnedOllama') as model:
                with self.assertRaisesRegex(RuntimeError,'Saved service safety hold'): controller(root)
                model.assert_not_called()

    def test_monitor_sharing_violation_is_retried_with_fixed_bound(self):
        with tempfile.TemporaryDirectory() as directory:
            target=Path(directory)/'status.json'
            original=os.replace
            with patch('experiments.ora_controller_v1.os.replace',side_effect=[PermissionError('reader'),None]) as replace:
                atomic(target,dict(phase='test'))
                self.assertEqual(replace.call_count,2)
            with patch('experiments.ora_controller_v1.os.replace',side_effect=PermissionError('permanent')) as replace,patch('experiments.ora_controller_v1.time.sleep'):
                with self.assertRaises(PermissionError): atomic(target,{})
                self.assertEqual(replace.call_count,51)

    def state(self,**changes):
        value=dict(failures=0,recoveries=0,started_utc=100,boot='boot-A',unclean=True,
                   owner=dict(pid=987654,creation_filetime_decimal='1'))
        value.update(changes); return value

    @patch('experiments.ora_controller_v1.identity',return_value=None)
    def test_crash_recovery_charges_persistent_budget(self,unused):
        state=resume_state(self.state(),'boot-A',110)
        self.assertEqual((state['failures'],state['recoveries'],state['last_recovery']),
                         (1,1,'controller-loss-same-boot'))
        resume_state(state,'boot-A',111)
        self.assertEqual(state['failures'],2)
        with self.assertRaises(RuntimeError): resume_state(state,'boot-A',112)
        with self.assertRaises(RuntimeError): resume_state(state,'boot-A',113)

    @patch('experiments.ora_controller_v1.identity',return_value=None)
    def test_simulated_boot_change_and_fixed_deadline(self,unused):
        state=self.state(deadline_utc=500)
        resume_state(state,'boot-B',200)
        self.assertEqual(state['last_recovery'],'boot-changed')
        self.assertEqual(state['deadline_utc'],500)
        with self.assertRaises(RuntimeError): resume_state(state,'boot-B',1)

    def test_live_custodian_cannot_be_replaced(self):
        state=self.state(owner=identity(os.getpid()))
        with self.assertRaises(RuntimeError): resume_state(state,'boot-A',110)

    def test_two_slots_and_closed_rotation_preserve_unknown_files(self):
        with tempfile.TemporaryDirectory() as directory:
            server=OwnedOllama(directory,2); self.assertEqual(server.path.name,'model-server-0')
            server.path.mkdir()
            (server.path/'native-result.json').write_text(json.dumps(dict(post_close_processes_exited=True,
                usage=dict(active_before_close=0))))
            unknown=server.path/'operator-notes.txt'; unknown.write_text('preserve')
            with self.assertRaises(ValueError): server.reserve_slot()
            self.assertEqual(unknown.read_text(),'preserve'); unknown.unlink()
            server.reserve_slot()
            self.assertEqual([p.name for p in server.path.iterdir()],['previous-epoch.json'])
            previous=json.loads((server.path/'previous-epoch.json').read_text())
            self.assertEqual(previous['recovery'],'recorded-closed-epoch')

    @patch('experiments.ora_controller_v1.identity',return_value=None)
    def test_abrupt_loss_requires_custodian_and_kernel_custody(self,unused):
        with tempfile.TemporaryDirectory() as directory:
            server=OwnedOllama(directory,0); server.path.mkdir()
            start=dict(pid=999999,creation_filetime_decimal='1',usage=dict(flags=0x2000),
                custodian=dict(pid=999998,creation_filetime_decimal='2'))
            marker=server.path/'suspended-start.json'
            for bad in (0,0x2800,0x3000):
                start['usage']['flags']=bad; marker.write_text(json.dumps(start))
                with self.assertRaises(RuntimeError): server.reserve_slot()
            start['usage']['flags']=0x2000; marker.write_text(json.dumps(start)); server.reserve_slot()
            prior=json.loads((server.path/'previous-epoch.json').read_text())
            self.assertTrue(prior['native_closure_receipt_absent'])

    def test_live_custodian_slot_refused(self):
        with tempfile.TemporaryDirectory() as directory:
            server=OwnedOllama(directory,0); server.path.mkdir()
            (server.path/'suspended-start.json').write_text(json.dumps(dict(custodian=identity(os.getpid()))))
            with self.assertRaises(RuntimeError): server.reserve_slot()

    def test_shutdown_event_closes_real_native_tree(self):
        shutdown=threading.Event(); shutdown.set()
        result=run_slice(lambda *unused:[sys.executable,'-B','-c','import time; time.sleep(30)'],ROOT,
            Limits(memory_bytes=128*1024**2,cpu_seconds=2,processes=2,wall_seconds=5),stop_event=shutdown)
        self.assertEqual(result['reason'],'controller-stop')
        self.assertTrue(result['post_close_processes_exited']); self.assertTrue(result['capture_eof'])


if __name__=='__main__': unittest.main()
