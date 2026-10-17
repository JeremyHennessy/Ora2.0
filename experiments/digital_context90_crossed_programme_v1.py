"""Pure supplied programmes; no target registry, producer or constructor imports."""
from experiments.digital_context90_source_v3 import programme as retention
REFERENCES={'fixed0': [[7, 2, 1], [0, 0, 0], [0, 0, 0], [4, 0, 0], [6, 0, 0], [0, 0, 0], [7, 0, 1]], 'fixed1': [[7, 2, 1], [0, 0, 0], [0, 0, 0], [4, 0, 1], [6, 0, 0], [0, 0, 0], [7, 0, 1]], 'retained_cue': [[7, 2, 1], [0, 1, 0], [0, 0, 0], [6, 1, 0], [0, 0, 0], [7, 0, 1]], 'retained_inverse': [[7, 2, 1], [0, 1, 0], [0, 0, 0], [21, 1, 0], [6, 1, 0], [0, 0, 0], [7, 0, 1]], 'current_distractor': [[7, 2, 1], [0, 0, 0], [0, 0, 0], [6, 0, 0], [0, 0, 0], [7, 0, 1]], 'current_inverse': [[7, 2, 1], [0, 0, 0], [0, 0, 0], [21, 0, 0], [6, 0, 0], [0, 0, 0], [7, 0, 1]], 'alternation0': [[7, 2, 1], [4, 1, 0], [0, 0, 0], [0, 0, 0], [6, 1, 0], [0, 0, 0], [21, 1, 0], [7, 0, 2]], 'alternation1': [[7, 2, 1], [4, 1, 1], [0, 0, 0], [0, 0, 0], [6, 1, 0], [0, 0, 0], [21, 1, 0], [7, 0, 2]], 'latest0': [[7, 2, 1], [4, 1, 0], [0, 0, 0], [0, 0, 0], [6, 1, 0], [0, 0, 0], [1, 0, 0], [8, 0, 9], [7, 0, 2], [21, 1, 0], [7, 0, 2]], 'latest1': [[7, 2, 1], [4, 1, 1], [0, 0, 0], [0, 0, 0], [6, 1, 0], [0, 0, 0], [1, 0, 0], [8, 0, 9], [7, 0, 2], [21, 1, 0], [7, 0, 2]]}
RETENTION=tuple('q'+str(q)+':'+e for q in (2,4,8) for e in ('A','B'))
OVERWRITE=tuple('overwrite'+str(q) for q in (2,4,8))
BATCHES={'retention':RETENTION,'overwrite':OVERWRITE,'reactive0':tuple(REFERENCES)[:5],'reactive1':tuple(REFERENCES)[5:]}
ACTORS=tuple(x for xs in BATCHES.values() for x in xs)

def programme(role):
 if type(role) is not str or role not in ACTORS:raise ValueError('full role roster')
 if role in RETENTION:return retention(int(role[1]),27 if role.endswith('A') else 1)
 if role in OVERWRITE:
  q=int(role[-1]);return [[7,q,1],[0,1,0],[0,0,0],[19,0,1],[6,0,0],[0,0,0],[1,0,0],[8,0,9],[7,0,1],[19,0,1],[21,0,0],[20,1,0],[7,0,1]]
 return [t[:] for t in REFERENCES[role]]

def completed_edge(role,pc,after):
 if after is None:return False
 if role in RETENTION:return pc==26 and after['pc'] in (27,1)
 entry=2 if role.startswith(('latest','alternation')) else 1
 return pc!=0 and programme(role)[pc][0]==7 and after['pc']==entry
