"""Finite STARTUP-02 unscreened paid chain assay; no runtime installation."""
import argparse
import copy
import hashlib
import json
from pathlib import Path
import random

ROOT=Path(__file__).resolve().parents[1]
MODES=('active','external','ghost','association_off','topup_off','supplied','food_withdrawn')
FILES=('docs/STARTUP-02-PROTOCOL.md','experiments/startup_unscreened.py','experiments/startup_unscreened_audit.py',
       'docs/STARTUP-01-PROTOCOL.md','experiments/startup_feasibility.py','experiments/startup_feasibility_audit.py')
def encode(v): return json.dumps(v,sort_keys=True,separators=(',',':'))
def sha(v): return hashlib.sha256(encode(v).encode()).hexdigest()
def initial(seed,mode):
    r=random.Random(seed); s=dict(atoms={},units={},free=[],potential={},food=[],waste=[],spare=[],reserve_work=[],
                                bank=[],chains={},products={},history={},heat=0)
    for prefix,count,kind,pool in (('M',24,'raw','free'),('F',64,'food','food'),('B',4,'reserve','spare')):
        for i in range(count):
            aid=prefix+str(i); s['atoms'][aid]=dict(bit=str(r.randrange(2)),kind=kind); s[pool].append(aid)
            if prefix=='M': s['potential'][aid]=[]
    for prefix,count,pool,origin in (('E',64,'bank','external'),('R',13,'reserve_work','reserve')):
        for i in range(count):
            uid=prefix+str(i); s[pool].append(uid)
            s['units'][uid]=dict(origin=origin,actor='genesis',food=None,parents=[],carrier=None,tick=-1)
    if mode=='supplied':
        reserved=s['reserve_work'][:]; body=s['spare'][:]
        s['products']['C']=dict(atoms=body,bonds=reserved[:3],work=reserved[3:5])
        s['history']['C']=dict(kind='product',origin='supplied',atoms=body[:],bonds=reserved[:3],debits=reserved,
                              parents=[],born=-1,endowment=reserved[3:5],fully_capture_funded=False,funders=[])
        s['reserve_work'].clear(); s['spare'].clear(); s['heat']=8
    return s,r
def step(s,mode,t,q):
    op,monomer,food_index,chain_index,actor_index,_=q
    atom=f'M{monomer%24}'; food=f'F{food_index%64}'
    keys=sorted(s['chains']); cid=keys[chain_index%len(keys)] if keys else None
    keys=sorted(s['products']); actor=keys[actor_index%len(keys)] if keys else None
    c=s['chains'].get(cid); p=s['products'].get(actor)
    result=dict(outcome='unavailable',spent=[],created=[],heat=0,product=None,actor=actor)
    has_food=food in s['food'] and not (mode=='food_withdrawn' and t>=128)
    matches=p is not None and len(p['atoms'])>1 and s['atoms'][p['atoms'][-1]]['bit']!=s['atoms'][food]['bit']
    def debit(pool,count):
        taken=pool[:count]; pool[:count]=[]; result['spent'].extend(taken); return taken
    def heat(n): s['heat']+=n; result['heat']+=n
    def units(n,origin,who,paid,carrier):
        result['created']=[f'U{t}.{j}' for j in range(n)]
        for uid in result['created']:
            if uid in s['units']: raise ValueError('Duplicate unit')
            s['units'][uid]=dict(origin=origin,actor=who,food=food,parents=list(paid),carrier=carrier,tick=t)
        return result['created'][:]
    if op<2:
        attached=atom in s['free'] or any(atom in chain['atoms'] for chain in s['chains'].values())
        charge=len(s['potential'][atom]); external=t<128 or mode=='external'
        account=s['bank'] if external else p['work'] if p else []
        suitable=attached and has_food and (external or matches) and (charge==0 if op==0 else charge in (1,2))
        if op==1 and mode=='topup_off': result['outcome']='disabled'
        elif suitable:
            if len(account)<2: result['outcome']='starved'
            else:
                paid=debit(account,2); s['food'].remove(food); s['waste'].append(food)
                s['potential'][atom].extend(units(3-charge,'activation' if op==0 else 'recharge','environment' if external else actor,paid,atom))
                heat(7+charge); result['outcome']='charged'
    elif op==2 and atom in s['free'] and s['potential'][atom]:
        used=debit(s['potential'][atom],1); heat(1)
        if mode=='association_off': result['outcome']='disabled'
        else:
            s['free'].remove(atom); key=f'C{t}'
            v=dict(kind='chain',origin='assembly',atoms=[atom],bonds=[],debits=used,parents=[],born=t)
            s['history'][key]=copy.deepcopy(v); s['chains'][key]=v; result['outcome']='started'
    elif op==3 and c and atom in s['free'] and len(s['potential'][atom])==3:
        used=debit(s['potential'][atom],3); heat(2); s['free'].remove(atom)
        key=f'C{t}'; v=dict(kind='chain',origin='assembly',atoms=c['atoms']+[atom],bonds=c['bonds']+[used[-1]],
                          debits=c['debits']+used,parents=[cid],born=t)
        s['chains'].pop(cid); s['chains'][key]=v; s['history'][key]=copy.deepcopy(v); result['outcome']='extended'
    elif op==4 and c and len(c['atoms'])>=2:
        available=[uid for aid in c['atoms'] for uid in s['potential'][aid]]
        if len(available)>=3:
            used=available[:3]; result['spent']=used[:]
            for aid in c['atoms']:
                s['potential'][aid]=[uid for uid in s['potential'][aid] if uid not in used]
            endowed=used[1:] if mode!='ghost' else []; heat(1 if endowed else 3)
            construction=c['debits']+used
            funding=[]; fully=True
            for uid in construction:
                meta=s['units'][uid]; funding.append(meta['actor'])
                if meta['origin'] not in ('activation','recharge') or len(meta['parents'])!=2 or any(s['units'][parent]['origin']!='capture' for parent in meta['parents']): fully=False
            key=f'P{t}'; v=dict(kind='product',origin='assembly',atoms=c['atoms'][:],bonds=c['bonds'][:],debits=construction,
                              parents=[cid],born=t,endowment=endowed[:],fully_capture_funded=fully,funders=sorted(set(funding)))
            s['history'][key]=v; s['products'][key]=dict(atoms=c['atoms'][:],bonds=c['bonds'][:],work=endowed[:]); s['chains'].pop(cid)
            result.update(outcome='released',product=key)
    elif op==5 and has_food and matches:
        if len(p['work'])<2: result['outcome']='starved'
        else:
            used=debit(p['work'],2); s['food'].remove(food); s['waste'].append(food)
            capacity=len(p['atoms'])-len(p['work']); created=units(3,'capture',actor,used,None)
            p['work'].extend(created[:capacity]); heat(7+len(created[capacity:])); result['outcome']='captured'
    return result
