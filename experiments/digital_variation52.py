"""Post-verification lineage bookkeeping; never executes an organism policy."""
from experiments.digital_informative_exposure23_interpret import audit,h

PROGRAM=[[4,1,1],[6,0,0],[5,0,1],[10,0,0],[12,0,0],[7,0,1]]
SEEDS=tuple(range(52000,52064))
MODES=('faithful','mutating')

def words(code):
    assert code and all(type(cell) is list and len(cell)==2 and type(cell[0]) is int and 0<=cell[0]<32 for cell in code)
    return [cell[0] for cell in code]

def census(events,program):
    """Call ONLY after generic audit; synthetic tests exercise temporal joins."""
    ancestral=h(sum(program,[]))
    actors={0:dict(parent=None,generation=0,genotype=ancestral,current=ancestral,changed=False,food=0,remote=0,births=0)}
    edges=[];deaths=[];mutated_words=0;paid_words=0;previous=0
    for ev in events:
        assert type(ev['tick']) is int and ev['tick']>previous;previous=ev['tick']
        actor=ev['actor'];assert type(actor) is int and actor in actors
        person=actors[actor]
        if 'self_write' in ev and ev['self_write']['old']!=ev['self_write']['value']:person['changed']=True
        if 'after' in ev:person['current']=h(words(ev['after']['code']))
        for write in ev.get('writes',[]):
            assert type(write['mutated']) is bool
            paid_words+=1;mutated_words+=int(write['mutated'])
        attempt=ev.get('attempt')
        if attempt and attempt['success']:
            person['food']+=1
            if attempt['position']!=0 and not person['changed'] and person['current']==person['genotype']:person['remote']+=1
        if 'birth' in ev:
            child=ev['birth']['child'];identity=child['id']
            assert type(identity) is int and identity not in actors and child['parent']==actor and child['generation']==person['generation']+1
            genotype=h(words(child['code']));person['births']+=1
            # Parent remote success must precede this division; never fill it retroactively.
            eligible=(actor!=0 and person['genotype']!=ancestral and not person['changed'] and
                      person['current']==person['genotype']==genotype and person['remote']>0)
            actors[identity]=dict(parent=actor,generation=child['generation'],genotype=genotype,current=genotype,changed=False,food=0,remote=0,births=0)
            edges.append(dict(tick=ev['tick'],parent=actor,child=identity,parent_remote_before_birth=person['remote'],exact_program_transfer=person['current']==genotype,eligible_parent=eligible))
        if 'death' in ev:deaths.append(dict(tick=ev['tick'],actor=actor))
    for edge in edges:
        child=actors[edge['child']]
        edge['child_stable_remote_food']=child['remote']
        edge['inherited_remote_function_witness']=bool(edge['eligible_parent'] and child['remote']>0)
    return dict(actors=actors,edges=edges,deaths=deaths,paid_words=paid_words,mutated_words=mutated_words,
                birth_genotypes=len({v['genotype'] for v in actors.values()}),
                novel_resource_actors=sum(v['genotype']!=ancestral and v['remote']>0 for v in actors.values()),
                inherited_remote_function_witnesses=sum(e['inherited_remote_function_witness'] for e in edges),
                maximum_generation=max(v['generation'] for v in actors.values()))

def interpret(row):
    assert type(row['seed']) is int and row['seed'] in SEEDS and row['mode'] in MODES
    assert row['route']=='ancestor' and h(row['genesis_program'])==h(PROGRAM)
    checked=audit(row)
    lineage=census(row['final']['events'],PROGRAM)
    assert lineage['paid_words']==checked['paid_copy_words'] and lineage['mutated_words']==checked['mutations']
    assert len(lineage['edges'])==checked['births'] and len(lineage['deaths'])==checked['deaths']
    if row['mode']=='faithful':assert lineage['mutated_words']==0 and lineage['birth_genotypes']==1 and checked['remote_food']==0
    return dict(checked=checked,lineage=lineage,evolution=False,learning=False,stage_credit=False)
