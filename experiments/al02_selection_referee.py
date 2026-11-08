"""Independent interpretation of immutable AL02 logs, never a World/producer.

No output can authenticate native origin. Synthetic fixtures remain synthetic.
Reuses AL07's independently written ownership/energy checks after stricter
scheduler, exact transition, RNG and termination reconstruction.
"""
from __future__ import annotations

import hashlib
import random

from experiments.al02_selection_request import (
    ARMS, canonical, prepare_request, validate_opening,
)
from experiments.causal_genealogy_audit import audit_world as genealogy


def _same(actual, expected):
    if canonical(actual) != canonical(expected):
        raise ValueError('immutable event/summary mismatch')


def _hash(ops):
    return hashlib.sha256(canonical(ops)).hexdigest()


def _interpret(seed, variant, food_a, food_b, events, births, summary):
    """Consume a COMPLETE log; do not produce or run a scientific history."""
    if type(seed) is not int or not 0 <= seed < 2**64 or variant not in ('faithful', 'mutating'):
        raise ValueError('bad source configuration')
    if any(type(x) is not int or x < 0 for x in (food_a, food_b)):
        raise ValueError('bad fixture resources')
    if type(events) is not list or not 1 <= len(events) <= 1801 or type(births) is not list or len(births) > 600:
        raise ValueError('bounded original streams required')
    cursor = 0
    tick = 0
    heat = 0
    free = set(range(4, 256))
    alive = {0: dict(code=[[op, i] for i, op in enumerate((0, 2, 3, 4))],
                     energy=4, pc=0, read=0, nursery=[], writes=[], generation=0)}
    actors = {0: dict(parent=None, code=[0, 2, 3, 4], born=0, foods_a=0,
                      foods_b=0, b_events=[], births=[], eligible=False, death=None)}
    receipts = []
    eligible_births = []
    last = -1
    next_id = 1
    copies = mutations = deaths = failed_copy = failed_divisions = 0
    max_population = 1
    rng = random.Random(seed)
    initial_a, initial_b = food_a, food_b

    def take(kind, **fields):
        nonlocal cursor
        expected = dict(event_id=cursor, tick=tick, kind=kind, **fields)
        if cursor >= len(events):
            raise ValueError('incomplete history')
        _same(events[cursor], expected)
        cursor += 1
        return expected

    def death(identity, reason):
        nonlocal heat, deaths
        entity = alive[identity]
        take('DEATH', organism_id=identity, reason=reason,
             energy_released=entity['energy'], abandoned_nursery=len(entity['nursery']))
        free.update(cell[1] for cell in entity['code'] + entity['nursery'])
        heat += entity['energy']
        actors[identity]['death'] = tick
        del alive[identity]
        deaths += 1

    take('GENESIS', organism_id=0, tape_ops=[0, 2, 3, 4], tape_units=[0, 1, 2, 3],
         food_a=food_a, food_b=food_b, energy=4, free_material=252)
    while alive and tick < 600:
        # No transition is attempted without original evidence for that tick.
        if cursor >= len(events):
            raise ValueError('live history truncated before600')
        ids = sorted(alive)
        actor = next((identity for identity in ids if identity > last), ids[0])
        last = actor
        entity = alive[actor]
        tick += 1
        pc = entity['pc']
        if not 0 <= pc < 4:
            take('FAULT', organism_id=actor, reason='pc_outside_tape', pc=pc)
            death(actor, 'pc_outside_tape')
            continue
        op = entity['code'][pc][0]
        before = entity['energy']
        if before < 1:
            death(actor, 'no_energy')
            continue
        entity['energy'] -= 1
        heat += 1
        outcome = 'executed'
        if op in (0, 1):
            if (food_a if op == 0 else food_b) > 0:
                if op == 0:
                    food_a -= 1
                    actors[actor]['foods_a'] += 1
                else:
                    actors[actor]['b_events'].append(dict(tick=tick, food_before=food_b,
                                                        coexisting=sorted(alive)))
                    food_b -= 1
                    actors[actor]['foods_b'] += 1
                entity['energy'] += 20
                outcome = 'ate_a' if op == 0 else 'ate_b'
            else:
                outcome = 'food_unavailable'
            entity['pc'] += 1
        elif op == 2:
            if entity['read'] >= 4:
                outcome = 'nursery_already_complete'
            elif entity['energy'] < 1 or not free:
                outcome = 'copy_material_or_energy_missing'
                failed_copy += 1
            else:
                entity['energy'] -= 1
                heat += 1
                index = entity['read']
                original, source_unit = entity['code'][index]
                value = original
                # Same PRNG specification, independent transition implementation.
                if rng.random() < (0.08 if variant == 'mutating' else 0.0):
                    value = [choice for choice in range(6) if choice != original][rng.randrange(5)]
                unit = min(free)
                free.remove(unit)
                event = take('COPY_WRITE', parent_id=actor,
                             parent_genome_hash=_hash([cell[0] for cell in entity['code']]),
                             source_index=index, source_material_unit=source_unit,
                             source_op=original, material_unit=unit, written_op=value,
                             mutated=value != original, nursery_index=len(entity['nursery']), paid_energy=2)
                entity['nursery'].append([value, unit])
                entity['writes'].append(event['event_id'])
                entity['read'] += 1
                copies += 1
                mutations += int(value != original)
                outcome = 'copied_one_byte'
            entity['pc'] += 1
        elif op == 3:
            entity['pc'] = 1 if entity['read'] < 4 else pc + 1
            outcome = 'loop_copy' if entity['pc'] == 1 else 'loop_finished'
        elif op == 4:
            if len(entity['nursery']) == 4 and len(entity['writes']) == 4 and entity['energy'] >= 6 and len(alive) < 64:
                entity['energy'] -= 6
                heat += 2
                child = next_id
                next_id += 1
                code = entity['nursery']
                parent_ops = [cell[0] for cell in entity['code']]
                child_ops = [cell[0] for cell in code]
                eligible = food_a == 0 and child_ops in ([0, 2, 3, 4], [1, 2, 3, 4])
                coexisting = sorted(alive)
                event = take('BIRTH', parent_id=actor, child_id=child,
                             parent_genome_hash=_hash(parent_ops), child_genome_hash=_hash(child_ops),
                             parent_genome_ops=parent_ops, child_genome_ops=child_ops,
                             child_material_units=[cell[1] for cell in code],
                             copy_event_ids=entity['writes'][:], generation=entity['generation'] + 1,
                             transferred_energy=4, genesis_seeded=False)
                receipts.append({key: value for key, value in event.items() if key not in ('kind', 'tick')})
                alive[child] = dict(code=code, energy=4, pc=0, read=0, nursery=[], writes=[], generation=entity['generation'] + 1)
                actors[child] = dict(parent=actor, code=child_ops, born=tick,
                                     foods_a=0, foods_b=0, b_events=[], births=[], eligible=eligible, death=None)
                if eligible:
                    eligible_births.append(dict(child=child, tick=tick, food_b=food_b, coexisting=coexisting))
                actors[actor]['births'].append(child)
                entity['nursery'] = []
                entity['writes'] = []
                entity['read'] = 0
                outcome = 'executed_division'
            else:
                failed_divisions += 1
                outcome = 'division_blocked'
            entity['pc'] = 0
        elif op == 5:
            entity['pc'] += 1
            outcome = 'nop'
        else:
            raise ValueError('invalid inherited opcode')
        take('EXEC', organism_id=actor, opcode=op, pc_before=pc, pc_after=entity['pc'],
             energy_before=before, energy_after=entity['energy'], read_head_after=entity['read'],
             nursery_bytes_after=len(entity['nursery']), outcome=outcome,
             food_a=food_a, food_b=food_b, population_after_instruction=len(alive), heat=heat)
        if entity['energy'] <= 0:
            death(actor, 'energy_exhausted')
        max_population = max(max_population, len(alive))
        units = list(free) + [cell[1] for e in alive.values() for cell in e['code'] + e['nursery']]
        if sorted(units) != list(range(256)) or sum(e['energy'] for e in alive.values()) + heat + 20 * (food_a + food_b) != 4 + 20 * (initial_a + initial_b):
            raise ValueError('independent conservation failure')
    if cursor != len(events):
        raise ValueError('trailing or reordered evidence')
    _same(births, receipts)
    expected = dict(seed=seed, variant=variant, ticks=tick, world_extinct=not alive,
                    live_count=len(alive), max_population=max_population,
                    birth_count=len(receipts), death_count=deaths, copy_events=copies,
                    mutated_bytes_written=mutations, failed_copy_attempts=failed_copy,
                    failed_divisions=failed_divisions, remaining_food_a=food_a,
                    remaining_food_b=food_b, consumed_food_a=initial_a-food_a,
                    consumed_food_b=initial_b-food_b, remaining_material=len(free), heat=heat,
                    max_material_residual=0, max_energy_residual=0,
                    genesis_energy=4 + 20 * (initial_a + initial_b), genesis_material=256,
                    remaining_tapes=[[cell[0] for cell in e['code']] for e in alive.values()])
    _same(summary, expected)
    tagged = [dict(event, seed=seed, variant=variant) for event in events]
    checked = genealogy(tagged, births, expected)
    if not checked['valid']:
        raise ValueError('AL07 ownership/energy cross-check failed')
    return dict(births=len(receipts), actors=actors, eligible_births=eligible_births,
                ticks=tick, extinct=not alive, authenticated_execution=False)


