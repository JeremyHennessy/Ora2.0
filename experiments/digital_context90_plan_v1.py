"""Finite new-version SOFTWARE custody only; no scientific context admission."""
M=1024**2
CONTRACT='6810c2e1c22b561534e2fb2f05f3d578254d4dfa6e42245d855c37d879e342f7'
SEEDS={'software':(2100690,2100691,2100692,2100693)}
REFERENCES=('fixed0','fixed1','retained_cue','retained_inverse','current_distractor','current_inverse','alternation0','alternation1','latest0','latest1')
BATCHES={'learners':tuple('q'+str(q)+':'+e for q in (2,4,8) for e in ('A','B')),'references':REFERENCES}
ACTORS=tuple(r for rs in BATCHES.values() for r in rs)

def config(mode):
 assert type(mode) is str and mode=='software'
 return dict(version='CONTEXT90-CUSTODY-v1',mode=mode,seeds=list(SEEDS[mode]),actors=list(ACTORS),batches={k:list(v) for k,v in BATCHES.items()},software_only=True,contract_sha256=CONTRACT,horizon=1200,decisions=60,cost_budget=1800,max_population=1,expansion_tick=0,vm_mode='no_variation',startup=200,factory=328,energy_cap=224)

def roles(mode):
 assert mode in SEEDS
 return tuple(r for seed in SEEDS[mode] for batch in BATCHES for r in (f'original:{seed}:{batch}:generate',f'original:{seed}:{batch}:audit',f'restored:{seed}:{batch}:generate'))

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
 if request['kind']=='generate':assert request['input'] is None
 else:assert request['kind']=='audit';spec_shape(request['input'],64*M)
 return request['kind']

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
 ceilings=dict(raw=1408,archive=1536,restore=1536,failure=128)
 assert all(limits[k]<=v*M for k,v in ceilings.items())
 assert sum(limits.values())<=4608*M
 return raw,failure,limits

def orchestrate(mode,refuse,invoke,verify):
 assert mode=='software'
 for key in ('role','configuration','source_sha','seal'):refuse(key)
 totals=dict(originals=0,replays=0,completed60=0,deaths=0,cpu=0,logic_fee=0,penalty=0,captured=0);rows=[]
 for seed in SEEDS[mode]:
  for batch,actors in BATCHES.items():
   original=None
   for role in (f'original:{seed}:{batch}:generate',f'original:{seed}:{batch}:audit',f'restored:{seed}:{batch}:generate'):
    result=invoke(role,original if role.endswith(':audit') else None);value=result['value'];spec=result['spec']
    assert value['seed']==seed and value['batch']==batch and value['software_only'] is True
    if role.endswith(':generate'):
     assert value['error'] is None and value['genesis_attempts']==value['completed_constructors']==len(actors)
     assert [r['role'] for r in value['records']]==list(actors)
     if role.startswith('original:'):
      original=spec;totals['originals']+=len(actors)
      for row in value['records']:
       events=row['state']['events'];ledger=row['ledger'];completed=sum(l['completion'] is not None for l in ledger)
       one=dict(seed=seed,role=row['role'],completed=completed,deaths=row['state']['deaths'],cpu=len(events),logic_fee=sum(e.get('logic_fee',0) for e in events),penalty=sum(e.get('penalty',0) for e in events),captured=sum(e.get('captured',0) for e in events),stop_reason=row['stop_reason'])
       rows.append(one);totals['completed60']+=int(completed==60)
       for k in ('deaths','cpu','logic_fee','penalty','captured'):totals[k]+=one[k]
     else:
      assert (spec['extent'],spec['sha256'])==(original['extent'],original['sha256']);totals['replays']+=len(actors)
    else:
     assert value['verified'] is True and value['evidence_inputs']==original
     assert [r['role'] for r in value['summaries']]==list(actors) and all(r['physics']['verified'] is True for r in value['summaries'])
    verify(role,result);del result,value
 assert totals['originals']==totals['replays']==64
 return dict(software_admission=True,execution_admission=False,stage_credit=False,totals=totals,rows=rows,scope='Known authored SOFTWARE physics/feasibility only; no scientific acceptance')
