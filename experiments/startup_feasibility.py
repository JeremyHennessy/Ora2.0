"""STARTUP-01 separate authored generic association candidate; no natural worlds."""
import argparse
import copy
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
def encode(v): return json.dumps(v,sort_keys=True,separators=(',',':'))
def sha(v): return hashlib.sha256(encode(v).encode()).hexdigest()
def configs():
    for n in (2,3,4):
        for bits in itertools.product('01',repeat=n):
            for mode,budget,food,renewal in itertools.product(MODES,(0,2*n,2*n+2),'01',('external','withdrawn','food_withdrawn')):
                yield dict(bits=''.join(bits),mode=mode,budget=budget,food_bit=food,renewal=renewal)
def empty(): return dict(atoms=[],pending=None,bonds=[],debits=[])
def initial(c):
    n=len(c['bits'])
    s=dict(atoms={},units={},objects={},history={},reserve=[],potential={},ready=[],food=[],waste=[],
           environment={},channels={str(p):empty() for p in range(2)},heat=0,bond_reserve=n-1)
    body=[f'B{i}' for i in range(n)]
    for aid in body: s['atoms'][aid]=dict(bit='0',kind='reserve',root='environment_raw')
    if c['mode']=='template':
        s['objects']['C']=dict(bits='0'*n,atoms=body,work=[],bonds=[],supplied_bonds=n-1)
        s['history']['C']=dict(origin='supplied',parent=None,template=None,atoms=list(body),bits='0'*n,
                              born=-1,debits=[],endowment=[],components=[],captured_resource_funded=False)
    else: s['reserve']=body
    for p in (0,1):
        for i,bit in enumerate(c['bits']):
            aid=f'M{p}.{i}'; s['atoms'][aid]=dict(bit=bit,kind='precursor',root='environment_raw')
            s['potential'][aid]=[]; s['ready'].append(aid)
        foods=[f'A{p}.{i}' for i in range(n)]+[f'Q{p}']+[f'F{p}.{i}' for i in range(2*n+2)]+[f'P{p}']
        for aid in foods: s['atoms'][aid]=dict(bit=c['food_bit'],kind='food',root='environment_raw')
        s['food'].extend(foods)
        bank=[f'E{p}.{i}' for i in range(c['budget'])]; s['environment'][str(p)]=bank
        for uid in bank: s['units'][uid]=dict(origin='external',actor=f'environment{p}',food=None,parents=[],carrier=None,tick=-1)
    return s
def requests(c):
    n=len(c['bits'])
    for p in (0,1):
        actor='C' if p==0 else 'D0'
        for i in range(n):
            yield ['harvest',p,actor,f'F{p}.{2*i}',None]
            yield ['harvest',p,actor,f'F{p}.{2*i+1}',None]
            yield ['activate',p,actor,f'M{p}.{i}',f'A{p}.{i}']
            yield ['recognize',p,actor,f'M{p}.{i}',None]
            yield ['bind',p,actor,None,None]
            if i==0:
                yield ['harvest',p,actor,f'F{p}.{2*n}',None]
                yield ['harvest',p,actor,f'F{p}.{2*n+1}',None]
                yield ['topup',p,actor,f'M{p}.0',f'Q{p}']
        yield ['release',p,actor,f'D{p}',None]
        yield ['probe',p,f'D{p}',f'P{p}',None]

