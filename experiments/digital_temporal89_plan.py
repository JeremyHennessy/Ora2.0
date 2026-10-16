"""Finite software custody graph and typed request scope;no targets or Worlds."""
M=1024**2
CONTRACT='3095e9f662466fb5cefed1605599041e1c6ca31e247abd119caf05613e6620c1'
SEEDS={'software':(2100589,2100590)} # Primary execution is deliberately not implemented/admitted.
ARMS=('intact','credit_erased','recall_disabled','model_disabled','update_frozen')
REFERENCES=('fixed0','fixed1','retained_cue','retained_inverse','current_distractor','current_inverse','alternation0','alternation1','latest0','latest1')
BATCHES={f'q{q}':tuple(f'q{q}:{a}' for a in ARMS) for q in (2,4,8)}
BATCHES['references']=REFERENCES
ACTORS=tuple(r for rs in BATCHES.values() for r in rs)

def config(mode):
 assert type(mode) is str and mode=='software'
 return dict(version='TEMPORAL89-CUSTODY-v1',mode=mode,seeds=list(SEEDS[mode]),actors=list(ACTORS),
  batches={k:list(v) for k,v in BATCHES.items()},software_only=True,contract_sha256=CONTRACT,
  horizon=1024,warm=48,decisions=60,cost_budget=1024,max_population=1,expansion_tick=0,vm_mode='no_variation')

def roles(mode):
 assert mode in SEEDS
 return tuple(role for seed in SEEDS[mode] for role in (
   *tuple(r for batch in BATCHES for r in (f'original:{seed}:{batch}:generate',f'original:{seed}:{batch}:audit',f'restored:{seed}:{batch}:generate')),
   f'original:{seed}:metrics'))+('original:all:accept',)

def capacity(role):return (64 if role.endswith(':generate') else 8)*M

def spec_shape(s,cap):
 from pathlib import Path
 assert type(s) is dict and set(s)=={'path','extent','sha256'}
 assert type(s['path']) is str and Path(s['path']).is_absolute()
 assert type(s['extent']) is int and 0<s['extent']<=cap
 assert type(s['sha256']) is str and len(s['sha256'])==64 and all(c in '0123456789abcdef' for c in s['sha256'])

def chain_shape(chain,role):
 assert type(chain) is dict and set(chain)=={'role','body','request','native'} and chain['role']==role
 for k,cap in (('body',capacity(role)),('request',65536),('native',M)):spec_shape(chain[k],cap)

def scope(request):
 import json
 assert type(request) is dict and set(request)=={'configuration','source_files','source_sha','config_sha','role','kind','input','grant','seal'}
 c=request['configuration'];assert type(c) is dict and json.dumps(c,sort_keys=True)==json.dumps(config(c.get('mode')),sort_keys=True)
 assert type(request['role']) is str and request['role'] in roles(c['mode'])
 assert request['kind']==request['role'].split(':')[-1]
 kind=request['kind'];value=request['input']
 if kind=='generate':assert value is None
 elif kind=='audit':spec_shape(value,64*M)
 elif kind=='metrics':
  seed=int(request['role'].split(':')[1]);assert type(value) is dict and list(value)==list(BATCHES)
  for batch in BATCHES:
   assert type(value[batch]) is list and len(value[batch])==3
   for chain,role in zip(value[batch],(f'original:{seed}:{batch}:generate',f'original:{seed}:{batch}:audit',f'restored:{seed}:{batch}:generate'),strict=True):chain_shape(chain,role)
 else:
  assert kind=='accept' and type(value) is dict and set(value)=={str(s) for s in SEEDS[c['mode']]}
  for seed in SEEDS[c['mode']]:chain_shape(value[str(seed)],f'original:{seed}:metrics')
 return kind

def layout(mode,sources,owners,reg_size):
 assert mode=='software' and 0<reg_size<=65536 and sum(sources.values())*2<=4*M and sum(owners.values())<=16*M
 raw={'registration.json':65536,'source.zip':2*M}
 for name,n in sources.items():
  assert 0<n<=M
  for export in ('original','restored'):raw[export+'/'+name]=n
 for name,n in owners.items():assert 0<n<=8*M;raw['owners/'+name]=n
 for role in roles(mode):raw['data/'+role.replace(':','-')+'.json']=capacity(role)
 for stem in [r.replace(':','-') for r in roles(mode)]+['refused'+str(i) for i in range(4)]:
  raw['native/'+stem+'.json']=M;raw['request/'+stem+'.json']=65536
 failure={'outcome.json':64*M,'budget.json':64*M}
 limits=dict(raw=sum(raw.values()),failure=128*M,restore=sum(raw.values())+128*M,archive=sum(raw.values())+136*M)
 ceilings=dict(raw=1664,archive=1792,restore=1792,failure=128)
 assert all(limits[k]<=v*M for k,v in ceilings.items())
 assert sum(limits.values())<=5376*M
 return raw,failure,limits

def orchestrate(mode,refuse,invoke,verify):
 assert mode=='software'
 for key in ('role','configuration','source_sha','seal'):refuse(key)
 metrics={}
 for seed in SEEDS[mode]:
  batches={}
  for batch,actors in BATCHES.items():
   original=None;chains=[]
   for role in (f'original:{seed}:{batch}:generate',f'original:{seed}:{batch}:audit',f'restored:{seed}:{batch}:generate'):
    result=invoke(role,original if role.endswith(':audit') else None);value=result['value'];spec=result['spec']
    assert value['seed']==seed and value['batch']==batch and value['software_only'] is True
    if role.endswith(':generate'):
     assert value['error'] is None and value['genesis_attempts']==value['completed_constructors']==len(actors)
     assert [r['role'] for r in value['records']]==list(actors)
     if role.startswith('original:'):original=spec
     else:assert (spec['extent'],spec['sha256'])==(original['extent'],original['sha256'])
    else:
     assert value['verified'] is True and value['evidence_inputs']==original
     assert [r['role'] for r in value['summaries']]==list(actors) and all(r['physics']['verified'] is True for r in value['summaries'])
    verify(role,result);chains.append(result['chain']);del result,value
   batches[batch]=chains
  role=f'original:{seed}:metrics';result=invoke(role,batches);value=result['value']
  assert value['seed']==seed and value['execution_admission'] is False and value['roles']==list(ACTORS)
  assert len(value['rows'])==25 and [e['capacity'] for e in value['endpoints']]==[2,4,8]
  metrics[str(seed)]=result['chain'];verify(role,result);del result,value,batches
 result=invoke('original:all:accept',metrics);value=result['value']
 assert value['verified'] is True and value['software_only'] is True and value['execution_admission'] is False
 assert value['scope']=='SOFTWARE complete-denominator/custody only,no scientific acceptance'
 verify('original:all:accept',result)
 return dict(metric_specs=metrics,scope_only_final=value,software_admission=True)
