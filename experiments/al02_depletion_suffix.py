"""Independent AL02 suffix interpretation from a pinned DATA boundary."""

from experiments.al02_depletion_checkpoint import (
    _canonical, _require, encode_checkpoint, restore_checkpoint, sequester_b,
)
from experiments.al02_depletion_projection import require_depletion
from experiments.al02_selection_referee import _hash


def verify_suffix(raw, pin, role, record):
    """Verify one complete branch. The original prefix must be authenticated separately."""
    _require(role in ('accessible', 'sequestered') and type(record) is dict
             and set(record) == {'role', 'prefix_sha256', 'events'}
             and record['role'] == role and record['prefix_sha256'] == pin,
             'Branch identity mismatch')
    state, rng = restore_checkpoint(raw, pin)
    require_depletion(state)
    if role == 'sequestered':
        state = sequester_b(state)
    result, _ = _verify_events(state, rng, record['events'], 600)
    return result


def _verify_events(state, rng, rows, stop_tick):
    _require(type(rows) is list and len(rows) <= 3 * (600 - state['tick']),
             'Invalid suffix extent')
    alive = {a['organism_id']: a for a in state['organisms']}
    free = set(state['free_units'])
    counters = state['counters']
    meals = cursor = 0
    initial_births = len(state['births'])

    def take(kind, **fields):
        nonlocal cursor
        event = dict(event_id=len(state['events']), tick=state['tick'], kind=kind, **fields)
        _require(cursor < len(rows) and _canonical(rows[cursor]) == _canonical(event),
                 f'Invalid or missing suffix event {event["event_id"]} ({kind})')
        state['events'].append(event)
        cursor += 1
        return event

    def death(actor, reason):
        identity = actor['organism_id']
        take('DEATH', organism_id=identity, reason=reason,
             energy_released=actor['energy'], abandoned_nursery=len(actor['nursery']))
        free.update(unit for _, unit in actor['tape'] + actor['nursery'])
        state['heat'] += actor['energy']
        counters['deaths'] += 1
        del alive[identity]

    while alive and state['tick'] < stop_tick:
        ids = sorted(alive)
        identity = next((i for i in ids if i > state['last_actor']), ids[0])
        state['tick'] += 1
        state['last_actor'] = identity
        actor = alive[identity]
        pc = actor['pc']
        if pc == 4:
            take('FAULT', organism_id=identity, reason='pc_outside_tape', pc=pc)
            death(actor, 'pc_outside_tape')
            continue
        op = actor['tape'][pc][0]
        before = actor['energy']
        actor['energy'] -= 1
        state['heat'] += 1
        actor['pc'] += 1
        if op in (0, 1):
            outcome = 'food_unavailable'
            food = 'food_a' if op == 0 else 'food_b'
            if state[food]:
                state[food] -= 1
                actor['energy'] += 20
                meals += int(op == 1)
                outcome = 'ate_a' if op == 0 else 'ate_b'
        elif op == 2:
            index = actor['read_head']
            if index == 4:
                outcome = 'nursery_already_complete'
            elif actor['energy'] < 1 or not free:
                outcome = 'copy_material_or_energy_missing'
                counters['failed_copy'] += 1
            else:
                original, source_unit = actor['tape'][index]
                value = original
                if rng.random() < 0.08:
                    value = [choice for choice in range(6) if choice != original][rng.randrange(5)]
                unit = min(free)
                free.remove(unit)
                actor['energy'] -= 1
                state['heat'] += 1
                event = take('COPY_WRITE', parent_id=identity,
                             parent_genome_hash=_hash([op for op, _ in actor['tape']]),
                             source_index=index, source_material_unit=source_unit,
                             source_op=original, material_unit=unit, written_op=value,
                             mutated=value != original, nursery_index=index, paid_energy=2)
                actor['nursery'].append([value, unit])
                actor['nursery_write_ids'].append(event['event_id'])
                actor['read_head'] += 1
                counters['mutations_written'] += int(value != original)
                outcome = 'copied_one_byte'
        elif op == 3:
            if actor['read_head'] < 4:
                actor['pc'] = 1
            outcome = 'loop_copy' if actor['pc'] == 1 else 'loop_finished'
        elif op == 4:
            actor['pc'] = 0
            outcome = 'division_blocked'
            if actor['read_head'] == 4 and actor['energy'] >= 6 and len(alive) < 64:
                child = state['next_organism_id']
                state['next_organism_id'] += 1
                parent_ops = [op for op, _ in actor['tape']]
                child_ops = [op for op, _ in actor['nursery']]
                actor['energy'] -= 6
                state['heat'] += 2
                event = take('BIRTH', parent_id=identity, child_id=child,
                             parent_genome_hash=_hash(parent_ops), child_genome_hash=_hash(child_ops),
                             parent_genome_ops=parent_ops, child_genome_ops=child_ops,
                             child_material_units=[unit for _, unit in actor['nursery']],
                             copy_event_ids=actor['nursery_write_ids'][:],
                             generation=actor['generation']+1, transferred_energy=4,
                             genesis_seeded=False)
                state['births'].append({key: value for key, value in event.items()
                                        if key not in ('kind', 'tick')})
                alive[child] = dict(organism_id=child, parent_id=identity, born_tick=state['tick'],
                                    generation=actor['generation']+1, energy=4, tape=actor['nursery'],
                                    pc=0, read_head=0, nursery=[], nursery_write_ids=[])
                actor.update(nursery=[], nursery_write_ids=[], read_head=0)
                outcome = 'executed_division'
            else:
                counters['failed_divisions'] += 1
        else:
            outcome = 'nop'
        take('EXEC', organism_id=identity, opcode=op, pc_before=pc, pc_after=actor['pc'],
             energy_before=before, energy_after=actor['energy'], read_head_after=actor['read_head'],
             nursery_bytes_after=len(actor['nursery']), outcome=outcome, food_a=state['food_a'],
             food_b=state['food_b'], population_after_instruction=len(alive), heat=state['heat'])
        if actor['energy'] == 0:
            death(actor, 'energy_exhausted')
        counters['max_population_seen'] = max(counters['max_population_seen'], len(alive))

    _require(cursor == len(rows), 'Trailing suffix events')
    state.update(organisms=list(alive.values()), free_units=sorted(free))
    final = encode_checkpoint(state, rng)
    return dict(paid_births=len(state['births'])-initial_births, b_meals=meals,
                accessible_b=state['food_b'], escrow_b=state['escrow_b'], extinct=not alive,
                authenticated_execution=False), final


