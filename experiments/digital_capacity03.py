"""Authored software measurement witnesses only; never a primary learner founder."""
from experiments.digital_context03 import World as BaseWorld,h,clone,state_types

VERSION='DIGITAL-CAPACITY-03-v1'
# Constructive measurement witness, not a discovered or population-installed policy.
WITNESS=[[2,0,0],[6,0,0],[1,1,0],[8,1,10],[10,0,0],[12,0,0],
         [4,1,1],[13,1,0],[7,0,0],[31,0,0],[4,1,1],[5,0,1],
         [3,0,0],[6,0,0],[1,1,0],[8,1,6],[7,0,4],
         [31,0,0],[31,0,0],[31,0,0]]
FIXED=[[4,0,0],[6,0,0],[10,0,0],[12,0,0],[4,1,1],[13,1,0],[7,0,0]]
PROGRAMS={'witness':clone(WITNESS),'disconnected':[[4,0,0]]+clone(WITNESS[1:]),
          'fixed':clone(FIXED),'parity':[[0,0,0]]+clone(FIXED[1:]),
          'padded_fixed':clone(FIXED)+[[31,0,0] for _ in range(13)]}

class World(BaseWorld):
    def __init__(self,seed,route='fixed'):
        assert type(seed) is int and seed>=0 and route in PROGRAMS
        self.seed=seed;self.mode='faithful';self.tick=0;self.last=-1;self.next_id=1;self.writes=0
        code=sum(PROGRAMS[route],[]);bill=len(code)+16
        assert bill<=128
        self.constructor_remaining=128-bill;self.heat=bill
        self.formation=[dict(unit=i,value=v,energy=1,assistance='supplied ancestor assembly') for i,v in enumerate(code+[0]*16)]
        self.food={i:[i//16,int(h([seed,'food',i])[:8],16)%2] for i in range(64)}
        self.free=list(range(bill,512));self.entities={0:self.body(0,None,0,[[v,i] for i,v in enumerate(code)],list(range(len(code),bill)),0)}
        self.events=[];self.births=0;self.deaths=0;self.maximum=1;self.check()

    @classmethod
    def restore(cls,state):
        state_types(state);assert type(state['tick']) is int and 0<=state['tick']<=4096
        values=[cell['value'] for cell in state['formation'][:-16]]
        routes=[name for name,program in PROGRAMS.items() if sum(program,[])==values];assert len(routes)==1
        world=cls(state['seed'],routes[0])
        while world.tick<state['tick']:assert world.step()
        assert h(world.snapshot())==h(state)
        return world

def history(seed,route):
    world=World(seed,route)
    while world.tick<64 and world.step():pass
    checkpoint=world.snapshot();resumed=World.restore(checkpoint)
    final=world.run(1536);assert final==resumed.run(1536)
    return dict(version=VERSION,seed=seed,mode='faithful',route=route,genesis_program=PROGRAMS[route],checkpoint=checkpoint,final=final,hash=h(final),ancestor_supplied=True,checkpoint_replay=True,learning_demonstrated=False)

if __name__=='__main__':
    import base64,json,sys,zlib
    seed=int(sys.argv[1]);assert seed in (25190,25191)
    # Lossless receipt transport under the unchanged 1 MiB native stdout cap.
    raw=json.dumps([history(seed,sys.argv[2])],sort_keys=True,separators=(',',':')).encode()
    print(base64.b64encode(zlib.compress(raw)).decode('ascii'))
