"""Independent literal single-entity VM/resource/control proof; no producer imports."""
import hashlib,json
OPS=(0,1,2,3,4,5,6,7,8,18,19,20)
def enc(v):return json.dumps(v,sort_keys=True,separators=(',',':')).encode()
def h(v):return hashlib.sha256(enc(v)).hexdigest()
def clone(v):return json.loads(json.dumps(v))
def move(program,s,feedback,zero,cue):
    n=clone(s);op,a,b=program[s['pc']];n['pc']=(s['pc']+1)%len(program)
    if op==0:n['r'][a%2]=cue
    if op==1:n['r'][a%2]=0 if zero else s['feedback']
    if op==2:n['r'][a%2]=s['m'][b%8]
    if op==3:n['m'][a%8]=s['r'][b%2]
    if op==4:n['r'][a%2]=b%16
    if op==5:n['r'][a%2]=s['r'][a%2]^s['r'][b%2]
    if op==6:n['feedback']=feedback
    if op==7 or op==8 and s['r'][a%2]==0:n['pc']=b%len(program)
    if op==19:n['r'][a%2]=s['m'][s['r'][b%2]%8]
    if op==20:n['m'][s['r'][a%2]%8]=s['r'][b%2]
    return n
def typed(v,key=None):
    if key in ('ancestor_supplied','checkpoint_replay','learning_demonstrated'):assert type(v) is bool
    elif type(v) is dict:
        for k,x in v.items():typed(x,k)
    elif type(v) is list:
        for x in v:typed(x)
    else:assert v is None or type(v) in (str,int)
