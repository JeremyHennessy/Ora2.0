"""AGGREGATE-01 finite reversible contact physics; no organism controller."""
import argparse,copy,hashlib,io,json,zipfile
from pathlib import Path
from .evidence_budget import Budget
from .evidence_budget_audit import audit as storage
ARMS=('candidate','no-bond','shuffled','inert','no-recycle','supplied')
STAT=('capture','basal','catalytic','manufacture','recycle','bind','unbind','thermal_motion','funded_motion','decay','damage','post_withdrawal_manufacture','post_withdrawal_recycle')
def encode(w):return json.dumps(w,sort_keys=True,separators=(',',':')).encode()
def draw(w):
    x=w['rng'];x^=(x<<13)&0xffffffff;x^=x>>17;x^=(x<<5)&0xffffffff;w['rng']=x&0xffffffff;return w['rng']
def lane(k):
    u,v=divmod(k,4);return hashlib.sha256(f'AGGREGATE-01|{u}|{v}'.encode('ascii')).digest()[0]%4
def pos(w,p):return w['atoms'][p]['pos'] if p<24 else w['carriers'][p-24]['pos']
def cluster(w,p):
    edges=w['edges']+[o['atoms'] for o in w['objects'] if o['alive']];found={p}
    while True:
        more={x for e in edges if any(x in found for x in e) for x in e}
        if more<=found:return sorted(found)
        found|=more
def translate(w,ids,delta):
    for p in ids:
        particle=w['atoms'][p] if p<24 else w['carriers'][p-24];particle['pos']=(particle['pos']+delta)%8
    for o in w['objects']:
        if o['alive']:o['pos']=w['atoms'][o['atoms'][0]]['pos']
def check(w):
    energy=sum(w['photons'])+w['thermal']+w['heat']+w['removed']+len(w['edges'])+3*sum(c['charged'] for c in w['carriers'])+sum(o['alive'] for o in w['objects'])
    if energy!=640 or min(w['photons']+[w['thermal'],w['heat'],w['removed']])<0:raise ValueError('Energy residual/borrowing')
    if len(w['atoms'])!=24 or len(w['carriers'])!=16:raise ValueError('Matter count')
    endpoints=[p for e in w['edges'] for p in e]
    if len(set(endpoints))!=len(endpoints) or w['edges']!=sorted(w['edges']):raise ValueError('Adhesive valence/order')
    for e in w['edges']:
        if len(e)!=2 or e!=sorted(set(e)) or not 0<=e[0]<e[1]<40 or pos(w,e[0])!=pos(w,e[1]):raise ValueError('Edge ownership/location')
    for i,a in enumerate(w['atoms']):
        if a['type']!=i//6 or not 0<=a['pos']<8:raise ValueError('Atom identity')
        if a['owner'] is not None:
            o=w['objects'][a['owner']]
            if a['status']!='component' or not o['alive'] or i not in o['atoms'] or a['pos']!=o['pos']:raise ValueError('Atom ownership')
        elif a['status'] not in ('raw','waste'):raise ValueError('Atom form')
    for i,o in enumerate(w['objects']):
        if o['id']!=i or len(set(o['atoms']))!=2:raise ValueError('Object identity')
        if o['alive'] and any(w['atoms'][p]['owner']!=i for p in o['atoms']):raise ValueError('Internal link ownership')
    for i,c in enumerate(w['carriers']):
        if c['lane']!=i%4 or not 0<=c['pos']<8 or c['charged']!=(c['charge'] is not None):raise ValueError('Carrier identity/provenance')
