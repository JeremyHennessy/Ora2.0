"""Variation65 independent full-audit-first projection; exact execution registration required.
No producer import, World construction, candidate execution or source selection.
"""
from experiments import digital_renewable64_interpret as full

PRIMARY=tuple(range(66000,66008))
UNSEEN=tuple(range(66200,66208))
SEEDS=PRIMARY+UNSEEN
ANCESTOR=full.ANCESTOR_WORDS


def ordinary_gate(summary):
    """Same closed64 predicates with a distinct registered65 membership guard."""
    assert summary['verified'] is True and type(summary['seed']) is int
    assert summary['seed'] in SEEDS and summary['mode']=='faithful'
    assert summary['fuel_mode']=='renewed' and summary['route']=='ancestor'
    assert summary['formation_cost']==43 and summary['genesis_program_hash']==full.h(ANCESTOR)
    t=summary['turnover']
    return (t['founder_expiry_tick'] is not None and t['post_founder_instructions']>=128
            and summary['births']>=12 and t['maximum_generation']>=3
            and t['post_founder_paid_personal_births']>0 and t['post_founder_renewed_food']>0
            and bool(t['paid_personal_chains']) and t['living_descendants']>=1)


def ordinary_admission(summaries):
    assert type(summaries) is list and len(summaries)==16
    seen=set();gates=[]
    for s in summaries:
        assert s['seed'] not in seen;seen.add(s['seed'])
        gates.append(ordinary_gate(s))  # Do not short-circuit later references.
    assert seen==set(SEEDS)
    return all(gates)


def _project_audited(row,summary):
    """Observation-only join after full replay; partial fixtures are not proof."""
    assert summary['verified'] is True
    energy={0:12};code={0:list(ANCESTOR)};generation={0:0}
    turns={0:0};food={0:0};birth_count={0:0};certificates={};born_hash={0:full.h(ANCESTOR)}
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


def audit_row(row):
    assert type(row['seed']) is int and row['seed'] in SEEDS
    assert row['mode'] in ('faithful','mutating') and row['fuel_mode']=='renewed'
    assert row['route']=='ancestor' and row['genesis_program']==[ANCESTOR[i:i+3] for i in range(0,27,3)]
    summary=full.audit(row)  # Required before any outcome/source projection.
    projected=_project_audited(row,summary)
    return dict(verified=True,summary=summary,projection=projected,history_hash=row['hash'],
                ordinary_gate=ordinary_gate(summary) if row['mode']=='faithful' else None,
                stage_credit=False)


def _actor_record(actors,identity):
    """Resolve numeric identity across in-memory and canonical JSON map keys."""
    assert type(actors) is dict and type(identity) is int and identity>=0
    normalized={}
    for key,record in actors.items():
        if type(key) is int:
            assert key>=0;number=key
        else:
            assert type(key) is str and key.isdecimal() and str(int(key))==key
            number=int(key)
        assert number not in normalized and type(record) is dict
        normalized[number]=record
    assert identity in normalized
    return normalized[identity]


def cohort(proofs):
    """Complete original-role contrast; engineering replays are kept outside."""
    assert type(proofs) is list and len(proofs)==32
    rows={}
    for proof in proofs:
        assert proof['verified'] is True and proof['stage_credit'] is False
        s=proof['summary'];assert s['verified'] is True
        assert type(s['seed']) is int and s['seed'] in SEEDS and s['mode'] in ('faithful','mutating')
        assert s['route']=='ancestor' and s['fuel_mode']=='renewed' and s['formation_cost']==43
        assert s['genesis_program_hash']==full.h(ANCESTOR)
        key=(s['seed'],s['mode']);assert key not in rows;rows[key]=proof
        if s['mode']=='faithful':assert ordinary_gate(s) and proof['ordinary_gate'] is True
        else:assert proof['ordinary_gate'] is None
    assert set(rows)=={(seed,mode) for seed in SEEDS for mode in ('faithful','mutating')}
    banks={};slots=[]
    for bank,seeds in [('primary',PRIMARY),('unseen',UNSEEN)]:
        contexts=[]
        for first in seeds[::2]:
            primary_delta=food_delta=live_delta=0;mutations=[];orientations=[]
            for seed in (first,first+1):
                fixed=rows[seed,'faithful'];mutated=rows[seed,'mutating']
                dp=mutated['projection']['primary_endpoint']-fixed['projection']['primary_endpoint']
                df=mutated['projection']['secondary_endpoint']-fixed['projection']['secondary_endpoint']
                dl=mutated['summary']['turnover']['living_descendants']-fixed['summary']['turnover']['living_descendants']
                primary_delta+=dp;food_delta+=df;live_delta+=dl;mutations.append(mutated['summary']['mutations']>0)
                orientations.append(dict(seed=seed,primary_difference=dp,food_difference=df,living_difference=dl,
                                         underexposed=mutated['projection']['underexposed']))
                slot=mutated['projection']['neutral_source_slot']
                fate=None if slot is None else _actor_record(mutated['projection']['actors'],slot['child'])
                slots.append(dict(seed=seed,slot=slot,fate=fate,history_hash=mutated['history_hash']))
            contexts.append(dict(context=first//2,orientations=orientations,primary_difference=primary_delta,
                                 food_difference=food_delta,living_difference=live_delta,
                                 passed=primary_delta>0 and food_delta>=20 and live_delta>=0 and all(mutations)))
        banks[bank]=dict(contexts=contexts,passed=all(c['passed'] for c in contexts))
    assert len(slots)==16
    return dict(verified=True,banks=banks,operator_advantage=all(b['passed'] for b in banks.values()),
                neutral_source_slots=slots,original_roles=32,source_assay_calls=0,
                selection=False,evolution=False,learning=False,stage_credit=False)


def generate(seed,mode):
    """Only an explicitly registered finite parent may call this lazy adapter."""
    assert type(seed) is int and seed in SEEDS and mode in ('faithful','mutating')
    from experiments import digital_renewable64 as producer
    assert producer.PROGRAMS=={'ancestor':[ANCESTOR[i:i+3] for i in range(0,27,3)]}
    return producer.history(seed,'ancestor',mode,'renewed')
