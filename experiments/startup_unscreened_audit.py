"""Independent STARTUP-02 interpreter/accounting; no worker imports."""
import argparse
import copy
import hashlib
import json
from pathlib import Path
import random
from collections import Counter

ROOT=Path(__file__).resolve().parents[1]
MODES=('active','external','ghost','association_off','topup_off','supplied','food_withdrawn')
FILES=('docs/STARTUP-02-PROTOCOL.md','experiments/startup_unscreened.py','experiments/startup_unscreened_audit.py',
       'docs/STARTUP-01-PROTOCOL.md','experiments/startup_feasibility.py','experiments/startup_feasibility_audit.py')
def canonical(v): return json.dumps(v,sort_keys=True,separators=(',',':'))
def digest(v): return hashlib.sha256(canonical(v).encode()).hexdigest()
def decode(raw):
    def pairs(items):
        result={}
        for k,v in items:
            if k in result: raise ValueError('Duplicate JSON key')
            result[k]=v
        return result
    return json.loads(raw,object_pairs_hook=pairs)
def sources(): return {f:hashlib.sha256((ROOT/f).read_bytes()).hexdigest() for f in FILES}
def configurations():
    return [dict(seed=seed,mode=mode) for seed in range(40000,40032) for mode in MODES]
def genesis(c):
    rng=random.Random(c['seed']); atoms={}
    for kind,prefix,count in (('raw','M',24),('food','F',64),('reserve','B',4)):
        for i in range(count): atoms[f'{prefix}{i}']=dict(bit=str(rng.randrange(2)),kind=kind)
    external=[f'E{i}' for i in range(64)]; reserve=[f'R{i}' for i in range(13)]
    units={u:dict(origin='external' if u[0]=='E' else 'reserve',actor='genesis',food=None,parents=[],carrier=None,tick=-1) for u in external+reserve}
    state=dict(atoms=atoms,units=units,free=[f'M{i}' for i in range(24)],potential={f'M{i}':[] for i in range(24)},
               food=[f'F{i}' for i in range(64)],waste=[],spare=[f'B{i}' for i in range(4)],reserve_work=reserve,
               bank=external,chains={},products={},history={},heat=0)
    if c['mode']=='supplied':
        value=dict(kind='product',origin='supplied',atoms=state['spare'][:],bonds=reserve[:3],debits=reserve[:],
                   parents=[],born=-1,endowment=reserve[3:5],fully_capture_funded=False,funders=[])
        state['history']['C']=value; state['products']['C']=dict(atoms=value['atoms'][:],bonds=value['bonds'][:],work=reserve[3:5])
        state['spare']=[]; state['reserve_work']=[]; state['heat']=8
    return state,rng
def validate(s):
    owners=s['free']+s['food']+s['waste']+s['spare']+[a for pool in (s['chains'],s['products']) for v in pool.values() for a in v['atoms']]
    if Counter(owners)!=Counter(s['atoms'].keys()): raise ValueError('Material identity/ownership')
    held=s['reserve_work']+s['bank']+[u for p in s['potential'].values() for u in p]
    held += [u for v in s['products'].values() for u in v['work']]
    bonds=[u for pool in (s['chains'],s['products']) for v in pool.values() for u in v['bonds']]
    if len(held+bonds)!=len(set(held+bonds)) or any(u not in s['units'] for u in held+bonds): raise ValueError('Energy ownership')
    if type(s['heat']) is not int or s['heat']<0 or len(held)+len(bonds)+8*len(s['food'])+s['heat']!=589: raise ValueError('Finite energy589')
    if any(len(v)>3 for v in s['potential'].values()) or any(len(v['work'])>len(v['atoms']) for v in s['products'].values()): raise ValueError('Local capacity')
    for uid,v in s['units'].items():
        if any(p not in s['units'] for p in v['parents']) or v['food'] is not None and v['food'] not in s['waste']: raise ValueError('Unit provenance')
    for oid,v in s['history'].items():
        if len(v['atoms'])!=len(set(v['atoms'])) or any(p not in s['history'] or s['history'][p]['born']>=v['born'] for p in v['parents']): raise ValueError('Structural ancestry')
        if v['kind']=='product' and len(v['debits'])!=3*len(v['atoms'])+1: raise ValueError('Full3n+1 debit')
    return True
