"""Independent literal fresh-label/control replay; unchanged paid operations.

The caller supplies the pinned genesis programme and horizon. Event annotations,
post-states and hashes are evidence to compare, never transition inputs.
"""
import hashlib
import json


def duplicate(value):
    return json.loads(json.dumps(value))


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':')).encode()).hexdigest()



# Independently specified compact fixed sources; no producer/source imports.
REFERENCE_PROGRAMMES = (
 [[7,2,1],[4,0,0],[6,0,0],[7,0,1]],
 [[7,2,1],[4,0,1],[6,0,0],[7,0,1]],
 [[7,2,1],[0,0,0],[6,0,0],[7,0,1]],
 [[7,2,1],[0,0,0],[21,0,0],[6,0,0],[7,0,1]],
 [[7,2,1],[4,0,0],[6,0,0],[21,0,0],[7,0,2]],
 [[7,2,1],[6,0,0],[1,1,0],[8,1,5],[7,0,1],[21,0,0],[7,0,1]])

def label_mask(seed, packet, admission=None):
    assert type(seed) is int and type(packet) is int and packet>=0
    phase=int(packet>=48)
    if seed in range(2100380,2100384):
        return ((0,255,90,165),(0,255,165,90))[phase][seed-2100380]
    assert admission=='CREDITED-FALLBACK87-v2'
    bank=tuple(range(1009700,1009708)) if seed in range(1009700,1009708) else tuple(range(1009900,1009908))
    assert seed in bank
    offset=bank.index(seed)
    return (0,255)[offset] if offset<2 else int(digest(['CREDITED-FALLBACK87-LABELS-v1',seed,phase])[:2],16)


def boundary_before(entity, pending, completed, initial_entry, control):
    if pending is None:
        return None
    previous, actual = pending
    assert entity['pc'] == actual
    assert (previous, actual) in ((4,6),(5,1),(11,6),(15,1),(15,16),(19,6),(20,16))
    active = int(completed >= 48)
    projected = actual
    if active and control == 'history_disabled':
        projected = initial_entry
    elif active and control == 'fallback_misbound' and actual in (1,16):
        projected = 16 if actual == 1 else 1
    entity['pc'] = projected
    return dict(previous_pc=previous, actual_entry=actual, projected_entry=projected,
                completed=completed, active=active)


