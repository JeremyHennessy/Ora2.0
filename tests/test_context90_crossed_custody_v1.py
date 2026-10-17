"""Seven NEW graph/custody groups using nonphysical synthetic values only."""
import ast,copy,hashlib,json,unittest
from pathlib import Path
from experiments import digital_context90_crossed_plan_v1 as plan
BASE=Path(__file__).resolve().parent

def enc(x):return json.dumps(x,sort_keys=True,separators=(',',':')).encode()
def spec(x):return dict(path=str(Path.cwd()/'SYNTHETIC'),extent=len(enc(x)),sha256=hashlib.sha256(enc(x)).hexdigest())
def source(name,relative):
 p=BASE/name
 return p if p.exists() else BASE.parent/relative

class Custody(unittest.TestCase):
 def simulate(self,mode,failrole=None,failrefusal=None,mutation=None):
  calls=[];refusals=[];verified=[]
  def refuse(key):
   self.assertEqual(calls,[]);refusals.append(key)
   if len(refusals)==failrefusal:raise RuntimeError('SYNTHETIC refused endpoint failure')
  def invoke(role,inputs):
   calls.append(role)
   if len(calls)==failrole:raise RuntimeError('SYNTHETIC role failure')
   if role=='primary:sampler':
    self.assertIsNone(inputs);value=dict(schema='CONTEXT90-CROSSED-DRAWS-v1',mode='primary',draws=[dict(tuple_id='C90X1-P'+str(i).zfill(2),words=['0'*64],rank=0) for i in range(9)])
   else:
    fields=role.split(':');i=int(fields[1]);cell=fields[2];batch=fields[3];actors=plan.BATCHES[batch]
    self.assertEqual(set(inputs),{'body','draw'})
    if role.endswith(':generate'):
     self.assertIsNone(inputs['body']);records=[dict(role=a,state=dict(deaths=0,tick=1),ledger=[dict(completion=None)],stop_reason='SYNTHETIC') for a in actors]
     value=dict(schema='CONTEXT90-CROSSED-BODY-v1',mode=mode,index=i,cell=cell,batch=batch,genesis_attempts=len(actors),completed_constructors=len(actors),records=records,error=None)
    else:
     self.assertIsNotNone(inputs['body']);summaries=[]
     for a in actors:
      learner=a.startswith('q');diag=cell in ('AA','CC');q=15 if learner and diag else 5 if learner else 10;r=14 if learner and diag else 4 if learner else 0
      prefix=dict(schema='CONTEXT90-CROSSED-PREFIX-v1',role=a,programme_sha256='0'*64,stream_sha256=hashlib.sha256(enc([i,cell[0],a])).hexdigest(),events=1,cut_state_sha256='0'*64,cut_trial=0)
      metrics=dict(index=i,cell=cell,role=a,Q=q,R=r,N=-1,O=-2,E=-3)
      summaries.append(dict(role=a,physics=dict(verified=True,scientific_worlds=int(mode=='primary'),metrics=metrics,prefix=prefix)))
     value=dict(schema='CONTEXT90-CROSSED-PROOF-v1',verified=True,mode=mode,index=i,cell=cell,batch=batch,producer_imported=False,evidence_inputs=inputs,summaries=summaries)
    if mutation=='prefix' and role=='original:0:AC:retention:audit':value['summaries'][0]['physics']['prefix']['stream_sha256']='f'*64
    if mutation=='body_mode' and role.endswith(':generate'):value['mode']='wrong'
   s=spec(value)
   if mutation=='replay' and role.startswith('restored:'):s['sha256']='f'*64
   return dict(value=value,spec=s,chain=dict(role=role))
  result=plan.orchestrate(mode,refuse,invoke,lambda role,value:verified.append(role))
  return calls,refusals,verified,result
 def test_new_full_inventories(self):
  for mode,n,calls,total in (('software',48,52,4864),('primary',433,437,40192)):
   self.assertEqual(len(plan.roles(mode)),n);raw,failure,limits=plan.layout(mode,{'experiments/SYNTHETIC.py':1024},{'SYNTHETIC':1024},1024)
   self.assertEqual(sum(k.startswith('native/') for k in raw),calls);self.assertEqual(sum(k.startswith('data/') for k in raw),n);self.assertLessEqual(sum(limits.values()),total*plan.M);self.assertEqual(sum(failure.values()),64*plan.M)
  with self.assertRaises(AssertionError):plan.layout('primary',{'x':4*plan.M},{},1)
 def test_new_complete_software_graph(self):
  calls,refusals,verified,r=self.simulate('software');self.assertEqual(calls,list(plan.roles('software')));self.assertEqual(calls,verified);self.assertEqual(refusals,['role','configuration','source_sha','seal']);self.assertEqual(r['totals']['originals'],76);self.assertEqual(r['totals']['replays'],76);self.assertEqual(r['totals']['prefix_pairs'],38);self.assertTrue(r['software_admission']);self.assertFalse(r['execution_admission'])
 def test_new_complete_primary_graph(self):
  calls,refusals,verified,r=self.simulate('primary');self.assertEqual(calls,list(plan.roles('primary')));self.assertEqual(calls[0],'primary:sampler');self.assertEqual(calls,verified);self.assertEqual(r['totals']['originals'],684);self.assertEqual(r['totals']['replays'],684);self.assertEqual(r['totals']['prefix_pairs'],342);self.assertEqual(r['metrics']['tuple_units'],9)
 def test_new_all_endpoint_failstops(self):
  for mode in ('software','primary'):
   for position in range(1,len(plan.roles(mode))+1):
    with self.assertRaisesRegex(RuntimeError,'SYNTHETIC role failure'):self.simulate(mode,failrole=position)
 def test_new_refusals_and_integrity_failstops(self):
  for mode in ('software','primary'):
   for pos in range(1,5):
    with self.assertRaisesRegex(RuntimeError,'SYNTHETIC refused endpoint failure'):self.simulate(mode,failrefusal=pos)
  for mutation in ('prefix','body_mode','replay'):
   with self.assertRaises(AssertionError):self.simulate('software',mutation=mutation)
 def test_new_controller_source_gates_and_profiles(self):
  t=ast.parse(source('controller.py','lab/run_context90_crossed_v1.py').read_bytes());get=lambda name:next(n for n in t.body if isinstance(n,ast.FunctionDef) and n.name==name);gate=ast.unparse(get('gate'))
  for text in ('crossed_whole_runtime_source','software_admission','152','52','source_head','status','verify_reuse'):self.assertIn(text,gate)
  profile=get('profile');scope=dict(plan=plan,M=plan.M);exec(compile(ast.fix_missing_locations(ast.Module(body=[copy.deepcopy(profile)],type_ignores=[])),'<SYNTHETIC resource profile>','exec'),scope)
  self.assertEqual(scope['profile']('software'),dict(evidence=4864*plan.M,free=4872*plan.M,cpu=600,wall=900));self.assertEqual(scope['profile']('primary'),dict(evidence=40192*plan.M,free=40200*plan.M,cpu=3600,wall=5400))
  worker=ast.unparse(get('worker'));self.assertIn('plan.orchestrate',worker);self.assertIn('negative == 4',worker);self.assertIn('437',worker);self.assertIn('sampler_may_have_drawn',worker)
 def test_new_native_source_body_archive_structure(self):
  t=ast.parse(source('controller.py','lab/run_context90_crossed_v1.py').read_bytes());worker=next(n for n in t.body if isinstance(n,ast.FunctionDef) and n.name=='worker');text=ast.unparse(worker)
  for token in ('post_close_processes_exited','active_before_close','receipt','grant_sha256','source_sha','config_sha','archive_exact','archive_sha256','native_calls','incomplete_genesis_attempts_not_inferred','observed_generator_counters','zipfile.ZipFile','restore','native_ok'):self.assertIn(token,text)
  self.assertIn('finally:',text);self.assertIn('error = exc',text);self.assertIn('archive_error = exc',text)

if __name__=='__main__':unittest.main()
