"""Six NEW pure integration groups; constructor/step are never called."""
import ast,copy,json,unittest
from pathlib import Path
from experiments import digital_context90_engine_v2 as engine
from experiments import digital_context90_world_v2 as task
from experiments import digital_context90_task_source_v1 as source
from experiments import digital_context90_referee_v2 as literal
BASE=Path(__file__).resolve().parent

def legacy(name,relative):
 p=BASE/name
 return p if p.exists() else BASE.parent/relative

def node(text,name):return next(n for n in ast.parse(text).body if isinstance(n,(ast.FunctionDef,ast.ClassDef)) and n.name==name)
def canon(n):return ast.dump(n,include_attributes=False)

def synthetic_union():
 e=dict(id=0,parent=None,generation=0,lineage=[],code=[[31,511] for _ in range(96)],state_units=[511]*16,memory=[15]*8,registers=[15,15],pc=31,feedback=2,cue=7,pos=0,energy=224,nursery=[],pending=None,lease=351,turns=1200,copy_sessions=0,children=0)
 paid=dict(version='CONTEXT90-PACKED-ACCESS-v2',decoded=[23,1,0],cpu=1,logic_fee=2,actor_cost=3,required=3,completed=True,read=dict(slot=15,cell=7,offset=2,word=15,value=3),write=dict(slot=15,cell=7,offset=2,before=15,value=3,after=15))
 event=dict(tick=1200,actor=0,before='f'*64,energy_before=224,input=[dict(packet=351,cue=7,energy=20,outcome='external_rejected') for _ in range(16)],kind='ordinary',decoded=[23,1,0],release_energy=16,packed=paid,logic_fee=2,penalty=4,after=e,state_hash='f'*64)
 ledger=dict(tick=1200,pc=31,trial=59,phase_before='ready',observation=dict(channel='post',value=7,resource_cue=7,packet=351),feedback_read=dict(available=1,value=2),phase_after='cue',completion=dict(completed=60,entry=27,energy=224),cost_after=1800)
 return len(json.dumps(dict(event=event,ledger=ledger),sort_keys=True,separators=(',',':')).encode())

