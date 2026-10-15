"""Frozen309-role primary custody. Exact whole-source CI and separate registration required."""
import ast,json,shutil,sys,zipfile
from pathlib import Path
LAB=Path('D:/OraLab');DEV=LAB/'src/Ora2.0-recording82';M=1024**2
sys.path.insert(0,str(LAB/'tools'));sys.path.insert(0,str(DEV))
import oralab
from experiments.digital_credited_fallback87v2_primary_boundary import REQUIRED
from experiments.digital_credited_fallback87v2_primary_child import CONFIG
from experiments.digital_credited_fallback87v2_primary_plan import ROLES,capacity,layout,admit_ci,orchestrate,recording_bound
from experiments.digital_revision84_custody import open_reserved
from experiments.evidence_budget import Budget
from experiments.evidence_write_grant68 import plain,digest
from experiments.process_limits import Limits,run
from cognitive76_controller_core_v2 import enc,sha,fill_reserved,native_ok

ROOT=LAB/'runs/credited-fallback87v2-primary-v1-20261015'
REG=LAB/'reports/credited-fallback87v2-primary-v1-registration.json'
REPORT=LAB/'reports/credited-fallback87v2-primary-v1.json'
PUBLIC=DEV/'lab/run_credited_fallback87v2_primary_v1.py'
FILES={n:DEV/n for n in REQUIRED|{
 'experiments/digital_memory80.py','experiments/digital_memory80_referee.py','experiments/digital_memory80_recording.py',
 'experiments/digital_credited_fallback86_source.py','experiments/digital_credited_fallback86_controls.py',
 'experiments/digital_credited_fallback86_control_referee.py','experiments/digital_recording82_reader.py',
 'experiments/digital_credited_fallback87v2_source.py','experiments/digital_credited_fallback87v2_world.py',
 'experiments/digital_credited_fallback87v2_referee.py','experiments/digital_revision84_source.py',
 'experiments/digital_latehistory78_source.py','experiments/digital_credited_fallback87v2_metrics.py',
 'experiments/digital_credited_fallback87v2_metric_binding.py','experiments/digital_credited_fallback87v2_acceptance.py',
 'experiments/digital_credited_fallback87v2_primary_child.py','experiments/digital_credited_fallback87v2_primary_plan.py',
 'experiments/digital_credited_fallback87v2_primary_boundary.py','experiments/digital_revision84_custody.py',
 'tests/test_digital_credited_fallback87v2_primary.py','lab/run_credited_fallback87v2_primary_v1.py',
 'docs/DIGITAL-CREDITED-FALLBACK87-PROSPECTIVE-CONTRACT-V2.md',
 'docs/DIGITAL-CREDITED-FALLBACK87-V2-PRIMARY-CUSTODY.md',
 'docs/DIGITAL-CREDITED-FALLBACK87-V2-PRIMARY-QUALIFICATION.md','docs/DIGITAL-CREDITED-FALLBACK87-V2-PRIMARY-QUALIFICATION-V2.md',
 'data/credited-fallback86-controls/active-size-fixture-v1.json'}}

def read(p):return json.loads(p.read_bytes())
def spec(p):return dict(path=str(p),extent=p.stat().st_size,sha256=oralab.sha(p))
def ci_path():return LAB/'reports'/('credited-fallback87v2-primary-source-ci-'+oralab.git(DEV,'rev-parse','HEAD')[:12]+'.json')
PROVENANCE=LAB/'tools/credited_fallback87v2_primary_reuse_v1.py'
def owners():return [Path(__file__),LAB/'tools/oralab.py',LAB/'tools/cognitive76_controller_core_v2.py',
 PROVENANCE,LAB/'reports/credited-fallback87-prospective-contract-v2-20261015.md',
 LAB/'reports/credited-fallback87v2-primary-controller-contract-v1-20261015.md',
 LAB/'reports/credited-fallback87v2-primary-custody-qualification-v1-20261015.md',
 LAB/'reports/credited-fallback87v2-primary-prepared-v2.json',
 LAB/'reports/credited-fallback87v2-origin-prepared-v2.json',
 LAB/'reports/credited-fallback87v2-origin-namespace-prepared-v1.json',
 LAB/'reports/credited-fallback87v2-origin-publication-v1.json',ci_path()]

def pins():return {str(p):oralab.sha(p) for p in list(FILES.values())+owners()}
def check(reg):assert pins()==reg['pins']
def gate():
 assert PUBLIC.read_bytes()==Path(__file__).read_bytes()
 admit_ci(read(ci_path()),oralab.git(DEV,'rev-parse','HEAD'),oralab.git(DEV,'status','--porcelain'))
 prepared=read(LAB/'reports/credited-fallback87v2-primary-prepared-v2.json');assert prepared['passed'] is True
 for path,value in prepared['pins'].items():assert oralab.sha(Path(path))==value
 from credited_fallback87v2_primary_reuse_v1 import verify
 verify()
 assert oralab.sha(LAB/'reports/credited-fallback87v2-primary-controller-contract-v1-20261015.md')==CONFIG['contract_sha256']
 assert oralab.sha(LAB/'reports/credited-fallback87-prospective-contract-v2-20261015.md')==CONFIG['scientific_contract_sha256']
 assert recording_bound()==39387136

