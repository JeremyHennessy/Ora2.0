"""Mobile55 paid lineage observations; supplied policy is not learning."""
from experiments.digital_informative_exposure23_interpret import audit, h
from experiments.digital_mobile54 import PROGRAM

SEEDS=tuple(range(55000,55032))
MODES=('faithful','mutating')
ROUTE='mobile55'


def natural(value):
    assert type(value) is int and value>=0
    return value


def words(code):
    assert type(code) is list and len(code)==27
    assert all(type(cell) is list and len(cell)==2 and type(cell[0]) is int and 0<=cell[0]<32 and type(cell[1]) is int and cell[1]>=0 for cell in code)
    return tuple(cell[0] for cell in code)


def generate(seed,mode):
    assert type(seed) is int and seed in SEEDS and mode in MODES
    from experiments import digital_informative_exposure23 as substrate
    assert ROUTE not in substrate.PROGRAMS
    prior=h(substrate.PROGRAMS)
    substrate.PROGRAMS[ROUTE]=[triple[:] for triple in PROGRAM]
    try:return substrate.history(seed,ROUTE,mode)
    finally:
        del substrate.PROGRAMS[ROUTE]
        assert h(substrate.PROGRAMS)==prior


def census(events):
    """Requires full generic audit first; prepared fixtures test joins only."""
    ancestral=tuple(sum(PROGRAM,[]))
    def person(parent,generation,code):
        return dict(parent=parent,generation=generation,birth_words=words(code),current_words=words(code),current_code=[cell[:] for cell in code],energy=12,
                    genotype=h(list(words(code))),self_written=False,alive=True,instructions=0,actions=0,moves=0,
                    food_by_site=[0]*4,attempts_by_site=[0]*4,site1_success_ticks=[],births=0)
    actors={0:person(None,0,[[v,i] for i,v in enumerate(ancestral)])}
    edges=[];deaths=[];certificates={};consumed=set();previous=0;cap_loss=0;refusals={}
    for event in events:
        tick=natural(event['tick']);assert tick>previous;previous=tick
        actor=natural(event['actor']);assert actor in actors and actors[actor]['alive']
        p=actors[actor];before_energy=p['energy'];p['instructions']+=1
        decoded=event['decoded'];assert type(decoded) is list and len(decoded)==3
        assert all(type(v) is int and 0<=v<32 for v in decoded)
        p['actions']+=int(decoded[0]==6);p['moves']+=int(decoded[0]==13)
        if 'self_write' in event:p['self_written']=True
        if 'after' in event:
            p['current_words']=words(event['after']['code']);p['current_code']=[cell[:] for cell in event['after']['code']]
            if 'energy' in event['after']:p['energy']=natural(event['after']['energy'])
        for write in event.get('writes',[]):
            identity=natural(write['write_id']);assert identity not in certificates
            assert natural(write['tick'])==tick and natural(write['index'])<27
            assert type(write['value']) is int and 0<=write['value']<32
            assert type(write['source_value']) is int and 0<=write['source_value']<32
            assert type(write['mutated']) is bool and write['mutated']==(write['value']!=write['source_value'])
            natural(write['unit']);natural(write['source_unit'])
            assert [write['source_value'],write['source_unit']]==p['current_code'][write['index']]
            certificates[identity]=dict(write,actor=actor)
        attempt=event.get('attempt')
        if attempt is not None:
            site=natural(attempt['position']);assert site<4 and decoded[0]==6
            assert type(attempt['success']) is int and attempt['success'] in (0,1)
            p['attempts_by_site'][site]+=1
            if attempt['success']:
                p['food_by_site'][site]+=1
                cap_loss+=max(0,before_energy-1+20-64)
                if actor!=0 and p['birth_words']!=ancestral and not p['self_written'] and p['current_words']==p['birth_words'] and site==1:
                    p['site1_success_ticks'].append(tick)
        if 'transfer' in event:
            recipient=natural(event['transfer']);assert recipient in actors and actors[recipient]['alive']
            actors[recipient]['energy']+=1
        if event.get('outcome') in ('copy_refused','division_refused'):
            outcome=event['outcome'];refusals[outcome]=refusals.get(outcome,0)+1
        if 'birth' in event:
            birth=event['birth'];child=birth['child'];identity=natural(child['id'])
            assert identity not in actors and natural(child['parent'])==actor
            generation=natural(child['generation']);assert generation==p['generation']+1
            child_words=words(child['code']);write_ids=birth['write_ids']
            assert type(write_ids) is list and len(write_ids)==27
            assert all(type(v) is int and v>=0 for v in write_ids) and len(set(write_ids))==27
            assert not consumed.intersection(write_ids)
            for index,(certificate_id,cell) in enumerate(zip(write_ids,child['code'])):
                assert certificate_id in certificates
                cert=certificates[certificate_id]
                assert cert['actor']==actor and cert['tick']<tick and cert['index']==index
                assert [cert['value'],cert['unit']]==cell
            assert type(birth['startup_energy']) is int and birth['startup_energy']==12
            assert type(child['energy']) is int and child['energy']==12
            consumed.update(write_ids);p['births']+=1
            eligible=(actor!=0 and p['birth_words']!=ancestral and not p['self_written'] and
                      p['current_words']==p['birth_words']==child_words and bool(p['site1_success_ticks']))
            actors[identity]=person(actor,generation,child['code'])
            edges.append(dict(tick=tick,parent=actor,child=identity,write_ids=write_ids[:],
                              child_program=list(child_words),parent_site1_before_birth=p['site1_success_ticks'][:],
                              parent_food_before_birth=sum(p['food_by_site']),eligible_parent=eligible,
                              exact_program_transfer=p['current_words']==child_words))
        if 'death' in event:
            p['alive']=False;deaths.append(dict(tick=tick,actor=actor))
    for edge in edges:
        edge['child_site1_success_ticks']=actors[edge['child']]['site1_success_ticks'][:]
        edge['transmitted_function_association']=bool(edge['eligible_parent'] and edge['child_site1_success_ticks'])
    return dict(actors=actors,edges=edges,deaths=deaths,energy_cap_loss=cap_loss,refusals=refusals,paid_words=len(certificates),
                mutated_words=sum(c['mutated'] for c in certificates.values()),
                transmitted_mutated_words=sum(certificates[i]['mutated'] for i in consumed),
                untransmitted_mutated_words=sum(c['mutated'] for i,c in certificates.items() if i not in consumed),
                birth_genotypes=len({p['genotype'] for p in actors.values()}),
                novel_site1_actors=sum(bool(p['site1_success_ticks']) for p in actors.values()),
                transmitted_function_associations=sum(e['transmitted_function_association'] for e in edges),
                maximum_generation=max(p['generation'] for p in actors.values()))


