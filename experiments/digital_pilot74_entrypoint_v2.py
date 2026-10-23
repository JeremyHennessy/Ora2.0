"""UNQUALIFIED direct-file pilot entrypoint. Exact external request pin required.

No run is authorized by this source. This launcher is part of the source union,
not an additional native experiment role, bootstrap grant or admission bypass.
"""
import hashlib,importlib,json,os,stat,sys
from pathlib import Path
MIB=1024**2
TARGETS={'digital_pilot74_child','digital_pilot74_source_ready_v2','digital_pilot74_journal_observed_child_v2','digital_pilot74_closed_audit_child_v2'}
CONFIG=dict(version='DIGITAL-PILOT74-NATIVE-qualification-v1',seeds=[3],cuts=[8192,9216,10240],horizon=10240,mode='faithful',inheritance_mode='parent_copy',fuel_mode='renewed',dose=8,software_only=True)

def encode(value):return json.dumps(value,sort_keys=True,separators=(',',':'),ensure_ascii=True,allow_nan=False).encode('ascii')
def digest(raw):return hashlib.sha256(raw).hexdigest()
def pairs(items):
    result={}
    for key,value in items:
        if key in result:raise ValueError('Duplicate canonical field')
        result[key]=value
    return result
def types(value,depth=0):
    assert depth<=24
    if type(value) is dict:
        assert all(type(k) is str for k in value)
        for item in value.values():types(item,depth+1)
    elif type(value) is list:
        for item in value:types(item,depth+1)
    else:assert value is None or type(value) in (str,int,bool)
def parse(raw):
    value=json.loads(raw,object_pairs_hook=pairs,parse_constant=lambda unused:(_ for _ in ()).throw(ValueError('Nonfinite input')))
    types(value);assert encode(value)==raw
    return value
def plain(path,directory=False):
    value=path.lstat()
    assert not stat.S_ISLNK(value.st_mode) and not getattr(value,'st_file_attributes',0)&0x400
    assert stat.S_ISDIR(value.st_mode) if directory else stat.S_ISREG(value.st_mode) and value.st_nlink==1
    return value
def identity(value):return value.st_dev,value.st_ino,value.st_size
def read(path,cap,expected=None):
    path=Path(path);assert path.is_absolute()
    chain=[(p,identity(plain(p,True))[:2]) for p in path.parents]
    before=plain(path);assert 0<before.st_size<=cap
    fd=os.open(path,os.O_RDONLY|getattr(os,'O_BINARY',0)|getattr(os,'O_NOFOLLOW',0))
    try:
        opened=os.fstat(fd);assert identity(opened)==identity(before) and stat.S_ISREG(opened.st_mode) and opened.st_nlink==1
        chunks=[];size=0
        while True:
            block=os.read(fd,min(65536,cap-size+1))
            if not block:break
            chunks.append(block);size+=len(block);assert size<=before.st_size
        raw=b''.join(chunks);assert len(raw)==before.st_size
        assert identity(os.fstat(fd))==identity(plain(path))==identity(before)
        for parent,old in chain:assert identity(plain(parent,True))[:2]==old
        if expected is not None:assert len(raw)==expected['extent'] and digest(raw)==expected['sha256']
        return raw,identity(before)
    finally:os.close(fd)

def bind(root,pins,identities):
    total=0
    assert type(pins) is dict and 1<=len(pins)<=256
    assert 'experiments/__init__.py' in pins and 'experiments/digital_pilot74_entrypoint_v2.py' in pins
    for relative,pin in pins.items():
        assert type(relative) is str and relative.isascii() and (relative.startswith('experiments/') and relative.endswith('.py') or relative in {'experiments/native/pilot74_guardian_v1.c','experiments/native/pilot74_guardian_v1.exe'}) and '..' not in relative and '\\' not in relative and ':' not in relative
        assert type(pin) is str and len(pin)==64 and all(c in '0123456789abcdef' for c in pin)
        raw,actual=read(root/relative,MIB);assert digest(raw)==pin;total+=len(raw)
        if relative in identities:assert identities[relative]==actual
        else:identities[relative]=actual
    assert total+65536<=1536*1024
    assert Path(__file__).resolve()==root/'experiments/digital_pilot74_entrypoint_v2.py'
    assert Path(sys.modules['__main__'].__file__).resolve()==Path(__file__).resolve()
    for name,module in list(sys.modules.items()):
        if name=='experiments' or name.startswith('experiments.'):
            path=Path(module.__file__).resolve();relative=path.relative_to(root).as_posix()
            assert relative in pins and digest(read(path,MIB)[0])==pins[relative]

