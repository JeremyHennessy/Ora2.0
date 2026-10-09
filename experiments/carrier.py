"""CARRIER-01 finite chemistry; no organism policy, service or external API."""
import argparse
import copy
import hashlib
import json
from pathlib import Path
import zipfile
from .evidence_budget import Budget
from .evidence_budget_audit import audit as storage_audit

ARMS=('candidate','inert','private','shuffled','no-recycle','supplied')
STAT=('capture','basal','catalytic','manufacture','recycle','motion','decay','damage',
      'after_damage_manufacture','after_damage_recycle','after_removal_manufacture','after_removal_recycle')


def draw(w):
    x=w['rng'];x^=(x<<13)&0xffffffff;x^=x>>17;x^=(x<<5)&0xffffffff
    w['rng']=x&0xffffffff
    return w['rng']


def lane(kind):
    u,v=divmod(kind,4)
    return hashlib.sha256(f'CARRIER-01|{u}|{v}'.encode('ascii')).digest()[0]%4


def canonical(w):
    return json.dumps(w,sort_keys=True,separators=(',',':')).encode()


def check(w):
    if sum(w['photons'])+3*sum(c['charged'] for c in w['carriers'])+sum(c['alive'] for c in w['objects'])+w['thermal']+w['heat']+w['removed']!=640:
        raise ValueError('Energy accounting')
    if w['thermal']<0 or any(x<0 for x in w['photons']):raise ValueError('Negative resource')
    for i,a in enumerate(w['atoms']):
        if a['status']=='component':
            c=w['objects'][a['owner']]
            if not c['alive'] or i not in c['atoms'] or a['pos']!=c['pos']:raise ValueError('Atom ownership')
        elif a['owner'] is not None:raise ValueError('Free atom owner')
    for c in w['objects']:
        if c['alive'] and any(w['atoms'][i]['owner']!=c['id'] for i in c['atoms']):raise ValueError('Component provenance')


def new(seed,arm):
    if not 73000<=seed<73032 or arm not in ARMS:raise ValueError('Registered samples only')
    w=dict(seed=seed,arm=arm,rng=seed,step=0,photons=[64]*8,thermal=128,heat=0,removed=0,
           atoms=[],carriers=[],objects=[],productive=[],lost=[],endpoint=False,
           stats={s:0 for s in STAT},zero_photons=None,zero_thermal=None,genesis=[])
    for i in range(24):
        w['atoms'].append(dict(type=i//6,pos=draw(w)%8,status='raw',owner=None,
                               waste_at=None,recycled_at=None,assisted=False,history=[]))
    for i in range(16):
        w['carriers'].append(dict(lane=i%4,pos=draw(w)%8,charged=False,charge=None))
    if arm=='supplied':
        for a,b in ((0,1),(2,3),(4,5),(6,7)):
            target=w['atoms'][a]['pos'];other=w['atoms'][b]
            for obj in (other,w['carriers'][0]):
                cost=min((target-obj['pos'])%8,(obj['pos']-target)%8)
                w['thermal']-=cost;w['heat']+=cost;w['stats']['motion']+=cost;obj['pos']=target
                w['genesis'].append(['transport',cost,target])
            w['photons'][target]-=4;w['heat']+=1
            w['carriers'][0].update(charged=True,charge=dict(step=0,donor=None,kind=None,atoms=None,assisted=False))
            w['stats']['capture']+=1;w['stats']['basal']+=1
            for i in (a,b):w['atoms'][i]['assisted']=True
            w['genesis'].append(['founder',make(w,a,b,0,0)])
    check(w)
    return w


def usable(w,ci,pair):
    c=w['carriers'][ci]
    return c['charged'] and (w['arm']!='private' or c['charge']['donor'] is None or sorted(pair)==c['charge']['atoms'])


