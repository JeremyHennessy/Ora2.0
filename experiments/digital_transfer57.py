"""Assisted Transfer57 genesis and independent finite resource comparison."""
from experiments.digital_informative_exposure23_interpret import audit,body,clone,h
from experiments.digital_mobile54 import PROGRAM
from experiments.digital_transfer57_source import enroll

SEEDS=tuple(range(57000,57008))
ROSTER=((55020,1),(55020,4),(55025,5),(55009,3),(55000,2),(55018,1),(55029,2),(55008,4))
SOURCE_HASH='ee718c93d4ebdfb569f535c23febb626490cf99e533e7a08ab7c290261450cd3'
VERSION='DIGITAL-TRANSFER-57-assisted-v1'
ROUTE='transfer57'


def source_bank(summary):
    assert h(summary)==SOURCE_HASH and summary['verified'] and summary['assay_unopened']
    assert (summary['eligible'],summary['enrolled'])==(151,8)
    assert summary['roster']==enroll(summary['pool'])
    assert tuple((r['seed'],r['child']) for r in summary['roster'])==ROSTER
    return summary['roster']


def choice(arm,source,summary):
    bank=source_bank(summary)
    if arm=='withheld':
        assert source is None
        return clone(PROGRAM),None
    assert arm=='retained' and type(source) is tuple and len(source)==2
    assert all(type(v) is int for v in source) and source in ROSTER
    record=bank[ROSTER.index(source)];program=record['program']
    assert len(program)==9 and all(type(t) is list and len(t)==3 and all(type(v) is int and 0<=v<32 for v in t) for t in program)
    assert record['program_hash']==h(sum(program,[]))
    return clone(program),dict(seed=source[0],child=source[1],program_hash=record['program_hash'],source_row_hash=record['source_row_hash'])


def generate(seed,arm,source,summary):
    assert type(seed) is int and seed in SEEDS
    program,origin=choice(arm,source,summary)
    from experiments import digital_informative_exposure23 as substrate
    assert ROUTE not in substrate.PROGRAMS
    before=h(substrate.PROGRAMS)
    matches=[name for name,p in substrate.PROGRAMS.items() if p==program]
    assert len(matches)<=1
    route=matches[0] if matches else ROUTE
    if not matches:substrate.PROGRAMS[ROUTE]=clone(program)
    try:
        row=substrate.history(seed,route,'faithful')
        return dict(version=VERSION,arm=arm,source=origin,source_manifest_hash=SOURCE_HASH,history=row)
    finally:
        if not matches:del substrate.PROGRAMS[ROUTE]
        assert h(substrate.PROGRAMS)==before


def natural(v):
    assert type(v) is int and v>=0
    return v


def census(program,events):
    """Chronological ledgers only; full independent VM audit must precede use."""
    values=sum(program,[]);founder=body(0,None,0,[[v,i] for i,v in enumerate(values)],list(range(27,43)),0)
    def actor(state,tick):
        return dict(parent=state['parent'],generation=state['generation'],birth_tick=tick,birth_program=[c[0] for c in state['code']],
                    birth_body_hash=h(state),state=clone(state),alive=True,instructions=0,actions=0,moves=0,
                    food_by_site=[0]*4,attempts_by_site=[0]*4,opportunities_by_site=[0]*4,self_writes=[],
                    stable_site1_ticks=[],site1_after_selfwrite_ticks=[],births=0,copy_words=0,cap_loss=0,received=0,sent=0,halt_heat=0)
    actors={0:actor(founder,0)};food={i:0 if i<32 else 1+(i-32)//16 for i in range(64)}
    certificates={};used=set();edges=[];previous=0
    for event in events:
        tick=natural(event['tick']);assert tick>previous;previous=tick
        identity=natural(event['actor']);assert identity in actors and actors[identity]['alive']
        p=actors[identity];state=p['state'];assert event['before']==h(state)
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
            assert write['mutated'] is False
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
                              changed_birth_program=child_program!=p['birth_program']))
            actors[cid]=actor(child,tick)
        if opcode==17:p['halt_heat']+=energy;energy=0
        if 'death' in event:
            assert energy==0 and 'after' not in event;p['alive']=False;p['state']['energy']=0
        else:
            assert event['after']['energy']==energy;p['state']=clone(event['after'])
    for p in actors.values():
        assert 12+20*sum(p['food_by_site'])+p['received']-p['instructions']-p['copy_words']-30*p['births']-p['sent']-p['cap_loss']-p['halt_heat']==p['state']['energy']
        state=p.pop('state');p['endpoint_energy']=state['energy'];p['endpoint_body_hash']=h(state) if p['alive'] else None
    for edge in edges:edge['child_stable_site1_ticks']=actors[edge['child']]['stable_site1_ticks'][:]
    return dict(actors=actors,edges=edges,paid_words=len(certificates),food_by_site=[sum(p['food_by_site'][i] for p in actors.values()) for i in range(4)],
                stable_site1_food=sum(len(p['stable_site1_ticks']) for p in actors.values()),
                site1_after_selfwrite_food=sum(len(p['site1_after_selfwrite_ticks']) for p in actors.values()),
                energy_cap_loss=sum(p['cap_loss'] for p in actors.values()),
                descendant_food=sum(sum(p['food_by_site']) for i,p in actors.items() if i!=0),
                resource_then_birth=sum(e['parent']!=0 and e['parent_food_before_birth']>0 for e in edges),
                first_birth_tick=edges[0]['tick'] if edges else 0)


