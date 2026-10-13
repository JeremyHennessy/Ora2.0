"""Genotype-specific observation ledger after the unchanged full VM referee.
Fork of the reviewed65 projection with only explicit initial program binding.
Closed65 remains byte-for-byte unchanged. This module never constructs a World.
"""
from experiments import digital_renewable64_interpret as full


def _project_audited(row,summary):
    """Observation-only join after full replay; partial fixtures are not proof."""
    assert summary['verified'] is True
    words=[v for instruction in row['genesis_program'] for v in instruction]
    assert len(words)==27 and all(type(v) is int and 0<=v<32 for v in words)
    assert full.h(words)==summary['genesis_program_hash']
    energy={0:12};code={0:list(words)};generation={0:0}
    turns={0:0};food={0:0};birth_count={0:0};certificates={};born_hash={0:full.h(words)}
    births=[];actors={};cap_loss=0;empty_act=0;self_writes=0;refusals={}
    for e in row['final']['events']:
        actor=e['actor'];prior_energy=energy[actor];parent_program=list(code[actor])
        turns[actor]+=1
        if e['outcome'].endswith('_refused'):
            refusals[e['outcome']]=refusals.get(e['outcome'],0)+1
        if e['decoded'][0]==6:
            if 'attempt' not in e:empty_act+=1
            elif e['attempt']['success']:
                food[actor]+=1
                gain=e['after']['energy']-(prior_energy-1)
                assert 0<=gain<=20
                cap_loss+=20-gain
        if 'self_write' in e:
            self_writes+=1;code[actor][e['self_write']['index']]=e['self_write']['value']
        for w in e.get('writes',[]):
            assert w['write_id'] not in certificates
            certificates[w['write_id']]=dict(w,actor=actor,source_program_hash=full.h(parent_program))
        if 'birth' in e:
            b=e['birth'];daughter=b['child'];child=daughter['id']
            assert child not in generation and daughter['generation']==generation[actor]+1
            words=[certificates[i] for i in b['write_ids']]
            assert len(words)==27 and all(w['actor']==actor for w in words)
            newborn=[v[0] for v in daughter['code']]
            copied_source=[w['source_value'] for w in words]
            assert newborn==[w['value'] for w in words]
            birth_count[actor]+=1
            births.append(dict(child=child,parent=actor,generation=daughter['generation'],tick=e['tick'],
                               parent_turns=turns[actor],parent_personal_food=food[actor],
                               parent_program_at_division=parent_program,
                               parent_program_at_division_hash=full.h(parent_program),
                               temporally_copied_source_program=copied_source,
                               temporally_copied_source_hash=full.h(copied_source),
                               copy_source_program_hashes=[w['source_program_hash'] for w in words],
                               newborn_program=newborn,newborn_program_hash=full.h(newborn),
                               actual_mutated_words=sum(w['mutated'] for w in words),
                               write_ids=b['write_ids'],paid_copy_words=27,state_formation_words=16,
                               startup_energy=b['startup_energy'],release_energy=b['release_energy']))
            energy[child]=daughter['energy'];code[child]=newborn;generation[child]=daughter['generation'];born_hash[child]=full.h(newborn)
            turns[child]=food[child]=birth_count[child]=0
        if 'transfer' in e:energy[e['transfer']]+=1
        if 'after' in e:
            assert code[actor]==[v[0] for v in e['after']['code']]
            energy[actor]=e['after']['energy']
        if 'death' in e or 'expiry' in e:
            actors[actor]=dict(generation=generation[actor],turns=turns[actor],food=food[actor],program_at_birth_hash=born_hash[actor],program_at_end_hash=full.h(code[actor]),
                               births=birth_count[actor],death_tick=e['tick'],
                               death_cause='execution_budget' if 'expiry' in e else ('halt' if e['outcome']=='halt' else 'zero_energy'),
                               censored=False)
            del energy[actor];del code[actor]
    for actor in energy:
        actors[actor]=dict(generation=generation[actor],turns=turns[actor],food=food[actor],program_at_birth_hash=born_hash[actor],program_at_end_hash=full.h(code[actor]),
                           births=birth_count[actor],death_tick=None,death_cause=None,censored=True)
    assert turns=={int(k):v for k,v in summary['turns'].items()}
    assert len(births)==summary['births'] and sum(food.values())==summary['successful_food']
    assert sum(turns.values())==summary['ticks'] and sum(birth_count.values())==summary['births']
    assert sum(not a['censored'] for a in actors.values())==summary['deaths']
    changed=sum(b['actual_mutated_words']>0 for b in births)
    t=summary['turnover'];founder_expired=t['founder_expiry_tick'] is not None
    return dict(actors=actors,births=births,cap_loss_energy=cap_loss,empty_act=empty_act,
                self_writes=self_writes,refusals=refusals,changed_paid_newborns=changed,
                final_food_by_site=[sum(v[0]==site for v in row['final']['food'].values()) for site in range(4)],
                underexposed=(changed<3 or t['maximum_generation']<3) if row['mode']=='mutating' else None,
                primary_endpoint=t['post_founder_paid_personal_births'] if founder_expired else 0,
                secondary_endpoint=t['post_founder_renewed_food'] if founder_expired else 0,
                neutral_source_slot=(births[0] if births else None) if row['mode']=='mutating' else None,
                learning=False,selection=False,stage_credit=False)