def model_value(entity, pc, completed, control):
    assert pc in (7,12)
    memory = entity['memory']
    index = entity['registers'][1]
    address = index % len(memory)
    origin = address
    active = int(completed >= 48)
    if active and control in ('model_erased','history_disabled'):
        origin = None
    elif active and control == 'model_misbound':
        origin = (address + len(memory)//2) % len(memory)
    value = 0 if origin is None else memory[origin]
    return dict(pc=pc,index=index,address=address,source_address=origin,
                truthful_cell=memory[address],value=value,active=active)


def boundary_after(pc, event, completed):
    after = event.get('after')
    if after is None or (pc, after['pc']) not in ((4,6),(5,1),(11,6),(15,1),(15,16),(19,6),(20,16)):
        return completed, None, None
    completed += 1
    return completed, (pc,after['pc']), dict(completed=completed,previous_pc=pc,
        entry=after['pc'],energy=after['energy'])


def audit(state, *, seed, mode, max_population, expansion_tick, program, horizon,
          software_assistance=None, control=None, ledger=None, reference=False, admission=None):
    assert type(seed) is int and (seed in range(2100380,2100384) or
        admission=='CREDITED-FALLBACK87-v2' and seed in tuple(range(1009700,1009708))+tuple(range(1009900,1009908)))
    assert type(reference) is bool
    assert software_assistance is None
    assert mode=='no_variation' and max_population==1 and expansion_tick==0
    assert horizon==1024
    assert mode in ('variation', 'no_variation', 'inheritance_disabled')
    assert type(max_population) is int and max_population in (1, 8)
    assert type(expansion_tick) is int and expansion_tick in (0, 1536)
    assert type(horizon) is int and 0 <= horizon <= 16384
    assert software_assistance is None or type(software_assistance) is str and software_assistance in (
        'gate0-reject8','gate0-reject1-then8','gate7')
    assert type(program) is list and 1 <= len(program) <= 32
    assert all(type(t) is list and len(t) == 3 and t[0] in (0,1,2,3,4,5,6,7,8,10,12,18,19,20,21)
               and all(type(v) is int and 0 <= v < 32 for v in t) for t in program)
    assert program[0][0] == 7 and program[0][1] in (2,4,8) and program[0][2] < len(program)
    # Exclude Python bool/int equivalence and all non-contract scalar types.
    def typed(value):
        if type(value) is dict:
            assert all(type(k) is str for k in value)
            for v in value.values(): typed(v)
        elif type(value) is list:
            for v in value: typed(v)
        else: assert value is None or type(value) in (int,str)
    typed(state)
    assert control is None or type(control) is str and control in (
        'intact','model_erased','model_misbound','fallback_misbound','history_disabled')
    completed=0; pending_boundary=None
    if control is None:
        assert reference and type(ledger) is list and len(ledger)==len(state['events'])
        assert program in REFERENCE_PROGRAMMES
        typed(ledger)
    else:
        assert mode=='no_variation' and max_population==1 and expansion_tick==0
        assert software_assistance is None and horizon==1024
        q=program[0][1]; initial_entry=program[0][2]
        assert initial_entry in (1,6,16)
        assert program==[
            [7,q,initial_entry],[4,0,0],[6,0,0],[1,0,0],[8,0,6],[7,0,1],
            [0,1,0],[19,0,1],[6,0,0],[1,0,0],[8,0,12],[7,0,6],
            [19,0,1],[21,0,0],[20,1,0],[8,0,1],
            [4,0,1],[6,0,0],[1,0,0],[8,0,6],[7,0,16]]
        assert type(ledger) is list and len(ledger)==len(state['events'])
        typed(ledger)

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

    events=state['events']; assert type(events) is list and len(events)<=horizon
    conserved()
    for receipt in events:
        assert s['entities'] and s['tick']<horizon
        ids=sorted(int(i) for i in s['entities'])
        actor=next((i for i in ids if i>s['last']),ids[0]); s['last']=actor
        e=s['entities'][str(actor)]
        if control is not None or reference:
            assert completed<60
            completed_before=completed
            entry=None if reference else boundary_before(e,pending_boundary,completed,initial_entry,control)
            pending_boundary=None
            pc_before=e['pc']
            observed_read=model_value(e,pc_before,completed,control) if not reference and pc_before in (7,12) else None
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
                p=packet(e,True);e['cue']=0 if p is None else s['food'][str(p)];r[a%2]=e['cue']
                event['sense']=dict(packet=p,cue=e['cue'])
            elif op==1: r[a%2]=e['feedback'];event['read_feedback']=e['feedback']
            elif op==2: r[a%2]=e['memory'][b%q]
            elif op==3: e['memory'][a%q]=r[b%2]
            elif op==4: r[a%2]=b%16
            elif op==5: r[a%2]^=r[b%2]
            elif op==6:
                p=packet(e);e['feedback']=2;event['penalty']=0
                if p is not None:
                    cue=s['food'].pop(str(p));target=(label_mask(seed,p,admission)>>cue)&1
                    port=r[a%2]%2;e['feedback']=int(port==target)
                    if str(p) in s['leases']: del s['leases'][str(p)];e['lease']=None
                    event['attempt']=dict(packet=p,cue=cue,target=target,port=port,success=e['feedback'])
                    if e['feedback']:
                        gain=min(20,224-e['energy']);e['energy']+=gain;s['heat']+=20-gain;event['captured']=gain
                    else:
                        s['heat']+=20;penalty=min(4,e['energy']);charge(e,penalty);event['penalty']=penalty
                event['feedback']=e['feedback']
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
                r[a%2]=e['memory'][r[b%2]%q] if control is None else observed_read['value']
            elif op==20: e['memory'][r[a%2]%q]=r[b%2]
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
        if control is not None or reference:
            if reference:
                after=event.get('after');completion=None;pending_boundary=None
                finish=2 if program==REFERENCE_PROGRAMMES[4] else 1
                if after is not None and pc_before!=0 and op==7 and after['pc']==finish:
                    completed+=1
                    completion=dict(completed=completed,previous_pc=pc_before,entry=finish,energy=after['energy'])
            else:
                completed,pending_boundary,completion=boundary_after(pc_before,event,completed)
            expected_ledger=dict(tick=event['tick'],dispatch_pc=pc_before,
                completed_before=completed_before,entry=entry,read=observed_read,completion=completion)
            assert ledger[s['tick']-1]==expected_ledger, 'Control ledger mismatch'
        assert event==receipt, 'Literal transition mismatch at dispatch '+str(s['tick'])
    assert s['tick']==horizon or not s['entities'] or ((control is not None or reference) and completed==60), 'Premature trace truncation'
    assert dict(s,events=events)==state, 'Final population mismatch'
    result=dict(verified=True,scientific_worlds=0,ticks=s['tick'],births=s['births'],deaths=s['deaths'],
                offered=s['offered'],admitted=s['admitted'],rejected=s['rejected'],heat=s['heat'],
                living_energy=sum(e['energy'] for e in s['entities'].values()),
                final_state_sha256=digest(s))
    if software_assistance is not None: result['software_assistance']=software_assistance
    return result