def transition(s,c,tick,q):
    action,mi,fi,ci,pi,unused=q
    aid,food=f'M{mi%24}',f'F{fi%64}'
    chain_id=sorted(s['chains'])[ci%len(s['chains'])] if s['chains'] else None
    actor=sorted(s['products'])[pi%len(s['products'])] if s['products'] else None
    chain=s['chains'].get(chain_id); product=s['products'].get(actor)
    result=dict(outcome='unavailable',spent=[],created=[],heat=0,product=None,actor=actor)
    usable_food=food in s['food'] and not (tick>=128 and c['mode']=='food_withdrawn')
    complementary=product is not None and len(product['atoms'])>=2 and s['atoms'][product['atoms'][-1]]['bit']!=s['atoms'][food]['bit']
    def consume(pool,n):
        chosen=pool[:n]; del pool[:n]; result['spent']+=chosen; return chosen
    def thermal(n): s['heat']+=n; result['heat']+=n
    def generate(n,origin,who,parents,carrier):
        ids=[f'U{tick}.{i}' for i in range(n)]
        for uid in ids:
            if uid in s['units']: raise ValueError('Unit ID reuse')
            s['units'][uid]=dict(origin=origin,actor=who,food=food,parents=parents[:],carrier=carrier,tick=tick)
        result['created']=ids; return ids
    if action in (0,1):
        accessible=aid in s['free'] or any(aid in v['atoms'] for v in s['chains'].values())
        old_charge=len(s['potential'][aid]); external=tick<128 or c['mode']=='external'
        pool=s['bank'] if external else product['work'] if product else []
        if action==1 and c['mode']=='topup_off': result['outcome']='disabled'
        elif accessible and usable_food and (external or complementary) and (old_charge==0 if action==0 else 0<old_charge<3):
            if len(pool)<2: result['outcome']='starved'
            else:
                paid=consume(pool,2); s['food'].remove(food); s['waste'].append(food)
                count=3-old_charge; made=generate(count,'activation' if action==0 else 'recharge','environment' if external else actor,paid,aid)
                s['potential'][aid]+=made; thermal(10-count); result['outcome']='charged'
    elif action==2:
        if aid in s['free'] and s['potential'][aid]:
            paid=consume(s['potential'][aid],1); thermal(1)
            if c['mode']=='association_off': result['outcome']='disabled'
            else:
                s['free'].remove(aid); oid=f'C{tick}'
                value=dict(kind='chain',origin='assembly',atoms=[aid],bonds=[],debits=paid,parents=[],born=tick)
                s['chains'][oid]=copy.deepcopy(value); s['history'][oid]=copy.deepcopy(value); result['outcome']='started'
    elif action==3:
        if chain is not None and aid in s['free'] and len(s['potential'][aid])==3:
            paid=consume(s['potential'][aid],3); thermal(2); s['free'].remove(aid)
            oid=f'C{tick}'; value=dict(kind='chain',origin='assembly',atoms=chain['atoms']+[aid],bonds=chain['bonds']+[paid[2]],
                debits=chain['debits']+paid,parents=[chain_id],born=tick)
            del s['chains'][chain_id]; s['chains'][oid]=copy.deepcopy(value); s['history'][oid]=copy.deepcopy(value); result['outcome']='extended'
    elif action==4:
        local=[u for a in chain['atoms'] for u in s['potential'][a]] if chain else []
        if chain is not None and len(chain['atoms'])>=2 and len(local)>=3:
            paid=local[:3]; result['spent']=paid
            for a in chain['atoms']: s['potential'][a]=[u for u in s['potential'][a] if u not in paid]
            thermal(3 if c['mode']=='ghost' else 1); endowed=[] if c['mode']=='ghost' else paid[1:]
            debits=chain['debits']+paid
            def captured(u):
                v=s['units'][u]
                return v['origin'] in ('activation','recharge') and len(v['parents'])==2 and all(s['units'][p]['origin']=='capture' for p in v['parents'])
            oid=f'P{tick}'; value=dict(kind='product',origin='assembly',atoms=chain['atoms'][:],bonds=chain['bonds'][:],
                debits=debits,parents=[chain_id],born=tick,endowment=endowed[:],fully_capture_funded=all(captured(u) for u in debits),
                funders=sorted({s['units'][u]['actor'] for u in debits}))
            s['history'][oid]=value; s['products'][oid]=dict(atoms=value['atoms'][:],bonds=value['bonds'][:],work=endowed[:])
            del s['chains'][chain_id]; result.update(outcome='released',product=oid)
    elif action==5 and usable_food and complementary:
        if len(product['work'])<2: result['outcome']='starved'
        else:
            paid=consume(product['work'],2); s['food'].remove(food); s['waste'].append(food)
            made=generate(3,'capture',actor,paid,None); space=len(product['atoms'])-len(product['work'])
            product['work']+=made[:space]; thermal(7+max(0,3-space)); result['outcome']='captured'
    return result
