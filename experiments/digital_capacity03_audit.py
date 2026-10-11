"""Independent capacity03 interpreter; no producer import."""
import hashlib,json

def h(x):return hashlib.sha256(json.dumps(x,sort_keys=True,separators=(',',':')).encode()).hexdigest()
def clone(x):return json.loads(json.dumps(x))

def types(x,key=None):
    if key in ('mutated','ancestor_supplied','checkpoint_replay','learning_demonstrated'):assert type(x) is bool
    elif isinstance(x,dict):
        for k,v in x.items():types(v,k)
    elif isinstance(x,list):
        for v in x:types(v)
    else:assert x is None or type(x) in (int,str)

def body(identity,parent,generation,code,units,pos):
    return dict(id=identity,parent=parent,generation=generation,code=code,state_units=units,
                memory=[0]*8,registers=[0,0],pc=0,cue=0,feedback=0,inbox=None,pos=pos,energy=12,nursery=[])

def audit(row):
    types(row)
    assert row['version']=='DIGITAL-CAPACITY-03-v1'
    witness=[[2,0,0],[6,0,0],[1,1,0],[8,1,10],[10,0,0],[12,0,0],[4,1,1],[13,1,0],[7,0,0],[31,0,0],[4,1,1],[5,0,1],[3,0,0],[6,0,0],[1,1,0],[8,1,6],[7,0,4],[31,0,0],[31,0,0],[31,0,0]]
    fixed=[[4,0,0],[6,0,0],[10,0,0],[12,0,0],[4,1,1],[13,1,0],[7,0,0]]
    programs={'witness':witness,'disconnected':[[4,0,0]]+witness[1:],
              'fixed':fixed,'parity':[[0,0,0]]+fixed[1:],
              'padded_fixed':fixed+[[31,0,0] for _ in range(13)]}
    assert row['route'] in programs
    assert row['genesis_program']==programs[row['route']]
    assert row['mode']=='faithful'
    assert row['ancestor_supplied'] and row['checkpoint_replay'] and not row['learning_demonstrated']
    seed=row['seed'];mode=row['mode'];assert type(seed) is int and seed>=0 and mode in ('mutating','faithful','copy_disabled')
    code=sum(row['genesis_program'],[]);bill=len(code)+16
    org={0:body(0,None,0,[[v,i] for i,v in enumerate(code)],list(range(len(code),bill)),0)}
    occupied=set(range(bill));food={i:[i//16,int(h([seed,'food',i])[:8],16)%2] for i in range(64)}
    formation=[dict(unit=i,value=v,energy=1,assistance='supplied ancestor assembly') for i,v in enumerate(code+[0]*16)]
    heat=bill;constructor=128-bill;writes=0;last=-1;next_id=1;births=deaths=0;maximum=1;events=[];tick=0
    certificates={};successful_food=failed_food=mutations=desc_births=messages=0
    def snapshot(include_events=True):
        state=dict(seed=seed,mode=mode,tick=tick,last=last,next_id=next_id,writes=writes,
                   constructor_remaining=constructor,heat=heat,formation=formation,food=food,
                   free=sorted(set(range(512))-occupied),entities=org,births=births,deaths=deaths,maximum=maximum)
        if include_events:state['events']=events
        return clone(state)
    assert len(row['final']['events'])<=1536
    for observed in row['final']['events']:
        tick+=1;ids=sorted(org);actor=next((i for i in ids if i>last),ids[0]);last=actor
        e=org[actor];n=len(e['code'])//3;opcode,a,b=[word[0] for word in e['code'][3*e['pc']:3*e['pc']+3]]
        event=dict(tick=tick,actor=actor,decoded=[opcode,a,b],before=h(e),outcome='executed')
        e['energy']-=1;heat+=1;e['pc']=(e['pc']+1)%n;r=e['registers']
        neighbors=[org[i] for i in ids if i!=actor and org[i]['pos']==e['pos']]
        local=sorted(i for i in food if food[i][0]==e['pos'])
        if opcode==0:
            e['cue']=e['pos'];r[a%2]=e['cue'];event['cue']=e['cue']
        if opcode==1:r[a%2]=e['feedback']
        if opcode==2:r[a%2]=e['memory'][b%8]
        if opcode==3:e['memory'][a%8]=r[b%2]
        if opcode==4:r[a%2]=b%16
        if opcode==5:r[a%2]=r[a%2]^r[b%2]
        if opcode==6:
            e['feedback']=0
            if local:
                packet=local[0];position,kind=food.pop(packet);target=0 if position==0 else int(h([seed,'site-port',position])[:8],16)%2
                e['feedback']=int(r[a%2]%2==target)
                event['attempt']=dict(packet=packet,position=position,cue=kind,port=r[a%2]%2,target=target,success=e['feedback'])
                if e['feedback']:
                    overflow=max(0,e['energy']+20-64);e['energy']+=20-overflow;heat+=overflow;successful_food+=1
                else:heat+=20;failed_food+=1
            event['feedback']=e['feedback']
        if opcode==7:e['pc']=b%n
        if opcode==8 and r[a%2]==0:e['pc']=b%n
        if opcode==9:
            address=b%len(e['code']);old=e['code'][address][0];e['code'][address][0]=r[a%2]
            event['self_write']=dict(unit=e['code'][address][1],index=address,old=old,value=r[a%2])
        if opcode==10:
            if mode!='copy_disabled' and len(e['nursery'])<len(e['code']) and 512-len(occupied)>=3 and e['energy']>=3:
                records=[];start=len(e['nursery'])
                for index in range(start,start+3):
                    source=e['code'][index];value=source[0];draw=int(h([seed,'mutation',writes])[:16],16)
                    if mode=='mutating' and draw%100<8:value=(value+1+(draw//100)%31)%32
                    unit=min(set(range(512))-occupied);occupied.add(unit)
                    entry=dict(unit=unit,value=value,index=index,tick=tick,source_unit=source[1],source_value=source[0],write_id=writes,mutated=value!=source[0])
                    certificates[writes]=(actor,clone(entry));writes+=1;mutations+=int(value!=source[0]);records.append(entry);e['nursery'].append(clone(entry))
                e['energy']-=3;heat+=3;event['writes']=records
            else:event['outcome']='copy_refused'
        if opcode==11 and len(e['nursery'])<len(e['code']):e['pc']=b%n
        if opcode==12:
            if len(e['nursery'])==len(e['code']) and e['energy']>=30 and 512-len(occupied)>=16 and len(org)<32:
                units=sorted(set(range(512))-occupied)[:16];occupied.update(units)
                assert all(certificates[w['write_id']]==(actor,w) for w in e['nursery'])
                child=body(next_id,actor,e['generation']+1,[[w['value'],w['unit']] for w in e['nursery']],units,e['pos'])
                event['birth']=dict(child=clone(child),write_ids=[w['write_id'] for w in e['nursery']],state_formation=[dict(unit=u,value=e['pos'] if i==14 else 0,energy=1) for i,u in enumerate(units)],release_energy=2,startup_energy=12)
                org[next_id]=child;next_id+=1;births+=1;desc_births+=int(e['generation']>0)
                e['energy']-=30;heat+=18;e['nursery']=[]
            else:event['outcome']='division_refused'
        if opcode==13:e['pos']=(e['pos']+(1 if r[a%2]%2 else -1))%4
        if opcode==14 and neighbors and neighbors[0]['inbox'] is None:
            neighbors[0]['inbox']=r[a%2];event['message']=dict(recipient=neighbors[0]['id'],value=r[a%2]);messages+=1
        if opcode==15 and e['inbox'] is not None:r[a%2]=e['inbox'];e['inbox']=None
        if opcode==16 and neighbors and e['energy']>=1 and neighbors[0]['energy']<64:
            e['energy']-=1;neighbors[0]['energy']+=1;event['transfer']=neighbors[0]['id']
        if opcode==17:heat+=e['energy'];e['energy']=0;event['outcome']='halt'
        if e['energy']==0:
            released=[g[1] for g in e['code']]+e['state_units']+[w['unit'] for w in e['nursery']]
            occupied.difference_update(released);del org[actor];deaths+=1;event['death']=released
        else:event['after']=clone(e)
        maximum=max(maximum,len(org))
        assert sum(o['energy'] for o in org.values())+constructor+heat+20*len(food)==1420
        owned=[v[1] for o in org.values() for v in o['code']]+[u for o in org.values() for u in o['state_units']]+[w['unit'] for o in org.values() for w in o['nursery']]
        assert len(owned)==len(set(owned)) and set(owned)==occupied and occupied<=set(range(512)) and len(org)<=32
        event['state_hash']=h(snapshot(False));assert observed==event;events.append(clone(event))
        if tick==min(64,row['final']['tick']):assert row['checkpoint']==snapshot()
    final=snapshot();assert row['final']==final and row['hash']==h(final)
    assert tick==1536 or not org
    assert row['checkpoint']['tick']==min(64,tick)
    retries=[]
    for event in events:
        attempt=event.get('attempt')
        if not attempt or not attempt['success']:continue
        prior=[e for e in events[:event['tick']-1] if e['actor']==event['actor'] and e.get('attempt',{}).get('position')==attempt['position']]
        if prior and not prior[-1]['attempt']['success']:
            failed=prior[-1]
            writes_between=[e['tick'] for e in events[failed['tick']:event['tick']-1] if e['actor']==event['actor'] and e['decoded'][0]==3]
            if writes_between:retries.append(dict(actor=event['actor'],site=attempt['position'],failed_tick=failed['tick'],write_ticks=writes_between,success_tick=event['tick']))
    return dict(paid_retry_witnesses=retries,verified=True,seed=seed,route=row['route'],mode=mode,ticks=tick,births=births,descendant_births=desc_births,deaths=deaths,
                successful_food=successful_food,failed_food=failed_food,unused_food=len(food),paid_copy_words=writes,
                mutations=mutations,maximum_population=maximum,heat=heat,live_energy=sum(e['energy'] for e in org.values()),
                free_material=512-len(occupied),messages=messages,change_exposed=sum('attempt' in ev and ev['attempt']['position']!=0 and ev['attempt']['target']==1 for ev in events),
                remote_food=sum(bool(ev.get('attempt',{}).get('success')) and ev['attempt']['position']!=0 for ev in events),
                descendant_remote_food=sum(bool(ev.get('attempt',{}).get('success')) and ev['attempt']['position']!=0 and ev['actor']!=0 for ev in events),
                repeated_hidden_port_actors=len({ev['actor'] for ev in events if 'attempt' in ev and ev['attempt']['position']!=0 and ev['attempt']['target']==1 and sum('attempt' in prior and prior['actor']==ev['actor'] and prior['attempt']['position']==ev['attempt']['position'] for prior in events[:ev['tick']-1])>=1}),
                learning=False,evolution=False,repair=False)

if __name__=='__main__':
    import sys
    print(json.dumps([audit(row) for row in json.load(open(sys.argv[1],encoding='utf-8'))],sort_keys=True))
