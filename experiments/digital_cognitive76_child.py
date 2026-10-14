"""Finite Cognitive76 source/config/grant endpoints; no runtime activation API."""
import hashlib,json,os,stat,sys
from pathlib import Path
from experiments.digital_cognitive76_source import manifest,programmes,candidate,REFERENCES
CONFIG=dict(version='DIGITAL-COGNITIVE76-SCIENTIFIC-v1',primary=list(range(77400,77408)),unseen=list(range(77600,77608)),controls=['intact','model_disabled','history_misbound'],candidates=list(range(16)),references=list(REFERENCES),horizon=512,failure_penalty=4,formation=76,source_manifest_sha256=hashlib.sha256(json.dumps(manifest(),sort_keys=True,separators=(',',':')).encode()).hexdigest(),contract_sha256='1f0a9a05b1eb6887c02f7fbedaccc628184288d11295064fab3c8b8def177572')
REQUIRED={'experiments/'+n+'.py' for n in ('__init__','digital_experience75_source','digital_cognitive76_source','digital_cognitive76_controls','digital_cognitive76_world','digital_cognitive76_referee','digital_cognitive76_history','digital_cognitive76_child','digital_capsule01_custody','evidence_write_grant68','process_limits','evidence_budget','evidence_budget_audit')}
def canonical(v):return json.dumps(v,sort_keys=True,separators=(',',':')).encode()
def hash_string(v):assert type(v) is str and len(v)==64 and all(c in '0123456789abcdef' for c in v)
def pairs(items):
 value={}
 for key,item in items:
  assert key not in value;value[key]=item
 return value
def read_spec(spec,cap):
 assert type(spec) is dict and set(spec)=={'path','extent','sha256'}
 assert type(spec['extent']) is int and 0<spec['extent']<=cap;hash_string(spec['sha256'])
 from experiments.digital_capsule01_custody import read_recording
 raw=read_recording(spec['path'],spec['extent'],spec['sha256'])
 value=json.loads(raw.decode('ascii'),object_pairs_hook=pairs);assert canonical(value)==raw
 return value

def plain(path,directory=False):
    info=path.lstat()
    assert not stat.S_ISLNK(info.st_mode) and not getattr(info,'st_file_attributes',0)&0x400
    assert stat.S_ISDIR(info.st_mode) if directory else stat.S_ISREG(info.st_mode) and info.st_nlink==1
    return info

def bounded_bytes(path,cap,extent=None):
    path=Path(path);assert path.is_absolute() and type(cap) is int and cap>0
    for parent in path.parents:plain(parent,True)
    before=plain(path);assert 0<before.st_size<=cap
    if extent is not None:assert type(extent) is int and 0<extent<=cap and before.st_size==extent
    with path.open('rb') as stream:
        opened=os.fstat(stream.fileno())
        assert (opened.st_dev,opened.st_ino,opened.st_size)==(before.st_dev,before.st_ino,before.st_size)
        assert stat.S_ISREG(opened.st_mode) and opened.st_nlink==1
        data=stream.read(cap+1)
    after=plain(path)
    assert len(data)==before.st_size<=cap and (after.st_dev,after.st_ino,after.st_size)==(before.st_dev,before.st_ino,before.st_size)
    return data

def verify_source(root,pins):
    assert type(pins) is dict and REQUIRED<=set(pins)
    root=Path(root).resolve()
    for name,value in pins.items():
        assert type(name) is str and name.isascii() and '\\' not in name and ':' not in name
        assert name and all(part not in ('','.','..') for part in name.split('/'))
        assert not Path(name).is_absolute();hash_string(value)
        data=bounded_bytes(root/name,1024**2)
        assert hashlib.sha256(data).hexdigest()==value
    return hashlib.sha256(canonical(pins)).hexdigest()

def module_origins(root,pins):
    for name,module in list(sys.modules.items()):
        if name.startswith('experiments.'):
            path='experiments/'+name.split('.')[-1]+'.py'
            assert path in pins and Path(module.__file__).resolve()==root/path

def validate_grant(request,source_sha,endpoint):
    from experiments import evidence_write_grant68 as transport
    grant=request['grant'];hash_string(request['grant_seal'])
    assert type(grant) is dict and set(grant)=={'version','root','phase','name','limit','source_sha','config_sha','role','device','inode'}
    assert transport.digest(grant)==request['grant_seal']
    assert grant['version']=='sharedlineage68-file-grant-candidate-v1'
    assert (grant['source_sha'],grant['config_sha'],grant['role'])==(source_sha,request['configuration_sha256'],request['role'])
    maximum=(8 if endpoint=='proof' else 64)*1024**2
    assert type(grant['limit']) is int and 0<grant['limit']<=maximum
    assert type(grant['phase']) is str and grant['phase'].isascii() and grant['phase'].replace('-','').isalnum()
    name=grant['name'];assert type(name) is str and '\\' not in name and ':' not in name
    assert name and all(part not in ('','.','..') for part in name.split('/'))
    root=Path(grant['root']);assert root.is_absolute()
    path=root/grant['phase']/name
    for parent in path.parents:transport.plain(parent,True)
    info=transport.plain(path)
    assert info.st_size==0 and type(grant['device']) is int and type(grant['inode']) is int
    assert (info.st_dev,info.st_ino)==(grant['device'],grant['inode'])

