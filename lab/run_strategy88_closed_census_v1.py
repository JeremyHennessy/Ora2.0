"""One bounded closed-data read, preserving source/native/exact archive."""
import ast,json,shutil,sys,zipfile
from pathlib import Path
L=Path('D:/OraLab');D=L/'src/Ora2.0-recording82';M=1024**2;sys.path.insert(0,str(L/'tools'));sys.path.insert(0,str(D))
import oralab
from experiments.process_limits import run,Limits
from experiments.evidence_budget import Budget
from experiments.digital_revision84_custody import open_reserved
from cognitive76_controller_core_v2 import enc,fill_reserved,native_ok
ROOT=L/'runs/strategy88-closed-census-v1-20261015';REPORT=L/'reports/strategy88-closed-census-v1.json'
SOURCE=L/'tools/strategy88_closed_census_v1.py';CONTRACT=L/'reports/strategy88-closed-census-contract-v1-20261015.md'
def read(p):return json.loads(p.read_bytes())
def spec(p):return dict(path=str(p),extent=p.stat().st_size,sha256=oralab.sha(p))
def worker(owner):
 assert oralab.sha(L/'state/operator.lock')==owner
 primary=read(L/'reports/strategy88-primary-v1.json');assert primary['verified'] and primary['archive_exact'] and primary['logical_originals']==312
 files={'worker.py':SOURCE,'owners/controller.py':Path(__file__),'owners/contract.md':CONTRACT,'owners/primary.json':L/'reports/strategy88-primary-v1.json'};batches=[]
 for seed in list(range(1010100,1010106))+list(range(1010300,1010306)):
  old=primary['completed_roles'][f'original:{seed}:metrics'];p=Path(old['path']);assert spec(p)==old;files[f'inputs/{seed}.json']=p
  batches.append(dict(seed=seed,spec=dict(path=str(ROOT/'raw/inputs'/f'{seed}.json'),extent=old['extent'],sha256=old['sha256'])))
 old=primary['completed_roles']['original:all:accept'];p=Path(old['path']);assert spec(p)==old;files['inputs/final.json']=p
 assert sum(p.stat().st_size for p in files.values())<8*M
 allowed={'hashlib','json','sys','fractions','math','pathlib'}
 for node in ast.walk(ast.parse(SOURCE.read_bytes())):
  if isinstance(node,ast.Import):assert all(x.name in allowed for x in node.names)
  if isinstance(node,ast.ImportFrom):assert node.module in allowed
 pins={str(p):oralab.sha(p) for p in files.values()}
 raw={k:p.stat().st_size for k,p in files.items()};raw.update({'native.json':M,'request.json':65536,'output.json':2*M})
 assert sum(raw.values())<=16*M
 fail={'outcome.json':2*M,'budget.json':2*M};limits=dict(raw=sum(raw.values()),failure=4*M,archive=20*M,restore=sum(raw.values())+4*M)
 assert limits['restore']<=20*M;b=Budget(ROOT,limits,60*M);error=None;ae=None;out=None;archive=None
 try:
  for phase,entries in (('raw',raw),('failure',fail)):
   for name,n in entries.items():
    with b.create(phase,name,reserve=n):pass
    with b.create('restore',phase+'/'+name,reserve=n):pass
  with b.create('archive','complete.zip',reserve=20*M):pass
  for k,p in files.items():fill_reserved(ROOT,k,p.read_bytes(),raw[k])
  final=dict(path=str(ROOT/'raw/inputs/final.json'),extent=old['extent'],sha256=old['sha256'])
  q=dict(source_sha=oralab.sha(SOURCE),batches=batches,final=final,output=str(ROOT/'raw/output.json'))
  fill_reserved(ROOT,'request.json',enc(q),65536)
  n=run([sys.executable,'-B',str(ROOT/'raw/worker.py'),str(ROOT/'raw/request.json')],Limits(memory_bytes=512*M,cpu_seconds=60,wall_seconds=90,processes=3),cwd=D)
  fill_reserved(ROOT,'native.json',enc(n),M);assert native_ok(n),n['output']
  receipt=json.loads(n['output']);out=read(ROOT/'raw/output.json');assert out['verified'] and receipt['sha256']==oralab.sha(ROOT/'raw/output.json') and receipt['extent']==(ROOT/'raw/output.json').stat().st_size
  assert pins=={str(p):oralab.sha(p) for p in files.values()}
 except BaseException as e:error=e
 finally:
  try:
   with open_reserved(b,'failure','outcome.json') as f:f.write(enc(dict(error=None if error is None else repr(error),new_worlds=0,new_targets=0)))
   with open_reserved(b,'failure','budget.json') as f:f.write(enc(b.snapshot()))
   names=[phase+'/'+name for phase,entries in (('raw',raw),('failure',fail)) for name in entries]
   with open_reserved(b,'archive','complete.zip') as f:
    with zipfile.ZipFile(f,'w',zipfile.ZIP_STORED) as z:
     for name in names:z.write(ROOT/name,name)
   with zipfile.ZipFile(ROOT/'archive/complete.zip') as z:
    for name in names:
     with open_reserved(b,'restore',name) as dst:
      with z.open(name) as src:
       while block:=src.read(M):dst.write(block)
   assert all(oralab.sha(ROOT/name)==oralab.sha(ROOT/'restore'/name) for name in names);archive=oralab.sha(ROOT/'archive/complete.zip')
  except BaseException as e:ae=e
  oralab.write_json(REPORT,dict(verified=error is None and ae is None,summary=out,pins=pins,native_calls=1,new_worlds=0,new_targets=0,error=None if error is None else repr(error),archive_error=None if ae is None else repr(ae),archive_exact=archive is not None,archive_sha256=archive))
 if error:raise error
 if ae:raise ae
 print('All312 closed metric rows/cost-resource identities/four signs and bank criteria reproduced;0newWorlds')
if __name__=='__main__':
 if len(sys.argv)==1:
  with oralab.lock():
   assert not ROOT.exists() and not REPORT.exists() and shutil.disk_usage(L).free>=68*M
   b=Budget(L/'runs/strategy88-closed-census-v1-controller-20261015',dict(raw=6*M,failure=2*M),8*M)
   n=run([sys.executable,'-B',str(Path(__file__)),oralab.sha(L/'state/operator.lock')],Limits(memory_bytes=768*M,cpu_seconds=120,wall_seconds=240,processes=4),cwd=D)
   with b.create('raw','native.json') as f:f.write(enc(n))
   b.write_snapshot('failure');assert native_ok(n),n['output'];print(n['output'])
 else:assert len(sys.argv)==2;worker(sys.argv[1])
