"""Finite paid spatial law; all functions installed, no life claim."""
import argparse, hashlib, json, math, random, struct
from collections import deque
from fractions import Fraction

ARMS=('candidate','independent','shuffled')
ALPHABET=[(k,i,d) for i in range(10) for k in ('capture','decay','work') for d in (-1,1)]+[('activate',i,d) for i in range(2) for d in (-1,1)]+[('bond',0,d) for d in (-1,1)]+[('hop',i,1) for i in range(2)]
def pack(x):return json.dumps(x,sort_keys=True,separators=(',',':')).encode()
def heat(s):
    f,i,a,b,p,w=s
    return 68-6*f-4*i-2*a.bit_count()+b-w
def weight(s):return math.comb(10,s[0])*math.comb(10-s[0],s[1])*2**heat(s)

def transition(s,action,arm):
    f,i,a,b,p,w=s;k,slot,d=action
    if k=='capture':
        if (f if d==1 else i)==0:return None
        t=(f-d,i+d,a,b,p,w);n=4
    elif k in ('decay','work'):
        if (i if d==1 else 10-f-i)==0:return None
        t=(f,i-d,a,b,p,w+(2*d if k=='work' else 0))
        n=4 if k=='decay' else {'candidate':(2,32),'independent':(17,17),'shuffled':(32,2)}[arm][b]
    elif k=='activate':
        if b or bool(a>>slot&1)!=(d==-1):return None
        t=(f,i,a^(1<<slot),b,p,w-3*d);n=16
    elif k=='bond':
        if bool(b)!=(d==-1) or d==1 and (a!=3 or p not in (0,3)):return None
        t=(f,i,a,1-b,p,w);n=16
    else:
        bits=3 if b else 1<<slot
        t=(f,i,a,b,p^bits,w);n=16
    if min(t[0],t[1],10-t[0]-t[1],t[5],heat(t))<0:return None
    probability=Fraction(n,64*2**max(0,heat(s)-heat(t)))
    return t,probability

def graph(arm):
    todo=deque((10,0,0,0,p,0) for p in range(4));seen=set(todo);edges=0;signatures=set()
    alphabet=[(k,0,d) for k in ('capture','decay','work') for d in (-1,1)]+ALPHABET[60:]
    while todo:
        s=todo.popleft()
        for action in alphabet:
            r=transition(s,action,arm)
            if r is None:continue
            t,rate=r;k,slot,d=action
            reverse=(k,slot,1 if k=='hop' else -d)
            u,back=transition(t,reverse,arm);assert u==s
            count=lambda x,z: (x[0] if z==('capture',1) else x[1] if z in (('capture',-1),('decay',1),('work',1)) else 10-x[0]-x[1]) if k in ('capture','decay','work') else 10
            # Aggregate chemical selection chooses a labelled token uniformly.
            cf=count(s,(k,d));cb=count(t,(k,-d))
            sig=(s[0],s[1],t[0],t[1],heat(t)-heat(s),rate,back,cf,cb)
            if sig not in signatures:
                assert weight(s)*rate*cf==weight(t)*back*cb
                signatures.add(sig)
            edges+=1
            if t not in seen:seen.add(t);todo.append(t)
            if len(seen)>250000 or edges>4000000:raise ValueError('Graph bound')
    return dict(arm=arm,states=len(seen),edges=edges,state_sha256=hashlib.sha256(pack(sorted(seen))).hexdigest(),rate_signatures=len(signatures),protected_heat_work_ceiling=max(s[5] for s in seen if heat(s)>=8))

def score(events,states,damage,rebuilt,current):
    cost=postcost=bound=postbound=0;before=None;pre=False;fresh=False
    for e in events:
        k,slot,d=e['action']
        bill=3*d if k=='activate' else 1 if k=='damage' else 0
        cost+=bill
        if damage is not None and e['step']>=2048:postcost+=bill
        if k=='work' and e['bond'] is not None and (e['origin']=='fresh-fuel' or d==-1):
            bound+=2*d
            if e['step']<2048 and d==1:pre=True
            if damage is not None and e['step']>=2048:
                postbound+=2*d
                if d==1 and e['bond']==rebuilt:fresh=True
        if k=='damage':before=e['before'][5]
    whole=states[-1][5];post=None if before is None else whole-before
    functioning_loss=damage is not None and pre
    surplus=bound-cost;postsurplus=postbound-postcost
    endpoint=functioning_loss and rebuilt is not None and current==rebuilt and fresh and whole>0 and post>0 and surplus>0 and postsurplus>0 and states[-1][-1]>=8
    return dict(endpoint=bool(endpoint),functioning_loss=functioning_loss,whole_work_surplus=whole,post_work_surplus=post,bond_fresh_net_work=bound,post_bond_fresh_net_work=postbound,all_paid_net_cost=cost,post_paid_net_cost=postcost,functional_surplus=surplus,post_functional_surplus=postsurplus)

