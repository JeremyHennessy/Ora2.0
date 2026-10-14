"""Prospective71 producer data boundary; no history authority. No producer import or organism execution.

Partial-state helpers are NOT full ancestry proof. Callers must first complete
the unchanged natural-history audit and independently replay the birth prefix.
"""
from experiments.digital_sharedlineage68_interpret import body, clone, h, types, ANCESTOR_WORDS
from experiments.digital_pressure71_family import child_source_values, family_from_audited

VERSION = 'DIGITAL-PRESSURE-SELECTION-71-NEWBORN-v2'
ROLES = ('sham', 'ancestor_value_control', 'inherited_source_control')
GENERATIONS = (2, 3)


def validate_provenance(provenance):
    assert type(provenance) is dict and set(provenance)=={'source_sha256','configuration_sha256'}
    for value in provenance.values():
        assert type(value) is str and len(value)==64 and all(c in '0123456789abcdef' for c in value)
    return True

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


def transition(state, slot, natural_hash, role, provenance):
    """Bind paid temporal COPY evidence; only declared newborn code values may intervene."""
    validate_provenance(provenance)
    types(state);types(slot)
    assert role in ROLES
    assert role!='ancestor_value_control' or slot['generation']==2
    assert role!='inherited_source_control' or slot['generation']==3
    assert type(natural_hash) is str and len(natural_hash) == 64
    assert all(c in '0123456789abcdef' for c in natural_hash)
    assert state['inheritance_mode']=='parent_copy'
    dose = integer(state['_dose'], 1); assert dose in (1, 8)
    assert type(slot) is dict and slot['generation'] in GENERATIONS
    integer(slot['generation'],1);integer(state['tick'],1)
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
        assert word['effective_source']=='parent_copy' and word['effective_source_value']==word['source_value']
        integer(word['effective_source_value']);assert word['effective_source_value']<32
        assert word['mutated'] == (word['value'] != word['source_value'])
        draw = int(h([state['seed'], 'mutation', identity])[:16], 16)
        assert type(word['mutation_draw']) is int and word['mutation_draw']==draw
        expected = ((word['source_value'] + 1 + (draw // 100) % 31) % 32
                    if draw % 100 < dose else word['source_value'])
        assert word['value'] == expected
        assert child['code'][index] == [word['value'], word['unit']]
    after = clone(state); daughter = actor_record(after['entities'], target)
    inherited_source = child_source_values(words, dose)
    baseline = ([[v,child['code'][i][1]] for i,v in enumerate(ANCESTOR_WORDS)] if slot['generation']==2 else inherited_source)
    mask = [i for i,cell in enumerate(child['code']) if cell[0]!=baseline[i][0]]
    if role != 'sham':
        for i, cell in enumerate(daughter['code']):
            cell[0] = baseline[i][0]
    record = dict(version=VERSION, dose=dose, role=role, provenance=clone(provenance),natural_history_hash=natural_hash,
        target=target, parent=slot['parent'], generation=slot['generation'], tick=slot['tick'],
        before_hash=h(state), after_hash=h(after), code_value_mask=mask,
        before_code=clone(child['code']), after_code=clone(daughter['code']),
        certificates=clone(words), assistance='DECLARED_COUNTERFACTUAL_NOT_NATURAL_REPAIR')
    return after, record


def validate_transition(before, after, record, slot, natural_hash, role, provenance):
    expected, binding = transition(before, slot, natural_hash, role,provenance)
    assert after == expected and record == binding
    return True
