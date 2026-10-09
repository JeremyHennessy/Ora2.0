"""Separate FUEL-01 interpreter; never imports the producer."""
import argparse,json,math
from pathlib import Path

MODES=('candidate','inert','shuffled','fuel-withdrawn')
def audit_record(r):
    seed,mode=r['seed'],r['arm']
    if seed not in (*range(76000,76032),76999) or mode not in MODES:raise ValueError('Sample')
    objects=[dict(id=a,atoms=[a],active=False,fuel=None,alive=True,parents=[],born=0,route='genesis') for a in range(24)]
    fuel=[0 for _ in range(96)];heat=0;random_state=seed;depleted=None
    counters=dict(activation=0,formation=0,cleavage=0,causal=0,reused=0,post_withdrawal=0)
    if len(r['trace'])!=4096 or r['cursor']!=24576:raise ValueError('Horizon/cursor')
    for t,(draws,actual) in enumerate(r['trace']):
        requested=[]
        for unused in range(6):
            random_state=((random_state ^ ((random_state*8192)&4294967295)))
            random_state^=random_state//131072
            random_state^=(random_state*32)&4294967295
            random_state&=4294967295;requested.append(random_state)
        if requested!=draws:raise ValueError('Random stream')
        if mode=='fuel-withdrawn' and t==2048:fuel=[2 if a==0 else a for a in fuel]
        ids=[i for i,o in enumerate(objects) if o['alive']]
        first,second,third=[ids[draws[j]%len(ids)] for j in (1,2,3)]
        a,b,c=objects[first],objects[second],objects[third];chosen=draws[4]%96;byte=draws[5]%256;reaction=draws[0]%3;expected=None
        if reaction==0 and len(a['atoms'])==1 and not a['active'] and fuel[chosen]==0:
            target=(sum(v%4 for v in c['atoms'])+(1 if mode=='shuffled' else 0))%4
            catalytic=mode!='inert' and len(c['atoms'])==2 and target==a['atoms'][0]%4
            threshold=128 if catalytic else 16
            if byte<threshold:
                fuel[chosen]=1;a.update(active=True,fuel=chosen);heat+=2;counters['activation']+=1
                if catalytic and byte>=16:counters['causal']+=1
                expected=['activate',first,chosen,third if catalytic else None]
        elif reaction==1 and first!=second and len(a['atoms'])==1 and len(b['atoms'])==1 and a['active'] and not b['active']:
            a['alive']=False;b['alive']=False;new_id=len(objects)
            objects.append(dict(id=new_id,atoms=sorted(a['atoms']+b['atoms']),active=False,fuel=a['fuel'],alive=True,parents=[first,second],born=t,route='form'))
            heat+=1;counters['formation']+=1
            if 'cleave' in (a['route'],b['route']):counters['reused']+=1
            if mode=='fuel-withdrawn' and t>=2048:counters['post_withdrawal']+=1
            expected=['form',first,second,new_id]
        elif reaction==2 and len(a['atoms'])==2 and byte<8:
            a['alive']=False;start=len(objects)
            for atom in a['atoms']:
                objects.append(dict(id=len(objects),atoms=[atom],active=False,fuel=None,alive=True,parents=[first],born=t,route='cleave'))
            heat+=1;counters['cleavage']+=1;expected=['cleave',first,start,start+1]
        if actual!=expected:raise ValueError('Reaction/cost/ancestry')
        living=[o for o in objects if o['alive']]
        if sorted(v for o in living for v in o['atoms'])!=list(range(24)):raise ValueError('Mass')
        energy=4*sum(f in (0,2) for f in fuel)+heat+sum(2 if o['active'] else len(o['atoms'])-1 for o in living)
        if energy!=384:raise ValueError('Energy')
        if depleted is None and 0 not in fuel:depleted=t
    final=dict(seed=seed,arm=mode,rng=random_state,step=4096,heat=heat,food=fuel,objects=objects,stats=counters,depleted_at=depleted)
    if r['final']!=final:raise ValueError('Complete state/provenance')
    dimers=sum(o['alive'] and len(o['atoms'])==2 for o in objects)
    opportunity=dimers>=3 and counters['activation']>=8 and counters['formation']>=8
    if r['live_dimers']!=dimers or r['opportunity']!=opportunity:raise ValueError('Endpoint')
    return dict(seed=seed,arm=mode,opportunity=opportunity,live_dimers=dimers,remaining_fuel=fuel.count(0),reserved_fuel=fuel.count(2),active_singles=sum(o['alive'] and o['active'] for o in objects),depleted_at=depleted,**counters)
def binomial(wins,losses):
    n=wins+losses
    return sum(math.comb(n,k) for k in range(wins,n+1))/2**n if n else 1.0
def panel(root,revision):
    root=Path(root);manifest=json.loads((root/'manifest.json').read_bytes())
    if manifest!=dict(revision=revision,seeds=list(range(76000,76032)),arms=list(MODES),worlds=128,attempts=524288):raise ValueError('Manifest')
    expected={'manifest.json'}|{f'{s}-{m}.json' for s in range(76000,76032) for m in MODES}
    if {p.name for p in root.iterdir()}!=expected:raise ValueError('Panel coverage')
    records=[audit_record(json.loads((root/f'{s}-{m}.json').read_bytes())) for s in range(76000,76032) for m in MODES]
    counts={m:sum(x['opportunity'] for x in records if x['arm']==m) for m in MODES};comparisons={}
    lookup={(r['seed'],r['arm']):r['opportunity'] for r in records}
    for null in ('inert','shuffled'):
        pairs=[(lookup[s,'candidate'],lookup[s,null]) for s in range(76000,76032)]
        wins=sum(a and not b for a,b in pairs);losses=sum(b and not a for a,b in pairs)
        comparisons[null]=dict(wins=wins,losses=losses,p=binomial(wins,losses))
    ps=sorted(v['p'] for v in comparisons.values());passed=counts['candidate']>=16 and ps[0]<=.025 and ps[1]<=.05
    totals={m:{key:sum(r[key] for r in records if r['arm']==m) for key in ('activation','formation','cleavage','causal','reused','post_withdrawal')} for m in MODES}
    return dict(source_revision=revision,worlds=128,attempts=524288,opportunity=counts,comparisons=comparisons,gate_pass=passed,totals=totals,records=records,classification='OPPORTUNITY GATE PASS' if passed else 'OPPORTUNITY GATE FAIL',self_maintenance_demonstrated=False)
def main():
    p=argparse.ArgumentParser();p.add_argument('--input',required=True);p.add_argument('--revision',required=True);a=p.parse_args()
    try:print(json.dumps(panel(a.input,a.revision),sort_keys=True))
    except (ValueError,KeyError,IndexError,TypeError) as e:print(str(e));raise SystemExit(2)
if __name__=='__main__':main()
