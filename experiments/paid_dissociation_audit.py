"""Independent DISSOCIATE-01 authored feasibility interpreter; no worker imports."""
import argparse
import copy
import hashlib
import itertools
import json
from pathlib import Path
from experiments import startup_unscreened_audit as old

ROOT=Path(__file__).resolve().parents[1]
MODES=('candidate','irreversible','cut_ghost','product_ghost','association_off','supplied','food_withdrawn','external')
FILES=old.FILES+('docs/DISSOCIATE-01-PROTOCOL.md','experiments/paid_dissociation.py','experiments/paid_dissociation_audit.py')
def configurations():
    return [dict(word=''.join(bits),budget=budget,food_bit=food,mode=mode) for n in (2,3,4) for bits in itertools.product('01',repeat=n) for budget in (0,12,32) for food in ('0','1') for mode in MODES]
def sources(): return {f:hashlib.sha256((ROOT/f).read_bytes()).hexdigest() for f in FILES}
def lawmode(c): return {'product_ghost':'ghost','association_off':'association_off','supplied':'supplied','food_withdrawn':'food_withdrawn','external':'external'}.get(c['mode'],'active')
def genesis(c):
    s,_=old.genesis(dict(seed=0,mode=lawmode(c)))
    for a,v in s['atoms'].items(): v['bit']=c['food_bit'] if a.startswith('F') else '0'
    for i,bit in enumerate(c['word']): s['atoms'][f'M{4+i}']['bit']=bit
    s['reserve_work']+=s['bank'][c['budget']:]; s['bank']=s['bank'][:c['budget']]
    s['recycles']={f'M{i}':[] for i in range(24)}
    return s
def program(c):
    actions=[]
    if c['mode']!='supplied':
        actions.extend([(0,0),(2,0)])
        for i in (1,2,3): actions.extend([(0,i),(3,i),(0,i)])
        actions.append((4,0))
    actions.extend([(0,4),(2,4)])
    for i in range(5,4+len(c['word'])): actions.extend([(0,i),(3,i)])
    result=[(i,op,atom,'pre') for i,(op,atom) in enumerate(actions)]
    later=[(5,0),(5,0),(6,4)]
    for i in range(4,4+len(c['word'])):
        later.extend([(5,0),(5,0),(0,i),(2 if i==4 else 3,i)])
        if i>4: later.extend([(5,0),(5,0),(0,i)])
    later.extend([(4,4),(5,4)])
    result.extend((128+i,op,atom,'post') for i,(op,atom) in enumerate(later))
    assert len(result)<=64 and result[-1][0]<256
    return result
def request(s,c,op,atom,phase):
    ordered=sorted(s['chains'],key=lambda key:(-len(s['chains'][key]['atoms']),key))
    chain=ordered[0] if ordered else None
    products=sorted((key for key,v in s['history'].items() if v['kind']=='product' and v['origin']=='assembly'),key=lambda key:s['history'][key]['born'])
    founder='C' if c['mode']=='supplied' else products[0] if products else None
    target=[key for key in products if all(f'M{i}' in s['history'][key]['atoms'] for i in range(4,4+len(c['word'])))]
    actor=target[-1] if phase=='post' and op==5 and atom==4 and target else None if phase=='post' and op==5 and atom==4 else founder
    food=min(s['food'],key=lambda key:int(key[1:])) if s['food'] else 'F0'
    return dict(op=op,atom=f'M{atom}',food=food,chain=chain,actor=actor)
def transition(s,c,tick,q):
    op=q['op']; actor=q['actor']; chain=q['chain']; mode=lawmode(c)
    result=dict(outcome='unavailable',spent=[],created=[],heat=0,product=None,actor=actor)
    if op==6:
        if c['mode']=='irreversible': result['outcome']='disabled'; return result
        if chain not in s['chains']: return result
        value=s['chains'][chain]; n=len(value['atoms']); external=tick<128 or c['mode']=='external'
        account=s['bank'] if external else s['products'].get(actor,{}).get('work',[])
        if len(account)<n+1: result['outcome']='starved'; return result
        work=account[:n+1]; del account[:n+1]
        bonds=value['bonds'][:]; charge=[u for a in value['atoms'] for u in s['potential'][a]]
        delta=len(work)+len(bonds)+len(charge); s['heat']+=delta
        for a in value['atoms']: s['potential'][a]=[]
        key=f'D{tick}'; pool='spare' if c['mode']=='cut_ghost' else 'free'
        s[pool]+=value['atoms']; del s['chains'][chain]
        s['history'][key]=dict(kind='dismantled',origin='inert_cut' if pool=='spare' else 'paid_cut',atoms=value['atoms'][:],
            parents=[chain],born=tick,work_debits=work,bond_debits=bonds,charge_debits=charge,returned=pool=='free')
        for a in value['atoms']: s['recycles'][a].append(key)
        result.update(outcome='inert_cut' if pool=='spare' else 'cut',spent=work+bonds+charge,heat=delta,product=key)
        return result
    if op in (3,4) and chain not in s['chains']: return result
    if op==5 and actor not in s['products']: return result
    if op<2 and tick>=128 and mode!='external' and actor not in s['products']: return result
    ids=sorted(s['chains']); ps=sorted(s['products'])
    draw=[op,int(q['atom'][1:]),int(q['food'][1:]),ids.index(chain) if chain in ids else 0,ps.index(actor) if actor in ps else 0,0]
    result=old.transition(s,dict(seed=0,mode=mode),tick,draw); result['actor']=actor
    return result