class Integration(unittest.TestCase):
 def test_new_programmes_and_scope(self):
  self.assertEqual(source.ROLES,literal.ROLES)
  for role in source.ROLES:
   p=source.programme(role);self.assertEqual(p,literal.programme(role));engine.validate(p)
   self.assertGreaterEqual(engine.FACTORY-3*len(p)-p[0][1]-8-engine.STARTUP,16)
  for seed in (True,2100589,1010500,1010600,0,2100694):
   for impl in (source,literal):
    with self.assertRaises((ValueError,AssertionError)):impl.admit(seed,source.ADMISSION)
  with self.assertRaises(ValueError):source.admit(2100690,'wrong')
  self.assertEqual((engine.STARTUP,engine.FACTORY,engine.INITIAL_ENERGY),(200,328,1608))

 def test_new_observations_and_phase_masks(self):
  for seed in source.SOFTWARE:
   for trial in range(60):
    self.assertEqual(source.label_mask(seed,trial,source.ADMISSION),literal.label_mask(seed,trial,source.ADMISSION))
    for channel in ('cue','pre','post'):
     self.assertEqual(source.observation(seed,trial,channel,source.ADMISSION),literal.task_observation(seed,trial,channel,source.ADMISSION))
  for trial in (True,-1,60):
   with self.assertRaises(ValueError):source.observation(2100690,trial,'cue',source.ADMISSION)

 def test_new_protocol_and_feedback(self):
  for role in source.ROLES:
   r=task.Runtime(2100690,role,source.ADMISSION)
   for trial in range(60):
    for channel in ('cue','pre','post'):
     if channel=='post':r.phase='post'  # Synthetic ACT edge; no World/step.
     self.assertEqual(r.observe(),(channel,source.observation(2100690,trial,channel,source.ADMISSION)))
    self.assertEqual(r.phase,'ready');r.completed+=1;r.phase='cue'
  for phase in ('cue','pre','act','post','ready'):
   for f in (0,1,2):self.assertEqual(task.feedback_value(phase,f),f if phase=='ready' else 2)
  for phase in ('unknown',None):
   with self.assertRaises(ValueError):task.feedback_value(phase,1)

 def test_new_actual_paid_branch_without_step(self):
  text=Path(engine.__file__).read_bytes();tree=ast.parse(text)
  branch=next(n for n in ast.walk(tree) if isinstance(n,ast.If) and isinstance(n.test,ast.Compare) and isinstance(n.test.left,ast.Name) and n.test.left.id=='op' and isinstance(n.test.ops[0],ast.In) and isinstance(n.test.comparators[0],ast.Tuple) and [v.value for v in n.test.comparators[0].elts]==[22,23,24,25])
  fn=ast.FunctionDef(name='paid_branch',args=ast.arguments(posonlyargs=[],args=[ast.arg(arg=n) for n in ('self','e','op','a','b','old','event')],kwonlyargs=[],kw_defaults=[],defaults=[]),body=branch.body,decorator_list=[])
  scope={'packed_transition':engine.packed_transition};exec(compile(ast.fix_missing_locations(ast.Module(body=[fn],type_ignores=[])),'new-synthetic-paid-branch','exec'),scope)
  class Meter:
   def __init__(self):self.heat=0
   def debit(self,e,n):
    assert e['energy']>=n;e['energy']-=n;self.heat+=n
  for instruction in ([22,0,1],[23,1,0],[24,0,8],[25,7,3]):
   for energy in range(1,6):
    original=dict(memory=[10]*8,registers=[3,9],pc=6,energy=energy)
    expect,receipt=literal.literal_packed(original,instruction,29)
    e=copy.deepcopy(original);e.update(code=[[0,i] for i in range(87)],pc=7,energy=energy-1);meter=Meter();event={}
    scope['paid_branch'](meter,e,*instruction,6,event)
    self.assertEqual({k:e[k] for k in original},expect);self.assertEqual(event,dict(packed=receipt,logic_fee=receipt['logic_fee']));self.assertEqual(meter.heat,receipt['logic_fee'])

 def test_new_physics_source_custody(self):
  original=ast.parse(legacy('legacy-engine.py','experiments/digital_memory80.py').read_bytes())
  changed=ast.parse(Path(engine.__file__).read_bytes())
  oldclass=next(n for n in original.body if isinstance(n,ast.ClassDef) and n.name=='World');newclass=next(n for n in changed.body if isinstance(n,ast.ClassDef) and n.name=='World')
  old={n.name:n for n in oldclass.body if isinstance(n,ast.FunctionDef)};new={n.name:n for n in newclass.body if isinstance(n,ast.FunctionDef)}
  for name in ('effective','snapshot','packet','input','debit','finish_copy','copy','draw','remove'):self.assertEqual(canon(old[name]),canon(new[name]))
  # Explicitly compare all old paid operation arms; new branch is appended only.
  oldstep=old['step'];newstep=new['step']
  def arms(step):
   result={}
   for n in ast.walk(step):
    if isinstance(n,ast.If) and isinstance(n.test,ast.Compare) and isinstance(n.test.left,ast.Name) and n.test.left.id=='op' and isinstance(n.test.ops[0],ast.Eq):result[n.test.comparators[0].value]=[canon(b) for b in n.body]
   return result
  self.assertEqual(arms(oldstep),arms(newstep))
  self.assertTrue(all(n.module in ('hashlib','json') for n in ast.walk(ast.parse(Path(literal.__file__).read_bytes())) if isinstance(n,ast.ImportFrom)))
  imports=[a.name for n in ast.walk(ast.parse(Path(literal.__file__).read_bytes())) if isinstance(n,ast.Import) for a in n.names];self.assertEqual(imports,['hashlib','json'])

 def test_new_synthetic_union_and_whole_extent(self):
  size=synthetic_union();self.assertLessEqual(size,4096)
  self.assertLessEqual(10*1200*4096+4*1024**2,56*1024**2)
  self.assertEqual(max(3*n+q+8 for n in range(1,33) for q in (2,4,8)),112)

if __name__=='__main__':unittest.main()
