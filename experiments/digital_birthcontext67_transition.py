"""Data-only birth-context binding. No producer import or organism execution.

Partial-state helpers are NOT full ancestry proof. Callers must first complete
the unchanged natural-history audit and independently replay the birth prefix.
"""
from experiments.digital_renewable64_interpret import body, clone, h

VERSION = 'DIGITAL-BIRTH-CONTEXT-67-v1'
ROLES = ('sham', 'remove_copy_mutations')
GENERATIONS = (1, 2, 3)


def integer(value, minimum=0):
    assert type(value) is int and value >= minimum
    return value


def actor_record(mapping, identity):
    integer(identity)
    assert type(mapping) is dict
    normalized = {}
    for key, value in mapping.items():
        if type(key) is int:
            integer(key); number = key
        else:
            assert type(key) is str and key.isascii() and key.isdecimal()
            number = int(key); assert str(number) == key
        assert number not in normalized
        normalized[number] = value
    assert identity in normalized
    return normalized[identity]


def slots_from_audited(row, summary):
    """Neutral chronological roster; does not construct or execute a World."""
    assert summary['verified'] is True and summary['seed'] == row['seed']
    assert row['hash'] == h(row['final'])
    certificates = {}; slots = {generation: None for generation in GENERATIONS}
    for event in row['final']['events']:
        for word in event.get('writes', []):
            identity = integer(word['write_id'])
            assert identity not in certificates
            certificates[identity] = dict(word, actor=event['actor'])
        if 'birth' not in event:
            continue
        birth = event['birth']; child = birth['child']; generation = child['generation']
        words = [certificates[identity] for identity in birth['write_ids']]
        assert len(words) == 27 and len(set(birth['write_ids'])) == 27
        assert all(w['actor'] == event['actor'] and w['index'] == i for i, w in enumerate(words))
        assert child['code'] == [[w['value'], w['unit']] for w in words]
        if generation in slots and slots[generation] is None:
            slots[generation] = dict(target=child['id'], parent=event['actor'],
                generation=generation, tick=event['tick'], certificates=clone(words),
                born_code=clone(child['code']), post_step_hash=event['state_hash'])
    return slots


def transition(state, slot, natural_hash, role):
    """Derive the sole allowed edit from paid temporal COPY values, never DIV code."""
    assert role in ROLES and type(natural_hash) is str and len(natural_hash) == 64
    assert type(slot) is dict and slot['generation'] in GENERATIONS
    target = integer(slot['target'], 1); integer(slot['parent']); integer(slot['tick'], 1)
    assert slot['tick'] <= 4096 and state['tick'] == slot['tick']
    assert state['mode'] == 'mutating' and state['fuel_mode'] == 'renewed'
    assert h({k: v for k, v in state.items() if k != 'events'}) == slot['post_step_hash']
    child = actor_record(state['entities'], target)
    assert actor_record(state['turns'], target) == 0
    assert child['parent'] == slot['parent'] and child['generation'] == slot['generation']
    assert child['id'] == target and child['code'] == slot['born_code']
    assert len(child['code']) == 27 and len(child['state_units']) == 16
    assert child == body(target, slot['parent'], slot['generation'],
                         child['code'], child['state_units'], child['pos'])
    words = slot['certificates']; assert type(words) is list and len(words) == 27
    ids = set()
    for index, word in enumerate(words):
        identity = integer(word['write_id']); assert identity not in ids; ids.add(identity)
        assert word['index'] == index and word['actor'] == slot['parent']
        assert type(word['mutated']) is bool
        for key in ('value', 'source_value'):
            integer(word[key]); assert word[key] < 32
        integer(word['source_unit']); integer(word['unit']); integer(word['tick'], 1)
        assert word['tick'] < slot['tick']
        assert word['mutated'] == (word['value'] != word['source_value'])
        draw = int(h([state['seed'], 'mutation', identity])[:16], 16)
        expected = ((word['source_value'] + 1 + (draw // 100) % 31) % 32
                    if draw % 100 < 8 else word['source_value'])
        assert word['value'] == expected
        assert child['code'][index] == [word['value'], word['unit']]
    after = clone(state); daughter = actor_record(after['entities'], target)
    mask = [i for i, word in enumerate(words) if word['mutated']]
    if role == 'remove_copy_mutations':
        for cell, word in zip(daughter['code'], words):
            cell[0] = word['source_value']
    record = dict(version=VERSION, role=role, natural_history_hash=natural_hash,
        target=target, parent=slot['parent'], generation=slot['generation'], tick=slot['tick'],
        before_hash=h(state), after_hash=h(after), mutation_mask=mask,
        before_code=clone(child['code']), after_code=clone(daughter['code']),
        certificates=clone(words), assistance='DECLARED_COUNTERFACTUAL_NOT_NATURAL_REPAIR')
    return after, record


def validate_transition(before, after, record, slot, natural_hash, role):
    expected, binding = transition(before, slot, natural_hash, role)
    assert after == expected and record == binding
    return True
