"""Thin single-transition wrapper over unchanged64 operations.

No execution admission is conveyed by this module. The finite external runner
must bind the reviewed source/configuration and exclusive operator lock.
"""
from experiments import digital_renewable64 as kernel
from experiments import digital_renewable64_interpret as natural_full
from experiments.digital_birthcontext67_transition import (
    VERSION, GENERATIONS, ROLES, actor_record, slots_from_audited, transition)


def _replay_to_birth(natural, slot):
    world = kernel.World(natural['seed'], 'mutating', 'ancestor', 'renewed')
    while world.tick < slot['tick']:
        assert world.step()
    assert world.events == natural['final']['events'][:slot['tick']]
    assert kernel.h(world.snapshot(False)) == slot['post_step_hash']
    return world


def _apply(world, slot, natural_hash, role):
    after, record = transition(world.snapshot(), slot, natural_hash, role)
    # Diagnostic metadata stays outside __dict__; every other physical value
    # remains identical, including material IDs and natural prefix events.
    daughter = world.entities[slot['target']]
    daughter['code'] = actor_record(after['entities'], slot['target'])['code']
    assert world.snapshot() == after
    world.check()
    return record


def history(natural, generation, role):
    assert type(generation) is int and generation in GENERATIONS and role in ROLES
    assert natural['mode'] == 'mutating' and natural['fuel_mode'] == 'renewed'
    assert natural['route'] == 'ancestor'
    assert sum(natural['genesis_program'], []) == natural_full.ANCESTOR_WORDS
    summary = natural_full.audit(natural)  # Full ancestry first, not winner screening.
    slot = slots_from_audited(natural, summary)[generation]
    result = dict(version=VERSION, natural=natural, branch=None,
                  generation=generation, role=role, transition=None)
    if slot is None:
        return result
    # Genesis restore independently repeats the complete paid prefix and edit.
    world = _replay_to_birth(natural, slot)
    record = _apply(world, slot, natural['hash'], role)
    restored = _replay_to_birth(natural, slot)
    assert _apply(restored, slot, natural['hash'], role) == record
    assert world.snapshot() == restored.snapshot()
    # Standard tick64 checkpoint can precede the fork; preserve that natural
    # checkpoint. For earlier forks, bind the actual edited tick64 snapshot.
    checkpoint = natural['checkpoint']
    if world.tick <= 64:
        while world.tick < 64 and world.step():
            assert restored.step()
        assert world.snapshot() == restored.snapshot()
        checkpoint = world.snapshot()
    final = world.run(4096); assert final == restored.run(4096)
    branch = dict(natural, checkpoint=checkpoint, final=final, hash=kernel.h(final))
    if role == 'sham':
        assert branch == natural
    result.update(branch=branch, transition=record)
    return result
