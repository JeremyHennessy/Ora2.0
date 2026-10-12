"""Per-actor predecessor/event joins; no producer or other projection import."""
import hashlib,json
from .digital_diagnosis59_origins_independent import trace


def digest(value):return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':')).encode()).hexdigest()
def copy(value):return json.loads(json.dumps(value))


def project(row):
    code=sum(row['genesis_program'],[]);assert len(code)==27
    founder=dict(id=0,parent=None,generation=0,code=[[v,i] for i,v in enumerate(code)],state_units=list(range(27,43)),memory=[0]*8,registers=[0,0],pc=0,cue=0,feedback=0,inbox=None,pos=0,energy=12,nursery=[])
    events=row['final']['events'];assert [e['tick'] for e in events]==list(range(1,len(events)+1))
    starts={0:(0,founder)};certificates={};birth_events=[];used=set()
    for e in events:
        for w in e.get('writes',[]):
            assert type(w['write_id']) is int and w['write_id'] not in certificates
            certificates[w['write_id']]=(e['actor'],w)
        if 'birth' in e:
            c=e['birth']['child'];assert c['id'] not in starts
            starts[c['id']]=(e['tick'],copy(c));birth_events.append(e)
    frames={};views={};actors={};before_states={};endings={};changes={}
    for identity,(born,start) in starts.items():
        mine=[e for e in events if e['actor']==identity];state=copy(start);previous=born;dead=None;ever_changed=False;sw=[];own=[]
        for e in mine:
            t=e['tick'];assert type(identity) is int and dead is None and t>previous
            # Other actors may change the inbox or transfer energy between this actor's steps.
            for intervening in events:
                if not previous<intervening['tick']<t:continue
                if intervening.get('message',{}).get('recipient')==identity:
                    assert state['inbox'] is None;state['inbox']=intervening['message']['value']
                if intervening.get('transfer')==identity:state['energy']+=1
            assert digest(state)==e['before'];before_states[t]=copy(state)
            op,x,y=e['decoded'];values=[c[0] for c in state['code']]
            assert values[state['pc']*3:state['pc']*3+3]==e['decoded']
            consumed={old['attempt']['packet'] for old in events if old['tick']<t and old.get('attempt',{}).get('success')}
            available=[p for p in range(64) if p not in consumed and (0 if p<32 else (p-32)//16+1)==state['pos'] and (p<16 or p>=32 or t>=64)]
            attempt=e.get('attempt');assert (attempt is not None)==(op==6 and bool(available))
            if attempt is not None:assert attempt['packet']==available[0] and attempt['position']==state['pos']
            overflow=max(0,state['energy']-1+20-64) if attempt and attempt['success'] else 0
            after_energy=state['energy']-1+(20-overflow if attempt and attempt['success'] else 0)-len(e.get('writes',[]))-30*int('birth' in e)-int('transfer' in e)
            if op==17:after_energy=0
            f=dict(tick=t,actor=identity,opcode=op,position=state['pos'],energy_before=state['energy'],local_packets=available,
                   attempt=copy(attempt),birth_program_stable=not ever_changed,cap_loss=overflow,energy_after=after_energy)
            own.append(f);frames[t]=f
            v=dict(tick=t,actor=identity,decoded=e['decoded'][:],pc_before=state['pc'])
            if op==6:v['packet_present']=attempt is not None
            if 'self_write' in e:
                w=e['self_write'];assert w['old']==values[w['index']]
                record=dict(tick=t,**copy(w),changed=w['value']!=w['old']);sw.append(record);ever_changed=ever_changed or record['changed'];v['self_write']=copy(w)
            for w in e.get('writes',[]):
                assert w['tick']==t and state['code'][w['index']]==[w['source_value'],w['source_unit']]
                assert w['value']==w['source_value'] and w['mutated'] is False
            if 'writes' in e:v['writes']=copy(e['writes'])
            if 'birth' in e:v['birth']=e['birth']['child']['id']
            if 'message' in e:v['message']=e['message']['recipient']
            if 'death' in e:assert after_energy==0 and 'after' not in e;dead=t;v['death']=True
            else:assert e['after']['energy']==after_energy;state=copy(e['after'])
            previous=t;views[t]=v
        # Apply transfers/messages after the final own step, including zero-action newborns.
        if dead is None:
            for e in events:
                if e['tick']<=previous:continue
                if e.get('message',{}).get('recipient')==identity:assert state['inbox'] is None;state['inbox']=e['message']['value']
                if e.get('transfer')==identity:state['energy']+=1
            endings[identity]=state
        acquired=[]
        for site in range(4):acquired.append([f['tick'] for f in own if f['position']==site and f['attempt'] and f['attempt']['success']])
        birth_words=[c[0] for c in start['code']]
        actors[str(identity)]=dict(parent=start['parent'],generation=start['generation'],birth_tick=born,birth_position=start['pos'],birth_program=birth_words,
          birth_program_hash=digest(birth_words),birth_body_hash=digest(start),instructions=len(mine),actions=sum(e['decoded'][0]==6 for e in mine),moves=sum(e['decoded'][0]==13 for e in mine),
          food_ticks_by_site=acquired,opportunities_by_site=[len([f for f in own if f['position']==site and f['local_packets']]) for site in range(4)],
          personal_trial_ticks=[f['tick'] for f in own if f['attempt'] is not None],empty_action_ticks=[f['tick'] for f in own if f['opcode']==6 and f['attempt'] is None],
          stable_food_ticks=[f['tick'] for f in own if f['attempt'] and f['attempt']['success'] and f['birth_program_stable']],self_writes=sw,
          paid_copy_words=sum(len(e.get('writes',[])) for e in mine),births=[e['tick'] for e in mine if 'birth' in e],death_tick=dead,alive=dead is None,
          endpoint_energy=state['energy'] if dead is None else 0,unfinished_copy_words=len(state['nursery']) if dead is None else 0,
          endpoint_body_hash=digest(state) if dead is None else None,cap_loss=sum(f['cap_loss'] for f in own))
    assert set(frames)==set(range(1,len(events)+1))
    edges=[]
    for e in birth_events:
        t=e['tick'];parent=e['actor'];birth=e['birth'];child=birth['child'];identity=child['id'];s=before_states[t];ids=birth['write_ids']
        assert child['parent']==parent and child['generation']==s['generation']+1 and e['decoded'][0]==12
        assert len(ids)==len(set(ids))==len(child['code'])==27 and not used.intersection(ids);used.update(ids)
        for index,wid in enumerate(ids):
            owner,w=certificates[wid];assert owner==parent and w['tick']<t and w['index']==index and [w['value'],w['unit']]==child['code'][index]
        assert child['pos']==s['pos'] and child['energy']==birth['startup_energy']==12 and birth['release_energy']==2
        assert child['registers']==[0,0] and child['memory']==[0]*8 and child['pc']==child['cue']==child['feedback']==0 and child['inbox'] is None and child['nursery']==[]
        assert len(birth['state_formation'])==len(child['state_units'])==16
        p=actors[str(parent)];c=actors[str(identity)]
        prior=[[v for v in vs if v<t] for vs in p['food_ticks_by_site']];later=[[v for v in vs if v>t] for vs in c['food_ticks_by_site']]
        edges.append(dict(tick=t,parent=parent,child=identity,write_ids=ids[:],equal_parent_birth=c['birth_program']==p['birth_program'],
                          equal_parent_division=c['birth_program']==[word[0] for word in s['code']],birth_position=child['pos'],startup_energy=12,
                          parent_energy_before=s['energy'],parent_energy_after=frames[t]['energy_after'],birth_body_hash=digest(child),
                          parent_prior_food=prior,child_later_food=later,same_site_continuation=[site for site in (1,2) if prior[site] and later[site]],
                          child_resource_before_own_birth=any(v<b for vs in c['food_ticks_by_site'] for v in vs for b in c['births'])))
    owned=[word[1] for s in endings.values() for word in s['code']]+[unit for s in endings.values() for unit in s['state_units']]+[w['unit'] for s in endings.values() for w in s['nursery']]
    assert len(set(owned))==len(owned) and sorted(set(range(512))-set(owned))==row['final']['free']
    consumed={e['attempt']['packet'] for e in events if e.get('attempt',{}).get('success')};assert set(range(64))-consumed==set(map(int,row['final']['food']))
    return dict(frames=[frames[t] for t in sorted(frames)],actors=actors,edges=edges,origins=trace([views[t] for t in sorted(views)],27),
                summary=dict(ticks=len(events),actors=len(actors),births=len(edges),deaths=sum(not a['alive'] for a in actors.values()),food=len(consumed),copy_words=len(certificates),free_material=512-len(owned),live_energy=sum(s['energy'] for s in endings.values())),
                causal_inheritance=False,learning=False,stage_credit=False)