def ordinary_gate(summary):
    counts=('seed','formation_cost','remote_food','births','paid_copy_words','descendant_food','resource_then_birth','first_birth_tick')
    if any(type(summary.get(k)) is not int or summary[k]<0 for k in counts):return False
    return (summary.get('mode')=='faithful' and summary['seed'] in SEEDS and summary['formation_cost']==43 and
            summary['remote_food']>0 and summary['births']>=2 and summary['paid_copy_words']>=54 and
            summary['descendant_food']>0 and summary['resource_then_birth']>0 and summary['first_birth_tick']==70)


def interpret(row):
    assert type(row['seed']) is int and row['seed'] in SEEDS and row['mode'] in MODES
    assert row['route']==ROUTE and row['genesis_program']==PROGRAM
    checked=audit(row);lineage=census(row['final']['events'])
    assert (lineage['paid_words'],lineage['mutated_words'],len(lineage['edges']),len(lineage['deaths']))==(checked['paid_copy_words'],checked['mutations'],checked['births'],checked['deaths'])
    assert sum(sum(p['food_by_site']) for p in lineage['actors'].values())==checked['successful_food']
    assert sum(p['instructions'] for p in lineage['actors'].values())==checked['ticks']
    assert sum(p['energy'] for p in lineage['actors'].values() if p['alive'])==checked['live_energy']
    summary=dict(checked,descendant_food=sum(sum(p['food_by_site']) for i,p in lineage['actors'].items() if i!=0),
                 resource_then_birth=sum(e['parent']!=0 and e['parent_food_before_birth']>0 for e in lineage['edges']),
                 first_birth_tick=lineage['edges'][0]['tick'] if lineage['edges'] else 0)
    summary['ordinary_admitted']=ordinary_gate(summary)
    if row['mode']=='faithful':
        assert lineage['mutated_words']==0 and lineage['birth_genotypes']==1 and lineage['novel_site1_actors']==0
    return dict(summary=summary,lineage=lineage,learning=False,evolution=False,causal_inheritance_benefit=False,stage_credit=False)


def replicated_contexts(observations):
    """Orientation duplicates never count as independent contexts."""
    seen=set();contexts=set()
    for seed,mode,count in observations:
        assert type(seed) is int and seed in SEEDS and mode in MODES
        natural(count);assert (seed,mode) not in seen;seen.add((seed,mode))
        if mode=='mutating' and count>0:contexts.add(seed//2)
    return dict(context_pairs=sorted(contexts),replicated_association=len(contexts)>=2,
                causal_inheritance_benefit=False,evolution=False,learning=False,stage_credit=False)
