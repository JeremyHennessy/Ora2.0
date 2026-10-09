"""FUEL-01 finite mass-bearing fuel chemistry; prospective unscreened panel."""
import argparse, copy, json
from pathlib import Path

ARMS=('candidate','inert','shuffled','fuel-withdrawn')
def encode(x):return json.dumps(x,sort_keys=True,separators=(',',':')).encode()
def initial(seed,arm):
    if seed not in (*range(76000,76032),76999) or arm not in ARMS:raise ValueError('Unregistered sample')
    return dict(seed=seed,arm=arm,rng=seed,step=0,heat=0,food=[0]*96,
        objects=[dict(id=i,atoms=[i],active=False,fuel=None,alive=True,parents=[],born=0,route='genesis') for i in range(24)],
        stats=dict(activation=0,formation=0,cleavage=0,causal=0,reused=0,post_withdrawal=0),depleted_at=None)
def check(w):
    live=[o for o in w['objects'] if o['alive']]
    if sorted(a for o in live for a in o['atoms'])!=list(range(24)):raise ValueError('Substrate ownership')
    if len(w['food'])!=96 or any(x not in (0,1,2) for x in w['food']):raise ValueError('Fuel ownership')
    bound=sum(2*o['active']+len(o['atoms'])-1 for o in live)
    if 4*sum(x!=1 for x in w['food'])+bound+w['heat']!=384 or w['heat']<0:raise ValueError('Energy')
    for i,o in enumerate(w['objects']):
        if o['id']!=i or len(o['atoms']) not in (1,2) or any(p<0 or p>=i for p in o['parents']):raise ValueError('Identity/ancestry')
        if o['active'] and len(o['atoms'])!=1:raise ValueError('Activation site')
        if o['fuel'] is not None and (not 0<=o['fuel']<96 or w['food'][o['fuel']]!=1):raise ValueError('Energy provenance')
def append(w,atoms,parents,t,route,fuel=None):
    w['objects'].append(dict(id=len(w['objects']),atoms=atoms,active=False,fuel=fuel,alive=True,parents=parents,born=t,route=route))
def advance(w,t,d):
    if t==2048 and w['arm']=='fuel-withdrawn':w['food']=[2 if f==0 else f for f in w['food']]
    live=[o for o in w['objects'] if o['alive']]
    x,y,z=[live[d[i]%len(live)] for i in (1,2,3)];f=d[4]%96;chance=d[5]&255;op=d[0]%3;event=None
    if op==0 and len(x['atoms'])==1 and not x['active'] and w['food'][f]==0:
        signature=(sum(a%4 for a in z['atoms'])+(w['arm']=='shuffled'))%4
        cat=w['arm']!='inert' and len(z['atoms'])==2 and signature==x['atoms'][0]%4
        if chance<(128 if cat else 16):
            w['food'][f]=1;x['active']=True;x['fuel']=f;w['heat']+=2;w['stats']['activation']+=1
            w['stats']['causal']+=int(cat and chance>=16);event=['activate',x['id'],f,z['id'] if cat else None]
    elif op==1 and x['id']!=y['id'] and len(x['atoms'])==len(y['atoms'])==1 and x['active'] and not y['active']:
        x['alive']=y['alive']=False;append(w,sorted(x['atoms']+y['atoms']),[x['id'],y['id']],t,'form',x['fuel'])
        w['heat']+=1;w['stats']['formation']+=1;w['stats']['reused']+=int(x['route']=='cleave' or y['route']=='cleave')
        w['stats']['post_withdrawal']+=int(t>=2048 and w['arm']=='fuel-withdrawn');event=['form',x['id'],y['id'],len(w['objects'])-1]
    elif op==2 and len(x['atoms'])==2 and chance<8:
        x['alive']=False
        for a in x['atoms']:append(w,[a],[x['id']],t,'cleave')
        w['heat']+=1;w['stats']['cleavage']+=1;event=['cleave',x['id'],len(w['objects'])-2,len(w['objects'])-1]
    w['step']=t+1
    if w['depleted_at'] is None and not any(f==0 for f in w['food']):w['depleted_at']=t
    check(w);return event
def numbers(w):
    result=[]
    for _ in range(6):
        x=w['rng'];x^=(x<<13)&0xffffffff;x^=x>>17;x^=(x<<5)&0xffffffff;w['rng']=x&0xffffffff;result.append(w['rng'])
    return result
def world(seed,arm):
    w=initial(seed,arm);trace=[]
    for t in range(4096):
        d=numbers(w);trace.append([d,advance(w,t,d)])
    live=sum(o['alive'] and len(o['atoms'])==2 for o in w['objects'])
    return dict(seed=seed,arm=arm,trace=trace,final=w,live_dimers=live,opportunity=live>=3 and w['stats']['formation']>=8 and w['stats']['activation']>=8,cursor=24576)
def main():
    from experiments.evidence_budget import Budget
    import copy
    p=argparse.ArgumentParser();p.add_argument('--output',required=True);p.add_argument('--revision',required=True);args=p.parse_args()
    b=Budget(Path(args.output),dict(raw=128*1024**2,failure=2*1024**2),130*1024**2)
    try:
        with b.create('raw','manifest.json') as f:f.write(encode(dict(revision=args.revision,seeds=list(range(76000,76032)),arms=ARMS,worlds=128,attempts=524288)))
        for seed in range(76000,76032):
            for arm in ARMS:
                with b.create('raw',f'{seed}-{arm}.json') as f:f.write(encode(world(seed,arm)))
            print(seed,flush=True)
    finally:
        with b.create('failure','budget.json',1024**2) as f:f.write(encode(copy.deepcopy(b.snapshot())))
if __name__=='__main__':main()
