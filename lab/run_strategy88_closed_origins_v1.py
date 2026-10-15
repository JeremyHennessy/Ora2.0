"""Prospectively registered one-shot retained-origin read with exact archive."""
import ast,hashlib,json,shutil,sys,zipfile
from pathlib import Path
L=Path('D:/OraLab');D=L/'src/Ora2.0-recording82';M=1024**2;sys.path.insert(0,str(L/'tools'));sys.path.insert(0,str(D))
import oralab
from experiments.process_limits import run,Limits
from experiments.evidence_budget import Budget
from experiments.digital_revision84_custody import open_reserved
from experiments.digital_credited_fallback87v2_metric_binding import authenticate
from experiments.digital_credited_fallback87v2_primary_boundary import verify_source
from cognitive76_controller_core_v2 import enc,fill_reserved,native_ok
TAG='strategy88-closed-origins-v1';ROOT=L/'runs'/(TAG+'-20261015');REG=L/'reports'/(TAG+'-registration.json');REPORT=L/'reports'/(TAG+'.json')
SOURCE=L/'tools/strategy88_closed_origins_v1.py';CONTRACT=L/'reports/strategy88-closed-origins-contract-v1-20261015.md';PRIMARY=L/'reports/strategy88-primary-v1.json'
OLD=L/'runs/strategy88-primary-v1-20261015'
def read(p):return json.loads(p.read_bytes())
def spec(p):return dict(path=str(p),extent=p.stat().st_size,sha256=oralab.sha(p))
def files():
 r=read(PRIMARY);assert r['verified'] and r['archive_exact'] and r['native_calls']==53 and r['logical_originals']==312
 assert oralab.sha(OLD/'archive/complete.zip')==r['archive_sha256']
 for k,v in r['pins'].items():assert oralab.sha(Path(k))==v
 old=read(L/'reports/credited-fallback87v2-primary-v1.json')
 for k,v in old['pins'].items():assert oralab.sha(Path(k))==v
 paths={'worker.py':SOURCE,'owners/controller.py':Path(__file__),'owners/contract.md':CONTRACT,'owners/primary.json':PRIMARY,
  'owners/primary-registration.json':L/'reports/strategy88-primary-v1-registration.json','owners/publication.json':L/'reports/strategy88-closed-publication-v1.json','owners/source-ci.json':L/'reports/strategy88-source-ci-af8aed39d58a.json'}
 config=read(L/'reports/strategy88-primary-v1-registration.json')['configuration'];members={}
 for seed in list(range(1010100,1010106))+list(range(1010300,1010306)):
  previous=[]
  for role in (f'original:{seed}:generate',f'original:{seed}:audit',f'restored:{seed}:generate',f'original:{seed}:metrics'):
   body=r['completed_roles'][role];p=Path(body['path']);assert spec(p)==body
   stem=role.replace(':','-');request=OLD/'raw/request'/(stem+'.json');native=OLD/'raw/native'/(stem+'.json');q=read(request);n=read(native);info=p.lstat()
   authenticate(q,n,body,role,config,str(p),(info.st_dev,info.st_ino));assert verify_source(OLD/'raw'/role.split(':')[0],q['source_files'])==q['source_sha']
   if role.endswith(':audit'):assert q['input']==previous[0]
   if role.endswith(':generate'):
    if role.startswith('restored:'):assert (body['extent'],body['sha256'])==(previous[0]['extent'],previous[0]['sha256'])
    previous.append(body)
   members['raw/data/'+stem+'.json']=body
   for path in (request,native):paths['custody/'+path.parent.name+'/'+path.name]=path;members['raw/'+path.parent.name+'/'+path.name]=spec(path)
   if not role.startswith('restored:'):paths[f'inputs/{seed}-'+role.split(':')[-1]+'.json']=p
 final=r['completed_roles']['original:all:accept'];paths['inputs/final.json']=Path(final['path']);members['raw/data/original-all-accept.json']=final
 assert sum(p.stat().st_size for p in paths.values())<=112*M
 # Closed archive membership authenticates retained bodies/requests/native before any new read.
 with zipfile.ZipFile(OLD/'archive/complete.zip') as z:
  for name,s in members.items():
   h=hashlib.sha256();extent=0
   with z.open(name) as f:
    while block:=f.read(M):extent+=len(block);h.update(block)
   assert extent==s['extent'] and h.hexdigest()==s['sha256']
 return paths
def plan(paths):
 raw={k:p.stat().st_size for k,p in paths.items()};raw.update({'native.json':M,'request.json':M,'output.json':8*M,'owners/registration.json':65536})
 assert sum(raw.values())<=128*M;fail={'outcome.json':8*M,'budget.json':8*M};lim=dict(raw=sum(raw.values()),failure=16*M,restore=sum(raw.values())+16*M,archive=144*M)
 assert lim['restore']<=144*M;return raw,fail,lim
