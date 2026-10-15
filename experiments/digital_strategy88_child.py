"""Typed source/grant guarded roles; constructors occur only after all guards."""
import hashlib,json,sys
from pathlib import Path
from experiments import digital_credited_fallback87v2_primary_boundary as boundary
from experiments import evidence_write_grant68 as transport
from experiments import digital_strategy88_plan as plan
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
def generate(seed,c):
 from experiments.digital_strategy88_source import ROLES,programme,ADMISSION
 from experiments.digital_strategy88_world import World
 from experiments.digital_memory80_recording import terminal_view
 records=[];attempts=0;constructed=0;error=None
 for role in ROLES:
  world=None
  try:
   attempts+=1;world=World(seed,role,ADMISSION if c['mode']=='primary' else None);constructed+=1
   while world.step():pass
   records.append(dict(role=role,programme=programme(role),state=terminal_view(world.__dict__),ledger=world.control_ledger(),stop_reason=world.stop_reason()))
  except BaseException as exc:
   error=repr(exc);partial=None;ledger=None;partial_error=None
   try:
    if world is not None:partial=terminal_view(world.__dict__);ledger=world.control_ledger()
   except BaseException as recovery:partial_error=repr(recovery)
   records.append(dict(role=role,programme=programme(role),state=partial,ledger=ledger,error=error,partial_error=partial_error));break
 return dict(version=c['version'],software_only=c['software_only'],seed=seed,genesis_attempts=attempts,completed_constructors=constructed,records=records,error=error)
def audit(request,seed,c):
 from experiments.digital_strategy88_referee import audit as literal,programme
 assert 'experiments.digital_memory80' not in sys.modules
 body=read(request['input'],64*M)
 assert body['version']==c['version'] and body['seed']==seed and body['software_only'] is c['software_only'] and body['error'] is None
 assert type(body['genesis_attempts']) is int and body['genesis_attempts']==body['completed_constructors']==26
 assert [r['role'] for r in body['records']]==c['actors']
 def evaluate(row):
  assert row['programme']==programme(row['role'])
  return literal(row['state'],seed=seed,mode='no_variation',max_population=1,expansion_tick=0,program=row['programme'],horizon=1024,
   ledger=row['ledger'],role=row['role'],admission='STRATEGY88-v1' if c['mode']=='primary' else None)
 summaries=[]
 for row in body['records']:summaries.append(dict(role=row['role'],physics=evaluate(row)))
 forged=0
 if c['mode']=='software' and seed==2100488:
  for kind in ('target','entry','cost','programme','hash','truncation'):
   row=json.loads(json.dumps(body['records'][0]))
   if kind=='programme':row['programme'][1][2]^=1
   elif kind=='truncation':row['state']['events'].pop();row['ledger'].pop()
   elif kind=='hash':row['state']['events'][0]['before']='0'*64
   elif kind=='cost':row['ledger'][0]['cost_after']+=1
   elif kind=='entry':
    item=next(x for x in row['ledger'] if x['entry'] is not None);item['entry']['projected_entry']=16 if item['entry']['projected_entry']!=16 else 1
   else:next(x['attempt'] for x in row['state']['events'] if 'attempt' in x)['target']^=1
   try:evaluate(row)
   except (AssertionError,KeyError,IndexError):forged+=1
   else:raise AssertionError('Literal forgery accepted: '+kind)
   del row
  assert forged==6
 return dict(verified=True,version=c['version'],software_only=c['software_only'],seed=seed,producer_imported=False,evidence_inputs=request['input'],summaries=summaries,forgeries_rejected=forged,stage_credit=False)
def metrics(request,seed):
 from experiments.digital_strategy88_metrics import derive
 chains=request['input']
 for chain in chains:authenticate(chain,request)
 original,proof,replay=chains
 assert (original['body']['extent'],original['body']['sha256'])==(replay['body']['extent'],replay['body']['sha256'])
 old=read(proof['request'],65536);assert old['input']==original['body']
 body=read(original['body'],64*M);evidence=read(proof['body'],8*M);assert evidence['evidence_inputs']==original['body']
 value=derive(body,evidence);value['input_chains']=chains;return value
def accept(request):
 from experiments.digital_strategy88_acceptance import interpret
 endpoints=[]
 for seed in plan.SEEDS['primary']:
  chain=request['input'][str(seed)];old=authenticate(chain,request);value=read(chain['body'],8*M)
  assert value['seed']==seed and value['software_only'] is False and value['execution_admission'] is False
  assert value['input_chains']==old['input'] and [r['prior'] for r in value['endpoints']]==list(range(4))
  endpoints.extend(value['endpoints']);del old,value
 value=interpret(endpoints);value['evidence_inputs']=request['input'];return value
def main():
 request=json.loads(boundary.bounded_bytes(Path(sys.argv[1]),65536),object_pairs_hook=boundary.pairs)
 kind=plan.scope(request);c=request['configuration'];root=Path.cwd();pins=request['source_files']
 assert Path(__file__).resolve()==root/'experiments/digital_strategy88_child.py' and 'experiments/digital_strategy88_child.py' in pins
 ss=hashlib.sha256(enc(pins)).hexdigest();cs=hashlib.sha256(enc(c)).hexdigest()
 assert ss==request['source_sha'] and cs==request['config_sha'] and boundary.verify_source(root,pins)==ss
 assert request['grant']['limit']==plan.capacity(request['role'])
 boundary.validate_grant(dict(grant=request['grant'],grant_seal=request['seal'],configuration_sha256=cs,role=request['role']),ss,'recording' if kind=='generate' else 'proof')
 error=None
 if kind=='accept':value=accept(request)
 else:
  seed=int(request['role'].split(':')[1])
  if kind=='generate':value=generate(seed,c);error=value['error']
  elif kind=='audit':value=audit(request,seed,c)
  else:value=metrics(request,seed)
 boundary.module_origins(root,pins);assert boundary.verify_source(root,pins)==ss
 if kind in ('metrics','accept'):
  assert not any(n.endswith(('_source','_world','_referee')) or n=='experiments.digital_memory80' for n in sys.modules if n.startswith('experiments.'))
 receipt=transport.record(request['grant'],request['seal'],ss,cs,request['role'],value)
 print(enc(dict(role=request['role'],source_sha=ss,config_sha=cs,receipt=receipt)).decode());assert error is None,error
if __name__=='__main__':
 try:main()
 except BaseException:
  print(enc(dict(rejected_before_world='experiments.digital_memory80' not in sys.modules)).decode());raise
