"""Finite RENEWAL-01 fresh diagnostic panel; unchanged STARTUP-02 physics."""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
from experiments import startup_unscreened as base

ROOT=Path(__file__).resolve().parents[1]
FILES=base.FILES+('docs/RENEWAL-01-PROTOCOL.md','experiments/renewal_opportunity.py','experiments/renewal_opportunity_audit.py')
def captured_charge(s,u):
    info=s['units'][u]
    return info['origin'] in ('activation','recharge') and len(info['parents'])==2 and all(s['units'][x]['origin']=='capture' for x in info['parents'])
def clean(s,units): return all(captured_charge(s,u) for u in units)

def measure(s,mode,t):
    free=s['free']; charges=s['potential']; cs=list(s['chains'].values()); ps=list(s['products'].values())
    access=free+[a for c in cs for a in c['atoms']]
    available_food=s['food'] if not(mode=='food_withdrawn' and t>=128) else []
    funded_cs=[c for c in cs if clean(s,c['debits'])]
    eligible=[a for a in free if len(charges[a])==3]
    funded_incoming=[a for a in eligible if clean(s,charges[a])]
    starts=[a for a in free if charges[a]] if mode!='association_off' else []
    pair_count=0; payers=0; captured_payers=0
    for p in ps:
        if len(p['work'])>=2:
            payers+=1
            if all(s['units'][u]['origin']=='capture' for u in p['work'][:2]):
                captured_payers+=1
                if len(p['atoms'])>=2:
                    bit=s['atoms'][p['atoms'][-1]]['bit']
                    pair_count+=len([f for f in available_food if s['atoms'][f]['bit']!=bit])
    affordable=0; funded_release=0
    for c in cs:
        local=sum([charges[a] for a in c['atoms']],[])
        if len(c['atoms'])>=2 and len(local)>=3:
            affordable+=1; funded_release+=int(clean(s,c['debits']+local[:3]))
    empty=len([a for a in access if not charges[a]])
    partial=len([a for a in access if len(charges[a]) in (1,2)])
    private=t>=128 and mode not in ('external','food_withdrawn')
    return dict(free_atoms=len(free),free_charged=len([a for a in free if charges[a]]),free_full=len(eligible),
        accessible_empty=empty,accessible_partial=partial,usable_food=len(available_food),products=len(ps),chains=len(cs),
        clean_chains=len(funded_cs),contaminated_chains=len(cs)-len(funded_cs),product_work=sum(len(p['work']) for p in ps),
        capture_work=sum(s['units'][u]['origin']=='capture' for p in ps for u in p['work']),payers=payers,capture_payers=captured_payers,
        capture_payer_food_pairs=pair_count,clean_starts=len([a for a in starts if captured_charge(s,charges[a][0])]),all_starts=len(starts),
        clean_extensions=len(funded_cs)*len(funded_incoming),all_extensions=len(cs)*len(eligible),clean_releases=funded_release,all_releases=affordable,
        capture_empty_requests=empty*pair_count if private else 0,capture_partial_requests=partial*pair_count if private and mode!='topup_off' else 0)

def outcome(s,e):
    r=e['result']; out=r['outcome']; answer='other'
    if out=='charged': answer='capture_paid_charge' if all(s['units'][u]['origin']=='capture' for u in r['spent']) else 'external_charge'
    elif out=='started': answer='clean_start' if clean(s,r['spent']) else 'contaminated_start'
    elif out in ('extended','released'):
        names=sorted(s['chains']); prior=s['chains'][names[e['draw'][3]%len(names)]]
        answer=('clean_' if clean(s,prior['debits']+r['spent']) else 'contaminated_')+('extension' if out=='extended' else 'release')
    elif out=='captured': answer='supplied_capture' if s['history'][r['actor']]['origin']=='supplied' else 'assembled_capture'
    return dict(kind=answer,post=e['tick']>=128)

def simulate(seed,mode):
    r=base.simulate(seed,mode); state,_=base.initial(seed,mode); observations=[]
    sums=Counter(); nonzero=Counter(); counts=Counter(); first=dict(clean_start=None,clean_extension=None,clean_release=None)
    for e in r['events']:
        t=e['tick']; row=dict(opportunities=measure(state,mode,t),selected=outcome(state,e)); observations.append(row)
        if t>=128:
            for k,v in row['opportunities'].items():
                sums[k]+=v
                if v: nonzero[k]+=1
        kind=row['selected']['kind']; counts[('pre/' if t<128 else 'post/')+kind]+=1
        if kind in first and first[kind] is None: first[kind]=t
        base.step(state,mode,t,e['draw'])
    r['observations']=observations
    r['diagnosis']=dict(post_opportunity_sums=dict(sums),post_nonzero_steps=dict(nonzero),selected=dict(counts),first_clean_ticks=first,**base.summarize([r])['totals'][mode])
    return r

def aggregate(records):
    rows={}
    for record in records:
        mode=record['config']['mode']; d=record['diagnosis']; row=rows.setdefault(mode,dict(worlds=0,totals={},post_opportunity_sums={},post_nonzero_steps={},selected={},worlds_with={}))
        row['worlds']+=1
        for key,value in d.items():
            if type(value) is int: row['totals'][key]=row['totals'].get(key,0)+value
        for group in ('post_opportunity_sums','post_nonzero_steps','selected'):
            for key,value in d[group].items(): row[group][key]=row[group].get(key,0)+value
        for key in ('clean_starts','clean_extensions','clean_releases','capture_empty_requests','capture_partial_requests'):
            row['worlds_with'][key]=row['worlds_with'].get(key,0)+int(d['post_opportunity_sums'][key]>0)
        clean_products={k for k,v in record['terminal']['history'].items() if v.get('fully_capture_funded')}
        probe=any(e['tick']>=128 and e['result']['outcome']=='captured' and e['result']['actor'] in clean_products for e in record['events'])
        row['worlds_with']['fully_capture_funded_probe']=row['worlds_with'].get('fully_capture_funded_probe',0)+int(probe)
    return rows

def run(output,revision):
    if len(revision)!=40 or any(c not in '0123456789abcdef' for c in revision): raise ValueError('Exact revision')
    output=Path(output); output.mkdir(parents=True,exist_ok=False); records=[]; checksum=hashlib.sha256()
    with (output/'records.jsonl').open('wb') as f:
        for seed in range(41000,41032):
            for mode in base.MODES:
                r=simulate(seed,mode); records.append(r); raw=(base.encode(r)+'\n').encode(); f.write(raw); checksum.update(raw)
    summary=dict(schema='renewal01-summary-v1',revision=revision,sources={f:hashlib.sha256((ROOT/f).read_bytes()).hexdigest() for f in FILES},records_sha256=checksum.hexdigest(),worlds=224,events=57344,independent_seed_blocks=32,totals=aggregate(records))
    (output/'summary.json').write_bytes((base.encode(summary)+'\n').encode()); return summary

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__); p.add_argument('--output-dir',required=True); p.add_argument('--source-revision',required=True); a=p.parse_args(); run(a.output_dir,a.source_revision)
