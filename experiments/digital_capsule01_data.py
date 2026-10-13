"""Prepared-data boundary for exact persistence01; not a resume authority.

No World construction, hydration, resource query or transition execution here.
Custody and structural invariants do not authenticate executed history. A separate
literal history/capsule referee and reviewed loader remain required before resume.
The caller must establish safe physical recording before supplying these bytes.
"""
import hashlib
import json

VERSION = 'DIGITAL-EXACT-PERSISTENCE-QUALIFICATION-01-data-v1'
FIELDS = frozenset('inheritance_mode fuel_mode turns offered admitted rejected next_packet seed mode tick last next_id writes constructor_remaining heat formation food free entities events births deaths maximum'.split())
BODY = frozenset('id parent generation code state_units memory registers pc cue feedback inbox pos energy nursery'.split())
WRITE = frozenset('unit value index tick source_unit source_value effective_source effective_source_value mutation_draw write_id mutated'.split())


def require(condition, message):
    if not condition:
        raise ValueError(message)


def integer(value, low, high, name):
    require(type(value) is int and low <= value <= high, name)
    return value


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=True).encode('ascii')


def digest(value):
    return hashlib.sha256(canonical(value)).hexdigest()


def pairs(items):
    result = {}
    for key, value in items:
        require(key not in result, 'duplicate JSON key')
        result[key] = value
    return result


def identity(value):
    require(type(value) is dict and set(value) == {'revision', 'source_sha256', 'config_sha256', 'law'}, 'identity fields')
    for key, length in [('revision', 40), ('source_sha256', 64), ('config_sha256', 64)]:
        require(type(value[key]) is str and len(value[key]) == length and all(c in '0123456789abcdef' for c in value[key]), key)
    require(value['law'] == 'DIGITAL-SHARED-LINEAGE-68-v1', 'law identity')


def id_map(value, high, name):
    require(type(value) is dict, name)
    result = {}
    for key, item in value.items():
        require(type(key) is str and key and all(c in '0123456789' for c in key) and (key == '0' or key[0] != '0'), name + ' canonical ID')
        require(len(key) <= 10, name + ' ID length')
        index = integer(int(key), 0, high, name + ' ID range')
        require(index not in result, name + ' duplicate ID')
        result[index] = item
    return result


def vector(value, count, high, name):
    require(type(value) is list and len(value) == count, name)
    for item in value:
        integer(item, 0, high, name)


def data_types(value, depth=0):
    require(depth <= 24, 'state nesting')
    if type(value) is dict:
        require(all(type(k) is str for k in value), 'data key')
        for item in value.values():
            data_types(item, depth + 1)
    elif type(value) is list:
        for item in value:
            data_types(item, depth + 1)
    else:
        require(value is None or type(value) in (int, str, bool), 'noninteger data')


