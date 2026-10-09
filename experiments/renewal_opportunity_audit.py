"""Independent RENEWAL-01 opportunity interpreter; imports no worker."""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
from experiments import startup_unscreened_audit as physics

ROOT=Path(__file__).resolve().parents[1]
FILES=physics.FILES+('docs/RENEWAL-01-PROTOCOL.md','experiments/renewal_opportunity.py','experiments/renewal_opportunity_audit.py')
def sources(): return {f:hashlib.sha256((ROOT/f).read_bytes()).hexdigest() for f in FILES}
def configurations(): return [dict(seed=i,mode=m) for i in range(41000,41032) for m in physics.MODES]
def paid(s,u):
    v=s['units'][u]
    return v['origin'] in ('activation','recharge') and len(v['parents'])==2 and all(s['units'][p]['origin']=='capture' for p in v['parents'])

def opportunities(s,mode,tick):
    free=s['free']; chains=list(s['chains'].values()); products=list(s['products'].values())
    accessible=free+[a for c in chains for a in c['atoms']]
    food=[] if mode=='food_withdrawn' and tick>=128 else s['food']
    clean=[c for c in chains if all(paid(s,u) for u in c['debits'])]
    full=[a for a in free if len(s['potential'][a])==3]
    clean_full=[a for a in full if all(paid(s,u) for u in s['potential'][a])]
    start=[a for a in free if s['potential'][a]] if mode!='association_off' else []
    clean_start=[a for a in start if paid(s,s['potential'][a][0])]
    payers=[p for p in products if len(p['work'])>=2]
    capture_payers=[p for p in payers if all(s['units'][u]['origin']=='capture' for u in p['work'][:2])]
    pairs=sum(sum(s['atoms'][f]['bit']!=s['atoms'][p['atoms'][-1]]['bit'] for f in food) for p in capture_payers if len(p['atoms'])>=2)
    release=[]; clean_release=[]
    for c in chains:
        units=[u for a in c['atoms'] for u in s['potential'][a]]
        if len(c['atoms'])>=2 and len(units)>=3:
            release.append(c)
            if all(paid(s,u) for u in c['debits']+units[:3]): clean_release.append(c)
    empty=sum(len(s['potential'][a])==0 for a in accessible)
    partial=sum(0<len(s['potential'][a])<3 for a in accessible)
    available=tick>=128 and mode not in ('external','food_withdrawn')
    return dict(free_atoms=len(free),free_charged=len(start) if mode!='association_off' else sum(bool(s['potential'][a]) for a in free),
        free_full=len(full),accessible_empty=empty,accessible_partial=partial,usable_food=len(food),products=len(products),
        chains=len(chains),clean_chains=len(clean),contaminated_chains=len(chains)-len(clean),
        product_work=sum(len(p['work']) for p in products),capture_work=sum(s['units'][u]['origin']=='capture' for p in products for u in p['work']),
        payers=len(payers),capture_payers=len(capture_payers),capture_payer_food_pairs=pairs,
        clean_starts=len(clean_start),all_starts=len(start),clean_extensions=len(clean)*len(clean_full),all_extensions=len(chains)*len(full),
        clean_releases=len(clean_release),all_releases=len(release),
        capture_empty_requests=empty*pairs if available else 0,
        capture_partial_requests=partial*pairs if available and mode!='topup_off' else 0)

def selected(s,mode,tick,e):
    result=e['result']; action=e['draw'][0]; out=result['outcome']; kind='other'
    if out=='charged':
        kind='capture_paid_charge' if all(s['units'][u]['origin']=='capture' for u in result['spent']) else 'external_charge'
    elif out=='started': kind='clean_start' if all(paid(s,u) for u in result['spent']) else 'contaminated_start'
    elif out in ('extended','released'):
        cid=sorted(s['chains'])[e['draw'][3]%len(s['chains'])]
        is_clean=all(paid(s,u) for u in s['chains'][cid]['debits']+result['spent'])
        kind=('clean_' if is_clean else 'contaminated_')+('extension' if out=='extended' else 'release')
    elif out=='captured': kind='assembled_capture' if s['history'][result['actor']]['origin']=='assembly' else 'supplied_capture'
    return dict(kind=kind,post=tick>=128)

