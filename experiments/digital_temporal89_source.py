"""Frozen temporal observation task registry; imports never query target values."""
import hashlib,json
from experiments.digital_temporal89_programme import programme as learner, REFERENCES

VERSION='TEMPORAL89-v1'
CONTRACT='3095e9f662466fb5cefed1605599041e1c6ca31e247abd119caf05613e6620c1'
SOFTWARE=(2100589,2100590)
PRIMARY=tuple(range(1010500,1010508))
UNSEEN=tuple(range(1010700,1010708))
RESERVED=tuple(range(1010600,1010608))+tuple(range(1010800,1010808))
SEEDS=SOFTWARE+PRIMARY+UNSEEN
ARMS=('intact','credit_erased','recall_disabled','model_disabled','update_frozen')
ROLES=tuple(f'q{q}:{a}' for q in (2,4,8) for a in ARMS)+tuple(REFERENCES)
WARM=48;DECISIONS=60;HORIZON=1024;COST_BUDGET=1024

def digest(x):return hashlib.sha256(json.dumps(x,sort_keys=True,separators=(',',':')).encode()).hexdigest()

def admit(seed,admission=None):
 assert type(seed) is int
 assert ((seed in SOFTWARE and admission=='TEMPORAL89-SOFTWARE-v1') or
         (seed in PRIMARY+UNSEEN and admission=='TEMPORAL89-PRIMARY-v1')),'Unregistered temporal context'

def label_mask(seed,trial,admission=None):
 admit(seed,admission);assert type(trial) is int and 0<=trial<60
 phase=int(trial>=48)
 if seed in SOFTWARE:return ((0,255),(90,165))[SOFTWARE.index(seed)][phase]
 bank=PRIMARY if seed in PRIMARY else UNSEEN;offset=bank.index(seed)
 return (0,255)[offset] if offset<2 else int(digest(['TEMPORAL89-LABELS-v1',seed,phase])[:2],16)

def observation(seed,trial,channel,admission=None):
 admit(seed,admission);assert type(trial) is int and 0<=trial<60 and channel in ('cue','pre','post')
 return int(digest(['TEMPORAL89-OBS-v1',seed,trial,channel])[:2],16)%8

def programme(role):
 assert type(role) is str and role in ROLES
 return learner(int(role[1])) if ':' in role else [t[:] for t in REFERENCES[role]]

def entry(role):return 2 if role.startswith(('latest','alternation')) else 1

def arm(role):return role.split(':')[1] if ':' in role else None

def completed_edge(role,pc,after):
 return after is not None and pc!=0 and programme(role)[pc][0]==7 and after['pc']==entry(role)

def manifest():
 return dict(version=VERSION,contract=CONTRACT,roles=list(ROLES),warm=WARM,decisions=DECISIONS,
  horizon=HORIZON,cost_budget=COST_BUDGET,phase='No target generation on import/manifest',
  supplied_model_updater=True,worlds=0,targets=0,stage_credit=False)
