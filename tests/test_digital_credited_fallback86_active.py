"""Pure scopes, budget arithmetic and real orchestration with NON-PHYSICS mocks."""
import ast
import copy
import hashlib
import json
from pathlib import Path
import unittest
import weakref
import tempfile
import os
from unittest.mock import patch
from types import SimpleNamespace
from experiments.digital_credited_fallback86_active_child import CONFIG,scope
from experiments.digital_credited_fallback86_active_plan import (
    ROLES,capacity,layout,registration_capacity,admit_ci,orchestrate,annotated_bound,recording_bound,M)


class ActiveCustody(unittest.TestCase):
    def base(self,role=ROLES[0]):
        kind=role.split(':')[-1]
        return dict(configuration=copy.deepcopy(CONFIG),source_files={},source_sha='',config_sha='',
            role=role,kind=kind,input=None if kind=='generate' else dict(path='x',extent=1,sha256='0'*64),grant={},seal='')

    def test_scope_all_cells_and_cached_foreign_refusals(self):
        self.assertEqual(len(ROLES),48)
        for role in ROLES:self.assertEqual(scope(self.base(role)),role.split(':')[-1])
        for role in ('original:2100080:generate','original:2100080:intact:generate',
            'original:1009400:model_erased:generate','original:1009300:model_erased:generate',
            'original:2140080:model_erased:generate','original:2100084:model_erased:generate'):
            with self.assertRaises(AssertionError):scope(self.base(role))
        for field,value in (('horizon',256),('warm',12),('decisions',59),('software_only',1),
                            ('cases',[[8,'model']]),('arms',['model_erased'])):
            request=self.base();request['configuration'][field]=value
            with self.assertRaises(AssertionError):scope(request)
        request=self.base();request['input']={'copied_warm_state':1}
        with self.assertRaises(AssertionError):scope(request)
        request=self.base(ROLES[1]);request['input']['unbound']=1
        with self.assertRaises(AssertionError):scope(request)

    def test_full_precharge_and_annotated_size_bounds(self):
        raw,failure,limits=layout({'one.py':1024},{'owner.json':1024},{'old.json':1024},65536)
        self.assertEqual(len([n for n in raw if n.startswith('native/')]),52)
        self.assertEqual(len([n for n in raw if n.startswith('request/')]),52)
        self.assertEqual(len([n for n in raw if n.startswith('data/')]),48)
        self.assertEqual(limits['restore'],sum(raw.values())+sum(failure.values()))
        self.assertEqual(limits['archive'],limits['restore']+4*M)
        self.assertEqual(limits['raw'],sum(raw.values()))
        for role in ROLES:self.assertEqual(raw['data/'+role.replace(':','-')+'.json'],capacity(role))
        self.assertLessEqual(sum(limits.values()),7552*M)
        self.assertEqual(registration_capacity(32768),65536)
        for sources,owners,cached,size in (({'large':M+1},{},{},1),({}, {'large':M+1},{},1),
            ({},{},{'huge':12*M+1},1),({},{},{},65537)):
            with self.assertRaises(AssertionError):layout(sources,owners,cached,size)
        fixture=json.loads((Path(__file__).parents[1]/'data/credited-fallback86-controls/active-size-fixture-v1.json').read_bytes())
        bound=annotated_bound(fixture)
        self.assertLessEqual(bound['paired_event_bytes'],4096)
        self.assertEqual(recording_bound(),39387136)
        self.assertLess(recording_bound(),64*M)

    def mock_graph(self,fail_at=None,parity_failure=False,input_failure=False):
        calls=[];verified=[]
        previous=[None]
        class ProducerBody(dict):pass
        def refuse(field):calls.append(('refuse',field))
        def invoke(role,inputs):
            if previous[0] is not None:self.assertIsNone(previous[0](), 'Previous full body retained across next role')
            calls.append(('role',role))
            if len(calls)-4==fail_at:raise MemoryError('Explicit NON-PHYSICS injected failure')
            export,seed,arm,kind=role.split(':')
            digest=hashlib.sha256((seed+':'+arm).encode()).hexdigest()
            spec=dict(path=role,extent=123,sha256=digest)
            common=dict(seed=int(seed),arm=arm,software_only=True,scientific_worlds=0,scientific_targets=0)
            if kind=='generate':
                value=dict(common,error=None,software_genesis_attempts=9,
                    records=[dict(descriptor=c,NON_PHYSICS=1) for c in CONFIG['cases']])
                value=ProducerBody(value);previous[0]=weakref.ref(value)
                if parity_failure and export=='restored':spec['sha256']='0'*64
            else:
                value=dict(common,verified=True,producer_imported=False,evidence_inputs=copy.deepcopy(inputs),
                    summaries=[dict(descriptor=c,proof=dict(verified=True,NON_PHYSICS=1)) for c in CONFIG['cases']])
                self.assertEqual(inputs['path'],f'original:{seed}:{arm}:generate')
                if input_failure:value['evidence_inputs']['path']='foreign'
            return dict(spec=spec,value=value)
        def verify(role,result):verified.append(role)
        return calls,verified,refuse,invoke,verify

    def test_actual_orchestration_all52_mock_roles(self):
        calls,verified,refuse,invoke,verify=self.mock_graph()
        result=orchestrate(refuse,invoke,verify)
        self.assertEqual(calls[:4],[('refuse',f) for f in ('role','configuration','source_sha','seal')])
        self.assertEqual(calls[4:],[('role',r) for r in ROLES])
        self.assertEqual(verified,list(ROLES))
        self.assertEqual(len(result),16)

    def test_actual_orchestration_fail_stop_and_no_cross_arm_parity(self):
        for options,error,expected in ((dict(fail_at=8),MemoryError,12),
            (dict(parity_failure=True),AssertionError,7),(dict(input_failure=True),AssertionError,6)):
            calls,verified,refuse,invoke,verify=self.mock_graph(**options)
            with self.assertRaises(error):orchestrate(refuse,invoke,verify)
            self.assertEqual(len(calls),expected)

    def test_exact_ci_dirty_state_and_pre_world_guard_order(self):
        receipt=dict(passed=True,conclusion='success',source_head='a'*40)
        admit_ci(receipt,'a'*40,'')
        for data,head,status in ((receipt,'a'*40,' M worker.py'),(receipt,'b'*40,''),
            (dict(receipt,conclusion=None),'a'*40,''),(dict(receipt,passed=1),'a'*40,'')):
            with self.assertRaises(AssertionError):admit_ci(data,head,status)
        root=Path(__file__).parents[1]
        child=(root/'experiments/digital_credited_fallback86_active_child.py').read_text()
        self.assertLess(child.index('kind=scope(request)'),child.index('from experiments.digital_credited_fallback86_controls import World'))
        self.assertLess(child.index('boundary.validate_grant('),child.index('from experiments.digital_credited_fallback86_controls import World'))
        self.assertIn('from experiments.digital_recording82_reader import read_spec',child)
        self.assertIn('state=terminal_view(world.__dict__)',child)
        text=(root/'lab/run_credited_fallback86_active_v1.py').read_text()
        tree=ast.parse(text)
        self.assertFalse(any(isinstance(n,ast.ImportFrom) and n.module in (
            'experiments.digital_memory80','experiments.digital_credited_fallback86_controls',
            'experiments.digital_credited_fallback86_control_referee') for n in ast.walk(tree)))
        self.assertIn('summary=orchestrate(refuse,invoke,verify)',text)
        self.assertIn('assert calls==52 and negatives==4 and len(summary)==16',text)
        self.assertIn("oralab.git(DEV,'status','--porcelain')",text)
        self.assertIn('incomplete_genesis_attempts_not_inferred',text)

    def test_cached_custody_reader_and_body_lifetime(self):
        from experiments.digital_credited_fallback86_active_plan import validate_cached
        from experiments.digital_recording82_reader import read_spec
        root=Path(__file__).resolve().parents[1]
        with tempfile.TemporaryDirectory(dir=root) as folder:
            target=Path(folder).resolve();self.assertTrue(target.is_relative_to(root))
            entries=[]
            for seed in range(2100080,2100084):
                body=dict(seed=seed,software_only=True,error=None,software_genesis_attempts=9,
                    records=[dict(descriptor=c,NON_PHYSICS=1) for c in CONFIG['cases']])
                raw=json.dumps(body,sort_keys=True,separators=(',',':')).encode()
                path=target/str(seed);path.write_bytes(raw)
                entries.append((seed,dict(path=str(path),extent=len(raw),sha256=hashlib.sha256(raw).hexdigest())))
            validate_cached(entries,read_spec)
            # Disclosed synthetic metadata refusal. Windows denied actual link
            # creation in the preserved V2 qualification; no access bypass.
            real_lstat=Path.lstat
            first_path=Path(entries[0][1]['path'])
            def synthetic_link(path,*args,**kwargs):
                info=real_lstat(path,*args,**kwargs)
                if path==first_path:
                    return SimpleNamespace(st_mode=info.st_mode,st_nlink=2)
                return info
            with patch.object(Path,'lstat',synthetic_link), patch.object(os,'open',side_effect=AssertionError('Must refuse before open')):
                with self.assertRaisesRegex(ValueError,'unshared regular recording'):
                    validate_cached(entries,read_spec)
            class CachedBody(dict):pass
            previous=[None];calls=[]
            def spy(spec):
                if previous[0] is not None:self.assertIsNone(previous[0]())
                value=CachedBody(read_spec(spec));previous[0]=weakref.ref(value);calls.append(spec)
                return value
            validate_cached(entries,spy)
            self.assertIsNone(previous[0]())
            self.assertEqual(calls,[spec for seed,spec in entries])
            controller=(root/'lab/run_credited_fallback86_active_v1.py').read_text()
            self.assertIn('validate_cached([(seed,closed[',controller)
            self.assertIn('read_cached)',controller)
            self.assertIn('for parent in path.parents:plain(parent,True)',controller)


if __name__=='__main__':unittest.main()
