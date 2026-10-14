"""Prospective finite PILOT74 wrapper; source implementation, not run admission.

Only faithful supplied software-seed3 history through10240. Independent exact
state/referee/loader/journal/native qualification is owed before any pilot run.
Historical Pressure71/Longitudinal01/Capsule03/04 laws and source stay unchanged.
"""
from experiments import digital_pressure71_population as kernel

VERSION='DIGITAL-PILOT74-FINITE-QUALIFICATION-v1'
MAX_HORIZON=10240
CUTS=(8192,9216,10240)

class World(kernel.World):
    def __init__(self,seed,mode='faithful',route='ancestor',fuel_mode='renewed',inheritance_mode='parent_copy',*,dose=8):
        assert type(seed) is int and seed==3
        assert (mode,route,fuel_mode,inheritance_mode)==('faithful','ancestor','renewed','parent_copy')
        assert type(dose) is int and dose==8
        super().__init__(seed,mode,route,fuel_mode,inheritance_mode,dose=dose)

    def input(self):
        # Literal Longitudinal01 inflow body; only this prospective bound differs.
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

    def run(self,horizon):
        assert type(horizon) is int and horizon in CUTS
        assert type(self.tick) is int and 0<=self.tick<=horizon
        while self.tick<horizon and self.step():pass
        return self.snapshot()
