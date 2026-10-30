"""DATA-only settlement fixtures. No process, compiler, World or native Job."""
import copy
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
import zipfile

ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from tools import eka1_external_settlement as s
from tools.eka1_native_owner_candidate import canonical

def h(value):return hashlib.sha256(value).hexdigest()
def tag(text):return h(text.encode('ascii'))

class SettlementChecks(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(dir=ROOT);self.base=Path(self.tmp.name)
        self.root=self.base/'evidence';self.root.mkdir()
        self.registry=self.base/'claims'
        self.patches=[patch.object(s,'REGISTRY',self.registry),patch.object(s,'current_birth',return_value=(300,3000))]
        for item in self.patches:item.start()
        self.owner=[100,1000];self.observer=[200,2000];self.verifier=[300,3000]
        self.sid1=tag('owner-scope');self.sid2=tag('observer-scope');self.assignment=tag('offline-fixture')
        self.plan={'schema':'EKA-EXTERNAL-SETTLEMENT-PLAN-v1','assignment_sha256':self.assignment,
                   'owner_birth':self.owner,'immutable_build_package_sha256':tag('build-reference-only'),
                   'scopes':[{'scope_id':self.sid1,'root_identity':tag('root1'),'kind':'PROCESS_LIFETIME','members':[self.owner]},
                             {'scope_id':self.sid2,'root_identity':tag('root2'),'kind':'PROCESS_LIFETIME','members':[self.observer]}],
                   'phases':[{'phase':name,'actor_birth':self.owner if index<5 else self.observer,
                              'scope_id':self.sid1 if index<5 else self.sid2}
                             for index,name in enumerate(['archive_create','restore','hash','completion','watchdog_shutdown','process_closure'])],
                   'archive_caps':{'payload_files':128,'payload_bytes':s.MAX_BYTES,'stored_bytes':s.MAX_BYTES,
                                   'retained_files':128,'retained_bytes':s.MAX_BYTES},'verifier_tail_scope':None}
        self.plan['phases'][-1].update(closed_scope_id=self.sid1,closed_birth=self.owner)
        self.samples=[{'scope_id':self.sid1,'root_identity':tag('root1'),'kind':'PROCESS_LIFETIME',
                       'measurer_birth':self.observer,'signaled':True,'active':0,'closed_births':[self.owner],
                       'signaled_tick':70,'measured_tick':80,'EOF':True,'USER_ticks':10,'KERNEL_ticks':5},
                      {'scope_id':self.sid2,'root_identity':tag('root2'),'kind':'PROCESS_LIFETIME',
                       'measurer_birth':self.verifier,'signaled':True,'active':0,'closed_births':[self.observer],
                       'signaled_tick':90,'measured_tick':100,'EOF':True,'USER_ticks':7,'KERNEL_ticks':3}]
        raw=b'fixed DATA fixture, not executable'
        for folder in ('payload','restored'):
            (self.root/folder).mkdir();(self.root/folder/'native.json').write_bytes(raw)
        (self.root/'tails').mkdir()
        for name in s.TAILS:(self.root/'tails'/name).write_bytes(canonical({'fixture':name}))
        with zipfile.ZipFile(self.root/'evidence.zip','x',zipfile.ZIP_DEFLATED) as z:z.writestr('native.json',raw)
    def tearDown(self):
        for item in reversed(self.patches):item.stop()
        self.tmp.cleanup()
    def inputs(self):
        plan=self.root/'settlement-plan.json';plan.write_bytes(canonical(self.plan));plan_sha=h(plan.read_bytes())
        events=[];previous='0'*64
        for index,phase in enumerate(self.plan['phases']):
            event=dict(phase,sequence=index,previous_sha256=previous,
                       ended_tick=85 if phase['phase']=='process_closure' else (index+1)*10)
            events.append(event);previous=h(canonical(event))
        files={p.relative_to(self.root).as_posix():h(p.read_bytes()) for p in self.root.rglob('*')
               if p.is_file() and p.name!='settlement-input.json'}
        self.receipt={'schema':'EKA-EXTERNAL-SETTLEMENT-INPUT-v1','assignment_sha256':self.assignment,
                      'plan_sha256':plan_sha,'samples':copy.deepcopy(self.samples),'events':events,
                      'event_tip_sha256':previous,'files':files}
        self.paths=(plan,plan_sha,self.root/'settlement-input.json',None)
        return self.finish_inputs()
    def finish_inputs(self):
        plan,sha,path,unused=self.paths;path.write_bytes(canonical(self.receipt))
        self.paths=(plan,sha,path,h(path.read_bytes()));return self.paths
    def settle(self):return s.settle(*self.inputs())
    def failure(self,pattern):
        with self.assertRaisesRegex(s.SettlementFailure,pattern) as failure:s.settle(*self.paths)
        report=failure.exception.observation
        self.assertEqual(report['decision'],'NO_GO');self.assertFalse(report['native_entry_enabled'])
        self.assertTrue((self.registry/(self.assignment+'.consumed.json')).exists())
        return report
    def test_disjoint_final_scopes_preserve_unsettled_writer_tail(self):
        report=self.settle()
        self.assertEqual(report['recorded_complete_covered_ticks'],25)
        self.assertEqual(report['verifier_writer_tail'],'UNSETTLED')
        self.assertEqual(report['decision'],'NO_GO');self.assertFalse(report['actual_native_measurements_independently_verified'])
        self.assertEqual(report['archive']['total_retained_files'],9)
        self.assertEqual(report['archive']['payload_files'],1)
    def test_reserved_tail_does_not_manufacture_ready(self):
        self.plan['verifier_tail_scope']=tag('future-outer-scope');report=self.settle()
        self.assertEqual(report['verifier_writer_tail'],'PENDING_SEPARATE_EXTERNAL_SCOPE')
        self.assertEqual(report['decision'],'NO_GO');self.assertTrue(report['unresolved_costs'])
    def test_missing_kernel_remains_unresolved_not_zero(self):
        self.samples[0]['KERNEL_ticks']=None;report=self.settle()
        self.assertIsNone(report['recorded_complete_covered_ticks'])
        self.assertIsNone(report['debits'][0]['recorded_total_ticks'])
        self.assertEqual(report['known_component_ticks_lower_bound'],20)
        self.assertIn(self.sid1,report['unresolved_costs'])
    def test_non_signaled_scope_is_terminal(self):
        self.samples[1]['signaled']=False;self.inputs();report=self.failure('custody/cutoff')
        self.assertEqual(report['known_component_ticks_lower_bound'],15)
    def test_self_measured_owner_refused(self):
        self.samples[0]['measurer_birth']=self.owner;self.inputs();self.failure('custody/cutoff')
    def test_circular_or_posthumous_measurement_refused(self):
        self.samples[1]['measurer_birth']=self.owner;self.inputs();self.failure('Circular or posthumous')
    def test_live_verifier_cannot_be_a_final_closed_scope(self):
        self.plan['scopes'][1]['members']=[self.verifier];self.inputs();self.failure('self-measured')
    def test_nested_scope_member_overlap_refused(self):
        self.plan['scopes'][1]['kind']='JOB_LIFETIME';self.plan['scopes'][1]['members'].append(self.owner)
        self.inputs();self.failure('nested')
    def test_same_root_under_two_scope_labels_refused(self):
        self.plan['scopes'][1]['root_identity']=self.plan['scopes'][0]['root_identity']
        self.inputs();self.failure('Duplicate')
    def test_duplicate_debit_refused(self):
        self.inputs();self.receipt['samples'][1]=copy.deepcopy(self.receipt['samples'][0]);self.finish_inputs()
        self.failure('Duplicate or alternate debit')
    def test_failed_measurement_never_refunds_claim(self):
        self.samples[0]['active']=1;self.inputs();self.failure('custody/cutoff')
        self.samples[0]['active']=0;self.inputs()
        with self.assertRaises(FileExistsError):s.settle(*self.paths)
    def test_receipt_cannot_include_its_own_final_hash(self):
        self.inputs();self.receipt['files']['settlement-input.json']='0'*64;self.finish_inputs()
        self.failure('own final write')
    def test_missing_postarchive_tail_refused(self):
        (self.root/'tails/completion.json').unlink();self.inputs();self.failure('tails required')
    def test_restored_data_difference_refused(self):
        (self.root/'restored/native.json').write_bytes(b'changed');self.inputs();self.failure('restoration')
    def test_total_extent_counts_restored_zip_tails_and_inputs(self):
        self.plan['archive_caps']['retained_bytes']=100;self.inputs();self.failure('Total retained extent')
    def test_phase_event_hash_change_refused(self):
        self.inputs();self.receipt['events'][3]['previous_sha256']='f'*64;self.finish_inputs()
        self.failure('hash/cutoff')
    def test_measurement_before_covered_phase_end_refused(self):
        self.samples[0]['signaled_tick']=40;self.inputs();self.failure('custody/cutoff')
    def test_closed_tail_scope_cannot_include_current_writer(self):
        self.plan['verifier_tail_scope']=self.sid2;self.inputs();self.failure('writer tail')
    def test_boolean_cpu_not_exact_integer(self):
        self.samples[0]['USER_ticks']=True;self.inputs();self.failure('Exact nonnegative integer')
    def test_owner_lifetime_cannot_be_omitted(self):
        self.plan['owner_birth']=[900,9000];self.inputs();self.failure('Original owner lifetime missing')
    def test_duplicate_closed_birth_evidence_not_deduplicated(self):
        self.samples[0]['closed_births'].append(self.owner);self.inputs();self.failure('custody/cutoff')
    def test_original_owner_cannot_record_own_final_closure(self):
        self.plan['phases'][-1].update(actor_birth=self.owner,scope_id=self.sid1)
        self.inputs();self.failure('External process closure')
    def test_undeclared_measurer_costs_cannot_disappear(self):
        self.samples[0]['measurer_birth']=[400,4000]
        self.inputs();self.failure('Undeclared measuring actor')
    def test_completion_cannot_precede_archive_creation(self):
        self.plan['phases'][0],self.plan['phases'][3]=self.plan['phases'][3],self.plan['phases'][0]
        self.inputs();self.failure('dependency order')
    def test_final_closure_targets_original_owner_scope(self):
        self.plan['phases'][-1]['closed_scope_id']=self.sid2
        self.inputs();self.failure('original owner scope/birth')
    def test_final_closure_cutoff_not_before_owner_signal(self):
        self.inputs();self.receipt['events'][-1]['ended_tick']=65
        self.receipt['event_tip_sha256']=h(canonical(self.receipt['events'][-1]));self.finish_inputs()
        report=self.failure('closure cutoff precedes')
        self.assertEqual(report['known_component_ticks_lower_bound'],25)

if __name__=='__main__':unittest.main()
