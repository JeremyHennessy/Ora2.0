"""Unqualified independent SharedLineage68 single-transition continuation replay.
Literal68 population operations plus one declared newborn code-value intervention.
No producer import. Partial fixture checks do not qualify a full continuation.
"""
import hashlib,json
from experiments import digital_sharedlineage68_interpret as natural_full
from experiments.digital_sharedlineage68_transition import (VERSION,ROLES,GENERATIONS,actor_record,slots_from_audited,validate_provenance)

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

def transition(state,slot,natural_hash,role,provenance):
    """Literal referee boundary, independently derived from the frozen law.

    No producer transition/validation helper is called. Full prefix replay must
    precede this check; partial prepared states remain software witnesses only.
    """
    types(state);types(slot)
    assert type(provenance) is dict and set(provenance)=={'source_sha256','configuration_sha256'}
    for digest in [natural_hash,*provenance.values()]:
        assert type(digest) is str and len(digest)==64 and set(digest)<=set('0123456789abcdef')
    assert role in ('sham','ancestor_value_control')
    for key,minimum in [('target',1),('parent',0),('generation',1),('tick',1)]:
        assert type(slot[key]) is int and slot[key]>=minimum
    assert slot['generation'] in (1,2) and slot['tick']<=4096
    assert type(state['tick']) is int and state['tick']==slot['tick']
    assert (state['mode'],state['fuel_mode'],state['inheritance_mode'])==('mutating','renewed','parent_copy')
    # Canonical identities are derived here rather than trusting the shared accessor.
    def lookup(mapping,identity):
        assert type(mapping) is dict
        normalized={}
        for key,value in mapping.items():
            assert type(key) in (int,str)
            if type(key) is str:
                assert key.isascii() and key.isdecimal() and str(int(key))==key
            number=int(key);assert number>=0 and number not in normalized
            normalized[number]=value
        assert identity in normalized
        return normalized[identity]
    daughter=lookup(state['entities'],slot['target'])
    own_turns=lookup(state['turns'],slot['target']);assert type(own_turns) is int and own_turns==0
    assert h({k:v for k,v in state.items() if k!='events'})==slot['post_step_hash']
    assert daughter['code']==slot['born_code'] and len(daughter['code'])==27 and len(daughter['state_units'])==16
    assert daughter==body(slot['target'],slot['parent'],slot['generation'],daughter['code'],daughter['state_units'],daughter['pos'])
    words=slot['certificates'];assert type(words) is list and len(words)==27
    write_ids=set()
    for index,word in enumerate(words):
        for key in ('write_id','index','actor','tick','source_unit','unit','source_value','effective_source_value','value','mutation_draw'):
            assert type(word[key]) is int and word[key]>=0
        assert word['write_id'] not in write_ids;write_ids.add(word['write_id'])
        assert word['index']==index and word['actor']==slot['parent'] and 0<word['tick']<slot['tick']
        assert word['effective_source']=='parent_copy' and word['effective_source_value']==word['source_value']
        assert word['source_value']<32 and word['value']<32
        draw=int(h([state['seed'],'mutation',word['write_id']])[:16],16)
        expected=word['source_value']
        if draw%100<8:expected=(expected+1+(draw//100)%31)%32
        assert word['mutation_draw']==draw and word['value']==expected
        assert type(word['mutated']) is bool and word['mutated']==(expected!=word['source_value'])
        assert daughter['code'][index]==[expected,word['unit']]
    # A deep copy plus explicit value writes preserves every other world field.
    after=clone(state);edited=lookup(after['entities'],slot['target'])
    mask=[i for i,cell in enumerate(daughter['code']) if cell[0]!=ANCESTOR_WORDS[i]]
    if role=='ancestor_value_control':
        for i in range(27):edited['code'][i][0]=ANCESTOR_WORDS[i]
    record=dict(version='DIGITAL-SHARED-LINEAGE-68-NEWBORN-v1',role=role,
        provenance=clone(provenance),natural_history_hash=natural_hash,target=slot['target'],
        parent=slot['parent'],generation=slot['generation'],tick=slot['tick'],before_hash=h(state),
        after_hash=h(after),code_value_mask=mask,before_code=clone(daughter['code']),
        after_code=clone(edited['code']),certificates=clone(words),
        assistance='DECLARED_COUNTERFACTUAL_NOT_NATURAL_REPAIR')
    return after,record

def audit_history(row,binding=None,natural_hash=None,observations=None):
    types(row)
    assert set(row)=={'version','seed','mode','fuel_mode','route','genesis_program','inheritance_mode','checkpoint','final','hash','ancestor_supplied','checkpoint_replay','learning_demonstrated'}
    assert row['version']=='DIGITAL-SHARED-LINEAGE-68-v1'
    inheritance_mode=row['inheritance_mode'];assert inheritance_mode in ('parent_copy','ancestor_copy')
    assert inheritance_mode=='parent_copy' or row['mode']=='mutating'
    assert row['route']=='ancestor'
    fuel_mode=row['fuel_mode'];assert fuel_mode=='renewed'
    program=row['genesis_program']
    assert 1<=len(program)<=32 and all(type(x) is list and len(x)==3 and all(type(v) is int and 0<=v<32 for v in x) for x in program)
    assert sum(program,[])==ANCESTOR_WORDS
    assert row['ancestor_supplied'] and row['checkpoint_replay'] and not row['learning_demonstrated']
    seed=row['seed'];mode=row['mode'];assert type(seed) is int and seed>=0 and mode in ('mutating','faithful')
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
    assert len(row['final']['events'])<=4096
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
        if observations is not None:observations.before(snapshot(False),event['decoded'])
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
        if observations is not None:observations.after(snapshot(False),event,clone(e))
        if binding is not None and tick==binding['slot']['tick']:
            slot=binding['slot']
            assert 'birth' in event and event['birth']['child']['id']==slot['target']
            assert slot['certificates']==[dict(certificates[i][1],actor=certificates[i][0]) for i in event['birth']['write_ids']]
            after,record=transition(snapshot(),slot,natural_hash,binding['role'],binding['provenance'])
            assert binding['record']==record
            org[slot['target']]['code']=actor_record(after['entities'],slot['target'])['code']
            if observations is not None:observations.intervention(after,slot['target'])
        if tick==min(64,row['final']['tick']):assert row['checkpoint']==snapshot()
    final=snapshot();assert row['final']==final and row['hash']==h(final)
    assert tick==4096 or not org
    assert row['checkpoint']['tick']==min(64,tick)
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

def audit(row,expected_provenance):
    """Full natural audit before neutral selection or edited continuation replay."""
    assert type(row) is dict and set(row) == {
        'version', 'natural', 'branch', 'generation', 'role', 'transition','provenance'}
    validate_provenance(expected_provenance);assert row['provenance']==expected_provenance
    assert row['version'] == VERSION and row['role'] in ROLES
    assert type(row['generation']) is int and row['generation'] in GENERATIONS
    natural = row['natural']; branch = row['branch']
    assert natural['inheritance_mode']=='parent_copy'
    assert natural['mode'] == 'mutating' and natural['fuel_mode'] == 'renewed'
    assert natural['route'] == 'ancestor' and sum(natural['genesis_program'], []) == ANCESTOR_WORDS
    summary = natural_full.audit(natural)
    slot = slots_from_audited(natural, summary)[row['generation']]
    if slot is None:
        assert branch is None and row['transition'] is None
        return dict(verified=True, seed=natural['seed'],generation=row['generation'],role=row['role'],
                    provenance=clone(expected_provenance),natural_history_hash=natural['hash'],branch_hash=None,slot=None, target=None, null=True,
                    selection=False, learning=False, stage_credit=False)
    assert type(branch) is dict
    for key in ('version', 'seed', 'mode','inheritance_mode', 'fuel_mode', 'route', 'genesis_program',
                'ancestor_supplied', 'checkpoint_replay', 'learning_demonstrated'):
        assert branch[key] == natural[key]
    assert branch['final']['events'][:slot['tick']] == natural['final']['events'][:slot['tick']]
    binding = dict(slot=slot, role=row['role'], record=row['transition'],provenance=expected_provenance)
    from experiments.digital_sharedlineage68_observe import Observation
    observation=Observation()
    measured = audit_history(branch, binding, natural['hash'],observation)
    projected=observation.finish(branch['final'],measured)
    if row['role'] == 'sham' or not row['transition']['code_value_mask']:
        assert branch == natural
    target = target_endpoint(branch['final'], slot)
    return dict(verified=True, seed=natural['seed'],generation=row['generation'],role=row['role'],
        provenance=clone(expected_provenance),natural_history_hash=natural['hash'],branch_hash=branch['hash'],slot=slot, null=False, summary=measured,
        target=target, projection=projected, selection=False, learning=False, stage_credit=False)


def target_endpoint(final, slot):
    """Observation after full replay, not a stand-alone ancestry certificate."""
    target = slot['target']; turns = births = food = 0; death_tick = cause = None
    for event in final['events'][slot['tick']:]:
        if event['actor'] != target:
            continue
        turns += 1; births += int('birth' in event)
        food += int(bool(event.get('attempt', {}).get('success')))
        if 'expiry' in event or 'death' in event:
            assert death_tick is None
            death_tick = event['tick']
            cause = ('execution_budget' if 'expiry' in event else
                     'halt' if event['outcome'] == 'halt' else 'zero_energy')
    assert turns == actor_record(final['turns'], target)
    return dict(turns=turns, births=births, food=food, death_tick=death_tick,
                death_cause=cause, censored=death_tick is None)
