"""Registered finite software qualification then separately registered primary."""
import ast,json,shutil,sys,zipfile
from pathlib import Path
L=Path('D:/OraLab');D=L/'src/Ora2.0-recording82';M=1024**2
sys.path.insert(0,str(L/'tools'));sys.path.insert(0,str(D))
import oralab
from experiments.digital_credited_fallback87v2_primary_boundary import REQUIRED
from experiments import digital_strategy88_plan as plan
from experiments.digital_revision84_custody import open_reserved
from experiments.evidence_budget import Budget
from experiments.evidence_write_grant68 import plain,digest
from experiments.process_limits import Limits,run
from cognitive76_controller_core_v2 import enc,sha,fill_reserved,native_ok
PUBLIC=D/'lab/run_strategy88_v1.py';CONTRACT=L/'reports/strategy88-prospective-contract-v1-20261015.md'
FILES={name:D/name for name in REQUIRED|{
 'experiments/digital_memory80.py','experiments/digital_memory80_referee.py','experiments/digital_memory80_recording.py',
 'experiments/digital_recording82_reader.py','experiments/digital_revision84_source.py','experiments/digital_latehistory78_source.py',
 'experiments/digital_credited_fallback87v2_referee.py','experiments/digital_credited_fallback87v2_primary_boundary.py',
 'experiments/digital_credited_fallback87v2_metric_binding.py','experiments/digital_revision84_custody.py',
 'experiments/digital_strategy88_source.py','experiments/digital_strategy88_world.py','experiments/digital_strategy88_referee.py',
 'experiments/digital_strategy88_metrics.py','experiments/digital_strategy88_acceptance.py','experiments/digital_strategy88_plan.py','experiments/digital_strategy88_child.py',
 'tests/test_digital_strategy88.py','lab/strategy88_pure_worker_v1.py','lab/run_strategy88_v1.py',
 'docs/DIGITAL-STRATEGY88-PROSPECTIVE-CONTRACT-V1.md','data/credited-fallback86-controls/active-size-fixture-v1.json'}}
def read(p):return json.loads(p.read_bytes())
def spec(p):return dict(path=str(p),extent=p.stat().st_size,sha256=oralab.sha(p))
def root(mode):return L/'runs'/('strategy88-'+mode+'-v1-20261015')
def registration(mode):return L/'reports'/('strategy88-'+mode+'-v1-registration.json')
def report(mode):return L/'reports'/('strategy88-'+mode+'-v1.json')
def ci_path():return L/'reports'/('strategy88-source-ci-'+oralab.git(D,'rev-parse','HEAD')[:12]+'.json')
def owners(mode):
 values=[Path(__file__),L/'tools/oralab.py',L/'tools/cognitive76_controller_core_v2.py',CONTRACT,ci_path(),
  L/'reports/intelligence-priority-action-20261015/ACTION-HANDOFF.json',L/'reports/credited-fallback87v2-primary-v1.json']
 if mode=='primary':values.append(report('software'))
 return values
def pins(mode):return {str(p):oralab.sha(p) for p in list(FILES.values())+owners(mode)}
def verify_reuse():
 old=read(L/'reports/credited-fallback87v2-primary-v1.json');assert old['verified'] and old['archive_exact']
 for path,value in old['pins'].items():assert oralab.sha(Path(path))==value
def gate(mode):
 assert PUBLIC.read_bytes()==Path(__file__).read_bytes()
 ci=read(ci_path());assert ci['passed'] is True and ci['conclusion']=='success' and ci['source_head']==oralab.git(D,'rev-parse','HEAD')
 assert oralab.git(D,'status','--porcelain')==''
 assert oralab.sha(CONTRACT)==plan.CONTRACT;verify_reuse()
 if mode=='primary':
  old=read(report('software'));assert old['verified'] and old['software_admission'] is True and old['native_calls']==14
  assert old['source_head']==ci['source_head'] and old['archive_exact']
  for path,value in old['pins'].items():assert oralab.sha(Path(path))==value
def layout(mode,reg):
 sizes={p.name:p.stat().st_size for p in owners(mode)};assert len(sizes)==len(owners(mode))
 return plan.layout(mode,{k:p.stat().st_size for k,p in FILES.items()},sizes,len(enc(reg)))
