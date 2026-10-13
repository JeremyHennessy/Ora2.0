"""Firstborn63 full-history integration; generic independent VM audit is mandatory.

No producer import or World execution. Prepared tables establish software only;
ordinary/primary execution requires separately registered finite admission.
The mutation-aware chronological ledger derives from reviewed Transfer57 census,
whose frozen faithful-only contract remains unchanged.
"""
from experiments.digital_informative_exposure23_interpret import audit,body,clone,h
from experiments.digital_transfer57 import choice,ROSTER,SOURCE_HASH
from experiments.digital_firstborn63_kernel import paired_prefix,firstborn_window,literal_gain

VERSION='DIGITAL-FIRSTBORN-FIDELITY-63-v1'
PRIMARY=tuple(range(64000,64008))
UNSEEN=tuple(range(64200,64208))
SEEDS=PRIMARY+UNSEEN
MODES=('faithful','mutating')

def identity(envelope,manifest):
    assert set(envelope)=={'version','arm','source','source_manifest_hash','history'}
    assert envelope['version']==VERSION and envelope['source_manifest_hash']==SOURCE_HASH
    origin=envelope['source']
    if origin is None:source=None
    else:
        assert type(origin) is dict and set(origin)=={'seed','child','program_hash','source_row_hash'}
        assert type(origin['seed']) is int and type(origin['child']) is int
        source=(origin['seed'],origin['child'])
    program,expected=choice(envelope['arm'],source,manifest)
    assert origin==expected
    row=envelope['history']
    assert type(row['seed']) is int and row['seed'] in SEEDS
    assert row['mode'] in MODES and row['genesis_program']==program
    return program,expected

def natural(v):
    assert type(v) is int and v>=0
    return v


