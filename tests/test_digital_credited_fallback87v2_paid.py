"""New22-role custody checks; all injected bodies explicitly NON-PHYSICS."""
import ast,copy,hashlib,json,tempfile,unittest,weakref,zipfile
from pathlib import Path
from experiments.digital_credited_fallback87v2_paid_child import CONFIG,scope
from experiments.digital_credited_fallback87v2_paid_plan import (
    ROLES,CASES,capacity,layout,orchestrate,admit_ci,annotated_bound,M)

class PaidCustody(unittest.TestCase):
    def base(self,role=ROLES[0]):
        kind=role.split(':')[-1]
        return dict(configuration=copy.deepcopy(CONFIG),source_files={},source_sha='',config_sha='',
            role=role,kind=kind,input=None if kind=='generate' else dict(path='x',extent=1,sha256='0'*64),grant={},seal='')

    def test_exact_software_roster_and_all_foreign_scopes(self):
        self.assertEqual(len(ROLES),18)
        for role in ROLES:self.assertEqual(scope(self.base(role)),role.split(':')[-1])
        for seed in (2100380,2100381,2100383,2100080,1009700,1009900,1009800,1010000):
            with self.assertRaises(AssertionError):scope(self.base(f'original:{seed}:intact:generate'))
        for name,value in (('horizon',256),('warm',12),('software_only',1),('seeds',[True]),
            ('contract_sha256','0'*64),('groups',['intact']),('decisions',61)):
            request=self.base();request['configuration'][name]=value
            with self.assertRaises(AssertionError):scope(request)
        request=self.base();request['input']={'warm_state':1}
        with self.assertRaises(AssertionError):scope(request)
        request=self.base(ROLES[1]);request['input']['foreign']=True
        with self.assertRaises(AssertionError):scope(request)
        for group in CASES:self.assertEqual(len(CASES[group]),6 if group=='references' else 9)

    def test_entire_precharge_and_annotated_union(self):
        raw,failure,limits=layout({'worker.py':M},{'owner.json':M},65536)
        self.assertEqual(sum(n.startswith('data/') for n in raw),18)
        self.assertEqual(sum(n.startswith('native/') for n in raw),22)
        self.assertEqual(sum(n.startswith('request/') for n in raw),22)
        for role in ROLES:self.assertEqual(raw['data/'+role.replace(':','-')+'.json'],capacity(role))
        self.assertEqual(limits['raw'],sum(raw.values()))
        self.assertEqual(limits['restore'],sum(raw.values())+sum(failure.values()))
        self.assertEqual(limits['archive'],limits['restore']+4*M)
        self.assertLessEqual(sum(limits.values()),3072*M)
        for sources,owners,size in (({'too-large':M+1},{'one':1},1),
            ({'one':1},{'too-large':M+1},1),({'one':1},{'one':1},65537)):
            with self.assertRaises(AssertionError):layout(sources,owners,size)
        root=Path(__file__).parents[1]
        fixture=json.loads((root/'data/credited-fallback86-controls/active-size-fixture-v1.json').read_bytes())
        result=annotated_bound(fixture)
        self.assertEqual(result['recording_bound'],39387136)
        self.assertLessEqual(result['paired_event_bytes'],4096)

    def graph(self,fail=None,parity=False,inputs_wrong=False,typed=False):
        calls=[];verified=[];previous=[None]
        class Body(dict):pass
        def refuse(field):calls.append(field)
        def invoke(role,inputs):
            if previous[0] is not None:self.assertIsNone(previous[0](), 'Full previous body retained')
            calls.append(role)
            if role==fail:raise MemoryError('NON-PHYSICS injected cap failure')
            export,seed,group,kind=role.split(':')
            spec=dict(path=role,extent=123,sha256=hashlib.sha256(group.encode()).hexdigest())
            common=dict(seed=int(seed),group=group,software_only=True,scientific_worlds=0,scientific_targets=0)
            if typed:common['scientific_targets']=False
            if kind=='generate':
                value=Body(common,error=None,software_genesis_attempts=len(CASES[group]),
                    records=[dict(descriptor=d,NON_PHYSICS=True) for d in CASES[group]])
                previous[0]=weakref.ref(value)
                if parity and export=='restored':spec['sha256']='0'*64
            else:
                self.assertEqual(inputs['path'],f'original:{seed}:{group}:generate')
                value=dict(common,verified=True,producer_imported=False,evidence_inputs=copy.deepcopy(inputs),
                    summaries=[dict(descriptor=d,proof=dict(verified=True,NON_PHYSICS=True)) for d in CASES[group]])
                if inputs_wrong:value['evidence_inputs']['path']='foreign'
            return dict(spec=spec,value=value)
        def verify(role,result):verified.append(role)
        return calls,verified,refuse,invoke,verify

    def test_real22_role_order_full_denominator_and_lifetime(self):
        calls,verified,*functions=self.graph()
        result=orchestrate(*functions)
        self.assertEqual(calls[:4],['role','configuration','source_sha','seal'])
        self.assertEqual(calls[4:],list(ROLES))
        self.assertEqual(verified,list(ROLES));self.assertEqual(len(result),6)
        self.assertEqual(sum(len(CASES[g])*2 for g in CASES),102)

    def test_fail_stop_parity_input_and_typed_receipts(self):
        for options,error,length in ((dict(fail=ROLES[7]),MemoryError,12),
                (dict(parity=True),AssertionError,7),(dict(inputs_wrong=True),AssertionError,6),
                (dict(typed=True),AssertionError,5)):
            calls,verified,*functions=self.graph(**options)
            with self.assertRaises(error):orchestrate(*functions)
            self.assertEqual(len(calls),length)

    def test_source_guard_branch_and_exact_ci_boundary(self):
        receipt=dict(passed=True,conclusion='success',source_head='a'*40)
        admit_ci(receipt,'a'*40,'')
        for data,head,status in ((receipt,'b'*40,''),(receipt,'a'*40,' M changed'),
            (dict(receipt,passed=1),'a'*40,''),(dict(receipt,conclusion=None),'a'*40,'')):
            with self.assertRaises(AssertionError):admit_ci(data,head,status)
        root=Path(__file__).parents[1]
        worker=(root/'experiments/digital_credited_fallback87v2_paid_child.py').read_text(encoding='utf-8')
        world=worker.index('from experiments.digital_credited_fallback87v2_world import World')
        for guard in ('kind=scope(request)','boundary.verify_source(root,pins)','boundary.validate_grant('):
            self.assertLess(worker.index(guard),world)
        self.assertIn('while world.step():pass',worker)
        self.assertIn('state=terminal_view(world.__dict__)',worker)
        self.assertIn("control=None if reference else group",worker)
        parent=(root/'lab/run_credited_fallback87v2_paid_v1.py').read_text(encoding='utf-8')
        self.assertIn('summary=orchestrate(refuse,invoke,verify)',parent)
        self.assertIn('assert calls==22 and negatives==4 and len(summary)==6',parent)
        self.assertLess(parent.index("b.create('restore'"),parent.index('def native_role('))
        tree=ast.parse(parent)
        self.assertFalse(any(isinstance(n,ast.ImportFrom) and n.module and
            n.module.endswith(('_world','_referee')) for n in ast.walk(tree)))

    def test_actual_granted_nonphysics_body_and_exact_source_archive(self):
        from experiments.evidence_budget import Budget
        from experiments.evidence_write_grant68 import plain,digest,record
        from experiments.digital_recording82_reader import read_spec
        from experiments.digital_cognitive76_child import canonical
        root=Path(__file__).parents[1]
        with tempfile.TemporaryDirectory(dir=root) as folder:
            run=Path(folder).resolve()/'fixture';budget=Budget(run,dict(raw=M),M)
            with budget.create('raw','fixture.json',reserve=8192):pass
            info=plain(run/'raw/fixture.json')
            grant=dict(version='sharedlineage68-file-grant-candidate-v1',root=str(run),phase='raw',
                name='fixture.json',limit=8192,source_sha='a'*64,config_sha='b'*64,
                role='NON-PHYSICS',device=info.st_dev,inode=info.st_ino)
            value=dict(NON_PHYSICS=True,worlds=0,targets=0)
            receipt=record(grant,digest(grant),'a'*64,'b'*64,'NON-PHYSICS',value)
            spec=dict(path=str(run/'raw/fixture.json'),extent=receipt['extent'],sha256=receipt['sha256'])
            self.assertEqual(read_spec(spec),value)
            with self.assertRaises(Exception):record(grant,digest(grant),'a'*64,'b'*64,'NON-PHYSICS',value)
            with self.assertRaises(Exception):read_spec(dict(spec,sha256='0'*64))
            source=root/'experiments/digital_credited_fallback87v2_paid_child.py'
            with zipfile.ZipFile(run/'source.zip','w',zipfile.ZIP_STORED) as z:z.write(source,'child.py')
            with zipfile.ZipFile(run/'source.zip') as z:
                restored=z.read('child.py');self.assertEqual(restored,source.read_bytes())
            self.assertEqual((run/'raw/fixture.json').read_bytes(),canonical(value))

if __name__=='__main__':unittest.main()