def worker(mode,owner):
 ROOT=root(mode);REG=registration(mode);reg=read(REG);c=plan.config(mode);assert pins(mode)==reg['pins'] and oralab.sha(L/'state/operator.lock')==owner
 raw,failure,limits=layout(mode,reg);b=Budget(ROOT,limits,(1920 if mode=='software' else 7552)*M)
 error=None;archive_error=None;calls=0;negative=0;completed={};launched=[];summary={};pure_checks=[]
 try:
  for name,n in failure.items():
   with b.create('failure',name,reserve=n):pass
  with b.create('archive','complete.zip',reserve=limits['archive']):pass
  for prefix,entries in (('raw',raw),('failure',failure)):
   for name,n in entries.items():
    with b.create('restore',prefix+'/'+name,reserve=n):pass
  for name,n in raw.items():
   with b.create('raw',name,reserve=n):pass
  fill_reserved(ROOT,'registration.json',REG.read_bytes(),raw['registration.json'])
  for name,p in FILES.items():fill_reserved(ROOT,'original/'+name,p.read_bytes(),raw['original/'+name])
  for p in owners(mode):fill_reserved(ROOT,'owners/'+p.name,p.read_bytes(),raw['owners/'+p.name])
  with open_reserved(b,'raw','source.zip') as f:
   with zipfile.ZipFile(f,'w',zipfile.ZIP_STORED) as z:
    for name in FILES:z.write(ROOT/'raw/original'/name,name)
  with zipfile.ZipFile(ROOT/'raw/source.zip') as z:
   for name in FILES:fill_reserved(ROOT,'restored/'+name,z.read(name),raw['restored/'+name])
  source_files={k:oralab.sha(p) for k,p in FILES.items()};ss=sha(enc(source_files));cs=sha(enc(c));slots={}
  assert all(oralab.sha(ROOT/'raw'/export/name)==v for export in ('original','restored') for name,v in source_files.items())
  for role in plan.roles(mode):
   name='data/'+role.replace(':','-')+'.json';info=plain(ROOT/'raw'/name)
   grant=dict(version='sharedlineage68-file-grant-candidate-v1',root=str(ROOT),phase='raw',name=name,limit=plan.capacity(role),source_sha=ss,config_sha=cs,role=role,device=info.st_dev,inode=info.st_ino)
   slots[role]=(grant,digest(grant))
  def launch(request,stem,export,refusal=False,pure=False):
   nonlocal calls
   fill_reserved(ROOT,'request/'+stem+'.json',enc(request),65536)
   command=[sys.executable,'-B',str(ROOT/'raw'/export/'lab/strategy88_pure_worker_v1.py'),str(ROOT/'raw/request'/(stem+'.json'))] if pure else [sys.executable,'-B','-m','experiments.digital_strategy88_child',str(ROOT/'raw/request'/(stem+'.json'))]
   n=run(command,Limits(memory_bytes=512*M,cpu_seconds=60,wall_seconds=90,processes=3),cwd=ROOT/'raw'/export)
   calls+=1;fill_reserved(ROOT,'native/'+stem+'.json',enc(n),M)
   if refusal:
    assert n['exit_code']!=0 and not n['timed_out'] and not n['output_truncated'] and n['post_close_processes_exited'] and n['usage']['active_before_close']==0
    assert '"rejected_before_world":true' in n['output']
   else:assert native_ok(n),n['output']
   return n
  if mode=='software':
   for export in ('original','restored'):
    n=launch(dict(source_files=source_files,source_sha=ss),'pure-'+export,export,pure=True)
    values=[json.loads(line) for line in n['output'].splitlines() if line.startswith('{') and '"checks"' in line]
    assert len(values)==1 and values[0]['verified'] is True and values[0]['checks']==6 and values[0]['worlds']==values[0]['targets']==0
    pure_checks.append(values[0])
  first=plan.roles(mode)[0];grant,seal=slots[first]
  base=dict(configuration=c,source_files=source_files,source_sha=ss,config_sha=cs,role=first,kind='generate',input=None,grant=grant,seal=seal)
  def refuse(key):
   nonlocal negative
   request=json.loads(json.dumps(base))
   if key=='role':request[key]='original:1010200:generate'
   elif key=='configuration':request[key]['cost_budget']=1024
   else:request[key]='0'*64
   launch(request,'refused'+str(negative),'original',True);negative+=1
   assert (ROOT/'raw'/grant['name']).stat().st_size==0
  def invoke(role,inputs):
   grant,seal=slots[role];stem=role.replace(':','-');export=role.split(':')[0]
   request=dict(configuration=c,source_files=source_files,source_sha=ss,config_sha=cs,role=role,kind=role.split(':')[-1],input=inputs,grant=grant,seal=seal)
   launched.append(role);n=launch(request,stem,export);out=json.loads(n['output'])
   assert out['role']==role and out['source_sha']==ss and out['config_sha']==cs
   path=ROOT/'raw'/grant['name'];receipt=out['receipt'];assert receipt['extent']==path.stat().st_size and receipt['sha256']==oralab.sha(path) and receipt['grant_sha256']==seal
   value=read(path);assert path.read_bytes()==enc(value)
   completed[role]=spec(path);chain=dict(role=role,body=completed[role],request=spec(ROOT/'raw/request'/(stem+'.json')),native=spec(ROOT/'raw/native'/(stem+'.json')))
   return dict(spec=completed[role],value=value,chain=chain)
  summary=plan.orchestrate(mode,refuse,invoke,lambda *args:verify_pins())
  assert negative==4 and calls==(14 if mode=='software' else 53) and len(completed)==len(plan.roles(mode))
  assert mode!='software' or len(pure_checks)==2
 except BaseException as exc:error=exc
 finally:
  exact=False
  try:
   with open_reserved(b,'failure','outcome.json') as f:f.write(enc(dict(error=None if error is None else repr(error),native_calls=calls,negative_requests_rejected=negative,launched=launched,completed=completed)))
   with open_reserved(b,'failure','budget.json') as f:f.write(enc(b.snapshot()))
   names=[phase+'/'+name for phase,entries in (('raw',raw),('failure',failure)) for name in entries]
   with open_reserved(b,'archive','complete.zip') as f:
    with zipfile.ZipFile(f,'w',zipfile.ZIP_STORED) as z:
     for name in names:z.write(ROOT/name,name)
   with zipfile.ZipFile(ROOT/'archive/complete.zip') as z:
    for name in names:
     with open_reserved(b,'restore',name) as dst:
      with z.open(name) as src:
       while block:=src.read(M):dst.write(block)
   exact=all(oralab.sha(ROOT/name)==oralab.sha(ROOT/'restore'/name) for name in names);assert exact
  except BaseException as exc:archive_error=exc
  oralab.write_json(report(mode),dict(verified=error is None and archive_error is None,mode=mode,source_head=reg['source_head'],native_calls=calls,
   completed_geneses=26*sum(r.endswith(':generate') for r in completed),logical_originals=26*sum(r.startswith('original:') and r.endswith(':generate') for r in completed),
   incomplete_genesis_attempts_not_inferred=bool(error and any(r.endswith(':generate') and r not in completed for r in launched)),
   new_scientific_geneses=0 if mode=='software' else 26*sum(r.endswith(':generate') for r in completed),negative_requests_rejected=negative,pure_checks=pure_checks,
   software_admission=summary.get('software_admission') if mode=='software' else None,summary=summary,completed_roles=completed,pins=reg['pins'],
   error=None if error is None else repr(error),archive_error=None if archive_error is None else repr(archive_error),archive_exact=exact,
   archive_sha256=oralab.sha(ROOT/'archive/complete.zip') if exact else None,stage_credit=False))
 if error:raise error
 if archive_error:raise archive_error
 print('STRATEGY88 '+mode+' closed with full literal/parity/native/source/grants/exact archive; inspect functional/strong/N/E separately')