def verify_pair(seed, raw, pin, branches):
    """Reconstruct the common prefix independently before interpreting either suffix."""
    from hashlib import sha256
    from random import Random
    from experiments.al02_depletion_checkpoint import COUNTERS

    _require(type(seed) is int and 0 <= seed < 2**64, 'Invalid committed seed')
    supplied, _ = restore_checkpoint(raw, pin)
    config = dict(seed=seed, variant='mutating', copy_enabled=True, mutation_rate=0.08,
                  material_units=256, population_limit=64, genesis_energy=604,
                  genesis_material=256, initial_food_a=12, initial_food_b=18)
    genesis = dict(event_id=0, tick=0, kind='GENESIS', organism_id=0,
                   tape_ops=[0, 2, 3, 4], tape_units=[0, 1, 2, 3], food_a=12, food_b=18,
                   energy=4, free_material=252)
    _require(_canonical(supplied['events'][0]) == _canonical(genesis), 'Wrong genesis')
    founder = dict(organism_id=0, tape=[[op, i] for i, op in enumerate((0, 2, 3, 4))],
                   energy=4, generation=0, parent_id=None, born_tick=0, pc=0,
                   read_head=0, nursery=[], nursery_write_ids=[])
    initial = dict(config_sha256=sha256(_canonical(config)).hexdigest(), tick=0,
                   last_actor=-1, next_organism_id=1, organisms=[founder],
                   free_units=list(range(4, 256)), food_a=12, food_b=18, escrow_b=0,
                   heat=0, events=[genesis], births=[],
                   counters=dict.fromkeys(COUNTERS, 0))
    initial['counters']['max_population_seen'] = 1
    _, reconstructed = _verify_events(initial, Random(seed), supplied['events'][1:],
                                      supplied['tick'])
    _require(raw == reconstructed, 'Prefix state or RNG does not match original events')
    _require(type(branches) is dict and set(branches) == {'accessible', 'sequestered'},
             'Both branch records required')
    if supplied['food_a']:
        _require(not supplied['organisms'] or supplied['tick'] == 600,
                 'Live prefix stopped without depletion')
        for role, record in branches.items():
            _require(_canonical(record) == _canonical(
                dict(role=role, prefix_sha256=pin, events=[])), 'Invalid no-trigger branch')
        return dict(contrast=0, triggered=False, extinct=not supplied['organisms'],
                    authenticated_execution=False)
    results = {role: verify_suffix(raw, pin, role, record) for role, record in branches.items()}
    return dict(contrast=results['accessible']['paid_births']-results['sequestered']['paid_births'],
                triggered=True, branches=results, authenticated_execution=False)


def verify_panel(committed_seeds, records):
    """Keep every committed index, including duplicate draws and biological nulls."""
    _require(type(committed_seeds) is list and type(records) is list
             and len(committed_seeds) == len(records) == 128, 'All 128 pairs required')
    results = []
    for index, (seed, record) in enumerate(zip(committed_seeds, records)):
        _require(type(record) is dict and set(record) == {'index', 'raw', 'pin', 'branches'}
                 and type(record['index']) is int and record['index'] == index,
                 'Invalid context record or operational failure')
        results.append(verify_pair(seed, record['raw'], record['pin'], record['branches']))
    return results