def mechanism(result):
    """Predeclared cohort gate on independently reconstructed states only."""
    actors = result['actors']
    observed = []
    for identity, actor in actors.items():
        if not actor['eligible'] or actor['code'] != [1, 2, 3, 4] or not actor['foods_b'] or not actor['births']:
            continue
        for feeding in actor['b_events']:
            a_cohort = [other for other, value in actors.items()
                        if value['eligible'] and value['code'] == [0, 2, 3, 4]
                        and value['death'] is not None and not value['births']
                        and other in feeding['coexisting'] and feeding['food_before'] > 0
                        and value['born'] < feeding['tick'] < value['death']]
            inherited = [child for child in actor['births']
                         if actors[child]['born'] > feeding['tick']
                         and actors[child]['code'] == actor['code']
                         and actors[child]['foods_b'] and actors[child]['births']]
            if a_cohort and inherited:
                observed.append(dict(parent=identity, feeding_tick=feeding['tick'],
                                     a_cohort=a_cohort, inherited=inherited))
    return dict(scope='CONDITIONAL_RESOURCE_VIABILITY_NOT_ISOLATED_SELECTION',
                witnesses=observed, demonstrated_in_log=bool(observed),
                authenticated_execution=False)


def verify_fixture(seed, variant, food_a, food_b, events, births, summary):
    result = _interpret(seed, variant, food_a, food_b, events, births, summary)
    return dict(result, scope='SYNTHETIC_FIXTURE_NOT_SCIENTIFIC_EVIDENCE')


