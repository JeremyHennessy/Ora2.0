"""NON-PHYSICS custody tests;no task constructor,step,target or source import."""
import ast,copy,json,unittest
from pathlib import Path
from experiments import digital_temporal89_plan as plan

class Temporal89Custody(unittest.TestCase):
 def request(self,role=None,inputs=None):
  role=role or plan.roles('software')[0]
  return dict(configuration=plan.config('software'),source_files={},source_sha='0'*64,config_sha='0'*64,
   role=role,kind=role.split(':')[-1],input=inputs,grant={},seal='0'*64)
 def spec(self):return dict(path=str(Path.cwd()/'NON-PHYSICS-placeholder'),extent=1,sha256='0'*64)
 def test_01_complete_scope(self):
  roles=plan.roles('software');self.assertEqual(len(roles),27);self.assertEqual(len(set(roles)),27)
  self.assertEqual(sum(r.endswith(':generate') for r in roles),16)
  self.assertEqual(sum(r.endswith(':audit') for r in roles),8)
  self.assertEqual(sum(r.endswith(':metrics') for r in roles),2)
  self.assertEqual(plan.scope(self.request()),'generate')
  for field,value in (('role','original:1010500:q2:generate'),('role','original:1010600:q2:generate'),
                      ('role','original:2100588:q2:generate'),('kind','audit')):
   r=self.request();r[field]=value
   with self.assertRaises(AssertionError):plan.scope(r)
  for field,value in (('mode','primary'),('warm',47),('cost_budget',1025),('software_only',1)):
   r=self.request();r['configuration'][field]=value
   with self.assertRaises(AssertionError):plan.scope(r)
 def test_02_exact_input_graph(self):
  s=2100589;chains={}
  for batch in plan.BATCHES:
   chains[batch]=[dict(role=r,body=self.spec(),request=self.spec(),native=self.spec()) for r in
    (f'original:{s}:{batch}:generate',f'original:{s}:{batch}:audit',f'restored:{s}:{batch}:generate')]
  r=self.request(f'original:{s}:metrics',chains);self.assertEqual(plan.scope(r),'metrics')
  for change in ('missing','swapped','detached','bool_extent'):
   bad=copy.deepcopy(r)
   if change=='missing':bad['input'].pop('q2')
   elif change=='swapped':bad['input']['q2'].reverse()
   elif change=='detached':bad['input']['q2'][0]['role']='restored:2100589:q2:generate'
   else:bad['input']['q2'][0]['body']['extent']=True
   with self.assertRaises(AssertionError):plan.scope(bad)
 def test_03_precharge_bounds(self):
  raw,failure,limits=plan.layout('software',{'experiments/x.py':1024},{'owner.json':1024},1024)
  self.assertEqual(len([p for p in raw if p.startswith('native/')]),31)
  self.assertEqual(len([p for p in raw if p.startswith('request/')]),31)
  self.assertEqual(len([p for p in raw if p.startswith('data/')]),27)
  self.assertLessEqual(sum(limits.values()),5376*plan.M)
  self.assertTrue(all('pure-' not in p for p in raw))
  with self.assertRaises(AssertionError):plan.layout('software',{'x.py':3*plan.M},{},1)
  with self.assertRaises(AssertionError):plan.spec_shape(dict(self.spec(),extent=True),plan.M)
 def simulate(self,fail=None):
  calls=[];refused=[];verified=[]
  def invoke(role,inputs):
   calls.append(role)
   if len(calls)==fail:raise RuntimeError('NON-PHYSICS injected stop')
   spec=self.spec();parts=role.split(':');seed=int(parts[1]) if parts[1]!='all' else None
   if role.endswith(':generate'):
    batch=parts[2];actors=list(plan.BATCHES[batch]);value=dict(seed=seed,batch=batch,software_only=True,
      error=None,genesis_attempts=len(actors),completed_constructors=len(actors),records=[dict(role=r) for r in actors])
   elif role.endswith(':audit'):
    batch=parts[2];value=dict(seed=seed,batch=batch,software_only=True,verified=True,evidence_inputs=inputs,
      summaries=[dict(role=r,physics=dict(verified=True)) for r in plan.BATCHES[batch]])
   elif role.endswith(':metrics'):
    self.assertEqual(list(inputs),list(plan.BATCHES));value=dict(seed=seed,execution_admission=False,
      roles=list(plan.ACTORS),rows=[dict(role=r) for r in plan.ACTORS],endpoints=[dict(capacity=q) for q in (2,4,8)])
   else:
    self.assertEqual(set(inputs),{'2100589','2100590'})
    value=dict(verified=True,software_only=True,scope='SOFTWARE complete-denominator/custody only,no scientific acceptance',execution_admission=False)
   return dict(spec=spec,chain=dict(role=role),value=value)
  def refuse(key):
   self.assertEqual(calls,[]);refused.append(key)
  try:result=plan.orchestrate('software',refuse,invoke,lambda role,value:verified.append(role))
  except RuntimeError:return calls,refused,verified,None
  return calls,refused,verified,result
 def test_04_full_order_and_reuse(self):
  calls,refused,verified,result=self.simulate()
  self.assertEqual(calls,list(plan.roles('software')));self.assertEqual(verified,calls)
  self.assertEqual(refused,['role','configuration','source_sha','seal'])
  self.assertTrue(result['software_admission']);self.assertEqual(len(calls)+len(refused),31)
 def test_05_fail_stop_every_role(self):
  for stop in range(1,28):
   calls,refused,verified,result=self.simulate(stop)
   self.assertEqual(len(calls),stop);self.assertEqual(len(verified),stop-1);self.assertIsNone(result)
   self.assertEqual(len(refused),4)
 def test_06_reused_authentication_and_preWorld_guards(self):
  root=Path(__file__).resolve().parents[1]/'experiments'
  old=ast.parse((root/'digital_strategy88_child.py').read_bytes());new=ast.parse((root/'digital_temporal89_child.py').read_bytes())
  for name in ('read','authenticate'):
   extract=lambda tree:next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name==name)
   self.assertEqual(ast.dump(extract(old),include_attributes=False),ast.dump(extract(new),include_attributes=False))
  main=next(n for n in new.body if isinstance(n,ast.FunctionDef) and n.name=='main')
  calls=[(n.lineno,ast.unparse(n.func)) for n in ast.walk(main) if isinstance(n,ast.Call)]
  line=lambda text:min(n for n,name in calls if name==text)
  self.assertLess(line('plan.scope'),line('generate'))
  self.assertLess(line('boundary.verify_source'),line('generate'))
  self.assertLess(line('boundary.validate_grant'),line('generate'))
  self.assertNotIn('digital_temporal89_world',ast.unparse(main))

if __name__=='__main__':unittest.main()
