"""Pure recorded projection from externally authenticated PILOT74 capsules.

No World, loader, publisher, I/O, entropy or audit execution. External digest
registration and full independent literal authentication remain caller gates.
"""
import hashlib,json
MIB=1024**2
VIEW_FIELDS=('tick','entities','food','free','constructor_remaining','heat','formation','offered','admitted','rejected','next_packet','next_id','writes','births','deaths','maximum','last','turns')
CUTS={8192:1,9216:2,10240:3}

def enc(v):return json.dumps(v,sort_keys=True,separators=(',',':'),ensure_ascii=True).encode('ascii')
def sha(b):return hashlib.sha256(b).hexdigest()
def h(v):return sha(enc(v))
def copy(v):return json.loads(enc(v))
def integer(v,lo,hi):
    assert type(v) is int and lo<=v<=hi
    return v

def pairs(items):
    out={}
    for k,v in items:
        assert k not in out
        out[k]=v
    return out

def decode(raw,cap):
    assert type(raw) is bytes and 0<len(raw)<=cap
    def constant(v):raise ValueError('Nonfinite JSON '+v)
    value=json.loads(raw.decode('ascii'),object_pairs_hook=pairs,parse_constant=constant)
    assert enc(value)==raw
    def typed(v,depth=0):
        assert depth<=24
        if type(v) is dict:
            assert all(type(k) is str for k in v)
            for x in v.values():typed(x,depth+1)
        elif type(v) is list:
            for x in v:typed(x,depth+1)
        else:assert v is None or type(v) in (int,str,bool)
    typed(value)
    return value

def spec(raw,expected,cap):
    assert type(expected) is dict and set(expected)=={'extent','sha256'}
    integer(expected['extent'],1,cap)
    assert type(expected['sha256']) is str and len(expected['sha256'])==64 and all(c in '0123456789abcdef' for c in expected['sha256'])
    assert type(raw) is bytes and len(raw)==expected['extent'] and sha(raw)==expected['sha256']

def wire_identity(identity,source):
    assert type(identity) is dict and set(identity)=={'run_id','world_id','source_revision','source_manifest_sha256','configuration_sha256'}
    for key in ('run_id','world_id'):
        x=identity[key];assert type(x) is str and 1<=len(x)<=80 and all(c.isascii() and (c.isalnum() or c in '-_.') for c in x)
    assert identity['source_revision']==source['revision'] and identity['source_manifest_sha256']==source['source_sha256'] and identity['configuration_sha256']==source['config_sha256']
    for key,n in (('source_revision',40),('source_manifest_sha256',64),('configuration_sha256',64)):
        x=identity[key];assert type(x) is str and len(x)==n and all(c in '0123456789abcdef' for c in x)

def authenticated_data(raw,audit_raw,source,authority):
    # Hashes are EXTERNAL inputs. A self-authored verified flag is insufficient.
    assert type(authority) is dict and set(authority)=={'capsule','audit'}
    spec(raw,authority['capsule'],40*MIB);spec(audit_raw,authority['audit'],128*1024)
    cap=decode(raw,40*MIB);proof=decode(audit_raw,128*1024)
    assert type(source) is dict and set(source)=={'revision','source_sha256','config_sha256','law'}
    assert source['law']=='DIGITAL-PILOT74-FINITE-QUALIFICATION-v1'
    assert set(cap)=={'version','identity','checkpoint64','state','state_sha256'} and cap['version']=='DIGITAL-PILOT74-STATE-data-v1' and cap['identity']==source
    state=cap['state'];assert type(state['tick']) is int and state['tick'] in CUTS and type(state['seed']) is int and state['seed']==3
    assert state['mode']=='faithful' and state['fuel_mode']=='renewed' and state['inheritance_mode']=='parent_copy' and state['_dose']==8
    assert cap['state_sha256']==h(state) and len(state['events'])==state['tick']
    assert set(proof)=={'version','verified','identity','capsule_sha256','extent','state_sha256','tick','audit_prefix_instructions','summary','engineering_only','stage_credit'}
    assert proof['version']=='DIGITAL-PILOT74-AUDIT-v1' and proof['verified'] is True and proof['engineering_only'] is True and proof['stage_credit'] is False
    assert proof['identity']==source and proof['capsule_sha256']==sha(raw) and type(proof['extent']) is int and proof['extent']==len(raw)
    assert proof['state_sha256']==cap['state_sha256'] and type(proof['tick']) is int and proof['tick']==state['tick'] and type(proof['audit_prefix_instructions']) is int and proof['audit_prefix_instructions']==state['tick']
    assert proof['summary']['verified'] is True and proof['summary']['stage_credit'] is False and proof['summary']['software_only'] is True
    return cap

def view(state):return copy({k:state[k] for k in VIEW_FIELDS})

