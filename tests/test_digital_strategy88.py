"""NON-PHYSICS source/CFG/whole-custody/arithmetic witnesses; zero Worlds."""
import ast,copy,hashlib,json,unittest,weakref
from pathlib import Path
from experiments import digital_strategy88_source as source
from experiments import digital_strategy88_referee as literal
from experiments import digital_strategy88_plan as plan
from experiments import digital_strategy88_acceptance as acceptance
ROOT=Path(__file__).resolve().parents[1]
def mock_rows(seed=None):
 seeds=acceptance.PRIMARY+acceptance.UNSEEN if seed is None else (seed,)
 return [dict(seed=s,prior=i,completed=60,common=12,correct=12,reset=0,misbound=0,older_uses=6,observed_mixed=int(s%100>=2),
  whole_correct=60,explore_correct=30,oracle_correct=50,N=-100,E=-100,C=400,oracle_N=200,oracle_E=70) for s in seeds for i in range(4)]
class Strategy88(unittest.TestCase):
 def test_source_inventory_and_independent_programmes(self):
  self.assertEqual(len(source.ROLES),26)
  for role in source.ROLES:
   code=source.programme(role);self.assertEqual(code,literal.programme(role));self.assertEqual(code[0][1],2)
   self.assertLessEqual(len(code),32);self.assertFalse({t[0] for t in code}&{2,3,10,12,19,20})
   self.assertTrue(all(type(v) is int and 0<=v<32 for t in code for v in t))
   if ':' in role:self.assertEqual(3*len(code)+10,76)
   elif role.startswith('rr'):self.assertEqual(3*len(code)+10,52)
  for i in range(4):
   self.assertEqual(source.programme(f'adaptive:{i}'),source.programme(f'history_reset:{i}'))
   self.assertEqual(source.programme(f'adaptive:{i}'),source.programme(f'credit_misbound:{i}'))
 def test_cfg_cold_budget_and_two_register_counterexample(self):
  for role in source.ROLES[:16]:
   code=source.programme(role)
   for entry in source.ENTRIES:
    for feedback in (0,1,2):
     pc=entry;count=0
     while True:
      op,a,b=code[pc];new=b if op==7 or op==8 and feedback==0 else pc+1;count+=1
      if pc in (4,5,9,10,14,15,20,21) and new in source.ENTRIES:break
      pc=new;self.assertLess(count,10)
     self.assertEqual(count,(5 if feedback==0 else 6) if entry==16 else (4 if feedback==0 else 5))
  self.assertEqual(76+361+6*4+16,477);self.assertLess(477,512)
  self.assertGreater(112-1-4*9,0);self.assertGreaterEqual(3*33,99);self.assertGreater(99,64)
  # NOT a World: operand2 aliases R0,so an imagined third register loses prediction.
  registers=[15,3];registers[0]=0;registers[2%2]^=15
  self.assertEqual(registers[2%2]&1,1) # repeats wrong port instead of target0
  self.assertEqual(224-112-76-16,20)
 def test_scope_and_source_admission_before_world(self):
  c=plan.config('software');r=dict(configuration=c,role='original:2100488:generate',kind='generate',input=None,
   source_files={},source_sha='a'*64,config_sha='b'*64,grant={},seal='c'*64)
  self.assertEqual(plan.scope(r),'generate')
  for role in ('original:1010100:generate','original:1010200:generate','original:1009700:generate','original:2100382:generate'):
   bad=copy.deepcopy(r);bad['role']=role
   with self.assertRaises(AssertionError):plan.scope(bad)
  bad=copy.deepcopy(r);bad['configuration']['max_population']=True
  with self.assertRaises(AssertionError):plan.scope(bad)
  for seed in source.RESERVED+(1009800,1010000):
   with self.assertRaises(AssertionError):source.admit(seed,source.ADMISSION)
  with self.assertRaises(AssertionError):source.target_mask(1010102,0)
  with self.assertRaises(AssertionError):literal.label_mask(1010102,0)
 def test_numeric_witnesses_and_negative_energy_separation(self):
  self.assertEqual(str(acceptance.tail(10,0)),'1/1024')
  self.assertGreater(acceptance.tail(6,0),acceptance.Fraction(1,80))
  self.assertEqual(acceptance.tail(0,0),1)
  rows=mock_rows();value=acceptance.interpret(rows)
  self.assertTrue(value['robust_functional_selection']);self.assertTrue(value['robust_strong_reference_value'])
  self.assertTrue(all(not p['nominal_costed_value'] and not p['finite_cohort_energy_gain'] for p in value['priors']))
  null=copy.deepcopy(rows)
  for r in null:r['reset']=r['correct']
  self.assertFalse(acceptance.interpret(null)['robust_functional_selection'])
  for bad in (rows[:-1],rows[:-1]+[rows[0]]):
   with self.assertRaises(AssertionError):acceptance.interpret(bad)
  bad=copy.deepcopy(rows);bad[0]['C']=True
  with self.assertRaises(AssertionError):acceptance.interpret(bad)
 def test_whole_dependency_graph_precharge_lifetime_and_failstop(self):
  for mode,expected in (('software',12),('primary',53)):
   calls=[];endpoints=[];refs=[]
   class Body(dict):pass
   def invoke(role,inputs):
    self.assertTrue(all(r() is None for r in refs));calls.append(role)
    kind=role.split(':')[-1];seed=None if kind=='accept' else int(role.split(':')[1])
    spec=dict(path='D:/OraLab/NONPHYSICS.json',extent=1,sha256='a'*64)
    if kind=='generate':v=Body(seed=seed,software_only=mode=='software',error=None,genesis_attempts=26,records=[dict(role=r) for r in plan.ACTORS]);refs.append(weakref.ref(v))
    elif kind=='audit':v=Body(seed=seed,software_only=mode=='software',verified=True,evidence_inputs=inputs,summaries=[dict(role=r,physics=dict(verified=True)) for r in plan.ACTORS]);refs.append(weakref.ref(v))
    elif kind=='metrics':
     ep=mock_rows(seed);endpoints.extend(ep);v=Body(seed=seed,execution_admission=False,endpoints=ep,
      rows=[dict(role=r,completed=60,successes=60,C=400,warm_packets=list(range(48))) for r in plan.ACTORS])
    else:v=acceptance.interpret(endpoints)
    return dict(spec=spec,value=v,chain=dict(role=role,body=spec,request=spec,native=spec))
   value=plan.orchestrate(mode,lambda key:calls.append('refuse:'+key),invoke,lambda *args:None)
   self.assertEqual(len(calls),expected);self.assertEqual(calls[:4],['refuse:'+k for k in ('role','configuration','source_sha','seal')])
   self.assertEqual(len(value['endpoints']),4*len(plan.SEEDS[mode]))
   raw,fail,lim=plan.layout(mode,{'source.py':1024},{'owner.json':1024},1024)
   self.assertEqual(sum(k.startswith('native/') for k in raw),expected+(2 if mode=='software' else 0))
   self.assertLessEqual(sum(lim.values()),(1920 if mode=='software' else 7552)*1024**2)
  called=[]
  def fail(role,inputs):called.append(role);raise RuntimeError('NON-PHYSICS stop')
  with self.assertRaises(RuntimeError):plan.orchestrate('primary',lambda k:None,fail,lambda *x:None)
  self.assertEqual(len(called),1)
  self.assertLess(26*(512*4096+65536)+1048576,64*1024**2)
  fixture=json.loads((ROOT/'data/credited-fallback86-controls/active-size-fixture-v1.json').read_bytes())
  event=fixture['ordinary_event_union'];event['tick']=1024
  event['after']['code']=[[31,511] for _ in range(96)]
  annotation=dict(tick=1024,dispatch_pc=31,completed_before=60,
   entry=dict(previous_pc=31,actual_entry=31,projected_entry=31,completed=60,active=1),
   read=None,completion=dict(completed=60,previous_pc=31,entry=31,energy=224),cost_after=512)
  self.assertLess(len(json.dumps([event,annotation],sort_keys=True,separators=(',',':')).encode()),4096)
  self.assertLess(fixture['static_snapshot_bytes'],65536)
 def test_literal_and_kernel_custody_invariants(self):
  old=ast.parse((ROOT/'experiments/digital_credited_fallback87v2_referee.py').read_bytes())
  new=ast.parse((ROOT/'experiments/digital_strategy88_referee.py').read_bytes())
  for name in ('newborn','charge','packet','write','conserved'):
   a=next(n for n in ast.walk(old) if isinstance(n,ast.FunctionDef) and n.name==name)
   b=next(n for n in ast.walk(new) if isinstance(n,ast.FunctionDef) and n.name==name)
   self.assertEqual(ast.dump(a),ast.dump(b))
  imports={n.module for n in ast.walk(new) if isinstance(n,ast.ImportFrom)}|{x.name for n in ast.walk(new) if isinstance(n,ast.Import) for x in n.names}
  self.assertLessEqual(imports,{'hashlib','json'})
  engine=(ROOT/'experiments/digital_memory80.py').read_bytes()
  self.assertIn(hashlib.sha256(engine).hexdigest(),{'1826b33893321d1a7a603ccef690e13b92ed16f26d6e6c093f14a45ca367e104','dc4b9ebfc6a38a12863df2a569e8f2d0722ed91e09ade14ca8693b08455bea64'})
  self.assertIn('registers=[0,0]',engine.decode())
  child=(ROOT/'experiments/digital_strategy88_child.py').read_text(encoding='utf-8')
  self.assertLess(child.index('kind=plan.scope(request)'),child.index("if kind=='accept':value=accept(request)"))
  worker=(ROOT/'lab/strategy88_pure_worker_v1.py').read_text(encoding='utf-8')
  self.assertLess(worker.index('sys.path.insert(0,str(Path(__file__).resolve().parents[1]))'),worker.index('from experiments import'))
if __name__=='__main__':unittest.main()
