"""Separate CARRIER-01 event interpreter. Does not import the producer."""
import argparse
import hashlib
import json
from pathlib import Path

MODES=('candidate','inert','private','shuffled','no-recycle','supplied')
COUNTERS=('capture','basal','catalytic','manufacture','recycle','motion','decay','damage',
          'after_damage_manufacture','after_damage_recycle','after_removal_manufacture','after_removal_recycle')


def token(s):
    n=s['rng'];n=(n^((n*8192)&4294967295))&4294967295
    n^=n//131072;n^=(n*32)&4294967295;s['rng']=n&4294967295
    return s['rng']


def encode(s):return json.dumps(s,sort_keys=True,separators=(',',':')).encode()


def channel(k):
    return hashlib.sha256(('CARRIER-01|%d|%d'%(k//4,k%4)).encode('ascii')).digest()[0]&3


def conservation(s):
    if len(s['atoms'])!=24 or len(s['carriers'])!=16:raise ValueError('Matter count')
    if sum(s['photons'])+s['thermal']+s['heat']+s['removed']+sum(3 if c['charged'] else 0 for c in s['carriers'])+sum(int(o['alive']) for o in s['objects'])!=640:
        raise ValueError('Energy residual')
    if min(s['photons']+[s['thermal'],s['heat'],s['removed']])<0:raise ValueError('Negative resource')
    for i,a in enumerate(s['atoms']):
        if a['type']!=i//6 or not 0<=a['pos']<8:raise ValueError('Atom identity')
        if a['status']=='component':
            if a['owner'] is None:raise ValueError('Owner missing')
            o=s['objects'][a['owner']]
            if not o['alive'] or i not in o['atoms'] or a['pos']!=o['pos']:raise ValueError('Ownership mismatch')
        elif a['status'] not in ('raw','waste') or a['owner'] is not None:raise ValueError('Material form')
    for i,o in enumerate(s['objects']):
        if o['id']!=i or len(set(o['atoms']))!=2:raise ValueError('Object identity')
        if o['alive'] and any(s['atoms'][a]['owner']!=i for a in o['atoms']):raise ValueError('Bound atoms')
    for i,c in enumerate(s['carriers']):
        if c['lane']!=i%4 or not 0<=c['pos']<8 or c['charged']!=(c['charge'] is not None):raise ValueError('Carrier identity/state')


def build(s,pair,ci,t):
    a,b=pair;left,right=s['atoms'][a],s['atoms'][b];fuel=s['carriers'][ci]
    ancestry=json.loads(json.dumps(fuel['charge']))
    low,high=min(left['type'],right['type']),max(left['type'],right['type'])
    k=4*low+high;oid=len(s['objects']);helped=left['assisted'] or right['assisted'] or ancestry['assisted']
    recycled=True
    for material in (left,right):
        recycled &= material['waste_at'] is not None and material['waste_at']>=512 and material['recycled_at'] is not None and material['recycled_at']>512
    qualified=(not helped and k in s['lost'] and recycled and ancestry['step']>512
               and ancestry['donor'] is not None and not ancestry['assisted'] and ancestry['kind']!=k)
    o=dict(id=oid,atoms=sorted(pair),kind=k,pos=left['pos'],alive=True,born=t,assisted=bool(helped),
           energy_parent=ancestry,atom_parents=[left['history'][:],right['history'][:]],
           restore_source_kind=ancestry['kind'] if qualified else None)
    s['objects'].append(o)
    for material in (left,right):
        material['status']='component';material['owner']=oid;material['history'].append(oid)
        material['assisted']=bool(material['assisted'] or helped)
    fuel['charged']=False;fuel['charge']=None;s['heat']+=2;s['stats']['manufacture']+=1
    if t>512:s['stats']['after_damage_manufacture']+=1
    if t>=1536:s['stats']['after_removal_manufacture']+=1
    src=ancestry['donor']
    if src is not None and not helped and ancestry['kind']!=k:
        s['productive']=sorted(set(s['productive'])|{src})
        earlier=s['objects'][src]
        if earlier['restore_source_kind']==k and ancestry['step']>512 and t<1536:s['endpoint']=True
    return o


def genesis(seed,mode):
    if seed not in range(73000,73032) or mode not in MODES:raise ValueError('Unregistered genesis')
    s=dict(seed=seed,arm=mode,rng=seed,step=0,photons=[64 for _ in range(8)],thermal=128,heat=0,removed=0,
           atoms=[],carriers=[],objects=[],productive=[],lost=[],endpoint=False,
           stats=dict.fromkeys(COUNTERS,0),zero_photons=None,zero_thermal=None,genesis=[])
    for i in range(24):s['atoms'].append(dict(type=i//6,pos=token(s)%8,status='raw',owner=None,waste_at=None,recycled_at=None,assisted=False,history=[]))
    for i in range(16):s['carriers'].append(dict(lane=i%4,pos=token(s)%8,charged=False,charge=None))
    if mode=='supplied':
        for a,b in ((0,1),(2,3),(4,5),(6,7)):
            dest=s['atoms'][a]['pos']
            for moving in (s['atoms'][b],s['carriers'][0]):
                difference=abs(dest-moving['pos']);cost=min(difference,8-difference)
                moving['pos']=dest;s['thermal']-=cost;s['heat']+=cost;s['stats']['motion']+=cost
                s['genesis'].append(['transport',cost,dest])
            s['photons'][dest]-=4;s['heat']+=1;s['stats']['capture']+=1;s['stats']['basal']+=1
            s['carriers'][0]['charged']=True;s['carriers'][0]['charge']=dict(step=0,donor=None,kind=None,atoms=None,assisted=False)
            s['atoms'][a]['assisted']=s['atoms'][b]['assisted']=True
            s['genesis'].append(['founder',build(s,[a,b],0,0)])
    conservation(s)
    return s


def dissolve(s,oid,t,reason):
    obj=s['objects'][oid];obj['alive']=False
    for a in obj['atoms']:
        s['atoms'][a]['status']='waste';s['atoms'][a]['owner']=None;s['atoms'][a]['waste_at']=t
    s['heat']+=1;s['stats'][reason]+=1


def advance(s,t,d):
    events=[]
    if t==512:
        destroyed=sorted(o['id'] for o in s['objects'] if o['alive'] and o['pos'] in range(4))
        previously={s['objects'][i]['kind'] for i in destroyed if i in s['productive'] and not s['objects'][i]['assisted']}
        for oid in destroyed:dissolve(s,oid,t,'damage')
        survivors={o['kind'] for o in s['objects'] if o['alive']}
        s['lost']=sorted(previously-survivors);events.append(['damage',destroyed,s['lost'][:]])
    if t==1536:
        left=sum(s['photons']);s['removed']+=left;s['photons']=[0 for _ in range(8)];events.append(['remove-photons',left])
    op=d[0]%6;cidx=d[1]%16;i=d[2]%24;j=d[3]%24;anch=d[4]%24;delta=1 if d[5]%2 else -1
    x,y=s['atoms'][i],s['atoms'][j];c=s['carriers'][cidx]
    oid=s['atoms'][anch]['owner'];o=s['objects'][oid] if oid is not None else None
    if op in (0,1) and s['thermal']>0:
        if op==1:
            c['pos']=(c['pos']+delta)%8;events.append(['move-carrier',cidx,delta])
        elif x['owner'] is None:
            x['pos']=(x['pos']+delta)%8;events.append(['move-atoms',[i],delta])
        else:
            obj=s['objects'][x['owner']];obj['pos']=(obj['pos']+delta)%8
            for atom in obj['atoms']:s['atoms'][atom]['pos']=obj['pos']
            events.append(['move-atoms',obj['atoms'][:],delta])
        s['thermal']-=1;s['heat']+=1;s['stats']['motion']+=1
    elif op==2 and not c['charged'] and s['photons'][c['pos']]>3:
        changed=int(s['arm']=='shuffled' and t>=512)
        enhanced=o is not None and s['arm']!='inert' and o['pos']==c['pos'] and (channel(o['kind'])+changed)%4==c['lane']
        accepted=d[6]%256
        if accepted<8 or (enhanced and accepted<64):
            source=o if enhanced and accepted>=8 else None
            ancestry=dict(step=t,donor=source['id'] if source else None,kind=source['kind'] if source else None,
                          atoms=source['atoms'][:] if source else None,assisted=source['assisted'] if source else False)
            c['charged']=True;c['charge']=ancestry;s['photons'][c['pos']]-=4;s['heat']+=1
            s['stats']['capture']+=1;s['stats']['catalytic' if source else 'basal']+=1;events.append(['charge',cidx,ancestry])
    elif op in (3,4) and i!=j and x['pos']==y['pos']==c['pos'] and c['charged']:
        allowed=s['arm']!='private' or c['charge']['donor'] is None or sorted([i,j])==c['charge']['atoms']
        if allowed and op==3 and x['status']==y['status']=='raw':events.append(['manufacture',build(s,[i,j],cidx,t)])
        elif allowed and op==4 and s['arm']!='no-recycle' and x['status']==y['status']=='waste':
            ancestry=json.loads(json.dumps(c['charge']));c['charged']=False;c['charge']=None
            for atom in (x,y):atom['status']='raw';atom['recycled_at']=t
            s['heat']+=3;s['stats']['recycle']+=1
            if t>512:s['stats']['after_damage_recycle']+=1
            if t>=1536:s['stats']['after_removal_recycle']+=1
            events.append(['recycle',sorted([i,j]),cidx,ancestry])
    elif op==5 and o is not None and d[7]%256<8:
        dissolve(s,oid,t,'decay');events.append(['decay',oid])
    s['step']=t
    if not any(s['photons']) and s['zero_photons'] is None:s['zero_photons']=t
    if not s['thermal'] and s['zero_thermal'] is None:s['zero_thermal']=t
    conservation(s)
    return events


def audit_world(path,revision):
    with Path(path).open('rb') as stream:
        header=json.loads(next(stream));initial=header['world'];s=genesis(initial['seed'],initial['arm'])
        if header!=dict(header=True,source_revision=revision,world=s):raise ValueError('Genesis/source mismatch')
        for t in range(1,2049):
            row=json.loads(next(stream));draws=[token(s) for _ in range(8)];events=advance(s,t,draws)
            expected=dict(step=t,draws=draws,events=events,state_sha256=hashlib.sha256(encode(s)).hexdigest())
            if row!=expected:raise ValueError('Draw/event/state mismatch at '+str(t))
        final=json.loads(next(stream))
        if final!=dict(final=True,world=s) or stream.read():raise ValueError('Final snapshot/history mismatch')
    return dict(seed=s['seed'],arm=s['arm'],endpoint=s['endpoint'],exposed=bool(s['lost']),lost=s['lost'],stats=s['stats'],
                zero_photons=s['zero_photons'],zero_thermal=s['zero_thermal'],charged_remaining=sum(c['charged'] for c in s['carriers']),
                thermal=s['thermal'],heat=s['heat'],removed=s['removed'],active=sum(c['alive'] for c in s['objects']))


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--input',required=True);p.add_argument('--revision',required=True);args=p.parse_args()
    try:
        root=Path(args.input);records=json.loads((root/'records.json').read_bytes());seeds=sorted({r['seed'] for r in records})
        if len(seeds)!=4 or seeds[0] not in range(73000,73032,4) or seeds!=list(range(seeds[0],seeds[0]+4)):raise ValueError('Registered batch scope')
        expected=[(s,a) for s in seeds for a in MODES]
        if [(r['seed'],r['arm']) for r in records]!=expected:raise ValueError('Missing/duplicate/reordered arm')
        actual=[audit_world(root/f'{s}-{a}.jsonl',args.revision) for s,a in expected]
        if actual!=records:raise ValueError('Records differ from independent histories')
        print(json.dumps(dict(verified=True,worlds=24,transitions=24*2048,endpoints=sum(r['endpoint'] for r in actual))))
    except (ValueError,KeyError,TypeError,StopIteration) as error:p.exit(2,str(error)+'\n')
