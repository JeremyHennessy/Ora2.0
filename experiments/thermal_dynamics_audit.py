"""Independent full thermal sample interpreter and registered decision statistics."""
import argparse
import hashlib
import json
import math
import random
import struct
from pathlib import Path
from .thermal_audit import transition, encode

def reconstruct(c,seed,arm):
    law=arm
    if arm=='shuffled':law='shuffled-working' if seed%2==0 else 'shuffled-reversed'
    alphabet=sorted([('build','body',d) for d in (-1,1)]+[('work','load',d) for d in (-1,1)]+[('heat',g+':'+b,d) for g in ('high','low') for b in ('hot','cold') for d in (-1,1)])
    randomizer=random.Random(seed);draws=hashlib.sha256()
    state=dict(H=36,K=12,W=2*c+1,e=None);history=[list(encode(state))];accepted=[]
    items=[dict(id=i,atom=i,parent=None,state='raw',alive=True) for i in range(3)]
    live=[0,1,2];lineage=[];current=previous=replacement=None
    pre=None;loss_step=None;used=False;balance=positive=negative=0
    charged=returned=loss_charge=0;depleted=None
    for tick in range(2048):
        pending=[]
        if pre is None and state['e']==0 and balance==5 and state['W']>=1:
            pending.append((('damage','body',1),None))
        # Loss precedes the proposal; all logical draws remain consumed.
        for stage in range(2):
            if stage==1:
                idx=randomizer.randrange(12);coin=randomizer.getrandbits(32);unused=randomizer.getrandbits(32)
                draws.update(struct.pack('<III',idx,coin,unused));primitive=alphabet[idx]
                result=transition(state,primitive,c,law)
                pending=[]
                if result is not None:
                    target,exponent=result
                    if not 0<=exponent<=32:raise ValueError('Rate range')
                    if coin<2**(32-exponent):pending=[(primitive,(target,exponent))]
            for primitive,result in pending:
                name,slot,direction=primitive;event=dict(step=tick,action=list(primitive),body=current)
                if name=='damage':
                    pre=state['W'];loss_step=tick;loss_charge+=1
                    state.update(W=state['W']-1,K=state['K']+4,e=None)
                else:
                    state,exponent=result;event['rate_exponent']=exponent
                if name=='work':
                    balance+=direction;positive+=int(direction>0);negative+=int(direction<0)
                    if direction>0 and replacement is not None and current==replacement:used=True
                if name in ('build','damage'):
                    building=name=='build' and direction>0
                    if building:
                        charged+=c;current=len(lineage)
                        lineage.append(dict(id=current,parent=previous,atoms=[0,1,2],alive=True));previous=current;event['new_body']=current
                        if pre is not None and replacement is None:replacement=current
                    else:
                        if name=='build':returned+=c
                        lineage[current]['alive']=False;current=None
                    replacement_items=[]
                    for atom,ancestor in enumerate(live):
                        items[ancestor]['alive']=False;identity=len(items)
                        items.append(dict(id=identity,atom=atom,parent=ancestor,state='active' if building else 'raw',alive=True));replacement_items.append(identity)
                    live=replacement_items;event['components']=live.copy()
                potential=0 if state['e'] is None else 3+state['e']
                if sum(state[x] for x in ('H','K','W'))+potential!=49+2*c:raise ValueError('Conservation')
                if sum(x['alive'] for x in items)!=3:raise ValueError('Duplicated material')
                accepted.append(event);history.append(list(encode(state)))
        if state['H']==0 and depleted is None:depleted=tick
    whole=state['W']-(2*c+1);post=None if pre is None else state['W']-pre
    continuous=replacement is not None and current==replacement and state['e']==0
    success=continuous and used and whole>0 and post>0 and state['K']>=12
    return dict(cost=c,seed=seed,arm=arm,states=history,events=accepted,objects=items,bodies=lineage,owners=live,current_body=current,first_rebuilt=replacement,pre_damage_work=pre,exposure_step=loss_step,fresh_work=used,net_work=balance,forward_work=positive,reverse_work=negative,construction_paid=charged,release_refund=returned,damage_paid=loss_charge,whole_surplus=whole,post_damage_surplus=post,continuity=continuous,endpoint=bool(success),hot_zero_step=depleted,draw_sha256=draws.hexdigest(),rng_sha256=hashlib.sha256(json.dumps(randomizer.getstate(),sort_keys=True).encode()).hexdigest(),total_energy=49+2*c,material_units=3,attempts=2048)

