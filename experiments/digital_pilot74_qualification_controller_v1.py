"""Qualification-only exact full workload. No production PASS fabrication or CLI.

No grant/review issuer. Independent source/build/preflight and actual owner grant
are external prerequisites. Same Controller methods, roles and resource laws.
"""
from experiments.digital_pilot74_finite_controller_v2 import *
from experiments import digital_pilot74_qualification_admission_v1 as admission

def validate_guardian(spec,expected):
    assert spec['sha256']==expected and os.name=='nt'
    r=physical.parse(physical.external(spec,65536),65536)
    admission.validate(r)
    from experiments import digital_pressure71_scientific_child as boundary
    assert boundary.verify_source(r['source_root'],r['source_files'])==r['source_sha256']
    assert guardian.ARTIFACTS<=set(r['source_files'])
    assert r['source_files']['experiments/native/pilot74_guardian_v1.exe']==r['guardian']['artifact']['sha256']
    assert r['guardian']['version']=='PILOT74-NATIVE-GUARDIAN-CONFIG-v1'
    assert Path(r['guardian']['artifact']['path'])==Path(r['source_root'])/'experiments/native/pilot74_guardian_v1.exe'
    physical.external(r['guardian']['artifact'],512*1024)
    build=physical.parse(physical.external(r['guardian']['build_review'],65536),65536)
    assert build['schema']=='PILOT74-GUARDIAN-BUILD-REVIEW-v1' and build['verdict']=='PASS'
    assert build['revision']==r['revision'] and build['artifact_sha256']==r['guardian']['artifact']['sha256'] and build['old_checks_rerun'] is False
    lock=r['operator_lock'];_,identity=physical.read_exact(lock['path'],{k:lock[k] for k in ('extent','sha256')},16384)
    assert identity[:2]==(lock['device'],lock['inode']) and guardian.win32_id(lock['path'])==r['guardian']['lock_win32_id']
    assert Path(r['python']['path']).resolve()==Path(sys.executable).resolve()==Path('D:/OraLab/tools/Python312/python.exe').resolve()
    physical.external(r['python'],16*1024**2)
    return r

def launch_qualification(spec,expected):
    return guardian._launch_guardian(spec,expected,validate_guardian(spec,expected))

def registration(spec,expected_sha):
    assert spec['sha256']==expected_sha
    raw=read(spec,65536);r=physical.parse(raw,65536)
    assert type(r) is dict and set(r)=={'schema','mode','run_id','world_id','root','source_root','revision','source_files','source_sha256','configuration','configuration_sha256','python','operator_lock','contracts','reviews','compatibility','guardian','qualification'}
    assert r['schema']=='PILOT74-WHOLE-WORKLOAD-QUALIFICATION-v1' and r['mode']=='new_software_resource_recovery_qualification'
    assert enc(r['configuration'])==enc(requests.CONFIG) and sha(enc(r['configuration']))==r['configuration_sha256']
    for key in ('run_id','world_id'):
        text=r[key];assert type(text) is str and 1<=len(text)<=80 and text.isascii() and all(c.isalnum() or c in '-_.' for c in text)
    revision=r['revision'];assert type(revision) is str and len(revision)==40 and all(c in '0123456789abcdef' for c in revision)
    root=Path(r['root']);source_root=Path(r['source_root'])
    assert root.is_absolute() and root.resolve().is_relative_to(Path('D:/OraLab/runs').resolve()) and not root.exists()
    assert source_root.is_absolute() and Path(__file__).resolve()==source_root/'experiments/digital_pilot74_qualification_controller_v1.py'
    assert source_boundary.verify_source(source_root,r['source_files'])==r['source_sha256']==sha(enc(r['source_files']))
    source_boundary.module_origins(source_root,r['source_files'])
    assert Path(r['python']['path']).resolve()==Path('D:/OraLab/tools/Python312/python.exe').resolve()==Path(sys.executable).resolve()
    read(r['python'],16*MIB)
    assert shutil.disk_usage(root.parent).free>=6*1024**3
    assert type(r['contracts']) is dict and set(r['contracts'])=={'qualification','publication','observer_agreement'}
    for kind,contract in r['contracts'].items():
        assert contract['sha256']==CONTRACT_SHA[kind];read(contract,128*1024)
    reviews=admission.validate(r)
    assert type(r['compatibility']) is dict and set(r['compatibility'])=={'capsule','audit'}
    read(r['compatibility']['capsule'],24*MIB);read(r['compatibility']['audit'],128*1024)
    lock=r['operator_lock'];assert Path(lock['path'])==Path(r['root']).parent/'qualification-owner.lock'
    _,identity=physical.read_exact(lock['path'],{k:lock[k] for k in ('extent','sha256')},16384)
    assert identity[:2]==(lock['device'],lock['inode'])
    validate_guardian(spec,expected_sha)
    return r,raw,reviews,parent_job()

def execute_qualification(spec,expected_sha):
    """Called only by separately reviewed outer supervisor, never automation text."""
    r,raw,reviews,job=registration(spec,expected_sha)
    controller=None
    try:
        controller=Controller.__new__(Controller)
        Controller.__init__(controller,r,raw,reviews,job)
        controller.guardian.ready(controller)
        controller.exported_roles();controller.journals();controller.publish()
        return controller.finalize(True)
    except BaseException as first:
        if controller is not None and hasattr(controller,'completed') and not controller.finalized:
            try:controller.finalize(False,first)
            except BaseException as later:first.add_note('Failure custody/archive incomplete: '+repr(later))
        else:first.add_note('Outer supervisor must retain partial precharge/finalization; no inner complete archive assumed')
        raise
