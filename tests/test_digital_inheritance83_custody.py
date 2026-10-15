"""Non-physics receipt fixtures; no World or label generator imported."""
import copy
import hashlib
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from experiments import digital_inheritance83_custody as c
from experiments import digital_inheritance83_primary_child as child
from experiments.evidence_budget import Budget
from experiments.evidence_write_grant68 import seal, record


class Custody(unittest.TestCase):
    def setUp(self):
        if os.environ.get('ORALAB_KEEP_FIXTURES'):
            from types import SimpleNamespace
            p=Path(os.environ['ORALAB_KEEP_FIXTURES'])/self._testMethodName
            p.mkdir(parents=True)
            self.temp=SimpleNamespace(name=str(p))
        else:
            self.temp = tempfile.TemporaryDirectory(dir=os.environ.get('ORALAB_TEST_TMP'))
            self.addCleanup(self.temp.cleanup)

    def fixture(self):
        root=Path(self.temp.name)/('case'+str(len(list(Path(self.temp.name).iterdir()))))
        b=Budget(root,dict(raw=128*c.M),128*c.M)
        pins={'fixture_only':'a'*64};role=c.plan()[0]
        grant,signature=seal(b,'raw','fixture.json',64*c.M,c.digest(pins),c.digest(c.CONFIG),role)
        req=dict(configuration=copy.deepcopy(c.CONFIG),source_files=pins,source_sha=c.digest(pins),
                 config_sha=c.digest(c.CONFIG),role=role,kind='generate',input=None,grant=grant,seal=signature)
        receipt=record(grant,signature,c.digest(pins),c.digest(c.CONFIG),role,dict(non_physics_fixture=True))
        out=dict(role=role,source_sha=c.digest(pins),config_sha=c.digest(c.CONFIG),receipt=receipt,error=None)
        native=dict(exit_code=0,timed_out=False,output_truncated=False,post_close_processes_exited=True,
                    usage=dict(active_before_close=0),output=c.canonical(out).decode())
        return role,req,native,pins,grant

    def test_whole_roster_and_precharge_arithmetic(self):
        roles=c.plan();a=c.allocations()
        self.assertEqual(len(roles),257)
        self.assertEqual(sum(r.endswith(':generate') for r in roles),160)
        self.assertEqual(sum(r.endswith(':audit') for r in roles),80)
        self.assertEqual(sum(r.endswith(':metrics') for r in roles),16)
        self.assertLess(sum(a.values())+64*c.M,12288*c.M)
        self.assertEqual(sum(k.startswith('native/') for k in a),261)
        self.assertEqual(child.CONFIG,c.CONFIG)

    def test_real_sealed_file_receipt(self):
        role,req,n,pins,g=self.fixture()
        spec=c.consume(role,None,req,n,pins,g)
        self.assertEqual(spec['sha256'],hashlib.sha256(Path(spec['path']).read_bytes()).hexdigest())

    def test_detached_native_input_source_grant_and_cleanup_refused(self):
        edits=[lambda r,n:r.update(input={'detached':True}),
               lambda r,n:r.update(source_sha='0'*64),
               lambda r,n:r.update(seal='0'*64),
               lambda r,n:r['grant'].update(inode=0),
               lambda r,n:n.update(exit_code=1),
               lambda r,n:n.update(timed_out=True),
               lambda r,n:n.update(output_truncated=True),
               lambda r,n:n.update(post_close_processes_exited=False),
               lambda r,n:n['usage'].update(active_before_close=1)]
        for i,edit in enumerate(edits):
            role,req,n,pins,g=self.fixture();expected=copy.deepcopy(g);edit(req,n)
            with self.subTest(edit=i),self.assertRaises(AssertionError):c.consume(role,None,req,n,pins,expected)

    def test_forged_native_receipt_and_changed_physical_body_refused(self):
        for field in ('role','source_sha','config_sha','sha256','extent','grant_sha256'):
            role,req,n,pins,g=self.fixture();out=json.loads(n['output'])
            out['receipt'][field]=0 if field=='extent' else '0'*64
            n['output']=json.dumps(out)
            with self.subTest(field=field),self.assertRaises(AssertionError):c.consume(role,None,req,n,pins,g)
        role,req,n,pins,g=self.fixture();(Path(g['root'])/'raw'/g['name']).write_bytes(b'{}')
        with self.assertRaises(AssertionError):c.consume(role,None,req,n,pins,g)

    def test_complete_orchestration_mock_keeps_every_input_dependency(self):
        grants={r:dict(device=1,inode=i,limit=(64 if r.endswith(':generate') else 8)*c.M)
                for i,r in enumerate(c.plan(),1)}
        calls=[];validated=[]
        def launch(role,inputs):calls.append((role,inputs));return {},{}
        def consume(role,inputs,request,native,pins,grant):
            if role.endswith(':audit'):self.assertIsNotNone(inputs)
            if role.endswith(':metrics'):
                self.assertEqual([x['mode'] for x in inputs],list(c.MODES))
                self.assertTrue(all(set(x)=={'mode','record','proof'} for x in inputs))
            if role=='final:acceptance':self.assertEqual(len(inputs),16)
            # An opaque NON-PHYSICS token, never a relabelled organism record.
            token=role.replace('restored:','original:')
            return dict(path='NON-PHYSICS/'+token,extent=1,sha256=hashlib.sha256(token.encode()).hexdigest())
        with patch('experiments.digital_cognitive76_child.validate_grant'),patch.object(c,'consume',consume):
            result=c.pipeline(launch,{},grants,validated)
        self.assertEqual(validated,c.plan());self.assertEqual(len(calls),257)
        self.assertEqual(result['original_cells'],80)
        self.assertFalse(result['primary_admitted'])

    def test_pipeline_stops_at_parity_failure_and_missing_slot_before_launch(self):
        grants={r:dict(device=1,inode=i,limit=(64 if r.endswith(':generate') else 8)*c.M)
                for i,r in enumerate(c.plan(),1)}
        calls=[]
        def launch(role,inputs):calls.append(role);return {},{}
        def mismatch(role,*unused):return dict(path='NON-PHYSICS',extent=1,sha256=role)
        with patch('experiments.digital_cognitive76_child.validate_grant'),patch.object(c,'consume',mismatch):
            with self.assertRaisesRegex(AssertionError,'producer parity'):c.pipeline(launch,{},grants)
        self.assertEqual(len(calls),2)
        calls.clear();grants.pop('final:acceptance')
        with self.assertRaises(AssertionError):c.pipeline(launch,{},grants)
        self.assertEqual(calls,[])

    def test_child_rejects_foreign_roles_before_world_import(self):
        before='experiments.digital_inheritance83_world' in __import__('sys').modules
        for seed in (2140080,2100080,1009000,1009200):
            req=dict(configuration=copy.deepcopy(c.CONFIG),role=f'original:{seed}:variation:generate',kind='generate',input=None)
            with self.assertRaisesRegex(AssertionError,'role'):child.role_parts(req)
        req=dict(configuration=dict(c.CONFIG,horizon=1),role=c.plan()[0],kind='generate',input=None)
        with self.assertRaisesRegex(AssertionError,'configuration'):child.role_parts(req)
        self.assertEqual(before,'experiments.digital_inheritance83_world' in __import__('sys').modules)

    def test_batch_releases_previous_payload_before_next_read(self):
        import gc
        import weakref
        class Payload: pass
        def inputs():
            for mode in c.MODES:
                state=dict(seed=0,mode=mode,payload=Payload())
                reference=weakref.ref(state['payload'])
                yield state,{}
                del state
                gc.collect()
                assert reference() is None,'previous full history retained before next read'
        def tiny_metric(state,proof):return dict(seed=state['seed'],mode=state['mode'],post_expansion_served={})
        def retained_old_zip_pattern(rows):
            values=[]
            for mode,pair in zip(c.MODES,rows,strict=True):
                state,proof=pair;values.append(tiny_metric(state,proof))
                del pair,state,proof
                gc.collect()
            return values
        with self.assertRaisesRegex(AssertionError,'previous full history retained'):
            retained_old_zip_pattern(inputs())
        with patch('experiments.digital_inheritance83_fitness.metrics',tiny_metric):
            result=child.batch_metrics(0,inputs())
            self.assertEqual([m['mode'] for m in result['metrics']],list(c.MODES))
            with self.assertRaises(StopIteration):child.batch_metrics(0,iter([]))

    def test_batch_child_key_table_has_guarded_canonical_round_trip(self):
        old=dict(post_expansion_served={1:3,2:4,10:5,11:6})
        raw=c.canonical(old)
        self.assertNotEqual(raw,c.canonical(json.loads(raw)))
        rows=[(dict(seed=0,mode=m),{}) for m in c.MODES]
        with patch('experiments.digital_inheritance83_fitness.metrics',lambda s,p:copy.deepcopy(old)):
            fixed=child.batch_metrics(0,iter(rows))
        encoded=c.canonical(fixed)
        self.assertEqual(encoded,c.canonical(json.loads(encoded)))
        self.assertEqual(fixed['metrics'][0]['post_expansion_served'],{'1':3,'2':4,'10':5,'11':6})


if __name__=='__main__':unittest.main()
