"""Two authored five-step software fixtures, never a registered task context.

Invented paid genesis objects exercise the supplied fixed cold prefix only.
No candidate is enrolled, no scientific seed used, no learned policy executed.
"""
from experiments import digital_experience75_world as kernel
from experiments.digital_experience75_source import references
from experiments.digital_experience75_controls import Control
def fixture(seed):
    assert type(seed) is int and seed in (95074,95075)
    code=references()['fixed_exploration'];values=sum(code,[])
    world=object.__new__(kernel.World)
    world.control_mode='intact';world._origin=None
    world.seed=seed;world.mode='faithful';world.tick=0;world.last=-1;world.next_id=1;world.writes=0
    world.constructor_remaining=70;world.heat=58
    world.formation=[dict(unit=i,value=v,energy=1,assistance='supplied ancestor assembly') for i,v in enumerate(values+[0]*16)]
    world.food={i:[0 if i<32 else 1+(i-32)//16,int(kernel.h([seed,'food',i])[:8],16)%2] for i in range(64)}
    for segment in (0,1):
        order=sorted(range(16),key=lambda i:kernel.h([seed//2,'experience75-cue-order',segment,i]))
        for rank,index in enumerate(order):world.food[16*segment+index][1]=int(rank>=8)
    world.free=list(range(58,512));world.entities={0:kernel.World.body(0,None,0,[[v,i] for i,v in enumerate(values)],list(range(42,58)),0)}
    world.events=[];world.births=world.deaths=0;world.maximum=1
    world._control=Control(code,world._local(world.entities[0]),'intact',seed)
    world.check()
    for _ in range(5):assert world.step()
    final=world.snapshot()
    return dict(version=kernel.VERSION,seed=seed,mode='faithful',route='fixed_exploration',control_mode='intact',genesis_program=code,checkpoint=final,final=final,hash=kernel.h(final),ancestor_supplied=True,checkpoint_replay=False,learning_demonstrated=False)
