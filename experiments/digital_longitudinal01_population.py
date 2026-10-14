"""Prospective finite engineering wrapper over unchanged Pressure71 VM.

Only software seeds3/4, supplied faithful ancestor and horizon<=8192. No
scientific seed, mutation panel, learner, efficient loader or activation API.
Checkpoint64 constructor/prefix replay is explicit engineering work.
"""
from experiments import digital_pressure71_population as kernel

VERSION='DIGITAL-FINITE-LONGITUDINAL-ECOLOGY-01-engineering-v1'
SEEDS=(3,4)
MAX_HORIZON=8192

def history(seed,*,horizon=MAX_HORIZON):
    assert type(seed) is int and seed in SEEDS
    assert type(horizon) is int and 64<=horizon<=MAX_HORIZON
    world=kernel.World(seed,'faithful','ancestor','renewed','parent_copy',dose=8)
    while world.tick<64 and world.step():pass
    checkpoint=world.snapshot()
    replayed=kernel.World.restore(checkpoint)
    final=world.run(horizon)
    assert final==replayed.run(horizon)
    return dict(version=VERSION,seed=seed,mode='faithful',inheritance_mode='parent_copy',
        fuel_mode='renewed',route='ancestor',dose=8,horizon=horizon,software_only=True,
        genesis_program=kernel.clone(kernel.PROGRAMS['ancestor']),checkpoint=checkpoint,
        final=final,hash=kernel.h(final),ancestor_supplied=True,checkpoint_replay=True,
        learning_demonstrated=False)