def plan(reg):
 osizes={p.name:p.stat().st_size for p in owners()};assert len(osizes)==len(owners())
 if REG.exists():assert REG.stat().st_size<=64*1024
 return layout({n:p.stat().st_size for n,p in FILES.items()},osizes,len(enc(reg)))

def worker(owner):
 reg=read(REG);check(reg);assert oralab.sha(LAB/'state/operator.lock')==owner
 raw,failure,limits=plan(reg);b=Budget(ROOT,limits,46080*M)
 error=None;archive_error=None;calls=0;negatives=0;launched=[];completed={};summary={}
 try:
  # Failure/archive/restore capacity exists before any raw file or valid role.
  for name,size in failure.items():
   with b.create('failure',name,reserve=size):pass
  with b.create('archive','complete.zip',reserve=limits['archive']):pass
  for prefix,entries in (('raw',raw),('failure',failure)):
   for name,size in entries.items():
    with b.create('restore',prefix+'/'+name,reserve=size):pass
  for name,size in raw.items():
   with b.create('raw',name,reserve=size):pass
  fill_reserved(ROOT,'registration.json',REG.read_bytes(),raw['registration.json'])
  for name,p in FILES.items():fill_reserved(ROOT,'original/'+name,p.read_bytes(),raw['original/'+name])
  for p in owners():fill_reserved(ROOT,'owners/'+p.name,p.read_bytes(),raw['owners/'+p.name])
  with open_reserved(b,'raw','source.zip') as stream:
   with zipfile.ZipFile(stream,'w',zipfile.ZIP_STORED) as z:
    for name in FILES:z.write(ROOT/'raw/original'/name,name)
  with zipfile.ZipFile(ROOT/'raw/source.zip') as z:
   for name in FILES:fill_reserved(ROOT,'restored/'+name,z.read(name),raw['restored/'+name])
  source_files={name:oralab.sha(p) for name,p in FILES.items()}
  assert all(oralab.sha(ROOT/'raw'/export/name)==value for export in ('original','restored') for name,value in source_files.items())
  ss=sha(enc(source_files));cs=sha(enc(CONFIG));slots={}
  for role in ROLES:
   name='data/'+role.replace(':','-')+'.json';info=plain(ROOT/'raw'/name)
   grant=dict(version='sharedlineage68-file-grant-candidate-v1',root=str(ROOT),phase='raw',name=name,
    limit=capacity(role),source_sha=ss,config_sha=cs,role=role,device=info.st_dev,inode=info.st_ino)
   slots[role]=(grant,digest(grant))
  def native_role(request,stem,refusal=False):
   nonlocal calls
   fill_reserved(ROOT,'request/'+stem+'.json',enc(request),64*1024)
   export='restored' if request['role'].startswith('restored:') else 'original'
   n=run([sys.executable,'-B','-m','experiments.digital_credited_fallback87v2_primary_child',str(ROOT/'raw/request'/(stem+'.json'))],
    Limits(memory_bytes=512*M,cpu_seconds=60,wall_seconds=90,processes=3),cwd=ROOT/'raw'/export)
   calls+=1;fill_reserved(ROOT,'native/'+stem+'.json',enc(n),M)
   if refusal:
    assert n['exit_code']!=0 and not n['timed_out'] and not n['output_truncated']
    assert n['post_close_processes_exited'] and n['usage']['active_before_close']==0
    assert '"rejected_before_world":true' in n['output']
   else:assert native_ok(n),n['output']
   return n
  grant,signature=slots[ROLES[0]]
  base=dict(configuration=CONFIG,source_files=source_files,source_sha=ss,config_sha=cs,
   role=ROLES[0],kind='generate',input=None,grant=grant,seal=signature)
  def refuse(field):
   nonlocal negatives
   request=json.loads(json.dumps(base))
   if field=='role':request[field]='original:2100382:intact:generate'  # CLOSED cached intact role
   elif field=='configuration':request[field]['horizon']=256
   else:request[field]='0'*64
   native_role(request,'refused'+str(negatives),True);negatives+=1
   assert (ROOT/'raw'/grant['name']).stat().st_size==0
  def invoke(role,inputs):
   grant,signature=slots[role];kind=role.split(':')[-1];stem=role.replace(':','-')
   request=dict(configuration=CONFIG,source_files=source_files,source_sha=ss,config_sha=cs,
    role=role,kind=kind,input=inputs,grant=grant,seal=signature)
   launched.append(role);native=native_role(request,stem)
   output=json.loads(native['output']);assert output['role']==role and output['source_sha']==ss and output['config_sha']==cs
   path=ROOT/'raw'/grant['name'];receipt=output['receipt']
   assert receipt['extent']==path.stat().st_size and receipt['sha256']==oralab.sha(path) and receipt['grant_sha256']==signature
   value=read(path);assert path.read_bytes()==enc(value)
   completed[role]=spec(path)
   chain=dict(role=role,body=completed[role],request=spec(ROOT/'raw/request'/(stem+'.json')),native=spec(ROOT/'raw/native'/(stem+'.json')))
   return dict(spec=completed[role],value=value,chain=chain)
  def verify(role,result):check(reg)
  summary=orchestrate(refuse,invoke,verify)
  assert calls==309 and negatives==4 and len(completed)==305 and len(summary['endpoints'])==144
 except BaseException as exc:error=exc
 finally:
  exact=False
  try:
   with open_reserved(b,'failure','outcome.json') as stream:
    stream.write(enc(dict(error=None if error is None else repr(error),native_calls=calls,
     launched=launched,completed=completed,negative_requests_rejected=negatives)))
   with open_reserved(b,'failure','budget.json') as stream:stream.write(enc(b.snapshot()))
   names=[prefix+'/'+name for prefix,entries in (('raw',raw),('failure',failure)) for name in entries if (ROOT/prefix/name).is_file()]
   with open_reserved(b,'archive','complete.zip') as stream:
    with zipfile.ZipFile(stream,'w',zipfile.ZIP_STORED) as z:
     for name in names:z.write(ROOT/name,name)
   with zipfile.ZipFile(ROOT/'archive/complete.zip') as z:
    for name in names:
     with open_reserved(b,'restore',name) as dest:
      with z.open(name) as src:
       while True:
        chunk=src.read(M)
        if not chunk:break
        dest.write(chunk)
   exact=all(oralab.sha(ROOT/name)==oralab.sha(ROOT/'restore'/name) for name in names);assert exact
  except BaseException as exc:archive_error=exc
  oralab.write_json(REPORT,dict(verified=error is None and archive_error is None,source_head=reg['source_head'],
   completed_scientific_geneses=sum(len(CONFIG['cases'][r.split(':')[2]]) for r in completed if r.endswith('generate')),
   completed_logical_originals=sum(len(CONFIG['cases'][r.split(':')[2]]) for r in completed if r.startswith('original:') and r.endswith('generate')),
   planned_logical_originals=816,planned_replay_inclusive_geneses=1632,scientific_targets_only_from_paid_ACT=True,
   incomplete_genesis_attempts_not_inferred=bool(error and any(r.endswith('generate') and r not in completed for r in launched)),
   native_calls=calls,negative_requests_rejected=negatives,summary=summary,
   error=None if error is None else repr(error),archive_error=None if archive_error is None else repr(archive_error),
   archive_exact=exact,archive_sha256=oralab.sha(ROOT/'archive/complete.zip') if exact else None,
   completed_roles=completed,pins=reg['pins'],stage_credit=False))
 if error:raise error
 if archive_error:raise archive_error
 print('Frozen primary closed:816 originals/816blank replays/full physics/parity/309native/separate arithmetic/archive verified. Read all nine decisions and N/E separately.')

