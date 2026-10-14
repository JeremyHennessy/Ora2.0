"""Prospective finite engineering wrapper over unchanged Pressure71 VM.

Only software seeds3/4, supplied faithful ancestor and horizon<=8192. No
scientific seed, mutation panel, learner, efficient loader or activation API.
Checkpoint64 constructor/prefix replay is explicit engineering work.
"""
from experiments import digital_pressure71_population as kernel

VERSION='DIGITAL-FINITE-LONGITUDINAL-ECOLOGY-01-engineering-v1'
SEEDS=(3,4)
MAX_HORIZON=8192

class World(kernel.World):
    def input(self):
        # Identical64-interval inflow/caps/draws, with the prospective bound.
        # Historical inherited input() intentionally stops after4096.
        if self.fuel_mode=='no_inflow' or self.tick%64:return None
        assert 64<=self.tick<=MAX_HORIZON
        offers=[]
        for site in range(4):
            for _ in range(4):
                packet=self.next_packet;self.next_packet+=1;self.offered+=1
                kind=int(kernel.h([self.seed,'renew-food',packet])[:8],16)%2
                admitted=sum(v[0]==site for v in self.food.values())<32
                if admitted:self.food[packet]=[site,kind];self.admitted+=1
                else:self.rejected+=1
                offers.append(dict(packet=packet,site=site,kind=kind,energy=20,outcome='admitted' if admitted else 'rejected'))
        return offers

def _bounded_steps(world,horizon):
    # The historical World.run intentionally refuses horizons above4096.
    # Advance this separately prospective fixture through unchanged step laws.
    assert type(horizon) is int and 64<=horizon<=MAX_HORIZON
    while world.tick<horizon and world.step():pass
    return world.snapshot()

def history(seed,*,horizon=MAX_HORIZON):
    assert type(seed) is int and seed in SEEDS
    assert type(horizon) is int and 64<=horizon<=MAX_HORIZON
    world=World(seed,'faithful','ancestor','renewed','parent_copy',dose=8)
    while world.tick<64 and world.step():pass
    checkpoint=world.snapshot()
    replayed=World.restore(checkpoint)
    assert type(world) is World and type(replayed) is World
    final=_bounded_steps(world,horizon)
    assert final==_bounded_steps(replayed,horizon)
    return dict(version=VERSION,seed=seed,mode='faithful',inheritance_mode='parent_copy',
        fuel_mode='renewed',route='ancestor',dose=8,horizon=horizon,software_only=True,
        genesis_program=kernel.clone(kernel.PROGRAMS['ancestor']),checkpoint=checkpoint,
        final=final,hash=kernel.h(final),ancestor_supplied=True,checkpoint_replay=True,
        learning_demonstrated=False)
