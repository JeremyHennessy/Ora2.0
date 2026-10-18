"""Strict closed-audit adapter; no World/producer/writer import or activation."""
import sys
from pathlib import Path
from experiments import digital_pressure71_scientific_child as boundary
from experiments import digital_pilot74_publication_reader_v2 as physical
from experiments import evidence_write_grant68 as transport
MIB=1024**2
ROLE='closed-projection-publication-audit'
REQUIRED=boundary.REQUIRED|{'experiments/'+n+'.py' for n in ('digital_pilot74_closed_audit_child_v2','digital_pilot74_closed_publication_audit_v2','digital_pilot74_projection_referee_v2','digital_pilot74_publication_reader_v2')}
CONFIG=dict(version='DIGITAL-PILOT74-NATIVE-qualification-v1',seeds=[3],cuts=[8192,9216,10240],horizon=10240,mode='faithful',inheritance_mode='parent_copy',fuel_mode='renewed',dose=8,software_only=True)

def forbidden_modules():
    banned=('experiments.digital_pilot74_population','experiments.digital_pilot74_loader','experiments.digital_pressure71_population','experiments.digital_mobile54','experiments.digital_pilot74_projection_v2','experiments.digital_pilot74_publication_v2')
    assert not any(n in sys.modules for n in banned),'Unexpected producer/VM/writer module in literal role'

def admit(request):
    assert type(request) is dict and set(request)=={'schema','configuration','revision','source_files','source_sha256','configuration_sha256','role','registration','output','operator_lock'}
    assert request['schema']=='PILOT74-CLOSED-AUDIT-REQUEST-v2' and request['role']==ROLE
    assert physical.encode(request['configuration'])==physical.encode(CONFIG)
    physical.checksum(request['source_sha256']);physical.checksum(request['configuration_sha256'])
    revision=request['revision'];assert type(revision) is str and len(revision)==40 and all(c in '0123456789abcdef' for c in revision)
    assert type(request['source_files']) is dict and REQUIRED<=set(request['source_files'])
    assert physical.digest(physical.encode(request['source_files']))==request['source_sha256']
    assert physical.digest(physical.encode(CONFIG))==request['configuration_sha256']
    root=Path.cwd();assert boundary.verify_source(root,request['source_files'])==request['source_sha256']
    item=request['output'];assert type(item) is dict and set(item)=={'grant','seal'}
    boundary.validate_grant(dict(grant=item['grant'],grant_seal=item['seal'],configuration_sha256=request['configuration_sha256'],role=ROLE),request['source_sha256'],'proof')
    assert item['grant']['phase']=='raw' and item['grant']['name']=='receipts/'+ROLE+'.json' and item['grant']['limit']==128*1024
    lock=request['operator_lock'];assert type(lock) is dict and set(lock)=={'path','extent','sha256','device','inode'} and Path(lock['path'])==Path('D:/OraLab/state/operator.lock')
    _,ident=physical.read_exact(lock['path'],{k:lock[k] for k in ('extent','sha256')},16384)
    assert type(lock['device']) is int and type(lock['inode']) is int and ident[:2]==(lock['device'],lock['inode'])
    registration=physical.parse(physical.external(request['registration'],MIB),MIB)
    final=registration['final'];source=final['source_identity']
    assert source==dict(revision=revision,source_sha256=request['source_sha256'],config_sha256=request['configuration_sha256'],law='DIGITAL-PILOT74-FINITE-QUALIFICATION-v1')
    publication_root=Path(item['grant']['root'])/'raw'/'publication'
    assert publication_root.is_absolute() and publication_root.resolve().is_relative_to(Path('D:/OraLab/runs').resolve())
    forbidden_modules();boundary.module_origins(root,request['source_files'])
    return registration,publication_root

def main():
    try:
        assert len(sys.argv)==4
        raw,unused=physical.read_exact(sys.argv[1],dict(extent=int(sys.argv[2]),sha256=sys.argv[3]),MIB)
        request=physical.parse(raw,MIB);registration,publication_root=admit(request)
        from experiments import digital_pilot74_closed_publication_audit_v2 as independent
        forbidden_modules();boundary.module_origins(Path.cwd(),request['source_files'])
        proof=independent.audit(publication_root,registration)
        # Recheck all physical/source/grant/owner origins before immutable proof.
        admit(request);forbidden_modules()
        item=request['output']
        result=transport.record(item['grant'],item['seal'],request['source_sha256'],request['configuration_sha256'],ROLE,proof)
        forbidden_modules();boundary.module_origins(Path.cwd(),request['source_files'])
        print(physical.encode(dict(role=ROLE,proof=result,worlds=0,vm_steps=0,publication_accepted=False,live_attachment=False)).decode('ascii'))
    except BaseException as error:
        print(physical.encode(dict(failed=True,first_exception=repr(error),role=ROLE,worlds=0,vm_steps=0,complete_proof=False)).decode('ascii'),file=sys.stderr)
        raise

if __name__=='__main__':main()