def verify_pins():
 # The worker-mode globals are pinned once more by the registered source snapshot.
 mode=sys.argv[2];assert pins(mode)==read(registration(mode))['pins']
if __name__=='__main__':
 action=sys.argv[1];mode=sys.argv[2];assert mode in plan.SEEDS
 if action=='register':
  assert len(sys.argv)==3
  with oralab.lock():
   gate(mode);assert not registration(mode).exists() and not root(mode).exists();assert shutil.disk_usage(L).free>=(1928 if mode=='software' else 7560)*M
   for p in list(FILES.values())+owners(mode):
    if p.suffix=='.py':ast.parse(p.read_bytes())
   reg=dict(pins=pins(mode),configuration=plan.config(mode),source_head=oralab.git(D,'rev-parse','HEAD'),mode=mode)
   layout(mode,reg);oralab.write_json(registration(mode),reg)
 elif action=='execute':
  assert len(sys.argv)==3
  with oralab.lock():
   gate(mode);assert pins(mode)==read(registration(mode))['pins']
   b=Budget(L/'runs'/('strategy88-'+mode+'-v1-controller-20261015'),dict(raw=6*M,failure=2*M),8*M)
   n=run([sys.executable,'-B',str(Path(__file__)),'worker',mode,oralab.sha(L/'state/operator.lock')],Limits(memory_bytes=768*M,cpu_seconds=600 if mode=='software' else 1200,wall_seconds=900 if mode=='software' else 1800,processes=4),cwd=D)
   with b.create('raw','native.json') as f:f.write(enc(n))
   b.write_snapshot('failure');assert native_ok(n),n['output'];print(n['output'])
 else:
  assert action=='worker' and len(sys.argv)==4;worker(mode,sys.argv[3])
