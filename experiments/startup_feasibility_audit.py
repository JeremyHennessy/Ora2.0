"""Independent STARTUP-01 interpreter: imports no worker or scientific kernel."""
import argparse
from collections import Counter
from copy import deepcopy
import hashlib
import itertools
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
FILES=('docs/STARTUP-01-PROTOCOL.md','experiments/startup_feasibility.py',
       'experiments/startup_feasibility_audit.py','docs/ENERGY-02-PROTOCOL.md',
       'experiments/precursor_coupling.py','experiments/precursor_coupling_audit.py',
       'docs/REACTIVATE-01-PROTOCOL.md','experiments/precursor_reactivation.py',
       'experiments/precursor_reactivation_audit.py')
MODES=('generic','template','ghost','association_off','topup_off','parent_release')

def text(v): return json.dumps(v,sort_keys=True,separators=(',',':'))
def digest(v): return hashlib.sha256(text(v).encode()).hexdigest()
def require(v,message):
    if not v: raise ValueError(message)
def unique(pairs):
    value={}
    for k,v in pairs:
        require(k not in value,'Duplicate JSON key')
        value[k]=v
    return value
def decode(raw): return json.loads(raw,object_pairs_hook=unique)

def panel():
    for n in range(2,5):
        for word in itertools.product('01',repeat=n):
            for mode in MODES:
                for b in (0,2*n,2*n+2):
                    for food in (0,1):
                        for renewal in ('external','withdrawn','food_withdrawn'):
                            yield dict(bits=''.join(word),mode=mode,budget=b,food_bit=str(food),renewal=renewal)

def schedule(c):
    n=len(c['bits'])
    for p in range(2):
        actor='C' if p==0 else 'D0'
        for i in range(n):
            for j in (2*i,2*i+1): yield ['harvest',p,actor,f'F{p}.{j}',None]
            yield ['activate',p,actor,f'M{p}.{i}',f'A{p}.{i}']
            yield ['recognize',p,actor,f'M{p}.{i}',None]
            yield ['bind',p,actor,None,None]
            if i==0:
                for j in (2*n,2*n+1): yield ['harvest',p,actor,f'F{p}.{j}',None]
                yield ['topup',p,actor,f'M{p}.0',f'Q{p}']
        yield ['release',p,actor,f'D{p}',None]
        yield ['probe',p,f'D{p}',f'P{p}',None]

def channel(): return dict(atoms=[],pending=None,bonds=[],debits=[])

def genesis(c):
    n=len(c['bits'])
    s=dict(atoms={},units={},objects={},history={},reserve=[],potential={},ready=[],food=[],waste=[],
           environment={},channels={'0':channel(),'1':channel()},heat=0,bond_reserve=n-1)
    bodies=['B'+str(i) for i in range(n)]
    for aid in bodies: s['atoms'][aid]=dict(bit='0',kind='reserve',root='environment_raw')
    if c['mode']=='template':
        s['objects']['C']=dict(bits='0'*n,atoms=bodies,work=[],bonds=[],supplied_bonds=n-1)
        s['history']['C']=dict(origin='supplied',parent=None,template=None,atoms=list(bodies),bits='0'*n,
                              born=-1,debits=[],endowment=[],components=[],captured_resource_funded=False)
    else: s['reserve']=bodies
    for p in range(2):
        for i,bit in enumerate(c['bits']):
            aid=f'M{p}.{i}'
            s['atoms'][aid]=dict(bit=bit,kind='precursor',root='environment_raw')
            s['potential'][aid]=[]
            s['ready'].append(aid)
        foods=[f'A{p}.{i}' for i in range(n)]+[f'Q{p}']+[f'F{p}.{i}' for i in range(2*n+2)]+[f'P{p}']
        for aid in foods: s['atoms'][aid]=dict(bit=c['food_bit'],kind='food',root='environment_raw')
        s['food'].extend(foods)
        s['environment'][str(p)]=[f'E{p}.{i}' for i in range(c['budget'])]
        for uid in s['environment'][str(p)]:
            s['units'][uid]=dict(origin='external',actor=f'environment{p}',food=None,parents=[],carrier=None,tick=-1)
    return s

def accounting(s,c):
    owners=s['reserve']+s['ready']+s['food']+s['waste']
    live=[]
    for obj in s['objects'].values():
        owners+=obj['atoms']; live+=obj['work']+obj['bonds']
        require(obj['bits']==''.join(s['atoms'][a]['bit'] for a in obj['atoms']),'Object bits')
        require(len(obj['work'])<=len(obj['atoms']),'Private capacity')
    for ch in s['channels'].values():
        owners+=ch['atoms']+([ch['pending']] if ch['pending'] else [])
        live+=ch['bonds']
        require(len(ch['bonds'])==max(0,len(ch['atoms'])-1),'Assembly bonds')
    for pool in s['potential'].values(): require(len(pool)<=3,'Local capacity'); live+=pool
    for pool in s['environment'].values(): live+=pool
    require(Counter(owners)==Counter(s['atoms']),'Mass identity/unique ownership')
    require(len(live)==len(set(live)) and all(u in s['units'] for u in live),'Energy ownership')
    initial=genesis(c)
    total=8*len(initial['food'])+2*c['budget']+len(c['bits'])-1
    require(8*len(s['food'])+len(live)+s['bond_reserve']+s['heat']==total,'Finite energy conservation')
    return total

