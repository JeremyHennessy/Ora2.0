"""Independent literal finite longitudinal engineering checker.
Only prospective admission differs from reviewed71; no producer/helper import,
new price/resource/scheduler law, learner, scientific seed or activation API.
"""
import hashlib,json

ANCESTOR_WORDS=[4,1,1,6,0,0,5,0,1,6,0,0,10,0,0,12,0,0,13,1,0,13,1,0,7,0,1]

def h(x):return hashlib.sha256(json.dumps(x,sort_keys=True,separators=(',',':')).encode()).hexdigest()
def clone(x):return json.loads(json.dumps(x))

def types(x,key=None):
    if key in ('mutated','ancestor_supplied','checkpoint_replay','learning_demonstrated','software_only'):assert type(x) is bool
    elif isinstance(x,dict):
        for k,v in x.items():types(v,k)
    elif isinstance(x,list):
        for v in x:types(v)
    else:assert x is None or type(x) in (int,str)

def body(identity,parent,generation,code,units,pos):
    return dict(id=identity,parent=parent,generation=generation,code=code,state_units=units,
                memory=[0]*8,registers=[0,0],pc=0,cue=0,feedback=0,inbox=None,pos=pos,energy=12,nursery=[])

def audit(row, projection=None):
    types(row)
    assert set(row)=={'version','seed','mode','fuel_mode','route','genesis_program','inheritance_mode','checkpoint','final','hash','ancestor_supplied','checkpoint_replay','learning_demonstrated','dose','horizon','software_only'}
    assert row['version']=='DIGITAL-PILOT74-FINITE-QUALIFICATION-v1'
    dose=row['dose'];assert type(dose) is int and dose==8
    horizon=row['horizon'];assert type(horizon) is int and horizon in (8192,9216,10240)
    software_only=row['software_only'];assert type(software_only) is bool
    assert software_only is True and type(row['seed']) is int and row['seed'] == 3
    inheritance_mode=row['inheritance_mode'];assert inheritance_mode in ('parent_copy','ancestor_copy')
    assert inheritance_mode=='parent_copy' or row['mode']=='mutating'
    assert row['route']=='ancestor'
    fuel_mode=row['fuel_mode'];assert fuel_mode=='renewed'
    program=row['genesis_program']
    assert 1<=len(program)<=32 and all(type(x) is list and len(x)==3 and all(type(v) is int and 0<=v<32 for v in x) for x in program)
    assert sum(program,[])==ANCESTOR_WORDS
    assert row['ancestor_supplied'] and row['checkpoint_replay'] and not row['learning_demonstrated']
    seed=row['seed'];mode=row['mode'];assert type(seed) is int and seed>=0 and mode=='faithful'
    code=sum(row['genesis_program'],[]);bill=len(code)+16
    org={0:body(0,None,0,[[v,i] for i,v in enumerate(code)],list(range(len(code),bill)),0)}
    occupied=set(range(bill));food={i:[0 if i<32 else 1+(i-32)//16,int(h([seed,'food',i])[:8],16)%2] for i in range(64)}
    formation=[dict(unit=i,value=v,energy=1,assistance='supplied ancestor assembly') for i,v in enumerate(code+[0]*16)]
    heat=bill;constructor=128-bill;writes=0;last=-1;next_id=1;births=deaths=0;maximum=1;events=[];tick=0
    offered=admitted=rejected=0;next_packet=64;turns={0:0}
    certificates={};successful_food=failed_food=mutations=desc_births=messages=0
    personal_food={0:0};birth_edges=[];expiry_records=[];renewed_food=0
    def snapshot(include_events=True):
        state=dict(_dose=dose,inheritance_mode=inheritance_mode,fuel_mode=fuel_mode,turns=turns,offered=offered,admitted=admitted,rejected=rejected,next_packet=next_packet,seed=seed,mode=mode,tick=tick,last=last,next_id=next_id,writes=writes,
                   constructor_remaining=constructor,heat=heat,formation=formation,food=food,
                   free=sorted(set(range(512))-occupied),entities=org,births=births,deaths=deaths,maximum=maximum)
        if include_events:state['events']=events
        return clone(state)
    assert len(row['final']['events'])<=horizon
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
        projection_before=clone(org[actor]) if projection is not None else None
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
                    if mode=='mutating' and draw%100<dose:value=(value+1+(draw//100)%31)%32
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
        if projection is not None:projection.observe(projection_before,event,snapshot)
        if tick==min(64,row['final']['tick']):assert row['checkpoint']==snapshot()
    final=snapshot();assert row['final']==final and row['hash']==h(final)
    assert tick==horizon or not org
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
    return dict(dose=dose,horizon=horizon,software_only=software_only,scientific_admission=False,inheritance_mode=inheritance_mode,genesis_program_hash=h(code),fuel_mode=fuel_mode,offered_tokens=offered,admitted_tokens=admitted,rejected_tokens=rejected,renewed_food=renewed_food,turns=clone(turns),expiry_records=expiry_records,birth_edges=birth_edges,turnover=turnover,selection=False,stage_credit=False,pre_food=pre,post_food=post,formation_cost=len(code)+16,founder_action_signature=signature,verified=True,seed=seed,route=row['route'],mode=mode,ticks=tick,births=births,descendant_births=desc_births,deaths=deaths,
                successful_food=successful_food,failed_food=failed_food,unused_food=len(food),paid_copy_words=writes,
                mutations=mutations,maximum_population=maximum,heat=heat,live_energy=sum(e['energy'] for e in org.values()),
                free_material=512-len(occupied),messages=messages,change_exposed=sum('attempt' in ev and ev['attempt']['position']!=0 and ev['attempt']['target']==1 for ev in events),
                remote_food=sum(bool(ev.get('attempt',{}).get('success')) and ev['attempt']['position']!=0 for ev in events),
                descendant_remote_food=sum(bool(ev.get('attempt',{}).get('success')) and ev['attempt']['position']!=0 and ev['actor']!=0 for ev in events),
                repeated_hidden_port_actors=len({ev['actor'] for ev in events if 'attempt' in ev and ev['attempt']['position']!=0 and ev['attempt']['target']==1 and sum('attempt' in prior and prior['actor']==ev['actor'] and prior['attempt']['position']==ev['attempt']['position'] for prior in events[:ev['tick']-1])>=1}),
                learning=False,evolution=False,repair=False)


CAPSULE_VERSION='DIGITAL-PILOT74-STATE-data-v1'
AUDIT_VERSION='DIGITAL-PILOT74-AUDIT-v1'

def _pairs(items):
    result={}
    for k,v in items:
        assert k not in result
        result[k]=v
    return result

def verify_capsule(raw,expected_identity,expected_sha256,extent,projection=None):
    """Independent full-prefix audit; never part of direct hydration."""
    assert type(raw) is bytes and type(extent) is int and 0<extent<=40*1024**2
    assert len(raw)==extent and hashlib.sha256(raw).hexdigest()==expected_sha256
    assert type(expected_identity) is dict and set(expected_identity)=={'revision','source_sha256','config_sha256','law'}
    for field,length in [('revision',40),('source_sha256',64),('config_sha256',64)]:
        value=expected_identity[field]
        assert type(value) is str and len(value)==length and all(c in '0123456789abcdef' for c in value)
    assert expected_identity['law']=='DIGITAL-PILOT74-FINITE-QUALIFICATION-v1'
    capsule=json.loads(raw.decode('ascii'),object_pairs_hook=_pairs,parse_constant=lambda v: (_ for _ in ()).throw(ValueError(v)))
    assert type(capsule) is dict and set(capsule)=={'version','identity','checkpoint64','state','state_sha256'}
    assert capsule['version']==CAPSULE_VERSION and capsule['identity']==expected_identity
    assert json.dumps(capsule,sort_keys=True,separators=(',',':'),ensure_ascii=True).encode('ascii')==raw
    state=capsule['state'];assert capsule['state_sha256']==h(state)
    assert type(state['tick']) is int and state['tick'] in (8192,9216,10240)
    row=dict(version='DIGITAL-PILOT74-FINITE-QUALIFICATION-v1',seed=state['seed'],mode='faithful',inheritance_mode='parent_copy',fuel_mode='renewed',route='ancestor',dose=8,horizon=state['tick'],software_only=True,genesis_program=[ANCESTOR_WORDS[i:i+3] for i in range(0,27,3)],checkpoint=capsule['checkpoint64'],final=state,hash=h(state),ancestor_supplied=True,checkpoint_replay=True,learning_demonstrated=False)
    summary=audit(row,projection)
    return dict(version=AUDIT_VERSION,verified=True,identity=expected_identity,capsule_sha256=expected_sha256,extent=extent,state_sha256=h(state),tick=state['tick'],audit_prefix_instructions=summary['ticks'],summary=summary,engineering_only=True,stage_credit=False)

# New source-free projection collector. No import of producer/cursor/helpers.
PROJECT_FIELDS=('tick','entities','food','free','constructor_remaining','heat','formation','offered','admitted','rejected','next_packet','next_id','writes','births','deaths','maximum','last','turns')

def public_bytes(value):return json.dumps(value,sort_keys=True,separators=(',',':'),ensure_ascii=True).encode('ascii')
def public_hash(raw):return hashlib.sha256(raw).hexdigest()
def public_view(state):return clone({key:state[key] for key in PROJECT_FIELDS})
def public_descriptor(name,raw):return dict(name=name,extent=len(raw),sha256=public_hash(raw))

def external(raw,authority,cap):
    assert type(raw) is bytes and 0<len(raw)<=cap
    assert type(authority) is dict and set(authority)=={'extent','sha256'} and type(authority['extent']) is int and authority['extent']==len(raw)
    value=authority['sha256'];assert type(value) is str and len(value)==64 and all(c in '0123456789abcdef' for c in value) and public_hash(raw)==value
    def bad(x):raise ValueError(x)
    result=json.loads(raw.decode('ascii'),object_pairs_hook=_pairs,parse_constant=bad);assert public_bytes(result)==raw
    return result

class ProjectionCollector:
    def __init__(self,initial,identity,capsule_sha,audit_sha,mode,boundary_state_sha256=None):
        self.initial=initial;assert type(initial) is str and len(initial)==64;self.identity=clone(identity);self.capsule_sha=capsule_sha;self.audit_sha=audit_sha;self.mode=mode
        self.past=[];self.files={};self.chunks=[];self.pending=[];self.checkpoints={}
        self.boundary_expected=boundary_state_sha256;self.boundary_actual={}
    def observe(self,before,event,snapshot):
        tick=event['tick']
        if self.boundary_expected is not None and tick in self.boundary_expected:
            full=snapshot();actual=h(full);assert actual==self.boundary_expected[tick],'Full literal boundary state mismatch'
            self.boundary_actual[tick]=actual;del full
        if 'birth' in event and tick<=8192:
            child=event['birth']['child'];self.past.append(dict(tick=tick,parent=event['actor'],child=child['id'],generation=child['generation']))
        if tick<8192:return
        if tick==8192:
            state=snapshot();assert h(state)==self.initial,'Complete independently reconstructed8192 hash mismatch'
            v=public_view(state);iv=dict(schema='ora-pilot-initial-state-v1',identity=clone(self.identity),cut=8192,source_capsule_sha256=self.capsule_sha,literal_audit_sha256=self.audit_sha,world_state_sha256=h(state),projection_sha256=h(v),state=v,existing_actor_ids=sorted(int(k) for k in state['entities']),supplied_behavior=True,schematic_positioning=True)
            gv=dict(schema='ora-pilot-genesis-summary-v1',identity=clone(self.identity),cut=8192,source_capsule_sha256=self.capsule_sha,ancestor_words=[u['value'] for u in state['formation'][:27]],formation=clone(state['formation']),past_birth_edges=self.past)
            a=public_bytes(iv);b=public_bytes(gv);assert len(a)<=65536 and len(b)<=16384
            self.files['initial.000001.json']=a;self.files['genesis.000001.json']=b;self.checkpoints[8192]=h(v);self.initial=None;return
        state=snapshot(False);after=event.get('after');op=event['decoded'][0]
        attempt=event.get('attempt');gain=0
        if attempt is not None and attempt['success']:
            assert after is not None;gain=after['energy']-before['energy']+1;assert 0<=gain<=20
        food={'attempted':attempt is not None,'packet':None if attempt is None else attempt['packet'],'site':None if attempt is None else attempt['position'],'cue':None if attempt is None else attempt['cue'],'port':None if attempt is None else attempt['port'],'success':0 if attempt is None else attempt['success'],'feedback':event.get('feedback'),'captured_energy':gain,'cap_heat':20-gain if attempt is not None and attempt['success'] else 0}
        move=None
        if op==13:
            position=(before['pos']+(2*(before['registers'][event['decoded'][1]%2]%2)-1))%4
            if after is not None:assert after['pos']==position
            move=dict(from_site=before['pos'],to_site=position)
        total={'heat':state['heat'],'constructor_remaining':state['constructor_remaining'],'food_energy':len(state['food'])*20,'living_energy':sum(body['energy'] for body in state['entities'].values()),'free_material':len(state['free']),'offered':state['offered'],'admitted':state['admitted'],'rejected':state['rejected'],'writes':state['writes'],'births':state['births'],'deaths':state['deaths'],'population':len(state['entities'])}
        projected={'tick':tick,'actor':event['actor'],'decoded':clone(event['decoded']),'outcome':event['outcome'],'body_before_sha256':h(before),'body_after_sha256':None if after is None else h(after),'body_after':clone(after),'move':move,'food':food,'copy':[{key:value for key,value in write.items() if key!='mutation_draw'} for write in event.get('writes',[])],'birth':clone(event.get('birth')),'death':clone(event.get('death')),'expiry':clone(event.get('expiry')),'message':clone(event.get('message')),'transfer':{'recipient':event['transfer'],'energy':1} if 'transfer' in event else None,'input':clone(event.get('input',[])),'totals':total,'projection_sha256':h(public_view(state))}
        self.pending.append(projected)
        if tick in (9216,10240):self.checkpoints[tick]=projected['projection_sha256']
        if len(self.pending)==128:
            index=len(self.chunks)+1;name='events.000001.'+format(index,'04d')+'.json';first=self.pending[0]['tick']
            value={'schema':'ora-pilot-event-chunk-v1','identity':clone(self.identity),'sequence':1,'chunk_sequence':index,'first_tick':first,'last_tick':tick,'event_count':128,'events':self.pending}
            raw=public_bytes(value);assert len(raw)<=1024**2
            self.files[name]=raw;self.chunks.append(dict(public_descriptor(name,raw),sequence=index,first_tick=first,last_tick=tick,event_count=128,identity=clone(self.identity)));self.pending=[]
    def finish(self,cut):
        assert self.initial is None and not self.pending and len(self.chunks)==(cut-8192)//128 and cut in (8192,9216,10240)
        seq={8192:1,9216:2,10240:3}[cut]
        initial=dict(public_descriptor('initial.000001.json',self.files['initial.000001.json']),cut=8192,source_capsule_sha256=self.capsule_sha,literal_audit_sha256=self.audit_sha)
        manifest={'schema':'ora-pilot-event-manifest-v1','identity':clone(self.identity),'sequence':seq,'mode':self.mode,'initial_state':initial,'genesis_summary':public_descriptor('genesis.000001.json',self.files['genesis.000001.json']),'chunks':self.chunks,'first_tick':8192,'last_tick':cut,'supplied_behavior':True,'schematic_positioning':True}
        raw=public_bytes(manifest);assert len(raw)<=16384;name='manifest.'+format(seq,'06d')+'.json';self.files[name]=raw
        return public_descriptor(name,raw)

def verify_projection(initial_raw,initial_audit_raw,terminal_raw,terminal_audit_raw,provided,*,source_identity,identity,initial_authority,terminal_authority,mode='recorded',boundary_state_sha256=None):
    """Full independent literal+projection work, ONLY in a separately admitted role."""
    assert mode in ('fixture','recorded') and type(provided) is dict and 3<=len(provided)<=19
    assert set(identity)=={'run_id','world_id','source_revision','source_manifest_sha256','configuration_sha256'}
    for key in ('run_id','world_id'):
        text=identity[key];assert type(text) is str and 1<=len(text)<=80 and all(c.isascii() and (c.isalnum() or c in '-_.') for c in text)
    assert identity['source_revision']==source_identity['revision'] and identity['source_manifest_sha256']==source_identity['source_sha256'] and identity['configuration_sha256']==source_identity['config_sha256']
    for a in (initial_authority,terminal_authority):assert type(a) is dict and set(a)=={'capsule','audit'}
    # Decode one externally pinned capsule at a time, release it before the
    # next decode and before independent full literal reconstruction. Complete
    # initial-state equality relies on the existing canonical SHA256 premise.
    metadata={}
    for label,raw,audit_raw,authority in (('first',initial_raw,initial_audit_raw,initial_authority),('final',terminal_raw,terminal_audit_raw,terminal_authority)):
        cap=external(raw,authority['capsule'],40*1024**2)
        proof=external(audit_raw,authority['audit'],128*1024)
        assert set(cap)=={'version','identity','checkpoint64','state','state_sha256'} and cap['version']==CAPSULE_VERSION and cap['identity']==source_identity and cap['state_sha256']==h(cap['state'])
        assert set(proof)=={'version','verified','identity','capsule_sha256','extent','state_sha256','tick','audit_prefix_instructions','summary','engineering_only','stage_credit'}
        assert proof['version']==AUDIT_VERSION and proof['verified'] is True and proof['engineering_only'] is True and proof['stage_credit'] is False
        assert proof['identity']==source_identity and proof['capsule_sha256']==public_hash(raw) and type(proof['extent']) is int and proof['extent']==len(raw) and proof['state_sha256']==cap['state_sha256']
        assert type(proof['tick']) is int and proof['tick']==cap['state']['tick'] and type(proof['audit_prefix_instructions']) is int and proof['audit_prefix_instructions']==proof['tick']
        metadata[label]=dict(tick=proof['tick'],state_sha256=cap['state_sha256'])
        del cap,proof
    assert metadata['first']['tick']==8192
    if boundary_state_sha256 is not None:
        assert type(boundary_state_sha256) is dict and set(boundary_state_sha256)=={8192,9216,10240} and metadata['final']['tick']==10240
        assert boundary_state_sha256[8192]==metadata['first']['state_sha256'] and boundary_state_sha256[10240]==metadata['final']['state_sha256']
    collector=ProjectionCollector(metadata['first']['state_sha256'],identity,public_hash(initial_raw),public_hash(initial_audit_raw),mode,boundary_state_sha256)
    proof=verify_capsule(terminal_raw,source_identity,public_hash(terminal_raw),len(terminal_raw),collector)
    manifest=collector.finish(proof['tick']);assert set(provided)==set(collector.files)
    for name,expected in collector.files.items():assert type(provided[name]) is bytes and provided[name]==expected,'Independent full projection bytes mismatch: '+name
    assert len(collector.checkpoints)==(1 if proof['tick']==8192 else 2 if proof['tick']==9216 else 3)
    return dict(schema='DIGITAL-PILOT74-INDEPENDENT-PROJECTION-v2',verified=True,identity=clone(identity),manifest=manifest,files={k:public_descriptor(k,v) for k,v in collector.files.items()},literal_capsule_sha256=proof['capsule_sha256'],literal_audit_prefix_instructions=proof['audit_prefix_instructions'],initial_capsule_sha256=public_hash(initial_raw),initial_literal_audit_sha256=public_hash(initial_audit_raw),terminal_literal_audit_sha256=public_hash(terminal_audit_raw),projection_checkpoints=collector.checkpoints,full_state_checkpoints=collector.boundary_actual,producer_imported=False,worlds_constructed=0,vm_steps=0,publication_accepted=False,live_attachment=False,stage_credit=False)