def trajectory(seed,arm,witness=False):
    rng=random.Random(seed);p=0 if witness else rng.getrandbits(1)+2*rng.getrandbits(1)
    s=(10,0,0,0,p,0);tokens=[0]*10;origin=[None]*10;virgin=[True]*10
    states=[list(s)+[heat(s)]];events=[];digest=hashlib.sha256()
    objects=[dict(id=j,atom=j,parent=None,state='raw') for j in range(2)];owners=[0,1]
    bonds=[];current=last=rebuilt=damage=None;occupancy=thermal=fresh=0
    def apply(action,step):
        nonlocal s,current,last,rebuilt,damage,thermal,fresh
        k,j,d=action;before=s;event=dict(step=step,action=list(action),before=list(s),bond=current,origin=None)
        if k=='damage':
            s=(s[0],s[1],s[2]&~1,0,s[4],s[5]-1);damage=step;current=None
        else:s,rate=transition(s,action,arm);event['rate']=[rate.numerator,rate.denominator]
        if k in ('capture','decay','work'):
            old=tokens[j];new={('capture',1):1,('capture',-1):0,('decay',1):2,('decay',-1):1,('work',1):2,('work',-1):1}[(k,d)];tokens[j]=new
            if new==1:
                origin[j]=('fresh-fuel' if virgin[j] else 'thermal-reactivation') if k=='capture' else 'thermal-reactivation' if k=='decay' else 'paid-work-reactivation'
                if k=='capture':virgin[j]=False
            if k=='work':
                event['origin']=origin[j] if d==1 else 'paid-work-reactivation'
                if d==1:
                    fresh+=2 if origin[j]=='fresh-fuel' else 0;thermal+=2 if origin[j]=='thermal-reactivation' else 0
            if new!=1:origin[j]=None
        if k in ('activate','damage'):
            old=owners[j];owners[j]=len(objects);objects.append(dict(id=owners[j],atom=j,parent=old,state='active' if k=='activate' and d==1 else 'raw'));event['object']=owners[j];event['parent']=old
        if k=='bond':
            if d==1:
                current=len(bonds);bonds.append(dict(id=current,parent=last,components=owners.copy()));last=current
                if damage is not None and rebuilt is None:rebuilt=current
            else:current=None
            event['new_bond']=current
        assert s[0]==tokens.count(0) and s[1]==tokens.count(1)
        event['after']=list(s);events.append(event);states.append(list(s)+[heat(s)])
    if witness:
        # Authored feasibility, never sampled evidence; each primitive remains paid.
        todo=[]
        for j in range(3):todo += [('capture',j,1),('work',j,1)]
        todo += [('activate',0,1),('activate',1,1),('bond',0,1),('capture',3,1),('work',3,1)]
        for n,a in enumerate(todo):apply(a,n)
        apply(('damage',0,1),2048)
        for a in [('capture',4,1),('work',4,1),('activate',0,1),('bond',0,1)]+[a for j in range(5,10) for a in [('capture',j,1),('work',j,1)]]:apply(a,2049+len(events))
    else:
        for step in range(4096):
            if step==2048 and s[3] and s[5]>=1:apply(('damage',0,1),step)
            idx=rng.randrange(68);draw=rng.getrandbits(32);noise=rng.getrandbits(32);digest.update(struct.pack('<III',idx,draw,noise))
            a=ALPHABET[idx];k,j,d=a
            allowed=k not in ('capture','decay','work') or tokens[j]==({'capture':(1,0),'decay':(2,1),'work':(2,1)}[k][d==1])
            r=transition(s,a,arm) if allowed else None
            if r is not None and draw*r[1].denominator<2**32*r[1].numerator:apply(a,step)
            occupancy+=s[3]
    result=dict(seed=seed,arm=arm,witness=witness,states=states,events=events,objects=objects,owners=owners,bonds=bonds,current_bond=current,first_rebuilt=rebuilt,damage_step=damage,token_states=tokens,token_origin=origin,virgin_tokens=virgin,fresh_gross_work=fresh,thermal_gross_work=thermal,bound_occupancy=occupancy,draw_sha256=digest.hexdigest(),rng_sha256=hashlib.sha256(pack(rng.getstate())).hexdigest())
    result['score']=score(events,states,damage,rebuilt,current);return result

def main():
    p=argparse.ArgumentParser();p.add_argument('--revision',required=True);p.add_argument('--mode',choices=('gate','panel'),required=True);p.add_argument('--output-file');a=p.parse_args()
    records=[trajectory(0,x,True) for x in ARMS] if a.mode=='gate' else [trajectory(s,x) for s in range(84000,84032) for x in ARMS]
    out=dict(schema='local01',source_revision=a.revision,mode=a.mode,records=records)
    if a.mode=='gate':out['graphs']=[graph(x) for x in ARMS]
    body=json.dumps(out,sort_keys=True).encode()
    if a.output_file:
        if len(body)>20*1024**2:raise ValueError('Prospective output size cap')
        with open(a.output_file,'r+b') as f:
            if f.read(1):raise ValueError('Requires empty externally reserved evidence file')
            f.write(body)
        print(json.dumps(dict(records=len(records),bytes=len(body))))
    else:print(body.decode())
if __name__=='__main__':main()
