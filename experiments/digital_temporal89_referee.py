"""Producer-free temporal task literal. Only hashlib/json imports; no shared task helpers."""
import hashlib,json

def duplicate(x):return json.loads(json.dumps(x))
def digest(x):return hashlib.sha256(json.dumps(x,sort_keys=True,separators=(',',':')).encode()).hexdigest()

def admit(seed,admission):
    assert type(seed) is int
    assert (seed in (2100589,2100590) and admission=='TEMPORAL89-SOFTWARE-v1' or
            seed in tuple(range(1010500,1010508))+tuple(range(1010700,1010708)) and admission=='TEMPORAL89-PRIMARY-v1')

def label_mask(seed,trial,admission):
    admit(seed,admission);assert type(trial) is int and 0<=trial<60
    phase=int(trial>=48)
    if seed in (2100589,2100590):return ((0,255),(90,165))[seed-2100589][phase]
    bank=tuple(range(1010500,1010508)) if seed in range(1010500,1010508) else tuple(range(1010700,1010708))
    offset=bank.index(seed)
    return (0,255)[offset] if offset<2 else int(digest(['TEMPORAL89-LABELS-v1',seed,phase])[:2],16)

def task_observation(seed,trial,channel,admission):
    admit(seed,admission);assert type(trial) is int and 0<=trial<60 and channel in ('cue','pre','post')
    return int(digest(['TEMPORAL89-OBS-v1',seed,trial,channel])[:2],16)%8

REFERENCE_PROGRAMMES={'fixed0': [[7, 2, 1], [0, 0, 0], [0, 0, 0], [4, 0, 0], [6, 0, 0], [0, 0, 0], [7, 0, 1]], 'fixed1': [[7, 2, 1], [0, 0, 0], [0, 0, 0], [4, 0, 1], [6, 0, 0], [0, 0, 0], [7, 0, 1]], 'retained_cue': [[7, 2, 1], [0, 1, 0], [0, 0, 0], [6, 1, 0], [0, 0, 0], [7, 0, 1]], 'retained_inverse': [[7, 2, 1], [0, 1, 0], [0, 0, 0], [21, 1, 0], [6, 1, 0], [0, 0, 0], [7, 0, 1]], 'current_distractor': [[7, 2, 1], [0, 0, 0], [0, 0, 0], [6, 0, 0], [0, 0, 0], [7, 0, 1]], 'current_inverse': [[7, 2, 1], [0, 0, 0], [0, 0, 0], [21, 0, 0], [6, 0, 0], [0, 0, 0], [7, 0, 1]], 'alternation0': [[7, 2, 1], [4, 1, 0], [0, 0, 0], [0, 0, 0], [6, 1, 0], [0, 0, 0], [21, 1, 0], [7, 0, 2]], 'alternation1': [[7, 2, 1], [4, 1, 1], [0, 0, 0], [0, 0, 0], [6, 1, 0], [0, 0, 0], [21, 1, 0], [7, 0, 2]], 'latest0': [[7, 2, 1], [4, 1, 0], [0, 0, 0], [0, 0, 0], [6, 1, 0], [0, 0, 0], [1, 0, 0], [8, 0, 9], [7, 0, 2], [21, 1, 0], [7, 0, 2]], 'latest1': [[7, 2, 1], [4, 1, 1], [0, 0, 0], [0, 0, 0], [6, 1, 0], [0, 0, 0], [1, 0, 0], [8, 0, 9], [7, 0, 2], [21, 1, 0], [7, 0, 2]]}
ARMS=('intact','credit_erased','recall_disabled','model_disabled','update_frozen')
ROLES=tuple(f'q{q}:{a}' for q in (2,4,8) for a in ARMS)+tuple(REFERENCE_PROGRAMMES)
def programme(role):
    assert type(role) is str and role in ROLES
    if role in REFERENCE_PROGRAMMES:return duplicate(REFERENCE_PROGRAMMES[role])
    q=int(role[1])
    return [[7,q,1],[0,1,0],[0,0,0],[19,0,1],[6,0,0],[0,0,0],[1,0,0],[8,0,9],[7,0,1],[19,0,1],[21,0,0],[20,1,0],[7,0,1]]

def completed_edge(role,pc,after,program):
    entry=2 if role.startswith(('latest','alternation')) else 1
    return after is not None and pc!=0 and program[pc][0]==7 and after['pc']==entry

