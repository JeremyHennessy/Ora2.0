"""Frozen finite crossed custody graph; no entropy, engine or constructor imports."""
from experiments import digital_context90_crossed_registry_v1 as registry
from experiments import digital_context90_crossed_metrics_v1 as metrics
from experiments.digital_context90_crossed_programme_v1 import BATCHES
M=1024**2
CONTRACT=registry.CONTRACT
config=registry.config
roles=registry.roles
capacity=registry.capacity


def layout(mode,sources,owners,reg_size):
 c=config(mode);assert type(reg_size) is int and 0<reg_size<=65536
 assert sum(sources.values())<=3*M and sum(owners.values())<=32*M
 assert sum(sources.values())+512*len(sources)<=4*M
 raw={'registration.json':65536,'source.zip':4*M}
 for name,n in sources.items():
  assert type(n) is int and 0<n<=M
  for export in ('original','restored'):raw[export+'/'+name]=n
 for name,n in owners.items():assert type(n) is int and 0<n<=16*M;raw['owners/'+name]=n
 for role in roles(mode):raw['data/'+role.replace(':','-')+'.json']=capacity(role)
 for stem in [r.replace(':','-') for r in roles(mode)]+['refused'+str(i) for i in range(4)]:raw['request/'+stem+'.json']=65536;raw['native/'+stem+'.json']=M
 failure={'outcome.json':32*M,'budget.json':32*M}
 ceilings=dict(raw=1536,failure=64,restore=1600,archive=1664) if mode=='software' else dict(raw=13312,failure=64,restore=13376,archive=13440)
 limits=dict(raw=sum(raw.values()),failure=64*M,restore=sum(raw.values())+64*M,archive=ceilings['archive']*M)
 assert all(limits[k]<=v*M for k,v in ceilings.items());assert sum(limits.values())<=(4864 if mode=='software' else 40192)*M
 return raw,failure,limits


def prefix_shape(p,role):
 assert type(p) is dict and set(p)=={'schema','role','programme_sha256','stream_sha256','events','cut_state_sha256','cut_trial'} and p['schema']=='CONTEXT90-CROSSED-PREFIX-v1' and p['role']==role
 for k in ('programme_sha256','stream_sha256','cut_state_sha256'):assert type(p[k]) is str and len(p[k])==64 and all(c in '0123456789abcdef' for c in p[k])
 assert type(p['events']) is int and 1<=p['events']<=2040 and type(p['cut_trial']) is int and 0<=p['cut_trial']<=96


def orchestrate(mode,refuse,invoke,verify):
 c=config(mode)
 for key in ('role','configuration','source_sha','seal'):refuse(key)
 draw=None;sampler=None
 if mode=='primary':
  sampler=invoke('primary:sampler',None);registry.verify_certificate(sampler['value']);draw=sampler['spec'];verify('primary:sampler',sampler)
 original=None;prefixes={};proof_rows=[];counts=dict(originals=0,replays=0,audits=0,prefix_pairs=0,completed112=0,deaths=0);case_rows=[]
 for role in roles(mode):
  if role=='primary:sampler':continue
  fields=role.split(':');index=int(fields[1]);cell=fields[2];batch=fields[3];kind=fields[-1];actors=BATCHES[batch]
  inputs=dict(body=original if kind=='audit' else None,draw=draw)
  result=invoke(role,inputs);v=result['value'];s=result['spec']
  assert v['mode']==mode and type(v['index']) is int and v['index']==index and v['cell']==cell and v['batch']==batch
  if kind=='generate':
   assert v['schema']=='CONTEXT90-CROSSED-BODY-v1' and v['error'] is None and type(v['genesis_attempts']) is int and v['genesis_attempts']==v['completed_constructors']==len(actors)
   assert [r['role'] for r in v['records']]==list(actors)
   if role.startswith('original:'):
    original=s;counts['originals']+=len(actors)
    for row in v['records']:
     completed=sum(l['completion'] is not None for l in row['ledger']);dead=row['state']['deaths'];counts['completed112']+=int(completed==112);counts['deaths']+=dead
     case_rows.append(dict(index=index,cell=cell,role=row['role'],completed=completed,deaths=dead,ticks=row['state']['tick'],stop_reason=row['stop_reason']))
   else:
    assert (s['extent'],s['sha256'])==(original['extent'],original['sha256']);counts['replays']+=len(actors)
  else:
   assert v['schema']=='CONTEXT90-CROSSED-PROOF-v1' and v['verified'] is True and v['producer_imported'] is False and v['evidence_inputs']==inputs
   assert [r['role'] for r in v['summaries']]==list(actors)
   for summary in v['summaries']:
    p=summary['physics'];actor=summary['role'];assert p['verified'] is True and p['scientific_worlds']==int(mode=='primary')
    row=p['metrics'];assert row['index']==index and row['cell']==cell and row['role']==actor;proof_rows.append(row)
    prefix_shape(p['prefix'],actor);key=(index,cell[0],actor)
    if cell in ('AA','CA'):assert key not in prefixes;prefixes[key]=p['prefix']
    else:assert prefixes.pop(key)==p['prefix'],'Paired full prefix mismatch';counts['prefix_pairs']+=1
   counts['audits']+=len(actors)
  verify(role,result);del v,result
 n=len(c['tuple_ids']);assert counts['originals']==counts['replays']==counts['audits']==n*4*19 and counts['prefix_pairs']==n*2*19 and not prefixes
 return dict(verified=True,software_admission=mode=='software',primary_closure=mode=='primary',execution_admission=False,stage_credit=False,totals=counts,cases=case_rows,metrics=metrics.aggregate(proof_rows,mode),sampler=None if sampler is None else sampler['spec'])