def audit_record(r):
    if r['cost'] not in (3,4,5) or r['seed'] not in range(83000,83064) or r['arm'] not in ('candidate','independent','shuffled'):raise ValueError('Unregistered sample')
    if reconstruct(r['cost'],r['seed'],r['arm'])!=r:raise ValueError('Complete independent trajectory mismatch')

def audit(root,revision):
    root=Path(root);manifest=json.loads((root/'manifest.json').read_bytes())
    if manifest!=dict(schema='thermal02',source_revision=revision,protocol_revision='8312eff',worlds=576,attempts=1179648,natural_worlds=0):raise ValueError('Manifest')
    records={};summary={};comparisons=[];aliases=0
    expected={'manifest.json'}
    for c in (3,4,5):
        for seed in range(83000,83064):
            for arm in ('candidate','independent','shuffled'):
                name=f'{c}-{seed}-{arm}.json';expected.add(name);r=json.loads((root/name).read_bytes());audit_record(r);records[c,seed,arm]=r
            if seed%2==0:
                a=records[c,seed,'candidate'].copy();b=records[c,seed,'shuffled'].copy();a.pop('arm');b.pop('arm')
                if a!=b:raise ValueError('Working shuffled positive-null alias differs')
                aliases+=1
        summary[str(c)]={}
        for arm in ('candidate','independent','shuffled'):
            rows=[records[c,s,arm] for s in range(83000,83064)]
            summary[str(c)][arm]=dict(worlds=64,successes=sum(r['endpoint'] for r in rows),exposed=sum(r['exposure_step'] is not None for r in rows),rebuilt=sum(r['first_rebuilt'] is not None for r in rows),fresh_function=sum(r['fresh_work'] for r in rows),continuous_rebuilt=sum(r['continuity'] for r in rows),whole_surplus_positive=sum(r['whole_surplus']>0 for r in rows),post_surplus_positive=sum(r['post_damage_surplus'] is not None and r['post_damage_surplus']>0 for r in rows),hot_depleted=sum(r['hot_zero_step'] is not None for r in rows),whole_surplus_sum=sum(r['whole_surplus'] for r in rows),net_work_sum=sum(r['net_work'] for r in rows))
        for arm in ('independent','shuffled'):
            wins=losses=0
            for seed in range(83000,83064):
                a=records[c,seed,'candidate']['endpoint'];b=records[c,seed,arm]['endpoint']
                wins+=a and not b;losses+=b and not a
            n=wins+losses;p=sum(math.comb(n,k) for k in range(wins,n+1))/2**n if n else 1.0
            comparisons.append(dict(cost=c,control=arm,wins=wins,losses=losses,p=p))
    if {p.name for p in root.iterdir() if p.is_file()}!=expected:raise ValueError('Extra/selected records')
    keep=True
    for rank,item in enumerate(sorted(comparisons,key=lambda x:x['p'])):
        threshold=.05/(6-rank);keep=keep and item['p']<=threshold;item['holm_reject']=keep;item['holm_threshold']=threshold
    gate=all(summary[str(c)]['candidate']['successes']>=8 for c in (3,4,5)) and all(r['holm_reject'] for r in comparisons)
    return dict(verified=True,source_revision=revision,worlds=576,attempts=1179648,natural_worlds=0,working_aliases=aliases,summary=summary,comparisons=comparisons,primary_pass=gate,self_maintenance_demonstrated=False,spontaneous_organization=False,next='Independent disjoint controlled reproduction' if gate else 'Close tested law/costs/horizon; choose distinct natural-organization law')

def main():
    p=argparse.ArgumentParser();p.add_argument('--input',required=True);p.add_argument('--revision',required=True);a=p.parse_args()
    try:print(json.dumps(audit(a.input,a.revision),sort_keys=True))
    except (ValueError,KeyError,IndexError,TypeError) as e:print(json.dumps(dict(verified=False,error=str(e))));raise SystemExit(2)

if __name__=='__main__':main()
