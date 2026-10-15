"""Explicit NON-PHYSICS extraction/binding fixtures. No constructors or targets."""
import ast,copy,json,unittest
from unittest.mock import patch
from pathlib import Path
from experiments import digital_credited_fallback87v2_metrics as metrics
from experiments import digital_credited_fallback87v2_metric_binding as binding

def fixture(erased=False,alias=False,joint=False,wrongbit=False):
    events=[];ledger=[]
    def add(pc,op=0,after=None,attempt=None,read=None,completion=None,entry=None):
        event=dict(tick=len(events)+1,decoded=[op,0,0])
        if after is not None:event['after']=dict(registers=after)
        if attempt is not None:event['attempt']=attempt
        events.append(event);ledger.append(dict(dispatch_pc=pc,completed_before=48,
            read=read,completion=completion,entry=entry))
    def act(pc,cue,port,target,packet):
        add(pc,6,attempt=dict(cue=cue,port=port,target=target,packet=packet,success=int(port==target)))
    add(6,after=[0,1]);add(7,read=dict(source_address=None,value=0))
    act(8,1,0,1,0);add(12,read=dict(source_address=None,value=0));add(13,after=[15,1])
    add(14,20,after=[15,1]);add(15,completion=dict(entry=16))
    add(16,entry=dict(active=1));act(17,2,0 if wrongbit else 1,1,1)
    add(16,entry=dict(active=1));act(17,2,0 if wrongbit else 1,1,2)
    add(6,after=[0,2 if alias else 1]);add(7,read=dict(source_address=None if erased else 1,value=15))
    act(8,2 if alias else 1,1,1,3)
    return dict(descriptor=[2,'model'],programme=[[7,2,6]],state=dict(events=events),ledger=ledger)

