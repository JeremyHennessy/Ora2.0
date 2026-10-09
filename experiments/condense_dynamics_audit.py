"""Independent set-state CONDENSE-02 attempt/provenance/statistics interpreter."""
import argparse
import hashlib
import json
from math import comb
from pathlib import Path
import random
import struct
from . import condense_audit as law


def canonical(x):return json.dumps(x,sort_keys=True,separators=(',',':')).encode()


def audit_record(record):
    seed,pos,arm=record['seed'],record['position'],record['arm']
    if pos not in range(8) or arm not in ('candidate','affinity-ghost','catalysis-ghost','passive'):raise ValueError('Frozen geometry/arm')
    s=law.convert((4,0,0,pos,0,0));rng=random.Random(seed);digest=hashlib.sha256()
    objects=[dict(id=i,atom=i,state='R',parent=None,food=None,alive=True) for i in range(3)]
    owners=[0,1,2];history=[[i] for i in range(3)]
    fuel=[dict(id=i,state='F',events=[]) for i in range(4)];bonds=[];live={}
    actions=[];events=[];states=[list(law.encode(s))+[law.heat(s,arm)]];steps=[]
    exposed=False;pre=None;depleted=None;used0=None
    def execute(action,target,tick,selected=None):
        nonlocal s,used0
        c,i,d=action;event=dict(action=list(action))
        if s[5]==1 and target[5]==2:used0=owners[0]
        if c in (0,1,4):
            parent=owners[i];objects[parent]['alive']=False
            if c==0:
                fuel[selected]['state']='S' if d>0 else 'F';fuel[selected]['events'].append(len(events))
            new=len(objects);objects.append(dict(id=new,atom=i,state='M' if c!=4 and d>0 else 'R',parent=parent,food=selected,alive=True));owners[i]=new;history[i].append(new)
            event.update(parent=parent,object=new,food=selected)
            if c==4:
                lost=[]
                for pair in list(live):
                    if i in law.PAIRS[pair]:
                        identity=live.pop(pair);bonds[identity]['alive']=False;lost.append(identity)
                event['lost_bonds']=sorted(lost)
        elif c==2:
            if d>0:
                identity=len(bonds);bonds.append(dict(id=identity,atoms=list(law.PAIRS[i]),objects=[owners[j] for j in law.PAIRS[i]],alive=True,stabilization=int(arm!='affinity-ghost')));live[i]=identity
            else:identity=live.pop(i);bonds[identity]['alive']=False
            event['bond']=identity
        else:event['moved_atoms']=sorted(j for j in range(3) if s[3][j]!=target[3][j])
        events.append(event);actions.append(list(action));steps.append(tick);s=target
        states.append(list(law.encode(s))+[law.heat(s,arm)])
        if sum(t['state']=='F' for t in fuel)!=s[0] or s[4]!=4-s[0]:raise ValueError('Material/work invariant')
        if 6*s[0]+2*len(s[1])-int(arm!='affinity-ghost')*len(s[2])+s[4]+(3 if s[5]==0 else 2)+law.heat(s,arm)!=35:raise ValueError('Every-event energy')
    for tick in range(1024):
        if tick==512:
            pre=list(law.encode(s))+[law.heat(s,arm)];choices=dict(law.proposals(s,arm))
            if (4,0,1) in choices:execute((4,0,1),choices[(4,0,1)],tick);exposed=True
        c=rng.randrange(4);i=rng.randrange(3);forward=rng.getrandbits(1)
        selected=rng.getrandbits(2);draw=rng.getrandbits(32);extra=rng.getrandbits(32)
        digest.update(struct.pack('<IIIIII',c,i,forward,selected,draw,extra));action=(c,i,2*forward-1)
        choices=dict(law.proposals(s,arm))
        if action not in choices:continue
        if c==0 and fuel[selected]['state']!=('F' if forward else 'S'):continue
        target=choices[action];_,exponent=law.rate(s,action,target,arm)
        if not 0<=exponent<=32:raise ValueError('Probability resolution')
        if draw>=2**(32-exponent):continue
        execute(action,target,tick,selected if c==0 else None)
        if depleted is None and s[0]==0:depleted=tick
    final=dict(start=[4,0,0,pos,0,0],path=actions,states=states,events=events,objects=objects,
               fuel=fuel,bonds=bonds,atom_history=history,total_energy=35,material_units=7,
               operator_spent=int(exposed),endpoint=law.qualifies(s,arm))
    success=exposed and law.qualifies(s,arm) and used0==owners[0]
    expected=dict(schema='condense02',seed=seed,position=pos,arm=arm,attempts=1024,event_steps=steps,
                  draw_sha256=digest.hexdigest(),rng_sha256=hashlib.sha256(canonical(rng.getstate())).hexdigest(),
                  loss_exposed=exposed,pre_loss=pre,first_depletion=depleted,used_object0=used0,
                  primary_endpoint=bool(success),final=final)
    if record!=expected:raise ValueError('Complete draw/event/identity/physical state mismatch')
    counts={str(c):{direction:sum(a[0]==c and a[2]==d for a in actions) for direction,d in (('forward',1),('reverse',-1))} for c in range(4)}
    route=None
    if used0 is not None:route=next(e['action'][0] for e in events if e.get('object')==used0)
    return dict(seed=seed,position=pos,arm=arm,exposed=exposed,endpoint=bool(success),physical_endpoint=law.qualifies(s,arm),
                fuel=s[0],work=s[4],heat=law.heat(s,arm),post_loss_net_work=s[4]-pre[4],
                first_depletion=depleted,used_object0=used0,rebuilt_route=route,counts=counts,
                fresh_object_continuity=used0 is not None and used0==owners[0])


