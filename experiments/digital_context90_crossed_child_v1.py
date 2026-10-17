"""Finite crossed child. Entropy and World imports occur only after full main guard."""
import hashlib,json,sys
from pathlib import Path
from experiments import digital_credited_fallback87v2_primary_boundary as boundary
from experiments import evidence_write_grant68 as transport
from experiments import digital_context90_crossed_registry_v1 as registry
from experiments import digital_context90_crossed_programme_v1 as source
enc=boundary.canonical

def read(spec,cap):
 registry.spec(spec,cap)
 from experiments.digital_recording82_reader import read_spec
 return read_spec(spec)

def checked_definition(mode,index,cell,certificate):
 from experiments.digital_context90_crossed_referee_v1 import independent_case
 c=registry.config(mode);admission='CONTEXT90-CROSSED-'+mode.upper()+'-v1'
 producer=registry.tuple_for(mode,index,certificate);literal=independent_case(c['resource_seeds'][index],index,cell,admission,certificate)
 assert producer==literal
 return producer

def generate(index,cell,batch,c,certificate):
 checked_definition(c['mode'],index,cell,certificate)
 from experiments.digital_context90_crossed_world_v1 import World
 from experiments.digital_memory80_recording import terminal_view
 records=[];attempts=0;constructed=0;error=None
 for role in source.BATCHES[batch]:
  world=None
  try:
   attempts+=1;world=World(index,cell,role,c['mode'],certificate,'CONTEXT90-CROSSED-'+c['mode'].upper()+'-v1');constructed+=1
   while world.step():assert len(enc(world.events[-1]))+len(enc(world.control_ledger()[-1]))<=4096,'Registered crossed event union extent'
   records.append(dict(role=role,programme=source.programme(role),state=terminal_view(world.__dict__),ledger=world.control_ledger(),stop_reason=world.stop_reason()))
  except BaseException as exc:
   error=repr(exc);partial=None;partial_error=None
   if world is not None:
    try:partial=dict(state=terminal_view(world.__dict__),ledger=world.control_ledger())
    except BaseException as recovery:partial_error=repr(recovery)
   records.append(dict(role=role,error=error,partial=partial,partial_error=partial_error));break
 return dict(schema='CONTEXT90-CROSSED-BODY-v1',mode=c['mode'],index=index,cell=cell,batch=batch,genesis_attempts=attempts,completed_constructors=constructed,records=records,error=error)

def audit(index,cell,batch,c,inputs,certificate):
 from experiments.digital_context90_crossed_referee_v1 import audit as literal,programme
 assert not any(n in sys.modules for n in ('experiments.digital_context90_crossed_engine_v1','experiments.digital_context90_crossed_world_v1'))
 body=read(inputs['body'],registry.CAPS[batch]*registry.M)
 assert type(body) is dict and set(body)=={'schema','mode','index','cell','batch','genesis_attempts','completed_constructors','records','error'}
 assert body['schema']=='CONTEXT90-CROSSED-BODY-v1' and body['mode']==c['mode'] and body['index']==index and body['cell']==cell and body['batch']==batch and body['error'] is None
 actors=list(source.BATCHES[batch]);assert type(body['genesis_attempts']) is int and body['genesis_attempts']==body['completed_constructors']==len(actors)
 assert [r['role'] for r in body['records']]==actors
 def evaluate(row,certificate_override=certificate):
  assert row['programme']==programme(row['role'])
  return literal(row['state'],seed=c['resource_seeds'][index],mode='no_variation',max_population=1,expansion_tick=0,program=row['programme'],horizon=2040,ledger=row['ledger'],role=row['role'],admission='CONTEXT90-CROSSED-'+c['mode'].upper()+'-v1',index=index,cell=cell,certificate=certificate_override)
 summaries=[dict(role=row['role'],physics=evaluate(row)) for row in body['records']];forged=[]
 if index==0 and cell=='AA' and batch=='retention':
  for kind in ('target','observation','feedback','field_read','field_write','logic_fee','cost','hash','order','truncation','prefix','tuple_draw','origin'):
   row=json.loads(json.dumps(body['records'][0]));draw=certificate
   if kind=='target':
    items=[e['attempt'] for e in row['state']['events'] if 'attempt' in e]
    if not items:continue
    items[0]['target']^=1
   elif kind=='observation':next(l['observation'] for l in row['ledger'] if l['observation'] is not None)['value']^=1
   elif kind=='feedback':
    items=[e for e in row['state']['events'] if 'read_feedback' in e]
    if not items:continue
    items[0]['read_feedback']^=1
   elif kind in ('field_read','field_write','origin'):
    key='read' if kind=='field_read' else 'write';items=[e['packed'][key] for e in row['state']['events'] if 'packed' in e and e['packed'][key] is not None]
    if not items:continue
    items[0]['value']^=1
   elif kind=='logic_fee':
    items=[e for e in row['state']['events'] if 'packed' in e]
    if not items:continue
    items[0]['logic_fee']+=1
   elif kind=='cost':row['ledger'][0]['cost_after']+=1
   elif kind in ('hash','prefix'):row['state']['events'][0]['before']='0'*64
   elif kind=='order':
    if len(row['state']['events'])<2:continue
    row['state']['events'][0],row['state']['events'][1]=row['state']['events'][1],row['state']['events'][0]
   elif kind=='truncation':row['state']['events'].pop();row['ledger'].pop()
   elif kind=='tuple_draw':
    draw={} if certificate is None else json.loads(json.dumps(certificate))
    if draw:draw['draws'][0]['rank']=(draw['draws'][0]['rank']+1)%registry.FAMILY
   try:evaluate(row,draw)
   except (AssertionError,ValueError,KeyError,IndexError):forged.append(kind)
   else:raise AssertionError('Crossed forgery accepted: '+kind)
 return dict(verified=True,schema='CONTEXT90-CROSSED-PROOF-v1',mode=c['mode'],index=index,cell=cell,batch=batch,evidence_inputs=inputs,producer_imported=False,summaries=summaries,forgeries_rejected=forged,stage_credit=False)