def canonical_output_lines():
    """Emit canonical JSON with one LF byte on Windows as on other hosts.

    Keep the parent parser strict; never strip/normalize a received proof.
    This changes only text newline translation, not task/source authority.
    """
    sys.stdout.reconfigure(newline='\n')
    sys.stderr.reconfigure(newline='\n')

def main():
    canonical_output_lines()
    original=list(sys.argv);stage='arguments'
    try:
        assert not sys.flags.optimize and len(original) in (5,6)
        target=original[1];assert target=='outer' or target in TARGETS
        assert len(original)==(6 if target=='digital_pilot74_journal_observed_child_v2' else 5)
        cap=65536 if target=='outer' else MIB
        expected=dict(extent=int(original[3]),sha256=original[4]);assert type(expected['extent']) is int and 0<expected['extent']<=cap
        raw,request_identity=read(Path(original[2]),cap,expected);request=parse(raw)
        endpoint=request['endpoint'] if target=='digital_pilot74_journal_observed_child_v2' else request
        assert type(endpoint) is dict
        root=Path(endpoint['source_root']) if target=='outer' else Path.cwd()
        assert root.is_absolute() and root.resolve()==root
        pins=endpoint['source_files'];assert digest(encode(pins))==endpoint['source_sha256']
        assert endpoint['configuration']==CONFIG and digest(encode(CONFIG))==endpoint['configuration_sha256']
        assert type(endpoint['revision']) is str and len(endpoint['revision'])==40 and all(c in '0123456789abcdef' for c in endpoint['revision'])
        if target=='outer':assert endpoint['schema']=='PILOT74-FINITE-REGISTRATION-v2' and endpoint['mode']=='finite_qualification'
        if target=='digital_pilot74_source_ready_v2':assert endpoint['schema']=='PILOT74-SOURCE-READINESS-REQUEST-v2'
        if target=='digital_pilot74_closed_audit_child_v2':assert endpoint['schema']=='PILOT74-CLOSED-AUDIT-REQUEST-v2'
        if target=='digital_pilot74_child':assert endpoint['kind'] in ('generate','audit','resume')
        identities={};stage='before-target-source-binding';bind(root,pins,identities)
        # Direct-file invocation avoids executing experiments/__init__ before
        # this verification. Actual stdlib/interpreter remains a pinned premise.
        sys.path[0]=str(root)
        module_name='digital_pilot74_outer_supervisor_v2' if target=='outer' else target
        assert 'experiments/'+module_name+'.py' in pins
        stage='import-target';module=importlib.import_module('experiments.'+module_name)
        assert Path(module.__file__).resolve()==root/'experiments'/(module_name+'.py')
        bind(root,pins,identities)
        second,current=read(Path(original[2]),cap,expected);assert second==raw and current==request_identity
        stage='target-admission'
        if target=='outer':
            raise RuntimeError('Old Python outer supervisor path REFUSED; reviewed native guardian required')
            result=module.supervise(dict(path=original[2],**expected),expected['sha256'])
            # supervisor owns its terminal receipt; nothing written into inner.
            bind(root,pins,identities)
            assert result['inner_archive_and_restore_attested'] is True
        else:
            sys.argv=[str(root/'experiments'/(module_name+'.py'))]+original[2:]
            module.main()
            stage='after-target-source-binding';bind(root,pins,identities)
        # Abrupt crash78 exits deliberately cannot reach or claim this check.
    except BaseException as first:
        # No traceback truncation, retry or synthetic successful target receipt.
        try:sys.stderr.write(encode(dict(schema='PILOT74-ENTRYPOINT-FAILURE-v2',stage=stage,first_exception=repr(first),post_target_integrity_unknown=True)).decode('ascii')+'\n')
        except BaseException as later:first.add_note('Entrypoint diagnostic unavailable: '+repr(later))
        raise
    finally:sys.argv=original

if __name__=='__main__':main()