def interpret(s,c,tick,q):
    s=deepcopy(s)
    action,p,actor,target,donor=q
    ch=s['channels'][str(p)]; obj=s['objects'].get(actor)
    r=dict(outcome='unavailable',spent=[],created=[],heat=0,product=None,endowment=[],bond=None)
    def spend(pool,k):
        taken=pool[:k]; del pool[:k]; r['spent']+=taken
        return taken
    def warm(k): s['heat']+=k; r['heat']+=k
    def food_ok(a): return a in s['food'] and not (p==1 and c['renewal']=='food_withdrawn')
    def affinity(a): return obj is not None and len(obj['bits'])>=2 and obj['bits'][-1]!=s['atoms'][a]['bit']
    def credit(k,origin,owner,food,parents,carrier):
        ids=[f'U{tick}.{i}' for i in range(k)]
        for uid in ids:
            require(uid not in s['units'],'Duplicate energy identity')
            s['units'][uid]=dict(origin=origin,actor=owner,food=food,parents=list(parents),carrier=carrier,tick=tick)
        r['created']=ids
        return ids
    if action in ('harvest','probe') and food_ok(target) and affinity(target):
        r['outcome']='starved'
        if len(obj['work'])>=2:
            paid=spend(obj['work'],2)
            s['food'].remove(target); s['waste'].append(target)
            made=credit(3,'capture',actor,target,paid,None)
            kept=min(3,len(obj['bits'])-len(obj['work']))
            obj['work']+=made[:kept]
            warm(7+3-kept); r['outcome']='captured'
    elif action in ('activate','topup'):
        bound=target in s['ready'] or any(target in x['atoms'] or target==x['pending'] for x in s['channels'].values())
        allowed=bound and target in s['potential'] and food_ok(donor)
        external=p==0 or c['renewal']=='external'
        pool=s['environment'][str(p)] if external else obj['work'] if obj else []
        allowed=allowed and (external or affinity(donor))
        charge=len(s['potential'].get(target,[]))
        if action=='topup' and c['mode']=='topup_off': r['outcome']='renewal_disabled'
        elif allowed and ((action=='activate' and charge==0) or action=='topup' and 0<charge<3):
            r['outcome']='starved'
            if len(pool)>=2:
                paid=spend(pool,2)
                s['food'].remove(donor); s['waste'].append(donor)
                quantity=3-charge
                ids=credit(quantity,'activation' if action=='activate' else 'topup',f'environment{p}' if external else actor,donor,paid,target)
                s['potential'][target]+=ids
                warm(10-quantity); r['outcome']='activated' if action=='activate' else 'recharged'
    elif action=='recognize' and ch['pending'] is None and len(ch['atoms'])<len(c['bits']) and target in s['ready']:
        matching=c['mode']!='template' or obj is not None and s['atoms'][target]['bit']==obj['bits'][len(ch['atoms'])]
        if s['potential'][target]:
            ch['debits']+=spend(s['potential'][target],1); warm(1)
            r['outcome']='association_disabled' if c['mode']=='association_off' else 'mismatch' if not matching else 'recognized'
            if matching and c['mode']!='association_off': s['ready'].remove(target); ch['pending']=target
        else: r['outcome']='starved'
    elif action=='bind' and ch['pending'] is not None:
        aid=ch['pending']; pool=s['potential'][aid]
        if ch['atoms'] and len(pool)<2: r['outcome']='starved'
        else:
            if ch['atoms']:
                paid=spend(pool,2); ch['debits']+=paid; ch['bonds'].append(paid[1]); r['bond']=paid[1]; warm(1)
            ch['atoms'].append(aid); ch['pending']=None; r['outcome']='bound'
    elif action=='release' and len(ch['atoms'])==len(c['bits']) and ch['pending'] is None:
        pending=[u for a in ch['atoms'] for u in s['potential'][a]]
        parent_release=c['mode']=='parent_release'
        enough=(obj is not None and len(obj['work'])>=1 and len(pending)>=2) if parent_release else len(pending)>=3
        r['outcome']='starved'
        if enough:
            release=spend(obj['work'],1) if parent_release else pending[:1]
            endowment=pending[:2] if parent_release else pending[1:3]
            for aid in ch['atoms']: s['potential'][aid]=[u for u in s['potential'][aid] if u not in release+endowment]
            if not parent_release: r['spent']+=release
            r['spent']+=endowment
            warm(1)
            debits=ch['debits']+release+endowment
            def own_resource(uid):
                meta=s['units'][uid]
                return meta['origin'] in ('activation','topup') and meta['actor']==actor and len(meta['parents'])==2 and all(s['units'][u]['origin']=='capture' and s['units'][u]['actor']==actor for u in meta['parents'])
            funded=all(own_resource(u) for u in debits)
            energy=[] if c['mode']=='ghost' else list(endowment)
            if c['mode']=='ghost': warm(2)
            bits=''.join(s['atoms'][a]['bit'] for a in ch['atoms'])
            components=[dict(atom=a,activation_units=[u for u,m in s['units'].items() if m['carrier']==a]) for a in ch['atoms']]
            s['history'][target]=dict(origin='ghost' if c['mode']=='ghost' else 'assembly',parent=actor if obj else None,
                                     template=actor if c['mode']=='template' else None,atoms=list(ch['atoms']),bits=bits,born=tick,
                                     debits=debits,endowment=list(energy),components=components,captured_resource_funded=funded)
            s['objects'][target]=dict(bits=bits,atoms=list(ch['atoms']),work=energy,bonds=list(ch['bonds']),supplied_bonds=0)
            s['channels'][str(p)]=channel()
            r.update(outcome='ghost_constructed' if c['mode']=='ghost' else 'constructed',product=target,endowment=energy)
    return s,r

