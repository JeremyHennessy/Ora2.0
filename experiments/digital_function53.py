"""Read-only opportunity census AFTER the unchanged full Exposure23 referee."""
from collections import Counter
from copy import deepcopy
from experiments.digital_variation52 import PROGRAM, SEEDS, MODES, interpret


def founder(program):
    return dict(code=[[v,i] for i,v in enumerate(sum(program,[]))],registers=[0,0],
                energy=12,pc=0,pos=0,nursery=[],generation=0,parent=None)


def scan(events, program=PROGRAM, mode='mutating'):
    states={0:founder(program)}; actors={}; writes={}; born=set(); counts=Counter(); previous=0
    def add(identity,state):
        actors[identity]=dict(parent=state['parent'],generation=state['generation'],
            birth_move_sites=[i//3 for i,c in enumerate(state['code']) if i%3==0 and c[0]==13],
            instructions=0,moves=0,food=0,failed_attempts=0,empty_actions=0,births=0,
            visited_positions=[state['pos']],executed_sites=[],self_writes=0,death_tick=None)
    add(0,states[0])
    for ev in events:
        assert type(ev['tick']) is int and ev['tick']>previous;previous=ev['tick']
        identity=ev['actor'];state=states[identity];person=actors[identity]
        op,a,b=ev['decoded'];assert all(type(v) is int and 0<=v<32 for v in ev['decoded'])
        assert ev['decoded']==[v[0] for v in state['code'][3*state['pc']:3*state['pc']+3]]
        person['instructions']+=1;person['executed_sites'].append(state['pc'])
        counts['instructions']+=1;counts['opcode_'+str(op)]+=1
        postpos=state['pos']
        if op==13:
            postpos=(state['pos']+(1 if state['registers'][a%2]%2 else -1))%4
            counts['moves']+=1;person['moves']+=1
        if postpos not in person['visited_positions']:person['visited_positions'].append(postpos)
        if op==6:
            counts['actions']+=1;attempt=ev.get('attempt')
            if attempt:
                assert attempt['position']==state['pos']
                counts['available_actions']+=1
                counts['home_attempts' if state['pos']==0 else 'remote_attempts']+=1
                key='food' if attempt['success'] else 'failed_attempts'
                counts[key]+=1;person[key]+=1
                if attempt['success'] and state['pos']!=0:counts['remote_food']+=1
            else:counts['empty_actions']+=1;person['empty_actions']+=1
        if 'self_write' in ev:person['self_writes']+=1;counts['self_writes']+=1
        if ev['outcome']=='copy_refused':
            counts['copy_refused']+=1
            if state['energy']-1<3:counts['copy_energy_refusals']+=1
            if len(state['nursery'])==len(state['code']):counts['copy_full_refusals']+=1
            if mode=='copy_disabled':counts['copy_disabled_refusals']+=1
        if ev['outcome']=='division_refused':
            counts['division_refused']+=1
            if state['energy']-1<30:counts['division_energy_refusals']+=1
            if len(state['nursery'])!=len(state['code']):counts['division_incomplete_refusals']+=1
        for w in ev.get('writes',[]):
            assert w['write_id'] not in writes;writes[w['write_id']]=w;counts['paid_words']+=1
            if w['mutated']:
                counts['mutated_words']+=1;counts['mutation_role_'+str(w['index']%3)]+=1
                if w['index']%3==0 and w['value']==13:counts['mutated_move_words']+=1
        if 'birth' in ev:
            birth=ev['birth'];child=birth['child'];new=child['id'];assert new not in states
            states[new]=deepcopy(child);add(new,child);counts['births']+=1;person['births']+=1
            for wid in birth['write_ids']:
                assert wid in writes and wid not in born;born.add(wid)
                if writes[wid]['mutated']:counts['mutations_reaching_birth']+=1
        if 'transfer' in ev:states[ev['transfer']]['energy']+=1
        if 'after' in ev:
            assert ev['after']['pos']==postpos;states[identity]=deepcopy(ev['after'])
        else:
            assert 'death' in ev;person['death_tick']=ev['tick'];counts['deaths']+=1
            person['unborn_nursery_words_at_death']=len(state['nursery'])+len(ev.get('writes',[]))-(len(state['code']) if 'birth' in ev else 0)
            del states[identity]
    for p in actors.values():
        p['executed_sites']=sorted(set(p['executed_sites']))
        p['unexecuted_birth_move_sites']=sorted(set(p['birth_move_sites'])-set(p['executed_sites']))
        p['visited_positions'].sort()
    counts['mutations_not_reaching_birth']=sum(w['mutated'] for i,w in writes.items() if i not in born)
    counts['actors_with_birth_move']=sum(bool(p['birth_move_sites']) for p in actors.values())
    counts['actors_executing_move']=sum(p['moves']>0 for p in actors.values())
    counts['actors_visiting_resource_sites']=sum(bool(set(p['visited_positions']) & {1,2}) for p in actors.values())
    counts['finite_survivors']=len(states)
    return dict(counts=dict(sorted(counts.items())),actors=actors)


def diagnose(row):
    assert row['seed'] in SEEDS and row['mode'] in MODES
    checked=interpret(row); result=scan(row['final']['events'],row['genesis_program'],row['mode'])
    for key, old in [('births','births'),('deaths','deaths'),('food','successful_food'),('remote_food','remote_food'),('paid_words','paid_copy_words'),('mutated_words','mutations')]:
        assert result['counts'].get(key,0)==checked['checked'][old]
    return dict(seed=row['seed'],mode=row['mode'],diagnosis=result,stage_credit=False,
                new_world_histories=0,causal_genotype_assay=False)
