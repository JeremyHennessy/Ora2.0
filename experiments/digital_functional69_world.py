"""Prospective69 single-intervention wrapper over unchanged68 population operations.

No execution admission is conveyed by this module. The finite external runner
must bind the reviewed source/configuration and exclusive operator lock.
"""
from experiments import digital_sharedlineage68_population as kernel
from experiments import digital_sharedlineage68_interpret as natural_full
from experiments.digital_functional69_transition import (
    VERSION, ROLES, actor_record, family_from_audited, transition,validate_provenance)


def _replay_to_birth(natural, slot):
    world = kernel.World(natural['seed'], 'mutating', 'ancestor', 'renewed')
    while world.tick < slot['tick']:
        assert world.step()
    assert world.events == natural['final']['events'][:slot['tick']]
    assert kernel.h(world.snapshot(False)) == slot['post_step_hash']
    return world


def _apply(world, slot, natural_hash, role,provenance):
    after, record = transition(world.snapshot(), slot, natural_hash, role,provenance)
    # Diagnostic metadata stays outside __dict__; every other physical value
    # remains identical, including material IDs and natural prefix events.
    daughter = world.entities[slot['target']]
    daughter['code'] = actor_record(after['entities'], slot['target'])['code']
    assert world.snapshot() == after
    world.check()
    return record


def history(natural, slot_kind, role,provenance):
    validate_provenance(provenance)
    assert slot_kind in ('parent','child') and role in ROLES
    assert role!='ancestor_value_control' or slot_kind=='parent'
    assert role!='inherited_source_control' or slot_kind=='child'
    assert natural['inheritance_mode']=='parent_copy'
    assert natural['mode'] == 'mutating' and natural['fuel_mode'] == 'renewed'
    assert natural['route'] == 'ancestor'
    assert sum(natural['genesis_program'], []) == natural_full.ANCESTOR_WORDS
    summary = natural_full.audit(natural)  # Full ancestry first, not winner screening.
    slot = family_from_audited(natural, summary)[slot_kind]
    result = dict(version=VERSION, natural=natural, branch=None,
                  slot_kind=slot_kind, role=role, provenance=kernel.clone(provenance),transition=None)
    if slot is None:
        return result
    # Genesis restore independently repeats the complete paid prefix and edit.
    world = _replay_to_birth(natural, slot)
    record = _apply(world, slot, natural['hash'], role,provenance)
    restored = _replay_to_birth(natural, slot)
    assert _apply(restored, slot, natural['hash'], role,provenance) == record
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
    if role == 'sham' or not record['code_value_mask']:
        assert branch == natural
    result.update(branch=branch, transition=record)
    return result
