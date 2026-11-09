"""Isolated projection of settled AL02 producer state. No simulator import."""

from hashlib import sha256

from experiments.al02_depletion_checkpoint import (
    ACTOR_FIELDS, COUNTERS, _canonical, _require, encode_checkpoint,
    restore_checkpoint, sequester_b,
)

# SHA-256 of frozen simulator source with LF newlines.
SOURCE_SHA256 = '90a93013e04e261c936847ffb3b1b0337970d3d81d4bfcbc534886f4336374db'


def project_depletion(world, source_bytes, expected_config_sha256):
    """Project a producer object at a caller-owned, synchronous dispatch boundary."""
    normalized = source_bytes.replace(b'\r\n', b'\n')
    _require(sha256(normalized).hexdigest() == SOURCE_SHA256, 'Unexpected simulator source')
    config = dict(seed=world.seed, variant=world.variant,
                  copy_enabled=world.copy_enabled, mutation_rate=world.mutation_rate,
                  material_units=world.material_units, population_limit=world.population_limit,
                  genesis_energy=world.genesis_energy, genesis_material=world.genesis_material,
                  initial_food_a=world.initial_food_a, initial_food_b=world.initial_food_b)
    _require(type(world.seed) is int and 0 <= world.seed < 2**64 and _canonical(config) == _canonical(dict(
        seed=world.seed, variant='mutating', copy_enabled=True, mutation_rate=0.08,
        material_units=256, population_limit=64, genesis_energy=604, genesis_material=256,
        initial_food_a=12, initial_food_b=18)), 'Unexpected AL02 configuration')
    pin = sha256(_canonical(config)).hexdigest()
    _require(pin == expected_config_sha256, 'Configuration pin mismatch')
    actors = []
    for identity, actor in sorted(world.organisms.items()):
        item = {key: getattr(actor, key) for key in ACTOR_FIELDS}
        _require(type(identity) is int and identity == item['organism_id'], 'Actor key mismatch')
        for field in ('tape', 'nursery'):
            item[field] = [[gene.op, gene.material_unit] for gene in item[field]]
        actors.append(item)
    state = dict(config_sha256=pin, tick=world.tick_count, last_actor=world.last_actor,
                 next_organism_id=world.next_organism_id, organisms=actors,
                 free_units=sorted(world.free_units), food_a=world.food_a, food_b=world.food_b,
                 escrow_b=0, heat=world.heat, events=world.events, births=world.births,
                 counters={key: getattr(world, key) for key in COUNTERS})
    raw = encode_checkpoint(state, world.rng)
    require_depletion(state)
    return raw


def require_depletion(state):
    """Check the boundary shape. Historical provenance is a separate obligation."""
    rows = state['events']
    _require(type(rows) is list and len(rows) >= 2, 'Missing depletion history')
    _require(all(type(row.get('tick')) is int for row in rows)
             and [row['tick'] for row in rows] == sorted(row['tick'] for row in rows)
             and [row['tick'] for row in rows if row.get('kind') in ('GENESIS', 'EXEC', 'FAULT')]
             == list(range(state['tick'] + 1)), 'Incomplete dispatch history')
    last = rows[-1]
    actor = next((a for a in state['organisms'] if a['organism_id'] == state['last_actor']), None)
    _require(actor is not None and state['food_a'] == state['escrow_b'] == 0 and
             state['counters']['energy_residual_max'] == state['counters']['material_residual_max'] == 0,
             'Invalid settled ledger')
    pc = actor['pc'] - 1
    _require(0 <= pc < 4 and actor['tape'][pc][0] == 0, 'Wrong depletion opcode')
    expected = dict(event_id=len(rows)-1, tick=state['tick'], kind='EXEC',
                    organism_id=state['last_actor'], opcode=0, pc_before=pc, pc_after=pc+1,
                    energy_before=actor['energy']-19, energy_after=actor['energy'],
                    read_head_after=actor['read_head'], nursery_bytes_after=len(actor['nursery']),
                    outcome='ate_a', food_a=0, food_b=state['food_b'],
                    population_after_instruction=len(state['organisms']), heat=state['heat'])
    _require(_canonical(last) == _canonical(expected) and expected['energy_before'] >= 1
             and rows[-2]['tick'] < state['tick'], 'Last paid A instruction is unsettled')
    stock = [row['food_a'] for row in rows[:-1] if row['kind'] in ('GENESIS', 'EXEC')]
    _require(stock and stock[0] == 12 and stock[-1] == 1 and min(stock) >= 1,
             'Missing first A depletion')
    _require(all(row['event_id'] == i for i, row in enumerate(rows)), 'Event order mismatch')



def fork_depletion(world, source_bytes, expected_config_sha256):
    """Return the shared commitment and detached DATA for the two branch starts."""
    raw = project_depletion(world, source_bytes, expected_config_sha256)
    pin = sha256(raw).hexdigest()
    state, rng = restore_checkpoint(raw, pin)
    return raw, pin, {'accessible': raw,
                      'sequestered': encode_checkpoint(sequester_b(state), rng)}
