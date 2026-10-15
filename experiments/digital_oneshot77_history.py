"""Bounded source roster generator; no outcome-selected enrollment."""
import base64,json,zlib
from experiments.digital_oneshot77_world import World,VERSION,PRIMARY,UNSEEN,h,PROGRAMS
from experiments.digital_oneshot77_source import REFERENCES,SOFTWARE
ARMS=('intact','model_disabled','history_misbound')
def roles(chunk):
    assert type(chunk) is int and chunk in (0,1,2)
    return [f'candidate{i}' for i in range(chunk*8,chunk*8+8)] if chunk<2 else list(REFERENCES)
def history(seed,route,control):
    assert type(seed) is int and seed in PRIMARY+UNSEEN+SOFTWARE and control in ARMS and route in PROGRAMS
    world=World(seed,'faithful',route,control)
    while world.tick<64 and world.step():pass
    checkpoint=world.snapshot();final=world.run(512)
    return dict(version=VERSION,seed=seed,mode='faithful',route=route,control_mode=control,genesis_program=PROGRAMS[route],checkpoint=checkpoint,final=final,hash=h(final),ancestor_supplied=True,checkpoint_replay=False,learning_demonstrated=False)