def validate_state(state):
    """Return fresh maps with integer IDs; NEVER authenticate or hydrate a World."""
    require(type(state) is dict and set(state) == FIELDS, 'complete state fields')
    data_types(state)
    require(state['inheritance_mode'] in ('parent_copy', 'ancestor_copy'), 'inheritance mode')
    require(state['mode'] in ('faithful', 'mutating'), 'mode')
    require(state['mode'] == 'mutating' or state['inheritance_mode'] == 'parent_copy', 'copy configuration')
    require(state['fuel_mode'] == 'renewed', 'fuel mode')
    integer(state['seed'], 0, 2**63 - 1, 'seed')
    tick = integer(state['tick'], 0, 512, 'finite endpoint')
    next_id = integer(state['next_id'], 1, 513, 'next entity')
    integer(state['last'], -1, next_id - 1, 'scheduler ID')
    for key in ('offered', 'admitted', 'rejected'):
        integer(state[key], 0, 128, key)
    require(state['offered'] == state['admitted'] + state['rejected'], 'inflow ledger')
    require(state['offered'] == 16 * (tick // 64), 'inflow schedule')
    require(integer(state['next_packet'], 64, 192, 'next packet') == 64 + state['offered'], 'packet cursor')
    integer(state['writes'], 0, 3 * tick, 'write cursor')
    integer(state['births'], 0, tick, 'birth count')
    integer(state['deaths'], 0, tick + 1, 'death count')
    integer(state['maximum'], 1, 32, 'population maximum')
    integer(state['constructor_remaining'], 0, 128, 'constructor reserve')
    integer(state['heat'], 0, 3980, 'heat')
    turns = id_map(state['turns'], next_id - 1, 'turns')
    entities = id_map(state['entities'], next_id - 1, 'entities')
    food = id_map(state['food'], state['next_packet'] - 1, 'food')
    require(set(turns) == set(range(next_id)), 'complete actor identities')
    require(len(entities) <= state['maximum'] and len(entities) == 1 + state['births'] - state['deaths'], 'population counts')
    require(next_id == state['births'] + 1, 'birth identity cursor')
    for turn in turns.values():
        integer(turn, 0, 256, 'own turns')
    require(sum(turns.values()) == tick, 'total turns')
    require(type(state['free']) is list, 'free material')
    units = list(state['free'])
    for unit in units:
        integer(unit, 0, 511, 'free unit')
    require(units == sorted(set(units)), 'free ordering/duplicates')
    energy = 0
    for actor, body in entities.items():
        require(type(body) is dict and set(body) == BODY, 'body fields')
        require(integer(body['id'], 0, next_id - 1, 'body ID') == actor and turns[actor] < 256, 'live actor')
        if actor == 0:
            require(body['parent'] is None and integer(body['generation'], 0, 0, 'founder generation') == 0, 'founder lineage')
        else:
            integer(body['parent'], 0, actor - 1, 'parent')
            integer(body['generation'], 1, actor, 'generation')
        code = body['code']
        require(type(code) is list and 3 <= len(code) <= 96 and len(code) % 3 == 0, 'program shape')
        for cell in code:
            require(type(cell) is list and len(cell) == 2, 'code cell')
            integer(cell[0], 0, 31, 'code value'); units.append(integer(cell[1], 0, 511, 'code unit'))
        vector(body['state_units'], 16, 511, 'state units'); units.extend(body['state_units'])
        vector(body['memory'], 8, 15, 'memory'); vector(body['registers'], 2, 15, 'registers')
        integer(body['pc'], 0, len(code) // 3 - 1, 'PC')
        integer(body['cue'], 0, 3, 'cue'); integer(body['feedback'], 0, 1, 'feedback')
        if body['inbox'] is not None:
            integer(body['inbox'], 0, 15, 'inbox')
        integer(body['pos'], 0, 3, 'position')
        energy += integer(body['energy'], 1, 64, 'live energy')
        nursery = body['nursery']
        require(type(nursery) is list and len(nursery) <= len(code) and len(nursery) % 3 == 0, 'nursery shape')
        for index, write in enumerate(nursery):
            require(type(write) is dict and set(write) == WRITE, 'nursery fields')
            require(integer(write['index'], 0, len(code) - 1, 'copy index') == index, 'nursery order')
            units.append(integer(write['unit'], 0, 511, 'nursery unit'))
            integer(write['source_unit'], 0, 511, 'source unit')
            for key in ('value', 'source_value', 'effective_source_value'):
                integer(write[key], 0, 31, key)
            integer(write['tick'], 1, tick, 'copy tick')
            integer(write['write_id'], 0, state['writes'] - 1, 'write ID')
            integer(write['mutation_draw'], 0, 2**64 - 1, 'mutation draw')
            require(type(write['mutated']) is bool and write['effective_source'] == state['inheritance_mode'], 'copy metadata')
    require(sorted(units) == list(range(512)), 'material ownership partition')
    site_counts = [0] * 4
    for packet in food.values():
        require(type(packet) is list and len(packet) == 2, 'packet shape')
        site_counts[integer(packet[0], 0, 3, 'packet site')] += 1
        integer(packet[1], 0, 1, 'packet kind')
    require(max(site_counts) <= 32, 'site cap')
    require(energy + state['constructor_remaining'] + state['heat'] + 20 * len(food) == 1420 + 20 * state['admitted'], 'energy ledger')
    formation = state['formation']
    require(type(formation) is list and len(formation) == 43, 'formation shape')
    for index, cell in enumerate(formation):
        require(type(cell) is dict and set(cell) == {'unit', 'value', 'energy', 'assistance'}, 'formation fields')
        require(integer(cell['unit'], 0, 42, 'formation unit') == index and type(cell['energy']) is int and cell['energy'] == 1, 'formation ledger')
        integer(cell['value'], 0, 31 if index < 27 else 0, 'formation value')
        require(cell['assistance'] == 'supplied ancestor assembly', 'formation assistance')
    events = state['events']
    require(type(events) is list and len(events) == tick, 'complete event extent')
    counts = {actor: 0 for actor in turns}
    for index, event in enumerate(events):
        require(type(event) is dict and type(event.get('tick')) is int and event['tick'] == index + 1, 'event order')
        actor = integer(event.get('actor'), 0, next_id - 1, 'event actor'); counts[actor] += 1
    require(counts == turns, 'event turn counters')
    require(state['last'] == (events[-1]['actor'] if events else -1), 'scheduler cursor')
    if events:
        require(events[-1].get('state_hash') == digest({k: v for k, v in state.items() if k != 'events'}), 'last state hash')
    result = dict(state)
    result.update(turns=turns, entities=entities, food=food)
    return result


def decode_prepared(raw, expected_identity, expected_sha256, max_bytes):
    """Validate byte custody first. Result is data, not permission to resume."""
    integer(max_bytes, 1, 32 * 1024**2, 'byte cap')
    require(type(raw) is bytes and 0 < len(raw) <= max_bytes, 'capsule extent')
    require(type(expected_sha256) is str and len(expected_sha256) == 64 and all(c in '0123456789abcdef' for c in expected_sha256), 'expected byte hash')
    require(hashlib.sha256(raw).hexdigest() == expected_sha256, 'capsule byte custody')
    identity(expected_identity)
    try:
        capsule = json.loads(raw.decode('ascii'), object_pairs_hook=pairs, parse_constant=lambda x: (_ for _ in ()).throw(ValueError('nonfinite JSON')))
    except (UnicodeError, json.JSONDecodeError, RecursionError) as error:
        raise ValueError('capsule encoding') from error
    require(type(capsule) is dict and set(capsule) == {'version', 'identity', 'state', 'state_sha256'}, 'capsule fields')
    require(capsule['version'] == VERSION, 'capsule version')
    identity(capsule['identity']); require(capsule['identity'] == expected_identity, 'source/config binding')
    require(canonical(capsule) == raw, 'canonical capsule bytes')
    require(capsule['state_sha256'] == digest(capsule['state']), 'state digest')
    return validate_state(capsule['state'])
