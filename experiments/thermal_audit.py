"""Independent thermal-work ledger, finite bounds and edge/provenance interpreter."""
import argparse
import hashlib
import json
from pathlib import Path

LEVELS={-1:None,0:0,1:3,2:1}


def encode(s):return (s['H'],s['K'],s['W'],next(i for i,e in LEVELS.items() if e==s['e']))


def transition(s,action,c,arm):
    name,slot,d=action;t=s.copy();b=0
    if name=='build':
        if d>0 and s['e'] is None:t.update(e=0,W=s['W']-c,K=s['K']+c-3)
        elif d<0 and s['e']==0:t.update(e=None,W=s['W']+c,K=s['K']-c+3)
        else:return None
        b=c
    elif name=='work':
        if s['e']!=(1 if d>0 else 0):return None
        t.update(e=0 if d>0 else 1,W=s['W']+d)
    elif name=='heat':
        if s['e'] is None:return None
        gap,bath=slot.split(':');lower,upper=(0,3) if gap=='high' else (1,3)
        if s['e']!=(lower if d>0 else upper):return None
        allowed={'candidate':{'high:hot','low:cold'},'shuffled-working':{'high:hot','low:cold'},'shuffled-reversed':{'high:cold','low:hot'}}
        if arm!='independent' and slot not in allowed[arm]:return None
        field='H' if bath=='hot' else 'K';t[field]-=d*(upper-lower);t['e']=upper if d>0 else lower;b=int(arm=='independent')
    else:raise ValueError('Unknown primitive')
    if any(t[f]<0 for f in ('H','K','W')):return None
    exponent=b+max(0,s['H']+2*s['K']-t['H']-2*t['K'])
    return t,exponent


def graph(c,arm):
    alphabet=sorted([('build','body',d) for d in (-1,1)]+[('work','load',d) for d in (-1,1)]+[('heat',x,d) for x in ('high:cold','high:hot','low:cold','low:hot') for d in (-1,1)])
    total=49+2*c;states=edges=0;rates=set();digest=hashlib.sha256()
    for label in (-1,0,1,2):
        level=LEVELS[label];potential=0 if level is None else 3+level
        remaining=total-potential
        for hot in range(remaining+1):
            for cold in range(remaining-hot+1):
                s=dict(H=hot,K=cold,W=remaining-hot-cold,e=level);states+=1
                for a in alphabet:
                    result=transition(s,a,c,arm)
                    if result is None:continue
                    t,exponent=result;reverse=transition(t,(a[0],a[1],-a[2]),c,arm)
                    if reverse is None or reverse[0]!=s:raise ValueError('Missing physical reverse')
                    if t['H']+t['K']+t['W']+(0 if t['e'] is None else 3+t['e'])!=total:raise ValueError('Energy creation')
                    if s['H']+2*s['K']-exponent!=t['H']+2*t['K']-reverse[1]:raise ValueError('Unpriced kinetic drive')
                    edges+=1;rates.add((a,exponent,reverse[1]))
                    digest.update((str(encode(s))+'|'+str(a)+'|'+str(encode(t))+'|'+str(exponent)+'\n').encode())
    return dict(states=states,edges=edges,rate_signatures=len(rates),edge_sha256=digest.hexdigest())


