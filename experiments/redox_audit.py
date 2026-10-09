"""Independent REDOX transition interpreter. Does not import the producer."""
import argparse
import copy
import hashlib
import json
from pathlib import Path
import random

def canonical(x):return json.dumps(x,sort_keys=True,separators=(',',':')).encode()
def sha(x):return hashlib.sha256(canonical(x)).hexdigest()

def new_object(s,b,i,pos,typ,energy,assisted,paid,parents,repair=False):
    uid=len(b)
    item={'uid':uid,'slot':i,'atoms':[i*2,i*2+1],'kind':typ,'assisted':assisted,
          'photons':copy.deepcopy(paid),'parents':parents[:]}
    if any(p>=uid for p in parents):raise ValueError('Nonancestral parent')
    b.append(item);s['next_id']=len(b);s['birth_head']=sha([s['birth_head'],item])
    return {'uid':uid,'slot':i,'cell':pos,'kind':typ,'q':energy,'assisted':assisted,
            'photons':copy.deepcopy(paid),'used':0,'repair':repair}

def charge(s,cell,t):
    count=s['photons'][cell]
    if count<2:raise ValueError('Photon overdraft')
    s['photons'][cell]=count-2
    return [[16*cell+count-1,t],[16*cell+count-2,t]]

def initialize(seed,arm):
    if arm not in ('candidate','inert','background','mixed','withdrawal','supplied'):
        raise ValueError('Arm')
    r=random.Random(seed);places=[r.randrange(64) for _ in range(48)];types=[r.randrange(16) for _ in range(12)]
    s={'arm':arm,'slots':[],'photons':[16 for _ in range(64)],'thermal':256,'operator':16,
       'heat':0,'exported':0,'next_id':0,'birth_head':'0'*64,'lost':{},'endpoint':[],
       'exact':[],'stats':{k:0 for k in ['capture','formation','catalysis','decay','motion',
             'damage','functional_damage','genesis','genesis_refused','post_formation','post_catalysis']},'zeros':{}}
    b=[]
    for i in range(48):s['slots'].append(new_object(s,b,i,places[i],None,0,False,[],[]))
    if arm=='supplied':
        for i in range(12):
            old=s['slots'][i];where=old['cell']
            if s['operator']==0 or s['photons'][where]<2:s['stats']['genesis_refused']+=1
            else:
                photons=charge(s,where,-1);s['operator']-=1;s['heat']+=2
                s['slots'][i]=new_object(s,b,i,where,types[i],1,True,photons,[old['uid']])
                s['stats']['genesis']+=1
    return s,b,r

def draw(r):
    action=r.randrange(4);slot=r.randrange(48);token=r.getrandbits(64);kind=r.randrange(16)
    byte=r.randrange(256);direction=r.randrange(4);destination=r.randrange(64);noise=r.getrandbits(64)
    return [action,slot,token,kind,byte,direction,destination,noise]