def simulate(seed,mode):
    s,r=initial(seed,mode); start=copy.deepcopy(s); chain=sha(s); events=[]
    for t in range(256):
        draw=[r.randrange(6)]+[r.randrange(65536) for _ in range(5)]; before=sha(s); result=step(s,mode,t,draw)
        event=dict(tick=t,draw=draw,before=before,after=sha(s),previous=chain,result=result)
        event['sha256']=sha(event); chain=event['sha256']; events.append(event)
    return dict(config=dict(seed=seed,mode=mode),initial=start,events=events,terminal=s)
def summarize(records):
    totals={}; outcomes={}; lengths={}
    for r in records:
        mode=r['config']['mode']; s=r['terminal']; births={k:v for k,v in s['history'].items() if v['kind']=='product' and v['origin']=='assembly'}
        captures=[e for e in r['events'] if e['result']['outcome']=='captured']; made=[e for e in captures if e['result']['actor'] in births]
        metrics=dict(worlds=1,founder_free_success=int(mode!='supplied' and len(made)>0),assemblies=len(births),assembled_captures=len(made),
            supplied_captures=len(captures)-len(made),post_withdrawal_captures=len([e for e in made if e['tick']>=128]),
            fully_capture_funded_births=len([v for v in births.values() if v['born']>=128 and v['fully_capture_funded']]),
            fully_capture_funded_probes=len([e for e in made if e['tick']>=128 and births[e['result']['actor']]['fully_capture_funded']]),
            remaining_food=len(s['food']),waste=len(s['waste']),heat=s['heat'],unused_external=len(s['bank']))
        target=totals.setdefault(mode,{})
        for k,v in metrics.items(): target[k]=target.get(k,0)+v
        for e in r['events']:
            key=f"{mode}/{e['draw'][0]}/{e['result']['outcome']}"; outcomes[key]=outcomes.get(key,0)+1
        for v in births.values():
            key=f"{mode}/{len(v['atoms'])}"; lengths[key]=lengths.get(key,0)+1
    return dict(totals=totals,outcomes=outcomes,assembly_lengths=lengths)
def run(output,revision):
    if len(revision)!=40 or any(c not in '0123456789abcdef' for c in revision): raise ValueError('Exact source revision')
    output=Path(output); output.mkdir(parents=True,exist_ok=False); records=[]; h=hashlib.sha256()
    with (output/'records.jsonl').open('wb') as f:
        for seed in range(40000,40032):
            for mode in MODES:
                record=simulate(seed,mode); records.append(record); data=(encode(record)+'\n').encode(); f.write(data); h.update(data)
    summary=dict(schema='startup02-summary-v1',revision=revision,sources={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in FILES},
                 records_sha256=h.hexdigest(),worlds=224,events=57344,independent_seed_blocks=32,reserved_samples_executed=False,**summarize(records))
    (output/'summary.json').write_bytes((encode(summary)+'\n').encode()); return summary
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__); p.add_argument('--output-dir',required=True); p.add_argument('--source-revision',required=True); a=p.parse_args()
    run(a.output_dir,a.source_revision)
