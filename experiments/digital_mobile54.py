"""Disclosed fixed mobile reproductive ancestor; unchanged Exposure23 laws."""
from experiments.digital_informative_exposure23_interpret import audit,h

PROGRAM=[[4,1,1],[6,0,0],[5,0,1],[6,0,0],[10,0,0],[12,0,0],[13,1,0],[13,1,0],[7,0,1]]
SEEDS=(54000,54001)
MODES=('faithful','copy_disabled')
ROUTE='mobile54'


def budget():
    words=len(PROGRAM)*3
    return dict(program_words=words,state_words=16,formation=words+16,
                constructor_remaining=128-words-16,constructor_after_release=128-words-32,
                free_material=512-words-16,copy_instructions=words//3,
                paid_copy_extra_energy=words,copy_base_energy=words//3,
                division_extra_energy=30,division_heat=18,startup_transfer=12,
                minimum_birth_heat=words+words//3+1+18,
                cold_start_energy=12,cold_first_cycle_base=9,cold_first_cycle_extra=3,
                cold_first_cycle_minimum_intake=20,cold_first_cycle_end=20,
                ordinary_cycle_base=8,ordinary_copy_cycle_extra=3,
                organism_accessible_energy=12+48*20,reachable_food=48,
                minimum_heat_birth_ceiling=(12+48*20)//(words+words//3+1+18),
                first_division_tick=70,unvisited_stock_energy=16*20)


def generate(seed,mode):
    assert type(seed) is int and seed in SEEDS and mode in MODES
    # A disclosed program registry entry in this isolated process, not a VM/law edit.
    from experiments import digital_informative_exposure23 as substrate
    assert ROUTE not in substrate.PROGRAMS
    prior=h(substrate.PROGRAMS)
    substrate.PROGRAMS[ROUTE]=[triple[:] for triple in PROGRAM]
    try:return substrate.history(seed,ROUTE,mode)
    finally:
        del substrate.PROGRAMS[ROUTE]
        assert h(substrate.PROGRAMS)==prior


def gate(s):
    keys=('seed','births','descendant_food','resource_then_birth','paid_copy_words','first_birth_tick','remote_food','formation_cost')
    if any(type(s.get(k)) is not int or s[k]<0 for k in keys):return False
    if s['seed'] not in SEEDS or s['formation_cost']!=43:return False
    if s.get('mode')=='copy_disabled':return s['births']==s['paid_copy_words']==s['first_birth_tick']==0 and s['remote_food']>0
    if s.get('mode')!='faithful':return False
    return s['births']>=2 and s['descendant_food']>0 and s['resource_then_birth']>0 and s['paid_copy_words']>=54 and s['first_birth_tick']==70 and s['remote_food']>0


def interpret(row):
    assert type(row['seed']) is int and row['seed'] in SEEDS and row['mode'] in MODES
    assert row['route']==ROUTE and h(row['genesis_program'])==h(PROGRAM)
    checked=audit(row)
    energy={0:12};food={};remote={};births=[];deaths=[];overflow=0;actions=[]
    for event in row['final']['events']:
        actor=event['actor'];before=energy[actor]
        if event['decoded'][0]==6:actions.append(dict(tick=event['tick'],actor=actor,attempt=event.get('attempt')))
        if event.get('attempt',{}).get('success'):
            food[actor]=food.get(actor,0)+1
            if event['attempt']['position']!=0:remote[actor]=remote.get(actor,0)+1
            overflow+=max(0,before-1+20-64)
        if 'birth' in event:
            child=event['birth']['child'];energy[child['id']]=12
            assert child['pos'] in (0,2) and h([w[0] for w in child['code']])==h(sum(PROGRAM,[]))
            births.append(dict(tick=event['tick'],parent=actor,child=child['id'],generation=child['generation'],
                              position=child['pos'],parent_food_before_birth=food.get(actor,0),
                              parent_remote_before_birth=remote.get(actor,0),write_ids=event['birth']['write_ids'],
                              parent_energy=event['after']['energy'],startup_energy=child['energy']))
        if 'after' in event:energy[actor]=event['after']['energy']
        if 'death' in event:deaths.append(dict(tick=event['tick'],actor=actor));del energy[actor]
    s=dict(checked,descendant_food=sum(v for k,v in food.items() if k!=0),
           resource_then_birth=sum(b['parent']!=0 and b['parent_food_before_birth']>0 for b in births),
           first_birth_tick=births[0]['tick'] if births else 0,birth_certificates=births,death_certificates=deaths,
           actor_food=food,actor_remote_food=remote,energy_cap_loss=overflow,actions=actions)
    s['admitted']=gate(s)
    return s


def panel(rows):
    assert len(rows)==4 and [(r['seed'],r['mode']) for r in rows]==[(s,m) for s in SEEDS for m in MODES]
    summaries=[interpret(row) for row in rows]
    return dict(summaries=summaries,ordinary_admitted=all(s['admitted'] for s in summaries),
                supplied_fixed_exploration=True,supplied_reproductive_policy=True,
                independent_context_pairs=1,learning=False,evolution=False,stage_credit=False)
