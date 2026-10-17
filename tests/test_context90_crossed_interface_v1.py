"""Seven NEW synthetic interface/AST groups; never import/construct/step World."""
import ast,copy,hashlib,json,unittest
from pathlib import Path
from experiments import digital_context90_crossed_registry_v1 as registry
from experiments import digital_context90_crossed_programme_v1 as source
from experiments import digital_context90_crossed_referee_v1 as literal
BASE=Path(__file__).resolve().parent

def path(name,relative):
 p=BASE/name
 return p if p.exists() else BASE.parent/relative

def tree(name,relative):return ast.parse(path(name,relative).read_bytes())
def function(t,name):return next(n for n in t.body if isinstance(n,ast.FunctionDef) and n.name==name)
def method(t,name):
 c=next(n for n in t.body if isinstance(n,ast.ClassDef) and n.name=='World');return next(n for n in c.body if isinstance(n,ast.FunctionDef) and n.name==name)
def dump(n):return ast.dump(n,include_attributes=False)

class Interface(unittest.TestCase):
 def test_new_admission_guard(self):
  t=tree('new-engine.py','experiments/digital_context90_crossed_engine_v1.py');init=method(t,'__init__');probe=ast.parse('def probe(seed,admission): pass').body[0];probe.body=copy.deepcopy(init.body[:2])+[ast.Return(ast.Constant(True))];module=ast.fix_missing_locations(ast.Module(body=[probe],type_ignores=[]));scope={};exec(compile(module,'<SYNTHETIC admission guard>','exec'),scope)
  f=scope['probe'];self.assertTrue(f(2100790,'CONTEXT90-CROSSED-SOFTWARE-v1'))
  for seed in range(1900900,1900909):self.assertTrue(f(seed,'CONTEXT90-CROSSED-PRIMARY-v1'))
  for seed,a in ((True,'CONTEXT90-CROSSED-SOFTWARE-v1'),(2100790.0,'CONTEXT90-CROSSED-SOFTWARE-v1'),(2100690,'CONTEXT90-CROSSED-SOFTWARE-v1'),(1010600,'CONTEXT90-CROSSED-PRIMARY-v1'),(2100790,'CONTEXT90-SOFTWARE-v1')):
   with self.assertRaises(ValueError):f(seed,a)
 def test_new_complete_programme_binding(self):
  for role in source.ACTORS:self.assertEqual(source.programme(role),literal.programme(role))
  self.assertEqual(len(literal.ROLES),19)
 def test_new_case_and_observation_interface(self):
  cert=dict(schema='CONTEXT90-CROSSED-DRAWS-v1',mode='primary',draws=[dict(tuple_id='C90X1-P'+str(i).zfill(2),words=[format(i,'064x')],rank=i) for i in range(9)])
  # Synthetic certificate arithmetic only, not an OS draw or registered PRIMARY artifact.
  for i in range(9):self.assertEqual(literal.independent_case(1900900+i,i,'AA','CONTEXT90-CROSSED-PRIMARY-v1',cert),registry.decode_rank(i))
  t=literal.independent_case(2100790,0,'AA','CONTEXT90-CROSSED-SOFTWARE-v1',None)
  for cell in registry.CELLS:
   for trial in range(112):
    self.assertEqual(literal.label_mask(t,cell,trial),registry.mask(t,cell,trial))
    for channel in ('cue','pre','post'):self.assertEqual(literal.task_observation(t,0,trial,channel),registry.observation(t,0,trial,channel))
  with self.assertRaises(AssertionError):literal.independent_case(2100790.0,0,'AA','CONTEXT90-CROSSED-SOFTWARE-v1',None)
  bad=copy.deepcopy(cert);bad['draws'][0]['rank']=True
  with self.assertRaises(AssertionError):literal.independent_case(1900900,0,'AA','CONTEXT90-CROSSED-PRIMARY-v1',bad)
 def play(self,rewrite=False,complete=True):
  t=dict(c=0,A=45,C=213,B=154);o=literal.Origins('q8:A',t);tick=0
  def send(trial,pc,op,regs,memory,**fields):
   nonlocal tick
   tick+=1;obs=fields.pop('observation',None);completion=fields.pop('completion',None);event=dict(tick=tick,decoded=[op,0,1],after=dict(registers=regs,memory=memory));event.update(fields);o.observe(event,dict(trial=trial,pc=pc,observation=obs,feedback_read=None,completion=completion))
  memory=[0]*8
  def decision(trial,route,value):
   slot=1+8*route;cell=slot//2;offset=2*(slot%2);regs=[value,slot]
   send(trial,27 if route==0 else 1,0,regs,memory[:],observation=dict(channel='cue',value=1))
   send(trial,4,22,regs,memory[:],packed=dict(read=dict(slot=slot,cell=cell,offset=offset,word=memory[cell],value=value),write=None))
  def act(trial,route,value,feedback):send(trial,5,6,[value,1+8*route],memory[:],feedback=feedback,attempt=dict(port=value%2,success=feedback))
  def write(trial,pc,route,value):
   slot=1+8*route;cell=slot//2;before=memory[cell];old=before//4%4;memory[cell]=before+(value-old)*4
   send(trial,pc,23,[value,slot],memory[:],packed=dict(read=None,write=dict(slot=slot,cell=cell,offset=2,before=before,value=value,after=memory[cell])))
  decision(0,0,0);act(0,0,0,0);write(0,25,0,1)
  if rewrite:
   decision(80,0,1);act(80,0,1,0);write(80,22,1,2);decision(95,1,2);act(95,1,2,0);write(95,22,0,1)
  decision(97,0,1);act(97,0,1,1)
  if complete:send(97,26,25,[1,1],memory[:],completion=dict(completed=98))
  return o
 def test_new_origin_completed_credit_and_rewrites(self):
  a=self.play();self.assertEqual((a.Q,a.R),(1,1));b=self.play(rewrite=True);self.assertEqual((b.Q,b.R),(1,0));c=self.play(complete=False);self.assertEqual((c.Q,c.R),(0,0));self.assertEqual(c.correct,1)
 def test_new_unchanged_physics_and_origin_before_hash_comparison(self):
  new=tree('new-engine.py','experiments/digital_context90_crossed_engine_v1.py');old=tree('old-engine.py','experiments/digital_context90_engine_v2.py')
  for name in ('step','body','check','input','packet','debit','snapshot','remove','copy','divide'):self.assertEqual(dump(method(new,name)),dump(method(old,name)))
  newer=tree('new-literal.py','experiments/digital_context90_crossed_referee_v1.py');older=tree('old-literal.py','experiments/digital_context90_referee_v2.py');self.assertEqual(dump(function(newer,'literal_packed')),dump(function(older,'literal_packed')))
  audit=function(newer,'audit');observer=next(n.lineno for n in ast.walk(audit) if isinstance(n,ast.Call) and ast.unparse(n.func)=='origins.observe');comparison=next(n.lineno for n in ast.walk(audit) if isinstance(n,ast.Assert) and 'event == receipt' in ast.unparse(n.test));self.assertLess(observer,comparison)
  imports=[n for n in newer.body if isinstance(n,(ast.Import,ast.ImportFrom))];self.assertEqual([a.name for n in imports for a in n.names],['hashlib','json'])
 def test_new_actual_child_guard_and_entropy_failure_shape(self):
  t=tree('new-child.py','experiments/digital_context90_crossed_child_v1.py');main=function(t,'main');calls=[(n.lineno,ast.unparse(n.func)) for n in ast.walk(main) if isinstance(n,ast.Call)]
  line=lambda k:min(n for n,v in calls if v==k)
  for k in ('registry.scope','boundary.verify_source','boundary.validate_grant'):
   self.assertLess(line(k),line('os.urandom'));self.assertLess(line(k),line('generate'))
  self.assertLess(line("value['draws'].append"),line('os.urandom'));self.assertLess(line('os.urandom'),line('transport.record'))
  self.assertIn("value['error'] = error",ast.unparse(main));self.assertIn('except BaseException',ast.unparse(main));self.assertEqual(sum(isinstance(n,ast.Call) and ast.unparse(n.func)=='os.urandom' for n in ast.walk(t)),1)
  generate=function(t,'generate');self.assertLess(next(n.lineno for n in ast.walk(generate) if isinstance(n,ast.Call) and ast.unparse(n.func)=='checked_definition'),next(n.lineno for n in ast.walk(generate) if isinstance(n,ast.Call) and ast.unparse(n.func)=='World'))
 def test_new_event_and_proof_extents_bound(self):
  def fields(t):
   found=set()
   for n in ast.walk(method(t,'step')):
    if isinstance(n,ast.Call) and isinstance(n.func,ast.Name) and n.func.id=='dict':found.update(k.arg for k in n.keywords)
    if isinstance(n,ast.Subscript) and isinstance(n.value,ast.Name) and n.value.id=='event' and isinstance(n.slice,ast.Constant):found.add(n.slice.value)
   return found
  self.assertEqual(fields(tree('new-world.py','experiments/digital_context90_crossed_world_v1.py')),fields(tree('old-world.py','experiments/digital_context90_world_v2.py')))
  receipt=json.loads(path('closed-interface.json','../../reports/context90-physical-interface-prepared-v1.json').read_bytes());self.assertTrue(receipt['verified']);self.assertLessEqual(receipt['values'][0]['synthetic_union_bytes'],4096)
  o=self.play(rewrite=True);enc=lambda v:json.dumps(v,sort_keys=True,separators=(',',':')).encode();self.assertLess(max(map(lambda x:len(enc(x)),o.channels)),512);self.assertLess(6*112*3*512+65536,2*1024**2)
  for n,cap in ((6,56),(3,28),(5,44)):self.assertLess(n*2040*4096+4*1024**2,cap*1024**2)
  self.assertLess(sum(len(enc(source.programme(r))) for r in source.ACTORS),65536)

if __name__=='__main__':unittest.main()
