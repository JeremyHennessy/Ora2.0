"""REDOX-01 installed abstract chemistry; no organism, policy or reward."""
import argparse
import copy
import hashlib
import json
from pathlib import Path
import random
import zipfile
from .evidence_budget import Budget
from .evidence_budget_audit import audit as storage_audit

ARMS=('candidate','inert','background','mixed','withdrawal','supplied')
LIMITS={'raw':64*1024**2,'archive':16*1024**2,'restore':64*1024**2,'failure':1024**2}
TOTAL=128*1024**2

def encoded(value):return json.dumps(value,sort_keys=True,separators=(',',':')).encode()
def digest(value):return hashlib.sha256(encoded(value)).hexdigest()
def compatible(k,j):return hashlib.sha256(f'REDOX-01|{k}|{j}'.encode('ascii')).digest()[0]%4==0
def distance(a,b):
    x,y=abs(a%8-b%8),abs(a//8-b//8)
    return min(x,8-x)+min(y,8-y)

class World:
    def __init__(self,seed,arm):
        if arm not in ARMS:raise ValueError('Unregistered arm')
        self.rng=random.Random(seed);self.births=[]
        positions=[self.rng.randrange(64) for _ in range(48)]
        supplied=[self.rng.randrange(16) for _ in range(12)]
        self.state=dict(arm=arm,slots=[],photons=[16]*64,thermal=256,operator=16,heat=0,
                        exported=0,next_id=0,birth_head='0'*64,lost={},endpoint=[],exact=[],damage_snapshot=None,
                        stats={k:0 for k in ('capture','formation','catalysis','decay','motion',
                                            'damage','functional_damage','genesis','genesis_refused',
                                            'post_formation','post_catalysis','pre_functional')},zeros={})
        for i,cell in enumerate(positions):
            self.state['slots'].append(self.birth(i,cell,None,0,False,[],[],False))
        if arm=='supplied':
            for i,kind in enumerate(supplied):
                p=self.state['slots'][i];cell=p['cell']
                if self.state['photons'][cell]<2 or self.state['operator']<1:
                    self.state['stats']['genesis_refused']+=1;continue
                photons=self.take(cell,-1);self.state['operator']-=1;self.state['heat']+=2
                self.state['slots'][i]=self.birth(i,cell,kind,1,True,photons,[p['uid']],False)
                self.state['stats']['genesis']+=1
        self.initial_rng=self.rng.getstate()
        self.check()

    def birth(self,slot,cell,kind,q,assisted,photons,parents,repair):
        s=self.state;uid=s['next_id'];s['next_id']+=1
        record=dict(uid=uid,slot=slot,atoms=[2*slot,2*slot+1],kind=kind,
                    assisted=assisted,photons=copy.deepcopy(photons),parents=list(parents))
        self.births.append(record);s['birth_head']=digest([s['birth_head'],record])
        return dict(uid=uid,slot=slot,cell=cell,kind=kind,q=q,assisted=assisted,
                    photons=copy.deepcopy(photons),used=0,repair=repair)

    def take(self,cell,t):
        n=self.state['photons'][cell];self.state['photons'][cell]-=2
        return [[cell*16+n-1,t],[cell*16+n-2,t]]

    def draws(self):
        r=self.rng
        return [r.randrange(4),r.randrange(48),r.getrandbits(64),r.randrange(16),
                r.randrange(256),r.randrange(4),r.randrange(64),r.getrandbits(64)]

    def advance(self,t,d):
        s=self.state;events=[]
        if t==2048:
            s['stats']['pre_functional']=sum(not p['assisted'] and bool(p['used']) for p in s['slots'] if p['kind'] is not None)
            if s['arm']=='withdrawal':
                s['exported']+=sum(s['photons']);s['photons']=[0]*64
                events.append(['withdraw',s['exported']])
            for i,p in enumerate(s['slots']):
                if p['kind'] is not None and p['cell']%8<4:
                    if not p['assisted'] and p['used']:
                        s['lost'][str(i)]=dict(uid=p['uid'],kind=p['kind'])
                        s['stats']['functional_damage']+=1
                    s['heat']+=1;s['stats']['damage']+=1
                    s['slots'][i]=self.birth(i,p['cell'],None,0,p['assisted'],[],[p['uid']],False)
                    events.append(['damage',p['uid'],s['slots'][i]['uid']])
            s['damage_snapshot']=[sum(s['photons']),sum(p['q'] for p in s['slots']),s['thermal']]
        action,i,token,j,byte,direction,dest,noise=d;p=s['slots'][i];cell=p['cell']
        result=['refuse',action,p['uid']]
        if action==0 and p['kind'] is None and p['q']==0 and s['photons'][cell]>=2:
            p['photons']=self.take(cell,t);p['q']=2;s['stats']['capture']+=1
            result=['capture',p['uid'],copy.deepcopy(p['photons'])]
        elif action==1 and p['kind'] is None and p['q']==2:
            neighbors=[x for x in s['slots'] if x['slot']!=i and distance(cell,x['cell'])<=1]
            contact=neighbors[token%len(neighbors)] if neighbors else None
            basal=19 if s['arm']=='background' else 4
            possible=(s['arm']!='inert' and contact is not None and contact['kind'] is not None
                      and compatible(contact['kind'],j))
            if byte<(64 if possible else basal):
                causal=possible and byte>=basal
                assisted=p['assisted'] or bool(causal and contact['assisted'])
                parents=[p['uid']]+([contact['uid']] if causal else [])
                repair=(str(i) in s['lost'] and causal and not assisted
                        and all(entry[1]>=2048 for entry in p['photons']))
                new=self.birth(i,cell,j,1,assisted,p['photons'],parents,repair)
                s['slots'][i]=new;s['heat']+=1;s['stats']['formation']+=1
                if t>=2048:s['stats']['post_formation']+=1
                if causal:
                    contact['used']+=1;s['stats']['catalysis']+=1
                    if t>=2048:s['stats']['post_catalysis']+=1
                    if contact['repair'] and contact['uid'] not in s['endpoint']:
                        s['endpoint'].append(contact['uid'])
                        if contact['kind']==s['lost'][str(contact['slot'])]['kind']:
                            s['exact'].append(contact['uid'])
                result=['form',p['uid'],new['uid'],contact['uid'] if causal else None]
        elif action==2:
            cost=2 if s['arm']=='mixed' else 1
            if s['thermal']>=cost:
                s['thermal']-=cost;s['heat']+=cost;s['stats']['motion']+=1
                x,y=cell%8,cell//8;dx,dy=((1,0),(-1,0),(0,1),(0,-1))[direction]
                p['cell']=dest if s['arm']=='mixed' else ((y+dy)%8)*8+(x+dx)%8
                result=['move',p['uid'],cell,p['cell'],cost]
        elif action==3 and p['kind'] is not None and byte<16:
            s['heat']+=1;s['stats']['decay']+=1
            new=self.birth(i,cell,None,0,p['assisted'],[],[p['uid']],False)
            s['slots'][i]=new;result=['decay',p['uid'],new['uid']]
        events.append(result)
        for key,value in [('photons',sum(s['photons'])),('thermal',s['thermal']),
                          ('buffer',sum(x['q'] for x in s['slots']))]:
            if value==0:s['zeros'].setdefault(key,t)
        self.check()
        return events

    def check(self):
        s=self.state
        if sum(s['photons'])+s['thermal']+s['operator']+s['heat']+s['exported']+sum(p['q'] for p in s['slots'])!=1296:
            raise ValueError('Energy conservation')
        if any(v<0 for v in s['photons']) or min(s['thermal'],s['operator'],s['heat'])<0:
            raise ValueError('Negative stock')
        if len({p['uid'] for p in s['slots']})!=48 or [p['slot'] for p in s['slots']]!=list(range(48)):
            raise ValueError('Material/identity violation')

    def record(self,seed):
        s=self.state
        return dict(seed=seed,arm=s['arm'],endpoint=bool(s['endpoint']),exact=bool(s['exact']),
                    exposed=bool(s['lost']),stats=copy.deepcopy(s['stats']),zeros=s['zeros'],
                    photons=sum(s['photons']),buffer=sum(p['q'] for p in s['slots']),
                    thermal=s['thermal'],operator=s['operator'],heat=s['heat'],exported=s['exported'],
                    final_hash=digest(s),births=len(self.births),damage_snapshot=s['damage_snapshot'])

def run_batch(root,start,revision):
    if start not in range(63000,63032,4):raise ValueError('Frozen four-seed batch')
    budget=Budget(root,LIMITS,TOTAL);records=[]
    for seed in range(start,start+4):
        for arm in ARMS:
            w=World(seed,arm)
            with budget.create('raw',f'{seed}-{arm}.jsonl') as out:
                out.write(encoded(dict(initial=w.state,initial_rng=w.initial_rng,seed=seed,
                                       arm=arm,source_revision=revision)) + b'\n')
                for t in range(4096):
                    d=w.draws();events=w.advance(t,d)
                    out.write(encoded(dict(t=t,draws=d,events=events,state_hash=digest(w.state)))+b'\n')
                out.write(encoded(dict(final=w.state,rng=w.rng.getstate(),draw_calls=60+4096*8,
                                       births=w.births,record=w.record(seed)))+b'\n')
            records.append(w.record(seed))
    with budget.create('raw','records.json') as out:out.write(encoded(records))
    raw=sorted((Path(root)/'raw').glob('*'))
    with budget.create('archive','raw.zip') as out:
        with zipfile.ZipFile(out,'w',zipfile.ZIP_DEFLATED) as z:
            for p in raw:z.write(p,p.name)
    with zipfile.ZipFile(Path(root)/'archive/raw.zip') as z:
        if z.testzip():raise ValueError('Archive corruption')
        for entry in z.infolist():
            with budget.create('restore',entry.filename,entry.file_size) as out:
                with z.open(entry) as incoming:
                    while chunk:=incoming.read(1024**2):out.write(chunk)
    for p in raw:
        if p.read_bytes()!=(Path(root)/'restore'/p.name).read_bytes():raise ValueError('Restored bytes differ')
    with budget.create('failure','budget.json',65536) as out:
        receipt=copy.deepcopy(budget.snapshot());out.write(encoded(receipt))
    storage_audit(root,receipt,LIMITS,TOTAL)
    return records

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--output',required=True);p.add_argument('--start',type=int,required=True)
    p.add_argument('--revision',required=True);a=p.parse_args()
    print(json.dumps(run_batch(a.output,a.start,a.revision)))
