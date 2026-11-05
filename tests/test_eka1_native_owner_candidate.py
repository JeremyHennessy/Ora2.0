"""Bounded offline owner/physical-ledger integration; never import or run a World.

Private registry patches isolate unittest cases only; no production reset API.
AST extraction executes the exact entrypoint bodies, replacing only the metadata
parser with inert metadata and native loaders with forbidden sentinels.
"""
import ast
import hashlib
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from tools import eka1_native_owner_candidate as native
from tools import eka1_cumulative_reservations as budget


def wrapper_scope(derived):
    name='digital_eka1_derived_reconstruction_v1.py' if derived else 'digital_eka1_selection_replay_v1.py'
    tree=ast.parse((ROOT/'experiments'/name).read_bytes())
    target='reconstruct_and_verify' if derived else 'replay_original_selection'
    names={'reservation_class','owner_class',target}
    nodes=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in names]
    pinname='SOURCE_PINS' if derived else 'INPUT_PINS'
    pins=ast.literal_eval(next(n.value for n in tree.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id==pinname for t in n.targets)))
    def forbidden():raise AssertionError('Native runtime loader reached')
    scope={'ROOT':ROOT,'Path':Path,'hashlib':hashlib,pinname:pins,
           'request_metadata':lambda r:r['configuration'],'prepare':lambda *a:({},{}),
           'metadata_inputs':forbidden,'runtime_sources':forbidden}
    exec(compile(ast.Module(body=nodes,type_ignores=[]),str(ROOT/'experiments'/name),'exec'),scope)
    return scope,target


