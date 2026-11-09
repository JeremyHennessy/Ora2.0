"""AL02 depletion checkpoint DATA codec. It neither imports nor creates a World."""

import hashlib
import json
import math
from random import Random


VERSION = 'AL02-DEPLETION-CHECKPOINT-v1'
MAX_BYTES = 2 * 1024 * 1024  # Codec bound, not a physical output grant.
COUNTERS = ('deaths', 'max_population_seen', 'mutations_written',
            'failed_divisions', 'failed_copy', 'energy_residual_max',
            'material_residual_max')
FIELDS = {'config_sha256', 'tick', 'last_actor', 'next_organism_id',
          'organisms', 'free_units', 'food_a', 'food_b', 'escrow_b', 'heat',
          'events', 'births', 'counters'}
ACTOR_FIELDS = {'organism_id', 'tape', 'energy', 'generation', 'parent_id',
                'born_tick', 'pc', 'read_head', 'nursery', 'nursery_write_ids'}


def _require(condition, message):
    if not condition:
        raise ValueError(message)


def _integer(value, low, high):
    return type(value) is int and low <= value <= high


def _canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'),
                      ensure_ascii=True, allow_nan=False).encode('ascii')


def _history_value(value, depth=0):
    """Reject values JSON would coerce instead of restoring exactly."""
    _require(depth <= 16, 'History nesting exceeds codec bound')
    if type(value) is dict:
        for key, item in value.items():
            _require(type(key) is str, 'History keys must be strings')
            _history_value(item, depth + 1)
    elif type(value) is list:
        for item in value:
            _history_value(item, depth + 1)
    else:
        _require(value is None or type(value) in (str, int, bool) or
                 (type(value) is float and math.isfinite(value)), 'Invalid history value')


def _rng_from_json(value):
    _require(type(value) is list and len(value) == 3 and type(value[0]) is int
             and value[0] == 3, 'Expected version 3 Random state')
    _, words, spare = value
    _require(type(words) is list and len(words) == 625 and
             all(_integer(word, 0, 2**32 - 1) for word in words[:-1]) and
             any(words[:-1]) and _integer(words[-1], 0, 624), 'Invalid MT state')
    _require(spare is None or (type(spare) is float and math.isfinite(spare)),
             'Invalid cached Gaussian')
    # Allocate the instance without __init__/seed. setstate restores all words
    # and the cached Gaussian before any draw is possible.
    rng = Random.__new__(Random)
    rng.setstate((3, tuple(words), spare))
    return rng


def _validate(state):
    _require(type(state) is dict and set(state) == FIELDS, 'Checkpoint fields differ')
    pin = state['config_sha256']
    _require(type(pin) is str and len(pin) == 64 and
             all(c in '0123456789abcdef' for c in pin), 'Invalid configuration pin')
    tick, next_id = state['tick'], state['next_organism_id']
    _require(_integer(tick, 0, 600) and _integer(next_id, 1, 601) and
             _integer(state['last_actor'], -1, next_id - 1), 'Invalid scheduler state')
    _require((tick == 0) == (state['last_actor'] == -1), 'Scheduler tick mismatch')
    a, b, escrow, heat = (state[key] for key in ('food_a', 'food_b', 'escrow_b', 'heat'))
    _require(_integer(a, 0, 12) and _integer(b, 0, 18) and
             _integer(escrow, 0, 18) and _integer(heat, 0, 604), 'Invalid resources')
    actors, free = state['organisms'], state['free_units']
    _require(type(actors) is list and len(actors) <= 64 and type(free) is list,
             'Invalid organism/material collections')
    units, ids, energy = list(free), set(), heat + 20 * (a + b + escrow)
    for actor in actors:
        _require(type(actor) is dict and set(actor) == ACTOR_FIELDS, 'Invalid actor fields')
        identity = actor['organism_id']
        _require(_integer(identity, 0, next_id - 1) and identity not in ids and
                 _integer(actor['energy'], 1, 604) and _integer(actor['born_tick'], 0, tick) and
                 _integer(actor['generation'], 0, identity) and _integer(actor['pc'], 0, 4),
                 'Invalid actor identity or state')
        parent = actor['parent_id']
        _require(parent is None if identity == 0 else _integer(parent, 0, identity - 1),
                 'Invalid parent identity')
        ids.add(identity)
        energy += actor['energy']
        tape, nursery, writes = (actor[key] for key in ('tape', 'nursery', 'nursery_write_ids'))
        _require(type(tape) is list and len(tape) == 4 and type(nursery) is list and
                 _integer(actor['read_head'], 0, 4) and len(nursery) == actor['read_head'] and
                 type(writes) is list and len(writes) == len(nursery) and
                 all(_integer(i, 0, 1800) for i in writes), 'Invalid tape or nursery')
        for gene in tape + nursery:
            _require(type(gene) is list and len(gene) == 2 and
                     _integer(gene[0], 0, 5), 'Invalid gene')
            units.append(gene[1])
    _require(all(_integer(unit, 0, 255) for unit in units) and
             sorted(units) == list(range(256)), 'Material conservation failed')
    _require(energy == 604, 'Energy conservation failed')
    events, births, counters = state['events'], state['births'], state['counters']
    _require(type(events) is list and 1 <= len(events) <= 1801 and
             type(births) is list and len(births) == next_id - 1 and
             all(type(row) is dict for row in events + births), 'Invalid history collections')
    _history_value(events)
    _history_value(births)
    _require(type(counters) is dict and set(counters) == set(COUNTERS) and
             all(_integer(v, 0, 1801) for v in counters.values()), 'Invalid counters')
    # The independent history verifier must authenticate the EXEC records.
    eaten = sum(e.get('kind') == 'EXEC' and e.get('outcome') == 'ate_b' for e in events)
    _require(eaten + b + escrow == 18, 'B consumption/escrow mismatch')
    return eaten


def encode_checkpoint(state, rng):
    """Encode the explicit DATA projection and the actual stdlib RNG state."""
    _validate(state)
    _require(type(rng) is Random, 'Expected standard-library Random')
    version, words, spare = rng.getstate()
    value = [version, list(words), spare]
    _rng_from_json(value)
    raw = _canonical({'version': VERSION, 'state': state, 'rng': value})
    _require(len(raw) <= MAX_BYTES, 'Checkpoint exceeds codec bound')
    return raw


def restore_checkpoint(raw, expected_sha256):
    """Restore detached DATA and RNG, under a caller-supplied trusted pin."""
    _require(type(raw) is bytes and 0 < len(raw) <= MAX_BYTES, 'Invalid checkpoint extent')
    _require(hashlib.sha256(raw).hexdigest() == expected_sha256, 'Checkpoint pin mismatch')
    value = json.loads(raw.decode('ascii'))
    _require(type(value) is dict and set(value) == {'version', 'state', 'rng'} and
             value['version'] == VERSION and _canonical(value) == raw,
             'Invalid checkpoint format')
    _validate(value['state'])
    return value['state'], _rng_from_json(value['rng'])


def sequester_b(state):
    """Transfer stock on detached DATA after an independently settled boundary.

    Caller must verify the paid last-A transition and completed instruction.
    This operation changes no history, actor, scheduler or RNG fields.
    """
    eaten = _validate(state)
    _require(state['food_a'] == 0 and state['escrow_b'] == 0, 'Invalid escrow source')
    result = json.loads(_canonical(state))
    result['escrow_b'], result['food_b'] = result['food_b'], 0
    _require(_validate(result) == eaten, 'Escrow changed consumption')
    return result
