"""Source/config/role/grant guarded finite SOFTWARE roles; no admission by string."""
import hashlib,json,sys
from pathlib import Path
from experiments import digital_credited_fallback87v2_primary_boundary as boundary
from experiments import evidence_write_grant68 as transport
from experiments import digital_context90_plan_v1 as plan

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
 from experiments.digital_context90_task_source_v1 import programme
 from experiments.digital_context90_world_v2 import World
 from experiments.digital_memory80_recording import terminal_view
 records=[];attempts=0;constructed=0;error=None
 for role in plan.BATCHES[batch]:
  world=None
  try:
   attempts+=1;world=World(seed,role,'CONTEXT90-SOFTWARE-v1');constructed+=1
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
 from experiments.digital_context90_referee_v2 import audit as literal,programme
 assert 'experiments.digital_context90_engine_v2' not in sys.modules
 body=read(request['input'],64*M);actors=list(plan.BATCHES[batch])
 assert body['version']==c['version'] and body['seed']==seed and body['batch']==batch and body['software_only'] is True and body['error'] is None
 assert type(body['genesis_attempts']) is int and body['genesis_attempts']==body['completed_constructors']==len(actors)
 assert [r['role'] for r in body['records']]==actors
 def evaluate(row):
  assert row['programme']==programme(row['role'])
  return literal(row['state'],seed=seed,mode='no_variation',max_population=1,expansion_tick=0,program=row['programme'],horizon=1200,
   ledger=row['ledger'],role=row['role'],admission='CONTEXT90-SOFTWARE-v1')
 summaries=[dict(role=row['role'],physics=evaluate(row)) for row in body['records']]
 forged=[]
 if seed==2100690 and batch=='learners':
  for kind in ('target','observation','feedback','field_read','field_write','logic_fee','cost','hash','truncation'):
   row=json.loads(json.dumps(body['records'][0]))
   if kind=='target':next(e['attempt'] for e in row['state']['events'] if 'attempt' in e)['target']^=1
   elif kind=='observation':next(l['observation'] for l in row['ledger'] if l['observation'] is not None)['value']^=1
   elif kind=='feedback':next(e for e in row['state']['events'] if 'read_feedback' in e)['read_feedback']^=1
   elif kind in ('field_read','field_write'):
    key='read' if kind=='field_read' else 'write'
    items=[e['packed'][key] for e in row['state']['events'] if 'packed' in e and e['packed'][key] is not None]
    if not items:continue # Death/shortfall cannot become a capability gate.
    items[0]['value']^=1
   elif kind=='logic_fee':next(e for e in row['state']['events'] if 'packed' in e)['logic_fee']+=1
   elif kind=='cost':row['ledger'][0]['cost_after']+=1
   elif kind=='hash':row['state']['events'][0]['before']='0'*64
   else:row['state']['events'].pop();row['ledger'].pop()
   try:evaluate(row)
   except (AssertionError,ValueError,KeyError,IndexError):forged.append(kind)
   else:raise AssertionError('Literal forgery accepted: '+kind)
 return dict(verified=True,version=c['version'],software_only=True,seed=seed,batch=batch,producer_imported=False,evidence_inputs=request['input'],summaries=summaries,forgeries_rejected=forged,stage_credit=False)


def main():
 request=json.loads(boundary.bounded_bytes(Path(sys.argv[1]),65536),object_pairs_hook=boundary.pairs)
 kind=plan.scope(request);c=request['configuration'];root=Path.cwd();pins=request['source_files']
 assert Path(__file__).resolve()==root/'experiments/digital_context90_child_v1.py' and 'experiments/digital_context90_child_v1.py' in pins
 ss=hashlib.sha256(enc(pins)).hexdigest();cs=hashlib.sha256(enc(c)).hexdigest()
 assert ss==request['source_sha'] and cs==request['config_sha'] and boundary.verify_source(root,pins)==ss
 assert request['grant']['limit']==plan.capacity(request['role'])
 boundary.validate_grant(dict(grant=request['grant'],grant_seal=request['seal'],configuration_sha256=cs,role=request['role']),ss,'recording' if kind=='generate' else 'proof')
 error=None
 seed=int(request['role'].split(':')[1])
 if kind=='generate':value=generate(seed,request['role'].split(':')[2],c);error=value['error']
 else:value=audit(request,seed,request['role'].split(':')[2],c)
 boundary.module_origins(root,pins);assert boundary.verify_source(root,pins)==ss
 receipt=transport.record(request['grant'],request['seal'],ss,cs,request['role'],value)
 print(enc(dict(role=request['role'],source_sha=ss,config_sha=cs,receipt=receipt)).decode());assert error is None,error

if __name__=='__main__':
 try:main()
 except BaseException:
  print(enc(dict(rejected_before_world='experiments.digital_context90_engine_v2' not in sys.modules)).decode());raise
