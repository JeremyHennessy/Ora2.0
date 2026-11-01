"""Focused staged DATA fixtures. No compiler, image load, child or World."""
import copy
import json
import os
from pathlib import Path
import sys
import unittest
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parent))
import test_eka1_build_only_contract as fixtures
from tools import eka1_build_only_contract as b


class StagedChecks(unittest.TestCase):
    def setUp(self):
        self.f=fixtures.BuildChecks();self.f.setUp();self.m=self.f.m
        self.m.update(schema=b.STAGED_SCHEMA,contract=b.STAGED_CONTRACT,
                      header=dict(path=str(self.f.out/b.DERIVED_OUTPUTS[0])))
        self.m['source']['tools/eka1_probe_child.py']=b.digest((b.ROOT/'tools/eka1_probe_child.py').read_bytes())
        self.m['release_pins']=b.release_inputs(self.m,self.f.out)
        self.m['root_binding']=dict(root_identity=b.digest(b'root'),USER_ticks=0,KERNEL_ticks=0,
            period_USER_ticks=0,period_KERNEL_ticks=0,active=0,total_processes=0,root_handle_retained=True)
        self.m['outputs']+=list(b.DERIVED_OUTPUTS)
        self.m['invocations']=b.invocations(self.m,self.f.out);self.plan()
    def tearDown(self):self.f.tearDown()
    def plan(self):
        self.f.external.plan['immutable_build_package_sha256']=b.recipe(self.m)
        self.f.external.inputs();self.m['external_settlement_plan']['sha256']=self.f.external.paths[1]
    def open(self):return self.f.open()
    def stage_a(self):
        obj=self.open()
        for i in range(2):obj.precharge(b.CATALOGUE[i]);obj.outcome(b.CATALOGUE[i],i,self.f.outcome(i))
        (obj.out/'eka1_owner_watchdog.dll').write_bytes(b'DATA watchdog, never loaded')
        return obj
    def a_sample(self):
        s=self.f.sample();s.update(USER_ticks=4,KERNEL_ticks=2,period_USER_ticks=4,period_KERNEL_ticks=2,
            members=[[1001,10001],[1002,10002]],signaled_births=[[1001,10001],[1002,10002]],
            job_total_processes=2,closed_tick=1020,measured_tick=1020,elapsed_ms=20,output_bytes=20,
            root_handle_retained=True)
        return s
    def derive(self,obj,s=None):
        with patch.object(b,'tick',return_value=1040):return obj.derive_stage_b(self.a_sample() if s is None else s)
    def complete(self):
        obj=self.stage_a();self.derive(obj)
        with patch.object(b,'tick',return_value=1041):
            for i in (2,3):obj.precharge(b.CATALOGUE[i]);obj.outcome(b.CATALOGUE[i],i,self.f.outcome(i))
        for name in self.m['outputs']:
            p=obj.out/name
            if not p.exists():p.write_bytes(b'DATA output, never executed')
        return obj
    def final_sample(self):
        s=self.f.sample();s['root_handle_retained']=True;return s
    def finish(self,obj,s=None):
        with patch.object(b,'tick',return_value=1060):return obj.finalize(self.final_sample() if s is None else s)
    def package(self):
        f=self.f;root=f.external.root
        for folder in ('payload','restored'):(root/folder/'native.json').unlink()
        import shutil,zipfile
        paths={'build/manifest.json':f.mp,'build/receipt.json':f.out/'build-final.json',
               'build/header.h':f.out/b.DERIVED_OUTPUTS[0]}
        paths.update({'build/source/'+n:b.ROOT/n for n in self.m['source']})
        paths.update({'build/output/'+p.name:p for p in f.out.iterdir() if p.name!='build-final.json'})
        for folder in ('payload','restored'):
            for name,p in paths.items():
                target=root/folder/name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,target)
        with zipfile.ZipFile(root/'evidence.zip','w',compression=zipfile.ZIP_DEFLATED) as z:
            for name in paths:z.write(root/'payload'/name,name)
        f.external.inputs()

    def test_one_attempt_retains_binding_and_charges_only_final_root(self):
        obj=self.stage_a();original=obj._raw;physical=obj._physical;end=obj._end
        d=self.derive(obj);self.assertEqual(d['decision'],'NO_GO');self.assertEqual(obj._debits,[])
        self.assertEqual((obj._raw,obj._physical,obj._end),(original,physical,end))
        for pin in obj._pins:self.assertIsNotNone(pin.handle)
        with self.assertRaises(OSError):(obj.out/'eka1_owner_watchdog.dll').write_bytes(b'cannot mutate pinned DATA')
        with patch.object(b,'tick',return_value=1041):
            for i in (2,3):obj.precharge(b.CATALOGUE[i]);obj.outcome(b.CATALOGUE[i],i,self.f.outcome(i))
        for name in self.m['outputs']:
            if not (obj.out/name).exists():(obj.out/name).write_bytes(b'DATA')
        r=self.finish(obj);self.assertEqual(r['root_total_ticks'],15);self.assertEqual(len(r['debits']),1)
        self.assertEqual(len(b.ledger_rows(obj._path)),11);self.assertTrue(all(p.handle is None for p in obj._pins))
        self.assertFalse(r['native_entry_enabled'])
        with self.assertRaises(b.NativeQualificationRequired):b.native_admission(obj)
    def test_external_revalidates_derived_archive_still_native_NO_GO(self):
        obj=self.complete();self.finish(obj);self.package();r=self.f.settle()
        self.assertEqual(r['decision'],'NO_GO');self.assertEqual(r['root_total_ticks'],15)
        self.assertIn('FINAL_WRITER_UNSETTLED',r['external']['status'])
    def test_stage_B_before_derivation_poisoned(self):
        obj=self.stage_a()
        with self.assertRaisesRegex(ValueError,'StageB'):obj.precharge(b.CATALOGUE[2])
        with self.assertRaisesRegex(RuntimeError,'Original failure'):self.derive(obj)
    def test_early_derivation_poisoned(self):
        obj=self.open()
        with self.assertRaisesRegex(ValueError,'successful StageA'):self.derive(obj)
        with self.assertRaisesRegex(RuntimeError,'Original failure'):obj.precharge(b.CATALOGUE[0])
    def test_second_derivation_cannot_mint_authority(self):
        obj=self.stage_a();self.derive(obj)
        with self.assertRaisesRegex(ValueError,'Exactly one'):self.derive(obj)
        with self.assertRaisesRegex(RuntimeError,'Original failure'):obj.precharge(b.CATALOGUE[2])
    def test_failed_stage_A_start_consumed_and_cannot_derive(self):
        obj=self.open();obj.precharge(b.CATALOGUE[0])
        with self.assertRaises(RuntimeError):obj.outcome(b.CATALOGUE[0],0,dict(status='CREATE_FAILED',error='fixture failed creation'))
        with self.assertRaisesRegex(RuntimeError,'Original failure'):self.derive(obj)
        self.assertEqual(obj._attempts,1);self.assertIn(b'fixture failed creation',obj._path.read_bytes())
    def test_missing_counter_retained_and_no_derivation_retry(self):
        obj=self.stage_a();s=self.a_sample();s['KERNEL_ticks']=None
        with self.assertRaises(ValueError):self.derive(obj,s)
        self.assertIsNone(b.ledger_rows(obj._path)[5]['event']['stage_a_sample']['KERNEL_ticks'])
        with self.assertRaisesRegex(RuntimeError,'Original failure'):self.derive(obj)
    def test_stage_A_root_change_or_unclosed_tree_rejected(self):
        obj=self.stage_a()
        b.validate_sample(self.a_sample(),self.m,self.f.msha,obj._physical,[(1001,10001),(1002,10002)],1000)
        for name,value in [('root_identity','f'*64),('active',1),('root_handle_retained',False),('EOF',False),('job_total_processes',3)]:
            with self.subTest(name=name):
                s=self.a_sample();s[name]=value
                with self.assertRaises(ValueError):b.validate_sample(s,self.m,self.f.msha,obj._physical,[(1001,10001),(1002,10002)],1000)
    def test_existing_header_retains_failure_and_closes_DLL_pin(self):
        obj=self.stage_a();header=obj.out/b.DERIVED_OUTPUTS[0];header.write_bytes(b'preexisting')
        with self.assertRaises(FileExistsError):self.derive(obj)
        self.assertEqual(header.read_bytes(),b'preexisting');self.assertTrue(all(p.handle is None for p in obj._pins))
        with self.assertRaisesRegex(RuntimeError,'Original failure'):obj.precharge(b.CATALOGUE[2])
    def test_manifest_write_interruption_preserves_partial_header_and_costs(self):
        obj=self.stage_a();original=b.save
        def interrupted(path,value):
            if path.name==b.DERIVED_OUTPUTS[1]:path.write_bytes(b'{partial');raise OSError('fixture interrupted manifest write')
            return original(path,value)
        with patch.object(b,'save',side_effect=interrupted):
            with self.assertRaisesRegex(OSError,'interrupted'):self.derive(obj)
        self.assertEqual((obj.out/b.DERIVED_OUTPUTS[1]).read_bytes(),b'{partial')
        self.assertTrue((obj.out/b.DERIVED_OUTPUTS[0]).exists());self.assertTrue(all(p.handle is None for p in obj._pins))
        self.assertEqual(obj._attempts,2)
    def test_changed_owner_or_ledger_cannot_cross_stage(self):
        obj=self.stage_a();self.derive(obj)
        with patch.object(b,'current_birth',return_value=(101,1001)):
            with self.assertRaisesRegex(ValueError,'Original process'):obj.precharge(b.CATALOGUE[2])
        self.assertEqual(obj._attempts,2)
    def test_replaced_ledger_cannot_cross_stage(self):
        obj=self.stage_a();self.derive(obj);raw=obj._path.read_bytes()
        # Fixture tampering only: Windows already denies deleting the open ledger.
        with self.assertRaises(OSError):obj._path.unlink()
        os.close(obj._fd);obj._path.rename(obj._path.with_suffix('.old'));obj._path.write_bytes(raw)
        obj._fd=os.open(obj._path,os.O_RDWR|os.O_BINARY);os.lseek(obj._fd,0,os.SEEK_END)
        with self.assertRaisesRegex(OSError,'Physical ledger'):obj.precharge(b.CATALOGUE[2])
    def test_elapsed_derivation_cannot_extend_original_deadline(self):
        obj=self.stage_a();self.derive(obj)
        with patch.object(b,'tick',return_value=31000):
            with self.assertRaisesRegex(TimeoutError,'deadline'):obj.precharge(b.CATALOGUE[2])
    def test_final_root_and_epoch_cannot_reset(self):
        self.stage_a();b.cumulative_stage_sample(self.final_sample(),self.a_sample())
        for name,value in [('root_identity','0'*64),('started_tick',1001),('USER_ticks',3),('KERNEL_ticks',1),('output_bytes',19),('peak_memory_bytes',1),('job_total_processes',1)]:
            with self.subTest(name=name):
                s=self.final_sample();s[name]=value
                with self.assertRaises(ValueError):b.cumulative_stage_sample(s,self.a_sample())
    def test_cumulative_USER_overrun_keeps_one_full_debit(self):
        obj=self.complete();s=self.final_sample();s['USER_ticks']=s['period_USER_ticks']=350000000
        with self.assertRaisesRegex(ValueError,'resource overrun'):self.finish(obj,s)
        r=json.loads((obj.out/'build-final.json').read_bytes());self.assertEqual(r['debits'][0]['USER_ticks'],350000000)
        self.assertFalse(r['native_entry_enabled'])
    def test_cumulative_output_overrun_terminal(self):
        obj=self.complete();s=self.final_sample();s['output_bytes']=1100000
        with self.assertRaisesRegex(ValueError,'resource overrun'):self.finish(obj,s)
        self.assertEqual(len(obj._debits),1)
    def test_nonzero_initial_epoch_cannot_bind(self):
        self.m['root_binding']['period_KERNEL_ticks']=1;self.plan()
        with self.assertRaisesRegex(ValueError,'zero epoch'):self.open()
    def test_unreviewed_release_pin_rejected(self):
        self.m['release_pins']['program']='unreviewed.py';self.plan()
        with self.assertRaisesRegex(ValueError,'release derivation'):self.open()
    def test_derived_handle_early_close_poisoned(self):
        obj=self.stage_a();self.derive(obj);obj._pins[0].close()
        with self.assertRaisesRegex(ValueError,'closed early'):obj.precharge(b.CATALOGUE[2])
    def test_missing_derived_archive_output_rejected(self):
        obj=self.complete();self.finish(obj);self.package()
        (self.f.external.root/'payload/build/output/stage-b-manifest.json').unlink()
        with self.assertRaisesRegex(ValueError,'exact manifest'):self.f.settle()
    def test_changed_derived_manifest_after_owner_closure_rejected(self):
        obj=self.complete();self.finish(obj);p=obj.out/b.DERIVED_OUTPUTS[1]
        data=json.loads(p.read_bytes());data['deadline_tick']+=1;p.write_bytes(b.canonical(data));self.package()
        with self.assertRaisesRegex(ValueError,'artifact changed'):self.f.settle()
    def test_same_root_cannot_be_reissued_to_new_owner(self):
        obj=self.stage_a();obj.close();self.m['assignment_id']+='-new';self.f.aid=self.m['assignment_id']
        self.m['owner_birth']=[101,1001];self.m['output_relative']+='-new';self.f.external.plan['owner_birth']=[101,1001];self.plan()
        self.f.prepare()
        with patch.object(b,'current_birth',return_value=(101,1001)):
            with self.assertRaises(FileExistsError):b.BuildOnly(self.f.mp,self.f.pp,manifest_sha256=self.f.msha,preparation_sha256=self.f.psha)
    def test_cumulative_wall_overrun_retains_costs(self):
        obj=self.complete();s=self.final_sample();s.update(closed_tick=34000,measured_tick=34000,elapsed_ms=33000)
        with patch.object(b,'tick',return_value=34000):
            with self.assertRaisesRegex(ValueError,'resource overrun'):obj.finalize(s)
        self.assertEqual(len(obj._debits),1)
    def test_failed_pin_close_preserves_origin_and_is_not_retried(self):
        obj=self.stage_a();original=b.save;close=b.CapsuleReadHandle.close;called=[]
        def interrupted(path,value):
            if path.name==b.DERIVED_OUTPUTS[1]:raise OSError('fixture original derivation failure')
            return original(path,value)
        def fail_close(pin):
            called.append(pin.handle);pin.close_attempted=True
            raise OSError('fixture pin closure UNKNOWN')
        with patch.object(b,'save',side_effect=interrupted),patch.object(b.CapsuleReadHandle,'close',new=fail_close):
            with self.assertRaisesRegex(OSError,'original derivation') as ctx:self.derive(obj)
        self.assertTrue(ctx.exception.__notes__);n=len(called)
        with self.assertRaisesRegex(OSError,'no retry'):obj.close()
        self.assertEqual(len(called),n);self.assertIn('original derivation',obj._failed)
        # Close fixture-owned DATA handles; this is not a runtime retry path.
        for pin in obj._pins:pin.close_attempted=False;close(pin)
    def test_all_distinct_cleanup_failures_have_once_only_durable_tail(self):
        obj=self.stage_a();original=b.save;close=b.CapsuleReadHandle.close;failed=[]
        def interrupted(path,value):
            if path.name==b.DERIVED_OUTPUTS[1]:raise OSError('original manifest failure')
            return original(path,value)
        def fail_close(pin):
            message='distinct-close-'+str(len(failed));failed.append(message);pin.close_attempted=True
            raise OSError(message)
        with patch.object(b,'save',side_effect=interrupted),patch.object(b.CapsuleReadHandle,'close',new=fail_close):
            with self.assertRaisesRegex(OSError,'original manifest'):self.derive(obj)
        tail=obj.out/'derived-cleanup-failure.json';raw=tail.read_bytes();report=json.loads(raw)
        self.assertEqual(len(report['cleanup_errors']),2);self.assertIn('original manifest',report['first_failure'])
        self.assertTrue(all(any(message in row for row in report['cleanup_errors']) for message in failed))
        with self.assertRaises(OSError):obj.close()
        self.assertEqual(tail.read_bytes(),raw);self.assertEqual(len(failed),2)
        for pin in obj._pins:pin.close_attempted=False;close(pin)
    def test_cleanup_tail_disk_failure_preserves_all_errors_in_primary_notes(self):
        obj=self.stage_a();original=b.save;close=b.CapsuleReadHandle.close;failed=[]
        def interrupted(path,value):
            if path.name==b.DERIVED_OUTPUTS[1]:raise OSError('original manifest interruption')
            if path.name=='derived-cleanup-failure.json':raise OSError('cleanup tail disk full')
            return original(path,value)
        def fail_close(pin):
            message='distinct-unclosed-'+str(len(failed));failed.append(message);pin.close_attempted=True
            raise OSError(message)
        try:
            with patch.object(b,'save',side_effect=interrupted),patch.object(b.CapsuleReadHandle,'close',new=fail_close):
                with self.assertRaisesRegex(OSError,'original manifest interruption') as ctx:self.derive(obj)
            notes=' '.join(ctx.exception.__notes__)
            self.assertIn('cleanup tail disk full',notes)
            self.assertTrue(all(message in notes for message in failed));self.assertEqual(len(failed),2)
            self.assertIn('original manifest interruption',json.loads((obj.out/'failure.json').read_bytes())['first_failure'])
        finally:
            for pin in obj._pins:pin.close_attempted=False;close(pin)


if __name__=='__main__':unittest.main()
