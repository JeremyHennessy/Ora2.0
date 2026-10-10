"""Finite reversible fuel-mediated assembly toy; installed possibility, not life."""
import argparse, hashlib, json, math, random, struct
from collections import deque
from fractions import Fraction

ARMS = ('candidate', 'independent', 'shuffled')
POTENTIAL = (0, 1, 4, 3)
CHEMICAL = ('assemble', 'drive', 'waste')
ALPHABET = [(k,j,d) for j in range(10) for k in CHEMICAL for d in (-1,1)] + [(k,0,d) for k in ('passive','relax','load') for d in (-1,1)] + [('hop',j,1) for j in range(2)]
def pack(x): return json.dumps(x,sort_keys=True,separators=(',',':')).encode()
def heat(s): return 68-6*s[0]-POTENTIAL[s[1]]-s[3]

def transition(s,action,arm):
    f,q,p,w=s; k,j,d=action; n=16
    if k=='assemble':
        if q!=(0 if d==1 else 1) or p not in (0,3): return None
        t=(f-d,1 if d==1 else 0,p,w); n={'candidate':32,'independent':17,'shuffled':2}[arm]
    elif k=='drive':
        if q!=(1 if d==1 else 2): return None
        t=(f-d,2 if d==1 else 1,p,w)
    elif k=='waste':
        t=(f-d,q,p,w); n={'candidate':2,'independent':17,'shuffled':32}[arm]
    elif k in ('passive','relax','load'):
        lo,hi={'passive':(0,1),'relax':(2,3),'load':(3,1)}[k]
        if q!=(lo if d==1 else hi) or k=='passive' and p not in (0,3): return None
        t=(f,hi if d==1 else lo,p,w+(2*d if k=='load' else 0))
    elif k=='hop': t=(f,q,p^(3 if q else 1<<j),w)
    else: raise ValueError('Unknown reaction')
    if min(t[0],10-t[0],t[3],heat(t))<0:return None
    return t,Fraction(n,64*2**max(0,heat(s)-heat(t)))

def physical(arm):
    seen={(10,0,p,0) for p in range(4)};todo=deque(sorted(seen));edges=0
    alphabet=[(k,0,d) for k in CHEMICAL for d in (-1,1)]+ALPHABET[60:]
    while todo:
        s=todo.popleft()
        for a in alphabet:
            result=transition(s,a,arm)
            if result is None:continue
            t,r=result;k,j,d=a;u,back=transition(t,(k,j,1 if k=='hop' else -d),arm);assert u==s
            cf=(s[0] if d==1 else 10-s[0]) if k in CHEMICAL else 1
            cb=(t[0] if d==-1 else 10-t[0]) if k in CHEMICAL else 1
            assert math.comb(10,s[0])*2**heat(s)*r*cf==math.comb(10,t[0])*2**heat(t)*back*cb
            edges+=1
            if t not in seen:seen.add(t);todo.append(t)
            if len(seen)>250000 or edges>4000000:raise ValueError('Physical graph cap')
    return dict(arm=arm,states=len(seen),edges=edges,state_sha256=hashlib.sha256(pack(sorted(seen))).hexdigest(),protected_heat_work_ceiling=max(s[3] for s in seen if heat(s)>=8))

def score(events,final,loss,rebuilt,current):
    cost=postcost=output=postoutput=0;pre=fresh=False;before=None;beforeheat=None
    for e in events:
        k,j,d=e['action'];bill=(6*d if k=='assemble' else d if k=='passive' else 1 if k=='damage' else 0)
        cost+=bill
        if loss is not None and e['step']>=2048:postcost+=bill
        if k=='load' and (e['origin']=='fresh-fuel' or d==-1):
            output+=2*d
            if e['step']<2048 and d==1:pre=True
            if loss is not None and e['step']>=2048:
                postoutput+=2*d
                if d==1 and e['dimer']==rebuilt:fresh=True
        if k=='damage':before=e['before'][3];beforeheat=heat(e['before'])
    w=final[3];post=None if before is None else w-before;exposed=loss is not None and pre
    endpoint=exposed and rebuilt is not None and rebuilt==current and fresh and w>0 and post>0 and output-cost>0 and postoutput-postcost>0 and heat(final)>=8 and heat(final)>=beforeheat
    return dict(endpoint=bool(endpoint),functioning_loss=exposed,whole_work_surplus=w,post_work_surplus=post,fresh_net_output=output,post_fresh_net_output=postoutput,all_net_formation_damage_cost=cost,post_net_cost=postcost,functional_surplus=output-cost,post_functional_surplus=postoutput-postcost,initial_heat_preserved=heat(final)>=8,post_heat_preserved=beforeheat is not None and heat(final)>=beforeheat)

