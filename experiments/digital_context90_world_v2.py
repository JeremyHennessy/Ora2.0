"""Prospective known-software task adapter; no construction or target query on import."""
import types,weakref
from experiments import digital_context90_engine_v2 as engine
from experiments import digital_context90_task_source_v1 as source
_RUNTIME=weakref.WeakKeyDictionary()

def bind(function,labels=None):
 namespace=dict(function.__globals__);namespace.update(SOFTWARE=source.SOFTWARE,MASKS=labels)
 return types.FunctionType(function.__code__,namespace,function.__name__,function.__defaults__,function.__closure__)

_genesis=bind(engine.World.__init__)

def feedback_value(phase,value):
 if phase not in ('cue','pre','act','post','ready') or type(value) is not int or value not in (0,1,2):raise ValueError('feedback phase')
 return value if phase=='ready' else 2

class Labels:
 def __init__(self,runtime):self.runtime=runtime
 def __getitem__(self,index):
  r=self.runtime
  assert source.SOFTWARE[index]==r.seed and r.phase=='act'
  bit=(source.label_mask(r.seed,r.completed,r.admission)>>r.original_cue)&1
  return 255 if bit else 0

class Runtime:
 def __init__(self,seed,role,admission):
  self.seed=seed;self.role=role;self.admission=admission;self.completed=0;self.phase='cue';self.original_cue=None;self.ledger=[]
  code=source.programme(role);self.cost=3*len(code)+code[0][1]+8
 def observe(self):
  channel={'cue':'cue','pre':'pre','post':'post'}[self.phase]
  symbol=source.observation(self.seed,self.completed,channel,self.admission)
  if self.phase=='cue':self.original_cue=symbol;self.phase='pre'
  elif self.phase=='pre':self.phase='act'
  else:self.phase='ready'
  return channel,symbol

class World(engine.World):
 def __init__(self,seed,role,admission=None):
  source.admit(seed,admission);code=source.programme(role);r=Runtime(seed,role,admission)
  _genesis(self,seed,code[0][1],'no_variation',1,0,code,admission)
  _RUNTIME[self]=dict(runtime=r,transition=bind(engine.World.step,Labels(r)))
 def stop_reason(self):
  r=_RUNTIME[self]['runtime']
  if not self.entities:return 'death'
  if r.completed>=source.DECISIONS:return 'decisions'
  if self.tick>=source.HORIZON:return 'horizon'
  if r.cost+7+(16 if self.tick+1==64 else 0)>source.COST_BUDGET:return 'cost_budget'
  return None
 def step(self):
  if self.stop_reason() is not None:return False
  owner=_RUNTIME[self];r=owner['runtime'];e=self.entities[0];pc=e['pc'];op,a,b=[v[0] for v in e['code'][3*pc:3*pc+3]]
  phase_before=r.phase;trial=r.completed
  if op==0:assert r.phase in ('cue','pre','post'),'Invalid observation protocol'
  if op==6:assert r.phase=='act','Action before task observations'
  assert owner['transition'](self);event=self.events[-1];observation=None;feedback_read=None
  if op==0:
   channel,value=r.observe();observation=dict(channel=channel,value=value,resource_cue=event['sense']['cue'],packet=event['sense']['packet'])
   e['cue']=value;e['registers'][a%2]=value;event['sense']['cue']=value
  elif op==6:r.phase='post'
  elif op==1:
   value=feedback_value(r.phase,e['feedback']);e['registers'][a%2]=value;event['read_feedback']=value
   feedback_read=dict(available=int(r.phase=='ready'),value=value)
  if 0 in self.entities:event['after']=engine.clone(e)
  event['state_hash']=engine.h(self.snapshot(False));r.cost+=1+event.get('logic_fee',0)+event.get('penalty',0)+event.get('release_energy',0)
  assert r.cost<=source.COST_BUDGET;completion=None
  if source.completed_edge(r.role,pc,event.get('after')):
   assert r.phase=='ready';r.completed+=1;r.phase='cue';r.original_cue=None
   completion=dict(completed=r.completed,entry=e['pc'],energy=e['energy'])
  r.ledger.append(dict(tick=self.tick,pc=pc,trial=trial,phase_before=phase_before,observation=observation,feedback_read=feedback_read,phase_after=r.phase,completion=completion,cost_after=r.cost))
  return True
 def control_ledger(self):return _RUNTIME[self]['runtime'].ledger
 def run(self,*args):raise RuntimeError('Separate registered bounded SOFTWARE custody required')
