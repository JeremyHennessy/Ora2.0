"""One frozen read-only diagnosis, complete finite custody and archive."""
import ast,json,shutil,sys,zipfile
from pathlib import Path
import oralab
L=Path('D:/OraLab');D=L/'src/Ora2.0-recording82';M=1024**2;sys.path.insert(0,str(D))
from experiments.evidence_budget import Budget
from experiments.process_limits import Limits,run
from experiments.digital_revision84_custody import open_reserved
from cognitive76_controller_core_v2 import enc,fill_reserved,native_ok
TAG='credited-fallback87v2-closed-credit-cost-v1'
ROOT=L/'runs'/(TAG+'-20261015');REG=L/'reports'/(TAG+'-registration.json');REPORT=L/'reports'/(TAG+'.json')
SOURCE=L/'tools/credited_fallback87v2_closed_credit_cost_v1.py'
CONTRACT=L/'reports/credited-fallback87v2-closed-credit-cost-contract-v1-20261015.md'
PRIMARY=L/'reports/credited-fallback87v2-primary-v1.json'
OLD=L/'runs/credited-fallback87v2-primary-v1-20261015'
def read(p):return json.loads(p.read_bytes())
def spec(p):return dict(path=str(p),extent=p.stat().st_size,sha256=oralab.sha(p))
def files():
 r=read(PRIMARY);assert r['verified'] and r['archive_exact'] and r['native_calls']==309
 assert r['completed_logical_originals']==816 and r['completed_scientific_geneses']==1632
 paths={'worker.py':SOURCE,'owners/controller.py':Path(__file__),'owners/contract.md':CONTRACT,'owners/primary-report.json':PRIMARY,
  'owners/publication.json':L/'reports/credited-fallback87v2-closed-publication-v1.json'}
 roles=r['completed_roles']
 for seed in list(range(1009700,1009708))+list(range(1009900,1009908)):
  for group in ('intact','model_erased','model_misbound','fallback_misbound','history_disabled','references'):
   role=f'original:{seed}:{group}:generate';s=roles[role];p=Path(s['path']);assert spec(p)==s
   paths[f'inputs/{seed}-{group}.json']=p
  role=f'original:{seed}:metrics';s=roles[role];p=Path(s['path']);assert spec(p)==s
  paths[f'inputs/{seed}-metrics.json']=p
 paths['inputs/final.json']=Path(roles['original:all:accept']['path'])
 assert oralab.sha(OLD/'archive/complete.zip')==r['archive_sha256']
 return paths
def pins(paths):return {str(p):oralab.sha(p) for p in paths.values()}
def plan(paths):
 raw={name:p.stat().st_size for name,p in paths.items()}
 raw.update({'native.json':M,'request.json':M,'output.json':8*M,'owners/registration.json':64*1024})
 assert sum(raw.values())<=384*M
 failure={'outcome.json':M,'budget.json':M}
 limits=dict(raw=sum(raw.values()),failure=sum(failure.values()),archive=sum(raw.values())+sum(failure.values())+M,restore=sum(raw.values())+sum(failure.values()))
 assert all(limits[k]<=v*M for k,v in dict(raw=384,archive=400,restore=400,failure=16).items())
 return raw,failure,limits
