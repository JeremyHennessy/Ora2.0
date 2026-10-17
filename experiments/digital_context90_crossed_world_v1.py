"""Crossed task runtime; actual constructor calls require separately guarded child."""
import types,weakref
from experiments import digital_context90_crossed_engine_v1 as engine
from experiments import digital_context90_crossed_registry_v1 as registry
from experiments import digital_context90_crossed_programme_v1 as source
_RUNTIME=weakref.WeakKeyDictionary()

def bind(function,labels=None):
 namespace=dict(function.__globals__)
 if labels is not None:namespace['MASKS']=labels
 return types.FunctionType(function.__code__,namespace,function.__name__,function.__defaults__,function.__closure__)

class Labels:
 def __init__(self,runtime):self.runtime=runtime
 def __getitem__(self,index):
  r=self.runtime
  assert engine.SOFTWARE[index]==r.seed and r.phase=='act'
  bit=(registry.mask(r.definition,r.cell,r.completed)//(2**r.original_cue))%2
  return 255 if bit else 0

class Runtime:
 def __init__(self,index,cell,role,mode,certificate):
  c=registry.config(mode);registry.integer(index,0,len(c['tuple_ids'])-1)
  if cell not in registry.CELLS or role not in source.ACTORS:raise ValueError('complete registered case')
  self.definition=registry.tuple_for(mode,index,certificate);self.index=index;self.cell=cell;self.role=role;self.mode=mode;self.seed=c['resource_seeds'][index]
  self.completed=0;self.phase='cue';self.original_cue=None;self.ledger=[];code=source.programme(role);self.cost=3*len(code)+code[0][1]+8
 def observe(self):
  channel={'cue':'cue','pre':'pre','post':'post'}[self.phase];value=registry.observation(self.definition,self.index,self.completed,channel)
  if self.phase=='cue':self.original_cue=value;self.phase='pre'
  elif self.phase=='pre':self.phase='act'
  else:self.phase='ready'
  return channel,value

class World(engine.World):
 def __init__(self,index,cell,role,mode,certificate=None,admission=None):
  expected={'software':'CONTEXT90-CROSSED-SOFTWARE-v1','primary':'CONTEXT90-CROSSED-PRIMARY-v1'}
  if mode not in expected or admission!=expected[mode]:raise ValueError('Separate crossed registration and guarded child required')
  r=Runtime(index,cell,role,mode,certificate);code=source.programme(role)
  engine.World.__init__(self,r.seed,code[0][1],'no_variation',1,0,code,admission)
  _RUNTIME[self]=dict(runtime=r,transition=bind(engine.World.step,Labels(r)))
 def stop_reason(self):
  r=_RUNTIME[self]['runtime']
  if not self.entities:return 'death'
  if r.completed>=112:return 'decisions'
  if self.tick>=2040:return 'horizon'
  if r.cost+7+(16 if self.tick+1==64 else 0)>3040:return 'cost_budget'
  return None
 def step(self):
  if self.stop_reason() is not None:return False
  owner=_RUNTIME[self];r=owner['runtime'];e=self.entities[0];pc=e['pc'];op,a,b=[v[0] for v in e['code'][3*pc:3*pc+3]];phase_before=r.phase;trial=r.completed
  if op==0:assert r.phase in ('cue','pre','post')
  if op==6:assert r.phase=='act'
  assert owner['transition'](self);event=self.events[-1];observation=None;feedback_read=None
  if op==0:
   channel,value=r.observe();observation=dict(channel=channel,value=value,resource_cue=event['sense']['cue'],packet=event['sense']['packet']);e['cue']=value;e['registers'][a%2]=value;event['sense']['cue']=value
  elif op==6:r.phase='post'
  elif op==1:
   value=e['feedback'] if r.phase=='ready' else 2;e['registers'][a%2]=value;event['read_feedback']=value;feedback_read=dict(available=int(r.phase=='ready'),value=value)
  if 0 in self.entities:event['after']=engine.clone(e)
  event['state_hash']=engine.h(self.snapshot(False));r.cost+=1+event.get('logic_fee',0)+event.get('penalty',0)+event.get('release_energy',0);assert r.cost<=3040
  completion=None
  if source.completed_edge(r.role,pc,event.get('after')):
   assert r.phase=='ready';r.completed+=1;r.phase='cue';r.original_cue=None;completion=dict(completed=r.completed,entry=e['pc'],energy=e['energy'])
  r.ledger.append(dict(tick=self.tick,pc=pc,trial=trial,phase_before=phase_before,observation=observation,feedback_read=feedback_read,phase_after=r.phase,completion=completion,cost_after=r.cost));return True
 def control_ledger(self):return _RUNTIME[self]['runtime'].ledger
 def run(self,*args):raise RuntimeError('Only separately registered bounded crossed child stepping')
