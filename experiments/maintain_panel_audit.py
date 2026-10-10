"""Independent full-draw interpreter, identities, work provenance and decision."""
import argparse
import hashlib
import json
import math
import random
from experiments.maintain_audit import successor,thermal,encoded

def interpret(record,revision):
    assert record['schema']=='maintain02-world' and record['source_revision']==revision
    seed=record['seed'];mask=seed-87000 if seed>=87000 else 21;arm=record['arm']
    assert record['catalogue']==mask and 0<=mask<64 and arm in ('candidate','independent','annealed')
    assert (record['attempts'],record['loss_step'])==(4096,2048) or seed in (0,1)
    randoms=random.Random(seed);digest=hashlib.sha256();state=(4,3,3,0,0)
    aids=[0,1,2];fids=list(range(3,13));fs=[1]*10;used=[False]*10;stored=[];identity=13
    chronology=iter(record['events']);row=next(chronology,None);capture_identity=set()
    first=None;paid=exposure=first_fresh=False;types=set();fresh=other=backward=cost=loss=gross=0
    previous=None;initial_costs=None
    def consume(n):
        assert len(stored)>=n
        result=stored[:n];del stored[:n];return result
    def check(step,slot,parent,catalyst,bill):
        nonlocal row,identity
        assert row==[step,slot,list(state),identity,parent,catalyst,bill]
        assert parent<identity and (catalyst is None or catalyst<identity) and all(x<identity for x in bill)
        identity+=1;row=next(chronology,None)
    links=[(j,i) for j in range(3) for i in range(3) if j!=i]
    for step in range(record['attempts']):
        if step==record['loss_step']:
            previous=state;initial_costs=(fresh,backward,cost,loss)
            exposure=state[3]==7 and aids[0] in capture_identity and state[4]>=2
            if state[3]&1 and state[4]>=2:
                old=aids[0];bill=consume(2);loss+=2;paid=True;aids[0]=identity
                state=(*state[:3],state[3]-1,state[4]-2);check(step,-1,old,None,bill)
        slot=randoms.randrange(46);j=randoms.randrange(3);draw=randoms.getrandbits(32);noise=randoms.getrandbits(32)
        digest.update(encoded([slot,j,draw,noise]));catalyst=None
        if slot>=40:
            i=(slot-40)//2;direction=1 if (slot-40)%2==0 else -1;kind='activate';r=4
            if i!=j and state[3]&(1<<j) and arm!='independent':
                active_edge=bool(mask&(1<<links.index((j,i))))
                if arm=='annealed':
                    count=sum(bool(mask&(1<<k)) for k,(src,dst) in enumerate(links) if src==j)
                    active_edge=(noise%2)<count
                if active_edge:r=64;catalyst=aids[j]
        else:
            token,channel=divmod(slot,4);i=token%3;kind=('capture','waste')[channel//2];direction=(1,-1)[channel%2]
            if fs[token]!=(direction>0):continue
            r=16 if kind=='capture' and (state[3]>>i)&1 else 4
            if r==16:catalyst=aids[i]
        proposal=successor(state,kind,i,direction)
        if proposal is None:continue
        target,_=proposal;drop=max(0,thermal(state)-thermal(target))
        if draw*64*(2**drop)>=r*4294967296:continue
        bill=[];parent=aids[i] if kind=='activate' else fids[token]
        if kind=='capture':
            if direction>0:
                gross+=2;stored.extend((identity,identity))
                if used[token]:other+=2
                else:fresh+=2
                if (state[3]>>i)&1:
                    capture_identity.add(aids[i])
                    if first is not None and not used[token]:
                        types.add(i)
                        if i==0 and aids[0]==first:first_fresh=True
            else:backward+=2;bill=consume(2)
        if kind=='activate':
            cost+=direction*3
            if direction>0:
                bill=consume(3)
                if paid and first is None and i==0:first=identity
            else:stored.extend((identity,)*3)
            aids[i]=identity
        else:fids[token]=identity;used[token]=True;fs[token]=int(direction<0)
        state=target;check(step,slot,parent,catalyst,bill);assert len(stored)==state[4]
    assert row is None
    assert record['final']==list(state) and record['atom_ids']==aids and record['fuel_ids']==fids
    assert record['fuel_state']==fs and record['touched']==used and record['work_provenance']==stored and record['next_identity']==identity
    assert record['draw_sha256']==digest.hexdigest() and record['random_sha256']==hashlib.sha256(encoded(randoms.getstate())).hexdigest()
    f0,b0,c0,l0=initial_costs
    score=dict(paid_loss=paid,exposed=exposure,first_rebuild=first is not None,first_rebuild_fresh_work=first_fresh,
        first_rebuild_retained=first is not None and aids[0]==first and bool(state[3]&1),post_types=sorted(types),
        fresh=fresh,other=other,reverse=backward,activation_net=cost,loss_cost=loss,whole_surplus=fresh-backward-cost-loss,
        post_surplus=fresh-f0-(backward-b0)-(cost-c0)-(loss-l0),final_work=state[4],post_work_gain=state[4]-previous[4],
        final_heat=thermal(state),pre_heat=thermal(previous),fuel_exhausted=sum(state[:3])==0,gross=gross)
    score['success']=bool(exposure and score['first_rebuild_retained'] and first_fresh and types=={0,1,2}
        and state[3]==7 and min(score['whole_surplus'],score['post_surplus'],state[4],score['post_work_gain'])>0
        and thermal(state)>=max(8,thermal(previous)))
    assert record['score']==score
    return score

def decision(record,revision):
    assert record['schema']=='maintain02-panel' and record['source_revision']==revision
    arms=('candidate','independent','annealed');expected=[(s,a) for s in range(87000,87064) for a in arms]
    assert [(r['seed'],r['arm']) for r in record['records']]==expected
    scores={(r['seed'],r['arm']):interpret(r,revision) for r in record['records']};summary={}
    for arm in arms:
        values=[scores[s,arm] for s in range(87000,87064)]
        keys=('success','exposed','paid_loss','first_rebuild','first_rebuild_fresh_work','first_rebuild_retained','fuel_exhausted',
              'fresh','other','reverse','activation_net','loss_cost','whole_surplus','post_surplus','final_work','gross')
        summary[arm]={k:sum(v[k] for v in values) for k in keys}
        summary[arm]['positive_post_surplus']=sum(v['post_surplus']>0 for v in values)
    comparisons=[]
    for arm in arms[1:]:
        better=sum(scores[s,'candidate']['success'] and not scores[s,arm]['success'] for s in range(87000,87064))
        worse=sum(scores[s,arm]['success'] and not scores[s,'candidate']['success'] for s in range(87000,87064))
        n=better+worse;p=sum(math.comb(n,k) for k in range(better,n+1))/2**n if n else 1.
        comparisons.append(dict(control=arm,candidate_only=better,control_only=worse,p=p))
    ordered=sorted(comparisons,key=lambda v:v['p']);running=0
    for i,v in enumerate(ordered):running=max(running,min(1,(2-i)*v['p']));v['holm_p']=running
    passed=summary['candidate']['exposed']>=48 and summary['candidate']['success']>=16 and all(v['holm_p']<=.05 for v in comparisons)
    return dict(schema='maintain02-decision',source_revision=revision,worlds=192,attempts=192*4096,
        full_independent_history_audit=True,summary=summary,comparisons=comparisons,primary_pass=passed,
        classification='POSITIVE_REQUIRES_REPRODUCTION' if passed else ('UNDEREXPOSED' if summary['candidate']['exposed']<48 else 'REJECTED'),
        reserved_samples_executed=False,self_maintenance_accepted=False,
        next_decision='Independently reproduce on reserved samples.' if passed else 'Close this exact law; preserve negative result, no tuning.')

def main():
    p=argparse.ArgumentParser();p.add_argument('--input',required=True);p.add_argument('--revision',required=True);p.add_argument('--single-world',action='store_true');a=p.parse_args()
    try:
        with open(a.input,encoding='utf-8') as f:r=json.load(f)
        print(json.dumps(interpret(r,a.revision) if a.single_world else decision(r,a.revision),sort_keys=True))
    except (AssertionError,ValueError,KeyError,TypeError,StopIteration) as e:
        print(json.dumps(dict(verified=False,error=str(e))));raise SystemExit(2)
if __name__=='__main__':main()