def main():
 request=json.loads(boundary.bounded_bytes(Path(sys.argv[1]),65536),object_pairs_hook=boundary.pairs);kind=registry.scope(request);c=request['configuration'];root=Path.cwd();pins=request['source_files']
 assert Path(__file__).resolve()==root/'experiments/digital_context90_crossed_child_v1.py' and 'experiments/digital_context90_crossed_child_v1.py' in pins
 ss=hashlib.sha256(enc(pins)).hexdigest();cs=hashlib.sha256(enc(c)).hexdigest()
 assert ss==request['source_sha'] and cs==request['config_sha'] and boundary.verify_source(root,pins)==ss
 assert request['grant']['limit']==registry.capacity(request['role'])
 boundary.validate_grant(dict(grant=request['grant'],grant_seal=request['seal'],configuration_sha256=cs,role=request['role']),ss,'recording' if kind=='generate' else 'proof')
 error=None
 if kind=='sample':
  # This is the ONLY entropy call site, after exact request/source/config/role/grant guard.
  import os
  value=dict(schema='CONTEXT90-CROSSED-DRAWS-v1',mode='primary',draws=[]);ceiling=(2**256//registry.FAMILY)*registry.FAMILY
  try:
   for index in range(9):
    record=dict(tuple_id=c['tuple_ids'][index],words=[],rank=None);value['draws'].append(record)
    for attempt in range(8):
     word=os.urandom(32);record['words'].append(word.hex());x=int.from_bytes(word,'big')
     if x<ceiling:record['rank']=x%registry.FAMILY;break
    if record['rank'] is None:raise ValueError('Finite entropy rejection exhausted')
   registry.verify_certificate(value)
   for index in range(9):checked_definition('primary',index,'AA',value)
  except BaseException as exc:
   error=repr(exc);value['schema']='CONTEXT90-CROSSED-DRAWS-FAILED-v1';value['error']=error

 else:
  fields=request['role'].split(':');index=int(fields[1]);cell=fields[2];batch=fields[3];certificate=read(request['input']['draw'],65536) if c['mode']=='primary' else None
  checked_definition(c['mode'],index,cell,certificate)
  if kind=='generate':value=generate(index,cell,batch,c,certificate);error=value['error']
  else:value=audit(index,cell,batch,c,request['input'],certificate)
 boundary.module_origins(root,pins);assert boundary.verify_source(root,pins)==ss
 receipt=transport.record(request['grant'],request['seal'],ss,cs,request['role'],value)
 print(enc(dict(role=request['role'],source_sha=ss,config_sha=cs,receipt=receipt)).decode());assert error is None,error

if __name__=='__main__':
 try:main()
 except BaseException:
  print(enc(dict(rejected_before_world='experiments.digital_context90_crossed_engine_v1' not in sys.modules)).decode());raise