def audit(root,revision):
    root=Path(root)
    if json.loads((root/'manifest.json').read_bytes())!=dict(revision=revision,worlds=256,attempts=262144,founder_free=True):raise ValueError('Source/full panel manifest')
    rows=[]
    for pos in range(8):
        for repetition in range(8):
            seed=79000+8*pos+repetition
            for arm in ('candidate','affinity-ghost','catalysis-ghost','passive'):
                record=json.loads((root/f'{seed}-{arm}.json').read_bytes())
                if (record['seed'],record['position'],record['arm'])!=(seed,pos,arm):raise ValueError('Unscreened panel')
                rows.append(audit_record(record))
    success={a:sum(r['endpoint'] for r in rows if r['arm']==a) for a in ('candidate','affinity-ghost','catalysis-ghost','passive')}
    tests=[]
    for null in ('affinity-ghost','catalysis-ghost'):
        wins=losses=0
        for seed in range(79000,79064):
            a=next(r for r in rows if r['seed']==seed and r['arm']=='candidate');b=next(r for r in rows if r['seed']==seed and r['arm']==null)
            wins+=int(a['endpoint'] and not b['endpoint']);losses+=int(b['endpoint'] and not a['endpoint'])
        n=wins+losses;p=sum(comb(n,k) for k in range(wins,n+1))/2**n if n else 1.0
        tests.append(dict(null=null,wins=wins,losses=losses,p=p))
    ps=sorted(t['p'] for t in tests);passed=success['candidate']>=8 and ps[0]<=.025 and ps[1]<=.05
    totals={a:dict(exposed=sum(r['exposed'] for r in rows if r['arm']==a),depleted=sum(r['first_depletion'] is not None for r in rows if r['arm']==a),work_min=min(r['work'] for r in rows if r['arm']==a),work_max=max(r['work'] for r in rows if r['arm']==a),post_loss_work=sum(r['post_loss_net_work'] for r in rows if r['arm']==a),fuel_paid_rebuilt_uses=sum(r['rebuilt_route']==0 for r in rows if r['arm']==a),thermal_rebuilt_uses=sum(r['rebuilt_route']==1 for r in rows if r['arm']==a)) for a in success}
    return dict(verified=True,source_revision=revision,worlds=256,attempts=262144,founder_free=True,
                success=success,comparisons=tests,totals=totals,records=rows,primary_pass=passed,
                autonomous_self_maintenance=False,thermodynamic_efficiency_advantage=False,
                decision='PRIMARY PASS: independent disjoint reproduction required' if passed else 'PRIMARY FAIL: close tested law/1024 horizon')


def main():
    p=argparse.ArgumentParser();p.add_argument('--input',required=True);p.add_argument('--revision',required=True);a=p.parse_args()
    try:print(json.dumps(audit(a.input,a.revision),sort_keys=True))
    except (ValueError,KeyError,IndexError,TypeError) as e:
        print(json.dumps(dict(verified=False,error=str(e))));raise SystemExit(2)


if __name__=='__main__':main()