def pins(paths):return {str(p):oralab.sha(p) for p in paths.values()}
def worker(owner):
 assert oralab.sha(L/'state/operator.lock')==owner;reg=read(REG);paths=files();assert pins(paths)==reg['pins'];raw,fail,lim=plan(paths);b=Budget(ROOT,lim,432*M)
 error=None;ae=None;out=None;archive=None;calls=0
 try:
  for phase,entries in (('raw',raw),('failure',fail)):
   for name,size in entries.items():
    with b.create(phase,name,reserve=size):pass
    with b.create('restore',phase+'/'+name,reserve=size):pass
  with b.create('archive','complete.zip',reserve=144*M):pass
  for name,p in paths.items():
   with open_reserved(b,'raw',name) as dst:
    with p.open('rb') as src:
     while block:=src.read(M):dst.write(block)
   assert oralab.sha(ROOT/'raw'/name)==reg['pins'][str(p)]
  fill_reserved(ROOT,'owners/registration.json',enc(reg),65536)
  batches=[dict(seed=s,body=spec(ROOT/'raw/inputs'/f'{s}-generate.json'),metrics=spec(ROOT/'raw/inputs'/f'{s}-metrics.json'),proof=spec(ROOT/'raw/inputs'/f'{s}-audit.json')) for s in list(range(1010100,1010106))+list(range(1010300,1010306))]
  q=dict(source_sha256=oralab.sha(SOURCE),batches=batches,output=str(ROOT/'raw/output.json'));fill_reserved(ROOT,'request.json',enc(q),M)
  n=run([sys.executable,'-B',str(ROOT/'raw/worker.py'),str(ROOT/'raw/request.json')],Limits(memory_bytes=512*M,cpu_seconds=60,wall_seconds=90,processes=3),cwd=D)
  calls+=1;fill_reserved(ROOT,'native.json',enc(n),M);assert native_ok(n),n['output']
  receipt=json.loads(n['output']);out=read(ROOT/'raw/output.json');assert out['verified'] and receipt['sha256']==oralab.sha(ROOT/'raw/output.json') and receipt['extent']==(ROOT/'raw/output.json').stat().st_size
  assert pins(paths)==reg['pins']
 except BaseException as e:error=e
 finally:
  try:
   with open_reserved(b,'failure','outcome.json') as f:f.write(enc(dict(error=None if error is None else repr(error),new_worlds=0,new_targets=0,native_calls=calls)))
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
  oralab.write_json(REPORT,dict(verified=error is None and ae is None,summary=out,pins=reg['pins'],native_calls=calls,new_worlds=0,new_targets=0,error=None if error is None else repr(error),archive_error=None if ae is None else repr(ae),archive_exact=archive is not None,archive_sha256=archive))
 if error:raise error
 if ae:raise ae
 print('All312 paid paths/all192 source origins/all48 contrasts independently reproduced;0newWorlds-targets')
if __name__=='__main__':
 action=sys.argv[1]
 if action=='register':
  with oralab.lock():
   assert len(sys.argv)==2 and not ROOT.exists() and not REG.exists() and not REPORT.exists() and shutil.disk_usage(L).free>=440*M
   allowed={'collections','hashlib','json','os','stat','sys','pathlib'}
   for node in ast.walk(ast.parse(SOURCE.read_bytes())):
    if isinstance(node,ast.Import):assert all(x.name in allowed for x in node.names)
    if isinstance(node,ast.ImportFrom):assert node.module in allowed
   paths=files();plan(paths);oralab.write_json(REG,dict(pins=pins(paths),scope='All312 closed originals/all192 origin histories;zero World/target calls',contract_sha=oralab.sha(CONTRACT)))
 elif action=='execute':
  with oralab.lock():
   assert len(sys.argv)==2;paths=files();assert pins(paths)==read(REG)['pins']
   b=Budget(L/'runs'/(TAG+'-controller-20261015'),dict(raw=6*M,failure=2*M),8*M)
   n=run([sys.executable,'-B',str(Path(__file__)),'worker',oralab.sha(L/'state/operator.lock')],Limits(memory_bytes=768*M,cpu_seconds=300,wall_seconds=600,processes=4),cwd=D)
   with b.create('raw','native.json') as f:f.write(enc(n))
   b.write_snapshot('failure');assert native_ok(n),n['output'];print(n['output'])
 else:assert action=='worker' and len(sys.argv)==3;worker(sys.argv[2])