def local(e):return dict(r=e['registers'][:],m=e['memory'][:],pc=e['pc'],feedback=e['feedback'])
def audit(row,expected_program,software=False):
    typed(row)
    assert set(row)=={'version','seed','mode','route','control_mode','genesis_program','checkpoint','final','hash','ancestor_supplied','checkpoint_replay','learning_demonstrated'}
    assert row['version']=='DIGITAL-EXPERIENCE75-WORLD-v1' and row['mode']=='faithful'
    assert type(software) is bool
    seed=row['seed'];assert type(seed) is int and seed in ((95074,95075) if software else tuple(range(75000,75008))+tuple(range(75200,75208)))
    control=row['control_mode'];assert control in ('intact','retained_disabled','own_disrupted')
    program=row['genesis_program'];assert program==expected_program and len(program)==14
    assert all(type(t) is list and len(t)==3 and t[0] in OPS and all(type(x) is int and 0<=x<32 for x in t) for t in program)
    assert row['ancestor_supplied'] is True and row['checkpoint_replay'] is False and row['learning_demonstrated'] is False
    values=sum(program,[]);bill=len(values)+16;assert bill==58
    e=dict(id=0,parent=None,generation=0,code=[[v,i] for i,v in enumerate(values)],state_units=list(range(42,58)),memory=[0]*8,registers=[0,0],pc=0,cue=0,feedback=0,inbox=None,pos=0,energy=12,nursery=[])
    food={i:[0 if i<32 else 1+(i-32)//16,int(h([seed,'food',i])[:8],16)%2] for i in range(64)}
    for segment in (0,1):
        order=sorted(range(16),key=lambda i:h([seed//2,'experience75-cue-order',segment,i]))
        for rank,index in enumerate(order):food[segment*16+index][1]=int(rank>=8)
    heat=58;constructor=70;tick=0;dead=False;events=[];reads=epoch=0;origin=None;shadow=local(e);penalties=0;successes=0;released_successes=0;distinct_reads=set();outcomes=set();contexts=set()
    formation=[dict(unit=i,value=v,energy=1,assistance='supplied ancestor assembly') for i,v in enumerate(values+[0]*16)]
    def snapshot(include_events=True):
        result=dict(control_mode=control,seed=seed,mode='faithful',tick=tick,last=0 if tick else -1,next_id=1,writes=0,constructor_remaining=constructor,heat=heat,formation=formation,food=food,free=list(range(512)) if dead else list(range(58,512)),entities={} if dead else {0:e},births=0,deaths=int(dead),maximum=1)
        if include_events:result['events']=events
        return clone(result)
    observed_events=row['final']['events'];assert type(observed_events) is list and (len(observed_events)==5 if software else 1<=len(observed_events)<=512)
    if software:assert program[:5]==[[4,1,1],[6,0,0],[5,0,1],[6,0,0],[18,0,0]]
    for observed in observed_events:
        assert not dead and any(v[0]==0 for v in food.values())
        tick+=1;before=local(e);op,a,b=program[e['pc']]
        event=dict(tick=tick,actor=0,decoded=[op,a,b],before=h(e),outcome='executed')
        if tick==64:
            assert constructor>=16;constructor-=16;heat+=16
            event['release']=dict(packets=list(range(16,32)),energy=16,assistance='supplied exogenous stock boundary')
        available=sorted(p for p,v in food.items() if v[0]==0 and (p<16 or p>=32 or tick>=64));cue=food[available[0]][1] if available else 0
        e['energy']-=1;heat+=1
        actual_feedback=e['feedback']
        if op==6:
            actual_feedback=0;event['penalty']=0
            if available:
                packet=available[0];kind=food[packet][1];pair=(seed-(75000 if seed<75200 else 75200))//2
                target=seed%2 if packet<16 else ((pair>>1)&1 if kind==0 else pair&1)
                actual_feedback=int(e['registers'][a%2]%2==target)
                event['attempt']=dict(packet=packet,position=0,cue=kind,port=e['registers'][a%2]%2,target=target,success=actual_feedback)
                if actual_feedback:
                    del food[packet];gain=min(20,64-e['energy']);e['energy']+=gain;heat+=20-gain;successes+=1;released_successes+=int(packet>=16)
                else:
                    debit=min(4,e['energy']);e['energy']-=debit;heat+=debit;event['penalty']=debit
            event['feedback']=actual_feedback
        native=move(program,before,actual_feedback,False,cue)
        e['registers']=native['r'];e['memory']=native['m'];e['pc']=native['pc'];e['feedback']=native['feedback']
        if op==0:e['cue']=cue;event['cue']=cue;event['sensor_packet']=available[0] if available else None
        shadow=move(program,shadow,0,True,cue);result=clone(native);sub=None;rewrites=[];sample=None
        if op==1:
            reads+=1
            if control=='own_disrupted':
                value=int(h([seed//2,'own-disrupt31',reads])[:8],16)%2
                sub=dict(read_index=reads,register=a%2,original=result['r'][a%2],value=value);result['r'][a%2]=value
            sample=dict(read_index=reads,own_source_tick=origin,original=native['r'][a%2],value=result['r'][a%2])
            if origin is not None and origin>=64:
                prior=events[origin-1]['attempt'];distinct_reads.add(origin);outcomes.add(prior['success']);contexts.add(prior['cue'])
        saved=clone(shadow) if op==6 else None
        if op==6:
            if control=='retained_disabled':
                for key in ('r','m','pc'):
                    if result[key]!=shadow[key]:rewrites.append(dict(channel=key,original=clone(result[key]),value=clone(shadow[key])))
                    result[key]=clone(shadow[key])
            assert result['feedback']==native['feedback'];epoch+=1;shadow=clone(result);origin=tick if 'attempt' in event else None
        annotation=dict(mode=control,epoch=epoch,read_count=reads,substitution=sub,rewrites=rewrites,shadow_at_action=saved,shadow=clone(shadow),personal_read=sample,latest_own_source_tick=origin)
        e['registers']=result['r'];e['memory']=result['m'];e['pc']=result['pc'];e['feedback']=result['feedback'];event['control']=annotation
        if e['energy']==0:
            dead=True;event['death']=list(range(58))
        else:event['after']=clone(e)
        assert (0 if dead else e['energy'])+constructor+heat+20*len(food)==1420
        assert [x[0] for x in e['code']]==values and e['pos']==0 and e['inbox'] is None and not e['nursery']
        event['state_hash']=h(snapshot(False));assert observed==event;events.append(clone(event))
        if tick==min(64,len(observed_events)):assert row['checkpoint']==snapshot()
        if tick>=64:penalties+=event.get('penalty',0)
    final=snapshot();assert row['final']==final and row['hash']==h(final)
    completed=not any(v[0]==0 for v in food.values());assert (software and tick==5) or tick==512 or dead or completed
    assert row['checkpoint']['tick']==min(64,tick)
    post_instructions=max(0,tick-63)
    return dict(verified=True,software_prepared=software,seed=seed,route=row['route'],control_mode=control,ticks=tick,formation_cost=58,total_paid_cost=58+tick+sum(x.get('penalty',0) for x in events),completed=completed,deaths=int(dead),successes=successes,released_successes=released_successes,post63_instructions=post_instructions,post63_penalties=penalties,score=max(0,20*released_successes-post_instructions-penalties),distinct_personal_post64_reads=len(distinct_reads),read_outcomes=sorted(outcomes),read_contexts=sorted(contexts),heat=heat,energy=0 if dead else e['energy'],births=0,mutation=0,stage_credit=False,learning=False)
