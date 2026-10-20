"""Prepared startup refusal/renewal contracts. No scheduler installation/reboot."""
import copy
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
import xml.etree.ElementTree as ET

ROOT=Path(__file__).resolve().parents[1]; sys.path.insert(0,str(ROOT))
from experiments.ora_controller_v1 import renew_completed
from experiments.ora_startup_plan_v1 import task_xml,NS
from experiments.ora_session_host_v1 import host,activation


class Startup(unittest.TestCase):
    def state(self):
        return dict(unclean=False,phase='stopped',reason='time-bound',deadline_utc=100,started_utc=0,
            seconds=100,epoch=12,failures=1,recoveries=1,completed_epochs=12,source_offset=24,history=[{'epoch':11}])

    def test_clean_renewal_preserves_memories_cursor_and_lifetime_budget(self):
        state=self.state(); renew_completed(state,101)
        self.assertEqual((state['started_utc'],state['deadline_utc'],state['epoch'],state['window']),(101,201,0,1))
        self.assertEqual((state['failures'],state['recoveries'],state['completed_epochs'],state['source_offset']),(1,1,12,24))
        self.assertEqual(state['lifetime_started_utc'],0)
        renew_completed(state,202); self.assertEqual(state['window'],2); self.assertEqual(state['failures'],1)

    def test_renewal_refuses_early_failed_interrupted_or_stopped_contracts(self):
        for change in ({'unclean':True},{'reason':'operator-stop'},{'reason':'failure-budget'},
                       {'phase':'service-running'},{'failures':3},{'deadline_utc':200}):
            state=self.state(); state.update(change); before=copy.deepcopy(state)
            with self.assertRaises(ValueError): renew_completed(state,101)
            self.assertEqual(state,before)

    def test_export_uses_current_user_least_privilege_disabled_and_no_restart_loop(self):
        for continuous in (False,True):
            raw=task_xml(sys.executable,ROOT,Path('D:/OraLab/state/startup-test'), 'S-1-5-21-1-2-3-1001',continuous)
            tree=ET.fromstring(raw); ns={'t':NS}
            self.assertEqual(tree.find('t:Settings/t:Enabled',ns).text,'false')
            self.assertEqual(tree.find('t:Principals/t:Principal/t:RunLevel',ns).text,'LeastPrivilege')
            self.assertEqual(tree.find('t:Principals/t:Principal/t:LogonType',ns).text,'InteractiveToken')
            self.assertEqual(tree.find('t:Settings/t:MultipleInstancesPolicy',ns).text,'IgnoreNew')
            self.assertIsNone(tree.find('t:Settings/t:RestartOnFailure',ns))
            command=tree.find('t:Actions/t:Exec/t:Command',ns).text
            self.assertEqual(command,sys.executable)
            self.assertNotIn('shutdown',raw.decode().lower())

    def test_disabled_or_missing_activation_refuses_before_native_launch(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)
            with patch('experiments.ora_session_host_v1.run_slice') as native:
                with self.assertRaises(FileNotFoundError): host(root,True)
                (root/'startup-activation.json').write_text('{"enabled":false,"mode":"continuous"}')
                with self.assertRaises(ValueError): host(root,True)
                native.assert_not_called()

    def test_sticky_stop_and_review_hold_refuse_before_activation(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory); (root/'STOP').touch()
            self.assertEqual(host(root,True)['reason'],'operator-stop')
            (root/'STOP').unlink(); (root/'startup-hold.json').write_text('{}')
            with self.assertRaises(RuntimeError): host(root,True)

    def test_simulated_same_boot_is_not_physical_reboot_evidence(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)
            value=dict(enabled=True,mode='reboot-test',source_head='pinned',source_hashes={},before_boot='same',
                       before_owner=dict(pid=999999,creation_filetime_decimal='1'))
            (root/'startup-activation.json').write_text(json.dumps(value))
            with patch('experiments.ora_session_host_v1.subprocess.check_output',return_value='pinned'),patch(
                'experiments.ora_session_host_v1.subprocess.call',return_value=0),patch(
                'experiments.ora_session_host_v1.boot_token',return_value='same'):
                with self.assertRaisesRegex(ValueError,'has not occurred'): activation(root,False)

    def test_host_failure_is_saved_and_retrigger_cannot_clear_hold(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)
            plan=dict(seconds=130,epoch_seconds=30,practice=0,files=[])
            with patch('experiments.ora_session_host_v1.activation',return_value=plan),patch(
                'experiments.ora_session_host_v1.run_slice',side_effect=RuntimeError('fixture failed')) as native:
                with self.assertRaisesRegex(RuntimeError,'fixture failed'): host(root)
                saved=json.loads((root/'host-state.json').read_text())
                self.assertEqual(saved['failures'],1)
                with self.assertRaisesRegex(RuntimeError,'held'): host(root)
                self.assertEqual(native.call_count,1)

    def test_finite_host_retains_global_counter_across_windows(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)
            (root/'controller-state.json').write_text(json.dumps(dict(failures=1,phase='stopped',reason='time-bound',unclean=False)))
            plan=dict(seconds=130,epoch_seconds=30,practice=0,files=[])
            native_result=dict(post_close_processes_exited=True,descendant_leak=False,output_limit_exceeded=False,
                               capture_eof=True,exit_code=0,reason='exit',output='fixture')
            with patch('experiments.ora_session_host_v1.activation',return_value=plan),patch(
                'experiments.ora_session_host_v1.run_slice',side_effect=lambda *a,**kw:dict(native_result)) as native:
                result=host(root,False,2)
                self.assertEqual(result['completed_windows'],2)
                self.assertEqual(result['controller_failures_seen'],1)
                self.assertEqual(native.call_count,2)


if __name__=='__main__': unittest.main()
