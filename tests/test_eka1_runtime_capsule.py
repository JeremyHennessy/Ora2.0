"""Offline capsule fixtures only. No executable or OS enforcement qualification."""
import hashlib
from pathlib import Path
import sys
import unittest
from unittest.mock import patch,Mock
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from tools import eka1_runtime_capsule as c
from tests import test_eka1_cpu_grant_transport as transport_fixture

class CodecChecks(unittest.TestCase):
    def value(self):
        return dict(owner_pid=19,owner_birth=200,ledger_volume=1,ledger_extent=12,
                    global_end=121000,role_end=9000,ledger_id=bytes(range(16)),
                    **{n:'a'*64 for n in c.HASH_FIELDS})
    def test_exact_abi(self):
        v=self.value();raw=c.encode(v)
        self.assertEqual(len(raw),478);self.assertEqual(c.decode(raw,1000),v)
    def test_expired_and_extended_deadlines(self):
        for now in [9000,121000]:
            with self.assertRaises(ValueError):c.decode(c.encode(self.value()),now)
        with self.assertRaises(ValueError):c.decode(c.encode(self.value()),999)
    def test_extra_authority_fields_refused(self):
        for name in ['command','memory_limit','owner','ledger_path']:
            v=self.value();v[name]='substitution'
            with self.assertRaises(ValueError):c.encode(v)
    def test_invalid_integer_types_and_ranges(self):
        for name,value in [('owner_pid',True),('owner_pid',2**32),('ledger_extent',0),('owner_birth',-1)]:
            v=self.value();v[name]=value
            with self.assertRaises(ValueError):c.encode(v)
    def test_noncanonical_frames(self):
        raw=c.encode(self.value())
        for changed in [raw[:-1],raw+b'x',b'X'+raw[1:],raw[:20]+b'\x01'+raw[21:],raw[:-1]+b'x']:
            with self.assertRaises(ValueError):c.decode(changed,1000)
    def test_native_gate_and_assignment_independence(self):
        header=(ROOT/'experiments/native/eka1_runtime_capsule.h').read_text()
        source=(ROOT/'experiments/native/eka1_probe_guardian.c').read_text()
        self.assertIn('#define EKA_CAPSULE_SOURCE_ONLY 1',header)
        self.assertIn('if(EKA_CAPSULE_SOURCE_ONLY)return 125',source)
        for old in ['EKA_OWNER_PID','EKA_OWNER_BIRTH','EKA_GLOBAL_END','EKA_SEAL','EKA_MARKER_ROOT']:
            self.assertNotIn(old,source)
    def test_release_header_has_no_run_binding(self):
        pins=dict(python=str(Path(sys.executable).resolve()),python_sha='a'*64,
                  program=str(ROOT/'tools/eka1_probe_child.py'),program_sha='b'*64,
                  watchdog=str(ROOT/'watchdog.dll'),watchdog_sha='c'*64)
        header=c.release_header(pins).decode('ascii')
        for forbidden in ['OWNER_PID','OWNER_BIRTH','GLOBAL_END','LEDGER_ID','EKA_SEAL']:
            self.assertNotIn(forbidden,header)
        pins['owner_pid']=19
        with self.assertRaises(ValueError):c.release_header(pins)

class CapsuleBindingChecks(transport_fixture.TransportChecks):
    # Reuse fixture setup, not the baseline test suite.
    def fixture(self):
        self.artifacts();t=self.consume();owner,_=self.binding(t)
        image=self.out/'eka1_probe_guardian.exe';image.write_bytes(b'fixture-not-executable')
        return t,owner,image
    def test_capsule_once_and_original_deadline(self):
        t,owner,image=self.fixture();handles=[]
        def retained(*args):
            h=Mock(handle=123);handles.append(h);return h
        with patch.object(c,'tick',return_value=1000),patch.object(c,'ledger_file_id',return_value=(1,b'x'*16)),patch.object(c,'CapsuleReadHandle',side_effect=retained):
            result=c.prepare(t,owner,image,hashlib.sha256(image.read_bytes()).hexdigest())
            self.assertFalse(result['native_entry_enabled'])
            self.assertEqual(result['facts']['global_end'],121000)
            with self.assertRaisesRegex(RuntimeError,'consumed'):c.prepare(t,owner,image,'a'*64)
        self.assertTrue(t.failed);self.assertTrue(owner._closed)
        for h in handles:h.close()
    def test_failed_image_pin_burns_attempt_and_owner(self):
        t,owner,image=self.fixture()
        with patch.object(c,'CapsuleReadHandle',side_effect=OSError('pin failed')):
            with self.assertRaisesRegex(OSError,'pin failed'):c.prepare(t,owner,image,'a'*64)
        self.assertTrue(t.failed);self.assertTrue(owner._closed)
        self.assertTrue(t._capsule_consumed)
    def test_capsule_failure_retains_partial_and_closes_image(self):
        t,owner,image=self.fixture();retained=Mock(handle=123)
        with patch.object(c,'tick',return_value=1000),patch.object(c,'ledger_file_id',return_value=(1,b'x'*16)),patch.object(c,'CapsuleReadHandle',side_effect=[retained,OSError('capsule pin failed')]):
            with self.assertRaisesRegex(OSError,'capsule pin failed'):c.prepare(t,owner,image,'a'*64)
        self.assertEqual((self.out/'3.runtime-capsule.bin').stat().st_size,478)
        retained.close.assert_called_once();self.assertTrue(owner._closed)

# Inherit only the reusable fixture, not baseline checks already accepted.
for _name in list(transport_fixture.TransportChecks.__dict__):
    if _name.startswith('test_'):setattr(CapsuleBindingChecks,_name,None)

if __name__=='__main__':unittest.main()
