"""Six NEW custody groups; all dependency values are nonphysical mocks."""
import ast,copy,unittest
from pathlib import Path
from experiments import digital_context90_plan_v1 as plan
BASE=Path(__file__).resolve().parent

def file(name,relative):
 p=BASE/name
 return p if p.exists() else BASE.parent/relative

class Custody(unittest.TestCase):
 def request(self,role=None,inputs=None):
  role=role or plan.roles('software')[0]
  return dict(configuration=plan.config('software'),source_files={},source_sha='0'*64,config_sha='0'*64,role=role,kind=role.split(':')[-1],input=inputs,grant={},seal='0'*64)
 def spec(self):return dict(path=str(Path.cwd()/'SYNTHETIC'),extent=1,sha256='0'*64)
 def test_new_scope(self):
  roles=plan.roles('software');self.assertEqual(len(roles),24);self.assertEqual(len(set(roles)),24)
  self.assertEqual(sum(r.endswith('generate') for r in roles),16);self.assertEqual(sum(r.endswith('audit') for r in roles),8)
  self.assertEqual(plan.scope(self.request()),'generate')
  for field,value in (('role','original:1010500:learners:generate'),('role','original:2100589:learners:generate'),('kind','audit')):
   r=self.request();r[field]=value
   with self.assertRaises(AssertionError):plan.scope(r)
  for field,value in (('startup',112),('factory',320),('software_only',1),('cost_budget',1801),('mode','primary')):
   r=self.request();r['configuration'][field]=value
   with self.assertRaises(AssertionError):plan.scope(r)
 def test_new_input_types(self):
  role='original:2100690:learners:audit';self.assertEqual(plan.scope(self.request(role,self.spec())),'audit')
  for bad in (None,dict(self.spec(),extent=True),dict(self.spec(),extent=64*plan.M+1),dict(self.spec(),path='relative'),dict(self.spec(),sha256='x'*64)):
   with self.assertRaises(AssertionError):plan.scope(self.request(role,bad))
 def test_new_extents(self):
  raw,fail,limits=plan.layout('software',{'experiments/x.py':1024},{'owner':1024},1024)
  self.assertEqual(len([p for p in raw if p.startswith('native/')]),28);self.assertEqual(len([p for p in raw if p.startswith('data/')]),24)
  self.assertLessEqual(sum(limits.values()),4608*plan.M)
  with self.assertRaises(AssertionError):plan.layout('software',{'x':3*plan.M},{},1)
 def simulate(self,failrole=None,failrefusal=None):
  calls=[];refused=[];verified=[]
  def refuse(key):
   self.assertEqual(calls,[]);refused.append(key)
   if len(refused)==failrefusal:raise RuntimeError('NEW synthetic refusal-stop')
  def invoke(role,inputs):
   calls.append(role)
   if len(calls)==failrole:raise RuntimeError('NEW synthetic role-stop')
   seed=int(role.split(':')[1]);batch=role.split(':')[2];actors=plan.BATCHES[batch]
   if role.endswith('generate'):
    records=[dict(role=a,state=dict(events=[dict(captured=0)],deaths=0),ledger=[dict(completion=None)],stop_reason='SYNTHETIC') for a in actors]
    v=dict(seed=seed,batch=batch,software_only=True,error=None,genesis_attempts=len(actors),completed_constructors=len(actors),records=records)
   else:v=dict(seed=seed,batch=batch,software_only=True,verified=True,evidence_inputs=inputs,summaries=[dict(role=a,physics=dict(verified=True)) for a in actors])
   return dict(spec=self.spec(),value=v,chain=dict(role=role))
  try:r=plan.orchestrate('software',refuse,invoke,lambda role,value:verified.append(role))
  except RuntimeError:r=None
  return calls,refused,verified,r
 def test_new_complete_order(self):
  calls,refused,verified,r=self.simulate();self.assertEqual(calls,list(plan.roles('software')));self.assertEqual(verified,calls)
  self.assertEqual(refused,['role','configuration','source_sha','seal']);self.assertEqual(r['totals']['originals'],64);self.assertEqual(r['totals']['replays'],64)
  self.assertFalse(r['execution_admission']);self.assertFalse(r['stage_credit'])
 def test_new_failstop(self):
  for pos in range(1,25):
   calls,refused,verified,r=self.simulate(failrole=pos);self.assertEqual(len(calls),pos);self.assertEqual(len(verified),pos-1);self.assertIsNone(r)
  for pos in range(1,5):
   calls,refused,verified,r=self.simulate(failrefusal=pos);self.assertEqual(calls,[]);self.assertEqual(len(refused),pos);self.assertIsNone(r)
 def test_new_guard_ast_and_controller(self):
  old=ast.parse(file('old-child.py','experiments/digital_temporal89_child.py').read_bytes());new=ast.parse(file('new-child.py','experiments/digital_context90_child_v1.py').read_bytes())
  get=lambda t,n:next(x for x in t.body if isinstance(x,ast.FunctionDef) and x.name==n)
  for name in ('read','authenticate'):self.assertEqual(ast.dump(get(old,name),include_attributes=False),ast.dump(get(new,name),include_attributes=False))
  main=get(new,'main');calls=[(n.lineno,ast.unparse(n.func)) for n in ast.walk(main) if isinstance(n,ast.Call)]
  line=lambda name:min(n for n,k in calls if k==name)
  for name in ('plan.scope','boundary.verify_source','boundary.validate_grant'):self.assertLess(line(name),line('generate'))
  controller=ast.parse(file('controller.py','lab/run_context90_software_v1.py').read_bytes());worker=get(controller,'worker')
  self.assertIn('plan.orchestrate',ast.unparse(worker));self.assertIn('gate(mode)',ast.unparse(controller))
  self.assertNotIn('World',ast.unparse(main))

if __name__=='__main__':unittest.main()