def step(old,c,tick,q):
    s=copy.deepcopy(old)
    action,p,actor,target,donor=q
    obj=s['objects'].get(actor); ch=s['channels'][str(p)]
    r=dict(outcome='unavailable',spent=[],created=[],heat=0,product=None,endowment=[],bond=None)
    def take(pool,n):
        ids=pool[:n]; del pool[:n]; r['spent'].extend(ids); return ids
    def heat(n): s['heat']+=n; r['heat']+=n
    def available(food): return food in s['food'] and not (p==1 and c['renewal']=='food_withdrawn')
    def complement(food): return obj is not None and len(obj['bits'])>=2 and obj['bits'][-1]!=s['atoms'][food]['bit']
    def make(count,origin,who,food,paid,carrier):
        ids=[f'U{tick}.{j}' for j in range(count)]
        for uid in ids:
            if uid in s['units']: raise ValueError('Repeated energy ID')
            s['units'][uid]=dict(origin=origin,actor=who,food=food,parents=list(paid),carrier=carrier,tick=tick)
        r['created']=ids; return ids
    if action=='harvest' or action=='probe':
        if available(target) and complement(target):
            if len(obj['work'])<2: r['outcome']='starved'
            else:
                paid=take(obj['work'],2); s['food'].remove(target); s['waste'].append(target)
                made=make(3,'capture',actor,target,paid,None)
                free=len(obj['bits'])-len(obj['work']); kept=made[:free]
                obj['work'].extend(kept); heat(7+len(made)-len(kept)); r['outcome']='captured'
    elif action in ('activate','topup'):
        accessible=target in s['ready'] or any(target in x['atoms'] or target==x['pending'] for x in s['channels'].values())
        external=p==0 or c['renewal']=='external'
        pool=s['environment'][str(p)] if external else obj['work'] if obj else []
        charge=len(s['potential'].get(target,[]))
        suitable=accessible and target in s['potential'] and available(donor) and (external or complement(donor))
        if action=='topup' and c['mode']=='topup_off': r['outcome']='renewal_disabled'
        elif suitable and (charge==0 if action=='activate' else 0<charge<3):
            if len(pool)<2: r['outcome']='starved'
            else:
                paid=take(pool,2); s['food'].remove(donor); s['waste'].append(donor)
                count=3-charge
                s['potential'][target].extend(make(count,'activation' if action=='activate' else 'topup',f'environment{p}' if external else actor,donor,paid,target))
                heat(10-count); r['outcome']='activated' if action=='activate' else 'recharged'
    elif action=='recognize':
        if ch['pending'] is None and len(ch['atoms'])<len(c['bits']) and target in s['ready']:
            if s['potential'][target]:
                ch['debits'].extend(take(s['potential'][target],1)); heat(1)
                matches=c['mode']!='template' or obj is not None and s['atoms'][target]['bit']==obj['bits'][len(ch['atoms'])]
                if c['mode']=='association_off': r['outcome']='association_disabled'
                elif not matches: r['outcome']='mismatch'
                else: ch['pending']=target; s['ready'].remove(target); r['outcome']='recognized'
            else: r['outcome']='starved'
    elif action=='bind' and ch['pending'] is not None:
        aid=ch['pending']
        if ch['atoms'] and len(s['potential'][aid])<2: r['outcome']='starved'
        else:
            if ch['atoms']:
                used=take(s['potential'][aid],2); ch['debits'].extend(used); ch['bonds'].append(used[1]); r['bond']=used[1]; heat(1)
            ch['atoms'].append(aid); ch['pending']=None; r['outcome']='bound'
    elif action=='release' and ch['pending'] is None and len(ch['atoms'])==len(c['bits']):
        local=[u for a in ch['atoms'] for u in s['potential'][a]]
        parent=c['mode']=='parent_release'
        funded=obj is not None and len(obj['work'])>=1 and len(local)>=2 if parent else len(local)>=3
        if not funded: r['outcome']='starved'
        else:
            release=take(obj['work'],1) if parent else local[:1]
            endowed=local[:2] if parent else local[1:3]
            for a in ch['atoms']: s['potential'][a]=[u for u in s['potential'][a] if u not in release+endowed]
            if not parent: r['spent'].extend(release)
            r['spent'].extend(endowed); heat(1)
            debits=ch['debits']+release+endowed
            def captured(uid):
                unit=s['units'][uid]
                return unit['origin'] in ('activation','topup') and unit['actor']==actor and len(unit['parents'])==2 and all(s['units'][u]['origin']=='capture' and s['units'][u]['actor']==actor for u in unit['parents'])
            bits=''.join(s['atoms'][a]['bit'] for a in ch['atoms'])
            work=[] if c['mode']=='ghost' else list(endowed)
            if c['mode']=='ghost': heat(2)
            birth=dict(origin='ghost' if c['mode']=='ghost' else 'assembly',parent=actor if obj else None,
                       template=actor if c['mode']=='template' else None,atoms=list(ch['atoms']),bits=bits,born=tick,
                       debits=debits,endowment=list(work),
                       components=[dict(atom=a,activation_units=[u for u,m in s['units'].items() if m['carrier']==a]) for a in ch['atoms']],
                       captured_resource_funded=all(captured(u) for u in debits))
            s['history'][target]=birth
            s['objects'][target]=dict(bits=bits,atoms=list(ch['atoms']),work=work,bonds=list(ch['bonds']),supplied_bonds=0)
            s['channels'][str(p)]=empty()
            r.update(outcome='ghost_constructed' if c['mode']=='ghost' else 'constructed',product=target,endowment=work)
    return s,r

def simulate(c):
    state=initial(c); start=copy.deepcopy(state); chain=sha(state); events=[]
    for tick,q in enumerate(requests(c)):
        before=sha(state); state,result=step(state,c,tick,q)
        event=dict(tick=tick,request=q,before=before,after=sha(state),previous=chain,result=result)
        event['sha256']=sha(event); chain=event['sha256']; events.append(event)
    return dict(config=c,initial=start,events=events,terminal=state)
def counts(record):
    births=record['terminal']['history']; probes=[]
    for event in record['events']:
        if event['request'][0]=='probe' and event['result']['outcome']=='captured': probes.append(event['request'][2])
    return dict(cases=1,first_construction=int('D0' in births),first_function=int('D0' in probes),
                second_construction=int('D1' in births),second_function=int('D1' in probes),
                captured_resource_second=int('D1' in probes and births['D1']['captured_resource_funded']),
                terminal_heat=record['terminal']['heat'])
def run(output,revision):
    if len(revision)!=40 or any(x not in '0123456789abcdef' for x in revision): raise ValueError('Exact revision required')
    output=Path(output); output.mkdir(parents=True,exist_ok=False)
    groups={}; total={}; rows=events=0; checksum=hashlib.sha256()
    with (output/'records.jsonl').open('wb') as stream:
        for c in configs():
            record=simulate(c); raw=(encode(record)+'\n').encode(); stream.write(raw); checksum.update(raw)
            key=f"n{len(c['bits'])}/{c['mode']}/b{c['budget']}/food{c['food_bit']}/{c['renewal']}"
            for group in (total,groups.setdefault(key,{})):
                for k,v in counts(record).items(): group[k]=group.get(k,0)+v
            rows+=1; events+=len(record['events'])
    summary=dict(schema='startup01-summary-v1',revision=revision,source_sha256={f:hashlib.sha256((ROOT/f).read_bytes()).hexdigest() for f in FILES},
                 records_sha256=checksum.hexdigest(),authored_cases=rows,events=events,groups=groups,total=total,
                 natural_worlds=0,reserved_samples_executed=False,reproduction_demonstrated=False)
    (output/'summary.json').write_bytes((encode(summary)+'\n').encode())
    return summary
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__); p.add_argument('--output-dir',required=True); p.add_argument('--source-revision',required=True)
    args=p.parse_args(); run(args.output_dir,args.source_revision)
