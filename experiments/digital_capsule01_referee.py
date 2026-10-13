"""Independent finite persistence01 history referee, adapted from literal68.

Only software seed1/faithful/parent_copy, complete natural prefixes <=512.
NO producer, data-boundary, loader or shared transition helper import.
All ordinary accounting/scheduler/COPY/expiry semantics remain literal68.
Prefix replay is explicit audit work; it is never part of efficient hydration.
No execution qualification is conveyed by this source alone.
"""
import hashlib,json

CAPSULE_VERSION='DIGITAL-EXACT-PERSISTENCE-QUALIFICATION-01-data-v1'

def _pairs(items):
    result={}
    for key,value in items:
        assert key not in result
        result[key]=value
    return result

def verify_capsule(raw,expected_identity,expected_sha256,extent):
    """Independent custody/schema/full literal history audit. No loader import."""
    assert type(raw) is bytes and type(extent) is int and 0<extent<=32*1024**2
    assert len(raw)==extent and hashlib.sha256(raw).hexdigest()==expected_sha256
    assert type(expected_identity) is dict and set(expected_identity)=={'revision','source_sha256','config_sha256','law'}
    for field,length in [('revision',40),('source_sha256',64),('config_sha256',64)]:
        value=expected_identity[field]
        assert type(value) is str and len(value)==length and all(c in '0123456789abcdef' for c in value)
    assert expected_identity['law']=='DIGITAL-SHARED-LINEAGE-68-v1'
    capsule=json.loads(raw.decode('ascii'),object_pairs_hook=_pairs,parse_constant=lambda value: (_ for _ in ()).throw(ValueError(value)))
    assert type(capsule) is dict and set(capsule)=={'version','identity','state','state_sha256'}
    assert capsule['version']==CAPSULE_VERSION and capsule['identity']==expected_identity
    assert json.dumps(capsule,sort_keys=True,separators=(',',':'),ensure_ascii=True).encode('ascii')==raw
    state=capsule['state'];assert capsule['state_sha256']==h(state)
    summary=audit_state(state)
    return dict(version='DIGITAL-CAPSULE01-AUDIT-v1',verified=True,identity=expected_identity,
                capsule_sha256=expected_sha256,extent=extent,state_sha256=h(state),tick=state['tick'],
                audit_prefix_instructions=summary['ticks'],summary=summary,
                engineering_only=True,stage_credit=False)

ANCESTOR_WORDS=[4,1,1,6,0,0,5,0,1,6,0,0,10,0,0,12,0,0,13,1,0,13,1,0,7,0,1]

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