def new(seed,arm):
    if (seed not in range(74000,74032) and seed!=74999) or arm not in ARMS:raise ValueError('Registered samples/author fixture')
    w=dict(seed=seed,arm=arm,rng=seed,step=0,photons=[64]*8,thermal=128,heat=0,removed=0,atoms=[],carriers=[],objects=[],edges=[],productive=[],rounds=[],stats={k:0 for k in STAT},genesis=[],zero_thermal=None,zero_photons=None,max_aggregate=1)
    for i in range(24):w['atoms'].append(dict(type=i//6,pos=draw(w)%8,status='raw',owner=None,history=[],waste_round=None,recycled_at=None,assisted=False))
    for i in range(16):w['carriers'].append(dict(lane=i%4,pos=draw(w)%8,charged=False,charge=None))
    if arm=='supplied':
        for a,b in ((0,1),(2,3),(4,5),(6,7)):
            target=w['atoms'][a]['pos']
            for particle in (w['atoms'][b],w['carriers'][0]):
                cost=min((target-particle['pos'])%8,(particle['pos']-target)%8);particle['pos']=target;w['thermal']-=cost;w['heat']+=cost;w['stats']['thermal_motion']+=cost;w['genesis'].append(['transport',cost,target])
            w['photons'][target]-=4;w['heat']+=1;w['stats']['capture']+=1;w['stats']['basal']+=1
            w['carriers'][0].update(charged=True,charge=dict(step=0,donor=None,kind=None,assisted=False))
            w['atoms'][a]['assisted']=w['atoms'][b]['assisted']=True
            w['genesis'].append(['founder',copy.deepcopy(make(w,a,b,0,0))])
    w['max_aggregate']=max(len(cluster(w,i)) for i in range(40));check(w);return w
def make(w,a,b,ci,t):
    atoms=[w['atoms'][a],w['atoms'][b]];c=w['carriers'][ci];source=copy.deepcopy(c['charge']);u,v=sorted(x['type'] for x in atoms);k=4*u+v
    assisted=any(x['assisted'] for x in atoms) or source['assisted'];restores=[]
    for r,round in enumerate(w['rounds']):
        if t<round['deadline'] and not assisted and k in round['lost'] and source['donor'] is not None and source['kind']!=k and source['step']>round['step'] and all(x['waste_round']==r and x['recycled_at'] is not None and x['recycled_at']>round['step'] for x in atoms):restores.append(r)
    o=dict(id=len(w['objects']),atoms=sorted([a,b]),kind=k,pos=atoms[0]['pos'],alive=True,born=t,assisted=bool(assisted),energy_parent=source,atom_parents=[x['history'][:] for x in atoms],restore_rounds=restores)
    w['objects'].append(o)
    for x in atoms:x.update(status='component',owner=o['id'],history=x['history']+[o['id']],assisted=bool(x['assisted'] or assisted))
    c.update(charged=False,charge=None);w['heat']+=2;w['stats']['manufacture']+=1
    if t>=3072:w['stats']['post_withdrawal_manufacture']+=1
    if source['donor'] is not None and not assisted and source['kind']!=k:
        donor=w['objects'][source['donor']]
        if source['donor'] not in w['productive']:w['productive'].append(source['donor']);w['productive'].sort()
        for r in donor['restore_rounds']:
            if source['step']>w['rounds'][r]['step'] and t<w['rounds'][r]['deadline']:w['rounds'][r]['qualified']=True
    for r in restores:w['rounds'][r]['rebuilt'].append(o['id'])
    return o
def kill(w,oid,t,label,round_id=None):
    o=w['objects'][oid];o['alive']=False
    for a in o['atoms']:w['atoms'][a].update(status='waste',owner=None,waste_round=round_id,recycled_at=None)
    w['heat']+=1;w['stats'][label]+=1
def tick(w,t,d):
    events=[]
    if t in (1024,2048):
        r=len(w['rounds']);ids=[o['id'] for o in w['objects'] if o['alive'] and o['id']%2==r]
        lost={w['objects'][i]['kind'] for i in ids if i in w['productive'] and not w['objects'][i]['assisted']}
        for oid in ids:kill(w,oid,t,'damage',r)
        survivors={o['kind'] for o in w['objects'] if o['alive']}
        w['rounds'].append(dict(step=t,deadline=2048 if r==0 else 3072,damaged=ids,lost=sorted(lost-survivors),rebuilt=[],qualified=False));events.append(['damage',r,copy.deepcopy(w['rounds'][-1])])
    if t==3072:
        count=sum(w['photons']);w['removed']+=count;w['photons']=[0]*8;events.append(['withdraw-photons',count])
    op,cell=d[0]%8,d[1]%8;ap=[i for i in range(24) if w['atoms'][i]['pos']==cell];cp=[i for i in range(16) if w['carriers'][i]['pos']==cell];pool=ap+[24+i for i in cp]
    pick=lambda values,k:values[d[k]%len(values)] if values else None
    p,q=pick(pool,2),pick(pool,3);a,b=pick(ap,2),pick(ap,3);ci,cj=pick(cp,2),pick(cp,4);delta=1 if d[5]&1 else -1
    if op==0 and p is not None:
        members=cluster(w,p)
        if w['thermal']>=len(members):
            w['thermal']-=len(members);w['heat']+=len(members);w['stats']['thermal_motion']+=len(members);translate(w,members,delta);events.append(['thermal-move',members,delta])
    elif op in (1,2) and p is not None and p!=q:
        edge=sorted([p,q]);used={x for e in w['edges'] for x in e};same_component=p<24 and q<24 and w['atoms'][p]['owner'] is not None and w['atoms'][p]['owner']==w['atoms'][q]['owner']
        if op==1 and w['arm']!='no-bond' and p not in used and q not in used and not same_component and d[6]&255<64 and w['photons'][cell]>=2:
            w['photons'][cell]-=2;w['heat']+=1;w['edges'].append(edge);w['edges'].sort();w['stats']['bind']+=1;events.append(['bind',edge])
        elif op==2 and edge in w['edges'] and d[7]&255<8 and w['photons'][cell]>=1:
            w['photons'][cell]-=1;w['heat']+=2;w['edges'].remove(edge);w['stats']['unbind']+=1;events.append(['unbind',edge])
    elif op==3 and ci is not None and not w['carriers'][ci]['charged'] and w['photons'][cell]>=4:
        oid=w['atoms'][b]['owner'] if b is not None else None;o=w['objects'][oid] if oid is not None else None
        enhanced=o is not None and w['arm']!='inert' and (lane(o['kind'])+int(w['arm']=='shuffled' and t>=1024))%4==w['carriers'][ci]['lane'];value=d[6]&255
        if value<8 or enhanced and value<64:
            donor=o if enhanced and value>=8 else None;source=dict(step=t,donor=donor['id'] if donor else None,kind=donor['kind'] if donor else None,assisted=donor['assisted'] if donor else False)
            w['photons'][cell]-=4;w['heat']+=1;w['carriers'][ci].update(charged=True,charge=source);w['stats']['capture']+=1;w['stats']['catalytic' if donor else 'basal']+=1;events.append(['capture',ci,source])
    elif op in (4,5) and a is not None and a!=b and cj is not None and w['carriers'][cj]['charged']:
        x,y=w['atoms'][a],w['atoms'][b]
        if op==4 and x['status']==y['status']=='raw':events.append(['manufacture',make(w,a,b,cj,t)])
        elif op==5 and w['arm']!='no-recycle' and x['status']==y['status']=='waste':
            source=copy.deepcopy(w['carriers'][cj]['charge']);w['carriers'][cj].update(charged=False,charge=None)
            x.update(status='raw',recycled_at=t);y.update(status='raw',recycled_at=t);w['heat']+=3;w['stats']['recycle']+=1
            if t>=3072:w['stats']['post_withdrawal_recycle']+=1
            events.append(['recycle',sorted([a,b]),cj,source])
    elif op==6 and a is not None and w['atoms'][a]['owner'] is not None and d[7]&255<8:
        oid=w['atoms'][a]['owner'];kill(w,oid,t,'decay');events.append(['decay',oid])
    elif op==7 and b is not None and ci is not None and w['carriers'][ci]['charged']:
        members=cluster(w,b)
        if len(members)<=3:
            source=copy.deepcopy(w['carriers'][ci]['charge']);w['carriers'][ci].update(charged=False,charge=None);w['heat']+=3;w['stats']['funded_motion']+=len(members);translate(w,members,delta);events.append(['funded-move',members,delta,ci,source])
    w['step']=t
    if not w['thermal'] and w['zero_thermal'] is None:w['zero_thermal']=t
    if not any(w['photons']) and w['zero_photons'] is None:w['zero_photons']=t
    # Only affected aggregates can grow; ordinary moves don't change connectivity.
    if any(e[0] in ('bind','manufacture') for e in events):w['max_aggregate']=max(w['max_aggregate'],max(len(cluster(w,x)) for x in range(40)))
    check(w);return events
def record(w):return dict(seed=w['seed'],arm=w['arm'],endpoint=len(w['rounds'])==2 and all(r['qualified'] for r in w['rounds']),rounds=w['rounds'],stats=w['stats'],zero_thermal=w['zero_thermal'],zero_photons=w['zero_photons'],charged_remaining=sum(c['charged'] for c in w['carriers']),removed=w['removed'],heat=w['heat'],thermal=w['thermal'],adhesive_edges=len(w['edges']),max_aggregate=w['max_aggregate'],active=sum(o['alive'] for o in w['objects']))
def run_world(seed,arm,revision,out):
    w=new(seed,arm);out.write(encode(dict(header=True,source_revision=revision,world=w))+b'\n')
    for t in range(1,4097):
        d=[draw(w) for _ in range(8)];events=tick(w,t,d);out.write(encode(dict(step=t,draws=d,events=events,state_sha256=hashlib.sha256(encode(w)).hexdigest()))+b'\n')
    out.write(encode(dict(final=True,world=w))+b'\n');return record(w)
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--start',required=True,type=int);p.add_argument('--revision',required=True);p.add_argument('--output',required=True);args=p.parse_args()
    if args.start not in range(74000,74032,4):p.error('Registered batch')
    budget=Budget(Path(args.output),dict(raw=48*1024**2,archive=32*1024**2,restore=48*1024**2,failure=2*1024**2),130*1024**2);records=[]
    try:
        for seed in range(args.start,args.start+4):
            for arm in ARMS:
                with budget.create('raw',f'{seed}-{arm}.jsonl') as out:records.append(run_world(seed,arm,args.revision,out))
        with budget.create('raw','records.json') as out:out.write(encode(records))
        payload=io.BytesIO()
        with zipfile.ZipFile(payload,'w',zipfile.ZIP_DEFLATED) as z:
            for q in (budget.root/'raw').iterdir():z.write(q,q.name)
        with budget.create('archive','complete.zip') as out:out.write(payload.getvalue())
        with zipfile.ZipFile(io.BytesIO(payload.getvalue())) as z:
            for e in z.infolist():
                with budget.create('restore',e.filename,e.file_size) as out:out.write(z.read(e))
        assert all(q.read_bytes()==(budget.root/'restore'/q.name).read_bytes() for q in (budget.root/'raw').iterdir())
        print(json.dumps(dict(worlds=24,transitions=24*4096,endpoints=sum(r['endpoint'] for r in records))))
    finally:
        with budget.create('failure','budget.json',1024**2) as out:
            receipt=copy.deepcopy(budget.snapshot());out.write(encode(receipt))
        storage(budget.root,receipt,receipt['limits'],receipt['total_limit'])
