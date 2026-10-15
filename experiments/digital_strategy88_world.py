"""Narrow registry/task/semantic-entry adapter over unchanged paid MEMORY80 code."""
import types,weakref
from experiments import digital_memory80 as engine
from experiments import digital_strategy88_source as source
_RUNTIME=weakref.WeakKeyDictionary()
def bind(function,labels=None):
 namespace=dict(function.__globals__);namespace.update(SOFTWARE=source.SEEDS,MASKS=labels)
 return types.FunctionType(function.__code__,namespace,function.__name__,function.__defaults__,function.__closure__)
_genesis=bind(engine.World.__init__)
class Labels:
 def __init__(self,seed,admission,scratch):self.seed=seed;self.admission=admission;self.scratch=scratch
 def __getitem__(self,index):
  assert source.SEEDS[index]==self.seed;packet=self.scratch['packet'];assert type(packet) is int and packet>=0
  return source.target_mask(self.seed,packet,self.admission)
class Runtime:
 def __init__(self,role):
  self.role=role;self.completed=0;self.pending=None;self.dispatch_pc=None;self.ledger=[]
  self.cost=3*len(source.programme(role))+10
 def before(self,entity):
  entry=None
  if self.pending is not None:
   previous,actual=self.pending;assert entity['pc']==actual
   projected=source.entry_projection(self.role,self.completed,actual) if ':' in self.role else actual
   entry=dict(previous_pc=previous,actual_entry=actual,projected_entry=projected,completed=self.completed,active=int(self.completed>=48))
   entity['pc']=projected;self.pending=None
  self.dispatch_pc=entity['pc'];return entry
 def after(self,event):
  self.cost+=1+event.get('penalty',0)+event.get('release_energy',0);assert self.cost<=512
  after=event.get('after')
  if source.completed_edge(self.role,self.dispatch_pc,after):
   self.completed+=1;self.pending=(self.dispatch_pc,after['pc'])
   return dict(completed=self.completed,previous_pc=self.dispatch_pc,entry=after['pc'],energy=after['energy'])
  return None
class World(engine.World):
 def __init__(self,seed,role,admission=None):
  source.admit(seed,admission);assert role in source.ROLES
  runtime=Runtime(role);_genesis(self,seed,2,'no_variation',1,0,source.programme(role))
  scratch={'packet':None};_RUNTIME[self]=dict(runtime=runtime,scratch=scratch,transition=bind(engine.World.step,Labels(seed,admission,scratch)))
 def packet(self,entity,reserve=False):
  value=engine.World.packet(self,entity,reserve)
  if not reserve:_RUNTIME[self]['scratch']['packet']=value
  return value
 def stop_reason(self):
  r=_RUNTIME[self]['runtime']
  if not self.entities:return 'death'
  if r.completed>=60:return 'decisions'
  if self.tick>=1024:return 'horizon'
  if r.cost+5+(16 if self.tick+1==64 else 0)>512:return 'cost_budget'
  return None
 def step(self):
  if self.stop_reason() is not None:return False
  owner=_RUNTIME[self];r=owner['runtime'];completed=r.completed;entry=r.before(self.entities[0]);pc=r.dispatch_pc
  assert owner['transition'](self);event=self.events[-1];completion=r.after(event)
  r.ledger.append(dict(tick=event['tick'],dispatch_pc=pc,completed_before=completed,entry=entry,read=None,completion=completion,cost_after=r.cost))
  return True
 def control_ledger(self):return _RUNTIME[self]['runtime'].ledger
 def run(self,*args):raise RuntimeError('Separate registered bounded custody required')
