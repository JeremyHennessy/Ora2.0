"""Prospectively supplied full-capacity family; no targets or Worlds on import."""
import hashlib
import json
from experiments.digital_latehistory78_source import LEARNER, REFERENCES

VERSION = 'DIGITAL-REVISION84-v1'
ADMISSION = 'REVISION84-v1'
PRIMARY = tuple(range(1009300, 1009308))
UNSEEN = tuple(range(1009500, 1009508))
RESERVED = tuple(range(1009400, 1009408))+tuple(range(1009600, 1009608))
SOFTWARE = tuple(range(2100280, 2100284))
SEEDS = SOFTWARE+PRIMARY+UNSEEN
FIXED = tuple(REFERENCES)
CONTROLS = ('intact', 'model_erased', 'history_misbound', 'update_frozen')
ROLES = FIXED+tuple('learner'+str(q) for q in (2,4,8))
OPS = (0,1,2,3,4,5,6,7,8,18,19,20,21)
WARM = 48
DECISIONS = 60
HORIZON = 1024

def digest(value):
    return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':')).encode()).hexdigest()

def admit(seed, admission=None):
    assert type(seed) is int and (seed in SOFTWARE or
        (admission == ADMISSION and seed in PRIMARY+UNSEEN)), 'Unregistered context'

def target_mask(seed, packet, admission=None):
    admit(seed, admission)
    assert type(packet) is int and packet >= 0
    phase = int(packet >= WARM)
    if seed in SOFTWARE:
        return ((0,255,90,165),(0,255,165,90))[phase][SOFTWARE.index(seed)]
    bank = PRIMARY if seed in PRIMARY else UNSEEN
    index = bank.index(seed)
    if index < 2:
        return (0,255)[index]
    return int(digest(['REVISION84-LABELS-v1',seed,phase])[:2],16)

def descriptor(role):
    assert type(role) is str and role in ROLES
    return int(role[-1]) if role.startswith('learner') else 2

def programme(role):
    q = descriptor(role)
    body = [t[:] for t in (LEARNER if role.startswith('learner') else REFERENCES[role])]
    while body[-1] == [18,0,0]:
        body.pop()
    for t in body:
        if t[0] in (7,8):
            t[2] += 1
    code = [[7,q,1]]+body
    assert all(t[0] in OPS for t in code)
    if role in FIXED:
        assert not ({t[0] for t in code} & {2,3,19,20})
    return code

def finish_pc(role):
    assert role in ROLES
    return 2 if role == 'fixed_alternation' else 1

def roster():
    return [(r,'intact') for r in FIXED]+[(f'learner{q}',c) for q in (2,4,8) for c in CONTROLS]

def manifest():
    return dict(version=VERSION,roles={r:dict(programme=programme(r),capacity=descriptor(r),
        formation=3*len(programme(r))+descriptor(r)+8,finish_pc=finish_pc(r),
        acquired_memory=[0]*descriptor(r),performance_selection=False,
        ancestor='Supplied LateHistory78 body / Learning81 compact translation; minimum fixed state')
        for r in ROLES},roster=roster(),primary=list(PRIMARY),unseen=list(UNSEEN),
        reserves=list(RESERVED),warm=WARM,decisions=DECISIONS,horizon=HORIZON,
        worlds=0,targets_queried=0,stage_credit=False)
