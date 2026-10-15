"""Supplied four-strategy selector; no target/World queries on import."""
import hashlib,json
from experiments.digital_revision84_source import programme as old_programme
VERSION='STRATEGY88-v1';ADMISSION=VERSION
CONTRACT='2c702fb7e523109c3bc58605aa1f2703178a4585edc268471e1095227299e3d6'
PRIMARY=tuple(range(1010100,1010106));UNSEEN=tuple(range(1010300,1010306))
RESERVED=tuple(range(1010200,1010206))+tuple(range(1010400,1010406))
SOFTWARE=(2100488,2100489);SEEDS=SOFTWARE+PRIMARY+UNSEEN
ARMS=('adaptive','history_reset','credit_misbound','explore')
FIXED=('fixed0','fixed1','cue_identity','cue_inverse','fixed_alternation','latest_reactive')
REFERENCES=FIXED+tuple('rr'+str(i) for i in range(4))
ROLES=tuple(f'{arm}:{i}' for arm in ARMS for i in range(4))+REFERENCES
ENTRIES=(1,6,11,16);WARM=48;DECISIONS=60;HORIZON=1024;COST_BUDGET=512
def canonical(x):return json.dumps(x,sort_keys=True,separators=(',',':')).encode()
def admit(seed,admission=None):
 assert type(seed) is int and (seed in SOFTWARE or admission==ADMISSION and seed in PRIMARY+UNSEEN),'Unregistered strategy context'
def target_mask(seed,packet,admission=None):
 admit(seed,admission);assert type(packet) is int and packet>=0
 phase=int(packet>=48)
 if seed in SOFTWARE:return ((0,170),(85,255))[SOFTWARE.index(seed)][phase]
 bank=PRIMARY if seed in PRIMARY else UNSEEN;offset=bank.index(seed)
 if offset<2:return (0,255)[offset]
 index=int(hashlib.sha256(canonical(['STRATEGY88-LABELS-v1',seed,phase])).hexdigest()[:2],16)%4
 return (0,255,170,85)[index]
def programme(role):
 assert type(role) is str and role in ROLES
 if role in FIXED:return old_programme(role)
 if role.startswith('rr'):
  return [[7,2,(1,4,7,10)[int(role[-1])]],
   [4,0,0],[6,0,0],[7,0,4],[4,0,1],[6,0,0],[7,0,7],
   [0,0,0],[6,0,0],[7,0,10],[0,0,0],[21,0,0],[6,0,0],[7,0,1]]
 arm,index=role.split(':');initial=int(index)
 code=[[7,2,ENTRIES[initial]],
  [4,0,0],[6,0,0],[1,0,0],[8,0,6],[7,0,1],
  [4,0,1],[6,0,0],[1,0,0],[8,0,11],[7,0,6],
  [0,0,0],[6,0,0],[1,0,0],[8,0,16],[7,0,11],
  [0,0,0],[21,0,0],[6,0,0],[1,0,0],[8,0,1],[7,0,16]]
 if arm=='explore':
  for pc,target in ((5,6),(10,11),(15,16),(21,1)):code[pc][2]=target
 return code
def initial(role):return int(role.split(':')[1]) if ':' in role else None
def completed_edge(role,pc,after):
 if after is None or pc==0:return False
 if ':' in role:return pc in (4,5,9,10,14,15,20,21) and after['pc'] in ENTRIES
 if role.startswith('rr'):return pc in (3,6,9,13) and after['pc'] in (1,4,7,10)
 return programme(role)[pc][0]==7 and after['pc']==(2 if role=='fixed_alternation' else 1)
def entry_projection(role,completed,actual):
 assert ':' in role and actual in ENTRIES
 arm,_=role.split(':')
 if completed>=WARM and arm=='history_reset':return ENTRIES[initial(role)]
 if completed>=WARM and arm=='credit_misbound':return ENTRIES[(ENTRIES.index(actual)+2)%4]
 return actual
def manifest():
 return dict(version=VERSION,roster=list(ROLES),source_parameters='Four supplied initial entries,all unscreened',
  capacity=2,blank_memory=[0,0],registers=[0,0],model_memory_used=False,
  source_formation=76,source_triples=22,source_words=66,cheap_rr_formation=52,
  acquired_channel='Semantic strategy entry/PC only; no cue-label model or free counterfactual predictions',
  current_feedback_truthful=True,worlds=0,targets=0,stage_credit=False)
