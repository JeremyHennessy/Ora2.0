"""Single fixed-context AL02 driver. No CLI or automatic admission."""

from hashlib import sha256

from experiments import executed_heredity as frozen
from experiments.al02_depletion_checkpoint import (
    ACTOR_FIELDS, COUNTERS, _canonical, encode_checkpoint,
)
from experiments.al02_depletion_producer import EscrowContinuation
from experiments.al02_depletion_projection import project_depletion
from experiments.al02_depletion_suffix import verify_pair

CONTEXT = (
    'ORA-AL02-EXPLORATORY-ONEPAIR|2026-11-09T11:50:03Z|'
    '0d1ed45b71909879bbaad2b7c1e00269a3a41f5c|ordinary-mutating-ancestor|12A-18B'
)
CONTEXT_SHA256 = '71bb1e2c35ff536900807c5c0ee86d30c13722b85291a8e8f086c0c62dc934b8'
SEED = 8195177122164069225
ROLES = ('accessible', 'sequestered')
MAX_OUTPUT = 1024 * 1024


def check_context(context, digest, seed):
    if (context != CONTEXT or digest != CONTEXT_SHA256 or type(seed) is not int
            or seed != SEED or sha256(context.encode('utf-8')).hexdigest() != digest
            or int(digest[:16], 16) != seed):
        raise ValueError('Fixed context identity mismatch')


def terminal_checkpoint(world, config_pin):
    """Only an untriggered terminal prefix can take this path."""
    if world.food_a <= 0 or (world.organisms and world.tick_count != frozen.MAX_STEPS):
        raise ValueError('Not an untriggered terminal prefix')
    actors = []
    for identity, actor in sorted(world.organisms.items()):
        data = {key: getattr(actor, key) for key in ACTOR_FIELDS}
        if identity != data['organism_id']:
            raise ValueError('Actor key mismatch')
        for key in ('tape', 'nursery'):
            data[key] = [[gene.op, gene.material_unit] for gene in data[key]]
        actors.append(data)
    state = dict(config_sha256=config_pin, tick=world.tick_count,
                 last_actor=world.last_actor, next_organism_id=world.next_organism_id,
                 organisms=actors, free_units=sorted(world.free_units), food_a=world.food_a,
                 food_b=world.food_b, escrow_b=0, heat=world.heat,
                 events=world.events, births=world.births,
                 counters={key: getattr(world, key) for key in COUNTERS})
    return encode_checkpoint(state, world.rng)


def observe_events(world, phase, save_event, start=0):
    """Copy emitted evidence without changing the frozen transition methods."""
    for event in world.events[start:]:
        save_event(phase, event)
    emit = world.emit

    def observed_emit(*args, **kwargs):
        event_id = emit(*args, **kwargs)
        save_event(phase, world.events[event_id])
        return event_id

    world.emit = observed_emit


def produce(context, digest, seed, source_bytes, *, save_event=None):
    """Worker entry point. The external supervisor must authorize launch first."""
    check_context(context, digest, seed)
    from experiments.al02_depletion_projection import SOURCE_SHA256
    if sha256(source_bytes.replace(b'\r\n', b'\n')).hexdigest() != SOURCE_SHA256:
        raise ValueError('Frozen source mismatch')
    config = dict(seed=seed, variant='mutating', copy_enabled=True, mutation_rate=0.08,
                  material_units=256, population_limit=64, genesis_energy=604,
                  genesis_material=256, initial_food_a=12, initial_food_b=18)
    config_pin = sha256(_canonical(config)).hexdigest()
    world = frozen.World(seed)
    if save_event is not None:
        observe_events(world, "prefix", save_event)
    while world.organisms and world.tick_count < frozen.MAX_STEPS and world.food_a:
        world.execute_one()
    triggered = world.food_a == 0
    raw = (project_depletion(world, source_bytes, config_pin) if triggered
           else terminal_checkpoint(world, config_pin))
    pin = sha256(raw).hexdigest()
    branches = {}
    for role in ROLES:
        events = []
        if triggered:
            branch = EscrowContinuation.restore(raw, pin, seed, role)
            if save_event is not None:
                observe_events(branch, role, save_event, len(world.events))
            branch.run()
            events = branch.events[len(world.events):]
        branches[role] = dict(role=role, prefix_sha256=pin, events=events)
    data = _canonical(dict(context_sha256=digest, checkpoint=raw.decode('ascii'),
                           checkpoint_sha256=pin, branches=branches))
    if len(data) > MAX_OUTPUT:
        raise ValueError('Raw evidence exceeds worker output budget')
    return data


def verify(raw):
    """Consume preserved raw bytes after worker closure, independently of producer state."""
    import json
    if type(raw) is not bytes or not 0 < len(raw) <= MAX_OUTPUT:
        raise ValueError('Raw evidence extent invalid')
    data = json.loads(raw.decode('ascii'))
    if (type(data) is not dict
            or set(data) != {'context_sha256', 'checkpoint', 'checkpoint_sha256', 'branches'}
            or _canonical(data) != raw or data['context_sha256'] != CONTEXT_SHA256
            or type(data['checkpoint']) is not str):
        raise ValueError('Raw evidence format or context invalid')
    return verify_pair(SEED, data['checkpoint'].encode('ascii'),
                       data['checkpoint_sha256'], data['branches'])
