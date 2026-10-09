"""Finite COFACTOR-01 chemistry; no supplied active founder."""
import argparse,copy,json
from pathlib import Path
ARMS=('candidate','catalyst-ghost','annealed','recycle-ghost','food-withdrawn','sham')
PAIRS=[(a,b) for a in range(4) for b in range(a,4)]
def pack(x):return json.dumps(x,sort_keys=True,separators=(',',':')).encode()
def rand(x):
    x^=(x<<13)&0xffffffff;x^=x>>17;x^=(x<<5)&0xffffffff;return x&0xffffffff
def catalogue(seed):
    x=seed^0x9e3779b9;rows=[]
    for a,b in PAIRS:
        row=[]
        for t in range(4):x=rand(x);row.append(int((x&255)<64))
        rows.append(row)
    return rows
def obj(i,atom,kind,t=0,species=None,parents=None,fuel=None,cofactors=None):
    return dict(id=i,atom=atom,kind=kind,species=species,born=t,parents=parents or [],fuel=fuel,cofactors=cofactors or [],alive=True)
def new(seed,arm):
    if seed not in (*range(77000,77032),77999) or arm not in ARMS:raise ValueError('Sample')
    return dict(seed=seed,arm=arm,rng=seed,step=0,work=288,heat=0,catalogue=catalogue(seed),objects=[obj(i,i,'F' if i<120 else 'W') for i in range(144)],windows=[],depleted_at=None,stats=dict(direct=0,recycled=0,decay=0,extra=0,post_withdrawal=0,losses=0))
def check(w):
    live=[o for o in w['objects'] if o['alive']]
    if sorted(o['atom'] for o in live)!=list(range(144)):raise ValueError('Mass')
    if w['work']<0 or w['heat']<0 or w['work']+w['heat']+sum({'F':6,'R':6,'M':2,'X':2,'W':0}[o['kind']] for o in live)!=1008:raise ValueError('Energy')
    for i,o in enumerate(w['objects']):
        if o['id']!=i or any(p<0 or p>=i for p in o['parents']):raise ValueError('Parent chronology')
        if o['fuel'] is not None and (o['fuel']>=i or w['objects'][o['fuel']]['kind']!='F'):raise ValueError('Fuel provenance')
        if any(p>=i or w['objects'][p]['kind']!='M' for p in o['cofactors']):raise ValueError('Cofactor provenance')
def add(w,atom,kind,t,species=None,parents=None,fuel=None,cofactors=None):
    o=obj(len(w['objects']),atom,kind,t,species,parents,fuel,cofactors);w['objects'].append(o);return o
