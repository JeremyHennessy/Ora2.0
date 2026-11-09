"""AL02 escrow continuation v1. No standalone entry point or execution grant."""

from hashlib import sha256
from pathlib import Path

from experiments import executed_heredity as frozen
from experiments.al02_depletion_checkpoint import (
    _canonical, _require, restore_checkpoint, sequester_b,
)
from experiments.al02_depletion_projection import SOURCE_SHA256, require_depletion

VERSION = 'AL02-ESCROW-CONTINUATION-v1'


def check_ledger(state):
    """Apply original live invariants with an explicit inaccessible energy compartment."""
    escrow = state.escrow_b
    if type(escrow) is not int or not 0 <= escrow <= state.initial_food_b:
        raise AssertionError('Invalid B escrow')
    if escrow and state.food_b:
        raise AssertionError('Escrow branch has accessible B')
    units = [gene.material_unit for actor in state.organisms.values()
             for gene in (*actor.tape, *actor.nursery)] + list(state.free_units)
    if sorted(units) != list(range(state.material_units)):
        raise AssertionError('Material units duplicated/lost')
    if any(actor.energy < 0 for actor in state.organisms.values()):
        raise AssertionError('Negative organism energy')
    if min(state.food_a, state.food_b, state.heat) < 0:
        raise AssertionError('Negative energy compartment')
    material = len(units) - state.genesis_material
    energy = (sum(actor.energy for actor in state.organisms.values()) + state.heat
              + frozen.ENERGY_PER_FOOD * (state.food_a + state.food_b + escrow)
              - state.genesis_energy)
    state.material_residual_max = max(state.material_residual_max, abs(material))
    state.energy_residual_max = max(state.energy_residual_max, abs(energy))
    if material or energy:
        raise AssertionError(f'Resource violation: material {material}, energy {energy}')
    if len(state.organisms) > state.population_limit:
        raise AssertionError('Population exceeded physical cap')
    authorized = {0} | {birth['child_id'] for birth in state.births}
    if not state.organisms.keys() <= authorized:
        raise AssertionError('Unregistered live organism without executed birth')
    if any(identity != actor.organism_id or (identity and actor.parent_id is None)
           for identity, actor in state.organisms.items()):
        raise AssertionError('Unverified descendant ancestry')
    return material, energy


def b_accounting(state):
    meals = sum(e['kind'] == 'EXEC' and e.get('outcome') == 'ate_b' for e in state.events)
    if meals + state.food_b + state.escrow_b != state.initial_food_b:
        raise AssertionError('B meals, accessible stock and escrow do not reconcile')
    return dict(remaining_food_b=state.food_b, escrow_b=state.escrow_b, consumed_food_b=meals)


class EscrowContinuation(frozen.World):
    """Reuse frozen dispatch and replace only its ledger and reported B accounting."""

    def __init__(self):
        raise TypeError('Restore only from a settled common checkpoint')

    @classmethod
    def restore(cls, raw, pin, seed, role):
        _require(role in ('accessible', 'sequestered'), 'Unknown branch role')
        _require(type(seed) is int and 0 <= seed < 2**64, 'Invalid committed seed')
        source = Path(frozen.__file__).read_bytes().replace(b'\r\n', b'\n')
        _require(sha256(source).hexdigest() == SOURCE_SHA256, 'Unexpected simulator source')
        state, rng = restore_checkpoint(raw, pin)
        require_depletion(state)
        config = dict(seed=seed, variant='mutating', copy_enabled=True, mutation_rate=0.08,
                      material_units=256, population_limit=64, genesis_energy=604,
                      genesis_material=256, initial_food_a=12, initial_food_b=18)
        _require(sha256(_canonical(config)).hexdigest() == state['config_sha256'],
                 'Configuration pin mismatch')
        if role == 'sequestered':
            state = sequester_b(state)
        obj = object.__new__(cls)
        vars(obj).update(config, state['counters'])
        for key in ('food_a', 'food_b', 'escrow_b', 'heat', 'last_actor',
                    'next_organism_id', 'events', 'births'):
            setattr(obj, key, state[key])
        obj.rng = rng
        obj.tick_count = state['tick']
        obj.free_units = set(state['free_units'])
        obj.organisms = {}
        for actor in state['organisms']:
            actor['tape'] = tuple(frozen.Gene(*gene) for gene in actor['tape'])
            actor['nursery'] = [frozen.Gene(*gene) for gene in actor['nursery']]
            obj.organisms[actor['organism_id']] = frozen.Organism(**actor)
        check_ledger(obj)
        b_accounting(obj)
        return obj

    def assert_invariants(self):
        return check_ledger(self)

    def run(self, maximum_ticks=frozen.MAX_STEPS):
        _require(type(maximum_ticks) is int and 0 <= maximum_ticks <= frozen.MAX_STEPS,
                 'Invalid absolute continuation horizon')
        summary = super().run(maximum_ticks)
        summary.update(b_accounting(self))
        return summary
