"""DISSOCIATE-01 separate authored finite breakup assay, no natural worlds."""
import argparse
import copy
import hashlib
import itertools
import json
from pathlib import Path
from experiments import startup_unscreened as base

ROOT=Path(__file__).resolve().parents[1]
MODES=('candidate','irreversible','cut_ghost','product_ghost','association_off','supplied','food_withdrawn','external')
FILES=base.FILES+('docs/DISSOCIATE-01-PROTOCOL.md','experiments/paid_dissociation.py','experiments/paid_dissociation_audit.py')
def encode(v): return json.dumps(v,sort_keys=True,separators=(',',':'))
def digest(v): return hashlib.sha256(encode(v).encode()).hexdigest()
def configs():
    for length in (2,3,4):
        for word in itertools.product('01',repeat=length):
            for budget,food,mode in itertools.product((0,12,32),('0','1'),MODES): yield dict(word=''.join(word),budget=budget,food_bit=food,mode=mode)
def mode(c): return {'product_ghost':'ghost','association_off':'association_off','supplied':'supplied','food_withdrawn':'food_withdrawn','external':'external'}.get(c['mode'],'active')
def initial(c):
    s,_=base.initial(0,mode(c))
    for aid in s['atoms']: s['atoms'][aid]['bit']=c['food_bit'] if aid[0]=='F' else '0'
    for i,bit in enumerate(c['word'],4): s['atoms'][f'M{i}']['bit']=bit
    inaccessible=s['bank'][c['budget']:]; s['bank']=s['bank'][:c['budget']]; s['reserve_work'].extend(inaccessible)
    s['recycles']={f'M{i}':[] for i in range(24)}; return s
def schedule(c):
    pre=[]
    if c['mode']!='supplied':
        pre=[(0,0),(2,0)]
        for atom in range(1,4): pre.extend([(0,atom),(3,atom),(0,atom)])
        pre.append((4,0))
    pre.extend([(0,4),(2,4)])
    for atom in range(5,len(c['word'])+4): pre.extend([(0,atom),(3,atom)])
    post=[(5,0),(5,0),(6,4)]
    for atom in range(4,len(c['word'])+4):
        post.extend([(5,0),(5,0),(0,atom),(2 if atom==4 else 3,atom)])
        if atom!=4: post.extend([(5,0),(5,0),(0,atom)])
    post.extend([(4,4),(5,4)])
    return [(t,op,a,'pre') for t,(op,a) in enumerate(pre)]+[(128+t,op,a,'post') for t,(op,a) in enumerate(post)]
def select(s,c,op,atom,phase):
    chains=sorted(s['chains'],key=lambda key:(-len(s['chains'][key]['atoms']),key))
    chain=chains[0] if chains else None
    products=sorted([key for key,value in s['history'].items() if value['kind']=='product' and value['origin']=='assembly'],key=lambda key:s['history'][key]['born'])
    founders=[key for key in products if set(s['history'][key]['atoms'])=={'M0','M1','M2','M3'}]
    founder='C' if c['mode']=='supplied' else founders[0] if founders else None
    requested=set(f'M{i}' for i in range(4,4+len(c['word'])))
    targets=[key for key in products if requested.issubset(s['history'][key]['atoms'])]
    actor=(targets[-1] if targets else None) if phase=='post' and op==5 and atom==4 else founder
    food=sorted(s['food'],key=lambda aid:int(aid[1:]))[0] if s['food'] else 'F0'
    return dict(op=op,atom=f'M{atom}',food=food,chain=chain,actor=actor)
