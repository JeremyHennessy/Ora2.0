"""Paid born-genotype sourcing; no authored experience policy or host execution."""
import base64,json,sys,zlib
from experiments.digital_context03 import World as Kernel,h,clone,state_types

VERSION='DIGITAL-DESCENT-04-v1'
ANCESTOR=[[0,0,0],[6,0,0],[10,0,0],[12,0,0],[4,1,1],[13,1,0],[7,0,0]]
FIXED=[[4,0,0]]+clone(ANCESTOR[1:])

class World(Kernel):
    def __init__(self,seed,mode='faithful',program=None):
        program=clone(ANCESTOR if program is None else program)
        assert type(seed) is int and seed>=0 and mode in ('mutating','faithful','copy_disabled')
        assert len(program)==7 and all(isinstance(x,list) and len(x)==3 and all(type(v) is int and 0<=v<32 for v in x) for x in program)
        self.seed=seed;self.mode=mode;self.tick=0;self.last=-1;self.next_id=1;self.writes=0
        code=sum(program,[]);bill=37;self.constructor_remaining=91;self.heat=bill
        self.formation=[dict(unit=i,value=v,energy=1,assistance='supplied ancestor assembly') for i,v in enumerate(code+[0]*16)]
        self.food={i:[i//16,int(h([seed,'food',i])[:8],16)%2] for i in range(64)}
        self.free=list(range(bill,512));self.entities={0:self.body(0,None,0,[[v,i] for i,v in enumerate(code)],list(range(21,bill)),0)}
        self.events=[];self.births=0;self.deaths=0;self.maximum=1;self.check()

    @classmethod
    def restore(cls,state):
        state_types(state);assert type(state['tick']) is int and 0<=state['tick']<=4096
        values=[x['value'] for x in state['formation'][:21]]
        world=cls(state['seed'],state['mode'],[values[i:i+3] for i in range(0,21,3)])
        while world.tick<state['tick']:assert world.step()
        assert h(world.snapshot())==h(state)
        return world

def history(seed,mode='faithful',route='parity',program=None):
    assert route in ('parity','fixed','candidate')
    genome=clone(program if route=='candidate' else FIXED if route=='fixed' else ANCESTOR)
    world=World(seed,mode,genome)
    while world.tick<64 and world.step():pass
    checkpoint=world.snapshot();resumed=World.restore(checkpoint)
    final=world.run(1536);assert final==resumed.run(1536)
    return dict(version=VERSION,seed=seed,mode=mode,route=route,genesis_program=genome,checkpoint=checkpoint,final=final,hash=h(final),ancestor_supplied=True,checkpoint_replay=True,learning_demonstrated=False)

if __name__=='__main__':
    seed=int(sys.argv[1]);mode=sys.argv[2];route=sys.argv[3]
    assert seed in (*range(25200,25204),*range(25300,25304))
    assert (seed<25300 and route=='parity') or (seed>=25300 and mode in ('faithful','copy_disabled'))
    program=json.load(open(sys.argv[4],encoding='utf-8')) if route=='candidate' else None
    raw=json.dumps([history(seed,mode,route,program)],sort_keys=True,separators=(',',':')).encode()
    print(base64.b64encode(zlib.compress(raw)).decode('ascii'))