class OriginMetrics(unittest.TestCase):
    def test_explicit_software_and_primary_count_namespaces(self):
        cases=[list(d) for d in metrics.DESCRIPTORS]
        for seed,software,count_field in ((2100382,True,'software_genesis_attempts'),
                (1009700,False,'scientific_genesis_attempts')):
            body=dict(seed=seed,group='intact',version='NON-PHYSICS',software_only=software,
                error=None,records=[dict(descriptor=d) for d in cases],**{count_field:9})
            proof=dict(body,verified=True,producer_imported=False,
                summaries=[dict(descriptor=d) for d in cases])
            with patch.object(metrics,'summarize',return_value=dict(NON_PHYSICS=True)):
                result=metrics.batch(body,proof)
                self.assertEqual(len(result['rows']),9)
                for count in (8,True):
                    wrong=copy.deepcopy(body);wrong[count_field]=count
                    with self.assertRaises(AssertionError):metrics.batch(wrong,proof)
                wrong=copy.deepcopy(body);del wrong[count_field]
                with self.assertRaises(AssertionError):metrics.batch(wrong,proof)

    def test_exact_older_vs_recent_and_supplied_origins(self):
        result=metrics.origins(fixture(),'intact')
        self.assertEqual(len(result['revisions']),1)
        self.assertEqual([u['valid_older_correct'] for u in result['uses']],[False,False,True,True])
        self.assertEqual(result['uses'][-1]['served_gap'],3)
        row=fixture();row['state']['events']=row['state']['events'][-3:];row['ledger']=row['ledger'][-3:]
        result=metrics.origins(row,'intact')
        self.assertIsNone(result['uses'][0]['origin'])
        self.assertFalse(result['uses'][0]['valid_older_correct'])

    def test_real_read_alias_semantic_bit_and_joint_channels(self):
        erased=metrics.origins(fixture(erased=True),'model_erased')
        self.assertIsNone(erased['uses'][-1]['origin'])
        alias=metrics.origins(fixture(alias=True),'model_misbound')
        self.assertFalse(alias['uses'][-1]['cue_match'])
        self.assertFalse(alias['uses'][-1]['valid_older_correct'])
        changed=metrics.origins(fixture(wrongbit=True),'fallback_misbound')
        self.assertFalse(changed['uses'][2]['bit_match'])
        joint=metrics.origins(fixture(),'history_disabled')
        self.assertIsNone(joint['uses'][2]['origin'])

    def test_absence_unsensed_feedback_and_observation_separation(self):
        row=fixture();row['state']['events'].insert(0,dict(tick=0,decoded=[6,0,0]))
        row['ledger'].insert(0,dict(dispatch_pc=2,read=None,entry=None,completion=None,completed_before=48))
        result=metrics.origins(row,'intact')
        self.assertEqual(len(result['uses']),4);self.assertEqual(result['uses'][-1]['ordinal'],4)
        self.assertNotIn('2',result['personally_sensed_maps'][0])
        self.assertIn('2',result['observed_maps'][0])
        # Unsensed fallback failure has no model-error origin and cannot justify STORE.
        row=fixture();row['ledger'][2]['dispatch_pc']=2
        with self.assertRaises(AssertionError):metrics.origins(row,'intact')

    def native_fixture(self):
        role='original:2100382:intact:generate';config=dict(version='NON-PHYSICS')
        source={'fixture.py':'c'*64};ss=binding.digest(source);cs=binding.digest(config)
        grant=dict(version='sharedlineage68-file-grant-candidate-v1',root='NON-PHYSICS',phase='raw',
            name='record.json',limit=64*1024**2,source_sha=ss,config_sha=cs,role=role,device=1,inode=2)
        spec=dict(path='NON-PHYSICS/record.json',extent=7,sha256='a'*64)
        request=dict(configuration=config,source_files=source,source_sha=ss,config_sha=cs,
            role=role,kind='generate',input=None,grant=grant,seal=binding.digest(grant))
        receipt=dict(grant_sha256=request['seal'],source_sha=ss,config_sha=cs,role=role,extent=7,sha256='a'*64)
        native=dict(exit_code=0,timed_out=False,output_truncated=False,post_close_processes_exited=True,
            usage=dict(active_before_close=0),output=json.dumps(dict(role=role,source_sha=ss,config_sha=cs,receipt=receipt)))
        return request,native,spec,role,config,spec['path'],(1,2)

    def test_native_source_config_role_seal_identity_and_receipt_refusals(self):
        args=self.native_fixture();self.assertEqual(binding.authenticate(*args)['body'],args[2])
        for field,value in (('source_sha','0'*64),('config_sha','0'*64),('role','foreign'),('seal','0'*64)):
            altered=copy.deepcopy(args);altered[0][field]=value
            with self.assertRaises(AssertionError):binding.authenticate(*altered)
        for field,value in (('exit_code',1),('timed_out',True),('output_truncated',True),('post_close_processes_exited',False)):
            altered=copy.deepcopy(args);altered[1][field]=value
            with self.assertRaises(AssertionError):binding.authenticate(*altered)
        for index,value in ((5,'foreign'),(6,(1,3))):
            altered=list(copy.deepcopy(args));altered[index]=value
            with self.assertRaises(AssertionError):binding.authenticate(*altered)
        altered=copy.deepcopy(args);altered[1]['usage']['active_before_close']=False
        with self.assertRaises(AssertionError):binding.authenticate(*altered)

    def test_detached_proof_missing_groups_and_no_execution_admission(self):
        body=dict(seed=2100382,group='intact',version='NON-PHYSICS',software_only=True,error=None,records=[])
        spec=dict(path='NON-PHYSICS',extent=1,sha256='a'*64)
        proof=dict(verified=True,producer_imported=False,evidence_inputs=spec,seed=2100382,
            group='intact',version='NON-PHYSICS',software_only=True,summaries=[])
        binding.bind_inputs(spec,body,proof)
        wrong=copy.deepcopy(proof);wrong['evidence_inputs']['sha256']='b'*64
        with self.assertRaises(AssertionError):binding.bind_inputs(spec,body,wrong)
        with self.assertRaises(AssertionError):metrics.combine([])
        with self.assertRaises(AssertionError):metrics.batch(body,proof)
        values=[]
        for group in metrics.GROUPS:
            rows=[]
            for d in (metrics.FIXED if group=='references' else metrics.DESCRIPTORS):
                rows.append(dict(descriptor=d if isinstance(d,str) else list(d),N=1,E=-1,completed=0,
                    warm_physical_sha256='NON-PHYSICS',late=[],own=dict(late=[],observed_mixed=0)))
            values.append(dict(seed=2100382,group=group,rows=rows))
        result=metrics.combine(values)
        self.assertFalse(result['execution_admission']);self.assertEqual(len(result['endpoints']),9)
        self.assertTrue(all(r['common']==r['older_uses']==0 for r in result['endpoints']))
        values[1]['group']='intact'
        with self.assertRaises(AssertionError):metrics.combine(values)

    def test_stdlib_only_body_and_accounting_forgery(self):
        root=Path(__file__).parents[1]
        for name in ('metrics','metric_binding'):
            tree=ast.parse((root/f'experiments/digital_credited_fallback87v2_{name}.py').read_bytes())
            imports=[a.name for n in ast.walk(tree) if isinstance(n,ast.Import) for a in n.names]
            self.assertEqual(set(imports),{'hashlib','json'})
            self.assertFalse(any(isinstance(n,ast.ImportFrom) for n in ast.walk(tree)))
        # Not a physical trace: isolated bookkeeping refusal with a matching final hash.
        state=dict(events=[],births=0,writes=0,entities={},heat=0,constructor_remaining=0,
            food={},admitted=0,offered=0,rejected=0)
        row=dict(descriptor=[2,'model'],programme=[[7,2,6]],state=state,ledger=[])
        proof=dict(verified=True,ticks=0,final_state_sha256=metrics.digest({k:v for k,v in state.items() if k!='events'}))
        audit=dict(descriptor=row['descriptor'],proof=proof,paid_cpu=0,completed=0,late_served=[])
        with self.assertRaises(AssertionError):metrics.summarize(row,audit,'intact')

if __name__=='__main__':unittest.main()