def worker(owner):
 reg=read(REG);paths=files();assert pins(paths)==reg['pins'] and oralab.sha(L/'state/operator.lock')==owner
 raw,failure,limits=plan(paths);b=Budget(ROOT,limits,1200*M)
 error=None;archive_error=None;value=None;archive=None;calls=0
 try:
  for phase,entries in (('raw',raw),('failure',failure)):
   for name,size in entries.items():
    with b.create(phase,name,reserve=size):pass
  with b.create('archive','complete.zip',reserve=limits['archive']):pass
  for phase,entries in (('raw',raw),('failure',failure)):
   for name,size in entries.items():
    with b.create('restore',phase+'/'+name,reserve=size):pass
  for name,p in paths.items():
   with open_reserved(b,'raw',name) as dst:
    with p.open('rb') as src:
     while block:=src.read(M):dst.write(block)
   assert oralab.sha(ROOT/'raw'/name)==reg['pins'][str(p)]
  fill_reserved(ROOT,'owners/registration.json',enc(reg),64*1024)
  batches=[]
  for seed in list(range(1009700,1009708))+list(range(1009900,1009908)):
   batches.append(dict(seed=seed,metrics=spec(ROOT/'raw/inputs'/f'{seed}-metrics.json'),groups=[
    dict(group=g,body=spec(ROOT/'raw/inputs'/f'{seed}-{g}.json')) for g in ('intact','model_erased','model_misbound','fallback_misbound','history_disabled','references')]))
  request=dict(source_sha256=oralab.sha(ROOT/'raw/worker.py'),final=spec(ROOT/'raw/inputs/final.json'),batches=batches,output=str(ROOT/'raw/output.json'))
  fill_reserved(ROOT,'request.json',enc(request),M)
  n=run([sys.executable,'-B',str(ROOT/'raw/worker.py'),str(ROOT/'raw/request.json')],Limits(memory_bytes=512*M,cpu_seconds=60,wall_seconds=90,processes=3),cwd=D)
  calls+=1;fill_reserved(ROOT,'native.json',enc(n),M);assert native_ok(n),n['output']
  out=json.loads(n['output']);value=read(ROOT/'raw/output.json');assert value['verified'] and value['original_histories']==816
  assert out['extent']==(ROOT/'raw/output.json').stat().st_size<=8*M and out['sha256']==oralab.sha(ROOT/'raw/output.json')
  assert pins(paths)==reg['pins']
 except BaseException as e:error=e
 finally:
  try:
   with open_reserved(b,'failure','outcome.json') as f:f.write(enc(dict(error=None if error is None else repr(error),native_calls=calls,new_worlds=0,targets=0)))
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
   assert all(oralab.sha(ROOT/name)==oralab.sha(ROOT/'restore'/name) for name in names)
   archive=oralab.sha(ROOT/'archive/complete.zip')
  except BaseException as e:archive_error=e
  oralab.write_json(REPORT,dict(verified=error is None and archive_error is None,native_calls=calls,new_worlds=0,targets=0,
   summary=value,error=None if error is None else repr(error),archive_error=None if archive_error is None else repr(archive_error),archive_exact=archive is not None,
   archive_sha256=archive,pins=reg['pins'],stage_credit=False))
 if error:raise error
 if archive_error:raise archive_error
 print('All816 closed originals: paid paths, model/semantic origins and nine-bank cost decompositions verified;0newWorlds-targets')
if __name__=='__main__':
 action=sys.argv[1]
 if action=='register':
  assert len(sys.argv)==2
  with oralab.lock():
   assert not REG.exists() and not ROOT.exists() and shutil.disk_usage(L).free>=1208*M
   assert oralab.sha(CONTRACT)=='5d388783d05ac574609c5f773c61c0799b39fd17f6ef45e25f7e3997c44add5e'
   tree=ast.parse(SOURCE.read_bytes());allowed={'collections','hashlib','json','math','os','stat','sys','pathlib'}
   for node in ast.walk(tree):
    if isinstance(node,ast.Import):assert all(x.name in allowed for x in node.names)
    if isinstance(node,ast.ImportFrom):assert node.module in allowed
   paths=files();plan(paths);oralab.write_json(REG,dict(pins=pins(paths),scope='All816 closed originals only;no physics rerun or targets',child=dict(memory_mib=512,cpu=60,wall=90,processes=3),parent=dict(memory_mib=768,cpu=300,wall=600,processes=4)))
 elif action=='execute':
  assert len(sys.argv)==2
  with oralab.lock():
   paths=files();assert pins(paths)==read(REG)['pins']
   b=Budget(L/'runs'/(TAG+'-controller-20261015'),dict(raw=6*M,failure=2*M),8*M)
   n=run([sys.executable,'-B',str(Path(__file__)),'worker',oralab.sha(L/'state/operator.lock')],Limits(memory_bytes=768*M,cpu_seconds=300,wall_seconds=600,processes=4),cwd=D)
   with b.create('raw','native.json') as f:f.write(enc(n))
   b.write_snapshot('failure');assert native_ok(n),n['output'];print(n['output'])
 else:
  assert action=='worker' and len(sys.argv)==3;worker(sys.argv[2])
