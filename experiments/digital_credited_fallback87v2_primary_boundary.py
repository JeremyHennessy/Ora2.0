"""Exact source-free boundary functions reused by AST; no producer imports."""
import hashlib,json,os,stat,sys
from pathlib import Path
REQUIRED={'experiments/'+n+'.py' for n in ('__init__','digital_experience75_source','digital_cognitive76_source','digital_cognitive76_controls','digital_cognitive76_world','digital_cognitive76_referee','digital_cognitive76_history','digital_cognitive76_child','digital_capsule01_custody','evidence_write_grant68','process_limits','evidence_budget','evidence_budget_audit')}

def canonical(v):return json.dumps(v,sort_keys=True,separators=(',',':')).encode()

def hash_string(v):assert type(v) is str and len(v)==64 and all(c in '0123456789abcdef' for c in v)

def pairs(items):
 value={}
 for key,item in items:
  assert key not in value;value[key]=item
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
