"""Finite71 endpoint adapter, UNQUALIFIED until exact parent/source/custody checks.

Referee paths import no producer. No teacher, successful genome or policy.
Matching metadata/flags do not establish actual paid admission.
"""
import hashlib,json,os,stat,sys
from pathlib import Path
from experiments.digital_pressure71_admission import admit,hash_string
from experiments.digital_pressure71_runplan import roles

REQUIRED={'experiments/'+name+'.py' for name in (
    '__init__','digital_pressure71_scientific_child','digital_pressure71_admission',
    'digital_pressure71_runplan','digital_pressure71_population','digital_pressure71_natural_referee',
    'digital_pressure71_world','digital_pressure71_referee','digital_pressure71_transition',
    'digital_pressure71_family','digital_pressure71_census','digital_functional69_contract',
    'digital_sharedlineage68_population','digital_sharedlineage68_interpret','digital_mobile54',
    'digital_informative_exposure23_interpret','evidence_write_grant68')}

def canonical(value):return json.dumps(value,sort_keys=True,separators=(',',':')).encode()

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

def read_spec(spec,cap):
    assert type(spec) is dict and set(spec)=={'path','sha256','extent'}
    hash_string(spec['sha256'])
    # Extent is checked before opening/hashing; overlarge inputs are never read.
    data=bounded_bytes(Path(spec['path']),cap,spec['extent'])
    assert hashlib.sha256(data).hexdigest()==spec['sha256']
    return json.loads(data)

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

def role_binding(request):
    assert request['kind'] in ('population','population_ref','fork','fork_ref')
    endpoint='proof' if request['kind'].endswith('_ref') else 'raw'
    kind=request['kind'].removesuffix('_ref')
    matches=[r for r in roles() if r['name']==request['name']]
    assert len(matches)==1;expected=matches[0]
    assert all(request[key]==value and type(request[key]) is type(value) for key,value in expected.items() if key!='kind')
    assert expected['kind']==kind and request['export'] in ('original','restored')
    assert request['role']==f"{request['export']}:{request['name']}:{endpoint}"
    return endpoint

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

def value_for(request,provenance):
    """Internal dispatch; execute_request must complete guards first."""
    kind=request['kind'];calls=0
    if kind in ('population','fork'):
        from experiments import digital_pressure71_population as kernel
        original=kernel.World.__init__
        def counted(self,*args,**kwargs):
            nonlocal calls
            calls+=1;return original(self,*args,**kwargs)
        kernel.World.__init__=counted
        try:
            if kind=='population':
                value=kernel.history(request['seed'],mode=request['mode'],inheritance_mode=request['inheritance_mode'],
                    dose=request['dose'],horizon=4096,software_only=False)
            else:
                natural=read_spec(request['input'],64*1024**2)
                assert (natural['seed'],natural['dose'],natural['mode'],natural['inheritance_mode'])==(request['seed'],request['dose'],'mutating','parent_copy')
                assert natural['horizon']==4096 and natural['software_only'] is False
                from experiments import digital_pressure71_world as fork
                value=fork.history(natural,request['slot_kind'],request['fork_role'],provenance)
        finally:kernel.World.__init__=original
    else:
        row=read_spec(request['input'],64*1024**2)
        if kind=='population_ref':
            assert (row['seed'],row['dose'],row['mode'],row['inheritance_mode'])==(request['seed'],request['dose'],request['mode'],request['inheritance_mode'])
            assert row['horizon']==4096 and row['software_only'] is False
            from experiments import digital_pressure71_natural_referee as referee
            value=dict(verified=True,summary=referee.audit(row),natural_history_hash=row['hash'],provenance=provenance,stage_credit=False)
        else:
            assert (row['natural']['seed'],row['natural']['dose'],row['slot_kind'],row['role'])==(request['seed'],request['dose'],request['slot_kind'],request['fork_role'])
            assert row['natural']['horizon']==4096 and row['natural']['software_only'] is False
            from experiments import digital_pressure71_referee as referee
            value=referee.audit(row,provenance)
            if request['slot_kind']=='parent' and not value['null']:
                from experiments.digital_pressure71_census import census_from_replayed
                value['census']=census_from_replayed(row['branch'],value['summary'],value['slot']['target'])
    return value,calls

def execute_request(root,request):
    root=Path(root).resolve();pins=request['source_files']
    source_sha=verify_source(root,pins);assert source_sha==request['source_sha256']
    provenance=dict(source_sha256=source_sha,configuration_sha256=request['configuration_sha256'])
    receipt=read_spec(request['admission'],1024**2) if 'admission' in request else None
    treatment=admit(request,provenance,receipt)
    endpoint=role_binding(request)
    validate_grant(request,source_sha,endpoint)
    module_origins(root,pins)
    # Producer import/construction starts only after all above membership/bindings.
    value,calls=value_for(request,provenance)
    module_origins(root,pins)
    from experiments import evidence_write_grant68 as transport
    manifest=transport.record(request['grant'],request['grant_seal'],source_sha,
        request['configuration_sha256'],request['role'],value)
    assert verify_source(root,pins)==source_sha
    manifest.update(world_constructors=calls,kind=request['kind'],software_only=False,treatment=treatment)
    return manifest

def main():
    root=Path.cwd().resolve()
    assert Path(__file__).resolve()==root/'experiments/digital_pressure71_scientific_child.py'
    request=json.loads(bounded_bytes(Path(sys.argv[1]).absolute(),1024**2))
    print(json.dumps(execute_request(root,request),sort_keys=True,separators=(',',':')))

if __name__=='__main__':main()
