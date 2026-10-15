"""Finite typed software/primary custody; no World or target imports."""
M=1024**2
CONTRACT='2c702fb7e523109c3bc58605aa1f2703178a4585edc268471e1095227299e3d6'
SEEDS={'software':(2100488,2100489),'primary':tuple(range(1010100,1010106))+tuple(range(1010300,1010306))}
ACTORS=tuple(f'{a}:{i}' for a in ('adaptive','history_reset','credit_misbound','explore') for i in range(4))+('fixed0','fixed1','cue_identity','cue_inverse','fixed_alternation','latest_reactive')+tuple('rr'+str(i) for i in range(4))
def config(mode):
 assert mode in SEEDS
 return dict(version='STRATEGY88-CUSTODY-v1',mode=mode,seeds=list(SEEDS[mode]),actors=list(ACTORS),software_only=mode=='software',
  contract_sha256=CONTRACT,horizon=1024,warm=48,decisions=60,cost_budget=512,max_population=1,expansion_tick=0,vm_mode='no_variation')
def roles(mode):
 return tuple(r for s in SEEDS[mode] for r in (f'original:{s}:generate',f'original:{s}:audit',f'restored:{s}:generate',f'original:{s}:metrics'))+(('original:all:accept',) if mode=='primary' else ())
def capacity(role):return (64 if role.endswith(':generate') else 8)*M
def scope(request):
 assert type(request) is dict and set(request)=={'configuration','source_files','source_sha','config_sha','role','kind','input','grant','seal'}
 import json
 c=request['configuration'];assert type(c) is dict and json.dumps(c,sort_keys=True)==json.dumps(config(c.get('mode')),sort_keys=True)
 assert request['role'] in roles(c['mode']) and request['kind']==request['role'].split(':')[-1]
 kind=request['kind'];value=request['input']
 if kind=='generate':assert value is None
 elif kind=='audit':spec_shape(value,64*M)
 elif kind=='metrics':
  seed=int(request['role'].split(':')[1]);assert type(value) is list and len(value)==3
  for chain,role in zip(value,(f'original:{seed}:generate',f'original:{seed}:audit',f'restored:{seed}:generate'),strict=True):chain_shape(chain,role)
 else:
  assert c['mode']=='primary' and type(value) is dict and set(value)=={str(s) for s in SEEDS['primary']}
  for seed in SEEDS['primary']:chain_shape(value[str(seed)],f'original:{seed}:metrics')
 return kind
def spec_shape(s,cap):
 from pathlib import Path
 assert type(s) is dict and set(s)=={'path','extent','sha256'}
 assert type(s['path']) is str and Path(s['path']).is_absolute()
 assert type(s['extent']) is int and 0<s['extent']<=cap
 assert type(s['sha256']) is str and len(s['sha256'])==64 and all(c in '0123456789abcdef' for c in s['sha256'])
def chain_shape(chain,role):
 assert type(chain) is dict and set(chain)=={'role','body','request','native'} and chain['role']==role
 for k,cap in (('body',capacity(role)),('request',65536),('native',M)):spec_shape(chain[k],cap)
def layout(mode,sources,owners,reg_size):
 assert mode in SEEDS and 0<reg_size<=65536 and sum(sources.values())*2<=8*M and sum(owners.values())<=16*M
 raw={'registration.json':65536,'source.zip':4*M}
 for name,n in sources.items():
  assert 0<n<=M
  for export in ('original','restored'):raw[export+'/'+name]=n
 for name,n in owners.items():assert 0<n<=8*M;raw['owners/'+name]=n
 for role in roles(mode):raw['data/'+role.replace(':','-')+'.json']=capacity(role)
 stems=[r.replace(':','-') for r in roles(mode)]+['refused'+str(i) for i in range(4)]+(['pure-original','pure-restored'] if mode=='software' else [])
 for stem in stems:raw['native/'+stem+'.json']=M;raw['request/'+stem+'.json']=65536
 failure={'outcome.json':64*M,'budget.json':64*M}
 limit=dict(raw=sum(raw.values()),failure=128*M,restore=sum(raw.values())+128*M,archive=sum(raw.values())+136*M)
 ceilings=dict(raw=512,archive=640,restore=640,failure=128) if mode=='software' else dict(raw=2304,archive=2560,restore=2560,failure=128)
 assert all(limit[k]<=v*M for k,v in ceilings.items())
 return raw,failure,limit
def orchestrate(mode,refuse,invoke,verify):
 for key in ('role','configuration','source_sha','seal'):refuse(key)
 metrics={};endpoints=[];software_admission=True
 for seed in SEEDS[mode]:
  original=None;chains=[]
  for role in (f'original:{seed}:generate',f'original:{seed}:audit',f'restored:{seed}:generate'):
   result=invoke(role,original if role.endswith(':audit') else None);v=result['value'];s=result['spec']
   assert v['seed']==seed and v['software_only'] is (mode=='software')
   if role.endswith(':generate'):
    assert v['error'] is None and v['genesis_attempts']==26 and [r['role'] for r in v['records']]==list(ACTORS)
    if role.startswith('original:'):original=s
    else:assert (s['extent'],s['sha256'])==(original['extent'],original['sha256'])
   else:
    assert v['verified'] is True and v['evidence_inputs']==original and [r['role'] for r in v['summaries']]==list(ACTORS)
    assert all(r['physics']['verified'] is True for r in v['summaries'])
   verify(role,result);chains.append(result['chain']);del result,v
  role=f'original:{seed}:metrics';result=invoke(role,chains);v=result['value']
  assert v['seed']==seed and v['execution_admission'] is False and len(v['endpoints'])==4
  if mode=='software':
   software_admission=software_admission and all(r['completed']==60 and r['successes']>=54 and r['C']<=477 and sorted(r['warm_packets'])==list(range(48)) for r in v['rows'] if r['role'].startswith('adaptive:'))
  metrics[str(seed)]=result['chain'];endpoints.extend(v['endpoints']);verify(role,result);del result,v,chains
 arithmetic=None
 if mode=='primary':
  result=invoke('original:all:accept',metrics);arithmetic=result['value'];assert arithmetic['numeric_interface_only'] and arithmetic['execution_admission'] is False
  verify('original:all:accept',result)
 return dict(metric_specs=metrics,endpoints=endpoints,arithmetic=arithmetic,software_admission=software_admission if mode=='software' else None)