def totals(state):
    return dict(heat=state['heat'],constructor_remaining=state['constructor_remaining'],food_energy=20*len(state['food']),living_energy=sum(b['energy'] for b in state['entities'].values()),free_material=len(state['free']),offered=state['offered'],admitted=state['admitted'],rejected=state['rejected'],writes=state['writes'],births=state['births'],deaths=state['deaths'],population=len(state['entities']))

def check_material(state):
    owned=list(state['free'])
    for b in state['entities'].values():owned.extend([x[1] for x in b['code']]+b['state_units']+[w['unit'] for w in b['nursery']])
    assert len(owned)==512 and sorted(owned)==list(range(512))

class Cursor:
    """Apply authenticated recorded deltas; never interpret a VM instruction."""
    def __init__(self,state):
        self.state=copy({k:v for k,v in state.items() if k!='events'})
        assert self.state['tick']==8192
        t=totals(self.state);self.energy=t['heat']+t['constructor_remaining']+t['food_energy']+t['living_energy'];self.admitted=self.state['admitted']
        check_material(self.state)
    def advance(self,event):
        s=self.state;tick=integer(event['tick'],8193,10240);assert tick==s['tick']+1
        actor=integer(event['actor'],0,s['next_id']-1);key=str(actor);ids=sorted(map(int,s['entities']));assert actor==next((i for i in ids if i>s['last']),ids[0])
        before=copy(s['entities'][key]);assert h(before)==event['before']
        op=event['decoded'][0];assert type(event['decoded']) is list and len(event['decoded'])==3
        for v in event['decoded']:integer(v,0,31)
        s['tick']=tick;s['last']=actor;s['heat']+=1;free=set(s['free'])
        offers=event.get('input',[]);assert ('input' in event)==(tick%64==0) and 'release' not in event
        if offers:assert len(offers)==16
        for offer in offers:
            packet=offer['packet'];assert packet==s['next_packet'];s['next_packet']+=1;s['offered']+=1
            if offer['outcome']=='admitted':
                assert str(packet) not in s['food'];s['food'][str(packet)]=[offer['site'],offer['kind']];s['admitted']+=1
            else:assert offer['outcome']=='rejected';s['rejected']+=1
        food=dict(attempted=False,packet=None,site=None,cue=None,port=None,success=0,feedback=event.get('feedback'),captured_energy=0,cap_heat=0)
        if 'attempt' in event:
            a=event['attempt'];assert op==6 and s['food'][str(a['packet'])]==[a['position'],a['cue']]
            food.update(attempted=True,packet=a['packet'],site=a['position'],cue=a['cue'],port=a['port'],success=a['success'])
            if a['success']:
                del s['food'][str(a['packet'])];gain=min(20,64-(before['energy']-1));food['captured_energy']=gain;food['cap_heat']=20-gain;s['heat']+=20-gain
        writes=event.get('writes',[])
        if writes:
            assert op==10 and len(writes)==3
            for w in writes:assert w['unit'] in free;free.remove(w['unit'])
            s['writes']+=len(writes);s['heat']+=len(writes)
        birth=event.get('birth')
        if birth is not None:
            assert op==12;child=birth['child'];cid=child['id'];assert cid==s['next_id'] and child['parent']==actor and str(cid) not in s['entities']
            assert birth['release_energy']==2 and birth['startup_energy']==12 and len(birth['state_formation'])==16
            for u in birth['state_formation']:assert u['unit'] in free and u['energy']==1;free.remove(u['unit'])
            s['entities'][str(cid)]=copy(child);s['turns'][str(cid)]=0;s['next_id']+=1;s['births']+=1;s['heat']+=18
        message=event.get('message')
        if message is not None:s['entities'][str(message['recipient'])]['inbox']=message['value']
        transfer=event.get('transfer')
        if transfer is not None:s['entities'][str(transfer)]['energy']+=1
        if op==17:s['heat']+=before['energy']-1
        death=event.get('death');after=event.get('after')
        if death is not None:
            assert after is None and len(set(death))==len(death) and not free.intersection(death);free.update(death);del s['entities'][key];s['deaths']+=1
        else:assert type(after) is dict and after['id']==actor;s['entities'][key]=copy(after)
        s['maximum']=max(s['maximum'],len(s['entities']));s['free']=sorted(free)
        assert h(s)==event['vm_state_hash'],'Recorded pre-turn world hash mismatch'
        s['turns'][key]+=1;expiry=event.get('expiry')
        if expiry is not None:
            assert expiry['actor']==actor and s['turns'][key]==256 and h(s['entities'][key])==expiry['body_before']
            assert expiry['energy']==s['entities'][key]['energy'] and len(set(expiry['units']))==len(expiry['units']) and not free.intersection(expiry['units'])
            s['heat']+=expiry['energy'];free.update(expiry['units']);del s['entities'][key];s['free']=sorted(free);s['deaths']+=1
        assert h(s)==event['state_hash'],'Recorded final world hash mismatch';check_material(s)
        t=totals(s);assert t['heat']+t['constructor_remaining']+t['food_energy']+t['living_energy']==self.energy+20*(s['admitted']-self.admitted)
        move=None
        if op==13:
            position=after['pos'] if after is not None else (before['pos']+(1 if before['registers'][event['decoded'][1]%2]%2 else -1))%4
            move=dict(from_site=before['pos'],to_site=position)
        return dict(tick=tick,actor=actor,decoded=copy(event['decoded']),outcome=event['outcome'],body_before_sha256=event['before'],body_after_sha256=h(after) if after is not None else None,body_after=copy(after),move=move,food=food,copy=[{k:v for k,v in w.items() if k!='mutation_draw'} for w in writes],birth=copy(birth),death=copy(death),expiry=copy(expiry),message=copy(message),transfer=None if transfer is None else dict(recipient=transfer,energy=1),input=copy(offers),totals=t,projection_sha256=h(view(s)))