def census(program,events,seed,mode):
    """Chronological ledgers only; full independent VM audit must precede use."""
    assert type(seed) is int and seed>=0 and mode in MODES
    values=sum(program,[]);founder=body(0,None,0,[[v,i] for i,v in enumerate(values)],list(range(27,43)),0)
    def actor(state,tick):
        return dict(parent=state['parent'],generation=state['generation'],birth_tick=tick,birth_program=[c[0] for c in state['code']],
                    birth_body_hash=h(state),state=clone(state),alive=True,instructions=0,actions=0,moves=0,steps=[],mutated_words=0,
                    food_by_site=[0]*4,attempts_by_site=[0]*4,opportunities_by_site=[0]*4,self_writes=[],
                    stable_site1_ticks=[],site1_after_selfwrite_ticks=[],births=0,copy_words=0,cap_loss=0,received=0,sent=0,halt_heat=0)
    actors={0:actor(founder,0)};food={i:0 if i<32 else 1+(i-32)//16 for i in range(64)}
    certificates={};used=set();edges=[];previous=0
    for event in events:
        tick=natural(event['tick']);assert tick>previous;previous=tick
        identity=natural(event['actor']);assert identity in actors and actors[identity]['alive']
        p=actors[identity];state=p['state'];assert event['before']==h(state)
        before_body=clone(state);available=[packet for packet,site in food.items() if site==state['pos'] and (packet not in range(16,32) or tick>=64)]
        pos=state['pos'];before_energy=state['energy'];code=clone(state['code'])
        opcode=event['decoded'][0];p['instructions']+=1;p['actions']+=int(opcode==6);p['moves']+=int(opcode==13)
        if any(site==pos and (packet not in range(16,32) or tick>=64) for packet,site in food.items()):p['opportunities_by_site'][pos]+=1
        energy=before_energy-1
        if 'self_write' in event:p['self_writes'].append(tick)
        attempt=event.get('attempt')
        if attempt is not None:
            assert opcode==6 and attempt['position']==pos and food[attempt['packet']]==pos
            p['attempts_by_site'][pos]+=1
            if attempt['success']:
                del food[attempt['packet']];p['food_by_site'][pos]+=1
                loss=max(0,energy+20-64);p['cap_loss']+=loss;energy+=20-loss
                if pos==1:
                    if p['self_writes']:p['site1_after_selfwrite_ticks'].append(tick)
                    elif [v[0] for v in code]==p['birth_program']:p['stable_site1_ticks'].append(tick)
        for write in event.get('writes',[]):
            wid=natural(write['write_id']);assert wid not in certificates
            assert write['tick']==tick and [write['source_value'],write['source_unit']]==code[write['index']]
            assert type(write['mutated']) is bool
            draw=int(h([seed,'mutation',wid])[:16],16)
            mutated=mode=='mutating' and draw%100<8
            value=(write['source_value']+1+(draw//100)%31)%32 if mutated else write['source_value']
            assert write['mutated']==mutated and write['value']==value
            p['mutated_words']+=int(mutated)
            certificates[wid]=(identity,clone(write));p['copy_words']+=1;energy-=1
        if 'message' in event:
            message=event['message'];recipient=actors[message['recipient']]
            assert recipient['alive'];recipient['state']['inbox']=message['value']
        if 'transfer' in event:
            recipient=actors[event['transfer']];assert recipient['alive']
            recipient['state']['energy']+=1;recipient['received']+=1;p['sent']+=1;energy-=1
        if 'birth' in event:
            birth=event['birth'];child=birth['child'];cid=natural(child['id'])
            assert cid not in actors and child['parent']==identity and child['generation']==p['generation']+1
            assert birth['startup_energy']==child['energy']==12
            ids=birth['write_ids'];assert len(ids)==len(child['code'])==27 and len(set(ids))==27 and not used.intersection(ids)
            for index,(wid,cell) in enumerate(zip(ids,child['code'])):
                assert wid in certificates;owner,write=certificates[wid]
                assert owner==identity and write['tick']<tick and write['index']==index and [write['value'],write['unit']]==cell
            used.update(ids);p['births']+=1;energy-=30
            child_program=[v[0] for v in child['code']]
            edges.append(dict(tick=tick,parent=identity,child=cid,write_ids=ids[:],exact_program_transfer=[v[0] for v in code]==child_program,
                              stable_parent_site1_before_birth=p['stable_site1_ticks'][:],parent_food_before_birth=sum(p['food_by_site']),
                              changed_birth_program=child_program!=p['birth_program'],
                              mutated_words=sum(certificates[wid][1]['mutated'] for wid in ids),
                              startup_energy=12,state_words=len(child['state_units']),release_energy=birth['release_energy']))
            assert len(child['state_units'])==16 and birth['release_energy']==2
            assert child==body(cid,identity,p['generation']+1,clone(child['code']),child['state_units'][:],pos)
            actors[cid]=actor(child,tick)
        if opcode==17:p['halt_heat']+=energy;energy=0
        if 'death' in event:
            assert energy==0 and 'after' not in event;p['alive']=False;p['state']['energy']=0
        else:
            assert event['after']['energy']==energy;p['state']=clone(event['after'])
        p['steps'].append(dict(tick=tick,opcode=opcode,position=pos,available_packets=sorted(available),
                               before=event['before'],program_before=h([v[0] for v in before_body['code']]),
                               after=h(event['after']) if 'after' in event else None,
                               program_after=h([v[0] for v in event['after']['code']]) if 'after' in event else None,
                               memory_after=h(event['after']['memory']) if 'after' in event else None,
                               registers_after=h(event['after']['registers']) if 'after' in event else None,
                               pc_after=event['after']['pc'] if 'after' in event else None,
                               inbox_after=event['after']['inbox'] if 'after' in event else None,
                               attempt=clone(attempt),writes=clone(event.get('writes',[])),death='death' in event))
    for p in actors.values():
        assert 12+20*sum(p['food_by_site'])+p['received']-p['instructions']-p['copy_words']-30*p['births']-p['sent']-p['cap_loss']-p['halt_heat']==p['state']['energy']
        state=p.pop('state');p['endpoint_energy']=state['energy'];p['endpoint_body_hash']=h(state) if p['alive'] else None
    for edge in edges:edge['child_stable_site1_ticks']=actors[edge['child']]['stable_site1_ticks'][:]
    return dict(actors=actors,edges=edges,paid_words=len(certificates),mutations=sum(p['mutated_words'] for p in actors.values()),food_by_site=[sum(p['food_by_site'][i] for p in actors.values()) for i in range(4)],
                stable_site1_food=sum(len(p['stable_site1_ticks']) for p in actors.values()),
                site1_after_selfwrite_food=sum(len(p['site1_after_selfwrite_ticks']) for p in actors.values()),
                energy_cap_loss=sum(p['cap_loss'] for p in actors.values()),
                descendant_food=sum(sum(p['food_by_site']) for i,p in actors.items() if i!=0),
                resource_then_birth=sum(e['parent']!=0 and e['parent_food_before_birth']>0 for e in edges),
                first_birth_tick=edges[0]['tick'] if edges else 0)


def interpret(envelope,manifest):
    program,origin=identity(envelope,manifest)
    row=envelope['history']
    checked=audit(row)  # Full independent VM law replay BEFORE any projections.
    assert checked['verified'] is True
    ledger=census(program,row['final']['events'],row['seed'],row['mode'])
    assert (ledger['paid_words'],ledger['mutations'],len(ledger['edges']),sum(not p['alive'] for p in ledger['actors'].values()))==(checked['paid_copy_words'],checked['mutations'],checked['births'],checked['deaths'])
    assert sum(ledger['food_by_site'])==checked['successful_food']
    assert sum(p['instructions'] for p in ledger['actors'].values())==checked['ticks']
    assert sum(p['endpoint_energy'] for p in ledger['actors'].values() if p['alive'])==checked['live_energy']
    window=firstborn_window(row['final']['events'],checked['ticks'],not row['final']['entities'])
    if window['birth_tick'] is not None:
        assert {k:window[k] for k in ('F','G')}==literal_gain(row['final']['events'],window['birth_tick'])
        # Literal minimum: at most3 paid words/COPY,27 code words per birth,
        # empty nurseries at first division; nine COPYs plus DIV require10 ticks.
        assert all(len(e.get('writes',[]))<=3 for e in row['final']['events'])
        edge=ledger['edges'][0];assert len(edge['write_ids'])==27 and edge['state_words']==16
        window['opportunities']=[s for s in ledger['actors'][1]['steps'] if edge['tick']<s['tick']<=edge['tick']+8]
    summary=dict(checked,arm=envelope['arm'],source=origin,source_manifest_hash=SOURCE_HASH,
                 descendant_food=ledger['descendant_food'],resource_then_birth=ledger['resource_then_birth'],
                 first_birth_tick=ledger['first_birth_tick'])
    return dict(summary=summary,lineage=ledger,window=window,raw_hash=row['hash'],
                learning=False,evolution=False,stage_credit=False)

def pair(left,right):
    a=left['summary'];b=right['summary']
    assert a['mode']=='faithful' and b['mode']=='mutating'
    for key in ('seed','arm','source','source_manifest_hash','formation_cost'):
        assert a[key]==b[key]
    assert a['verified'] is b['verified'] is True and a['formation_cost']==43
    prefix=paired_prefix(left['events'],right['events'])
    assert prefix['birth_tick']==left['window']['birth_tick']==right['window']['birth_tick']
    return dict(seed=a['seed'],arm=a['arm'],source=a['source'],changed=prefix['changed'],
                complete=left['window']['complete'] and right['window']['complete'],
                faithful=clone(left['window']),mutating=clone(right['window']),
                F=left['window']['F']-right['window']['F'],G=left['window']['G']-right['window']['G'])

def paired(envelopes,manifest):
    assert type(envelopes) is list and len(envelopes)==2
    results=[]
    for envelope in envelopes:
        result=interpret(envelope,manifest)
        result['events']=envelope['history']['final']['events']
        results.append(result)
    result=pair(*results)
    return dict(pair=result,histories=[{k:v for k,v in r.items() if k!='events'} for r in results])

def ordinary_gate(result):
    p=result['pair'];histories=result['histories'];assert len(histories)==2
    assert p['arm']=='withheld' and p['source'] is None and type(p['seed']) is int and p['seed'] in SEEDS
    a,b=[r['summary'] for r in histories]
    assert a['mode']=='faithful' and b['mode']=='mutating'
    for s in (a,b):
        assert s['verified'] is True and s['source'] is None and s['arm']=='withheld' and s['seed']==p['seed']
        assert s['source_manifest_hash']==SOURCE_HASH and s['formation_cost']==43
        for key in ('formation_cost','first_birth_tick','births','paid_copy_words','remote_food','descendant_food','resource_then_birth'):
            natural(s[key])
    return p['complete'] and a['first_birth_tick']==b['first_birth_tick']==70 and a['births']>=2 and a['paid_copy_words']>=54 and a['remote_food']>0 and a['descendant_food']>0 and a['resource_then_birth']>0 and p['faithful']['F']>=1

def ordinary_admission(results):
    assert type(results) is list and len(results)==16
    seen=set();admitted=True
    for result in results:
        seed=result['pair']['seed'];assert type(seed) is int and seed in SEEDS and seed not in seen
        seen.add(seed);admitted=ordinary_gate(result) and admitted
    assert seen==set(SEEDS)
    return admitted

def cohort(pairs):
    """Whole144 pairs/288 experimental roles; original/restored replay is separate.

    No source/context exclusions, pooled rescue or baseline subtraction. Referee
    pairs must be derived from independently audited complete raw histories.
    """
    assert type(pairs) is list and len(pairs)==144
    seen={};references={};sources={r:{} for r in ROSTER}
    for p in pairs:
        seed=p['seed'];assert type(seed) is int and seed in SEEDS
        for k in ('F','G'):assert type(p[k]) is int
        for k in ('complete','changed'):assert type(p[k]) is bool
        for window in (p['faithful'],p['mutating']):
            assert type(window['F']) is int and window['F']>=0 and type(window['G']) is int
        assert p['F']==p['faithful']['F']-p['mutating']['F'] and p['G']==p['faithful']['G']-p['mutating']['G']
        if p['arm']=='withheld':
            assert p['source'] is None;role=None;references[seed]=p
        else:
            assert p['arm']=='retained';o=p['source'];assert type(o['seed']) is int and type(o['child']) is int
            role=(o['seed'],o['child']);assert role in ROSTER;sources[role][seed]=p
        key=(role,seed);assert key not in seen;seen[key]=p
    assert set(references)==set(SEEDS) and all(set(v)==set(SEEDS) for v in sources.values())
    contexts=[]
    for stratum,seeds in [('primary',PRIMARY),('unseen',UNSEEN)]:
        for seed in seeds[::2]:
            cells=[sources[r][s] for r in ROSTER for s in (seed,seed+1)]
            F=sum(p['F'] for p in cells);G=sum(p['G'] for p in cells)
            complete=all(p['complete'] for p in cells)
            changed=sum(p['changed'] for p in cells)
            contexts.append(dict(stratum=stratum,seeds=[seed,seed+1],F=F,G=G,complete=complete,
                                 changed_firstborns=changed,underexposed=changed==0,
                                 qualified=complete and changed>0 and F>0 and G>0))
    all_complete=all(p['complete'] for p in pairs)
    return dict(contexts=contexts,baseline=[references[s] for s in SEEDS],pairs=clone(pairs),
                unique_histories=288,complete=all_complete,
                causal_early_firstborn_fidelity_benefit=all_complete and all(c['qualified'] for c in contexts),
                learning=False,evolution=False,selection=False,stage_credit=False)
