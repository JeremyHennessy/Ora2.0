"""Authored cold-prefix plus one non-learning cognitive cycle fixtures, never a registered task context.

Invented paid genesis objects exercise the supplied fixed cold prefix and NOP/NOP controller only.
No candidate is enrolled, no scientific seed used, no learned policy executed.
"""
from experiments import digital_cognitive76_world as kernel
from experiments.digital_cognitive76_source import references
from experiments.digital_cognitive76_controls import Control
def fixture(seed, control='intact'):
    assert control in ('intact','model_disabled','history_misbound')
    assert type(seed) is int and seed in (95076,95077)
    code=references()['fixed_cognitive'];values=sum(code,[])
    world=object.__new__(kernel.World)
    world.control_mode=control;world._origin=None
    world.seed=seed;world.mode='faithful';world.tick=0;world.last=-1;world.next_id=1;world.writes=0
    world.constructor_remaining=52;world.heat=76
    world.formation=[dict(unit=i,value=v,energy=1,assistance='supplied ancestor assembly') for i,v in enumerate(values+[0]*16)]
    world.food={i:[0 if i<32 else 1+(i-32)//16,int(kernel.h([seed,'food',i])[:8],16)%2] for i in range(64)}
    for segment in (0,1):
        order=sorted(range(16),key=lambda i:kernel.h([seed//2,'experience75-cue-order',segment,i]))
        for rank,index in enumerate(order):world.food[16*segment+index][1]=int(rank>=8)
    world.free=list(range(76,512));world.entities={0:kernel.World.body(0,None,0,[[v,i] for i,v in enumerate(values)],list(range(60,76)),0)}
    world.events=[];world.births=world.deaths=0;world.maximum=1
    world._control=Control(code,world._local(world.entities[0]),control,seed)
    world.check()
    for _ in range(11 if seed%2==0 else 18):assert world.step()
    final=world.snapshot()
    return dict(version=kernel.VERSION,seed=seed,mode='faithful',route='fixed_cognitive',control_mode=control,genesis_program=code,checkpoint=final,final=final,hash=kernel.h(final),ancestor_supplied=True,checkpoint_replay=False,learning_demonstrated=False)
