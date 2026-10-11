"""Independent singlecopy09 interpreter; no producer import."""
import hashlib,json

def h(x):return hashlib.sha256(json.dumps(x,sort_keys=True,separators=(',',':')).encode()).hexdigest()
def clone(x):return json.loads(json.dumps(x))

def sample(seed,key,size):
    maximum=4294967296-(4294967296%size);trail=[];attempt=0
    while attempt<16:
        candidate=int(h([seed,'draw',key,attempt])[0:8],16)
        trail.append({'key':key,'attempt':attempt,'word':candidate,'modulus':size,'energy':1})
        if candidate<maximum:return candidate%size,trail
        attempt+=1
    raise AssertionError('Frozen rejection-draw ceiling exceeded')

def types(x,key=None):
    if key in ('mutated','ancestor_supplied','checkpoint_replay','learning_demonstrated'):assert type(x) is bool
    elif isinstance(x,dict):
        for k,v in x.items():types(v,k)
    elif isinstance(x,list):
        for v in x:types(v)
    else:assert x is None or type(x) in (int,str)

def body(identity,parent,generation,code,units,pos):
    return dict(id=identity,parent=parent,generation=generation,code=code,state_units=units,
                memory=[0]*8,registers=[0,0],pc=0,cue=0,feedback=0,inbox=None,pos=pos,energy=12,nursery=[],selector=None)