def make(w,a,b,ci,t):
    atoms=[w['atoms'][a],w['atoms'][b]];fuel=w['carriers'][ci];parent=copy.deepcopy(fuel['charge'])
    u,v=sorted(x['type'] for x in atoms);kind=4*u+v;identity=len(w['objects'])
    assisted=any(x['assisted'] for x in atoms) or parent['assisted']
    recovered=all(x['waste_at'] is not None and x['waste_at']>=512 and x['recycled_at'] is not None and x['recycled_at']>512 for x in atoms)
    restore=(not assisted and kind in w['lost'] and recovered and parent['step']>512
             and parent['donor'] is not None and not parent['assisted'] and parent['kind']!=kind)
    obj=dict(id=identity,atoms=sorted([a,b]),kind=kind,pos=atoms[0]['pos'],alive=True,born=t,
             assisted=assisted,energy_parent=parent,atom_parents=[x['history'].copy() for x in atoms],
             restore_source_kind=parent['kind'] if restore else None)
    w['objects'].append(obj)
    for x in atoms:x.update(status='component',owner=identity,history=x['history']+[identity],assisted=x['assisted'] or assisted)
    fuel.update(charged=False,charge=None);w['heat']+=2;w['stats']['manufacture']+=1
    if t>512:w['stats']['after_damage_manufacture']+=1
    if t>=1536:w['stats']['after_removal_manufacture']+=1
    if parent['donor'] is not None and not assisted and parent['kind']!=kind:
        if parent['donor'] not in w['productive']:w['productive'].append(parent['donor']);w['productive'].sort()
        donor=w['objects'][parent['donor']]
        if donor['restore_source_kind']==kind and parent['step']>512 and t<1536:w['endpoint']=True
    return obj


def kill(w,identity,t,label):
    c=w['objects'][identity];c['alive']=False
    for i in c['atoms']:w['atoms'][i].update(status='waste',owner=None,waste_at=t)
    w['heat']+=1;w['stats'][label]+=1


def tick(w,t,draws):
    events=[]
    if t==512:
        ids=[c['id'] for c in w['objects'] if c['alive'] and c['pos']<4]
        possible={w['objects'][i]['kind'] for i in ids if i in w['productive'] and not w['objects'][i]['assisted']}
        for i in ids:kill(w,i,t,'damage')
        w['lost']=sorted(k for k in possible if not any(c['alive'] and c['kind']==k for c in w['objects']))
        events.append(['damage',ids,w['lost'].copy()])
    if t==1536:
        n=sum(w['photons']);w['removed']+=n;w['photons']=[0]*8;events.append(['remove-photons',n])
    op,ci,a,b,anchor,direction,accept,decay=draws
    op%=6;ci%=16;a%=24;b%=24;anchor%=24
    carrier=w['carriers'][ci];x=w['atoms'][a];y=w['atoms'][b]
    selected=w['atoms'][anchor]['owner'];component=w['objects'][selected] if selected is not None else None
    if op==0 and w['thermal']:
        delta=1 if direction&1 else -1
        if x['owner'] is None:x['pos']=(x['pos']+delta)%8;ids=[a]
        else:
            c=w['objects'][x['owner']];c['pos']=(c['pos']+delta)%8;ids=c['atoms'].copy()
            for i in ids:w['atoms'][i]['pos']=c['pos']
        w['thermal']-=1;w['heat']+=1;w['stats']['motion']+=1;events.append(['move-atoms',ids,delta])
    elif op==1 and w['thermal']:
        delta=1 if direction&1 else -1;carrier['pos']=(carrier['pos']+delta)%8
        w['thermal']-=1;w['heat']+=1;w['stats']['motion']+=1;events.append(['move-carrier',ci,delta])
    elif op==2 and not carrier['charged'] and w['photons'][carrier['pos']]>=4:
        value=accept&255
        compatible=(component is not None and w['arm']!='inert' and component['pos']==carrier['pos']
                    and (lane(component['kind'])+(w['arm']=='shuffled' and t>=512))%4==carrier['lane'])
        if value<8 or compatible and value<64:
            donor=component if compatible and value>=8 else None
            source=dict(step=t,donor=donor['id'] if donor else None,kind=donor['kind'] if donor else None,
                        atoms=donor['atoms'].copy() if donor else None,assisted=donor['assisted'] if donor else False)
            w['photons'][carrier['pos']]-=4;w['heat']+=1;carrier.update(charged=True,charge=source)
            w['stats']['capture']+=1;w['stats']['catalytic' if donor else 'basal']+=1
            events.append(['charge',ci,source])
    elif op==3 and a!=b and x['status']==y['status']=='raw' and x['pos']==y['pos']==carrier['pos'] and usable(w,ci,[a,b]):
        events.append(['manufacture',make(w,a,b,ci,t)])
    elif op==4 and w['arm']!='no-recycle' and a!=b and x['status']==y['status']=='waste' and x['pos']==y['pos']==carrier['pos'] and usable(w,ci,[a,b]):
        source=copy.deepcopy(carrier['charge']);carrier.update(charged=False,charge=None)
        x.update(status='raw',recycled_at=t);y.update(status='raw',recycled_at=t)
        w['heat']+=3;w['stats']['recycle']+=1
        if t>512:w['stats']['after_damage_recycle']+=1
        if t>=1536:w['stats']['after_removal_recycle']+=1
        events.append(['recycle',sorted([a,b]),ci,source])
    elif op==5 and component is not None and decay&255<8:
        identity=component['id'];kill(w,identity,t,'decay');events.append(['decay',identity])
    w['step']=t
    if sum(w['photons'])==0 and w['zero_photons'] is None:w['zero_photons']=t
    if w['thermal']==0 and w['zero_thermal'] is None:w['zero_thermal']=t
    check(w)
    return events


