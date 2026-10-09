"""Independent RATCHET-02 interpreter; no producer import."""
import argparse
import hashlib
import itertools
import json
from math import comb
from pathlib import Path
import random
import struct
from .ratchet_audit import proposals, energy_heat, qualifies


def canonical(value):
    return json.dumps(value,sort_keys=True,separators=(',',':')).encode()


def audit_record(r):
    seed,arm,barriers = r['seed'],r['arm'],r['barriers']
    if arm not in ('candidate','uncoupled','isotropic','equilibrium') or len(barriers)!=3 or any(b not in range(4) for b in barriers):
        raise ValueError('Arm/barrier registration')
    generator = random.Random(seed);digest = hashlib.sha256()
    s = (16,0,10,0);states = [list(s)+[energy_heat(s)]]
    tokens = [dict(id=i,state='F',transformations=[]) for i in range(16)]
    objects = [dict(id=0,atoms=[0,1,2],parent=None,construction_work=6,alive=True)]
    steps,actions,events = [],[],[]
    paused = False;before = None;depletion = None
    for tick in range(4096):
        if tick == 2048:
            before = list(s)+[energy_heat(s)]
            if s[2]<7:
                paused = True
            else:
                s = (s[0],0,s[2]-7,1)
                objects[0]['alive'] = False
                objects.append(dict(id=1,atoms=[0,1,2],parent=0,construction_work=6,destruction_work=1,alive=True))
                actions.append([5,1]);steps.append(tick)
                events.append(dict(action=[5,1],token=None,machine=1));states.append(list(s)+[energy_heat(s)])
        channel = generator.randrange(5);forward = generator.getrandbits(1)
        selected = generator.getrandbits(4);u = generator.getrandbits(32)
        digest.update(struct.pack('<IIII',channel,forward,selected,u));direction = 2*forward-1
        if paused:
            continue
        mapping = dict(proposals(s,arm));action = (channel,direction)
        if action not in mapping:
            continue
        chemical = channel in (0,4)
        old_type = 'F' if forward else 'W'
        if chemical and tokens[selected]['state'] != old_type:
            continue
        t = mapping[action]
        b = barriers[0 if chemical else 2 if channel==2 else 1]+int(chemical and arm=='isotropic')
        loss = max(0,energy_heat(s)-energy_heat(t))
        if not 0 <= b+loss <= 32:
            raise ValueError('Rate resolution')
        if u >= 2**(32-b-loss):
            continue
        if chemical:
            tokens[selected]['state'] = 'W' if forward else 'F'
            tokens[selected]['transformations'].append(dict(event=len(actions),machine=objects[-1]['id'],route=list(action)))
        actions.append(list(action));steps.append(tick)
        events.append(dict(action=list(action),token=selected if chemical else None,machine=objects[-1]['id']))
        s = t;states.append(list(s)+[energy_heat(s)])
        if depletion is None and s[0]==0:
            depletion = tick
        if sum(t['state']=='F' for t in tokens)!=s[0] or 6*s[0]+s[2]+int(s[1]==1)+2+energy_heat(s)!=144:
            raise ValueError('Every-event energy/material ledger')
    final = dict(path=actions,snapshots=states,events=events,objects=objects,tokens=tokens,
                 total_energy=144,structural_atoms=[0,1,2],initial_work=16,initial_heat=32,
                 startup_work=6,replacement_work=7 if s[3] else 0,endpoint=qualifies(s))
    expected = dict(schema='ratchet02',seed=seed,arm=arm,barriers=barriers,attempts=4096,event_steps=steps,
                    draw_sha256=digest.hexdigest(),rng_sha256=hashlib.sha256(canonical(generator.getstate())).hexdigest(),
                    pre_replace=before,stopped_unfunded=paused,first_depletion=depletion,final=final)
    if r != expected:
        raise ValueError('Complete random dynamics/ledger/provenance mismatch')
    counts = {str(c):dict(forward=sum(a==[c,1] for a in actions),reverse=sum(a==[c,-1] for a in actions)) for c in range(5)}
    return dict(seed=seed,arm=arm,barriers=barriers,endpoint=qualifies(s),funded=not paused,
                fuel=s[0],work=s[2],heat=energy_heat(s),conformation=s[1],counts=counts,
                pre_replace=before,first_depletion=depletion)


def audit(root,revision):
    root = Path(root)
    if json.loads((root/'manifest.json').read_bytes())!=dict(revision=revision,worlds=256,attempts=1048576,founder_free=False):
        raise ValueError('Frozen panel manifest')
    rows=[]
    for i,barriers in enumerate(itertools.product(range(4),repeat=3)):
        for arm in ('candidate','uncoupled','isotropic','equilibrium'):
            record=json.loads((root/f'{78000+i}-{arm}.json').read_bytes())
            if (record['seed'],record['arm'],record['barriers'])!=(78000+i,arm,list(barriers)):
                raise ValueError('Unscreened catalogue completeness')
            rows.append(audit_record(record))
    success={arm:sum(r['endpoint'] for r in rows if r['arm']==arm) for arm in ('candidate','uncoupled','isotropic','equilibrium')}
    tests=[]
    for null in ('uncoupled','isotropic'):
        pairs=[([r for r in rows if r['seed']==seed and r['arm']=='candidate'][0], [r for r in rows if r['seed']==seed and r['arm']==null][0]) for seed in range(78000,78064)]
        wins=sum(a['endpoint'] and not b['endpoint'] for a,b in pairs);losses=sum(b['endpoint'] and not a['endpoint'] for a,b in pairs);n=wins+losses
        probability=sum(comb(n,k) for k in range(wins,n+1))/2**n if n else 1.0
        tests.append(dict(null=null,wins=wins,losses=losses,p=probability))
    ordered=sorted(tests,key=lambda t:t['p']);passed=success['candidate']>=8 and ordered[0]['p']<=.025 and ordered[1]['p']<=.05
    totals={arm:dict(funded=sum(r['funded'] for r in rows if r['arm']==arm),depleted=sum(r['first_depletion'] is not None for r in rows if r['arm']==arm),work_min=min(r['work'] for r in rows if r['arm']==arm),work_max=max(r['work'] for r in rows if r['arm']==arm),fuel_min=min(r['fuel'] for r in rows if r['arm']==arm),fuel_max=max(r['fuel'] for r in rows if r['arm']==arm)) for arm in success}
    return dict(verified=True,source_revision=revision,worlds=256,attempts=1048576,founder_free=False,
                success=success,comparisons=tests,totals=totals,records=rows,primary_pass=passed,
                autonomous_self_maintenance=False,decision='PRIMARY PASS: disjoint reproduction required' if passed else 'PRIMARY FAIL: close tested finite law/horizon')


def main():
    p=argparse.ArgumentParser();p.add_argument('--input',required=True);p.add_argument('--revision',required=True);a=p.parse_args()
    try:print(json.dumps(audit(a.input,a.revision),sort_keys=True))
    except (ValueError,KeyError,IndexError,TypeError) as e:
        print(json.dumps(dict(verified=False,error=str(e))));raise SystemExit(2)


if __name__=='__main__':main()