def summarize(record,observations):
    sums=Counter(); nonzero=Counter(); events=Counter(); first={k:None for k in ('clean_start','clean_extension','clean_release')}
    for tick,o in enumerate(observations):
        if tick>=128:
            sums.update(o['opportunities']); nonzero.update(k for k,v in o['opportunities'].items() if v)
        key=o['selected']['kind']; events[('post/' if tick>=128 else 'pre/')+key]+=1
        if key in first and first[key] is None: first[key]=tick
    return dict(post_opportunity_sums=dict(sums),post_nonzero_steps=dict(nonzero),selected=dict(events),first_clean_ticks=first,**physics.metrics(record))

def verify(record):
    base={k:record[k] for k in ('config','initial','events','terminal')}
    physics.verify_record(base,record['config'])
    s,rng=physics.genesis(record['config']); observations=[]
    for tick,e in enumerate(record['events']):
        observations.append(dict(opportunities=opportunities(s,record['config']['mode'],tick),selected=selected(s,record['config']['mode'],tick,e)))
        physics.transition(s,record['config'],tick,e['draw']); physics.validate(s)
    expected=summarize(base,observations)
    if physics.canonical(record['observations'])!=physics.canonical(observations) or physics.canonical(record['diagnosis'])!=physics.canonical(expected):
        raise ValueError('Opportunity/provenance/diagnosis mismatch')
    return expected

def aggregate(records):
    result={}
    for r in records:
        row=result.setdefault(r['config']['mode'],dict(worlds=0,totals={},post_opportunity_sums={},post_nonzero_steps={},selected={},worlds_with={}))
        d=r['diagnosis']; row['worlds']+=1
        for key,value in d.items():
            if type(value) is int: row['totals'][key]=row['totals'].get(key,0)+value
        for group in ('post_opportunity_sums','post_nonzero_steps','selected'):
            for key,value in d[group].items(): row[group][key]=row[group].get(key,0)+value
        for key in ('clean_starts','clean_extensions','clean_releases','capture_empty_requests','capture_partial_requests'):
            row['worlds_with'][key]=row['worlds_with'].get(key,0)+int(d['post_opportunity_sums'].get(key,0)>0)
        post_clean_probe=any(e['tick']>=128 and e['result']['outcome']=='captured' and e['result']['actor'] in r['terminal']['history'] and r['terminal']['history'][e['result']['actor']].get('fully_capture_funded') for e in r['events'])
        row['worlds_with']['fully_capture_funded_probe']=row['worlds_with'].get('fully_capture_funded_probe',0)+int(post_clean_probe)
    return result

def inspect(output,revision):
    output=Path(output); records=[]; checksum=hashlib.sha256(); configs=configurations()
    with (output/'records.jsonl').open('rb') as f:
        for index,raw in enumerate(f):
            if index>=224 or not raw.endswith(b'\n'): raise ValueError('Panel size/LF')
            r=physics.decode(raw); checksum.update(raw)
            if physics.canonical(r['config'])!=physics.canonical(configs[index]): raise ValueError('Fresh frozen sample order')
            verify(r); records.append(r)
    if len(records)!=224: raise ValueError('Incomplete panel')
    expected=dict(schema='renewal01-summary-v1',revision=revision,sources=sources(),records_sha256=checksum.hexdigest(),worlds=224,events=57344,independent_seed_blocks=32,totals=aggregate(records))
    summary=physics.decode((output/'summary.json').read_bytes())
    if physics.canonical(summary)!=physics.canonical(expected): raise ValueError('Summary/source/denominator')
    for mode in ('ghost','association_off'):
        if expected['totals'][mode]['totals']['assembled_captures']: raise ValueError('Null captures')
    if expected['totals']['food_withdrawn']['totals']['post_withdrawal_captures']: raise ValueError('Food withdrawal')
    return dict(schema='renewal01-audit-v1',worlds=224,events=57344,zero_material_energy_residual=True,exact_semantic_noise_replay=True,exact_opportunity_provenance_replay=True,totals=expected['totals'],autonomous_origin_demonstrated=False,reproduction_demonstrated=False)

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__); p.add_argument('--input-dir',required=True); p.add_argument('--source-revision',required=True); a=p.parse_args()
    try: print(json.dumps(inspect(a.input_dir,a.source_revision),indent=2,sort_keys=True))
    except (ValueError,OSError,KeyError,TypeError) as e: p.exit(2,f'Rejected RENEWAL-01: {e}\n')
