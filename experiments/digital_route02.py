"""Prospective paid founder configurations under the unchanged ecosystem02 law."""
from experiments.digital_ecosystem02 import World as BaseWorld,ANCESTOR,MODES,h,clone

VERSION='DIGITAL-ROUTE-02-v1'
PROGRAMS={'stationary':clone(ANCESTOR),'mobile':clone(ANCESTOR[:-1])+[[13,0,0]]}

class World(BaseWorld):
    def __init__(self,seed,mode='faithful',route='stationary'):
        assert type(seed) is int and seed>=0 and mode in MODES and route in PROGRAMS
        # Paid genesis configuration; no body is rewritten after assembly.
        self.seed=seed;self.mode=mode;self.tick=0;self.last=-1;self.next_id=1;self.writes=0
        code=sum(PROGRAMS[route],[]);bill=len(code)+16
        self.constructor_remaining=128-bill;self.heat=bill
        self.formation=[dict(unit=i,value=v,energy=1,assistance='supplied ancestor assembly') for i,v in enumerate(code+[0]*16)]
        self.food={i:[i//16,int(h([seed,'food',i])[:8],16)%2] for i in range(64)}
        self.free=list(range(bill,512));self.entities={0:self.body(0,None,0,[[v,i] for i,v in enumerate(code)],list(range(len(code),bill)),0)}
        self.events=[];self.births=0;self.deaths=0;self.maximum=1;self.check()

    @classmethod
    def restore(cls,state):
        assert type(state['tick']) is int and 0<=state['tick']<=4096
        values=[cell['value'] for cell in state['formation'][:18]]
        routes=[name for name,program in PROGRAMS.items() if sum(program,[])==values]
        assert len(routes)==1
        world=cls(state['seed'],state['mode'],routes[0])
        while world.tick<state['tick']:assert world.step()
        assert h(world.snapshot())==h(state)
        return world

def history(seed,route,mode):
    assert (route,mode) in (('stationary','faithful'),('mobile','faithful'),('mobile','copy_disabled'))
    world=World(seed,mode,route)
    while world.tick<64 and world.step():pass
    checkpoint=world.snapshot();resumed=World.restore(checkpoint)
    final=world.run(1536);assert final==resumed.run(1536)
    return dict(version=VERSION,seed=seed,mode=mode,route=route,genesis_program=PROGRAMS[route],checkpoint=checkpoint,final=final,hash=h(final),ancestor_supplied=True,checkpoint_replay=True,learning_demonstrated=False)

if __name__=='__main__':
    import json,sys
    seed=int(sys.argv[1]);assert 24900<=seed<24904
    print(json.dumps([history(seed,sys.argv[2],sys.argv[3])],sort_keys=True,separators=(',',':')))