def trajectory(seed,arm,witness=False):
    rng=random.Random(seed);p=0 if witness else rng.getrandbits(1)+2*rng.getrandbits(1)
    s=(10,0,p,0);tokens=[0]*10;virgin=[True]*10;charge=None
    states=[list(s)+[heat(s)]];events=[];digest=hashlib.sha256()
    objects=[dict(id=j,atom=j,parent=None,state='raw') for j in range(2)];owners=[0,1];dimers=[]
    current=last=rebuilt=loss=None;fresh=other=occupancy=0
    def apply(action,step):
        nonlocal s,charge,current,last,rebuilt,loss,fresh,other
        k,j,d=action;e=dict(step=step,action=list(action),before=list(s),dimer=current,origin=None)
        if k=='damage':s=(s[0],0,s[2],s[3]-1);loss=step
        else:s,r=transition(s,action,arm);e['rate']=[r.numerator,r.denominator]
        if k in CHEMICAL:
            tokens[j]=1 if d==1 else 0
            if k=='drive':charge=('fresh-fuel' if virgin[j] else 'regenerated-fuel') if d==1 else None
            virgin[j]=False
        if k=='load':
            e['origin']=charge if d==1 else 'paid-work-reversal'
            if d==1:
                fresh+=2*int(charge=='fresh-fuel');other+=2*int(charge!='fresh-fuel');charge=None
            else:charge='paid-work-reversal'
        if k in ('assemble','passive','damage'):
            parent=current;created=[]
            for atom in range(2):
                old=owners[atom];owners[atom]=len(objects);created.append(owners[atom]);objects.append(dict(id=owners[atom],atom=atom,parent=old,state='bound' if s[1] else 'raw'))
            e['objects']=created
            if s[1]:
                current=len(dimers);dimers.append(dict(id=current,parent=last,components=owners.copy()));last=current
                if loss is not None and rebuilt is None:rebuilt=current
            else:current=None
            e['new_dimer']=current;charge=None
        assert s[0]==tokens.count(0)
        e['after']=list(s);events.append(e);states.append(list(s)+[heat(s)])
    if witness:
        todo=[('assemble',0,1)]+[a for j in (1,2,3) for a in [('drive',j,1),('relax',0,1),('load',0,1)]]
        for n,a in enumerate(todo):apply(a,n)
        apply(('damage',0,1),2048);apply(('assemble',4,1),2048)
        for j in range(5,10):
            for a in [('drive',j,1),('relax',0,1),('load',0,1)]:apply(a,2049+len(events))
    else:
        for step in range(4096):
            if step==2048 and s[1] and s[3]>=1:apply(('damage',0,1),step)
            idx=rng.randrange(68);draw=rng.getrandbits(32);noise=rng.getrandbits(32);digest.update(struct.pack('<III',idx,draw,noise));a=ALPHABET[idx];k,j,d=a
            allowed=k not in CHEMICAL or tokens[j]==int(d==-1)
            r=transition(s,a,arm) if allowed else None
            if r is not None and draw*r[1].denominator<2**32*r[1].numerator:apply(a,step)
            occupancy+=int(s[1]!=0)
    result=dict(seed=seed,arm=arm,witness=witness,states=states,events=events,objects=objects,owners=owners,dimers=dimers,current_dimer=current,first_rebuilt=rebuilt,damage_step=loss,token_states=tokens,virgin_tokens=virgin,charge_origin=charge,fresh_gross_work=fresh,other_gross_work=other,bound_occupancy=occupancy,draw_sha256=digest.hexdigest(),rng_sha256=hashlib.sha256(pack(rng.getstate())).hexdigest())
    result['score']=score(events,s,loss,rebuilt,current);return result

def main():
    p=argparse.ArgumentParser();p.add_argument('--revision',required=True);p.add_argument('--mode',choices=('gate','panel'),required=True);p.add_argument('--output-file');a=p.parse_args()
    records=[trajectory(0,x,True) for x in ARMS] if a.mode=='gate' else [trajectory(s,x) for s in range(85000,85032) for x in ARMS]
    out=dict(schema='assemble01',source_revision=a.revision,mode=a.mode,records=records)
    if a.mode=='gate':out['graphs']=[physical(x) for x in ARMS]
    body=json.dumps(out,sort_keys=True).encode()
    if a.output_file:
        if len(body)>20*1024**2:raise ValueError('Prospective output cap')
        with open(a.output_file,'r+b') as f:
            if f.read(1):raise ValueError('Requires externally reserved empty file')
            f.write(body)
        print(json.dumps(dict(records=len(records),bytes=len(body))))
    else:print(body.decode())
if __name__=='__main__':main()
