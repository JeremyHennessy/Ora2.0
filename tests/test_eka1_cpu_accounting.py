"""Offline raw-counter/closure failure fixtures; no native processes or World."""
import copy
import ctypes
import json
import hashlib
import os
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import Mock,patch
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from tools import eka1_cpu_accounting as cpu
from tools import eka1_native_probe as probe


def snapshot(u=0,k=0):
    return dict(user_ticks=u,kernel_ticks=k,period_user_ticks=u,period_kernel_ticks=k,
                active=0,total_processes=2 if u else 0,cpu_limit_ticks=80000000,
                memory_limit=256*1024**2,process_limit=4,flags=0x220c)


class CpuChecks(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(dir=ROOT);self.out=Path(self.tmp.name)
        p=self.out/'ledger';self.fd=os.open(p,os.O_CREAT|os.O_EXCL|os.O_RDWR|os.O_BINARY,0o600)
        os.write(self.fd,b'reserved');os.fsync(self.fd);s=os.fstat(self.fd)
        self.owner=SimpleNamespace(_fd=self.fd,_path=p,_physical=(s.st_dev,s.st_ino),
                                   _birth=(7,int(hashlib.sha256(str(self.out).encode()).hexdigest()[:12],16)),_assignment=hashlib.sha256(str(self.out).encode()).hexdigest(),_ledger=SimpleNamespace(_bytes=8),_closed=False,_failed=None)
        self.birth_patch=patch.object(cpu,'current_birth',return_value=self.owner._birth);self.birth_patch.start()
        self.job=Mock(handle=123);self.job.usage.return_value={'active_before_close':0}
        self.reader=patch.object(cpu,'root_snapshot',return_value=snapshot());self.read=self.reader.start()
        self.meter=cpu.RootCpuAttempt(self.job,self.out,3,self.owner,probe.save)
        self.guardian=dict(pid=11,birth='333',signaled=True,root_member=True,user_ticks=100,kernel_ticks=50)
        self.private=dict(pid=12,birth='444',closed=True,total_processes=1,active_processes=0,user_ticks=1000,kernel_ticks=500,
                          leader_signaled=True,leader_root_member=True,leader_private_member=True,
                          leader_user_ticks=1000,leader_kernel_ticks=500)
        self.read.return_value=snapshot(1100,550)
    def tearDown(self):
        self.reader.stop();self.birth_patch.stop();os.close(self.fd);self.tmp.cleanup()
    def finish(self,errors=()):return self.meter.finish(self.guardian,self.private,errors)
    def final(self):return json.loads((self.out/'3.cpu-final.json').read_text())
    def test_root_debited_once_private_not_added(self):
        r=self.finish();self.assertEqual(r['debit_ticks'],1650)
        before=(self.out/'3.cpu-final.json').read_bytes()
        with self.assertRaisesRegex(cpu.CpuAccountingFailure,'consumed'):self.finish()
        self.assertEqual((self.out/'3.cpu-final.json').read_bytes(),before)
    def test_third_zero_cpu_birth_fails_but_full_measured_debit_remains(self):
        self.read.return_value['total_processes']=3
        with self.assertRaisesRegex(cpu.CpuAccountingFailure,'Root successful-birth'):self.finish()
        self.assertEqual(self.final()['debit_ticks'],1650)
        self.assertEqual(self.final()['status'],'UNKNOWN_UNRESOLVED')
    def test_private_extra_birth_fails_without_refunding_root(self):
        self.private['total_processes']=2
        with self.assertRaisesRegex(cpu.CpuAccountingFailure,'Sole private'):self.finish()
        self.assertEqual(self.final()['debit_ticks'],1650)
    def test_missing_private_cardinality_is_not_imputed(self):
        del self.private['total_processes']
        with self.assertRaisesRegex(cpu.CpuAccountingFailure,'Sole private'):self.finish()
        self.assertEqual(self.final()['debit_ticks'],1650)
    def test_same_guardian_and_child_birth_fails(self):
        self.private.update(pid=self.guardian['pid'],birth=self.guardian['birth'])
        with self.assertRaisesRegex(cpu.CpuAccountingFailure,'distinct retained births'):self.finish()
        self.assertEqual(self.final()['debit_ticks'],1650)
    def test_overrun_retains_full_debit_and_terminal_failure(self):
        self.private.update(user_ticks=20625000,leader_user_ticks=20625000)
        self.read.return_value=snapshot(20625100,550)
        with self.assertRaises(cpu.CpuBudgetExceeded):self.finish()
        self.assertEqual(self.final()['status'],'FAIL_CPU_BUDGET')
        self.assertEqual(self.final()['debit_ticks'],20625650)
        with self.assertRaisesRegex(cpu.CpuAccountingFailure,'consumed'):self.finish()
    def test_missing_kernel_counter_never_zero(self):
        del self.read.return_value['kernel_ticks']
        with self.assertRaises(KeyError):self.finish()
        self.assertIsNone(self.final()['debit_ticks']);self.assertEqual(self.final()['status'],'UNKNOWN_UNRESOLVED')
    def test_bad_counter_types_or_sign_terminal(self):
        for bad in (-1,True,1.0,None,2**63):
            with self.subTest(bad=bad):
                with self.assertRaises(cpu.CpuAccountingFailure):cpu.ticks(bad)
        self.read.return_value['kernel_ticks']=-1
        with self.assertRaises(cpu.CpuAccountingFailure):self.finish()
        self.assertIsNone(self.final()['debit_ticks'])
    def test_epoch_reset_or_readback_change_refused(self):
        self.read.return_value['period_user_ticks']=0
        with self.assertRaisesRegex(cpu.CpuAccountingFailure,'epoch'):self.finish()
        self.assertIsNone(self.final()['debit_ticks'])
    def test_root_limit_change_refused(self):
        self.read.return_value['cpu_limit_ticks']=80000001
        with self.assertRaisesRegex(cpu.CpuAccountingFailure,'readback'):self.finish()
    def test_unexpected_breakaway_flag_refused(self):
        self.read.return_value['flags']|=0x800
        with self.assertRaisesRegex(cpu.CpuAccountingFailure,'readback'):self.finish()
        self.assertIsNone(self.final()['debit_ticks'])
    def test_nested_inconsistency_retains_known_root_cost(self):
        self.private['kernel_ticks']=501
        with self.assertRaises(cpu.CpuAccountingFailure):self.finish()
        self.assertEqual(self.final()['debit_ticks'],1650)
        self.assertEqual(self.final()['status'],'UNKNOWN_UNRESOLVED')
    def test_live_or_unmeasured_private_birth_refused(self):
        self.private['leader_signaled']=False
        with self.assertRaisesRegex(cpu.CpuAccountingFailure,'custody'):self.finish()
    def test_missing_private_counters_terminal_with_known_root_debit(self):
        self.private=None
        with self.assertRaisesRegex(cpu.CpuAccountingFailure,'Private final'):self.finish()
        self.assertEqual(self.final()['debit_ticks'],1650)
    def test_live_root_has_no_final_debit(self):
        self.read.return_value['active']=1
        with self.assertRaisesRegex(cpu.CpuAccountingFailure,'closure'):self.finish()
        self.assertIsNone(self.final()['debit_ticks'])
    def test_lost_root_handle_custody_has_no_invented_cost(self):
        self.job.handle=456
        with self.assertRaisesRegex(cpu.CpuAccountingFailure,'custody'):self.finish()
        self.assertIsNone(self.final()['debit_ticks'])
    def test_changed_assignment_or_physical_extent_refused(self):
        os.write(self.fd,b'x');os.fsync(self.fd)
        with self.assertRaisesRegex(cpu.CpuAccountingFailure,'ledger custody'):self.finish()
    def test_same_size_ledger_corruption_refused(self):
        os.lseek(self.fd,0,os.SEEK_SET);os.write(self.fd,b'corrupt!');os.fsync(self.fd)
        self.assertEqual(os.fstat(self.fd).st_size,8)
        with self.assertRaisesRegex(cpu.CpuAccountingFailure,'ledger bytes'):self.finish()
        self.assertIsNone(self.final()['debit_ticks'])
    def test_final_write_interruption_pending_survives_without_retry(self):
        self.meter.save=Mock(side_effect=OSError('partial final write'))
        with self.assertRaisesRegex(OSError,'partial final'):self.finish()
        self.assertTrue((self.out/'3.cpu-pending.json').exists())
        with self.assertRaisesRegex(cpu.CpuAccountingFailure,'consumed'):self.finish()
        self.meter.save.assert_called_once()
    def test_overrun_and_final_write_failure_preserve_first_cause(self):
        self.private.update(user_ticks=20625000,leader_user_ticks=20625000)
        self.read.return_value=snapshot(20625100,550)
        self.meter.save=Mock(side_effect=OSError('receipt unavailable'))
        with self.assertRaises(cpu.CpuBudgetExceeded) as caught:self.finish()
        self.assertIsInstance(caught.exception.__cause__,OSError)
        self.assertEqual(caught.exception.cpu_observation['debit_ticks'],20625650)
        self.assertEqual(caught.exception.cpu_observation['persistence'],'FINAL_WRITE_INCOMPLETE_NO_RETRY')
        self.assertTrue((self.out/'3.cpu-pending.json').exists())
        with self.assertRaisesRegex(cpu.CpuAccountingFailure,'consumed'):self.finish()
        self.meter.save.assert_called_once()
    def test_constructor_read_failure_has_durable_pending_before_query(self):
        other=self.out/'other';other.mkdir()
        owner=copy.copy(self.owner);owner._assignment=hashlib.sha256(str(other).encode()).hexdigest()
        def read(job):
            self.assertTrue((other/'3.cpu-pending.json').exists());raise OSError('query failed')
        with patch.object(cpu,'root_snapshot',side_effect=read):
            with self.assertRaisesRegex(OSError,'query failed'):cpu.RootCpuAttempt(Mock(handle=456),other,3,owner,probe.save)
        self.assertFalse((other/'3.cpu-final.json').exists())
    def test_reopening_pending_refused_before_any_query(self):
        with self.assertRaisesRegex(cpu.CpuAccountingFailure,'consumed'):cpu.RootCpuAttempt(self.job,self.out,3,self.owner,probe.save)
    def test_alternate_root_or_output_cannot_duplicate_assignment(self):
        other=self.out/'other';other.mkdir()
        with self.assertRaisesRegex(cpu.CpuAccountingFailure,'consumed'):cpu.RootCpuAttempt(Mock(handle=456),other,3,self.owner,probe.save)
    def test_alternate_wrapper_assignment_cannot_duplicate_kernel_root(self):
        other=self.out/'other';other.mkdir();owner=copy.copy(self.owner);owner._assignment='b'*64
        with self.assertRaisesRegex(cpu.CpuAccountingFailure,'consumed'):cpu.RootCpuAttempt(Mock(handle=123),other,3,owner,probe.save)
    def test_actual_owner_birth_change_refuses_final_charge(self):
        with patch.object(cpu,'current_birth',return_value=(8,888)):
            with self.assertRaisesRegex(cpu.CpuAccountingFailure,'custody'):self.finish()
        self.assertIsNone(self.final()['debit_ticks'])
    def kernel_fixture(self):
        k=Mock();k.WaitForSingleObject.return_value=0;k.GetProcessId.return_value=11
        def times(h,created,ended,kernel,user):
            for p,n in ((created,333),(ended,999),(kernel,50),(user,100)):
                ctypes.cast(p,ctypes.POINTER(ctypes.c_ulonglong)).contents.value=n
            return True
        def member(h,j,p):ctypes.cast(p,ctypes.POINTER(ctypes.c_int)).contents.value=1;return True
        k.GetProcessTimes.side_effect=times;k.IsProcessInJob.side_effect=member
        return k
    def test_failed_termination_still_measures_and_seals(self):
        self.job.terminate.side_effect=OSError('terminate failed')
        with self.assertRaisesRegex(cpu.CpuAccountingFailure,'Termination'):
            probe.settle_root(self.job,self.meter,self.kernel_fixture(),SimpleNamespace(process=22,pid=11),'333',self.private,0)
        self.job.terminate.assert_called_once();self.assertEqual(self.final()['debit_ticks'],1650)
        self.assertIn('terminate failed',str(self.final()['control_errors']))
    def test_unresponsive_guardian_keeps_unresolved_cost_receipt(self):
        k=self.kernel_fixture();k.WaitForSingleObject.return_value=258
        with self.assertRaises(cpu.CpuAccountingFailure):probe.settle_root(self.job,self.meter,k,SimpleNamespace(process=22,pid=11),'333',self.private,0)
        self.assertEqual(self.final()['status'],'UNKNOWN_UNRESOLVED')
    def test_retained_guardian_birth_mismatch_terminal(self):
        with self.assertRaises(cpu.CpuAccountingFailure):probe.settle_root(self.job,self.meter,self.kernel_fixture(),SimpleNamespace(process=22,pid=11),'999',self.private,0)
        self.assertEqual(self.final()['status'],'UNKNOWN_UNRESOLVED')
    def test_archive_failure_does_not_refund_root_or_allow_second_attempt(self):
        self.finish();before=(self.out/'3.cpu-final.json').read_bytes()
        report={'status':'offline','elapsed_seconds':0,'results':[]}
        with patch.object(probe,'native_admission'),patch.object(probe,'_execution_consumed',False),patch.object(probe,'_evidence_directory',self.out),patch.object(probe,'_owner_watchdog_started',False),patch.object(probe,'qualify',return_value=report),patch.object(probe,'archive_evidence',side_effect=OSError('archive failed')):
            with self.assertRaisesRegex(OSError,'archive failed'):probe.execute(self.out)
            with self.assertRaisesRegex(ValueError,'consumed'):probe.execute(self.out)
        self.assertEqual((self.out/'3.cpu-final.json').read_bytes(),before)
        self.assertEqual(json.loads((self.out/'archive-failure.json').read_text())['archive_cost'],'UNKNOWN_UNRESOLVED')
    def test_native_admission_is_held(self):
        with self.assertRaisesRegex(probe.owner_source.NativeQualificationRequired,'NOT_READY'):probe.execute(self.out)


if __name__=='__main__':unittest.main(verbosity=2)