def audit(row):
    types(row)
    assert row['version']=='DIGITAL-SINGLECOPY-09-v1'
    program=row['genesis_program']
    assert 1<=len(program)<=32 and all(type(x) is list and len(x)==3 and all(type(v) is int and 0<=v<32 for v in x) for x in program)
    assert row['ancestor_supplied'] and row['checkpoint_replay'] and not row['learning_demonstrated']
    seed=row['seed'];mode=row['mode'];assert type(seed) is int and seed>=0 and mode in ('single','per_word','faithful','copy_disabled')
    code=sum(row['genesis_program'],[]);bill=len(code)+18
    org={0:body(0,None,0,[[v,i] for i,v in enumerate(code)],list(range(len(code),bill)),0)}
    occupied=set(range(bill));food={i:[0 if i<32 else 1+(i-32)//16,int(h([seed,'food',i])[:8],16)%2] for i in range(64)}
    formation=[dict(unit=i,value=v,energy=1,assistance='supplied ancestor assembly') for i,v in enumerate(code+[0]*18)]
    heat=bill;constructor=128-bill;writes=0;last=-1;next_id=1;births=deaths=0;maximum=1;events=[];tick=0
    certificates={};successful_food=failed_food=mutations=desc_births=messages=0
    def snapshot(include_events=True):
        state=dict(seed=seed,mode=mode,tick=tick,last=last,next_id=next_id,writes=writes,
                   constructor_remaining=constructor,heat=heat,formation=formation,food=food,
                   free=sorted(set(range(512))-occupied),entities=org,births=births,deaths=deaths,maximum=maximum)
        if include_events:state['events']=events
        return clone(state)
    assert len(row['final']['events'])<=512
    for observed in row['final']['events']:
        tick+=1;ids=sorted(org);actor=next((i for i in ids if i>last),ids[0]);last=actor
        release=None
        if tick==64:
            assert constructor>=16
            constructor-=16;heat+=16
            release=dict(packets=list(range(16,32)),energy=16,assistance='supplied exogenous stock boundary')
        e=org[actor];n=len(e['code'])//3;opcode,a,b=[word[0] for word in e['code'][3*e['pc']:3*e['pc']+3]]
        event=dict(tick=tick,actor=actor,decoded=[opcode,a,b],before=h(e),outcome='executed')
        if release:event['release']=release
        e['energy']-=1;heat+=1;e['pc']=(e['pc']+1)%n;r=e['registers']
        neighbors=[org[i] for i in ids if i!=actor and org[i]['pos']==e['pos']]
        local=sorted(i for i in food if food[i][0]==e['pos'] and (not 16<=i<32 or tick>=64))
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
                packet=local[0];position,kind=food[packet];target=(seed%2 if position==0 else int(h([seed,'site-port',position])[:8],16)%2)^int(tick>=64)
                e['feedback']=int(r[a%2]%2==target)
                event['attempt']=dict(packet=packet,position=position,cue=kind,port=r[a%2]%2,target=target,success=e['feedback'])
                if e['feedback']:
                    del food[packet]
                    overflow=max(0,e['energy']+20-64);e['energy']+=20-overflow;heat+=overflow;successful_food+=1
                else:failed_food+=1
            event['feedback']=e['feedback']
        if opcode==7:e['pc']=b%n
        if opcode==8 and r[a%2]==0:e['pc']=b%n
        if opcode==9:
            address=b%len(e['code']);old=e['code'][address][0];e['code'][address][0]=r[a%2]
            event['self_write']=dict(unit=e['code'][address][1],index=address,old=old,value=r[a%2])
        if opcode==10:
            if mode!='copy_disabled' and len(e['nursery'])<len(e['code']) and 512-len(occupied)>=3:
                start=len(e['nursery']);initial=start==0;selected=e['selector'];draws=[]
                if initial:
                    address,log=sample(seed,['selector-index',writes],len(e['code']));draws.extend(log)
                    offset,log=sample(seed,['selector-offset',writes],31);draws.extend(log);selected=[address,offset+1]
                changes=[]
                for i in range(3):
                    index=start+i;word,log=sample(seed,['word',writes+i],len(e['code'])*31);draws.extend(log)
                    delta=0
                    if mode=='single' and index==selected[0]:delta=selected[1]
                    if mode=='per_word' and word%len(e['code'])==0:delta=word//len(e['code'])+1
                    changes.append((e['code'][index][0]+delta)%32)
                cost=3+len(draws)+(2 if initial else 0)
                if e['energy']>=cost:
                    e['selector']=selected;event['sampling']=draws;event['selector']=selected[:];event['selector_store_energy']=2 if initial else 0
                    records=[]
                    for index,value in zip(range(start,start+3),changes):
                        source=e['code'][index];unit=min(set(range(512))-occupied);occupied.add(unit)
                        entry=dict(unit=unit,value=value,index=index,tick=tick,source_unit=source[1],source_value=source[0],write_id=writes,mutated=value!=source[0])
                        certificates[writes]=(actor,clone(entry));writes+=1;mutations+=int(value!=source[0]);records.append(entry);e['nursery'].append(clone(entry))
                    e['energy']-=cost;heat+=cost;event['writes']=records;event['copy_energy']=cost
                else:event['outcome']='copy_refused'
            else:event['outcome']='copy_refused'
        if opcode==11 and len(e['nursery'])<len(e['code']):e['pc']=b%n
        if opcode==12:
            if len(e['nursery'])==len(e['code']) and e['energy']>=32 and 512-len(occupied)>=18 and len(org)<32:
                units=sorted(set(range(512))-occupied)[:18];occupied.update(units)
                assert all(certificates[w['write_id']]==(actor,w) for w in e['nursery'])
                child=body(next_id,actor,e['generation']+1,[[w['value'],w['unit']] for w in e['nursery']],units,e['pos'])
                event['birth']=dict(child=clone(child),write_ids=[w['write_id'] for w in e['nursery']],state_formation=[dict(unit=u,value=e['pos'] if i==14 else 0,energy=1) for i,u in enumerate(units)],release_energy=2,startup_energy=12)
                org[next_id]=child;next_id+=1;births+=1;desc_births+=int(e['generation']>0)
                e['energy']-=32;heat+=20;e['nursery']=[];e['selector']=None
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
    assert tick==512 or not org
    assert row['checkpoint']['tick']==min(64,tick)
    signature=[['ACT',ev['attempt']['position'],ev['attempt']['port']] if 'attempt' in ev else ['MOVE',ev['after']['pos']] for ev in events if ev['actor']==0 and ('attempt' in ev or (ev['decoded'][0]==13 and 'after' in ev))]
    offspring_errors=[]
    for ev in events:
        if 'birth' in ev:
            errors=sum(certificates[i][1]['mutated'] for i in ev['birth']['write_ids']);offspring_errors.append(errors)
            if mode=='single':assert errors==1
            if mode in ('faithful','copy_disabled'):assert errors==0
    feedback_readers={ev['actor'] for ev in events if ev['decoded'][0]==1}
    fresh=sum(bool(ev.get('attempt',{}).get('success')) and 16<=ev['attempt']['packet']<32 for ev in events if 'attempt' in ev)
    pre=sum(bool(e.get('attempt',{}).get('success')) for e in events if e['tick']<64)
    post=sum(bool(e.get('attempt',{}).get('success')) for e in events if e['tick']>=64)
    return dict(fresh_packets=fresh,offspring_errors=offspring_errors,feedback_reads=sum(ev['decoded'][0]==1 for ev in events),born_feedback_readers=sorted(feedback_readers-{0}),memory_writes=sum(ev['decoded'][0]==3 for ev in events),pre_food=pre,post_food=post,formation_cost=len(code)+18,founder_action_signature=signature,verified=True,seed=seed,route=row['route'],mode=mode,ticks=tick,births=births,descendant_births=desc_births,deaths=deaths,
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
