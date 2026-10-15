"""Actual primary scope/graph with explicit NON-PHYSICS data; no World/targets."""
import ast,copy,hashlib,json,unittest,weakref
from pathlib import Path
from experiments.digital_credited_fallback87v2_primary_child import CONFIG,scope,group_roles
from experiments.digital_credited_fallback87v2_primary_plan import SEEDS,GROUPS,CASES,ROLES,capacity,layout,orchestrate,admit_ci,annotated_bound,M
from experiments.digital_credited_fallback87v2_acceptance import interpret

def file_spec(role):return dict(path=str(Path(__file__).resolve().parent/('NON-PHYSICS-'+role.replace(':','-'))),extent=123,sha256=hashlib.sha256(role.encode()).hexdigest())
def chain(role):return dict(role=role,body=file_spec(role),request=file_spec(role+'-request'),native=file_spec(role+'-native'))
def base(role=ROLES[0],inputs=None):
    return dict(configuration=copy.deepcopy(CONFIG),source_files={},source_sha='',config_sha='',
        role=role,kind=role.split(':')[-1],input=inputs,grant={},seal='')

class PrimaryCustody(unittest.TestCase):
    def test_exact_scope_all305_and_foreign_refusals(self):
        for role in ROLES:
            kind=role.split(':')[-1]
            inputs=None
            if kind=='audit':inputs=file_spec(role)
            elif kind=='metrics':inputs=[chain(r) for r in group_roles(int(role.split(':')[1]))]
            elif kind=='accept':inputs={str(s):chain(f'original:{s}:metrics') for s in SEEDS}
            self.assertEqual(scope(base(role,inputs)),kind)
        for seed in (2100382,2100080,1009800,1010000,1009699,1009708):
            with self.assertRaises(AssertionError):scope(base(f'original:{seed}:intact:generate'))
        for field,value in (('warm',12),('decisions',61),('horizon',2048),('software_only',True),('seeds',[1009700]),('contract_sha256','0'*64)):
            request=base();request['configuration'][field]=value
            with self.assertRaises(AssertionError):scope(request)
        role=f'original:{SEEDS[0]}:metrics';inputs=[chain(r) for r in group_roles(SEEDS[0])]
        inputs[0]['role']='foreign'
        with self.assertRaises(AssertionError):scope(base(role,inputs))

    def test_full_precharge305_data309_native_and_bounds(self):
        raw,failure,limits=layout({'source.py':M},{'owner.json':M},65536)
        self.assertEqual(len(ROLES),305)
        self.assertEqual(sum(n.startswith('native/') for n in raw),309)
        self.assertEqual(sum(n.startswith('request/') for n in raw),309)
        self.assertEqual(sum(n.startswith('data/') for n in raw),305)
        self.assertEqual(limits['restore'],sum(raw.values())+sum(failure.values()))
        self.assertEqual(limits['archive'],limits['restore']+8*M)
        self.assertLessEqual(sum(limits.values()),46080*M)
        self.assertEqual(sum(len(CASES[r.split(':')[2]]) for r in ROLES if r.endswith(':generate')),1632)
        for role in ROLES:self.assertEqual(raw['data/'+role.replace(':','-')+'.json'],capacity(role))
        fixture=json.loads((Path(__file__).parents[1]/'data/credited-fallback86-controls/active-size-fixture-v1.json').read_bytes())
        self.assertEqual(annotated_bound(fixture)['recording_bound'],39387136)
        for sources,owners,size in (({'bad':M+1},{'one':1},1),({'one':1},{'bad':M+1},1),({'one':1},{'one':1},65537)):
            with self.assertRaises(AssertionError):layout(sources,owners,size)

    def mock_graph(self,fail=None,parity=False,detach=False,wrong_count=False):
        calls=[];verified=[];previous=[None];all_endpoints=[]
        class Body(dict):pass
        def refuse(field):calls.append(field)
        def invoke(role,inputs):
            if previous[0] is not None:self.assertIsNone(previous[0](), 'Old full body retained across next role')
            calls.append(role);scope(base(role,inputs))
            if role==fail:raise MemoryError('NON-PHYSICS injected stop')
            export=role.split(':')[0];kind=role.split(':')[-1];current=file_spec(role)
            if kind in ('generate','audit'):
                seed=int(role.split(':')[1]);group=role.split(':')[2]
                current['sha256']=hashlib.sha256((str(seed)+group).encode()).hexdigest()
                common=dict(seed=seed,group=group,software_only=False,NON_PHYSICS=True)
                if kind=='generate':
                    value=Body(common,error=None,scientific_genesis_attempts=True if wrong_count else len(CASES[group]),records=[dict(descriptor=d) for d in CASES[group]])
                    if parity and export=='restored':current['sha256']='0'*64
                else:
                    value=Body(common,verified=True,producer_imported=False,evidence_inputs=copy.deepcopy(inputs),summaries=[dict(descriptor=d,proof=dict(verified=True)) for d in CASES[group]])
                    if detach:value['evidence_inputs']['sha256']='0'*64
            elif kind=='metrics':
                seed=int(role.split(':')[1]);self.assertEqual([c['role'] for c in inputs],group_roles(seed))
                points=[dict(seed=seed,descriptor=list(d),completed=0,N=0,E=-1,fixed_oracle_N=0,fixed_oracle_E=0,
                    common=0,correct_intact=0,correct_joint=0,correct_model=0,correct_route=0,correct_misbound=0,older_uses=0,observed_mixed=0) for d in CASES['intact']]
                all_endpoints.extend(points);value=Body(seed=seed,endpoints=points,execution_admission=False)
            else:
                self.assertEqual(set(inputs),{str(s) for s in SEEDS})
                value=Body(interpret(all_endpoints))
            previous[0]=weakref.ref(value)
            return dict(spec=current,value=value,chain=dict(chain(role),body=current))
        def verify(role,result):verified.append(role)
        return calls,verified,refuse,invoke,verify

    def test_actual309_callback_order_full16_51_and_lifetime(self):
        calls,verified,*functions=self.mock_graph();out=orchestrate(*functions)
        self.assertEqual(calls[:4],['role','configuration','source_sha','seal'])
        self.assertEqual(calls[4:],list(ROLES));self.assertEqual(verified,list(ROLES))
        self.assertEqual(len(out['endpoints']),144);self.assertEqual(len(out['metric_specs']),16)
        self.assertTrue(all(not d['arithmetic_mechanistic_paid_choice'] for d in out['arithmetic']['descriptors']))
        self.assertFalse(out['arithmetic']['execution_admission'])

    def test_fail_stop_parity_detach_typed_counts(self):
        for options,error,size in ((dict(fail=ROLES[7]),MemoryError,12),(dict(parity=True),AssertionError,7),
                (dict(detach=True),AssertionError,6),(dict(wrong_count=True),AssertionError,5)):
            calls,verified,*functions=self.mock_graph(**options)
            with self.assertRaises(error):orchestrate(*functions)
            self.assertEqual(len(calls),size)

    def test_source_free_boundaries_exact_reused_AST_and_guard_order(self):
        root=Path(__file__).parents[1]
        old=ast.parse((root/'experiments/digital_cognitive76_child.py').read_bytes())
        new=ast.parse((root/'experiments/digital_credited_fallback87v2_primary_boundary.py').read_bytes())
        functions={n.name:ast.dump(n) for n in new.body if isinstance(n,ast.FunctionDef)}
        for node in old.body:
            if isinstance(node,ast.FunctionDef) and node.name in functions:self.assertEqual(functions[node.name],ast.dump(node))
        self.assertFalse(any(isinstance(n,ast.ImportFrom) and n.module and n.module.endswith('_source') for n in new.body))
        child=(root/'experiments/digital_credited_fallback87v2_primary_child.py').read_text(encoding='utf-8')
        tree=ast.parse(child)
        self.assertFalse(any(isinstance(n,ast.ImportFrom) and n.module and n.module.endswith(('_source','_world','_referee')) for n in tree.body))
        main=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='main')
        text=ast.unparse(main)
        self.assertLess(text.index('kind = scope(request)'),text.index('value = generate(seed, group)'))
        self.assertLess(text.index('boundary.validate_grant'),text.index('value = generate(seed, group)'))
        self.assertIn('admission=ADMISSION',child);self.assertIn('scientific_genesis_attempts',child)
        for name in ('metrics','accept'):
            body=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name==name)
            self.assertFalse(any(isinstance(n,ast.ImportFrom) and n.module and n.module.endswith(('_source','_world','_referee')) for n in ast.walk(body)))

    def test_exact_head_CI_parent_cleanup_precharge_and_empty_scope(self):
        good=dict(passed=True,conclusion='success',source_head='a'*40);admit_ci(good,'a'*40,'')
        for data,head,status in ((good,'b'*40,''),(good,'a'*40,' M file'),(dict(good,passed=1),'a'*40,''),(dict(good,conclusion=None),'a'*40,'')):
            with self.assertRaises(AssertionError):admit_ci(data,head,status)
        root=Path(__file__).parents[1];text=(root/'lab/run_credited_fallback87v2_primary_v1.py').read_text(encoding='utf-8')
        self.assertIn('assert calls==309 and negatives==4',text)
        self.assertIn('summary=orchestrate(refuse,invoke,verify)',text)
        self.assertIn('incomplete_genesis_attempts_not_inferred',text)
        self.assertLess(text.index("b.create('restore'"),text.index('def native_role('))
        self.assertIn("kind=role.split(':')[-1]",text)
        role='original:all:accept'
        with self.assertRaises(AssertionError):scope(base(role,{}))

if __name__=='__main__':unittest.main()