def certificate(c,arm,n):
    s=dict(H=36,K=12,W=2*c+1,e=None);states=[list(encode(s))];events=[]
    items=[dict(id=i,atom=i,parent=None,state='raw',alive=True) for i in range(3)]
    live=[0,1,2];bodies=[];body=None;prior_work=None;net_work=0
    stream=[('build','body',1)]
    for i in range(n):
        if i==5:stream.extend([('damage','body',1),('build','body',1)])
        stream.extend([('heat','high:hot',1),('heat','low:'+('hot' if arm=='independent' and c>=6 else 'cold'),-1),('work','load',1)])
    for a in stream:
        event=dict(action=list(a),body=body)
        if a[0]=='damage':
            if s['e']!=0 or net_work!=5 or s['W']<1:raise ValueError('Unpriced/wrong exposure')
            prior_work=s['W'];s.update(K=s['K']+4,W=s['W']-1,e=None);bodies[body]['alive']=False
        else:
            result=transition(s,a,c,arm)
            if result is None:raise ValueError('Unfunded physical witness')
            s,exponent=result;event['rate_exponent']=exponent
            if a[0]=='work':net_work+=a[2]
            if a[0]=='build':
                index=len(bodies);bodies.append(dict(id=index,parent=body,atoms=[0,1,2],alive=True));body=index;event['new_body']=index
        if a[0] in ('build','damage'):
            ids=[]
            for atom in range(3):
                ancestor=live[atom];items[ancestor]['alive']=False;index=len(items)
                items.append(dict(id=index,atom=atom,parent=ancestor,state='raw' if a[0]=='damage' else 'active',alive=True));ids.append(index)
            live=ids;event['components']=ids
        if s['H']+s['K']+s['W']+(0 if s['e'] is None else 3+s['e'])!=49+2*c:raise ValueError('Every-event conservation')
        if sum(item['alive'] for item in items)!=3:raise ValueError('Material duplication')
        events.append(event);states.append(list(encode(s)))
    return dict(states=states,events=events,objects=items,bodies=bodies,owners=live,pre_damage_work=prior_work,net_cycles=net_work,total_energy=49+2*c,material_units=3,whole_surplus=s['W']-(2*c+1),post_damage_surplus=s['W']-prior_work,endpoint=s['e']==0 and s['W']>2*c+1 and s['W']>prior_work and s['K']>=12)


def check_record(record):
    c,arm=record['cost'],record['arm']
    if c not in range(3,13) or arm not in ('candidate','independent','shuffled-working','shuffled-reversed'):raise ValueError('Frozen cost/layout')
    feasible=[]
    for n in range(74):
        if arm=='shuffled-reversed':h,k=36+2*n,10+2*c-3*n
        elif arm=='independent' and c>=6:h,k=36-n,10+2*c
        else:h,k=36-3*n,10+2*c+2*n
        if n>2*c+1 and n>c+6 and h>=0 and k>=12:feasible.append(n)
    possible=bool(feasible)
    expected=dict(cost=c,arm=arm,possible=possible,candidate_cycle_limit=12,whole_surplus_upper=12-(2*c+1),post_surplus_upper=12-(c+6),physical=graph(c,arm),witness=certificate(c,arm,min(feasible)) if possible else None)
    if record!=expected:raise ValueError('Complete bound/rate/state/identity mismatch')
    return possible


def audit(data,revision):
    if data['schema']!='thermal01' or data['source_revision']!=revision or data['natural_worlds']!=0 or data['controlled_cases']!=40:raise ValueError('Exact source/controlled scope')
    required=[(c,a) for c in range(3,13) for a in ('candidate','independent','shuffled-working','shuffled-reversed')]
    if [(r['cost'],r['arm']) for r in data['records']]!=required:raise ValueError('Missing/selected case')
    for r in data['records']:check_record(r)
    by_arm={a:[r['cost'] for r in data['records'] if r['arm']==a and r['possible']] for a in ('candidate','independent','shuffled-working','shuffled-reversed')}
    feasible=by_arm['candidate'];gate=feasible==[3,4,5] and all(c in by_arm['independent'] and c in by_arm['shuffled-working'] for c in feasible)
    return dict(verified=True,source_revision=revision,controlled_cases=40,natural_worlds=0,possible_costs=by_arm,candidate_refused_costs=[c for c in range(3,13) if c not in feasible],physical_states=sum(r['physical']['states'] for r in data['records']),physical_edges=sum(r['physical']['edges'] for r in data['records']),whole_and_post_damage_surplus_possible=gate,fair_primary_control_endpoints=True,reachability_or_maximum_yield_advantage=False,feasibility_gate_pass=gate,spontaneous_organization=False,self_maintenance_demonstrated=False,high_cost_independent_witnesses='Rare one-bath thermal fluctuations: nonzero paths, not mean single-bath work production',next='Separately freeze controlled kinetics for all three feasible costs; natural assembly and calibrated full costs remain separate gates')


def main():
    p=argparse.ArgumentParser();p.add_argument('--input',required=True);p.add_argument('--revision',required=True);a=p.parse_args()
    try:print(json.dumps(audit(json.loads(Path(a.input).read_bytes()),a.revision),sort_keys=True))
    except (ValueError,KeyError,IndexError,TypeError) as error:
        print(json.dumps(dict(verified=False,error=str(error))));raise SystemExit(2)


if __name__=='__main__':main()
