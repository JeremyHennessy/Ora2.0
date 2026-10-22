"""Prospective shared Context90 resource engine; valid roles require separate custody registration."""
import hashlib,json
from experiments.digital_context90_access_v2 import transition as packed_transition,validate_instruction as packed_validate
VERSION='CONTEXT90-CROSSED-RESOURCE-v1'
SOFTWARE=(2100790,)+tuple(range(1900900,1900909))
MASKS=(0,)*10
CAPACITIES=(2,4,8)
STARTUP=200
FACTORY=328
INITIAL_ENERGY=1608
OPS=(0,1,2,3,4,5,6,7,8,10,12,18,19,20,21,22,23,24,25)
def clone(x):return json.loads(json.dumps(x))
def h(x):return hashlib.sha256(json.dumps(x,sort_keys=True,separators=(',',':')).encode()).hexdigest()
def draw_value(key,stage):return int(h(key)[:8],16)&(7 if stage=='gate' else 3)
def programme(q):
 assert type(q) is int and q in CAPACITIES
 return [[7,q,1],[0,1,0],[19,0,1],[6,0,0],[1,0,0],[8,0,13],[4,1,1],[5,0,1],[8,0,10],[7,0,1],[10,0,0],[12,0,0],[7,0,1],[19,0,1],[21,0,0],[20,1,0],[7,0,1]]
def validate(code):
 assert type(code) is list and 1<=len(code)<=32
 assert all(type(t) is list and len(t)==3 and t[0] in OPS and all(type(v) is int and 0<=v<32 for v in t) for t in code)
 assert code[0][0]==7 and code[0][1] in CAPACITIES and code[0][2]<len(code)
 for t in code:
  if t[0] in (22,23,24,25):packed_validate(t,len(code))

