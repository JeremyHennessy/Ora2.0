"""Performance-blind compact translation of the disclosed generic scaffold."""
import hashlib,json
from experiments.digital_latehistory78_source import LEARNER,REFERENCES
VERSION='DIGITAL-LEARNING81-SOURCE-v1'
PRIMARY=tuple(range(1008500,1008508))
UNSEEN=tuple(range(1008700,1008708))
RESERVED=tuple(range(1008600,1008608))+tuple(range(1008800,1008808))
SOFTWARE=tuple(range(2100180,2100184))
CONTROLS=('intact','model_erased','history_misbound')
FIXED=tuple(REFERENCES)
ROLES=FIXED+tuple('learner'+str(q) for q in (2,4,8))
OPS=(0,1,2,3,4,5,6,7,8,18,19,20,21)

def digest(v):return hashlib.sha256(json.dumps(v,sort_keys=True,separators=(',',':')).encode()).hexdigest()

def descriptor(role):
    assert type(role) is str and role in ROLES
    return int(role[-1]) if role.startswith('learner') else 8

def programme(role):
    q=descriptor(role)
    original=LEARNER if role.startswith('learner') else REFERENCES[role]
    body=[t[:] for t in original]
    while body[-1]==[18,0,0]:body.pop()
    for t in body:
        if t[0] in (7,8):t[2]+=1
    result=[[7,q,1]]+body
    assert all(t[0] in OPS for t in result)
    return result

def finish_pc(role):return 2 if role=='fixed_alternation' else 1

def roster():
    return [(role,'intact') for role in FIXED]+[(f'learner{q}',c) for q in (2,4,8) for c in CONTROLS]

def manifest():
    return dict(version=VERSION,roles={r:dict(programme=programme(r),capacity=descriptor(r),
        formation=3*len(programme(r))+descriptor(r)+8,finish_pc=finish_pc(r),
        ancestor='Disclosed LateHistory78 generic model or fixed/reactive source; compact header/jump translation',
        acquired_memory=[0]*descriptor(r),performance_selection=False) for r in ROLES},
        roster=roster(),primary=list(PRIMARY),unseen=list(UNSEEN),reserves=list(RESERVED),
        worlds=0,targets_queried=0,stage_credit=False)
