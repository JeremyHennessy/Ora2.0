"""Fail-closed data/source/owner admission for one full-workload qualification.

External exact pins authenticate review origin; this module never issues a grant
or creates PASS evidence. No World construction, native launch or retry here.
"""
import copy,os,time,sys
from pathlib import Path
from experiments import digital_pilot74_publication_reader_v2 as physical
from experiments import digital_pilot74_finite_requests_v2 as requests
from experiments import digital_pilot74_finite_inventory_v2 as inventory
from experiments import digital_pilot74_guardian_v1 as guardian
SCHEMA='PILOT74-WHOLE-WORKLOAD-QUALIFICATION-v1'
MODE='new_software_resource_recovery_qualification'
REVIEWS={'source_scope','native_build','wire_storage','whole_source_ci'}
CEILINGS=dict(memory_bytes=2147483648,user_cpu_seconds=2400,wall_ms=3600000,contained_processes=4,raw_archive_restore_each_bytes=1342177280,failure_bytes=134217728,controller_bytes=8388608,minimum_free_bytes=6442450944)

def parsed(pin,cap=131072):return physical.parse(physical.external(pin,cap),cap)
def binding(r):
    value=copy.deepcopy(r);value['qualification'].pop('grant',None)
    return physical.digest(physical.encode(value))

def shape(r,plan):
    assert r['schema']==SCHEMA and r['mode']==MODE
    assert set(r['reviews'])==REVIEWS
    assert set(r['qualification'])=={'plan','grant','preserved_failure_lock'}
    assert plan['schema']=='PILOT74-WHOLE-WORKLOAD-PLAN-v1'
    assert plan['source_sha256']==r['source_sha256'] and plan['revision']==r['revision']
    assert plan['configuration_sha256']==r['configuration_sha256']
    assert physical.encode(r['configuration'])==physical.encode(requests.CONFIG)
    assert plan['ceilings']==CEILINGS
    assert plan['counts']==dict(roles=26,genesis=2,hydrates=15,vm_steps=34816)
    expected=[row['name'] for row in inventory.retained.plan()['roles']]
    assert plan['roles']==expected and len(expected)==26
    assert plan['production_admission'] is False and plan['live_attachment'] is False
    assert plan['attempts']==1 and plan['retry_permitted'] is False
    assert plan['caller_module']=='experiments.digital_pilot74_qualification_caller_v1'
    assert type(plan['closure_reserve_ms']) is int and 0<plan['closure_reserve_ms']<3600000
    assert Path(r['operator_lock']['path'])==Path(r['root']).parent/'qualification-owner.lock'
    assert Path(r['operator_lock']['path'])!=Path('D:/OraLab/state/operator.lock')
    return True

def validate(r):
    if sys.flags.optimize:raise ValueError('Optimized admission forbidden')
    q=r['qualification'];plan=parsed(q['plan']);shape(r,plan)
    reviews={}
    for kind,pin in r['reviews'].items():
        v=parsed(pin)
        assert v['schema']=='PILOT74-QUALIFICATION-PREFLIGHT-REVIEW-v1'
        assert v['kind']==kind and v['verdict']=='PASS'
        assert v['scope']=='one_full_workload_qualification_only'
        assert v['revision']==r['revision'] and v['source_sha256']==r['source_sha256']
        assert v['configuration_sha256']==r['configuration_sha256'] and v['plan']==q['plan']
        assert v['reviewer_identity'] and v['review_evidence'] and v['production_admission'] is False
        if kind=='whole_source_ci':assert v['head_sha']==r['revision'] and v['conclusion']=='success' and v['old_suites_rerun'] is False
        reviews[kind]=v
    preserved=q['preserved_failure_lock'];assert Path(preserved['path'])==Path('D:/OraLab/state/operator.lock')
    _,identity=physical.read_exact(preserved['path'],{k:preserved[k] for k in ('extent','sha256')},16384)
    assert identity[:2]==(preserved['device'],preserved['inode'])
    grant=parsed(q['grant']);now=time.monotonic_ns()
    assert grant['schema']=='PILOT74-FULL-QUALIFICATION-OWNER-GRANT-v1' and grant['verdict']=='PASS'
    assert grant['registration_body_sha256']==binding(r) and grant['plan']==q['plan']
    assert grant['source_sha256']==r['source_sha256'] and grant['operator_lock']==r['operator_lock']
    assert grant['reviewer_identity'] and grant['review_evidence']
    assert grant['issued_monotonic_ns']<=now<grant['expires_monotonic_ns']<=grant['issued_monotonic_ns']+300*10**9
    assert grant['attempts']==1 and grant['production_admission'] is False
    lock=parsed(r['operator_lock'],16384)
    assert lock['schema']=='PILOT74-QUALIFICATION-OWNER-LOCK-v1'
    owner={k:lock[k] for k in ('pid','creation_filetime_decimal')}
    assert grant['owner']==owner and type(owner['pid']) is int and owner['pid']>0
    k=guardian._kernel();handle=k.OpenProcess(0x1000|0x100000,False,owner['pid']);guardian.checked(handle)
    try:
        assert str(guardian._birth(k,handle))==owner['creation_filetime_decimal']
        assert k.WaitForSingleObject(handle,0)==258
    finally:guardian.checked(k.CloseHandle(handle))
    return reviews