if __name__=='__main__':
 action=sys.argv[1]
 if action=='register':
  assert len(sys.argv)==2
  with oralab.lock():
   gate();assert not REG.exists() and not ROOT.exists();assert shutil.disk_usage(LAB).free>=46088*M
   for p in list(FILES.values())+owners():
    if p.suffix=='.py':ast.parse(p.read_bytes())
   reg=dict(pins=pins(),configuration=CONFIG,source_head=oralab.git(DEV,'rev-parse','HEAD'),
    child=dict(memory_mib=512,cpu=60,wall=90,processes=3),parent=dict(memory_mib=768,cpu=2400,wall=3600,processes=4),
    evidence_mib=46080,controller_mib=8,scope='All816 frozen originals/816blank replays; all16 contexts/all9sources/5arms/6references; no reserve use')
   plan(reg);oralab.write_json(REG,reg)
 elif action=='execute':
  assert len(sys.argv)==2
  with oralab.lock():
   gate();check(read(REG));b=Budget(LAB/'runs/credited-fallback87v2-primary-v1-controller-20261015',dict(raw=6*M,failure=2*M),8*M)
   n=run([sys.executable,'-B',str(Path(__file__)),'worker',oralab.sha(LAB/'state/operator.lock')],
    Limits(memory_bytes=768*M,cpu_seconds=2400,wall_seconds=3600,processes=4),cwd=DEV)
   with b.create('raw','native.json') as stream:stream.write(enc(n))
   b.write_snapshot('failure');assert native_ok(n),n['output'];print(n['output'])
 else:
  assert action=='worker' and len(sys.argv)==3;worker(sys.argv[2])