def step(s,c,t,q):
    op=q['op']; actor=q['actor']; cid=q['chain']; law=mode(c)
    r=dict(outcome='unavailable',spent=[],created=[],heat=0,product=None,actor=actor)
    if op==6:
        if c['mode']=='irreversible': r['outcome']='disabled'; return r
        if cid not in s['chains']: return r
        chain=s['chains'][cid]; body=chain['atoms'][:]; cost=len(body)+1
        bank=s['bank'] if t<128 or c['mode']=='external' else s['products'].get(actor,{}).get('work',[])
        if len(bank)<cost: r['outcome']='starved'; return r
        paid=bank[:cost]; bank[:cost]=[]
        bonds=chain['bonds'][:]; charge=sum([s['potential'][a] for a in body],[])
        for a in body: s['potential'][a]=[]
        returned=c['mode']!='cut_ghost'; s['free' if returned else 'spare'].extend(body); s['chains'].pop(cid)
        oid=f'D{t}'; s['history'][oid]=dict(kind='dismantled',origin='paid_cut' if returned else 'inert_cut',atoms=body,
            parents=[cid],born=t,work_debits=paid,bond_debits=bonds,charge_debits=charge,returned=returned)
        for a in body: s['recycles'][a].append(oid)
        heat=len(paid+bonds+charge); s['heat']+=heat
        r.update(outcome='cut' if returned else 'inert_cut',spent=paid+bonds+charge,heat=heat,product=oid); return r
    if op in (3,4) and cid not in s['chains'] or op==5 and actor not in s['products'] or op<2 and t>=128 and law!='external' and actor not in s['products']: return r
    cs=sorted(s['chains']); ps=sorted(s['products'])
    draw=[op,int(q['atom'][1:]),int(q['food'][1:]),cs.index(cid) if cid in cs else 0,ps.index(actor) if actor in ps else 0,0]
    r=base.step(s,law,t,draw); r['actor']=actor; return r
def simulate(c):
    s=initial(c); start=copy.deepcopy(s); chain=digest(s); events=[]
    for t,op,atom,phase in schedule(c):
        q=select(s,c,op,atom,phase); before=digest(s); result=step(s,c,t,q)
        event=dict(tick=t,request=q,before=before,after=digest(s),previous=chain,result=result); event['sha256']=digest(event); chain=event['sha256']; events.append(event)
    return dict(config=c,initial=start,events=events,terminal=s)
def metrics(record):
    s=record['terminal']; target={f'M{i}' for i in range(4,4+len(record['config']['word']))}
    cuts={key:v for key,v in s['history'].items() if v['kind']=='dismantled'}
    products={key:v for key,v in s['history'].items() if v['kind']=='product' and v['origin']=='assembly' and set(v['atoms'])==target}
    renewed=set(); reused=False
    for key,product in products.items():
        earlier=[v for v in cuts.values() if v['returned'] and set(v['atoms'])==target and v['born']<product['born']]
        reused=reused or bool(earlier)
        if earlier and product['fully_capture_funded'] and all(s['units'][u]['origin']=='capture' for cut in earlier for u in cut['work_debits']): renewed.add(key)
    probes={e['result']['actor'] for e in record['events'] if e['tick']>=128 and e['result']['outcome']=='captured'}
    return dict(cases=1,cuts=sum(v['returned'] for v in cuts.values()),inert_cuts=sum(not v['returned'] for v in cuts.values()),
        cut_work=sum(len(v['work_debits']) for v in cuts.values()),cut_bond_heat=sum(len(v['bond_debits']) for v in cuts.values()),cut_charge_heat=sum(len(v['charge_debits']) for v in cuts.values()),
        reused_release=int(reused),fully_capture_paid_release=int(bool(renewed)),fully_capture_paid_probe=int(bool(renewed&probes)),target_probe=int(bool(set(products)&probes)),
        founder_captures=sum(e['result']['outcome']=='captured' and e['result']['actor'] not in products for e in record['events']),final_heat=s['heat'],remaining_food=len(s['food']),events=len(record['events']))
def aggregate(records):
    totals={}
    for r in records:
        c=r['config']; key=f"{c['mode']}/{len(c['word'])}/{c['budget']}/{c['food_bit']}"; row=totals.setdefault(key,{})
        for field,value in metrics(r).items(): row[field]=row.get(field,0)+value
    return totals
def run(output,revision):
    if len(revision)!=40 or any(c not in '0123456789abcdef' for c in revision): raise ValueError('Exact revision')
    output=Path(output); output.mkdir(parents=True,exist_ok=False); records=[]; h=hashlib.sha256()
    with (output/'records.jsonl').open('wb') as f:
        for c in configs():
            r=simulate(c); records.append(r); raw=(encode(r)+'\n').encode(); f.write(raw); h.update(raw)
    summary=dict(schema='dissociate01-summary-v1',revision=revision,sources={f:hashlib.sha256((ROOT/f).read_bytes()).hexdigest() for f in FILES},records_sha256=h.hexdigest(),cases=1344,events=sum(len(r['events']) for r in records),authored_feasibility_only=True,natural_worlds=0,totals=aggregate(records))
    (output/'summary.json').write_bytes((encode(summary)+'\n').encode()); return summary
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__); p.add_argument('--output-dir',required=True); p.add_argument('--source-revision',required=True); a=p.parse_args(); run(a.output_dir,a.source_revision)
