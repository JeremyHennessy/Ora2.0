"""Separate AGGREGATE-01 interpreter; imports no experimental producer."""
import argparse,hashlib,json
from pathlib import Path
MODES=('candidate','no-bond','shuffled','inert','no-recycle','supplied')
COUNTERS=('capture','basal','catalytic','manufacture','recycle','bind','unbind','thermal_motion','funded_motion','decay','damage','post_withdrawal_manufacture','post_withdrawal_recycle')
def pack(s):return json.dumps(s,sort_keys=True,separators=(',',':')).encode()
def random(s):
    n=s['rng'];n=(n^((n*8192)&4294967295))&4294967295;n^=n//131072;n^=(n*32)&4294967295;s['rng']=n&4294967295;return s['rng']
def channel(k):return hashlib.sha256(('AGGREGATE-01|%d|%d'%(k//4,k%4)).encode('ascii')).digest()[0]&3
def location(s,i):return s['atoms'][i]['pos'] if i<24 else s['carriers'][i-24]['pos']
def aggregate(s,i):
    links=[set() for _ in range(40)]
    for a,b in s['edges']+[o['atoms'] for o in s['objects'] if o['alive']]:links[a].add(b);links[b].add(a)
    visited=set();stack=[i]
    while stack:
        node=stack.pop()
        if node not in visited:visited.add(node);stack.extend(links[node]-visited)
    return sorted(visited)
def relocate(s,nodes,direction):
    for i in nodes:
        p=s['atoms'][i] if i<24 else s['carriers'][i-24];p['pos']=(p['pos']+direction)%8
    for o in s['objects']:
        if o['alive']:o['pos']=s['atoms'][o['atoms'][0]]['pos']
def verify(s):
    if len(s['atoms'])!=24 or len(s['carriers'])!=16:raise ValueError('Matter inventory')
    amount=sum(s['photons'])+s['thermal']+s['heat']+s['removed']+len(s['edges'])+sum(3 if c['charged'] else 0 for c in s['carriers'])+sum(int(o['alive']) for o in s['objects'])
    if amount!=640 or min(s['photons']+[s['thermal'],s['heat'],s['removed']])<0:raise ValueError('Independent energy residual')
    seen=set()
    if s['edges']!=sorted(s['edges']):raise ValueError('Edge ordering')
    for edge in s['edges']:
        if len(edge)!=2 or not 0<=edge[0]<edge[1]<40 or location(s,edge[0])!=location(s,edge[1]) or seen.intersection(edge):raise ValueError('Edge valence/identity/location')
        seen.update(edge)
    for i,a in enumerate(s['atoms']):
        if a['type']!=i//6 or not 0<=a['pos']<8:raise ValueError('Atom identity/location')
        if a['owner'] is None:
            if a['status'] not in ('raw','waste'):raise ValueError('Free atom')
        else:
            obj=s['objects'][a['owner']]
            if a['status']!='component' or not obj['alive'] or i not in obj['atoms'] or a['pos']!=obj['pos']:raise ValueError('Bound atom')
    for i,o in enumerate(s['objects']):
        if o['id']!=i or len(set(o['atoms']))!=2 or (o['alive'] and any(s['atoms'][a]['owner']!=i for a in o['atoms'])):raise ValueError('Component identity/ownership')
    for i,c in enumerate(s['carriers']):
        if c['lane']!=i%4 or not 0<=c['pos']<8 or c['charged']!=(c['charge'] is not None):raise ValueError('Carrier identity/payment')
def assemble(s,pair,ci,t):
    a,b=pair;x,y=s['atoms'][a],s['atoms'][b];c=s['carriers'][ci];ancestry=json.loads(json.dumps(c['charge']))
    u,v=sorted((x['type'],y['type']));k=4*u+v;helped=bool(x['assisted'] or y['assisted'] or ancestry['assisted']);replaced=[]
    for r,ch in enumerate(s['rounds']):
        recycled=all(z['waste_round']==r and z['recycled_at'] is not None and z['recycled_at']>ch['step'] for z in (x,y))
        if t<ch['deadline'] and not helped and k in ch['lost'] and recycled and ancestry['donor'] is not None and ancestry['kind']!=k and ancestry['step']>ch['step']:replaced.append(r)
    obj=dict(id=len(s['objects']),atoms=sorted(pair),kind=k,pos=x['pos'],alive=True,born=t,assisted=helped,energy_parent=ancestry,atom_parents=[x['history'][:],y['history'][:]],restore_rounds=replaced)
    s['objects'].append(obj)
    for z in (x,y):z['status']='component';z['owner']=obj['id'];z['history'].append(obj['id']);z['assisted']=bool(z['assisted'] or helped)
    c['charged']=False;c['charge']=None;s['heat']+=2;s['stats']['manufacture']+=1
    if t>=3072:s['stats']['post_withdrawal_manufacture']+=1
    if ancestry['donor'] is not None and not helped and ancestry['kind']!=k:
        src=ancestry['donor'];s['productive']=sorted(set(s['productive'])|{src})
        for r in s['objects'][src]['restore_rounds']:
            if ancestry['step']>s['rounds'][r]['step'] and t<s['rounds'][r]['deadline']:s['rounds'][r]['qualified']=True
    for r in replaced:s['rounds'][r]['rebuilt'].append(obj['id'])
    return obj
def genesis(seed,mode):
    if (seed not in range(74000,74032) and seed!=74999) or mode not in MODES:raise ValueError('Registered genesis/author fixture')
    s=dict(seed=seed,arm=mode,rng=seed,step=0,photons=[64 for _ in range(8)],thermal=128,heat=0,removed=0,atoms=[],carriers=[],objects=[],edges=[],productive=[],rounds=[],stats=dict.fromkeys(COUNTERS,0),genesis=[],zero_thermal=None,zero_photons=None,max_aggregate=1)
    for i in range(24):s['atoms'].append(dict(type=i//6,pos=random(s)%8,status='raw',owner=None,history=[],waste_round=None,recycled_at=None,assisted=False))
    for i in range(16):s['carriers'].append(dict(lane=i%4,pos=random(s)%8,charged=False,charge=None))
    if mode=='supplied':
        for a,b in ((0,1),(2,3),(4,5),(6,7)):
            dest=s['atoms'][a]['pos']
            for moving in (s['atoms'][b],s['carriers'][0]):
                difference=abs(dest-moving['pos']);cost=min(difference,8-difference);moving['pos']=dest;s['thermal']-=cost;s['heat']+=cost;s['stats']['thermal_motion']+=cost;s['genesis'].append(['transport',cost,dest])
            s['photons'][dest]-=4;s['heat']+=1;s['stats']['capture']+=1;s['stats']['basal']+=1
            s['carriers'][0]['charged']=True;s['carriers'][0]['charge']=dict(step=0,donor=None,kind=None,assisted=False)
            s['atoms'][a]['assisted']=s['atoms'][b]['assisted']=True
            s['genesis'].append(['founder',json.loads(json.dumps(assemble(s,[a,b],0,0)))])
    s['max_aggregate']=max(len(aggregate(s,i)) for i in range(40));verify(s);return s
def degrade(s,oid,t,counter,r=None):
    o=s['objects'][oid];o['alive']=False
    for i in o['atoms']:
        a=s['atoms'][i];a['status']='waste';a['owner']=None;a['waste_round']=r;a['recycled_at']=None
    s['heat']+=1;s['stats'][counter]+=1
def advance(s,t,d):
    events=[]
    if t==1024 or t==2048:
        r=len(s['rounds']);destroyed=sorted(o['id'] for o in s['objects'] if o['alive'] and o['id']%2==r)
        useful={s['objects'][i]['kind'] for i in destroyed if i in s['productive'] and not s['objects'][i]['assisted']}
        for i in destroyed:degrade(s,i,t,'damage',r)
        survivors={o['kind'] for o in s['objects'] if o['alive']}
        s['rounds'].append(dict(step=t,deadline=2048 if r==0 else 3072,damaged=destroyed,lost=sorted(useful-survivors),rebuilt=[],qualified=False));events.append(['damage',r,json.loads(json.dumps(s['rounds'][-1]))])
    if t==3072:
        remaining=sum(s['photons']);s['removed']+=remaining;s['photons']=[0 for _ in range(8)];events.append(['withdraw-photons',remaining])
    cell=d[1]%8;op=d[0]%8
    atoms=[i for i,a in enumerate(s['atoms']) if a['pos']==cell];carriers=[i for i,c in enumerate(s['carriers']) if c['pos']==cell];particles=atoms+[24+i for i in carriers]
    p=particles[d[2]%len(particles)] if particles else None;q=particles[d[3]%len(particles)] if particles else None
    a=atoms[d[2]%len(atoms)] if atoms else None;b=atoms[d[3]%len(atoms)] if atoms else None
    ci=carriers[d[2]%len(carriers)] if carriers else None;cj=carriers[d[4]%len(carriers)] if carriers else None;delta=1 if d[5]%2 else -1
    if op==0 and p is not None:
        nodes=aggregate(s,p)
        if s['thermal']>=len(nodes):
            s['thermal']-=len(nodes);s['heat']+=len(nodes);s['stats']['thermal_motion']+=len(nodes);relocate(s,nodes,delta);events.append(['thermal-move',nodes,delta])
    elif op==1 or op==2:
        if p is not None and p!=q:
            edge=sorted((p,q));taken={i for e in s['edges'] for i in e};internal=p<24 and q<24 and s['atoms'][p]['owner'] is not None and s['atoms'][p]['owner']==s['atoms'][q]['owner']
            if op==1 and s['arm']!='no-bond' and not internal and not taken.intersection(edge) and d[6]%256<64 and s['photons'][cell]>=2:
                s['edges']=sorted(s['edges']+[edge]);s['photons'][cell]-=2;s['heat']+=1;s['stats']['bind']+=1;events.append(['bind',edge])
            elif op==2 and edge in s['edges'] and d[7]%256<8 and s['photons'][cell]>=1:
                s['edges'].remove(edge);s['photons'][cell]-=1;s['heat']+=2;s['stats']['unbind']+=1;events.append(['unbind',edge])
    elif op==3 and ci is not None:
        fuel=s['carriers'][ci]
        if not fuel['charged'] and s['photons'][cell]>3:
            source_id=s['atoms'][b]['owner'] if b is not None else None;obj=s['objects'][source_id] if source_id is not None else None
            changed=int(s['arm']=='shuffled' and t>=1024);compatible=obj is not None and s['arm']!='inert' and (channel(obj['kind'])+changed)%4==fuel['lane'];value=d[6]%256
            if value<8 or compatible and value<64:
                source=obj if compatible and value>=8 else None;ancestry=dict(step=t,donor=source['id'] if source else None,kind=source['kind'] if source else None,assisted=source['assisted'] if source else False)
                fuel['charged']=True;fuel['charge']=ancestry;s['photons'][cell]-=4;s['heat']+=1;s['stats']['capture']+=1;s['stats']['catalytic' if source else 'basal']+=1;events.append(['capture',ci,ancestry])
    elif op in (4,5) and a is not None and a!=b and cj is not None and s['carriers'][cj]['charged']:
        x,y=s['atoms'][a],s['atoms'][b]
        if op==4 and x['status']==y['status']=='raw':events.append(['manufacture',assemble(s,[a,b],cj,t)])
        elif op==5 and s['arm']!='no-recycle' and x['status']==y['status']=='waste':
            fuel=s['carriers'][cj];ancestry=json.loads(json.dumps(fuel['charge']));fuel['charged']=False;fuel['charge']=None
            for z in (x,y):z['status']='raw';z['recycled_at']=t
            s['heat']+=3;s['stats']['recycle']+=1
            if t>=3072:s['stats']['post_withdrawal_recycle']+=1
            events.append(['recycle',sorted((a,b)),cj,ancestry])
    elif op==6 and a is not None and s['atoms'][a]['owner'] is not None and d[7]%256<8:
        oid=s['atoms'][a]['owner'];degrade(s,oid,t,'decay');events.append(['decay',oid])
    elif op==7 and ci is not None and b is not None and s['carriers'][ci]['charged']:
        nodes=aggregate(s,b)
        if len(nodes)<=3:
            fuel=s['carriers'][ci];ancestry=json.loads(json.dumps(fuel['charge']));fuel['charged']=False;fuel['charge']=None
            s['heat']+=3;s['stats']['funded_motion']+=len(nodes);relocate(s,nodes,delta);events.append(['funded-move',nodes,delta,ci,ancestry])
    s['step']=t
    if s['thermal']==0 and s['zero_thermal'] is None:s['zero_thermal']=t
    if sum(s['photons'])==0 and s['zero_photons'] is None:s['zero_photons']=t
    if any(e[0] in ('bind','manufacture') for e in events):s['max_aggregate']=max(s['max_aggregate'],max(len(aggregate(s,i)) for i in range(40)))
    verify(s);return events
def summary(s):return dict(seed=s['seed'],arm=s['arm'],endpoint=len(s['rounds'])==2 and all(r['qualified'] for r in s['rounds']),rounds=s['rounds'],stats=s['stats'],zero_thermal=s['zero_thermal'],zero_photons=s['zero_photons'],charged_remaining=sum(c['charged'] for c in s['carriers']),removed=s['removed'],heat=s['heat'],thermal=s['thermal'],adhesive_edges=len(s['edges']),max_aggregate=s['max_aggregate'],active=sum(o['alive'] for o in s['objects']))
def audit_world(path,revision):
    with Path(path).open('rb') as stream:
        first=json.loads(next(stream));w=first['world'];s=genesis(w['seed'],w['arm'])
        if first!=dict(header=True,source_revision=revision,world=s):raise ValueError('Genesis/source mismatch')
        for t in range(1,4097):
            row=json.loads(next(stream));tokens=[random(s) for _ in range(8)];events=advance(s,t,tokens)
            if row!=dict(step=t,draws=tokens,events=events,state_sha256=hashlib.sha256(pack(s)).hexdigest()):raise ValueError('Independent event/RNG/state mismatch at '+str(t))
        final=json.loads(next(stream))
        if final!=dict(final=True,world=s) or stream.read():raise ValueError('Independent final/ancestry mismatch')
    return summary(s)
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--input',required=True);p.add_argument('--revision',required=True);args=p.parse_args()
    try:
        root=Path(args.input);records=json.loads((root/'records.json').read_bytes());seeds=sorted({r['seed'] for r in records})
        if len(seeds)!=4 or seeds[0] not in range(74000,74032,4) or seeds!=list(range(seeds[0],seeds[0]+4)):raise ValueError('Registered scope')
        expected=[(s,a) for s in seeds for a in MODES]
        if [(r['seed'],r['arm']) for r in records]!=expected:raise ValueError('Incomplete/reordered samples')
        if [audit_world(root/f'{s}-{a}.jsonl',args.revision) for s,a in expected]!=records:raise ValueError('Summary mismatch')
        print(json.dumps(dict(verified=True,worlds=24,transitions=24*4096,endpoints=sum(r['endpoint'] for r in records))))
    except (ValueError,KeyError,TypeError,StopIteration) as error:p.exit(2,str(error)+'\n')
