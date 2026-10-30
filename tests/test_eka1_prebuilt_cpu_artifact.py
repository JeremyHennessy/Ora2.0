"""Offline bytes/receipt fixtures only. No PE load, compiler or native child."""
import hashlib
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import Mock,patch
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from tools import eka1_prebuilt_cpu_artifact as a
from tools import eka1_native_probe as p
from tools import eka1_native_owner_candidate as o

class PrebuiltChecks(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(dir=ROOT);self.out=Path(self.tmp.name)
        sha=lambda v:hashlib.sha256(v).hexdigest()
        self.files={}
        for role,name in a.ARTIFACTS.items():
            raw=('DATA_FIXTURE_NOT_A_COMPILED_'+role).encode();(self.out/name).write_bytes(raw)
            self.files[role]=sha(raw)
        self.source={n:sha((ROOT/n).read_bytes()) for n in a.SOURCE_INPUTS}
        self.receipt={'schema':'EKA-SEPARATE-BUILD-OBSERVATION-v1','source_sha256':self.source,
                      'artifact_sha256':self.files,'root_USER_ticks':70,'root_KERNEL_ticks':30,
                      'attempts':None,'closure':{'root_empty':True,'all_owned_births_signaled':True,
                                                'EOF':True,'exit_code':0}}
        self.protocol=a.LEGACY_PROTOCOL
    def tearDown(self):self.tmp.cleanup()
    def package(self):
        raw=o.canonical(self.receipt);(self.out/'separate-build-receipt.json').write_bytes(raw)
        manifest={'schema':'EKA-PREBUILT-CPU-CANDIDATE-v1','binding_protocol':self.protocol,
                  'source_sha256':self.source,'artifact_sha256':self.files,
                  'build_receipt_sha256':hashlib.sha256(raw).hexdigest()}
        raw=o.canonical(manifest);path=self.out/'package.json';path.write_bytes(raw)
        return path,hashlib.sha256(raw).hexdigest()
    def evaluate(self):return a.evaluate(*self.package())
    def test_legacy_prebuilt_never_reusable_even_if_all_hashes_match(self):
        result=self.evaluate()
        self.assertEqual(result['decision'],'NO_GO');self.assertFalse(result['native_entry_enabled'])
        self.assertEqual(result['fresh_assignment_binding'],'INCOMPATIBLE_EMBEDDED_OWNER_LEDGER_DEADLINE')
        self.assertEqual(result['receipt_root_USER_plus_KERNEL_ticks'],100)
        self.assertFalse(result['external_build_costs_settled'])
    def test_claimed_future_protocol_does_not_enable_native(self):
        self.protocol='CLAIMED_FUTURE_CAPSULE_V2';result=self.evaluate()
        self.assertEqual(result['fresh_assignment_binding'],'UNKNOWN_UNQUALIFIED_BINDING_PROTOCOL')
        self.assertFalse(result['native_entry_enabled'])
    def test_missing_kernel_cost_is_unknown_not_zero(self):
        del self.receipt['root_KERNEL_ticks'];result=self.evaluate()
        self.assertIsNone(result['receipt_root_USER_plus_KERNEL_ticks'])
        self.assertTrue(result['missing_root_costs_unresolved'])
    def test_bool_or_negative_cost_refused(self):
        for value in (True,-1,1.0):
            self.receipt['root_KERNEL_ticks']=value
            with self.subTest(value=value):
                with self.assertRaises(ValueError):self.evaluate()
    def test_unknown_attempt_count_not_zero_imputed(self):
        result=self.evaluate()
        self.assertIsNone(result['reported_attempt_count']);self.assertFalse(result['attempted_birth_custody_verified'])
    def test_explicit_failed_and_rejected_attempts_still_not_native_proof(self):
        self.receipt['attempts']=[{'sequence':0,'precharged_before_effect':True,'outcome':'failed'},
                                  {'sequence':1,'precharged_before_effect':True,'outcome':'rejected'}]
        result=self.evaluate();self.assertEqual(result['reported_attempt_count'],2)
        self.assertFalse(result['attempted_birth_custody_verified'])
    def test_unpaid_rejected_creation_refused(self):
        self.receipt['attempts']=[{'sequence':0,'precharged_before_effect':False,'outcome':'rejected'}]
        with self.assertRaisesRegex(ValueError,'refunded'):self.evaluate()
    def test_missing_or_bad_closure_is_not_complete(self):
        self.receipt['closure']['EOF']=False;result=self.evaluate()
        self.assertFalse(result['build_closure_claimed']);self.assertFalse(result['build_closure_independently_qualified'])
    def test_changed_binary_refused(self):
        path,sha=self.package();(self.out/a.ARTIFACTS['guardian']).write_bytes(b'changed')
        with self.assertRaisesRegex(ValueError,'changed'):a.evaluate(path,sha)
    def test_changed_header_refused(self):
        path,sha=self.package();(self.out/a.ARTIFACTS['header']).write_bytes(b'new ledger pins')
        with self.assertRaises(ValueError):a.evaluate(path,sha)
    def test_combined_artifact_extent_bounded_before_hashing(self):
        path,sha=self.package()
        with (self.out/a.ARTIFACTS['guardian']).open('r+b') as stream:stream.truncate(64*1024**2)
        with self.assertRaisesRegex(ValueError,'Combined prebuilt'):a.evaluate(path,sha)
    def test_receipt_from_another_binary_refused(self):
        self.receipt['artifact_sha256']=dict(self.files,guardian='0'*64)
        with self.assertRaisesRegex(ValueError,'exact sources'):self.evaluate()
    def test_unreviewed_source_refused(self):
        self.source['experiments/native/eka1_probe_guardian.c']='0'*64
        with self.assertRaises(ValueError):self.evaluate()
    def test_legacy_build_receipt_cannot_claim_complete_costs(self):
        self.receipt['schema']='resource01-result-v1'
        with self.assertRaises(ValueError):self.evaluate()
    def test_shared_hardlinked_artifact_refused(self):
        os.link(self.out/a.ARTIFACTS['guardian'],self.out/'alias.exe')
        with self.assertRaisesRegex(ValueError,'Shared'):self.evaluate()
    def test_inline_build_inner_refuses_even_if_outer_gate_bypassed(self):
        with patch.object(p,'kernel') as kernel,patch.object(p,'Job') as job,patch('subprocess.Popen') as process:
            with self.assertRaisesRegex(o.NativeQualificationRequired,'INLINE_BUILD_RETIRED'):
                p._build(None,None,None,None,None)
            kernel.assert_not_called();job.assert_not_called();process.assert_not_called()
        self.assertFalse(hasattr(p,'bounded_build'))
    def test_public_build_failure_consumes_owner_without_calling_compiler(self):
        owner=o.NativeOwnerCandidate.__new__(o.NativeOwnerCandidate)
        owner._closed=False;owner._failed=None;owner._fail=Mock()
        with patch.object(p,'native_admission'),patch.object(p,'verify_reservations'),patch('subprocess.Popen') as process:
            with self.assertRaisesRegex(o.NativeQualificationRequired,'INLINE_BUILD_RETIRED'):
                p.build(self.out,owner,{},'0'*64,1000)
        owner._fail.assert_called_once();process.assert_not_called()

if __name__=='__main__':unittest.main()