def audit(state,*,seed,mode,max_population,expansion_tick,program,horizon,ledger,role,admission=None):
    admit(seed,admission)
    assert mode=='no_variation' and max_population==1 and expansion_tick==0 and horizon==1024
    assert type(program) is list and program==programme(role) and program[0][1] in (2,4,8)
    def typed(value):
        if type(value) is dict:
            assert all(type(k) is str for k in value)
            for v in value.values():typed(v)
        elif type(value) is list:
            for v in value:typed(v)
        else:assert value is None or type(value) in (int,str)
    typed(state);typed(ledger)
    assert type(ledger) is list and len(ledger)==len(state['events'])
    completed=0;phase='cue';original_cue=None;credit_due=False;arm=role.split(':')[1] if ':' in role else None
    software_assistance=None;control=None
    def newborn(identity, parent, generation, dna, units, lineage):
        return dict(id=identity,parent=parent,generation=generation,lineage=lineage,
                    code=duplicate(dna),state_units=units,memory=[0]*dna[1][0],
                    registers=[0,0],pc=0,feedback=0,cue=0,pos=0,energy=112,
                    nursery=[],pending=None,lease=None,turns=0,copy_sessions=0,children=0)

    words=[v for triple in program for v in triple]
    footprint=len(words)+program[0][1]+8
    assert 256-footprint-112 >= 16
    s=dict(seed=seed,mode=mode,max_population=max_population,expansion_tick=expansion_tick,
           tick=0,last=-1,next_id=1,writes=0,births=0,deaths=0,offered=0,admitted=0,
           rejected=0,next_packet=64,heat=footprint,constructor_remaining=256-footprint-112,
           food={str(p):p%(8 if expansion_tick==0 else 2) for p in range(64)},leases={},
           free=list(range(footprint,512)),entities={'0':newborn(0,None,0,
               [[v,i] for i,v in enumerate(words)],list(range(len(words),footprint)),[])})

    def charge(e, amount):
        assert e['energy'] >= amount
        e['energy']-=amount; s['heat']+=amount

    def packet(e, reserve=False):
        if e['lease'] is not None: return e['lease']
        available=sorted(int(p) for p in s['food'] if p not in s['leases']
                         and (not 16<=int(p)<32 or s['tick']>=64))
        if not available: return None
        p=available[0]
        if reserve: e['lease']=p; s['leases'][str(p)]=e['id']
        return p

    def write(e, event, units, allele=None):
        if e['energy']<3:
            s['free']=sorted(s['free']+units); event['copy_refused']='word_energy'; return
        charge(e,3); event['writes']=[]
        for unit in units:
            index=len(e['nursery']); original,source=e['code'][index]
            value=allele if index==1 and allele is not None else original
            record=dict(unit=unit,value=value,index=index,source_unit=source,
                        source_value=original,write_id=s['writes'],mutated=int(value!=original))
            s['writes']+=1; e['nursery'].append(record); event['writes'].append(duplicate(record))

    def conserved():
        units=s['free'][:]
        for e in s['entities'].values():
            units += [v[1] for v in e['code']]+e['state_units']+[w['unit'] for w in e['nursery']]
            if e['pending']: units+=e['pending']['units']
            assert 0<e['energy']<=224 and e['turns']<2048
        assert sorted(units)==list(range(512)) and len(s['entities'])<=max_population
        assert len(s['food'])<=64 and s['offered']==s['admitted']+s['rejected']
        assert sum(e['energy'] for e in s['entities'].values())+s['heat']+s['constructor_remaining']+20*len(s['food'])==1536+20*s['admitted']
        for p,owner in s['leases'].items():
            assert p in s['food'] and s['entities'][str(owner)]['lease']==int(p)

    charged=footprint
    events=state['events']; assert type(events) is list and len(events)<=horizon
    conserved()
    for receipt in events:
        assert s['entities'] and s['tick']<horizon
        ids=sorted(int(i) for i in s['entities'])
        actor=next((i for i in ids if i>s['last']),ids[0]); s['last']=actor
        e=s['entities'][str(actor)]
        assert completed<60 and charged+5+(16 if s['tick']+1==64 else 0)<=1024
        trial=completed;active=completed>=48;cut=None
        if credit_due:
            assert phase=='ready'
            if active and arm=='credit_erased':
                cut=dict(register=1,before=e['registers'][1],after=0,trial=trial)
                e['registers'][1]=0
            credit_due=False
        pc_before=e['pc'];phase_before=phase;observation=None;feedback_read=None;observed_read=None;observed_store=None
        op0,a0,b0=program[pc_before]
        if op0==0:assert phase in ('cue','pre','post')
        if op0==6:assert phase=='act'
        if op0==19:
            index=e['registers'][b0%2]%len(e['memory'])
            if active and arm=='recall_disabled' and pc_before==3:index=0
            returned=0 if active and arm=='model_disabled' else e['memory'][index]
            observed_read=dict(pc=pc_before,index=index,source_value=e['memory'][index],returned=returned,active=int(active))
        if op0==20:
            index=e['registers'][a0%2]%len(e['memory'])
            observed_store=dict(pc=pc_before,index=index,before=e['memory'][index],attempted=e['registers'][b0%2],applied=int(not(active and arm=='update_frozen')))
        s['tick']+=1; e['turns']+=1
        event=dict(tick=s['tick'],actor=actor,before=digest(e),energy_before=e['energy'],input=[])
        if s['tick']%64==0:
            span=8 if s['tick']>=expansion_tick else 2
            for i in range(16):
                p=s['next_packet'];s['next_packet']+=1;s['offered']+=1
                cue=(i+s['tick']//64)%span; admitted=len(s['food'])<64
                if admitted: s['food'][str(p)]=cue;s['admitted']+=1
                else: s['rejected']+=1
                event['input'].append(dict(packet=p,cue=cue,energy=20,
                    outcome='admitted' if admitted else 'external_rejected'))
        if s['tick']==64:
            s['constructor_remaining']-=16;s['heat']+=16;event['release_energy']=16
        charge(e,1)
        if e['pending']:
            event['kind']='sampler_draw'; pending=e['pending'];stage=pending['stage'];pending['draws']+=1
            key=[seed,'capacity-sampler',e['lineage'],pending['session'],stage,pending['draws']]
            raw=int(digest(key)[:8],16)&(7 if stage=='gate' else 3)
            # Named, prospectively registered software witnesses only. The
            # default never trusts receipt-provided draws or host callbacks.
            if software_assistance=='gate7': raw=7 if stage=='gate' else 3
            elif software_assistance=='gate0-reject8': raw=0 if stage=='gate' else 3
            elif software_assistance=='gate0-reject1-then8':
                raw=0 if stage=='gate' else (3 if pending['allele_draws']==0 else 2)
            event['draw']=dict(stage=stage,value=raw,key=digest(key),ordinal=pending['draws'])
            allele=None;abort=False
            if stage=='gate':
                if raw==0: pending['stage']='allele'
                else: allele=e['code'][1][0]
            else:
                pending['allele_draws']+=1
                if raw<3: allele=(2,4,8)[raw]
                elif pending['allele_draws']==8: abort=True
            if allele is not None or abort:
                event['sampler_finished']=dict(proposed=allele,abort=int(abort),draws=pending['draws'])
                if abort: s['free']=sorted(s['free']+pending['units'])
                else: write(e,event,pending['units'],e['code'][1][0] if mode=='no_variation' else allele)
                e['pending']=None;e['pc']=(e['pc']+1)%(len(e['code'])//3)
        else:
            old=e['pc']; op,a,b=[v[0] for v in e['code'][3*old:3*old+3]]
            r=e['registers'];q=2 if mode=='inheritance_disabled' else len(e['memory']);n=len(e['code'])//3
            event.update(kind='ordinary',decoded=[op,a,b]);e['pc']=(old+1)%n
            if op==0:
                p=packet(e,True);resource_cue=0 if p is None else s['food'][str(p)]
                channel={'cue':'cue','pre':'pre','post':'post'}[phase]
                symbol=task_observation(seed,completed,channel,admission)
                e['cue']=symbol;r[a%2]=symbol;event['sense']=dict(packet=p,cue=symbol)
                observation=dict(channel=channel,value=symbol,resource_cue=resource_cue,packet=p)
                if phase=='cue':original_cue=symbol;phase='pre'
                elif phase=='pre':phase='act'
                else:phase='ready';credit_due=True
            elif op==1:
                value=e['feedback'] if phase=='ready' else 2
                r[a%2]=value;event['read_feedback']=value
                feedback_read=dict(available=int(phase=='ready'),value=value)
            elif op==2: r[a%2]=e['memory'][b%q]
            elif op==3: e['memory'][a%q]=r[b%2]
            elif op==4: r[a%2]=b%16
            elif op==5: r[a%2]^=r[b%2]
            elif op==6:
                p=packet(e);e['feedback']=2;event['penalty']=0
                if p is not None:
                    cue=s['food'].pop(str(p));target=(label_mask(seed,completed,admission)>>original_cue)&1
                    port=r[a%2]%2;e['feedback']=int(port==target)
                    if str(p) in s['leases']: del s['leases'][str(p)];e['lease']=None
                    event['attempt']=dict(packet=p,cue=cue,target=target,port=port,success=e['feedback'])
                    if e['feedback']:
                        gain=min(20,224-e['energy']);e['energy']+=gain;s['heat']+=20-gain;event['captured']=gain
                    else:
                        s['heat']+=20;penalty=min(4,e['energy']);charge(e,penalty);event['penalty']=penalty
                event['feedback']=e['feedback'];phase='post'
            elif op==7: e['pc']=b%n
            elif op==8:
                if r[a%2]==0: e['pc']=b%n
            elif op==10:
                if len(e['nursery'])==len(e['code']) or len(s['free'])<3 or e['energy']<3:
                    event['copy_refused']='full_or_material_or_energy'
                else:
                    units=s['free'][:3];del s['free'][:3]
                    if not e['nursery']:
                        e['copy_sessions']+=1;e['pending']=dict(stage='gate',draws=0,allele_draws=0,
                            session=e['copy_sessions'],units=units)
                        e['pc']=old;event['sampler_started']=duplicate(e['pending'])
                    else: write(e,event,units)
            elif op==12:
                if len(e['nursery'])!=len(e['code']) or len(s['entities'])>=max_population:
                    event['division_refused']='nursery_or_population'
                else:
                    state_count=e['nursery'][1]['value']+8
                    if len(s['free'])<state_count or e['energy']<state_count+114:
                        event['division_refused']='material_or_energy'
                    else:
                        units=s['free'][:state_count];del s['free'][:state_count]
                        identity=s['next_id'];s['next_id']+=1;e['children']+=1
                        child=newborn(identity,actor,e['generation']+1,
                            [[w['value'],w['unit']] for w in e['nursery']],units,e['lineage']+[e['children']])
                        e['energy']-=state_count+114;s['heat']+=state_count+2;s['entities'][str(identity)]=child
                        event['birth']=dict(child=duplicate(child),state_formation=units,state_energy=state_count,
                            startup_energy=112,release_energy=2,parent_energy_after_division=e['energy'],
                            write_ids=[w['write_id'] for w in e['nursery']])
                        e['nursery']=[];s['births']+=1
            elif op==19:
                r[a%2]=observed_read['returned']
            elif op==20:
                if observed_store['applied']:e['memory'][r[a%2]%q]=r[b%2]
            elif op==21: r[a%2]^=15
            # Opcode18 is an admitted ordinary no-op in this frozen law.
        if e['energy']==0 or e['turns']==2048:
            units=[v[1] for v in e['code']]+e['state_units']+[w['unit'] for w in e['nursery']]
            if e['pending']: units+=e['pending']['units']
            if e['lease'] is not None: del s['leases'][str(e['lease'])]
            s['heat']+=e['energy'];s['free']=sorted(s['free']+units);del s['entities'][str(actor)];s['deaths']+=1
            event['death']=dict(cause='energy' if e['energy']==0 else 'installed_age_law',released=units,dissipated=e['energy'])
        else: event['after']=duplicate(e)
        conserved();event['state_hash']=digest(s)
        charged+=1+event.get('penalty',0)+event.get('release_energy',0);assert charged<=1024
        completion=None
        if completed_edge(role,pc_before,event.get('after'),program):
            assert phase=='ready' and not credit_due
            completed+=1;phase='cue';original_cue=None
            completion=dict(completed=completed,entry=event['after']['pc'],energy=event['after']['energy'])
        expected_ledger=dict(tick=event['tick'],pc=pc_before,trial=trial,phase_before=phase_before,cut=cut,
            observation=observation,read=observed_read,store=observed_store,feedback_read=feedback_read,
            phase_after=phase,completion=completion,cost_after=charged)
        assert ledger[s['tick']-1]==expected_ledger,'Control ledger mismatch'
        assert event==receipt, 'Literal transition mismatch at dispatch '+str(s['tick'])
    assert s['tick']==horizon or not s['entities'] or completed==60 or charged+5+(16 if s['tick']+1==64 else 0)>1024,'Premature trace truncation'
    assert dict(s,events=events)==state, 'Final population mismatch'
    result=dict(verified=True,scientific_worlds=0,ticks=s['tick'],births=s['births'],deaths=s['deaths'],
                offered=s['offered'],admitted=s['admitted'],rejected=s['rejected'],heat=s['heat'],
                living_energy=sum(e['energy'] for e in s['entities'].values()),
                final_state_sha256=digest(s))
    result.update(completed=completed,charged_cost=charged)
    return result
