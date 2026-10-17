"""Pure frozen contract, graph and integer decoder; NO entropy/World imports."""
import json
from pathlib import Path
from experiments.digital_context90_crossed_programme_v1 import ACTORS,BATCHES
CONTRACT='b2d7402f2fa00e34dffd5eca4f747fff6f0e830ed7bc983706fa0613acb9ad7c'
FAMILY=33292288
CELLS=('AA','AC','CA','CC')
CAPS={'retention':56,'overwrite':28,'reactive0':44,'reactive1':44}
M=1024**2

def integer(v,lo,hi):
 if type(v) is not int or not lo<=v<=hi:raise ValueError('integer bounds')
 return v

def insert_bit(x,c,bit):
 integer(x,0,127);integer(c,0,7);integer(bit,0,1)
 low=x%(2**c);high=x//(2**c)
 return low+bit*(2**c)+high*(2**(c+1))

def decode_rank(rank):
 integer(rank,0,FAMILY-1);b=rank%128;rank//=128;k=rank%127;rank//=127;a=rank%256;c=rank//256
 removed=(a%(2**c))+(a//(2**(c+1)))*(2**c)
 other=k+int(k>=removed);bit=(a//(2**c))%2
 return dict(c=c,A=a,C=insert_bit(other,c,bit),B=insert_bit(b,c,1-bit))

def decode_words(words):
 if type(words) is not list or not 1<=len(words)<=8:raise ValueError('finite entropy extent')
 ceiling=(2**256//FAMILY)*FAMILY
 for i,w in enumerate(words):
  if type(w) is not str or len(w)!=64 or any(c not in '0123456789abcdef' for c in w):raise ValueError('raw entropy word')
  x=int(w,16)
  if x<ceiling:
   if i!=len(words)-1:raise ValueError('draw after accepted word')
   return x%FAMILY
 raise ValueError('finite rejection exhaustion')

def config(mode):
 if type(mode) is not str or mode not in ('software','primary'):raise ValueError('mode')
 n=1 if mode=='software' else 9
 return dict(schema='CONTEXT90-CROSSED-CONFIG-v1',mode=mode,contract_sha256=CONTRACT,tuple_ids=['C90X1-S00'] if mode=='software' else ['C90X1-P'+str(i).zfill(2) for i in range(n)],resource_seeds=[2100790] if mode=='software' else list(range(1900900,1900909)),cells=list(CELLS),batches={k:list(v) for k,v in BATCHES.items()},horizon=2040,cost_budget=3040,decisions=112,phases=[80,16,16],startup=200,factory=328,energy_cap=224,max_population=1,expansion_tick=0,vm_mode='no_variation')

def roles(mode):
 c=config(mode);rows=[]
 if mode=='primary':rows.append('primary:sampler')
 for i in range(len(c['tuple_ids'])):
  for cell in CELLS:
   for batch in BATCHES:rows.extend((f'original:{i}:{cell}:{batch}:generate',f'original:{i}:{cell}:{batch}:audit',f'restored:{i}:{cell}:{batch}:generate'))
 return tuple(rows)

def kind(role):return 'sample' if role=='primary:sampler' else role.split(':')[-1]

def capacity(role):
 if role=='primary:sampler':return 65536
 return (CAPS[role.split(':')[3]] if kind(role)=='generate' else 2)*M

def spec(s,cap):
 if type(s) is not dict or set(s)!= {'path','extent','sha256'}:raise ValueError('input spec')
 if type(s['path']) is not str or not Path(s['path']).is_absolute():raise ValueError('plain absolute input')
 integer(s['extent'],1,cap)
 if type(s['sha256']) is not str or len(s['sha256'])!=64 or any(c not in '0123456789abcdef' for c in s['sha256']):raise ValueError('input digest')

def scope(request):
 if type(request) is not dict or set(request)!= {'configuration','source_files','source_sha','config_sha','role','kind','input','grant','seal'}:raise ValueError('request shape')
 c=request['configuration']
 if type(c) is not dict or json.dumps(c,sort_keys=True)!=json.dumps(config(c.get('mode')),sort_keys=True):raise ValueError('exact configuration')
 role=request['role']
 if type(role) is not str or role not in roles(c['mode']) or request['kind']!=kind(role):raise ValueError('registered role')
 inputs=request['input']
 if kind(role)=='sample':
  if inputs is not None:raise ValueError('sampler inputs')
 else:
  if type(inputs) is not dict or set(inputs)!= {'body','draw'}:raise ValueError('dependent inputs')
  if c['mode']=='primary':spec(inputs['draw'],65536)
  elif inputs['draw'] is not None:raise ValueError('software entropy refused')
  if kind(role)=='audit':spec(inputs['body'],CAPS[role.split(':')[3]]*M)
  elif inputs['body'] is not None:raise ValueError('generator body refused')
 return kind(role)

def verify_certificate(value):
 if type(value) is not dict or set(value)!= {'schema','mode','draws'} or value['schema']!='CONTEXT90-CROSSED-DRAWS-v1' or value['mode']!='primary' or type(value['draws']) is not list or len(value['draws'])!=9:raise ValueError('draw certificate')
 tuples=[]
 for i,d in enumerate(value['draws']):
  if type(d) is not dict or set(d)!= {'tuple_id','words','rank'} or d['tuple_id']!='C90X1-P'+str(i).zfill(2):raise ValueError('draw identity')
  integer(d['rank'],0,FAMILY-1)
  if decode_words(d['words'])!=d['rank']:raise ValueError('raw draw/rank mismatch')
  tuples.append(decode_rank(d['rank']))
 return tuples

def tuple_for(mode,index,certificate=None):
 integer(index,0,0 if mode=='software' else 8);config(mode)
 if mode=='software':
  if certificate is not None:raise ValueError('software draw refused')
  return dict(c=0,A=45,C=213,B=154)
 if certificate is None:raise ValueError('registered draw input required')
 return verify_certificate(certificate)[index]

def definition(t):
 if type(t) is not dict or set(t)!= {'c','A','B','C'}:raise ValueError('tuple definition')
 integer(t['c'],0,7)
 for k in ('A','B','C'):integer(t[k],0,255)
 a=(t['A']//(2**t['c']))%2
 if t['A']==t['C'] or (t['C']//(2**t['c']))%2!=a or (t['B']//(2**t['c']))%2==a:raise ValueError('matched family')

def mask(t,cell,trial):
 definition(t)
 if cell not in CELLS:raise ValueError('case')
 integer(trial,0,111)
 return t[cell[0]] if trial<80 else t['B'] if trial<96 else t[cell[1]]

def observation(t,index,trial,channel):
 definition(t);integer(trial,0,111);integer(index,0,8)
 if channel=='cue':return (t['c']+trial)%8
 if channel=='pre':return (3*trial+index)%8
 if channel=='post':return (5*trial+1+index)%8
 raise ValueError('observation channel')
