"""Chronological raw projection. Full independent VM audit is a caller precondition."""
from .digital_informative_exposure23_interpret import body,clone,h
from .digital_diagnosis59_origins import trace


def project(row):
    program=sum(row['genesis_program'],[]);assert len(program)==27
    initial=body(0,None,0,[[v,i] for i,v in enumerate(program)],list(range(27,43)),0)
    states={0:initial};births={0:clone(initial)};born={0:0};frames=[];views=[];changed=set();writes={};spent=set();edges=[]
    remaining=set(range(64));free=469;last=0;deaths={};selfwrites={0:[]}
    for event in row['final']['events']:
        t=event['tick'];i=event['actor'];assert type(t) is int and t==last+1 and type(i) is int and i in states
        last=t;s=states[i];assert event['before']==h(s)
        code=[c[0] for c in s['code']];op,a,b=event['decoded'];pc=s['pc'];assert event['decoded']==code[3*pc:3*pc+3]
        local=sorted(p for p in remaining if (0 if p<32 else 1+(p-32)//16)==s['pos'] and (not 16<=p<32 or t>=64))
        attempt=event.get('attempt');assert (attempt is not None)==(op==6 and bool(local))
        energy=s['energy']-1;loss=0
        if attempt is not None:
            assert attempt['packet']==local[0] and attempt['position']==s['pos']
            if attempt['success']:
                remaining.remove(attempt['packet']);loss=max(0,energy+20-64);energy+=20-loss
        frame=dict(tick=t,actor=i,opcode=op,position=s['pos'],energy_before=s['energy'],local_packets=local,
                   attempt=clone(attempt),birth_program_stable=i not in changed,cap_loss=loss)
        view=dict(tick=t,actor=i,decoded=event['decoded'][:],pc_before=pc)
        if op==6:view['packet_present']=attempt is not None
        if 'self_write' in event:
            w=event['self_write'];assert w['old']==code[w['index']]
            record=dict(tick=t,**clone(w),changed=w['old']!=w['value']);selfwrites[i].append(record)
            if record['changed']:changed.add(i)
            view['self_write']=clone(w)
        for w in event.get('writes',[]):
            wid=w['write_id'];assert type(wid) is int and wid not in writes and w['tick']==t
            assert [w['source_value'],w['source_unit']]==s['code'][w['index']] and w['value']==w['source_value'] and w['mutated'] is False
            writes[wid]=(i,clone(w));energy-=1;free-=1
        if 'writes' in event:view['writes']=clone(event['writes'])
        if 'birth' in event:
            birth=event['birth'];child=birth['child'];c=child['id'];ids=birth['write_ids']
            assert op==12 and c not in births and child['parent']==i and child['generation']==s['generation']+1
            assert child['energy']==birth['startup_energy']==12 and birth['release_energy']==2
            assert child['pos']==s['pos'] and child['pc']==child['feedback']==child['cue']==0
            assert child['registers']==[0,0] and child['memory']==[0]*8 and child['inbox'] is None and child['nursery']==[]
            assert len(ids)==len(set(ids))==len(child['code'])==27 and not spent.intersection(ids)
            assert len(birth['state_formation'])==len(child['state_units'])==16
            for index,(wid,cell) in enumerate(zip(ids,child['code'])):
                owner,w=writes[wid];assert owner==i and w['tick']<t and w['index']==index and [w['value'],w['unit']]==cell
            spent.update(ids);states[c]=clone(child);births[c]=clone(child);born[c]=t;selfwrites[c]=[]
            edges.append(dict(tick=t,parent=i,child=c,write_ids=ids[:],equal_parent_birth=program_of(child)==program_of(births[i]),
                              equal_parent_division=program_of(child)==code,birth_position=child['pos'],startup_energy=12,
                              parent_energy_before=s['energy'],parent_energy_after=energy-30,birth_body_hash=h(child)))
            energy-=30;free-=16;view['birth']=c
        if 'message' in event:
            msg=event['message'];assert states[msg['recipient']]['inbox'] is None
            states[msg['recipient']]['inbox']=msg['value'];view['message']=msg['recipient']
        if 'transfer' in event:states[event['transfer']]['energy']+=1;energy-=1
        if op==17:energy=0
        frame['energy_after']=energy;frames.append(frame)
        if 'death' in event:
            assert energy==0 and 'after' not in event;deaths[i]=t;free+=len(event['death']);del states[i];view['death']=True
        else:assert event['after']['energy']==energy;states[i]=clone(event['after'])
        views.append(view)
    assert free==len(row['final']['free']) and remaining==set(map(int,row['final']['food']))
    actors={}
    for i,start in births.items():
        own=[f for f in frames if f['actor']==i];acquired=[[f['tick'] for f in own if f['attempt'] and f['attempt']['success'] and f['position']==site] for site in range(4)]
        actors[str(i)]=dict(parent=start['parent'],generation=start['generation'],birth_tick=born[i],birth_position=start['pos'],
          birth_program=program_of(start),birth_program_hash=h(program_of(start)),birth_body_hash=h(start),instructions=len(own),
          actions=sum(f['opcode']==6 for f in own),moves=sum(f['opcode']==13 for f in own),food_ticks_by_site=acquired,
          opportunities_by_site=[sum(f['position']==site and bool(f['local_packets']) for f in own) for site in range(4)],
          personal_trial_ticks=[f['tick'] for f in own if f['attempt'] is not None],empty_action_ticks=[f['tick'] for f in own if f['opcode']==6 and f['attempt'] is None],
          stable_food_ticks=[f['tick'] for f in own if f['attempt'] and f['attempt']['success'] and f['birth_program_stable']],
          self_writes=selfwrites[i],paid_copy_words=sum(owner==i for owner,w in writes.values()),
          births=[e['tick'] for e in edges if e['parent']==i],death_tick=deaths.get(i),alive=i in states,
          endpoint_energy=states[i]['energy'] if i in states else 0,unfinished_copy_words=len(states[i]['nursery']) if i in states else 0,
          endpoint_body_hash=h(states[i]) if i in states else None,cap_loss=sum(f['cap_loss'] for f in own))
    for edge in edges:
        parent=actors[str(edge['parent'])];child=actors[str(edge['child'])];t=edge['tick']
        edge['parent_prior_food']=[[v for v in vs if v<t] for vs in parent['food_ticks_by_site']]
        edge['child_later_food']=[[v for v in vs if v>t] for vs in child['food_ticks_by_site']]
        edge['same_site_continuation']=[site for site in range(1,3) if edge['parent_prior_food'][site] and edge['child_later_food'][site]]
        edge['child_resource_before_own_birth']=any(v<b for vs in child['food_ticks_by_site'] for v in vs for b in child['births'])
    return dict(frames=frames,actors=actors,edges=edges,origins=trace(views,27),
                summary=dict(ticks=len(frames),actors=len(actors),births=len(edges),deaths=len(deaths),food=64-len(remaining),copy_words=len(writes),free_material=free,live_energy=sum(s['energy'] for s in states.values())),
                causal_inheritance=False,learning=False,stage_credit=False)


def program_of(state):return [c[0] for c in state['code']]
