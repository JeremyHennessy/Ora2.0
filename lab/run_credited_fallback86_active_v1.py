"""Frozen52-role active-control SOFTWARE reference. No scientific execution interface."""
import ast,json,shutil,sys,zipfile
from pathlib import Path
LAB=Path('D:/OraLab');DEV=LAB/'src/Ora2.0-recording82';M=1024**2
sys.path.insert(0,str(LAB/'tools'));sys.path.insert(0,str(DEV))
import oralab
from experiments.digital_cognitive76_child import REQUIRED
from experiments.digital_credited_fallback86_active_child import CONFIG
from experiments.digital_credited_fallback86_active_plan import ROLES,capacity,layout,registration_capacity,admit_ci,orchestrate,recording_bound,validate_cached
from experiments.digital_recording82_reader import read_spec as read_cached
from experiments.digital_revision84_custody import open_reserved
from experiments.evidence_budget import Budget
from experiments.evidence_write_grant68 import plain,digest
from experiments.process_limits import Limits,run
from cognitive76_controller_core_v2 import enc,sha,fill_reserved,native_ok

ROOT=LAB/'runs/credited-fallback86-active-software-v1-20261015'
REG=LAB/'reports/credited-fallback86-active-software-v1-registration.json'
REPORT=LAB/'reports/credited-fallback86-active-software-v1.json'
PUBLIC=DEV/'lab/run_credited_fallback86_active_v1.py'
FILES={n:DEV/n for n in REQUIRED|{
 'experiments/digital_memory80.py','experiments/digital_memory80_referee.py','experiments/digital_memory80_recording.py',
 'experiments/digital_credited_fallback86_source.py','experiments/digital_credited_fallback86_controls.py',
 'experiments/digital_credited_fallback86_control_referee.py','experiments/digital_recording82_reader.py',
 'experiments/digital_credited_fallback86_active_child.py','experiments/digital_credited_fallback86_active_plan.py',
 'experiments/digital_revision84_custody.py','tests/test_digital_credited_fallback86_active.py',
 'lab/run_credited_fallback86_active_v1.py','docs/DIGITAL-CREDITED-FALLBACK86-ACTIVE-CONTROL-CONTRACT.md',
 'docs/DIGITAL-CREDITED-FALLBACK86-ACTIVE-CUSTODY-QUALIFICATION.md',
 'docs/DIGITAL-CREDITED-FALLBACK86-ACTIVE-CUSTODY-V2.md',
 'docs/DIGITAL-CREDITED-FALLBACK86-ACTIVE-CUSTODY-V3.md',
 'data/credited-fallback86-controls/active-size-fixture-v1.json'}}

def read(p):return json.loads(p.read_bytes())
def spec(p):return dict(path=str(p),extent=p.stat().st_size,sha256=oralab.sha(p))
def ci_path():return LAB/'reports'/('credited-fallback86-active-source-ci-'+oralab.git(DEV,'rev-parse','HEAD')[:12]+'.json')
def owners():return [Path(__file__),LAB/'tools/oralab.py',LAB/'tools/cognitive76_controller_core_v2.py',
 LAB/'reports/credited-fallback86-active-control-contract-v1-20261015.md',
 LAB/'reports/credited-fallback86-active-custody-qualification-v1-20261015.md',
 LAB/'reports/credited-fallback86-active-custody-v2-20261015.md',
 LAB/'reports/credited-fallback86-active-custody-v3-20261015.md',
 LAB/'reports/credited-fallback86-active-controller-prepared-v3.json',
 LAB/'reports/credited-fallback86-control-prepared-v1.json',
 LAB/'reports/credited-fallback86-control-source-publication-verified-v1.json',
 LAB/'reports/credited-fallback86-paid-reference-v1.json',
 LAB/'reports/memory80-terminal-recording-v1.json',LAB/'reports/recording82-reader-v1.json',ci_path()]

def cached():
 closed=read(LAB/'reports/credited-fallback86-paid-reference-v1.json')
 assert closed['verified'] and closed['archive_exact']
 return {str(seed)+'-'+Path(closed['completed_roles'][f'original:{seed}:generate']['path']).name:
         Path(closed['completed_roles'][f'original:{seed}:generate']['path']) for seed in CONFIG['seeds']}

def pins():return {str(p):oralab.sha(p) for p in list(FILES.values())+owners()+list(cached().values())}
def check(reg):
 assert pins()==reg['pins']
 for path in cached().values():
  for parent in path.parents:plain(parent,True)
  plain(path)

