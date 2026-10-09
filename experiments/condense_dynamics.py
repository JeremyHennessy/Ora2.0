"""CONDENSE-02 tiny raw-start finite kinetics; no organism/controller."""
import argparse
import copy
import hashlib
import json
import random
import struct
from . import condense_gate as law
from .evidence_budget import Budget


def world(seed,position,arm):
    rng=random.Random(seed);digest=hashlib.sha256();s=(4,0,0,position,0,0)
    fuel=[dict(id=i,state='F',events=[]) for i in range(4)]
    path=[];steps=[];selections=[];exposed=False;before=None;depleted=None
    for tick in range(1024):
        if tick==512:
            before=list(s)+[law.heat(s,arm)];options=dict(law.edges(s,arm))
            if (4,0,1) in options:
                s=options[(4,0,1)];exposed=True;path.append([4,0,1]);steps.append(tick);selections.append(None)
        c=rng.randrange(4);i=rng.randrange(3);forward=rng.getrandbits(1)
        token=rng.getrandbits(2);draw=rng.getrandbits(32);noise=rng.getrandbits(32)
        digest.update(struct.pack('<IIIIII',c,i,forward,token,draw,noise));action=(c,i,2*forward-1)
        options=dict(law.edges(s,arm))
        if action not in options:continue
        if c==0 and fuel[token]['state']!=('F' if forward else 'S'):continue
        t=options[action];_,exponent=law.probability(s,action,t,arm)
        if not 0<=exponent<=32:raise ValueError('Exact draw precision')
        if draw>=2**(32-exponent):continue
        if c==0:
            fuel[token]['state']='S' if forward else 'F';fuel[token]['events'].append(len(path))
        path.append(list(action));steps.append(tick);selections.append(token if c==0 else None);s=t
        if depleted is None and s[0]==0:depleted=tick
        if s[4]!=4-s[0]:raise ValueError('Work per net fuel invariant')
    final=law.provenance(arm,(4,0,0,position,0,0),path);final['fuel']=fuel
    owners=[0,1,2];used0=None
    for k,event in enumerate(final['events']):
        c,i,d=event['action']
        if final['states'][k][5]==1 and final['states'][k+1][5]==2:used0=owners[0]
        if c in (0,1,4):
            owners[i]=event['object'];selected=selections[k]
            final['objects'][event['object']]['food']=selected;event['food']=selected
    success=exposed and final['endpoint'] and used0==owners[0]
    return dict(schema='condense02',seed=seed,position=position,arm=arm,attempts=1024,
                event_steps=steps,draw_sha256=digest.hexdigest(),rng_sha256=hashlib.sha256(law.pack(rng.getstate())).hexdigest(),
                loss_exposed=exposed,pre_loss=before,first_depletion=depleted,
                used_object0=used0,primary_endpoint=bool(success),final=final)


def main():
    p=argparse.ArgumentParser();p.add_argument('--output',required=True);p.add_argument('--revision',required=True);a=p.parse_args()
    b=Budget(a.output,dict(raw=48*1024**2,failure=2*1024**2),50*1024**2)
    try:
        with b.create('raw','manifest.json') as f:f.write(law.pack(dict(revision=a.revision,worlds=256,attempts=262144,founder_free=True)))
        for position in range(8):
            for repetition in range(8):
                seed=79000+8*position+repetition
                for arm in law.ARMS:
                    with b.create('raw',f'{seed}-{arm}.json') as f:f.write(law.pack(world(seed,position,arm)))
    finally:
        with b.create('failure','budget.json',1024**2) as f:f.write(law.pack(copy.deepcopy(b.snapshot())))


if __name__=='__main__':main()
