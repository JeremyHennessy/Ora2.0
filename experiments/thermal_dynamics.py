"""Prospectively fixed controlled thermal renewal panel; no natural founders."""
import argparse
import hashlib
import json
import random
import struct
from pathlib import Path
from .thermal_gate import actions, move, ENERGY
from .evidence_budget import Budget

ARMS=('candidate','independent','shuffled')

def world(cost,seed,arm):
    layout=arm if arm!='shuffled' else ('shuffled-working' if seed%2==0 else 'shuffled-reversed')
    rng=random.Random(seed);digest=hashlib.sha256();alphabet=actions()
    s=(36,12,2*cost+1,-1);states=[list(s)];events=[]
    objects=[dict(id=i,atom=i,parent=None,state='raw',alive=True) for i in range(3)]
    owners=[0,1,2];bodies=[];body=last=rebuilt=None;before=None;net=0;fresh=False
    paid=refund=damage_cost=0;forward=reverse=0;exposure=None;hot_zero=None
    def apply(a,step,p=None):
        nonlocal s,body,last,rebuilt,before,net,fresh,paid,refund,damage_cost,forward,reverse,exposure
        kind,slot,d=a;event=dict(step=step,action=list(a),body=body)
        if kind=='damage':
            before=s[2];exposure=step;damage_cost+=1
            s=(s[0],s[1]+4,s[2]-1,-1)
        else:
            s,p=move(s,a,cost,layout);event['rate_exponent']=p
        if kind=='work':
            net+=d;forward+=int(d==1);reverse+=int(d==-1)
            if d==1 and body==rebuilt and rebuilt is not None:fresh=True
        if kind in ('build','damage'):
            if kind=='build' and d==1:
                paid+=cost;body=len(bodies)
                bodies.append(dict(id=body,parent=last,atoms=[0,1,2],alive=True));last=body;event['new_body']=body
                if before is not None and rebuilt is None:rebuilt=body
            else:
                if kind=='build':refund+=cost
                bodies[body]['alive']=False;body=None
            new=[]
            for atom,old in enumerate(owners):
                objects[old]['alive']=False;identity=len(objects)
                objects.append(dict(id=identity,atom=atom,parent=old,state='active' if body is not None else 'raw',alive=True));new.append(identity)
            owners[:]=new;event['components']=new
        assert sum(s[:3])+ENERGY[s[3]]==49+2*cost
        assert sum(o['alive'] for o in objects)==3
        events.append(event);states.append(list(s))
    for step in range(2048):
        if before is None and s[3]==0 and net==5 and s[2]>=1:apply(('damage','body',1),step)
        index=rng.randrange(12);draw=rng.getrandbits(32);noise=rng.getrandbits(32)
        digest.update(struct.pack('<III',index,draw,noise));a=alphabet[index];result=move(s,a,cost,layout)
        if result is not None:
            assert 0<=result[1]<=32
            if draw < (1<<(32-result[1])):apply(a,step)
        if s[0]==0 and hot_zero is None:hot_zero=step
    whole=s[2]-(2*cost+1);post=None if before is None else s[2]-before
    continuity=rebuilt is not None and body==rebuilt and s[3]==0
    endpoint=continuity and fresh and whole>0 and post>0 and s[1]>=12
    return dict(cost=cost,seed=seed,arm=arm,states=states,events=events,objects=objects,bodies=bodies,owners=owners,current_body=body,first_rebuilt=rebuilt,pre_damage_work=before,exposure_step=exposure,fresh_work=fresh,net_work=net,forward_work=forward,reverse_work=reverse,construction_paid=paid,release_refund=refund,damage_paid=damage_cost,whole_surplus=whole,post_damage_surplus=post,continuity=continuity,endpoint=bool(endpoint),hot_zero_step=hot_zero,draw_sha256=digest.hexdigest(),rng_sha256=hashlib.sha256(json.dumps(rng.getstate(),sort_keys=True).encode()).hexdigest(),total_energy=49+2*cost,material_units=3,attempts=2048)

def main():
    p=argparse.ArgumentParser();p.add_argument('--output',required=True);p.add_argument('--revision',required=True);a=p.parse_args()
    b=Budget(Path(a.output),dict(raw=99*1024**2,failure=1024**2),100*1024**2)
    try:
        with b.create('raw','manifest.json') as f:f.write(json.dumps(dict(schema='thermal02',source_revision=a.revision,protocol_revision='8312eff',worlds=576,attempts=1179648,natural_worlds=0)).encode())
        for c in (3,4,5):
            for seed in range(83000,83064):
                for arm in ARMS:
                    with b.create('raw',f'{c}-{seed}-{arm}.json') as f:f.write(json.dumps(world(c,seed,arm),sort_keys=True).encode())
    finally:
        with b.create('failure','budget.json',1024**2) as f:f.write(json.dumps(b.snapshot()).encode())

if __name__=='__main__':main()
