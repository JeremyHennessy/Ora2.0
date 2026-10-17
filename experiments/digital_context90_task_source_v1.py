"""Known authored SOFTWARE protocol only; no scientific contexts admitted."""
from experiments.digital_context90_source_v3 import programme as learner
SOFTWARE=(2100690,2100691,2100692,2100693)
ADMISSION='CONTEXT90-SOFTWARE-v1'
DECISIONS=60
HORIZON=1200
COST_BUDGET=1800
REFERENCES={'fixed0': [[7, 2, 1], [0, 0, 0], [0, 0, 0], [4, 0, 0], [6, 0, 0], [0, 0, 0], [7, 0, 1]], 'fixed1': [[7, 2, 1], [0, 0, 0], [0, 0, 0], [4, 0, 1], [6, 0, 0], [0, 0, 0], [7, 0, 1]], 'retained_cue': [[7, 2, 1], [0, 1, 0], [0, 0, 0], [6, 1, 0], [0, 0, 0], [7, 0, 1]], 'retained_inverse': [[7, 2, 1], [0, 1, 0], [0, 0, 0], [21, 1, 0], [6, 1, 0], [0, 0, 0], [7, 0, 1]], 'current_distractor': [[7, 2, 1], [0, 0, 0], [0, 0, 0], [6, 0, 0], [0, 0, 0], [7, 0, 1]], 'current_inverse': [[7, 2, 1], [0, 0, 0], [0, 0, 0], [21, 0, 0], [6, 0, 0], [0, 0, 0], [7, 0, 1]], 'alternation0': [[7, 2, 1], [4, 1, 0], [0, 0, 0], [0, 0, 0], [6, 1, 0], [0, 0, 0], [21, 1, 0], [7, 0, 2]], 'alternation1': [[7, 2, 1], [4, 1, 1], [0, 0, 0], [0, 0, 0], [6, 1, 0], [0, 0, 0], [21, 1, 0], [7, 0, 2]], 'latest0': [[7, 2, 1], [4, 1, 0], [0, 0, 0], [0, 0, 0], [6, 1, 0], [0, 0, 0], [1, 0, 0], [8, 0, 9], [7, 0, 2], [21, 1, 0], [7, 0, 2]], 'latest1': [[7, 2, 1], [4, 1, 1], [0, 0, 0], [0, 0, 0], [6, 1, 0], [0, 0, 0], [1, 0, 0], [8, 0, 9], [7, 0, 2], [21, 1, 0], [7, 0, 2]]}
ROLES=tuple('q'+str(q)+':'+r for q in (2,4,8) for r in ('A','B'))+tuple(REFERENCES)

def admit(seed,admission=None):
 if type(seed) is not int or seed not in SOFTWARE or admission!=ADMISSION:raise ValueError('Registered SOFTWARE scope only')

def programme(role):
 if type(role) is not str or role not in ROLES:raise ValueError('full role roster')
 return learner(int(role[1]),27 if role.endswith('A') else 1) if ':' in role else [t[:] for t in REFERENCES[role]]

def label_mask(seed,trial,admission=None):
 admit(seed,admission)
 if type(trial) is not int or not 0<=trial<60:raise ValueError('trial')
 return ((0,255,0),(255,0,255),(90,165,90),(165,90,165))[SOFTWARE.index(seed)][trial//20]

def observation(seed,trial,channel,admission=None):
 admit(seed,admission)
 if type(trial) is not int or not 0<=trial<60 or channel not in ('cue','pre','post'):raise ValueError('observation')
 offset=seed-SOFTWARE[0]
 return trial%8 if channel=='cue' else (3*trial+offset)%8 if channel=='pre' else (5*trial+1+offset)%8

def completed_edge(role,pc,after):
 if after is None:return False
 if ':' in role:return pc==26 and after['pc'] in (27,1)
 entry=2 if role.startswith(('latest','alternation')) else 1
 return pc!=0 and programme(role)[pc][0]==7 and after['pc']==entry
