"""Bounded source roster generator; no outcome-selected enrollment."""
import base64,json,zlib
from experiments.digital_latehistory78_world import World,VERSION,PRIMARY,UNSEEN,h,PROGRAMS
from experiments.digital_latehistory78_source import REFERENCES,SOFTWARE
ARMS=('intact','late_erasure','late_misbound')
def history(seed,route,control):
    assert type(seed) is int and seed in PRIMARY+UNSEEN+SOFTWARE and control in ARMS and route in PROGRAMS
    world=World(seed,'faithful',route,control)
    while world.tick<64 and world.step():pass
    checkpoint=world.snapshot();final=world.run(512)
    return dict(version=VERSION,seed=seed,mode='faithful',route=route,control_mode=control,genesis_program=PROGRAMS[route],checkpoint=checkpoint,final=final,hash=h(final),ancestor_supplied=True,checkpoint_replay=False,learning_demonstrated=False)
