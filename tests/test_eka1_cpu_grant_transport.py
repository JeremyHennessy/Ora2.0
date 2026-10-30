"""Bounded offline transport/refusal checks: no process, compiler or World."""
import copy
import hashlib
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import Mock,patch
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from tools import eka1_cpu_grant_transport as t
from tools import eka1_native_probe as p
from tools import eka1_native_owner_candidate as o

class TransportChecks(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(dir=ROOT);self.base=Path(self.tmp.name)
        self.registry=self.base/'registry';self.birth=(19,200)
        self.patches=[patch.object(t,'REGISTRY',self.registry),patch.object(o,'current_birth',return_value=self.birth),patch.object(t,'tick',return_value=1000)]
        for item in self.patches:item.start()
        self.tool=self.base/'compiler-observation';self.tool.write_bytes(b'observation-not-native-proof')
        self.manifest={'schema':'EKA-CPU-PROSPECTIVE-ASSIGNMENT-v1','assignment_id':'single-cpu-fixture',
                       'purpose':'ONE_CPU_STRESS_ONLY','mode':3,'output_relative':'runs/eka1-cpu-offline-fixture-'+self.base.name,
                       'source':{n:t.digest((ROOT/n).read_bytes()) for n in p.SOURCE_FILES},
                       'interpreter':{'path':str(Path(sys.executable).resolve()),'sha256':t.digest(Path(sys.executable).read_bytes())},
                       'toolchain':{str(self.tool):t.digest(self.tool.read_bytes())},'limits':copy.deepcopy(t.LIMITS)}
        self.closure={str(ROOT/n):v for n,v in self.manifest['source'].items()}
        self.closure[str(Path(sys.executable).resolve())]=self.manifest['interpreter']['sha256']
        self.manifest['interpreter']['closure_sha256']=t.digest(o.canonical(self.closure))
        self.closure_patch=patch.object(p,'custody',return_value=self.closure);self.closure_patch.start()
        self.mp=self.base/'manifest.json';self.gp=self.base/'grant.json';self.fd=None;self.out=None;self.owner=None
    def tearDown(self):
        if self.fd is not None and (self.owner is None or self.owner._fd is not None):os.close(self.fd)
        if self.out is not None:
            import shutil
            shutil.rmtree(self.out)
        for item in reversed(self.patches):item.stop()
        self.closure_patch.stop()
        self.tmp.cleanup()
    def artifacts(self,change=None):
        self.mp.write_bytes(o.canonical(self.manifest));self.msha=t.digest(self.mp.read_bytes())
        g={'schema':'EKA-CPU-OPERATOR-APPROVAL-v1','manifest_sha256':self.msha,'assignment_id':self.manifest['assignment_id'],
           'authorization':'EXPLICIT_HUMAN_OPERATOR','acknowledge_nondeterministic_CPU_overshoot':True,'attempts':1}
        if change:change(g)
        self.gp.write_bytes(o.canonical(g));self.gsha=t.digest(self.gp.read_bytes())
    def consume(self):return t.CpuGrantTransport(self.mp,self.gp,manifest_sha256=self.msha,operator_grant_sha256=self.gsha)
    def binding(self,transport):
        self.out=ROOT/self.manifest['output_relative'];self.out.mkdir(parents=True)
        registration={'global_end_tick':121000,'execution_modes':[3],'source':self.closure,'interpreter':str(Path(sys.executable).resolve())}
        (self.out/'registration.json').write_bytes(o.canonical(registration));seal=t.digest((self.out/'registration.json').read_bytes())
        owner=o.NativeOwnerCandidate.__new__(o.NativeOwnerCandidate);self.owner=owner
        owner._closed=False;owner._failed=None;owner._cleanup_errors=[]
        owner._birth=self.birth;owner._assignment=seal;owner._path=self.out/'ledger'
        self.fd=os.open(owner._path,os.O_CREAT|os.O_EXCL|os.O_RDWR|os.O_BINARY,0o600);os.write(self.fd,b'precharged36')
        fd=os.fstat(self.fd);owner._fd=self.fd;owner._physical=(fd.st_dev,fd.st_ino)
        owner._ledger=Mock(_bytes=fd.st_size)
        def check():
            if owner._closed or owner._failed is not None:raise RuntimeError('Owner closed/incomplete')
        owner._check=Mock(side_effect=check)
        with patch.object(p,'verify_reservations',return_value=registration):
            result=transport.bind(owner,self.out,seal,121000)
        return owner,result
    def test_once_bind_cannot_enable_native_even_with_matching_approval_json(self):
        self.artifacts();v=self.consume();owner,bound=self.binding(v)
        self.assertEqual(bound['producer_birth'],list(self.birth))
        self.assertEqual(v.preflight()['decision'],'NO_GO')
        self.assertFalse(v.preflight()['operator_approval_alone_sufficient'])
        with self.assertRaises(o.NativeQualificationRequired):p.native_admission(v)
    def test_fixed_registry_prevents_new_output_from_refunding_claim(self):
        self.artifacts();self.consume()
        with self.assertRaises(FileExistsError):self.consume()
        self.assertEqual(len(list(self.registry.glob('*.consumed.json'))),2)
    def test_new_manifest_hash_cannot_refund_same_assignment_id(self):
        self.artifacts();self.consume()
        self.manifest['output_relative']+='-changed';self.artifacts()
        with self.assertRaises(FileExistsError):self.consume()
    def test_delayed_binding_cannot_mint_fresh_deadline(self):
        self.artifacts();v=self.consume()
        with patch.object(t,'tick',return_value=121000):
            with self.assertRaisesRegex(ValueError,'absolute deadline'):self.binding(v)
        self.assertTrue(v.failed)
    def test_failed_grant_validation_burns_claim(self):
        self.artifacts(lambda g:g.update(acknowledge_nondeterministic_CPU_overshoot=False))
        with self.assertRaisesRegex(ValueError,'acknowledgement'):self.consume()
        with self.assertRaises(FileExistsError):self.consume()
    def test_bool_attempt_is_not_one_attempt(self):
        self.artifacts(lambda g:g.update(attempts=True))
        with self.assertRaises(ValueError):self.consume()
    def test_changed_threshold_is_refused_and_consumed(self):
        self.manifest['limits']['private_USER_ticks']+=1;self.artifacts()
        with self.assertRaises(ValueError):self.consume()
        self.assertTrue(list(self.registry.glob('*.consumed.json')))
    def test_wrong_external_grant_hash_never_accepted(self):
        self.artifacts();self.gsha='0'*64
        with self.assertRaisesRegex(ValueError,'Pinned artifact'):self.consume()
    def test_second_bind_fails_without_reusable_authority(self):
        self.artifacts();v=self.consume();self.binding(v)
        with self.assertRaisesRegex(RuntimeError,'second bind'):v.bind(None,None,None,None)
        with self.assertRaisesRegex(RuntimeError,'No complete'):v.preflight()
        self.assertTrue(self.owner._closed)
        with self.assertRaises(RuntimeError):self.owner.ledger
    def test_replaced_same_byte_registry_marker_refused(self):
        self.artifacts();v=self.consume();self.binding(v)
        new=v.marker.with_suffix('.copy');new.write_bytes(v.marker.read_bytes());os.replace(new,v.marker)
        with self.assertRaisesRegex(ValueError,'physical artifact'):v.preflight()
    def test_changed_consumer_birth_refused_before_binding(self):
        self.artifacts();v=self.consume()
        with patch.object(o,'current_birth',return_value=(20,201)):
            with self.assertRaisesRegex(ValueError,'original consuming'):self.binding(v)
        self.assertTrue(v.failed)
    def test_changed_ledger_same_extent_is_terminal(self):
        self.artifacts();v=self.consume();owner,bound=self.binding(v)
        owner._path.write_bytes(b'changed_1234')
        with self.assertRaises(ValueError):v.preflight()
        self.assertTrue(v.failed)
        self.assertTrue(owner._closed)
    def test_replaced_ledger_same_bytes_and_extent_is_terminal(self):
        self.artifacts();v=self.consume();owner,bound=self.binding(v)
        other=owner._path.with_suffix('.other');other.write_bytes(owner._path.read_bytes())
        os.close(self.fd);self.fd=None;os.replace(other,owner._path)
        self.fd=os.open(owner._path,os.O_RDWR|os.O_BINARY);owner._fd=self.fd
        with self.assertRaisesRegex(ValueError,'physical ledger'):v.preflight()
    def test_changed_registration_refused(self):
        self.artifacts();v=self.consume();self.binding(v)
        (self.out/'registration.json').write_bytes(b'{}')
        with self.assertRaisesRegex(ValueError,'registration'):v.preflight()
    def test_changed_grant_after_bind_is_terminal(self):
        self.artifacts();v=self.consume();self.binding(v);self.gp.write_bytes(b'{}')
        with self.assertRaises(ValueError):v.preflight()
        with self.assertRaises(RuntimeError):v.preflight()
        self.assertTrue(self.owner._closed)
    def test_original_deadline_expiry_no_extension(self):
        self.artifacts();v=self.consume();self.binding(v)
        with patch.object(t,'tick',return_value=121000):
            with self.assertRaisesRegex(ValueError,'deadline'):v.preflight()
    def test_binding_write_failure_consumes_authority(self):
        self.artifacts();v=self.consume()
        with patch.object(t,'save',side_effect=OSError('archive fixture')):
            with self.assertRaises(OSError):self.binding(v)
        self.assertTrue(v.bound and v.failed)
        self.assertTrue(self.owner._closed)
        with self.assertRaises(RuntimeError):v.bind(None,None,None,None)
    def test_changed_library_closure_is_terminal_before_execution(self):
        self.artifacts();v=self.consume();self.binding(v)
        with patch.object(p,'custody',return_value={}):
            with self.assertRaisesRegex(ValueError,'closure changed'):v.preflight()
        self.assertTrue(self.owner._closed)
    def test_registered_closure_cannot_differ_from_static_approval(self):
        self.artifacts();v=self.consume()
        real=self.closure
        # Keep static observation valid; only the independently verified runtime
        # registration fixture is altered at the boundary under test.
        with patch.object(p,'verify_reservations',return_value={'global_end_tick':121000,'execution_modes':[3],'source':{},'interpreter':str(Path(sys.executable).resolve())}):
            # binding() normally supplies its own verified fixture; override it
            # by changing just the declaration returned by that nested patch.
            old_patch=patch.object(t,'tick',return_value=1000)
            old_patch.start()
            try:
                owner=o.NativeOwnerCandidate.__new__(o.NativeOwnerCandidate)
                owner._birth=self.birth;owner._fail=Mock()
                self.out=ROOT/self.manifest['output_relative'];self.out.mkdir(parents=True)
                with self.assertRaisesRegex(ValueError,'static approval'):v.bind(owner,self.out,'a'*64,121000)
                owner._fail.assert_called_once()
            finally:old_patch.stop()
    def test_missing_source_dependency_refused(self):
        del self.manifest['source']['tools/eka1_cpu_accounting.py'];self.artifacts()
        with self.assertRaisesRegex(ValueError,'source list'):self.consume()

if __name__=='__main__':unittest.main()