def damage(w,t):
    target=w['seed']%4 if t==2048 else (w['seed']//4)%4
    selected=[o for o in w['objects'] if o['alive'] and o['kind']=='M' and o['species']==target]
    w['windows'].append(dict(start=t,target=target,lost=len(selected) if w['arm']!='sham' else 0,exposed=bool(selected) and w['arm']!='sham',eliminated=w['arm']!='sham',first_birth=None,outputs=[],end_counts=None,end_fresh=None,success=False))
    for o in selected:
        w['work']-=1;w['heat']+=1
        if w['arm']!='sham':o['alive']=False;add(w,o['atom'],'W',t,parents=[o['id']]);w['heat']+=2;w['stats']['losses']+=1
    return ['loss',target,[o['id'] for o in selected],w['arm']=='sham']
def advance(w,t,d):
    boundary=damage(w,t) if t in (2048,4096) else None
    if t==6144 and w['arm']=='food-withdrawn':
        removed=[o for o in w['objects'] if o['alive'] and o['kind']=='F']
        for o in removed:o['alive']=False;add(w,o['atom'],'R',t,parents=[o['id']])
        boundary=['withdraw',[o['id'] for o in removed]]
    live=[o for o in w['objects'] if o['alive']];x,y,a,b=[live[d[i]%len(live)] for i in (1,2,3,4)]
    target=d[5]%4;chance=d[6]&255;op=d[0]%3;event=None;product=None;cat=[]
    if a['id']!=b['id'] and a['kind']==b['kind']=='M':
        row=w['catalogue'][PAIRS.index(tuple(sorted((a['species'],b['species']))))]
        permitted=(d[7]%4<sum(row)) if w['arm']=='annealed' else bool(row[target])
        if permitted and w['arm']!='catalyst-ghost':cat=[a['id'],b['id']]
    if op in (0,1) and chance<(64 if cat else 4) and ((op==0 and x['kind']=='F') or (op==1 and x['kind']=='W' and y['kind']=='F')):
        payer=x if op==0 else y;parents=[x['id']] if op==0 else [x['id'],y['id']];x['alive']=False
        if op==1:y['alive']=False;add(w,y['atom'],'W',t,parents=parents)
        kind='X' if op==1 and w['arm']=='recycle-ghost' else 'M';product=add(w,x['atom'],kind,t,target,parents,payer['id'],cat);w['heat']+=4
        w['stats']['direct' if op==0 else 'recycled']+=1;w['stats']['extra']+=int(bool(cat) and chance>=4);w['stats']['post_withdrawal']+=int(t>=6144 and w['arm']=='food-withdrawn')
        event=['convert',op,x['id'],payer['id'],product['id'],kind,target,cat]
    elif op==2 and x['kind']=='M' and chance<8:
        x['alive']=False;product=add(w,x['atom'],'W',t,parents=[x['id']]);w['heat']+=2;w['stats']['decay']+=1;event=['decay',x['id'],product['id']]
    for window in w['windows']:
        if window['start']<=t<window['start']+1024 and product and product['kind']=='M':
            if product['species']==window['target'] and window['first_birth'] is None:window['first_birth']=t
            if window['first_birth'] is not None and t>window['first_birth']:window['outputs']=sorted(set(window['outputs']+[product['species']]))
        if t+1==window['start']+1024:
            living=[o for o in w['objects'] if o['alive'] and o['kind']=='M'];window['end_counts']=[sum(o['species']==s for o in living) for s in range(4)];window['end_fresh']=sum(o['species']==window['target'] and o['born']>=window['start'] for o in living)
            window['success']=window['exposed'] and window['eliminated'] and window['outputs']==list(range(4)) and all(window['end_counts']) and window['end_fresh']>0
    w['step']=t+1
    if w['depleted_at'] is None and not any(o['alive'] and o['kind']=='F' for o in w['objects']):w['depleted_at']=t
    check(w);return [boundary,event]
def world(seed,arm):
    w=new(seed,arm);trace=[]
    for t in range(8192):
        d=[]
        for _ in range(8):w['rng']=rand(w['rng']);d.append(w['rng'])
        trace.append([''.join(f'{v:08x}' for v in d),advance(w,t,d)])
    return dict(seed=seed,arm=arm,trace=trace,final=w,cursor=65536,success=all(x['success'] for x in w['windows']))
def main():
    from experiments.evidence_budget import Budget
    p=argparse.ArgumentParser();p.add_argument('--output',required=True);p.add_argument('--revision',required=True);a=p.parse_args();b=Budget(Path(a.output),dict(raw=192*1024**2,failure=2*1024**2),194*1024**2)
    try:
        with b.create('raw','manifest.json') as f:f.write(pack(dict(revision=a.revision,seeds=list(range(77000,77032)),arms=ARMS,worlds=192,attempts=1572864)))
        for seed in range(77000,77032):
            for arm in ARMS:
                with b.create('raw',f'{seed}-{arm}.json') as f:f.write(pack(world(seed,arm)))
            print(seed,flush=True)
    finally:
        with b.create('failure','budget.json',1024**2) as f:f.write(pack(copy.deepcopy(b.snapshot())))
if __name__=='__main__':main()