def descriptor(name,raw):return dict(name=name,extent=len(raw),sha256=sha(raw))

def project(initial_raw,initial_audit_raw,terminal_raw,terminal_audit_raw,*,source_identity,identity,initial_authority,terminal_authority,mode='recorded'):
    """Return bounded immutable payload BYTES; does not publish or authenticate OS."""
    assert mode in ('fixture','recorded');wire_identity(identity,source_identity)
    initial=authenticated_data(initial_raw,initial_audit_raw,source_identity,initial_authority);state=initial['state'];assert state['tick']==8192
    initial_state_hash=initial['state_sha256'];prefix_hash=h(state['events']);cursor=Cursor(state)
    initial_value=dict(schema='ora-pilot-initial-state-v1',identity=copy(identity),cut=8192,source_capsule_sha256=sha(initial_raw),literal_audit_sha256=sha(initial_audit_raw),world_state_sha256=initial_state_hash,projection_sha256=h(view(state)),state=view(state),existing_actor_ids=sorted(map(int,state['entities'])),supplied_behavior=True,schematic_positioning=True)
    genesis=dict(schema='ora-pilot-genesis-summary-v1',identity=copy(identity),cut=8192,source_capsule_sha256=sha(initial_raw),ancestor_words=[x['value'] for x in state['formation'][:27]],formation=copy(state['formation']),past_birth_edges=[dict(tick=e['tick'],parent=e['actor'],child=e['birth']['child']['id'],generation=e['birth']['child']['generation']) for e in state['events'] if 'birth' in e])
    del state,initial
    terminal=authenticated_data(terminal_raw,terminal_audit_raw,source_identity,terminal_authority);state=terminal['state'];cut=state['tick'];sequence=CUTS[cut]
    assert h(state['events'][:8192])==prefix_hash
    files={};initial_name='initial.000001.json';genesis_name='genesis.000001.json'
    for name,value,cap in ((initial_name,initial_value,65536),(genesis_name,genesis,16384)):
        raw=enc(value);assert len(raw)<=cap;files[name]=raw
    chunks=[];pending=[];checkpoints={8192:h(view(cursor.state))}
    for event in state['events'][8192:]:
        pending.append(cursor.advance(event))
        if event['tick']==9216:checkpoints[9216]=h(view(cursor.state))
        if len(pending)==128:
            n=len(chunks)+1;name='events.000001.'+str(n).zfill(4)+'.json'
            chunk=dict(schema='ora-pilot-event-chunk-v1',identity=copy(identity),sequence=1,chunk_sequence=n,first_tick=pending[0]['tick'],last_tick=pending[-1]['tick'],event_count=128,events=pending)
            raw=enc(chunk);assert len(raw)<=MIB;files[name]=raw;chunks.append(dict(descriptor(name,raw),sequence=n,first_tick=chunk['first_tick'],last_tick=chunk['last_tick'],event_count=128,identity=copy(identity)));pending=[]
    assert not pending and len(chunks)==(cut-8192)//128 and len(chunks)<=16
    assert cursor.state=={k:v for k,v in state.items() if k!='events'},'Full endpoint reconstruction mismatch'
    checkpoints[cut]=h(view(cursor.state))
    manifest=dict(schema='ora-pilot-event-manifest-v1',identity=copy(identity),sequence=sequence,mode=mode,initial_state=dict(descriptor(initial_name,files[initial_name]),cut=8192,source_capsule_sha256=sha(initial_raw),literal_audit_sha256=sha(initial_audit_raw)),genesis_summary=descriptor(genesis_name,files[genesis_name]),chunks=chunks,first_tick=8192,last_tick=cut,supplied_behavior=True,schematic_positioning=True)
    raw=enc(manifest);assert len(raw)<=16384;name='manifest.'+str(sequence).zfill(6)+'.json';files[name]=raw
    return dict(files=files,manifest=descriptor(name,raw),projection_checkpoints=checkpoints,raw_terminal_capsule_sha256=sha(terminal_raw),raw_terminal_literal_audit_sha256=sha(terminal_audit_raw),publication_accepted=False,live_attachment=False,stage_credit=False)
