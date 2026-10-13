"""Pure prospective69 fixture helpers; not full ancestry/continuation evidence.

No World, hash sampler, seed query, policy, execution admission or stage credit.
Complete independent raw-history/custody checks must precede scientific use.
"""
ANCESTOR=[4,1,1,6,0,0,5,0,1,6,0,0,10,0,0,12,0,0,13,1,0,13,1,0,7,0,1]
VERSION='DIGITAL-FUNCTIONAL-INHERITANCE-69-v1'

def integer(value,minimum=0,maximum=None):
    assert type(value) is int and value>=minimum
    assert maximum is None or value<=maximum
    return value

def child_source_values(certificates):
    """Prepared/full-audited certificates only; preserve own draws,not their truth.

    This partial validator cannot authenticate a history or prove paid ancestry.
    The future literal referee must independently derive every certificate/mask.
    """
    assert type(certificates) is list and len(certificates)==27
    writes=set();units=set();sources=set();parent=None;last_tick=0;code=[]
    for index,w in enumerate(certificates):
        assert type(w) is dict and w['index']==integer(w['index'],0,26)==index
        actor=integer(w['actor']);parent=actor if parent is None else parent;assert actor==parent
        identity=integer(w['write_id']);unit=integer(w['unit'],0,511);source=integer(w['source_unit'],0,511)
        assert identity not in writes and unit not in units and source not in sources
        writes.add(identity);units.add(unit);sources.add(source)
        tick=integer(w['tick'],1,4096);assert tick>=last_tick;last_tick=tick
        src=integer(w['source_value'],0,31);effective=integer(w['effective_source_value'],0,31)
        assert w['effective_source']=='parent_copy' and effective==src
        draw=integer(w['mutation_draw'],0,2**64-1);value=integer(w['value'],0,31)
        changed=draw%100<8
        expected=(src+1+(draw//100)%31)%32 if changed else src
        assert value==expected and type(w['mutated']) is bool and w['mutated']==changed
        baseline=(ANCESTOR[index]+1+(draw//100)%31)%32 if changed else ANCESTOR[index]
        code.append([baseline,unit])
    assert units.isdisjoint(sources)
    return code

def endpoint(e):
    assert type(e) is dict and type(e['censored']) is bool
    integer(e['births']);integer(e['food'])
    assert type(e['signatures']) is list
    for signature in e['signatures']:
        assert type(signature) is list and signature
        if signature[0]=='ACT':
            assert len(signature)==3;integer(signature[1],0,3);integer(signature[2],0,1)
        else:
            assert signature[0]=='MOVE' and len(signature)==2;integer(signature[1],0,3)
    return e

def contrast(sham,control,changed):
    """Complete measured endpoints; caller still owes authenticated paid history."""
    endpoint(sham);endpoint(control);assert type(changed) is bool
    complete=not sham['censored'] and not control['censored']
    db=sham['births']-control['births'];df=sham['food']-control['food']
    useful=changed and complete and ((db>0 and df>=0) or(df>0 and db>=0))
    different=[i for i,(a,b) in enumerate(zip(sham['signatures'],control['signatures'])) if a!=b]
    return dict(complete=complete,birth_difference=db,food_difference=df,useful=useful,
        new_strategy=useful and bool(different),differing_action_ordinals=different,
        stage_credit=False,requires_authenticated_full_history=True)

def functional_contribution(parent,parent_control,child,child_control,parent_changed,source_changed,paid_edge):
    """Fixture reachability only; no boolean paid marker proves a scientific edge."""
    assert type(paid_edge) is bool
    p=contrast(parent,parent_control,parent_changed);c=contrast(child,child_control,source_changed)
    qualifies=(paid_edge and p['new_strategy'] and c['new_strategy'] and child['food']>0 and child['births']>0)
    return dict(parent=p,child=c,conditional_functional_contribution=qualifies,
        stage_credit=False,requires_authenticated_full_history=True)

def lifecycle_bill():
    """Conditional supplied-route arithmetic; fresh full admission remains owed."""
    return dict(code_words=27,state_units=16,founder_assembly=43,founder_startup_supplied=12,
        constructor_pool=128,constructor_after_assembly=85,constructor_after_release=69,
        initial_energy=1420,material_pool=512,free_after_assembly=469,
        copy_instructions=9,copy_base=9,copy_extra=27,division_base=1,division_extra=30,
        child_startup=12,min_parent_birth_debit=67,min_birth_heat=55,
        conditional_cold_cycle_base=9,conditional_cold_cycle_copy_extra=3,
        conditional_cold_cycle_intake=20,conditional_cold_cycle_end=20,
        conditional_first_division_own_instruction=70,conditional_next_division_spacing=72,
        conditional_max_ordinary_births_per_256_turns=3,viability_demonstrated=False)