def metrics(record):
    history=record['terminal']['history']; events=record['events']
    probes={e['request'][2] for e in events if e['request'][0]=='probe' and e['result']['outcome']=='captured'}
    return dict(cases=1,first_construction=int('D0' in history),first_function=int('D0' in probes),
                second_construction=int('D1' in history),second_function=int('D1' in probes),
                captured_resource_second=int('D1' in probes and history['D1']['captured_resource_funded']),
                terminal_heat=record['terminal']['heat'])

def inspect(record,c):
    require(set(record)=={'config','initial','events','terminal'},'Record schema')
    require(text(record['config'])==text(c),'Panel order/configuration')
    state=genesis(c); require(text(record['initial'])==text(state),'Genesis/scaffolding')
    chain=digest(state); expected=list(schedule(c))
    require(len(record['events'])==len(expected),'Event count')
    for tick,(event,q) in enumerate(zip(record['events'],expected)):
        require(set(event)=={'tick','request','before','after','previous','result','sha256'},'Event schema')
        require(event['tick']==tick and type(event['tick']) is int and event['request']==q,'Schedule')
        require(event['before']==digest(state) and event['previous']==chain,'Event prefix')
        state,result=interpret(state,c,tick,q); accounting(state,c)
        require(text(event['result'])==text(result) and event['after']==digest(state),'Independent reaction/provenance divergence')
        require(event['sha256']==digest({k:v for k,v in event.items() if k!='sha256'}),'Event hash')
        chain=event['sha256']
    require(text(record['terminal'])==text(state),'Terminal state/history')
    for key,birth in state['history'].items():
        if key!='C': require(len(birth['debits'])==3*len(c['bits'])+1,'Full formation price')
    return metrics(record)

def audit(directory,revision):
    directory=Path(directory)
    summary=decode((directory/'summary.json').read_bytes())
    hashes={name:hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in FILES}
    require(summary['revision']==revision and summary['source_sha256']==hashes,'Reviewed source')
    rows={}; total=Counter(); digestor=hashlib.sha256(); count=events=0
    with (directory/'records.jsonl').open('rb') as stream:
        for c in panel():
            raw=stream.readline(); require(raw.endswith(b'\n'),'Missing complete record')
            record=decode(raw); result=inspect(record,c); digestor.update(raw)
            key=f"n{len(c['bits'])}/{c['mode']}/b{c['budget']}/food{c['food_bit']}/{c['renewal']}"
            row=rows.setdefault(key,Counter()); row.update(result); total.update(result)
            count+=1; events+=len(record['events'])
        require(not stream.read(1),'Extra panel record')
    rows={k:dict(v) for k,v in rows.items()}
    expected=dict(schema='startup01-summary-v1',revision=revision,source_sha256=hashes,records_sha256=digestor.hexdigest(),
                  authored_cases=count,events=events,groups=rows,total=dict(total),natural_worlds=0,
                  reserved_samples_executed=False,reproduction_demonstrated=False)
    require(text(summary)==text(expected),'Summary/full-case aggregation')
    require(count==3024 and events==133920,'Frozen panel completeness')
    for key,row in rows.items():
        if any('/'+mode+'/' in key for mode in ('ghost','association_off','topup_off','parent_release')):
            require(row['first_function']==0,'Null control productive')
    return dict(schema='startup01-audit-v1',cases=count,events=events,groups=rows,total=dict(total),
                conservation=True,provenance=True,full_formation_price=True,independent_replay=True,
                natural_worlds=0,reproduction_claim=False)

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--input-dir',required=True); p.add_argument('--source-revision',required=True)
    args=p.parse_args()
    try: print(json.dumps(audit(args.input_dir,args.source_revision),sort_keys=True,indent=2))
    except (ValueError,OSError,KeyError,TypeError) as exc: p.exit(2,f'Rejected evidence: {exc}\n')