def step(s,b,t,d):
    ev=[];counts=s['stats']
    if t==2048:
        if s['arm']=='withdrawal':
            s['exported']=sum(s['photons']);s['photons']=[0 for _ in range(64)]
            ev.append(['withdraw',s['exported']])
        for i in range(48):
            obj=s['slots'][i]
            if obj['kind'] is None or obj['cell']%8>=4:continue
            if obj['used']>0 and obj['assisted'] is False:
                s['lost'][str(i)]={'uid':obj['uid'],'kind':obj['kind']};counts['functional_damage']+=1
            counts['damage']+=1;s['heat']+=1
            s['slots'][i]=new_object(s,b,i,obj['cell'],None,0,obj['assisted'],[],[obj['uid']])
            ev.append(['damage',obj['uid'],s['slots'][i]['uid']])
    action,i,token,typ,byte,direction,destination,noise=d
    obj=s['slots'][i];where=obj['cell'];event=['refuse',action,obj['uid']]
    if action==0:
        if obj['kind'] is None and obj['q']==0 and s['photons'][where]>=2:
            obj['q']=2;obj['photons']=charge(s,where,t);counts['capture']+=1
            event=['capture',obj['uid'],copy.deepcopy(obj['photons'])]
    if action==1 and obj['kind'] is None and obj['q']==2:
        near=[]
        for other in s['slots']:
            dx=abs(where%8-other['cell']%8);dy=abs(where//8-other['cell']//8)
            if other['slot']!=i and min(dx,8-dx)+min(dy,8-dy)<=1:near.append(other)
        catalyst=near[token%len(near)] if near else None
        base=19 if s['arm']=='background' else 4
        matches=False
        if catalyst and catalyst['kind'] is not None and s['arm']!='inert':
            key='REDOX-01|'+str(catalyst['kind'])+'|'+str(typ)
            matches=hashlib.sha256(key.encode('ascii')).digest()[0]%4==0
        threshold=64 if matches else base
        if byte<threshold:
            causal=matches and byte>=base
            aided=obj['assisted'] or bool(causal and catalyst['assisted'])
            parents=[obj['uid']]
            if causal:parents.append(catalyst['uid'])
            repaired=(str(i) in s['lost'] and causal and not aided
                      and all(x[1]>=2048 for x in obj['photons']))
            new=new_object(s,b,i,where,typ,1,aided,obj['photons'],parents,repaired)
            s['slots'][i]=new;s['heat']+=1;counts['formation']+=1
            if t>=2048:counts['post_formation']+=1
            if causal:
                catalyst['used']+=1;counts['catalysis']+=1
                if t>=2048:counts['post_catalysis']+=1
                if catalyst['repair'] and catalyst['uid'] not in s['endpoint']:
                    s['endpoint'].append(catalyst['uid'])
                    if catalyst['kind']==s['lost'][str(catalyst['slot'])]['kind']:
                        s['exact'].append(catalyst['uid'])
            event=['form',obj['uid'],new['uid'],catalyst['uid'] if causal else None]
    if action==2:
        price=2 if s['arm']=='mixed' else 1
        if s['thermal']>=price:
            s['thermal']-=price;s['heat']+=price;counts['motion']+=1
            if s['arm']=='mixed':obj['cell']=destination
            else:
                x,y=where%8,where//8
                if direction==0:x=(x+1)%8
                elif direction==1:x=(x-1)%8
                elif direction==2:y=(y+1)%8
                else:y=(y-1)%8
                obj['cell']=y*8+x
            event=['move',obj['uid'],where,obj['cell'],price]
    if action==3 and obj['kind'] is not None and byte<16:
        s['heat']+=1;counts['decay']+=1
        new=new_object(s,b,i,where,None,0,obj['assisted'],[],[obj['uid']])
        s['slots'][i]=new;event=['decay',obj['uid'],new['uid']]
    ev.append(event)
    for resource,remaining in [('photons',sum(s['photons'])),('thermal',s['thermal']),
                               ('buffer',sum(obj['q'] for obj in s['slots']))]:
        if remaining==0 and resource not in s['zeros']:s['zeros'][resource]=t
    if sum(s['photons'])+s['thermal']+s['operator']+s['heat']+s['exported']+sum(x['q'] for x in s['slots'])!=1296:
        raise ValueError('Energy residual')
    if any(x<0 for x in s['photons']) or s['thermal']<0 or s['operator']<0:raise ValueError('Overdraft')
    if {x['slot'] for x in s['slots']}!=set(range(48)) or len({x['uid'] for x in s['slots']})!=48:
        raise ValueError('Material ownership')
    if any(x['q'] not in (0,2) if x['kind'] is None else x['q']!=1 for x in s['slots']):
        raise ValueError('Chemical state')
    return ev

def record(s,b,seed):
    return {'seed':seed,'arm':s['arm'],'endpoint':bool(s['endpoint']),'exact':bool(s['exact']),
            'exposed':bool(s['lost']),'stats':s['stats'],'zeros':s['zeros'],
            'photons':sum(s['photons']),'buffer':sum(x['q'] for x in s['slots']),
            'thermal':s['thermal'],'operator':s['operator'],'heat':s['heat'],'exported':s['exported'],
            'final_hash':sha(s),'births':len(b)}

def audit_world(path,revision):
    with Path(path).open('rb') as incoming:
        header=json.loads(next(incoming));seed,arm=header['seed'],header['arm']
        if header['source_revision']!=revision:raise ValueError('Source mismatch')
        s,b,r=initialize(seed,arm)
        if header['initial']!=s or canonical(header['initial_rng'])!=canonical(r.getstate()):raise ValueError('Initial state')
        for t in range(4096):
            row=json.loads(next(incoming));d=draw(r)
            if row['t']!=t or row['draws']!=d:raise ValueError('Draw/cursor mismatch')
            if row['events']!=step(s,b,t,d) or row['state_hash']!=sha(s):raise ValueError('Transition/payment/provenance mismatch')
        final=json.loads(next(incoming))
        if incoming.read():raise ValueError('Unexpected trailing data')
        if final['final']!=s or final['births']!=b or canonical(final['rng'])!=canonical(r.getstate()):
            raise ValueError('Complete final history/RNG mismatch')
        if final['draw_calls']!=32828 or final['record']!=record(s,b,seed):raise ValueError('Endpoint/cursor mismatch')
        return final['record']

def audit_batch(root,revision):
    paths=sorted(Path(root).glob('*.jsonl'));expected=json.loads((Path(root)/'records.json').read_bytes())
    results=[audit_world(p,revision) for p in paths]
    if len(results)!=24 or sorted(results,key=lambda x:(x['seed'],x['arm']))!=sorted(expected,key=lambda x:(x['seed'],x['arm'])):
        raise ValueError('Panel records mismatch')
    return {'worlds':len(results),'steps':len(results)*4096,'energy_material_identity_and_rng':True}

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--input',required=True);p.add_argument('--revision',required=True)
    a=p.parse_args();print(json.dumps(audit_batch(a.input,a.revision)))
