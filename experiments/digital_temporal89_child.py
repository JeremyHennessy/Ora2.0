"""Source/config/role/grant guarded finite SOFTWARE roles; no admission by string."""
import hashlib,json,sys
from pathlib import Path
from experiments import digital_credited_fallback87v2_primary_boundary as boundary
from experiments import evidence_write_grant68 as transport
from experiments import digital_temporal89_plan as plan

enc=boundary.canonical;M=1024**2

def read(s,cap):
 plan.spec_shape(s,cap)
 from experiments.digital_recording82_reader import read_spec
 return read_spec(s)

def authenticate(chain,request):
 from experiments.digital_credited_fallback87v2_metric_binding import authenticate as bind
 old=read(chain['request'],65536);native=read(chain['native'],M);plan.scope(old)
 assert old['source_files']==request['source_files'] and old['source_sha']==request['source_sha'] and old['config_sha']==request['config_sha']
 assert old['grant']['root']==request['grant']['root']
 p=Path(chain['body']['path']);info=transport.plain(p)
 actual=str(Path(old['grant']['root'])/old['grant']['phase']/old['grant']['name'])
 bind(old,native,chain['body'],chain['role'],request['configuration'],actual,(info.st_dev,info.st_ino))
 export=chain['role'].split(':')[0]
 assert boundary.verify_source(Path(old['grant']['root'])/'raw'/export,old['source_files'])==request['source_sha']
 return old

def generate(seed,batch,c):
 from experiments.digital_temporal89_source import programme
 from experiments.digital_temporal89_world import World
 from experiments.digital_memory80_recording import terminal_view
 records=[];attempts=0;constructed=0;error=None
 for role in plan.BATCHES[batch]:
  world=None
  try:
   attempts+=1;world=World(seed,role,'TEMPORAL89-SOFTWARE-v1');constructed+=1
   while world.step():
    assert len(enc(world.events[-1]))+len(enc(world.control_ledger()[-1]))<=4096,'Registered event union extent'
   records.append(dict(role=role,programme=programme(role),state=terminal_view(world.__dict__),ledger=world.control_ledger(),stop_reason=world.stop_reason()))
  except BaseException as exc:
   error=repr(exc);partial=None;partial_error=None
   if world is not None:
    try:partial=dict(state=terminal_view(world.__dict__),ledger=world.control_ledger())
    except BaseException as recovery:partial_error=repr(recovery)
   records.append(dict(role=role,error=error,partial=partial,partial_error=partial_error));break
 return dict(version=c['version'],software_only=True,seed=seed,batch=batch,genesis_attempts=attempts,completed_constructors=constructed,records=records,error=error)

def audit(request,seed,batch,c):
 from experiments.digital_temporal89_referee import audit as literal,programme
 assert 'experiments.digital_memory80' not in sys.modules
 body=read(request['input'],64*M);actors=list(plan.BATCHES[batch])
 assert body['version']==c['version'] and body['seed']==seed and body['batch']==batch and body['software_only'] is True and body['error'] is None
 assert type(body['genesis_attempts']) is int and body['genesis_attempts']==body['completed_constructors']==len(actors)
 assert [r['role'] for r in body['records']]==actors
 def evaluate(row):
  assert row['programme']==programme(row['role'])
  return literal(row['state'],seed=seed,mode='no_variation',max_population=1,expansion_tick=0,program=row['programme'],horizon=1024,
   ledger=row['ledger'],role=row['role'],admission='TEMPORAL89-SOFTWARE-v1')
 summaries=[dict(role=row['role'],physics=evaluate(row)) for row in body['records']]
 forged=[];not_applicable=[]
 if seed==2100589 and batch=='q8':
  for kind in ('target','observation','feedback','cut','decision_read','updater_read','store','cost','hash','truncation'):
   row=json.loads(json.dumps(body['records'][0] if kind!='cut' else body['records'][1]));found=True
   if kind=='target':next(e['attempt'] for e in row['state']['events'] if 'attempt' in e)['target']^=1
   elif kind=='observation':next(l['observation'] for l in row['ledger'] if l['observation'] is not None)['value']^=1
   elif kind=='feedback':next(e for e in row['state']['events'] if 'read_feedback' in e)['read_feedback']^=1
   elif kind in ('decision_read','updater_read'):
    pc=3 if kind=='decision_read' else 9;items=[l['read'] for l in row['ledger'] if l['read'] is not None and l['read']['pc']==pc]
    if items:items[0]['returned']^=1
    else:found=False
   elif kind in ('cut','store'):
    items=[l[kind] for l in row['ledger'] if l[kind] is not None]
    if items:items[0]['after' if kind=='cut' else 'applied']^=1
    else:found=False
   elif kind=='cost':row['ledger'][0]['cost_after']+=1
   elif kind=='hash':row['state']['events'][0]['before']='0'*64
   else:row['state']['events'].pop();row['ledger'].pop()
   if found:
    try:evaluate(row)
    except (AssertionError,KeyError,IndexError):forged.append(kind)
    else:raise AssertionError('Literal forgery accepted: '+kind)
   else:not_applicable.append(kind) # Valid death/shortfall must never become a physics rejection.
   del row
 return dict(verified=True,version=c['version'],software_only=True,seed=seed,batch=batch,producer_imported=False,
  evidence_inputs=request['input'],summaries=summaries,forgeries_rejected=forged,forgeries_not_applicable=not_applicable,stage_credit=False)

