"""Read-only Mobile55 lifecycle diagnosis; never generates or repairs organisms."""


def edge_reason(edge, actors):
    parent = actors[str(edge['parent'])]
    child = actors[str(edge['child'])]
    prior = [tick for tick in parent['site1_success_ticks'] if tick < edge['tick']]
    assert prior == edge['parent_site1_before_birth']
    if not prior:
        return 'no_qualified_parent_function_before_birth'
    if parent['birth_words'] != child['birth_words']:
        assert not edge['eligible_parent']
        return 'changed_child_program'
    if not edge['eligible_parent']:
        return 'parent_unstable_at_division'
    if not child['site1_success_ticks']:
        assert not edge['transmitted_function_association']
        return 'exact_child_without_qualified_function'
    assert edge['transmitted_function_association']
    return 'registered_association'


def diagnose(row, proof):
    """Caller must perform the full generic VM audit before these raw-event joins."""
    actors = {str(k): v for k, v in proof['lineage']['actors'].items()}
    trace = {k: [] for k in actors}
    energy = {0: 12};positions = {0: 0};nursery = {0: 0};free = 469
    remaining = set(range(64));records = {}
    for key, p in actors.items():
        records[key] = dict(actor=int(key),parent=p['parent'],generation=p['generation'],
            birth_program=list(p['birth_words']),qualified_site1_ticks=p['site1_success_ticks'][:],
            instructions=0,actions=0,moves=0,food=0,site1_food=0,
            site1_instruction_opportunities=0,site1_attempts=0,empty_actions=0,
            paid_copy_words=0,division_attempts=0,births=0,division_refusals=[],
            received=0,sent=0,cap_loss=0,halt_loss=0,endpoint_energy=0,
            alive=p['alive'],death_tick=None)
    for event in row['final']['events']:
        actor=event['actor'];key=str(actor);r=records[key];trace[key].append(event)
        tick=event['tick'];op=event['decoded'][0];before=energy[actor];pos=positions[actor]
        local=[packet for packet in remaining if (0 if packet<32 else 1+(packet-32)//16)==pos and (not 16<=packet<32 or tick>=64)]
        r['instructions']+=1;r['actions']+=int(op==6);r['moves']+=int(op==13)
        r['site1_instruction_opportunities']+=int(pos==1 and bool(local))
        if op==6:
            assert ('attempt' in event)==bool(local)
            if not local:r['empty_actions']+=1
        if 'attempt' in event:
            attempt=event['attempt'];assert attempt['packet']==min(local) and attempt['position']==pos
            r['site1_attempts']+=int(pos==1)
            if attempt['success']:
                remaining.remove(attempt['packet']);r['food']+=1;r['site1_food']+=int(pos==1)
                r['cap_loss']+=max(0,before-1+20-64)
        writes=len(event.get('writes',[]));nursery[actor]+=writes;r['paid_copy_words']+=writes;free-=writes
        if op==12:
            r['division_attempts']+=1
            gates=dict(complete_nursery=nursery[actor]==27,energy_after_base=before-1,
                       enough_energy=before-1>=30,free_material=free,enough_material=free>=16,
                       live_population=len(energy),population_room=len(energy)<32)
            assert ('birth' in event)==all(gates[k] for k in ('complete_nursery','enough_energy','enough_material','population_room'))
            if 'birth' not in event:r['division_refusals'].append(dict(tick=tick,**gates))
        if 'birth' in event:
            child=event['birth']['child'];identity=child['id'];r['births']+=1;free-=16
            assert identity not in energy;energy[identity]=12;positions[identity]=pos;nursery[identity]=0;nursery[actor]=0
        if 'transfer' in event:
            recipient=event['transfer'];energy[recipient]+=1;r['sent']+=1;records[str(recipient)]['received']+=1
        if op==17:r['halt_loss']+=before-1
        if 'after' in event:energy[actor]=event['after']['energy'];positions[actor]=event['after']['pos']
        if 'death' in event:
            free+=len(event['death']);r['death_tick']=tick;del energy[actor];del positions[actor];del nursery[actor]
    edges=[]
    for edge in proof['lineage']['edges']:
        reason=edge_reason(edge,actors)
        edges.append(dict(tick=edge['tick'],parent=edge['parent'],child=edge['child'],reason=reason,
            parent_site1_before_birth=edge['parent_site1_before_birth'],exact_program_transfer=edge['exact_program_transfer'],
            child_site1_success_ticks=edge['child_site1_success_ticks'],
            child_instructions=records[str(edge['child'])]['instructions'],child_food=records[str(edge['child'])]['food'],
            child_alive=records[str(edge['child'])]['alive']))
    for key,r in records.items():
        r['endpoint_energy']=energy.get(int(key),0)
        assert r['endpoint_energy']==12+20*r['food']+r['received']-r['instructions']-r['paid_copy_words']-30*r['births']-r['sent']-r['cap_loss']-r['halt_loss']
        assert r['food']==sum(actors[key]['food_by_site']) and r['births']==actors[key]['births']
        assert r['alive']==(int(key) in energy) and r['instructions']==actors[key]['instructions']
        if r['qualified_site1_ticks']:
            first=r['qualified_site1_ticks'][0]
            r['births_before_first_function']=sum(e['parent']==int(key) and e['tick']<first for e in edges)
            r['births_after_first_function']=sum(e['parent']==int(key) and e['tick']>first for e in edges)
            r['remaining_scheduled_instructions_after_first_function']=sum(e['tick']>first for e in trace[key])
            r['paid_children']=[e for e in edges if e['parent']==int(key)]
    assert free==len(row['final']['free']) and len(remaining)==proof['summary']['unused_food']
    assert len(edges)==proof['summary']['births'] and sum(r['food'] for r in records.values())==proof['summary']['successful_food']
    return dict(seed=row['seed'],mode=row['mode'],actors=records,edges=edges,
                qualified_actors=[r for r in records.values() if r['qualified_site1_ticks']],
                inherited_benefit=False,evolution=False,learning=False,stage_credit=False)