def audit_state(state):
    types(state)
    assert type(state) is dict and type(state['tick']) is int and 0 <= state['tick'] <= 512
    seed=state['seed'];mode=state['mode'];fuel_mode=state['fuel_mode'];inheritance_mode=state['inheritance_mode']
    assert type(seed) is int and seed == 1 and mode == 'faithful'
    assert fuel_mode == 'renewed' and inheritance_mode == 'parent_copy'
    row=dict(seed=seed,mode=mode,fuel_mode=fuel_mode,inheritance_mode=inheritance_mode,
             genesis_program=[ANCESTOR_WORDS[i:i+3] for i in range(0,27,3)],route='ancestor',
             final=state,hash=h(state))
    code=sum(row['genesis_program'],[]);bill=len(code)+16
    org={0:body(0,None,0,[[v,i] for i,v in enumerate(code)],list(range(len(code),bill)),0)}
    occupied=set(range(bill));food={i:[0 if i<32 else 1+(i-32)//16,int(h([seed,'food',i])[:8],16)%2] for i in range(64)}
    formation=[dict(unit=i,value=v,energy=1,assistance='supplied ancestor assembly') for i,v in enumerate(code+[0]*16)]
    heat=bill;constructor=128-bill;writes=0;last=-1;next_id=1;births=deaths=0;maximum=1;events=[];tick=0
    offered=admitted=rejected=0;next_packet=64;turns={0:0}
    certificates={};successful_food=failed_food=mutations=desc_births=messages=0
    personal_food={0:0};birth_edges=[];expiry_records=[];renewed_food=0
    def snapshot(include_events=True):
        state=dict(inheritance_mode=inheritance_mode,fuel_mode=fuel_mode,turns=turns,offered=offered,admitted=admitted,rejected=rejected,next_packet=next_packet,seed=seed,mode=mode,tick=tick,last=last,next_id=next_id,writes=writes,
                   constructor_remaining=constructor,heat=heat,formation=formation,food=food,
                   free=sorted(set(range(512))-occupied),entities=org,births=births,deaths=deaths,maximum=maximum)
        if include_events:state['events']=events
        return clone(state)
    assert len(row['final']['events']) == state['tick'] <= 512
    for observed in row['final']['events']:
        tick+=1;ids=sorted(org);actor=next((i for i in ids if i>last),ids[0]);last=actor
        offers=None
        if fuel_mode=='renewed' and tick%64==0:
            offers=[]
            for site in range(4):
                for _ in range(4):
                    packet=next_packet;next_packet+=1;offered+=1
                    kind=int(h([seed,'renew-food',packet])[:8],16)%2
                    accepted=sum(v[0]==site for v in food.values())<32
                    if accepted:food[packet]=[site,kind];admitted+=1
                    else:rejected+=1
                    offers.append(dict(packet=packet,site=site,kind=kind,energy=20,outcome='admitted' if accepted else 'rejected'))
        release=None
        if tick==64:
            assert constructor>=16
            constructor-=16;heat+=16
            release=dict(packets=list(range(16,32)),energy=16,assistance='supplied exogenous stock boundary')
        e=org[actor];n=len(e['code'])//3;opcode,a,b=[word[0] for word in e['code'][3*e['pc']:3*e['pc']+3]]
        event=dict(tick=tick,actor=actor,decoded=[opcode,a,b],before=h(e),outcome='executed')
        if offers is not None:event['input']=offers
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
                packet=local[0];position,kind=food[packet];target=(seed%2 ^ int(h([seed//2,'latent15'])[:8],16)%2 ^ int(int(h([seed//2,'noise15',packet])[:8],16)%16==0)) if position==0 and packet in range(16,32) else (seed%2 if position==0 else int(h([seed,'site-port',position])[:8],16)%2)^int(tick>=64)
                if packet>=64:target=seed%2 ^ (int(h([seed//2,'renew-port',position])[:8],16)%2) ^ int(tick>=2048)
                e['feedback']=int(r[a%2]%2==target)
                event['attempt']=dict(packet=packet,position=position,cue=kind,port=r[a%2]%2,target=target,success=e['feedback'])
                if e['feedback']:
                    del food[packet]
                    overflow=max(0,e['energy']+20-64);e['energy']+=20-overflow;heat+=overflow;successful_food+=1
                    personal_food[actor]+=1;renewed_food+=int(packet>=64)
                else:failed_food+=1
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
                    source=e['code'][index]
                    effective=source[0] if inheritance_mode=='parent_copy' else ANCESTOR_WORDS[index]
                    draw=int(h([seed,'mutation',writes])[:16],16);value=effective
                    if mode=='mutating' and draw%100<8:value=(value+1+(draw//100)%31)%32
                    unit=min(set(range(512))-occupied);occupied.add(unit)
                    entry=dict(unit=unit,value=value,index=index,tick=tick,source_unit=source[1],source_value=source[0],effective_source=inheritance_mode,effective_source_value=effective,mutation_draw=draw,write_id=writes,mutated=value!=effective)
                    certificates[writes]=(actor,clone(entry));writes+=1;mutations+=int(value!=effective);records.append(entry);e['nursery'].append(clone(entry))
                e['energy']-=3;heat+=3;event['writes']=records
            else:event['outcome']='copy_refused'
        if opcode==11 and len(e['nursery'])<len(e['code']):e['pc']=b%n
        if opcode==12:
            if len(e['nursery'])==len(e['code']) and e['energy']>=30 and 512-len(occupied)>=16 and len(org)<32:
                units=sorted(set(range(512))-occupied)[:16];occupied.update(units)
                assert all(certificates[w['write_id']]==(actor,w) for w in e['nursery'])
                child=body(next_id,actor,e['generation']+1,[[w['value'],w['unit']] for w in e['nursery']],units,e['pos'])
                event['birth']=dict(child=clone(child),write_ids=[w['write_id'] for w in e['nursery']],state_formation=[dict(unit=u,value=e['pos'] if i==14 else 0,energy=1) for i,u in enumerate(units)],release_energy=2,startup_energy=12)
                birth_edges.append(dict(parent=actor,child=next_id,generation=child['generation'],tick=tick,parent_personal_food=personal_food[actor],write_ids=event['birth']['write_ids']))
                turns[next_id]=0;personal_food[next_id]=0
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
        assert sum(o['energy'] for o in org.values())+constructor+heat+20*len(food)==1420+20*admitted
        owned=[v[1] for o in org.values() for v in o['code']]+[u for o in org.values() for u in o['state_units']]+[w['unit'] for o in org.values() for w in o['nursery']]
        assert len(owned)==len(set(owned)) and set(owned)==occupied and occupied<=set(range(512)) and len(org)<=32
        event['vm_state_hash']=h(snapshot(False))
        turns[actor]+=1
        if actor in org and turns[actor]==256:
            released=[g[1] for g in e['code']]+e['state_units']+[w['unit'] for w in e['nursery']]
            expiry=dict(actor=actor,turns=256,energy=e['energy'],units=released,body_before=h(e),reason='execution_budget')
            event['expiry']=expiry;expiry_records.append(dict(expiry,tick=tick))
            heat+=e['energy'];occupied.difference_update(released);del org[actor];deaths+=1
        assert offered==admitted+rejected and next_packet==64+offered
        assert all(sum(v[0]==site for v in food.values())<=32 for site in range(4))
        assert all(0<=v<=256 for v in turns.values()) and all(turns[i]<256 for i in org)
        assert sum(o['energy'] for o in org.values())+constructor+heat+20*len(food)==1420+20*admitted
        owned=[v[1] for o in org.values() for v in o['code']]+[u for o in org.values() for u in o['state_units']]+[w['unit'] for o in org.values() for w in o['nursery']]
        assert len(owned)==len(set(owned)) and set(owned)==occupied
        event['state_hash']=h(snapshot(False));assert observed==event;events.append(clone(event))
    final=snapshot();assert row['final']==final and row['hash']==h(final)
    assert tick == state['tick']
    founder_expiry=next((e['tick'] for e in expiry_records if e['actor']==0),None)
    after_founder=[] if founder_expiry is None else [ev for ev in events if ev['tick']>founder_expiry]
    edges={edge['child']:edge for edge in birth_edges}
    chains=[]
    for end in birth_edges:
        if end['generation']!=3:continue
        middle=edges.get(end['parent']);first=edges.get(middle['parent']) if middle else None
        if middle and first and (first['generation'],middle['generation'])==(1,2) and middle['parent_personal_food']>0 and end['parent_personal_food']>0:
            chains.append([first['child'],middle['child'],end['child']])
    turnover=dict(founder_expiry_tick=founder_expiry,post_founder_instructions=len(after_founder),
                  post_founder_paid_personal_births=sum(edge['parent']!=0 and edge['parent_personal_food']>0 and founder_expiry is not None and edge['tick']>founder_expiry for edge in birth_edges),
                  post_founder_renewed_food=sum(ev.get('attempt',{}).get('success',0) and ev['attempt']['packet']>=64 for ev in after_founder),
                  living_descendants=sum(i!=0 for i in org),maximum_generation=max([0]+[e['generation'] for e in birth_edges]),paid_personal_chains=chains)
    signature=[['ACT',ev['attempt']['position'],ev['attempt']['port']] if 'attempt' in ev else ['MOVE',ev['after']['pos']] for ev in events if ev['actor']==0 and ('attempt' in ev or (ev['decoded'][0]==13 and 'after' in ev))]
    pre=sum(bool(e.get('attempt',{}).get('success')) for e in events if e['tick']<64)
    post=sum(bool(e.get('attempt',{}).get('success')) for e in events if e['tick']>=64)
    return dict(inheritance_mode=inheritance_mode,genesis_program_hash=h(code),fuel_mode=fuel_mode,offered_tokens=offered,admitted_tokens=admitted,rejected_tokens=rejected,renewed_food=renewed_food,turns=clone(turns),expiry_records=expiry_records,birth_edges=birth_edges,turnover=turnover,selection=False,stage_credit=False,pre_food=pre,post_food=post,formation_cost=len(code)+16,founder_action_signature=signature,verified=True,seed=seed,route=row['route'],mode=mode,ticks=tick,births=births,descendant_births=desc_births,deaths=deaths,
                successful_food=successful_food,failed_food=failed_food,unused_food=len(food),paid_copy_words=writes,
                mutations=mutations,maximum_population=maximum,heat=heat,live_energy=sum(e['energy'] for e in org.values()),
                free_material=512-len(occupied),messages=messages,change_exposed=sum('attempt' in ev and ev['attempt']['position']!=0 and ev['attempt']['target']==1 for ev in events),
                remote_food=sum(bool(ev.get('attempt',{}).get('success')) and ev['attempt']['position']!=0 for ev in events),
                descendant_remote_food=sum(bool(ev.get('attempt',{}).get('success')) and ev['attempt']['position']!=0 and ev['actor']!=0 for ev in events),
                repeated_hidden_port_actors=len({ev['actor'] for ev in events if 'attempt' in ev and ev['attempt']['position']!=0 and ev['attempt']['target']==1 and sum('attempt' in prior and prior['actor']==ev['actor'] and prior['attempt']['position']==ev['attempt']['position'] for prior in events[:ev['tick']-1])>=1}),
                learning=False,evolution=False,repair=False)
