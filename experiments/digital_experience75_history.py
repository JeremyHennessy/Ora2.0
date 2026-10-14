"""Bounded source roster generator; no outcome-selected enrollment."""
import base64,json,zlib
from experiments.digital_experience75_world import World,VERSION,PRIMARY,UNSEEN,h,PROGRAMS
from experiments.digital_experience75_source import REFERENCES,candidate
ARMS=('intact','retained_disabled','own_disrupted')
def roles(chunk):
    assert type(chunk) is int and chunk in (0,1,2)
    return [f'candidate{i}' for i in range(chunk*8,chunk*8+8)] if chunk<2 else list(REFERENCES)
def history(seed,route,control):
    assert type(seed) is int and seed in PRIMARY+UNSEEN and control in ARMS and route in PROGRAMS
    world=World(seed,'faithful',route,control)
    while world.tick<64 and world.step():pass
    checkpoint=world.snapshot();final=world.run(512)
    return dict(version=VERSION,seed=seed,mode='faithful',route=route,control_mode=control,genesis_program=PROGRAMS[route],checkpoint=checkpoint,final=final,hash=h(final),ancestor_supplied=True,checkpoint_replay=False,learning_demonstrated=False)
def batch(seed,control,chunk):
    assert type(seed) is int and seed in PRIMARY+UNSEEN and control in ARMS
    return dict(contract='DIGITAL-EXPERIENCE75-BATCH-v1',seed=seed,control=control,chunk=chunk,histories=[dict(role=role,ancestry=candidate(int(role[9:])) if role.startswith('candidate') else None,row=history(seed,role,control)) for role in roles(chunk)],learning=False,stage_credit=False)
if __name__=='__main__':
    import sys
    print(base64.b64encode(zlib.compress(json.dumps(batch(int(sys.argv[1]),sys.argv[2],int(sys.argv[3])),sort_keys=True,separators=(',',':')).encode())).decode())