class NativeOwnerChecks(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(dir=ROOT)
        self.path=Path(self.tmp.name)/'ledger.jsonl'
        self.isolation=patch.multiple(native,_active=None,_consumed=set(),_lifetime_used=False)
        self.isolation.start()
        self.owner=None
        self.request={'configuration':{'dose':1},'assignment_id':'offline-only',
                      'assigned_stop_tick':4096,'stop_tick':4096,'arm':'true',
                      'binding':{'original_world_id':'offline-only'}}
        digest=hashlib.sha256(native.canonical(self.request)).hexdigest()
        self.hashes={(d,r):digest for d in (1,8) for r in native.ROLES}
    def tearDown(self):
        if self.owner is not None:self.owner.close()
        self.isolation.stop();self.tmp.cleanup()
    def make(self,**changes):
        args=dict(owner_birth=native.current_birth(),assignment_id='offline-only',request_hashes=self.hashes)
        args.update(changes)
        self.owner=native.NativeOwnerCandidate(self.path,**args)
        return self.owner
    def invoke(self,derived=False,**changes):
        scope,target=wrapper_scope(derived)
        kwargs=dict(reservations=self.owner.ledger,genesis_index=0,owner=self.owner)
        kwargs.update(changes)
        return scope[target](b'',b'',self.request,**kwargs) if derived else scope[target](b'',self.request,**kwargs)
    def replay(self,**changes):
        args=dict(assignment_id='offline-only',dose=1,role='true',request=self.request,genesis_index=0)
        args.update(changes)
        return self.owner.replay(self.owner.ledger,**args)
    def rows(self):return [__import__('json').loads(v) for v in self.path.read_bytes().splitlines()]
    def test_real_current_windows_birth_is_stable(self):
        a=native.current_birth();self.assertEqual(a,native.current_birth());self.assertEqual(a[0],os.getpid());self.assertGreater(a[1],0)
    def test_selection_entry_burns_full_envelope_before_hold(self):
        o=self.make();ledger=o.ledger
        with self.assertRaisesRegex(native.NativeQualificationRequired,'NOT_READY'):self.invoke()
        self.assertTrue(o._closed);self.assertTrue(ledger._closed)
        self.assertEqual(ledger._genesis[1][0],4096)
        self.assertEqual([r['reservation']['kind'] for r in self.rows()],['role','genesis','dispatch'])
        self.assertTrue(all(r['execution_authenticated'] is False for r in self.rows()))
    def test_derived_entry_burns_full_hidden_prefix_and_tail_before_hold(self):
        o=self.make();ledger=o.ledger
        with self.assertRaises(native.NativeQualificationRequired):self.invoke(True)
        self.assertEqual(ledger._genesis[1][0],4096)
    def test_attempted_launch_charged_but_no_process_created(self):
        o=self.make();ledger=o.ledger
        with self.assertRaises(native.NativeQualificationRequired):
            o.launch_role(assignment_id='offline-only',dose=1,role='original_producer',request=self.request)
        self.assertEqual(ledger._births,1)
        self.assertEqual([r['reservation']['kind'] for r in self.rows()],['role','process_birth'])
    def test_terminal_hold_never_refunds_or_reopens_with_new_label(self):
        o=self.make()
        with self.assertRaises(native.NativeQualificationRequired):self.replay()
        raw=self.path.read_bytes()
        with self.assertRaises(RuntimeError):self.replay()
        with self.assertRaisesRegex(ValueError,'no replacement'):
            native.NativeOwnerCandidate(Path(self.tmp.name)/'alternate',owner_birth=native.current_birth(),assignment_id='new-label',request_hashes=self.hashes)
        self.assertEqual(raw,self.path.read_bytes());self.assertFalse((Path(self.tmp.name)/'alternate').exists())
    def test_failed_exclusive_open_also_consumes_lifetime(self):
        self.path.write_bytes(b'existing')
        with self.assertRaises(FileExistsError):self.make()
        with self.assertRaisesRegex(ValueError,'no replacement'):
            native.NativeOwnerCandidate(Path(self.tmp.name)/'other',owner_birth=native.current_birth(),assignment_id='different',request_hashes=self.hashes)
        self.assertEqual(self.path.read_bytes(),b'existing')
    def test_alternate_ledger_rejected_before_genesis(self):
        o=self.make();ledger=o.ledger
        with self.assertRaisesRegex(ValueError,'Alternate ledger'):
            o.replay(object(),assignment_id='offline-only',dose=1,role='true',request=self.request,genesis_index=0)
        self.assertEqual(ledger._genesis[1],{});self.assertEqual(self.path.read_bytes(),b'')
    def test_changed_owner_birth_terminally_refuses(self):
        o=self.make()
        with patch.object(native,'current_birth',return_value=(os.getpid(),1)):
            with self.assertRaisesRegex(RuntimeError,'birth differs'):o.ledger
        self.assertTrue(o._closed)
    def test_forged_constructor_birth_refused_without_file(self):
        with self.assertRaises(ValueError):self.make(owner_birth=(os.getpid(),1))
        self.assertFalse(self.path.exists())
    def test_enclosing_deadline_refuses_before_reservation(self):
        o=self.make()
        with patch.object(native.time,'monotonic',return_value=o._deadline):
            with self.assertRaises(TimeoutError):o.ledger
        self.assertEqual(self.path.read_bytes(),b'');self.assertTrue(o._closed)
    def test_role_deadline_includes_reservation_time(self):
        o=self.make();start=o._started
        # property check, enter check, role deadline start, post-role check.
        with patch.object(native.time,'monotonic',side_effect=[start,start,start,start+181]):
            with self.assertRaises(TimeoutError):self.replay()
        # Deadline reached in the post-role check; no native path reached.
        self.assertTrue(o._closed)
    def test_slow_role_fsync_cannot_extend_deadline(self):
        o=self.make();clock=[o._started];sync=budget.os.fsync
        def delayed(fd):
            sync(fd);clock[0]+=181
        with patch.object(native.time,'monotonic',side_effect=lambda:clock[0]),patch.object(budget.os,'fsync',side_effect=delayed):
            with self.assertRaises(TimeoutError):self.replay()
        self.assertEqual([r['reservation']['kind'] for r in self.rows()],['role'])
        self.assertTrue(o._closed)
    def test_changed_physical_extent_refused(self):
        o=self.make()
        with self.path.open('ab') as f:f.write(b'external')
        with self.assertRaises(OSError):o.ledger
        self.assertEqual(self.path.read_bytes(),b'external')
    def test_offset_drift_refused(self):
        o=self.make();os.lseek(o._fd,1,os.SEEK_SET)
        with self.assertRaises(OSError):o.ledger
    def test_parent_reparse_detected_on_operation(self):
        o=self.make();original=Path.is_symlink
        with patch.object(Path,'is_symlink',lambda p:p==self.path.parent or original(p)):
            with self.assertRaisesRegex(OSError,'ancestry'):o.ledger
        self.assertTrue(o._closed)
    def test_hardlinked_ledger_refused(self):
        o=self.make();os.link(self.path,Path(self.tmp.name)/'alias')
        with self.assertRaises(OSError):o.ledger
    def test_request_hashes_copied_not_retained_by_reference(self):
        o=self.make();self.hashes[1,'true']='0'*64
        with self.assertRaises(native.NativeQualificationRequired):self.replay()
    def test_mutated_request_refused_before_charge(self):
        o=self.make();self.request['stop_tick']=1
        with self.assertRaisesRegex(ValueError,'request differs'):self.replay()
        self.assertEqual(self.path.read_bytes(),b'')
    def test_boolean_dose_request_hash_key_refused(self):
        digest=self.hashes.pop((1,'owner'));self.hashes[True,'owner']=digest
        with self.assertRaises(ValueError):self.make()
        self.assertFalse(self.path.exists())
    def test_over_budget_dispatch_refused_after_genesis_and_role_burn(self):
        self.request['stop_tick']=4097
        self.hashes={(d,r):hashlib.sha256(native.canonical(self.request)).hexdigest() for d in (1,8) for r in native.ROLES}
        o=self.make();ledger=o.ledger
        with self.assertRaises(ValueError):self.replay()
        self.assertEqual(ledger._genesis[1],{0:0});self.assertTrue(o._closed)
    def test_precharge_sync_failure_preserves_bytes_and_closes(self):
        o=self.make()
        with patch.object(budget.os,'fsync',side_effect=OSError('offline fsync failure')):
            with self.assertRaisesRegex(OSError,'fsync'):self.replay()
        raw=self.path.read_bytes();self.assertTrue(raw);self.assertTrue(o._closed)
        with self.assertRaises(RuntimeError):self.replay()
        self.assertEqual(raw,self.path.read_bytes())
    def test_reservation_partial_write_terminal(self):
        o=self.make();write=budget.os.write
        def short(fd,raw):return write(fd,raw[:5])
        with patch.object(budget.os,'write',side_effect=short):
            with self.assertRaisesRegex(OSError,'Short'):self.replay()
        self.assertEqual(len(self.path.read_bytes()),5);self.assertTrue(o._closed)
    def test_wrong_assignment_and_request_arm_refused(self):
        o=self.make()
        with self.assertRaisesRegex(ValueError,'Alternate ledger/assignment'):self.replay(assignment_id='another')
        self.assertEqual(self.path.read_bytes(),b'')
    def test_mismatched_arm_even_in_fixed_catalog_refused(self):
        self.request['arm']='xor1'
        self.hashes={(d,r):hashlib.sha256(native.canonical(self.request)).hexdigest() for d in (1,8) for r in native.ROLES}
        self.make()
        with self.assertRaisesRegex(ValueError,'arm differs'):self.replay()
        self.assertEqual(self.path.read_bytes(),b'')
    def test_smaller_caller_supplied_restore_bound_has_no_api(self):
        self.make()
        with self.assertRaises(TypeError):self.replay(stop_tick=1)
        self.assertEqual(self.path.read_bytes(),b'')
    def test_expired_owner_blocks_both_metadata_parsers(self):
        o=self.make();ledger=o.ledger
        for derived in (False,True):
            scope,target=wrapper_scope(derived)
            def forbidden(*args):raise AssertionError('Parser before owner/deadline')
            scope['prepare']=scope['request_metadata']=forbidden
            with patch.object(native.time,'monotonic',return_value=o._deadline):
                with self.assertRaises((TimeoutError,RuntimeError)):
                    scope[target](*([b'',b'',self.request] if derived else [b'',self.request]),reservations=ledger,genesis_index=0,owner=o)
        self.assertEqual(self.path.read_bytes(),b'')
    def test_dispatch_sync_failure_retains_full_attempted_charge(self):
        o=self.make()
        with patch.object(budget.os,'fsync',side_effect=[None,None,OSError('dispatch sync failed')]):
            with self.assertRaisesRegex(OSError,'dispatch sync'):self.replay()
        raw=self.path.read_bytes()
        self.assertIn(b'"count":4096',raw);self.assertTrue(o._closed)
        with self.assertRaises(RuntimeError):self.replay()
        self.assertEqual(raw,self.path.read_bytes())
    def test_native_modules_not_imported(self):
        self.assertFalse(any(n.startswith('experiments.digital_') for n in sys.modules))

if __name__=='__main__':unittest.main(verbosity=2)