def ordinary_gate(s):
    keys=('seed','formation_cost','remote_food','births','paid_copy_words','descendant_food','resource_then_birth','first_birth_tick')
    if any(type(s.get(k)) is not int or s[k]<0 for k in keys):return False
    return s.get('arm')=='withheld' and s.get('mode')=='faithful' and s['seed'] in SEEDS and s['formation_cost']==43 and s['remote_food']>0 and s['births']>=2 and s['paid_copy_words']>=54 and s['descendant_food']>0 and s['resource_then_birth']>0 and s['first_birth_tick']==70


def interpret(envelope,summary):
    assert envelope['version']==VERSION and envelope['source_manifest_hash']==SOURCE_HASH
    origin=envelope['source'];source=None if origin is None else (origin['seed'],origin['child'])
    program,expected=choice(envelope['arm'],source,summary);assert origin==expected
    row=envelope['history'];assert type(row['seed']) is int and row['seed'] in SEEDS and row['mode']=='faithful' and row['genesis_program']==program
    checked=audit(row);lineage=census(program,row['final']['events'])
    assert (lineage['paid_words'],len(lineage['edges']),sum(not p['alive'] for p in lineage['actors'].values()))==(checked['paid_copy_words'],checked['births'],checked['deaths'])
    assert sum(lineage['food_by_site'])==checked['successful_food'] and sum(p['instructions'] for p in lineage['actors'].values())==checked['ticks']
    assert sum(p['endpoint_energy'] for p in lineage['actors'].values() if p['alive'])==checked['live_energy']
    assert checked['mutations']==0
    result=dict(checked,arm=envelope['arm'],source=expected,source_manifest_hash=SOURCE_HASH,site1_food=lineage['food_by_site'][1],
                stable_site1_food=lineage['stable_site1_food'],site1_after_selfwrite_food=lineage['site1_after_selfwrite_food'],
                descendant_food=lineage['descendant_food'],resource_then_birth=lineage['resource_then_birth'],first_birth_tick=lineage['first_birth_tick'],energy_cap_loss=lineage['energy_cap_loss'])
    result['ordinary_admitted']=ordinary_gate(result)
    return dict(summary=result,lineage=lineage,assisted_genesis=True,endogenous_inheritance_demonstrated=False,learning=False,evolution=False,stage_credit=False)


def compare(rows):
    """Only accepts all72 independent-referee summaries, not raw producer claims."""
    assert len(rows)==72;seen={};references={};retained={key:{} for key in ROSTER}
    for row in rows:
        s=row['summary'];assert s['verified'] is True and s['source_manifest_hash']==SOURCE_HASH and s['mode']=='faithful' and s['formation_cost']==43
        seed=s['seed'];assert type(seed) is int and seed in SEEDS
        for field in ('successful_food','site1_food'):natural(s[field])
        assert s['site1_food']<=s['successful_food']
        if s['arm']=='withheld':
            assert s['source'] is None and ordinary_gate(s);key=('withheld',seed);references[seed]=s
        else:
            assert s['arm']=='retained';source=s['source'];identity=(source['seed'],source['child'])
            assert all(type(v) is int for v in identity) and identity in ROSTER
            key=(identity,seed);retained[identity][seed]=s
        assert key not in seen;seen[key]=s
    assert set(references)==set(SEEDS) and all(set(v)==set(SEEDS) for v in retained.values())
    entries=[]
    for source,results in retained.items():
        pairs=[]
        for seed in SEEDS[::2]:
            food_delta=sum(results[s]['successful_food']-references[s]['successful_food'] for s in (seed,seed+1))
            site1_delta=sum(results[s]['site1_food']-references[s]['site1_food'] for s in (seed,seed+1))
            pairs.append(dict(context=seed//2,seeds=[seed,seed+1],food_delta=food_delta,site1_delta=site1_delta,qualified=food_delta>0 and site1_delta>0))
        entries.append(dict(source=list(source),pairs=pairs,provisional_assisted_resource_benefit=all(p['qualified'] for p in pairs)))
    return dict(entries=entries,unique_histories=72,shared_references=8,retained_histories=64,independent_context_pairs=4,
                eligible_sources=151,enrolled_sources=8,endogenous_inheritance_demonstrated=False,selection=False,evolution=False,learning=False,stage_credit=False)