def run_world(seed,arm,revision,stream,steps=2048):
    w=new(seed,arm)
    stream.write(canonical(dict(header=True,source_revision=revision,world=w))+b'\n')
    for t in range(1,steps+1):
        tokens=[draw(w) for _ in range(8)];events=tick(w,t,tokens)
        stream.write(canonical(dict(step=t,draws=tokens,events=events,state_sha256=hashlib.sha256(canonical(w)).hexdigest()))+b'\n')
    stream.write(canonical(dict(final=True,world=w))+b'\n')
    return dict(seed=seed,arm=arm,endpoint=w['endpoint'],exposed=bool(w['lost']),lost=w['lost'],
                stats=w['stats'],zero_photons=w['zero_photons'],zero_thermal=w['zero_thermal'],
                charged_remaining=sum(c['charged'] for c in w['carriers']),thermal=w['thermal'],
                heat=w['heat'],removed=w['removed'],active=sum(c['alive'] for c in w['objects']))


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--start',type=int,required=True)
    p.add_argument('--revision',required=True);p.add_argument('--output',required=True);args=p.parse_args()
    if args.start not in range(73000,73032,4):p.error('Registered batch start')
    b=Budget(Path(args.output),{'raw':32*1024**2,'archive':16*1024**2,'restore':32*1024**2,'failure':2*1024**2},82*1024**2)
    records=[]
    try:
        for seed in range(args.start,args.start+4):
            for arm in ARMS:
                with b.create('raw',f'{seed}-{arm}.jsonl') as out:records.append(run_world(seed,arm,args.revision,out))
        with b.create('raw','records.json') as out:out.write(canonical(records))
        import io
        payload=io.BytesIO()
        with zipfile.ZipFile(payload,'w',zipfile.ZIP_DEFLATED) as z:
            for q in (b.root/'raw').iterdir():z.write(q,q.name)
        with b.create('archive','complete.zip') as out:out.write(payload.getvalue())
        with zipfile.ZipFile(io.BytesIO(payload.getvalue())) as z:
            for item in z.infolist():
                with b.create('restore',item.filename,item.file_size) as out:out.write(z.read(item))
        for q in (b.root/'raw').iterdir():
            if q.read_bytes()!=(b.root/'restore'/q.name).read_bytes():raise ValueError('Restore differs')
        print(json.dumps(dict(worlds=24,transitions=24*2048,endpoints=sum(r['endpoint'] for r in records))))
    finally:
        with b.create('failure','budget.json',1024**2) as out:
            receipt=copy.deepcopy(b.snapshot());out.write(canonical(receipt))
        storage_audit(b.root,receipt,receipt['limits'],receipt['total_limit'])