def verify_panel(request, manifest, records):
    plan = prepare_request(request)
    seeds = validate_opening(plan, manifest)
    if type(records) is not list or len(records) != 34:
        raise ValueError('all34 worlds required; no exclusions')
    expected = {(slot['role'], slot['context_index']) for slot in plan['slots']}
    results = {}
    for record in records:
        if type(record) is not dict or set(record) != {'role', 'context_index', 'events', 'births', 'summary'}:
            raise ValueError('exact world record required')
        if type(record['context_index']) is not int:
            raise ValueError('exact context index required')
        key = (record['role'], record['context_index'])
        if key not in expected or key in results:
            raise ValueError('duplicate, unauthorized or swapped world')
        variant, food_a, food_b = ARMS[key[0]]
        results[key] = _interpret(seeds[key[1]], variant, food_a, food_b,
                                  record['events'], record['births'], record['summary'])
    if set(results) != expected:
        raise ValueError('incomplete denominator')
    deltas = [(results['mixed_mutating', i]['births'] - results['mixed_faithful', 0]['births']) -
              (results['all_a_mutating', i]['births'] - results['all_a_faithful', 0]['births']) for i in range(16)]
    return dict(scope='LOG_CONSISTENCY_ONLY_NOT_NATIVE_AUTHENTICATION',
                authenticated_execution=False, deltas=deltas,
                positive=sum(value > 0 for value in deltas),
                primary_positive=sum(value > 0 for value in deltas) >= 12,
                scientific_selection_claim=False,
                mechanistic=[dict(role=key[0], context_index=key[1], **mechanism(value))
                             for key, value in results.items()],
                worlds=[dict(role=key[0], context_index=key[1], **value)
                        for key, value in results.items()])
