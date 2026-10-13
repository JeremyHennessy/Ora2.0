"""Paid explicit genesis; unchanged Renewable64 execution/resource semantics.
No global PROGRAMS mutation. Caller binds source identity outside organism state.
Software/science execution requires separate prospective admission.
"""
from experiments import digital_renewable64 as kernel


def words_valid(words):
    assert type(words) is list and len(words)==27
    assert all(type(v) is int and 0<=v<32 for v in words)


class GenesisWorld(kernel.World):
    def __init__(self,seed,words):
        words_valid(words)
        assert type(seed) is int and seed>=0
        self.fuel_mode='renewed';self.turns={0:0};self.offered=0;self.admitted=0;self.rejected=0;self.next_packet=64
        self.seed=seed;self.mode='faithful';self.tick=0;self.last=-1;self.next_id=1;self.writes=0
        code=words[:];bill=len(code)+16
        self.constructor_remaining=128-bill;self.heat=bill
        self.formation=[dict(unit=i,value=v,energy=1,assistance='supplied ancestor assembly') for i,v in enumerate(code+[0]*16)]
        self.food={i:[0 if i<32 else 1+(i-32)//16,int(kernel.h([seed,'food',i])[:8],16)%2] for i in range(64)}
        self.free=list(range(bill,512));self.entities={0:self.body(0,None,0,[[v,i] for i,v in enumerate(code)],list(range(len(code),bill)),0)}
        self.events=[];self.births=0;self.deaths=0;self.maximum=1;self.check()

    @classmethod
    def restore(cls,state):
        raise AssertionError('Explicit paid genesis binding required; no registry lookup')

    @classmethod
    def restore_bound(cls,state,words):
        words_valid(words);kernel.state_types(state)
        assert type(state['tick']) is int and 0<=state['tick']<=4096
        assert state['mode']=='faithful' and state['fuel_mode']=='renewed'
        world=cls(state['seed'],words)
        assert state['formation']==world.formation
        while world.tick<state['tick']:assert world.step()
        assert world.snapshot()==state
        return world


def history(seed,words,route):
    """Generic software-capable producer; scientific provenance bound by wrapper."""
    assert type(route) is str and route
    world=GenesisWorld(seed,words)
    while world.tick<64 and world.step():pass
    checkpoint=world.snapshot();restored=GenesisWorld.restore_bound(checkpoint,words)
    final=world.run(4096);assert final==restored.run(4096)
    return dict(version=kernel.VERSION,seed=seed,mode='faithful',fuel_mode='renewed',route=route,
                genesis_program=[words[i:i+3] for i in range(0,27,3)],checkpoint=checkpoint,final=final,
                hash=kernel.h(final),ancestor_supplied=True,checkpoint_replay=True,learning_demonstrated=False)
