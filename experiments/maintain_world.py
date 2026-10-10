"""Registered raw-start maintenance dynamics; no selected catalogue."""
import argparse
from collections import deque
import hashlib
import json
import random
from experiments.maintain_gate import START,heat,move,pack,pref

ARMS=('candidate','independent','annealed')

def world(seed,arm,revision,attempts=4096,loss_step=2048):
    assert arm in ARMS
    mask=seed-87000 if seed>=87000 else 21
    assert 0<=mask<64
    rng=random.Random(seed);draws=hashlib.sha256();s=START
    atoms=[0,1,2];fuels=list(range(3,13));fuel=[True]*10;touched=[False]*10
    next_id=13;work=deque();events=[];last_capture={};fresh=other=reverse=netcost=loss_cost=0
    pre=None;paid=False;exposed=False;first=None;posttypes=set();post_first_fresh=False
    baseline=None;gross=0
    def debit(n):
        assert len(work)>=n
        return [work.popleft() for _ in range(n)]
    for step in range(attempts):
        if step==loss_step:
            pre=s;baseline=(fresh,other,reverse,netcost,loss_cost)
            exposed=s[3]==7 and atoms[0] in last_capture and s[4]>=2
            if s[3]&1 and s[4]>=2:
                old=atoms[0];origins=debit(2);loss_cost+=2;paid=True
                s=(*s[:3],s[3]^1,s[4]-2);atoms[0]=next_id
                events.append([step,-1,list(s),next_id,old,None,origins]);next_id+=1
        slot=rng.randrange(46);cofactor=rng.randrange(3);u=rng.getrandbits(32);noise=rng.getrandbits(32)
        draws.update(pack([slot,cofactor,u,noise]))
        if slot<40:
            token=slot//4;channel=slot%4;k='capture' if channel<2 else 'waste';d=1 if channel%2==0 else -1;i=token%3
            if fuel[token]!=(d==1):continue
            rate=16 if k=='capture' and s[3]&(1<<i) else 4
            catalyst=atoms[i] if rate==16 else None
        else:
            i=(slot-40)//2;k='activate';d=1 if slot%2==0 else -1
            rate=pref(mask,s[3],i,cofactor,arm,noise&1)
            catalyst=atoms[cofactor] if rate==64 else None
        result=move(s,(k,i,d))
        if not result:continue
        t,_=result;power=min(0,heat(t)-heat(s))
        if u*64*(1<<(-power)) >= rate*(1<<32):continue
        origins=[];old=atoms[i] if k=='activate' else fuels[token]
        if k=='capture':
            if d==1:
                gross+=2;work.extend([next_id]*2)
                if not touched[token]:fresh+=2
                else:other+=2
                if s[3]&(1<<i):
                    last_capture[atoms[i]]=step
                    if first is not None and not touched[token]:
                        posttypes.add(i)
                        if i==0 and atoms[0]==first:post_first_fresh=True
            else:reverse+=2;origins=debit(2)
        if k=='activate':
            netcost+=3*d
            if d==1:
                origins=debit(3)
                if paid and first is None and i==0:first=next_id
            else:work.extend([next_id]*3)
            atoms[i]=next_id
        else:fuels[token]=next_id;fuel[token]=d==-1;touched[token]=True
        s=t;events.append([step,slot,list(s),next_id,old,catalyst,origins]);next_id+=1
        assert len(work)==s[4]
    f0,o0,r0,n0,l0=baseline
    score=dict(paid_loss=paid,exposed=exposed,first_rebuild=first is not None,
        first_rebuild_fresh_work=post_first_fresh,first_rebuild_retained=first is not None and atoms[0]==first and bool(s[3]&1),
        post_types=sorted(posttypes),fresh=fresh,other=other,reverse=reverse,activation_net=netcost,loss_cost=loss_cost,
        whole_surplus=fresh-reverse-netcost-loss_cost,post_surplus=(fresh-f0)-(reverse-r0)-(netcost-n0)-(loss_cost-l0),
        final_work=s[4],post_work_gain=s[4]-pre[4],final_heat=heat(s),pre_heat=heat(pre),fuel_exhausted=sum(s[:3])==0,gross=gross)
    score['success']=bool(exposed and score['first_rebuild_retained'] and post_first_fresh and posttypes=={0,1,2}
        and s[3]==7 and min(score['whole_surplus'],score['post_surplus'],s[4],score['post_work_gain'])>0 and heat(s)>=max(8,heat(pre)))
    return dict(schema='maintain02-world',source_revision=revision,seed=seed,catalogue=mask,arm=arm,attempts=attempts,loss_step=loss_step,
        events=events,final=list(s),atom_ids=atoms,fuel_ids=fuels,fuel_state=fuel,touched=touched,work_provenance=list(work),
        next_identity=next_id,draw_sha256=draws.hexdigest(),random_sha256=hashlib.sha256(pack(rng.getstate())).hexdigest(),score=score)

def main():
    p=argparse.ArgumentParser();p.add_argument('--revision',required=True);p.add_argument('--seed',type=int);p.add_argument('--arm',choices=ARMS);p.add_argument('--output-file');a=p.parse_args()
    if a.seed is not None:r=world(a.seed,a.arm,a.revision)
    else:r=dict(schema='maintain02-panel',source_revision=a.revision,records=[world(seed,arm,a.revision) for seed in range(87000,87064) for arm in ARMS])
    if a.output_file:
        payload=pack(r);assert len(payload)<=50*1024**2
        with open(a.output_file,'r+b') as f:
            assert f.read()==b'';f.seek(0);f.write(payload);f.flush()
        print(json.dumps(dict(worlds=len(r['records']),bytes=len(payload))))
    else:print(json.dumps(r,sort_keys=True))
if __name__=='__main__':main()
