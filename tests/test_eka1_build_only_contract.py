"""Bounded BUILD_ONLY DATA fixtures. No tool, native child or World execution."""
import copy
import hashlib
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from tools import eka1_build_only_contract as b
from tests import test_eka1_external_settlement as external_fixture

class BuildChecks(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(dir=ROOT);self.base=Path(self.tmp.name)
        self.registry=self.base/'registry';self.owner=(100,1000);self.build=None
        self.external=external_fixture.SettlementChecks();self.external.setUp()
        self.patches=[patch.object(b,'REGISTRY',self.registry),patch.object(b,'current_birth',return_value=self.owner),patch.object(b,'tick',return_value=1000)]
        for p in self.patches:p.start()
        self.aid='build-'+self.base.name;self.out=ROOT/'runs'/('eka1-build-only-'+self.base.name)
        self.mp=self.base/'manifest.json';self.pp=self.base/'preparation.json'
        def file(name):
            p=self.base/name;p.write_bytes(('DATA fixture '+name).encode());return dict(path=str(p),sha256=b.digest(p.read_bytes()))
        compiler=file('compiler.exe');linker=file('linker.exe');header=file('eka1_probe_pins.h');dep=file('sdk.h')
        self.external.assignment=b.digest(self.aid.encode());self.external.plan['assignment_sha256']=self.external.assignment
        self.external.inputs();plan,plan_sha,unused,unused2=self.external.paths
        self.m=dict(schema='EKA-BUILD-ONLY-MANIFEST-v1',scope='BUILD_ONLY',contract=b.CONTRACT,
          assignment_id=self.aid,owner_birth=list(self.owner),deadline_tick=31000,limits=copy.deepcopy(b.LIMITS),
          output_relative=self.out.relative_to(ROOT).as_posix(),source={n:b.digest((ROOT/n).read_bytes()) for n in b.SOURCES},
          header=header,interpreter=dict(path=str(Path(sys.executable).resolve()),sha256=b.digest(Path(sys.executable).read_bytes())),
          toolchain=dict(compiler=compiler,linker=linker),environment=dict(SystemRoot=os.environ.get('SystemRoot','C:/Windows')),
          invocations=[dict(role=r,image=(compiler if r.startswith('compile') else linker)['path'],argv=['/nologo','FIXED_DATA_ONLY']) for r in b.CATALOGUE],
          outputs=list(b.BUILD_OUTPUTS),external_cost_categories=list(b.EXTERNAL),
          external_settlement_plan=dict(path=str(plan),sha256=plan_sha),
          **{n:{dep['path']:dep['sha256']} for n in ('sdk','includes','libraries','dependencies')})
        self.m['invocations']=b.invocations(self.m,self.out)
        self.external.plan['immutable_build_package_sha256']=b.recipe(self.m)
        self.external.inputs();self.m['external_settlement_plan']['sha256']=self.external.paths[1]
    def tearDown(self):
        if self.build is not None:
            try:self.build.close()
            except OSError:pass
        import shutil
        if self.out.exists():shutil.rmtree(self.out)
        for p in reversed(self.patches):p.stop()
        self.external.tearDown();self.tmp.cleanup()
    def prepare(self):
        self.mp.write_bytes(b.canonical(self.m));self.msha=b.digest(self.mp.read_bytes())
        self.prep=dict(schema='EKA-BUILD-ONLY-PREPARATION-v1',assignment_id=self.aid,manifest_sha256=self.msha,scope='BUILD_ONLY',authority='SOURCE_ONLY',attempts=1)
        self.pp.write_bytes(b.canonical(self.prep));self.psha=b.digest(self.pp.read_bytes())
    def open(self):
        self.prepare();self.build=b.BuildOnly(self.mp,self.pp,manifest_sha256=self.msha,preparation_sha256=self.psha);return self.build
    def outcome(self,index):
        role=b.CATALOGUE[index];tool=self.m['toolchain']['compiler' if role.startswith('compile') else 'linker']
        return dict(status='CREATED',birth=[1001+index,10001+index],parent_birth=list(self.owner),image_sha256=tool['sha256'],exit_code=0,signaled=True,root_member=True,EOF=True,termination_succeeded=True)
    def complete(self):
        obj=self.open()
        for i,role in enumerate(b.CATALOGUE):obj.precharge(role);obj.outcome(role,i,self.outcome(i))
        for n in self.m['outputs']:(self.out/n).write_bytes(b'DATA only, never loaded')
        return obj
    def sample(self):
        return dict(scope='BUILD_ONLY',assignment_sha256=self.msha,ledger_identity=list(self.build._physical),root_identity=b.digest(b'root'),
                    USER_ticks=10,KERNEL_ticks=5,initial_USER_ticks=0,initial_KERNEL_ticks=0,period_USER_ticks=10,period_KERNEL_ticks=5,
                    members=[[1001+i,10001+i] for i in range(4)],signaled_births=[[1001+i,10001+i] for i in range(4)],
                    active=0,EOF=True,termination_succeeded=True,nested_CPU_added=False,job_total_processes=4,peak_memory_bytes=1024,elapsed_ms=50,output_bytes=50,
                    started_tick=1000,closed_tick=1050,measured_tick=1050)
    def final_failure(self,sample,pattern):
        with self.assertRaisesRegex((ValueError,RuntimeError,TimeoutError,OSError),pattern):self.build.finalize(sample)
        result=json.loads((self.out/'build-final.json').read_text());self.assertFalse(result['native_entry_enabled']);return result
    def test_source_only_valid_binding_and_native_gate(self):
        obj=self.open();v=obj.preflight();self.assertEqual(v['decision'],'NO_GO');self.assertEqual(v['opaque_nested_attempts'],'UNKNOWN')
        with self.assertRaises(b.NativeQualificationRequired):b.native_admission(obj)
    def package(self):
        root=self.external.root
        for folder in ('payload','restored'):
            (root/folder/'native.json').unlink()
        import shutil,zipfile
        paths={'build/manifest.json':self.mp,'build/receipt.json':self.out/'build-final.json',
               'build/header.h':Path(self.m['header']['path'])}
        paths.update({'build/source/'+n:ROOT/n for n in b.SOURCES})
        paths.update({'build/output/'+p.name:p for p in self.out.iterdir() if p.name!='build-final.json'})
        for folder in ('payload','restored'):
            for name,p in paths.items():
                target=root/folder/name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,target)
        (root/'evidence.zip').unlink()
        with zipfile.ZipFile(root/'evidence.zip','x',zipfile.ZIP_DEFLATED) as z:
            for name,p in paths.items():z.write(p,name)
        self.external.inputs()
    def settle(self):
        with patch.object(b,'current_birth',return_value=(300,3000)):
            return b.settle_build(self.mp,self.msha,self.out/'build-final.json',b.digest((self.out/'build-final.json').read_bytes()),
                                  external_receipt_sha256=b.digest(self.external.paths[2].read_bytes()))
    def test_successful_DATA_capture_still_no_GO_or_paid_claim(self):
        obj=self.complete();result=obj.finalize(self.sample())
        self.assertEqual(result['root_total_ticks'],15);self.assertEqual(len(result['debits']),1)
        self.assertEqual(result['decision'],'NO_GO');self.assertIn('verifier_final_write',result['unresolved_costs'])
        self.assertEqual(result['opaque_nested_attempts'],'UNKNOWN')
        self.assertEqual(result['status'],'PROVISIONAL_BUILD_COSTS_EXTERNAL_SETTLEMENT_REQUIRED')
    def test_distinct_external_phase_exact_archive_still_NO_GO(self):
        obj=self.complete();obj.finalize(self.sample());self.package();result=self.settle()
        self.assertEqual(result['decision'],'NO_GO');self.assertEqual(result['root_total_ticks'],15)
        self.assertFalse(result['external']['actual_native_measurements_independently_verified'])
    def test_scientific_scope_rejected(self):
        self.m['scope']='SCIENTIFIC'
        with self.assertRaisesRegex(ValueError,'separate build'):self.open()
    def test_reissued_preparation_same_assignment_cannot_reset(self):
        self.open();self.m['deadline_tick']=30000;self.prepare()
        with self.assertRaises(FileExistsError):b.BuildOnly(self.mp,self.pp,manifest_sha256=self.msha,preparation_sha256=self.psha)
    def test_new_assignment_cannot_reset_same_original_owner_lifetime(self):
        self.open();self.m['assignment_id']+='-replacement';self.m['output_relative']+='-replacement';self.aid=self.m['assignment_id'];self.prepare()
        with self.assertRaises(FileExistsError):b.BuildOnly(self.mp,self.pp,manifest_sha256=self.msha,preparation_sha256=self.psha)
    def test_failed_preparation_burns_identity(self):
        self.prepare();self.prep['authority']='NATIVE';self.pp.write_bytes(b.canonical(self.prep));self.psha=b.digest(self.pp.read_bytes())
        with self.assertRaises(ValueError):b.BuildOnly(self.mp,self.pp,manifest_sha256=self.msha,preparation_sha256=self.psha)
        with self.assertRaises(FileExistsError):b.BuildOnly(self.mp,self.pp,manifest_sha256=self.msha,preparation_sha256=self.psha)
    def test_bool_preparation_attempts_is_not_one(self):
        self.prepare();self.prep['attempts']=True;self.pp.write_bytes(b.canonical(self.prep))
        with self.assertRaises(ValueError):b.BuildOnly(self.mp,self.pp,manifest_sha256=self.msha,preparation_sha256=b.digest(self.pp.read_bytes()))
    def test_changed_header_after_binding_poisoned(self):
        obj=self.open();Path(self.m['header']['path']).write_bytes(b'changed')
        with self.assertRaisesRegex(ValueError,'bytes changed'):obj.precharge(b.CATALOGUE[0])
        with self.assertRaisesRegex(RuntimeError,'Original failure'):obj.precharge(b.CATALOGUE[0])
    def test_changed_toolchain_after_binding(self):
        obj=self.open();Path(self.m['toolchain']['compiler']['path']).write_bytes(b'changed')
        with self.assertRaises(ValueError):obj.precharge(b.CATALOGUE[0])
    def test_source_pin_changed_rejected(self):
        self.m['source'][b.SOURCES[0]]='0'*64
        with self.assertRaises(ValueError):self.open()
    def test_alternate_owner_rejected(self):
        self.m['owner_birth']=[101,1001]
        with self.assertRaises(ValueError):self.open()
    def test_uncharged_outcome_rejected(self):
        obj=self.open()
        with self.assertRaisesRegex(ValueError,'precharge'):obj.outcome(b.CATALOGUE[0],0,self.outcome(0))
    def test_failed_create_consumes_durable_reservation(self):
        obj=self.open();obj.precharge(b.CATALOGUE[0])
        with self.assertRaisesRegex(RuntimeError,'terminal'):obj.outcome(b.CATALOGUE[0],0,dict(status='CREATE_FAILED',error='not found'))
        self.assertEqual(obj._attempts,1);self.assertIn(b'supervised_attempt',obj._path.read_bytes())
        with self.assertRaises(RuntimeError):obj.precharge(b.CATALOGUE[0])
    def test_rejected_create_preserves_error(self):
        obj=self.open();obj.precharge(b.CATALOGUE[0])
        with self.assertRaises(RuntimeError):obj.outcome(b.CATALOGUE[0],0,dict(status='REJECTED',error='policy denied'))
        self.assertIn(b'policy denied',obj._path.read_bytes())
    def test_manifest_mutation_cannot_extend_lifetime(self):
        obj=self.open();obj._manifest['deadline_tick']+=1
        with self.assertRaisesRegex(ValueError,'assignment changed'):obj.preflight()
    def test_original_deadline_expiration(self):
        obj=self.open()
        with patch.object(b,'tick',return_value=31000):
            with self.assertRaises(TimeoutError):obj.precharge(b.CATALOGUE[0])
        self.assertEqual(obj._attempts,0)
    def test_alternate_ledger_identity(self):
        obj=self.open();obj._physical=(1,2)
        with self.assertRaisesRegex(OSError,'Physical ledger'):obj.precharge(b.CATALOGUE[0])
    def test_in_place_ledger_rewrite(self):
        obj=self.open();raw=obj._path.read_bytes()
        with obj._path.open('r+b') as f:f.write(b'X'+raw[1:])
        with self.assertRaises(OSError):obj.precharge(b.CATALOGUE[0])
    def test_partial_debit_write_preserved_without_retry(self):
        obj=self.open();real=os.write
        def partial(fd,raw):return real(fd,raw[:7])
        with patch.object(b.os,'write',side_effect=partial):
            with self.assertRaises(OSError):obj.precharge(b.CATALOGUE[0])
        self.assertTrue(obj._storage_failed);self.assertEqual(obj._attempts,0)
        result=self.final_failure(self.sample(),'Physical ledger');self.assertEqual(result['root_total_ticks'],15)
    def test_missing_kernel_never_zero(self):
        self.complete();s=self.sample();s['KERNEL_ticks']=None
        result=self.final_failure(s,'Missing USER or KERNEL');self.assertIsNone(result['root_total_ticks']);self.assertIsNone(result['KERNEL_ticks'])
    def test_changed_epoch_counter_refused(self):
        self.complete();s=self.sample();s['period_USER_ticks']=9
        self.final_failure(s,'epochs')
    def test_duplicate_nested_billing_refused(self):
        self.complete();s=self.sample();s['nested_CPU_added']=True
        self.final_failure(s,'duplicate')
    def test_missing_child_custody(self):
        self.complete();s=self.sample();s['members']=s['members'][:-1]
        self.final_failure(s,'custody')
    def test_missing_EOF(self):
        self.complete();s=self.sample();s['EOF']=False
        self.final_failure(s,'custody')
    def test_failed_termination(self):
        self.complete();s=self.sample();s['termination_succeeded']=False
        self.final_failure(s,'custody')
    def test_overrun_preserves_actual_cost(self):
        self.complete();s=self.sample();s['USER_ticks']=s['period_USER_ticks']=b.LIMITS['USER_ticks']+1
        result=self.final_failure(s,'overrun');self.assertEqual(result['root_total_ticks'],b.LIMITS['USER_ticks']+6)
        self.assertEqual(len(result['debits']),1);self.assertEqual(result['debits'][0]['USER_ticks'],b.LIMITS['USER_ticks']+1)
    def test_memory_overrun_keeps_single_measured_debit(self):
        self.complete();s=self.sample();s['peak_memory_bytes']=b.LIMITS['memory_bytes']+1
        r=self.final_failure(s,'overrun');self.assertEqual(len(r['debits']),1);self.assertEqual(r['root_total_ticks'],15)
    def test_wall_overrun_keeps_single_measured_debit(self):
        self.complete();s=self.sample();s['elapsed_ms']=30001;s['closed_tick']=s['measured_tick']=31001
        r=self.final_failure(s,'overrun');self.assertEqual(len(r['debits']),1);self.assertEqual(r['root_total_ticks'],15)
    def test_deadline_overrun_keeps_single_measured_debit(self):
        self.complete();s=self.sample();s['measured_tick']=31001
        r=self.final_failure(s,'deadline');self.assertEqual(len(r['debits']),1);self.assertEqual(r['root_total_ticks'],15)
    def test_alternate_sample_assignment(self):
        self.complete();s=self.sample();s['assignment_sha256']='0'*64
        self.final_failure(s,'custody')
    def test_missing_output_keeps_CPU_cost(self):
        self.complete();(self.out/'eka1_owner_watchdog.dll').unlink()
        result=self.final_failure(self.sample(),'output');self.assertEqual(result['root_total_ticks'],15)
    def test_provisional_finalization_once_without_self_settlement(self):
        obj=self.complete();obj.finalize(self.sample())
        with self.assertRaisesRegex(RuntimeError,'exactly once'):obj.finalize(self.sample())
    def test_archive_failure_retains_root_and_original_failure(self):
        obj=self.complete();obj.finalize(self.sample());self.package()
        with patch.object(b.settlement,'settle',side_effect=OSError('archive failed')):
            with self.assertRaisesRegex(OSError,'archive failed'):self.settle()
        result=json.loads((self.out/'build-final.json').read_text());self.assertEqual(result['root_total_ticks'],15)
    def test_unrelated_archive_rejected_and_no_settlement_retry(self):
        obj=self.complete();obj.finalize(self.sample())
        with self.assertRaisesRegex(ValueError,'this exact'):self.settle()
        with self.assertRaises(FileExistsError):self.settle()
    def test_live_owner_cannot_self_settle(self):
        obj=self.complete();obj.finalize(self.sample());self.package()
        with self.assertRaisesRegex(ValueError,'Live original owner'):
            b.settle_build(self.mp,self.msha,self.out/'build-final.json',b.digest((self.out/'build-final.json').read_bytes()),external_receipt_sha256='a'*64)
    def test_mutated_caller_outcome_does_not_change_durable_birth(self):
        obj=self.open();original=self.outcome(0);obj.precharge(b.CATALOGUE[0]);obj.outcome(b.CATALOGUE[0],0,original)
        original['birth'][0]=9999
        self.assertEqual(obj._outcomes[0][2]['birth'][0],1001)
    def test_unexplained_associated_process_cannot_omit_identity(self):
        self.complete();s=self.sample();s['job_total_processes']=5
        self.final_failure(s,'complete identity')
    def test_arbitrary_or_scientific_compiler_arguments_rejected(self):
        self.m['invocations'][0]['argv']=['scientificWorld.py']
        self.external.plan['immutable_build_package_sha256']=b.recipe(self.m)
        self.external.inputs();self.m['external_settlement_plan']['sha256']=self.external.paths[1]
        with self.assertRaisesRegex(ValueError,'arbitrary command'):self.open()
    def test_failure_writer_failure_does_not_replace_origin(self):
        obj=self.open()
        with patch.object(b,'save',side_effect=OSError('disk full')):
            with self.assertRaisesRegex(ValueError,'precharge') as ctx:obj.outcome(b.CATALOGUE[0],0,self.outcome(0))
        self.assertTrue(ctx.exception.__notes__);self.assertIn('precharge',obj._failed)
    def test_missing_archive_tail_is_real_validator_failure(self):
        obj=self.complete();obj.finalize(self.sample());self.package()
        (self.external.root/'tails/final-closure.json').unlink();self.external.inputs()
        with self.assertRaisesRegex(b.settlement.SettlementFailure,'tails required'):self.settle()
    def test_unknown_external_kernel_never_substituted_zero(self):
        obj=self.complete();obj.finalize(self.sample());self.package()
        self.external.samples[0]['KERNEL_ticks']=None;self.external.inputs()
        with self.assertRaisesRegex(ValueError,'external CPU'):self.settle()
        report=json.loads(next(self.registry.glob('settlement-*.failure.json')).read_text())
        self.assertIsNone(report['external']['debits'][0]['recorded_KERNEL_ticks'])
    def test_cleanup_failure_preserves_first_counter_failure(self):
        obj=self.complete();s=self.sample();s['KERNEL_ticks']=None;fd=obj._fd
        with patch.object(b.os,'close',side_effect=OSError('close failed')):
            with self.assertRaisesRegex(ValueError,'Missing USER or KERNEL') as ctx:obj.finalize(s)
        self.assertIn('Missing USER or KERNEL',obj._failed);self.assertTrue(obj._cleanup_errors);self.assertTrue(ctx.exception.__notes__)
        os.close(fd)  # Test-owned descriptor cleanup, not a production retry path.
        obj._fd=None
    def tampered_external(self,name,value):
        obj=self.complete();obj.finalize(self.sample());p=self.out/'build-final.json'
        r=json.loads(p.read_bytes());r['raw_root_sample'][name]=value;p.write_bytes(b.canonical(r));self.package()
        with self.assertRaises((ValueError,TimeoutError)):self.settle()
    def test_external_rejects_changed_raw_USER(self):self.tampered_external('USER_ticks',11)
    def test_external_rejects_absent_raw_KERNEL(self):self.tampered_external('KERNEL_ticks',None)
    def test_external_rejects_raw_EOF_false(self):self.tampered_external('EOF',False)
    def test_external_rejects_missing_signaled_births(self):self.tampered_external('signaled_births',[])
    def test_external_rejects_nonzero_initial_counter(self):self.tampered_external('initial_USER_ticks',1)
    def test_external_rejects_late_measurement(self):self.tampered_external('measured_tick',31001)
    def test_external_rechecks_current_output_after_archive(self):
        obj=self.complete();obj.finalize(self.sample());self.package()
        (self.out/'eka1_probe_guardian.exe').write_bytes(b'changed after archive')
        with self.assertRaisesRegex(ValueError,'Retained build output'):self.settle()
    def test_close_failure_cannot_launder_provisional_receipt(self):
        obj=self.complete();fd=obj._fd
        with patch.object(b.os,'close',side_effect=OSError('close failed')):
            with self.assertRaisesRegex(OSError,'close failed'):obj.finalize(self.sample())
        os.close(fd);obj._fd=None;self.package()
        with self.assertRaisesRegex(ValueError,'failure tail'):self.settle()

if __name__=='__main__':unittest.main()
