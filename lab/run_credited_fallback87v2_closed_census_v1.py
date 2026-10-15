"""One finite read-only closed-census role, no producer import or activation."""
import ast,json,sys,zipfile
from pathlib import Path
import oralab
L=Path('D:/OraLab');D=L/'src/Ora2.0-recording82';M=1024**2;sys.path.insert(0,str(D))
from experiments.evidence_budget import Budget
from experiments.process_limits import Limits,run
from cognitive76_controller_core_v2 import enc,fill_reserved,native_ok
ROOT=L/'runs/credited-fallback87v2-closed-census-v1-20261015'
SOURCE=L/'tools/credited_fallback87v2_closed_census_v1.py'

def read(p):return json.loads(p.read_bytes())
def spec(p):return dict(path=str(p),extent=p.stat().st_size,sha256=oralab.sha(p))

if __name__=='__main__':
 with oralab.lock():
  r=read(L/'reports/credited-fallback87v2-primary-v1.json');assert r['verified'] and r['archive_exact'] and r['native_calls']==309
  ast.parse(SOURCE.read_bytes())
  new=L/'runs/credited-fallback87v2-primary-v1-20261015'
  req=read(new/'raw/request/original-all-accept.json');assert len(req['input'])==16
  b=Budget(ROOT,dict(raw=64*M,archive=64*M,restore=64*M,failure=8*M),200*M)
  def save(phase,name,data,reserve=0):
   with b.create(phase,name,reserve=reserve) as f:f.write(data)
  def copy(p,name):
   with b.create('raw',name,reserve=p.stat().st_size) as dst:
    with p.open('rb') as src:
     while block:=src.read(M):dst.write(block)
   out=spec(ROOT/'raw'/name);assert out['sha256']==oralab.sha(p);return out
  save('raw','native.json',b'',M);save('raw','request.json',b'',M);save('raw','output.json',b'',2*M)
  source=copy(SOURCE,'worker.py');final=copy(new/'raw/data/original-all-accept.json','inputs/final.json')
  batches=[]
  for seed in list(range(1009700,1009708))+list(range(1009900,1009908)):
   metric_spec=req['input'][str(seed)]['body']
   metric=copy(Path(metric_spec['path']),f'inputs/{seed}-metrics.json');assert metric['sha256']==metric_spec['sha256']
   batches.append(dict(seed=seed,metrics=metric))
  for p in (Path(__file__),L/'reports/credited-fallback87v2-closed-census-contract-v1-20261015.md',L/'reports/credited-fallback87v2-primary-v1.json'):
   copy(p,'owners/'+p.name)
  request=dict(source_sha256=source['sha256'],final=final,batches=batches,output=str(ROOT/'raw/output.json'))
  fill_reserved(ROOT,'request.json',enc(request),M)
  error=None;archive_error=None;archive_sha=None;value=None
  try:
   n=run([sys.executable,'-B',str(ROOT/'raw/worker.py'),str(ROOT/'raw/request.json')],Limits(memory_bytes=512*M,cpu_seconds=60,wall_seconds=90,processes=3),cwd=D)
   fill_reserved(ROOT,'native.json',enc(n),M);assert native_ok(n),n['output']
   out=json.loads(n['output']);value=read(ROOT/'raw/output.json');assert out['verified'] and value['verified']
   assert out['sha256']==oralab.sha(ROOT/'raw/output.json') and out['extent']==(ROOT/'raw/output.json').stat().st_size<=2*M
  except BaseException as e:error=e
  finally:
   save('failure','outcome.json',enc(dict(error=None if error is None else repr(error),new_worlds=0,target_queries=0)))
   try:
    names=[p.relative_to(ROOT).as_posix() for phase in ('raw','failure') for p in (ROOT/phase).rglob('*') if p.is_file()]
    with b.create('archive','complete.zip') as f:
     with zipfile.ZipFile(f,'w',zipfile.ZIP_STORED) as z:
      for name in names:z.write(ROOT/name,name)
    with zipfile.ZipFile(ROOT/'archive/complete.zip') as z:
     for name in names:
      with z.open(name) as src:
       with b.create('restore',name) as dst:
        while block:=src.read(M):dst.write(block)
    assert all(oralab.sha(ROOT/p)==oralab.sha(ROOT/'restore'/p) for p in names)
    archive_sha=oralab.sha(ROOT/'archive/complete.zip')
   except BaseException as e:archive_error=e
   b.write_snapshot('failure')
   oralab.write_json(L/'reports/credited-fallback87v2-closed-census-v1.json',dict(verified=error is None and archive_error is None,
    native_calls=1,new_worlds=0,target_queries=0,summary=value,error=None if error is None else repr(error),
    archive_error=None if archive_error is None else repr(archive_error),archive_sha256=archive_sha,source_sha256=source['sha256']))
  if error:raise error
  if archive_error:raise archive_error
  print('Independent all816 metric-table accounting/all-nine signs and N/E verified;zero new Worlds/targets')