def metrics(request,seed):
 from experiments.digital_temporal89_metrics import derive_row,context
 rows=[]
 for batch in plan.BATCHES:
  chains=request['input'][batch]
  for chain in chains:authenticate(chain,request)
  original,proof,replay=chains
  assert (original['body']['extent'],original['body']['sha256'])==(replay['body']['extent'],replay['body']['sha256'])
  old=read(proof['request'],65536);assert old['input']==original['body']
  body=read(original['body'],64*M);evidence=read(proof['body'],8*M)
  assert body['error'] is None and body['seed']==evidence['seed']==seed and body['batch']==evidence['batch']==batch
  assert evidence['evidence_inputs']==original['body'] and evidence['verified'] is True and evidence['producer_imported'] is False
  assert [r['role'] for r in body['records']]==[r['role'] for r in evidence['summaries']]==list(plan.BATCHES[batch])
  for row,summary in zip(body['records'],evidence['summaries'],strict=True):
   assert summary['physics']['verified'] is True
   value=derive_row(row);assert value['completed']==summary['physics']['completed'] and value['physical']['C']==summary['physics']['charged_cost']
   rows.append(value);del value
  # Neither loop variable may keep the previous complete body alive on next read.
  del row,summary,body,evidence,old
 value=context(seed,rows);value['input_chains']=request['input'];return value

def accept(request):
 contexts=[]
 for seed in plan.SEEDS['software']:
  chain=request['input'][str(seed)];old=authenticate(chain,request);value=read(chain['body'],8*M)
  assert value['seed']==seed and value['execution_admission'] is False and value['source_free'] is True
  assert value['input_chains']==old['input'] and value['roles']==list(plan.ACTORS) and len(value['rows'])==25
  assert [e['capacity'] for e in value['endpoints']]==[2,4,8]
  contexts.append(dict(seed=seed,rows=[dict(role=r['role'],completed=r['completed'],physical=r['physical'],warm_energy=r['warm_energy']) for r in value['rows']]))
  del value,old
 return dict(verified=True,software_only=True,scope='SOFTWARE complete-denominator/custody only,no scientific acceptance',
  contexts=contexts,evidence_inputs=request['input'],execution_admission=False,stage_credit=False)

def main():
 request=json.loads(boundary.bounded_bytes(Path(sys.argv[1]),65536),object_pairs_hook=boundary.pairs)
 kind=plan.scope(request);c=request['configuration'];root=Path.cwd();pins=request['source_files']
 assert Path(__file__).resolve()==root/'experiments/digital_temporal89_child.py' and 'experiments/digital_temporal89_child.py' in pins
 ss=hashlib.sha256(enc(pins)).hexdigest();cs=hashlib.sha256(enc(c)).hexdigest()
 assert ss==request['source_sha'] and cs==request['config_sha'] and boundary.verify_source(root,pins)==ss
 assert request['grant']['limit']==plan.capacity(request['role'])
 boundary.validate_grant(dict(grant=request['grant'],grant_seal=request['seal'],configuration_sha256=cs,role=request['role']),ss,'recording' if kind=='generate' else 'proof')
 error=None
 if kind=='accept':value=accept(request)
 else:
  seed=int(request['role'].split(':')[1])
  if kind=='generate':value=generate(seed,request['role'].split(':')[2],c);error=value['error']
  elif kind=='audit':value=audit(request,seed,request['role'].split(':')[2],c)
  else:value=metrics(request,seed)
 boundary.module_origins(root,pins);assert boundary.verify_source(root,pins)==ss
 if kind in ('metrics','accept'):
  assert not any(n.endswith(('_source','_world','_referee','_programme')) or n=='experiments.digital_memory80' for n in sys.modules if n.startswith('experiments.'))
 receipt=transport.record(request['grant'],request['seal'],ss,cs,request['role'],value)
 print(enc(dict(role=request['role'],source_sha=ss,config_sha=cs,receipt=receipt)).decode());assert error is None,error

if __name__=='__main__':
 try:main()
 except BaseException:
  print(enc(dict(rejected_before_world='experiments.digital_memory80' not in sys.modules)).decode());raise