def roles(chunk):
 assert type(chunk) is int and chunk in (0,1,2)
 return [f'candidate{i}' for i in range(chunk*8,chunk*8+8)] if chunk<2 else list(REFERENCES)
def admit(request):
 assert type(request) is dict and set(request)=={'configuration','revision','source_files','source_sha256','configuration_sha256','seed','control','chunk','kind','export','role','input','grant','grant_seal'}
 assert canonical(request['configuration'])==canonical(CONFIG)
 assert request['configuration_sha256']==hashlib.sha256(canonical(CONFIG)).hexdigest()
 assert type(request['revision']) is str and len(request['revision'])==40 and all(c in '0123456789abcdef' for c in request['revision'])
 assert type(request['seed']) is int and request['seed'] in CONFIG['primary']+CONFIG['unseen']
 assert request['control'] in CONFIG['controls'];roles(request['chunk'])
 assert request['kind'] in ('generate','audit') and request['export'] in ('original','restored')
 assert request['kind']!='audit' or request['export']=='original'
 role=f"{request['export']}:{request['seed']}:{request['control']}:{request['chunk']}:{request['kind']}"
 assert request['role']==role and (request['input'] is None if request['kind']=='generate' else type(request['input']) is dict)
 assert type(request['source_files']) is dict and REQUIRED<=set(request['source_files'])
 assert request['source_sha256']==hashlib.sha256(canonical(request['source_files'])).hexdigest()
 endpoint='proof' if request['kind']=='audit' else 'raw'
 validate_grant(request,request['source_sha256'],endpoint)
 assert request['grant']['limit']==(1024**2 if endpoint=='proof' else 16*1024**2)
 return role
def main():
 request=json.loads(bounded_bytes(Path(sys.argv[1]),1024**2),object_pairs_hook=pairs);role=admit(request)
 root=Path.cwd();pins=request['source_files'];assert verify_source(root,pins)==request['source_sha256']
 from experiments import evidence_write_grant68 as transport
 counts=dict(genesis=0,ordinary_steps=0)
 if request['kind']=='audit':
  from experiments import digital_cognitive76_referee as referee
  batch=read_spec(request['input'],16*1024**2)
  assert set(batch)=={'contract','seed','control','chunk','histories','learning','stage_credit'}
  assert batch['contract']=='DIGITAL-COGNITIVE76-BATCH-v1' and type(batch['seed']) is int and batch['seed']==request['seed'] and batch['control']==request['control'] and type(batch['chunk']) is int and batch['chunk']==request['chunk']
  assert batch['learning'] is False and batch['stage_credit'] is False and [x['role'] for x in batch['histories']]==roles(request['chunk'])
  expected=programmes();proofs=[]
  for item in batch['histories']:
   assert set(item)=={'role','ancestry','row'}
   expected_ancestry=candidate(int(item['role'][9:])) if item['role'].startswith('candidate') else None
   assert item['ancestry']==expected_ancestry
   row=item['row'];assert row['seed']==request['seed'] and row['control_mode']==request['control'] and row['route']==item['role']
   proofs.append(dict(role=item['role'],row_sha256=referee.h(row),summary=referee.audit(row,expected[item['role']])))
  value=dict(contract='DIGITAL-COGNITIVE76-PROOF-v1',seed=request['seed'],control=request['control'],chunk=request['chunk'],proofs=proofs,learning=False,stage_credit=False)
  assert 'experiments.digital_cognitive76_world' not in sys.modules and 'experiments.digital_cognitive76_history' not in sys.modules
 else:
  from experiments import digital_cognitive76_world as kernel,digital_cognitive76_history as producer
  old_init,old_step=kernel.World.__init__,kernel.World.step
  def counted_init(self,*a,**kw):counts['genesis']+=1;return old_init(self,*a,**kw)
  def counted_step(self):
   result=old_step(self)
   if result:counts['ordinary_steps']+=1
   return result
  kernel.World.__init__,kernel.World.step=counted_init,counted_step
  try:
   value=producer.batch(request['seed'],request['control'],request['chunk'])
   assert counts['genesis']==len(roles(request['chunk'])) and counts['ordinary_steps']==sum(x['row']['final']['tick'] for x in value['histories'])
  except BaseException as error:
   print(canonical(dict(failed=True,role=role,counts=counts,error=repr(error),partial_state_unavailable=True,stage_credit=False)).decode(),file=sys.stderr);raise
  finally:kernel.World.__init__,kernel.World.step=old_init,old_step
 module_origins(root,pins);assert verify_source(root,pins)==request['source_sha256']
 receipt=transport.record(request['grant'],request['grant_seal'],request['source_sha256'],request['configuration_sha256'],role,value)
 assert verify_source(root,pins)==request['source_sha256']
 print(canonical(dict(role=role,revision=request['revision'],source_sha256=request['source_sha256'],configuration_sha256=request['configuration_sha256'],receipt=receipt,counts=counts,learning=False,stage_credit=False)).decode())
if __name__=='__main__':main()