def validate(s):
    old.validate(s)
    for atom,ancestors in s['recycles'].items():
        if len(ancestors)!=len(set(ancestors)) or any(key not in s['history'] or atom not in s['history'][key]['atoms'] or s['history'][key]['kind']!='dismantled' for key in ancestors): raise ValueError('Recycling provenance')
    for key,v in s['history'].items():
        if v['kind']=='dismantled' and len(v['work_debits'])!=len(v['atoms'])+1: raise ValueError('Full breakup price')
def metrics(r):
    s=r['terminal']; target={f'M{i}' for i in range(4,4+len(r['config']['word']))}
    cuts={key:v for key,v in s['history'].items() if v['kind']=='dismantled'}
    products={key:v for key,v in s['history'].items() if v['kind']=='product' and v['origin']=='assembly' and set(v['atoms'])==target}
    paid=[]
    for key,v in products.items():
        prior=[d for d,cut in cuts.items() if cut['returned'] and set(cut['atoms'])==target and cut['born']<v['born']]
        if prior and v['fully_capture_funded'] and all(s['units'][u]['origin']=='capture' for d in prior for u in cuts[d]['work_debits']): paid.append(key)
    probes={e['result']['actor'] for e in r['events'] if e['result']['outcome']=='captured' and e['tick']>=128}
    return dict(cases=1,cuts=sum(v['returned'] for v in cuts.values()),inert_cuts=sum(not v['returned'] for v in cuts.values()),
        cut_work=sum(len(v['work_debits']) for v in cuts.values()),cut_bond_heat=sum(len(v['bond_debits']) for v in cuts.values()),cut_charge_heat=sum(len(v['charge_debits']) for v in cuts.values()),
        reused_release=int(any(any(cut['returned'] and set(cut['atoms'])==target and cut['born']<v['born'] for cut in cuts.values()) for v in products.values())),
        fully_capture_paid_release=int(bool(paid)),fully_capture_paid_probe=int(bool(set(paid)&probes)),target_probe=int(bool(set(products)&probes)),
        founder_captures=sum(e['result']['outcome']=='captured' and e['result']['actor'] not in products for e in r['events']),
        final_heat=s['heat'],remaining_food=len(s['food']),events=len(r['events']))
def aggregate(records):
    totals={}
    for r in records:
        c=r['config']; key=f"{c['mode']}/{len(c['word'])}/{c['budget']}/{c['food_bit']}"; row=totals.setdefault(key,{})
        for field,value in metrics(r).items(): row[field]=row.get(field,0)+value
    return totals
def inspect(output,revision):
    output=Path(output); configs=configurations(); records=[]; h=hashlib.sha256()
    with (output/'records.jsonl').open('rb') as f:
        for i,raw in enumerate(f):
            if i>=len(configs) or not raw.endswith(b'\n'): raise ValueError('Panel size/LF')
            h.update(raw); r=old.decode(raw); c=configs[i]
            if old.canonical(r['config'])!=old.canonical(c): raise ValueError('Frozen authored configuration')
            s=genesis(c); validate(s); chain=old.digest(s)
            if old.canonical(r['initial'])!=old.canonical(s) or len(r['events'])!=len(program(c)): raise ValueError('Genesis/schedule')
            for event,(tick,op,atom,phase) in zip(r['events'],program(c)):
                q=request(s,c,op,atom,phase); before=old.digest(s); result=transition(s,c,tick,q); validate(s)
                expected=dict(tick=tick,request=q,before=before,after=old.digest(s),previous=chain,result=result); expected['sha256']=old.digest(expected)
                if old.canonical(event)!=old.canonical(expected): raise ValueError('Reaction/accounting/provenance divergence')
                chain=expected['sha256']
            if old.canonical(r['terminal'])!=old.canonical(s): raise ValueError('Terminal/recycling history')
            records.append(r)
    if len(records)!=1344: raise ValueError('Complete1344 cases')
    expected=dict(schema='dissociate01-summary-v1',revision=revision,sources=sources(),records_sha256=h.hexdigest(),cases=1344,events=sum(len(r['events']) for r in records),authored_feasibility_only=True,natural_worlds=0,totals=aggregate(records))
    if old.canonical(old.decode((output/'summary.json').read_bytes()))!=old.canonical(expected): raise ValueError('Summary/source/denominator')
    return dict(schema='dissociate01-audit-v1',cases=1344,events=expected['events'],zero_material_energy_residual=True,exact_semantic_replay=True,full_cut_formation_provenance_verified=True,authored_feasibility_only=True,natural_worlds=0,totals=expected['totals'],autonomous_origin_demonstrated=False)
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__); p.add_argument('--input-dir',required=True); p.add_argument('--source-revision',required=True); a=p.parse_args()
    try: print(json.dumps(inspect(a.input_dir,a.source_revision),indent=2,sort_keys=True))
    except (ValueError,OSError,KeyError,TypeError) as e: p.exit(2,f'Rejected DISSOCIATE-01: {e}\n')
