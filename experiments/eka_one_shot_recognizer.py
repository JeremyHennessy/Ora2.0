"""Inert recognition of the accepted November 1 fixed one-shot layout.

No World, seed sampler, interpreter, launch or scientific admission. A code
match and consistent COPY records do not authenticate an ancestry or its costs.
The independently qualified full-history referee remains required.
"""

DEFINITION = 'NOV1-ONE-SHOT-FIXED-LAYOUT-v1'
OPCODES = (6, 1, 8, 7, 4, 6, 10, 12, 7)


def _require(condition, message):
    if not condition:
        raise ValueError(message)


def _integer(value, minimum, maximum):
    _require(type(value) is int and minimum <= value <= maximum,
             'Expected an integer within the source bounds')
    return value


def _executed_instruction(event, opcode):
    decoded = event['decoded']
    _require(type(decoded) is list and len(decoded) == 3, 'Malformed decoded instruction')
    for value in decoded:
        _integer(value, 0, 31)
    _require(decoded[0] == opcode, 'Unexpected event opcode')
    _require(event.get('outcome') == 'executed', 'Event was not successful')


def recognize_values(values):
    """Return register roles for this fixed class, or None for another code.

    This is intentionally narrower than all equivalent learning algorithms.
    SET aliases are exactly 1 and 17 from the accepted origin-distance audit.
    No program image or successful organism is constructed or executed here.
    """
    _require(type(values) is list and len(values) == 27, 'Expected 27 words')
    for value in values:
        _integer(value, 0, 31)
    rows = [values[index:index + 3] for index in range(0, 27, 3)]
    if tuple(row[0] for row in rows) != OPCODES:
        return None
    for port in (0, 1):
        feedback = 1 - port
        if (rows[0][1] % 2 == port and
                rows[1][1] % 2 == feedback and
                rows[2][1] % 2 == feedback and rows[2][2] % 9 == 4 and
                rows[3][2] % 9 == 5 and
                rows[4][1] % 2 == port and rows[4][2] in (1, 17) and
                rows[5][1] % 2 == port and rows[8][2] % 9 == 5):
            return {'definition': DEFINITION, 'port_register': port,
                    'feedback_register': feedback}
    return None


def inspect_birth_bindings(birth_event, copy_events):
    """Check a literal birth and its nine supplied successful COPY records.

    Records can be fabricated consistently, so this function ALWAYS leaves
    ancestry unauthenticated and registered eligibility unevaluated. It does
    not derive mutation hashes, replay source states, prove payment, inspect
    future outcomes, or trust a caller's 'verified' flag.
    """
    parent = _integer(birth_event['actor'], 0, 4095)
    birth_tick = _integer(birth_event['tick'], 1, 4096)
    _executed_instruction(birth_event, 12)
    birth = birth_event['birth']
    child = birth['child']
    _integer(child['id'], parent + 1, 4096)
    _require(type(child['parent']) is int and child['parent'] == parent,
             'Child parent differs')
    _integer(child['generation'], 1, 4096)
    position = _integer(child['pos'], 0, 3)
    for field, expected in (('registers', [0, 0]), ('memory', [0] * 8),
                            ('pc', 0), ('cue', 0), ('feedback', 0),
                            ('inbox', None), ('energy', 12), ('nursery', [])):
        _require(child[field] == expected and type(child[field]) is type(expected),
                 'Newborn state differs')
    _require(all(type(value) is int for value in child['registers'] + child['memory']),
             'Newborn numeric state must contain integers')
    code = child['code']
    _require(type(code) is list and len(code) == 27, 'Expected 27 code units')
    values, units = [], []
    for word in code:
        _require(type(word) is list and len(word) == 2, 'Malformed code unit')
        values.append(_integer(word[0], 0, 31))
        units.append(_integer(word[1], 0, 511))
    state_units = child['state_units']
    _require(type(state_units) is list and len(state_units) == 16,
             'Expected 16 state units')
    for unit in state_units:
        _integer(unit, 0, 511)
    _require(len(set(units + state_units)) == 43, 'Repeated body material')
    expected_formation = [dict(unit=unit, value=position if index == 14 else 0,
                               energy=1) for index, unit in enumerate(state_units)]
    _require(all(type(entry[key]) is int for entry in birth['state_formation']
                 for key in ('unit', 'value', 'energy')), 'Malformed formation values')
    _require(birth['state_formation'] == expected_formation and
             type(birth['release_energy']) is int and birth['release_energy'] == 2 and
             type(birth['startup_energy']) is int and birth['startup_energy'] == 12,
             'Formation record differs')
    write_ids = birth['write_ids']
    _require(type(write_ids) is list and len(write_ids) == 27,
             'Expected 27 bound writes')
    for identity in write_ids:
        _integer(identity, 0, 2**64 - 1)
    _require(len(set(write_ids)) == 27, 'Reused write identity')
    _require(write_ids == sorted(write_ids), 'Write identities are not ordered')
    _require(type(copy_events) is list and len(copy_events) == 9,
             'Expected nine successful COPY events')
    previous_tick = 0
    source_units = []
    index = 0
    for event in copy_events:
        tick = _integer(event['tick'], previous_tick + 1, birth_tick - 1)
        previous_tick = tick
        _require(type(event['actor']) is int and event['actor'] == parent,
                 'COPY actor differs')
        _executed_instruction(event, 10)
        writes = event['writes']
        _require(type(writes) is list and len(writes) == 3,
                 'Expected three words per successful COPY')
        for word in writes:
            _require(type(word['index']) is int and word['index'] == index and
                     type(word['tick']) is int and word['tick'] == tick and
                     type(word['write_id']) is int and word['write_id'] == write_ids[index],
                     'COPY index, tick or write binding differs')
            source = _integer(word['source_value'], 0, 31)
            source_units.append(_integer(word['source_unit'], 0, 511))
            _require(word['effective_source'] == 'parent_copy' and
                     type(word['effective_source_value']) is int and
                     word['effective_source_value'] == source,
                     'Not a parent COPY source')
            draw = _integer(word['mutation_draw'], 0, 2**64 - 1)
            expected = (source + 1 + (draw // 100) % 31) % 32 if draw % 100 < 8 else source
            _require(type(word['mutated']) is bool and
                     word['mutated'] == (expected != source), 'Mutation marker differs')
            _require(type(word['value']) is int and word['value'] == expected and
                     type(word['unit']) is int and
                     [word['value'], word['unit']] == code[index],
                     'Child words do not match COPY')
            index += 1
    _require(len(set(source_units)) == 27 and
             set(source_units).isdisjoint(units + state_units),
             'COPY source material overlaps or repeats')
    return {'code_match': recognize_values(values),
            'local_copy_binding_consistent': True,
            'ancestry_authenticated': False,
            'registered_eligibility': 'NOT_EVALUATED'}