def metrics(record):
    s=record['terminal']; births={k:v for k,v in s['history'].items() if v['kind']=='product' and v['origin']=='assembly'}
    captures=[e for e in record['events'] if e['result']['outcome']=='captured']; assembled=[e for e in captures if e['result']['actor'] in births]
    return dict(worlds=1,founder_free_success=int(record['config']['mode']!='supplied' and bool(assembled)),assemblies=len(births),
        assembled_captures=len(assembled),supplied_captures=len(captures)-len(assembled),
        post_withdrawal_captures=sum(e['tick']>=128 for e in assembled),
        fully_capture_funded_births=sum(v['fully_capture_funded'] and v['born']>=128 for v in births.values()),
        fully_capture_funded_probes=sum(e['tick']>=128 and births[e['result']['actor']]['fully_capture_funded'] for e in assembled),
        remaining_food=len(s['food']),waste=len(s['waste']),heat=s['heat'],unused_external=len(s['bank']))
def aggregate(records):
    totals={}; outcomes={}; lengths={}
    for r in records:
        mode=r['config']['mode']; tally=totals.setdefault(mode,{})
        for k,v in metrics(r).items(): tally[k]=tally.get(k,0)+v
        for e in r['events']:
            key=f"{mode}/{e['draw'][0]}/{e['result']['outcome']}"; outcomes[key]=outcomes.get(key,0)+1
        for v in r['terminal']['history'].values():
            if v['kind']=='product' and v['origin']=='assembly':
                key=f"{mode}/{len(v['atoms'])}"; lengths[key]=lengths.get(key,0)+1
    return dict(totals=totals,outcomes=outcomes,assembly_lengths=lengths)
def verify_record(record,config):
    if canonical(record['config'])!=canonical(config) or len(record['events'])!=256: raise ValueError('Frozen sample/horizon')
    state,rng=genesis(config); validate(state)
    if canonical(record['initial'])!=canonical(state): raise ValueError('Genesis')
    chain=digest(state)
    for tick,e in enumerate(record['events']):
        draw=[rng.randrange(6)]+[rng.randrange(65536) for _ in range(5)]
        before=digest(state); result=transition(state,config,tick,draw); validate(state)
        expected=dict(tick=tick,draw=draw,before=before,after=digest(state),previous=chain,result=result)
        expected['sha256']=digest(expected)
        if canonical(e)!=canonical(expected): raise ValueError('Reaction/noise/accounting divergence')
        chain=expected['sha256']
    if canonical(record['terminal'])!=canonical(state): raise ValueError('Terminal/history/provenance')
    return metrics(record)
def inspect(output,revision):
    output=Path(output); summary=decode((output/'summary.json').read_bytes())
    if summary['revision']!=revision or summary['sources']!=sources(): raise ValueError('Source identity')
    checksum=hashlib.sha256(); records=[]; configs=configurations()
    with (output/'records.jsonl').open('rb') as f:
        for index,raw in enumerate(f):
            if index>=224 or not raw.endswith(b'\n'): raise ValueError('Panel size/LF')
            checksum.update(raw); r=decode(raw); verify_record(r,configs[index]); records.append(r)
    if len(records)!=224: raise ValueError('Complete224 worlds')
    expected=dict(schema='startup02-summary-v1',revision=revision,sources=sources(),records_sha256=checksum.hexdigest(),
                  worlds=224,events=57344,independent_seed_blocks=32,reserved_samples_executed=False,**aggregate(records))
    if canonical(summary)!=canonical(expected): raise ValueError('Summary/denominator')
    for mode in ('ghost','association_off'):
        if expected['totals'][mode]['assembled_captures']: raise ValueError('Inert/association control')
    return dict(schema='startup02-audit-v1',worlds=224,events=57344,independent_seed_blocks=32,zero_material_energy_residual=True,
                exact_semantic_noise_replay=True,**aggregate(records),autonomous_origin_demonstrated=False,reproduction_demonstrated=False)
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__); p.add_argument('--input-dir',required=True); p.add_argument('--source-revision',required=True); a=p.parse_args()
    try: print(json.dumps(inspect(a.input_dir,a.source_revision),indent=2,sort_keys=True))
    except (ValueError,OSError,KeyError,TypeError) as e: p.exit(2,f'Rejected STARTUP-02: {e}\n')
