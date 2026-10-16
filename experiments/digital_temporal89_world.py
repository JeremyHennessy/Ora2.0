"""Narrow task observation/label/feedback hooks over unchanged paid MEMORY80 step.

Whole custody/CI/separate registration must admit each role before construction.
No World or target is created on import. Runtime is external trusted task state,
not an additional organism input or an uncharged organism computation.
"""
import types,weakref
from experiments import digital_memory80 as engine
from experiments import digital_temporal89_source as source

_RUNTIME=weakref.WeakKeyDictionary()

def bind(function,labels=None):
 namespace=dict(function.__globals__);namespace.update(SOFTWARE=source.SEEDS,MASKS=labels)
 return types.FunctionType(function.__code__,namespace,function.__name__,function.__defaults__,function.__closure__)

_genesis=bind(engine.World.__init__)

def feedback_value(phase,value):
 assert phase in ('cue','pre','act','post','ready') and type(value) is int and value in (0,1,2)
 return value if phase=='ready' else 2

def model_read(e,pc,a,b,active,arm):
 index=e['registers'][b%2]%len(e['memory'])
 if active and arm=='recall_disabled' and pc==3:index=0
 value=0 if active and arm=='model_disabled' else e['memory'][index]
 return dict(pc=pc,index=index,source_value=e['memory'][index],returned=value,active=int(active))

def store_plan(e,pc,a,b,active,arm):
 index=e['registers'][a%2]%len(e['memory'])
 return dict(pc=pc,index=index,before=e['memory'][index],attempted=e['registers'][b%2],applied=int(not(active and arm=='update_frozen')))

class Labels:
 def __init__(self,runtime):self.runtime=runtime
 def __getitem__(self,index):
  r=self.runtime;assert source.SEEDS[index]==r.seed and r.phase=='act'
  # Old resource cue is not a new sensory input: a constant mask supplies the
  # target for the separately declared retained task cue,whatever that packet cue.
  bit=(source.label_mask(r.seed,r.completed,r.admission)>>r.original_cue)&1
  return 255 if bit else 0

class Runtime:
 def __init__(self,seed,role,admission):
  self.seed=seed;self.role=role;self.admission=admission;self.completed=0
  self.phase='cue';self.original_cue=None;self.credit_due=False;self.ledger=[]
  code=source.programme(role);self.cost=3*len(code)+code[0][1]+8
 def before(self,e):
  cut=None
  if self.credit_due:
   assert self.phase=='ready'
   if self.completed>=48 and source.arm(self.role)=='credit_erased':
    cut=dict(register=1,before=e['registers'][1],after=0,trial=self.completed)
    e['registers'][1]=0
   self.credit_due=False
  return cut
 def observe(self):
  channel={'cue':'cue','pre':'pre','post':'post'}[self.phase]
  symbol=source.observation(self.seed,self.completed,channel,self.admission)
  if self.phase=='cue':self.original_cue=symbol;self.phase='pre'
  elif self.phase=='pre':self.phase='act'
  else:self.phase='ready';self.credit_due=True
  return channel,symbol

class World(engine.World):
 def __init__(self,seed,role,admission=None):
  source.admit(seed,admission);assert type(role) is str and role in source.ROLES
  r=Runtime(seed,role,admission);code=source.programme(role)
  _genesis(self,seed,code[0][1],'no_variation',1,0,code)
  _RUNTIME[self]=dict(runtime=r,transition=bind(engine.World.step,Labels(r)))
 def stop_reason(self):
  r=_RUNTIME[self]['runtime']
  if not self.entities:return 'death'
  if r.completed>=60:return 'decisions'
  if self.tick>=1024:return 'horizon'
  if r.cost+5+(16 if self.tick+1==64 else 0)>1024:return 'cost_budget'
  return None
 def step(self):
  if self.stop_reason() is not None:return False
  owner=_RUNTIME[self];r=owner['runtime'];e=self.entities[0]
  cut=r.before(e);pc=e['pc'];op,a,b=[v[0] for v in e['code'][3*pc:3*pc+3]]
  phase_before=r.phase;trial=r.completed;active=trial>=48;arm=source.arm(r.role)
  if op==0:assert r.phase in ('cue','pre','post'),'Invalid observation protocol'
  if op==6:assert r.phase=='act','Action before legal task observations'
  read=None;store=None
  if op==19:
   read=model_read(e,pc,a,b,active,arm)
  if op==20:
   store=store_plan(e,pc,a,b,active,arm)
  assert owner['transition'](self);event=self.events[-1];observation=None;feedback_read=None
  if op==0:
   channel,value=r.observe();observation=dict(channel=channel,value=value,resource_cue=event['sense']['cue'],packet=event['sense']['packet'])
   e['cue']=value;e['registers'][a%2]=value;event['sense']['cue']=value
  elif op==6:r.phase='post'
  elif op==1:
   value=feedback_value(r.phase,e['feedback'])
   e['registers'][a%2]=value;event['read_feedback']=value
   feedback_read=dict(available=int(r.phase=='ready'),value=value)
  elif read is not None:e['registers'][a%2]=read['returned']
  elif store is not None and not store['applied']:e['memory'][store['index']]=store['before']
  if 0 in self.entities:event['after']=engine.clone(e)
  # Every substitution is real source state before the recorded after hashes.
  event['state_hash']=engine.h(self.snapshot(False));r.cost+=1+event.get('penalty',0)+event.get('release_energy',0)
  assert r.cost<=1024;completion=None
  if source.completed_edge(r.role,pc,event.get('after')):
   assert r.phase=='ready' and not r.credit_due
   r.completed+=1;r.phase='cue';r.original_cue=None
   completion=dict(completed=r.completed,entry=e['pc'],energy=e['energy'])
  r.ledger.append(dict(tick=self.tick,pc=pc,trial=trial,phase_before=phase_before,cut=cut,
   observation=observation,read=read,store=store,feedback_read=feedback_read,
   phase_after=r.phase,completion=completion,cost_after=r.cost))
  return True
 def control_ledger(self):return _RUNTIME[self]['runtime'].ledger
 def run(self,*args):raise RuntimeError('Separate registered bounded custody required')