def gate():
 assert PUBLIC.read_bytes()==Path(__file__).read_bytes()
 admit_ci(read(ci_path()),oralab.git(DEV,'rev-parse','HEAD'),oralab.git(DEV,'status','--porcelain'))
 prepared=read(LAB/'reports/credited-fallback86-active-controller-prepared-v3.json');assert prepared['passed']
 for path,value in prepared['pins'].items():assert oralab.sha(Path(path))==value
 source=read(LAB/'reports/credited-fallback86-control-prepared-v1.json');assert source['passed']
 assert read(LAB/'reports/credited-fallback86-control-source-publication-verified-v1.json')['publication_verified']
 for path,value in source['pins'].items():assert oralab.sha(Path(path))==value
 closed=read(LAB/'reports/credited-fallback86-paid-reference-v1.json')
 assert closed['verified'] and closed['archive_exact']
 for seed in CONFIG['seeds']:
  original=closed['completed_roles'][f'original:{seed}:generate']
  assert spec(Path(original['path']))==original
 validate_cached([(seed,closed['completed_roles'][f'original:{seed}:generate']) for seed in CONFIG['seeds']],read_cached)
 for name in ('experiments/digital_memory80.py','experiments/digital_memory80_referee.py','experiments/digital_memory80_recording.py'):
  assert oralab.sha(DEV/name)==closed['pins'][str(DEV/name)]
 reader=read(LAB/'reports/recording82-reader-v1.json');assert reader['verified'] and reader['archive_exact']
 hashes=[v for p,v in reader['pins'].items() if p.replace('\\','/').endswith('experiments/digital_recording82_reader.py')]
 assert hashes==[oralab.sha(DEV/'experiments/digital_recording82_reader.py')]
 assert sha((LAB/'reports/credited-fallback86-active-control-contract-v1-20261015.md').read_bytes())==CONFIG['contract_sha256']
 assert recording_bound()<64*M

def plan(reg):
 osizes={p.name:p.stat().st_size for p in owners()};assert len(osizes)==len(owners())
 if REG.exists():assert REG.stat().st_size<=64*1024
 return layout({n:p.stat().st_size for n,p in FILES.items()},osizes,{n:p.stat().st_size for n,p in cached().items()},registration_capacity(len(enc(reg))))

def worker(owner):
 reg=read(REG);check(reg);assert oralab.sha(LAB/'state/operator.lock')==owner
 raw,failure,limits=plan(reg);b=Budget(ROOT,limits,7552*M)
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
  for name,p in cached().items():fill_reserved(ROOT,'cached/'+name,p.read_bytes(),raw['cached/'+name])
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
   n=run([sys.executable,'-B','-m','experiments.digital_credited_fallback86_active_child',str(ROOT/'raw/request'/(stem+'.json'))],
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
   if field=='role':request[field]='original:2100080:generate'  # CLOSED cached intact role
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
   return dict(spec=completed[role],value=value)
  def verify(role,result):check(reg)
  summary=orchestrate(refuse,invoke,verify)
  assert calls==52 and negatives==4 and len(summary)==16
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
   scientific_worlds=0,scientific_targets=0,completed_software_geneses=9*sum(r.endswith('generate') for r in completed),
   incomplete_genesis_attempts_not_inferred=bool(error and any(r.endswith('generate') and r not in completed for r in launched)),
   native_calls=calls,negative_requests_rejected=negatives,summary=summary,
   error=None if error is None else repr(error),archive_error=None if archive_error is None else repr(archive_error),
   archive_exact=exact,archive_sha256=oralab.sha(ROOT/'archive/complete.zip') if exact else None,
   completed_roles=completed,pins=reg['pins'],stage_credit=False))
 if error:raise error
 if archive_error:raise archive_error
 print('Paid software complete:144active original/144restored SOFTWARE geneses/full literal/parity/archive verified;0science.')

if __name__=='__main__':
 action=sys.argv[1]
 if action=='register':
  assert len(sys.argv)==2
  with oralab.lock():
   gate();assert not REG.exists() and not ROOT.exists();assert shutil.disk_usage(LAB).free>=7560*M
   for p in list(FILES.values())+owners()+list(cached().values()):
    if p.suffix=='.py':ast.parse(p.read_bytes())
   reg=dict(pins=pins(),configuration=CONFIG,source_head=oralab.git(DEV,'rev-parse','HEAD'),
    child=dict(memory_mib=512,cpu=60,wall=90,processes=3),parent=dict(memory_mib=768,cpu=1200,wall=2400,processes=4),
    evidence_mib=7552,controller_mib=8,scope='All144 active source/map/control SOFTWARE cells; no primary science')
   plan(reg);oralab.write_json(REG,reg)
 elif action=='execute':
  assert len(sys.argv)==2
  with oralab.lock():
   gate();check(read(REG));b=Budget(LAB/'runs/credited-fallback86-active-software-v1-controller-20261015',dict(raw=6*M,failure=2*M),8*M)
   n=run([sys.executable,'-B',str(Path(__file__)),'worker',oralab.sha(LAB/'state/operator.lock')],
    Limits(memory_bytes=768*M,cpu_seconds=1200,wall_seconds=2400,processes=4),cwd=DEV)
   with b.create('raw','native.json') as stream:stream.write(enc(n))
   b.write_snapshot('failure');assert native_ok(n),n['output'];print(n['output'])
 else:
  assert action=='worker' and len(sys.argv)==3;worker(sys.argv[2])