class World:
 def __init__(self,seed,capacity=2,mode='variation',max_population=8,expansion_tick=1536,code=None,admission=None):
  valid=type(seed) is int and ((seed==2100790 and admission=='CONTEXT90-CROSSED-SOFTWARE-v1') or (seed in range(1900900,1900909) and admission=='CONTEXT90-CROSSED-PRIMARY-v1'))
  if not valid:raise ValueError('Separate registered crossed custody required')
  assert mode=='no_variation' and type(max_population) is int and max_population==1 and type(expansion_tick) is int and expansion_tick==0
  assert mode in ('variation','no_variation','inheritance_disabled') and type(max_population) is int and max_population in (1,8)
  assert type(expansion_tick) is int and expansion_tick in (0,1536)
  code=programme(capacity) if code is None else clone(code);validate(code)
  self.seed=seed;self.mode=mode;self.max_population=max_population;self.expansion_tick=expansion_tick
  self.tick=0;self.last=-1;self.next_id=1;self.writes=0;self.births=0;self.deaths=0
  self.offered=0;self.admitted=0;self.rejected=0;self.next_packet=64
  self.heat=3*len(code)+code[0][1]+8;self.constructor_remaining=FACTORY-self.heat-STARTUP
  assert self.constructor_remaining>=16
  span=8 if expansion_tick==0 else 2;self.food={p:p%span for p in range(64)};self.leases={}
  n=3*len(code);bill=n+code[0][1]+8;self.free=list(range(bill,512))
  self.entities={0:self.body(0,None,0,[[v,i] for i,v in enumerate(sum(code,[]))],list(range(n,bill)),[])}
  self.events=[];self.check()
 @staticmethod
 def body(identity,parent,generation,code,units,lineage):
  q=code[1][0]
  return dict(id=identity,parent=parent,generation=generation,lineage=lineage,code=clone(code),state_units=units,memory=[0]*q,registers=[0,0],pc=0,feedback=0,cue=0,pos=0,energy=STARTUP,nursery=[],pending=None,lease=None,turns=0,copy_sessions=0,children=0)
 def effective(self,e):return 2 if self.mode=='inheritance_disabled' else len(e['memory'])
 def check(self):
  units=self.free[:]
  for identity,e in self.entities.items():
   q=e['code'][1][0];validate([[v[0] for v in e['code'][i:i+3]] for i in range(0,len(e['code']),3)])
   assert q in CAPACITIES and len(e['memory'])==q and len(e['state_units'])==q+8
   assert len(e['registers'])==2 and all(type(v) is int and 0<=v<16 for v in e['memory']+e['registers'])
   assert 0<e['energy']<=224 and 0<=e['pc']<len(e['code'])//3 and e['feedback'] in (0,1,2) and e['pos']==0
   assert 0<=e['turns']<2048 and len(e['nursery'])%3==0 and len(e['nursery'])<=len(e['code'])
   units += [v[1] for v in e['code']]+e['state_units']+[w['unit'] for w in e['nursery']]
   if e['pending']:units+=e['pending']['units']
   if e['lease'] is not None:assert self.leases[e['lease']]==identity and e['lease'] in self.food
  assert sorted(units)==list(range(512)) and len(self.entities)<=self.max_population
  assert all(owner in self.entities and self.entities[owner]['lease']==p for p,owner in self.leases.items())
  assert len(self.food)<=64 and self.offered==self.admitted+self.rejected
  assert sum(e['energy'] for e in self.entities.values())+self.constructor_remaining+self.heat+20*len(self.food)==INITIAL_ENERGY+20*self.admitted
 def snapshot(self,events=True):return clone({k:v for k,v in self.__dict__.items() if events or k!='events'})
 def packet(self,e,reserve=False):
  if e['lease'] is not None:return e['lease']
  available=[p for p in sorted(self.food) if p not in self.leases and (not 16<=p<32 or self.tick>=64)]
  if not available:return None
  p=available[0]
  if reserve:e['lease']=p;self.leases[p]=e['id']
  return p
 def input(self):
  if self.tick%64:return []
  offers=[];span=8 if self.tick>=self.expansion_tick else 2
  for i in range(16):
   p=self.next_packet;self.next_packet+=1;self.offered+=1;cue=(i+self.tick//64)%span;ok=len(self.food)<64
   if ok:self.food[p]=cue;self.admitted+=1
   else:self.rejected+=1
   offers.append(dict(packet=p,cue=cue,energy=20,outcome='admitted' if ok else 'external_rejected'))
  return offers
 def debit(self,e,value):assert e['energy']>=value;e['energy']-=value;self.heat+=value
 def finish_copy(self,e,event,units,allele=None):
  if e['energy']<3:
   self.free=sorted(self.free+units);event['copy_refused']='word_energy';return False
  self.debit(e,3);records=[]
  for unit in units:
   index=len(e['nursery']);value,source_unit=e['code'][index];original=value
   if index==1 and allele is not None:value=allele
   w=dict(unit=unit,value=value,index=index,source_unit=source_unit,source_value=original,write_id=self.writes,mutated=int(value!=original))
   self.writes+=1;e['nursery'].append(w);records.append(clone(w))
  event['writes']=records;return True
 def copy(self,e,event,old_pc):
  if len(e['nursery'])==len(e['code']) or len(self.free)<3 or e['energy']<3:
   event['copy_refused']='full_or_material_or_energy';return
  units=self.free[:3];del self.free[:3]
  if not e['nursery']:
   e['copy_sessions']+=1;e['pending']=dict(stage='gate',draws=0,allele_draws=0,session=e['copy_sessions'],units=units)
   e['pc']=old_pc;event['sampler_started']=clone(e['pending'])
  else:self.finish_copy(e,event,units)
 def draw(self,e,event):
  pending=e['pending'];stage=pending['stage'];pending['draws']+=1
  key=[self.seed,'capacity-sampler',e['lineage'],pending['session'],stage,pending['draws']]
  raw=draw_value(key,stage)
  event['draw']=dict(stage=stage,value=raw,key=h(key),ordinal=pending['draws'])
  allele=None;abort=False
  if stage=='gate':
   if raw==0:pending['stage']='allele'
   else:allele=e['code'][1][0]
  else:
   pending['allele_draws']+=1
   if raw<3:allele=CAPACITIES[raw]
   elif pending['allele_draws']==8:abort=True
  if allele is not None or abort:
   event['sampler_finished']=dict(proposed=allele,abort=int(abort),draws=pending['draws'])
   if abort:self.free=sorted(self.free+pending['units'])
   else:self.finish_copy(e,event,pending['units'],e['code'][1][0] if self.mode=='no_variation' else allele)
   e['pending']=None;e['pc']=(e['pc']+1)%(len(e['code'])//3)
 def divide(self,e,event):
  if len(e['nursery'])!=len(e['code']) or len(self.entities)>=self.max_population:
   event['division_refused']='nursery_or_population';return
  q=e['nursery'][1]['value'];state=q+8
  if len(self.free)<state or e['energy']<state+STARTUP+2:
   event['division_refused']='material_or_energy';return
  units=self.free[:state];del self.free[:state];identity=self.next_id;self.next_id+=1
  e['children']+=1;child=self.body(identity,e['id'],e['generation']+1,[[w['value'],w['unit']] for w in e['nursery']],units,e['lineage']+[e['children']])
  e['energy']-=state+STARTUP+2;self.heat+=state+2;self.entities[identity]=child
  event['birth']=dict(child=clone(child),state_formation=units,state_energy=state,startup_energy=STARTUP,release_energy=2,parent_energy_after_division=e['energy'],write_ids=[w['write_id'] for w in e['nursery']])
  e['nursery']=[];self.births+=1
 def remove(self,e,event,cause):
  units=[v[1] for v in e['code']]+e['state_units']+[w['unit'] for w in e['nursery']]
  if e['pending']:units+=e['pending']['units']
  if e['lease'] is not None:del self.leases[e['lease']]
  self.heat+=e['energy'];self.free=sorted(self.free+units);del self.entities[e['id']];self.deaths+=1
  event['death']=dict(cause=cause,released=units,dissipated=e['energy'])
 def step(self):
  if not self.entities or self.tick>=16384:return False
  ids=sorted(self.entities);actor=next((i for i in ids if i>self.last),ids[0]);self.last=actor;e=self.entities[actor]
  self.tick+=1;e['turns']+=1;event=dict(tick=self.tick,actor=actor,before=h(e),energy_before=e['energy'],input=self.input())
  if self.tick==64:self.constructor_remaining-=16;self.heat+=16;event['release_energy']=16
  self.debit(e,1)
  if e['pending']:event['kind']='sampler_draw';self.draw(e,event)
  else:
   old=e['pc'];op,a,b=[v[0] for v in e['code'][3*old:3*old+3]];r=e['registers'];q=self.effective(e)
   event.update(kind='ordinary',decoded=[op,a,b]);e['pc']=(old+1)%(len(e['code'])//3)
   if op==0:
    p=self.packet(e,True);e['cue']=0 if p is None else self.food[p];r[a%2]=e['cue'];event['sense']=dict(packet=p,cue=e['cue'])
   elif op==1:r[a%2]=e['feedback'];event['read_feedback']=e['feedback']
   elif op==2:r[a%2]=e['memory'][b%q]
   elif op==3:e['memory'][a%q]=r[b%2]
   elif op==4:r[a%2]=b%16
   elif op==5:r[a%2]^=r[b%2]
   elif op==6:
    p=self.packet(e);e['feedback']=2;event['penalty']=0
    if p is not None:
     cue=self.food.pop(p);target=(MASKS[SOFTWARE.index(self.seed)]>>cue)&1;port=r[a%2]%2;e['feedback']=int(port==target)
     if p in self.leases:del self.leases[p];e['lease']=None
     event['attempt']=dict(packet=p,cue=cue,target=target,port=port,success=e['feedback'])
     if e['feedback']:
      gain=min(20,224-e['energy']);e['energy']+=gain;self.heat+=20-gain;event['captured']=gain
     else:
      self.heat+=20;penalty=min(4,e['energy']);self.debit(e,penalty);event['penalty']=penalty
    event['feedback']=e['feedback']
   elif op==7:e['pc']=b%(len(e['code'])//3)
   elif op==8:
    if r[a%2]==0:e['pc']=b%(len(e['code'])//3)
   elif op==10:self.copy(e,event,old)
   elif op==12:self.divide(e,event)
   elif op==19:r[a%2]=e['memory'][r[b%2]%q]
   elif op==20:e['memory'][r[a%2]%q]=r[b%2]
   elif op==21:r[a%2]^=15
   elif op in (22,23,24,25):
    before=dict(memory=e['memory'],registers=e['registers'],pc=old,energy=e['energy']+1)
    after,paid=packed_transition(before,[op,a,b],len(e['code'])//3)
    self.debit(e,paid['logic_fee'])
    e['memory']=after['memory'];e['registers']=after['registers'];e['pc']=after['pc']
    event['packed']=paid;event['logic_fee']=paid['logic_fee']
  if not e['energy'] or e['turns']==2048:self.remove(e,event,'energy' if not e['energy'] else 'installed_age_law')
  else:event['after']=clone(e)
  self.check();event['state_hash']=h(self.snapshot(False));self.events.append(event);return True
 def run(self,*args):raise RuntimeError('Separate registered bounded custody required')
