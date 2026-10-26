"""Preparation-only accounting. No World imports, grants, seeds or execution."""
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
GATE='data/eka1-authentication-qualification-gates-20261026.json'
GATE_SHA='7bd9a58e541f5380c7e465ee4b18aa2d6e81efaa3d51e3f6dee1f56b38b20b81'
ROLES=('owner','original_producer','selection_replay','true','identity_sham','xor1','independent_verifier')
PANELS=('complete_original_equality','earliest_outcome_blind_READ','empty_FORAGE_overwrites',
 'paid_birth_ancestry','no_READ_keeps_outcomes','common_prestate_tick_minus1',
 'one_paid_READ_and_conservation','true_sham_physical_identity','xor_only_declared_READ',
 'complete_derived_suffix','wrong_source_owner_raw_rejected','early_late_failure_and_restore')
PROOFS=('assignment_registry','original_owner_grant','original_raw_native_receipt',
 'common_prestate_raw_custody','executed_code_interpreter_stdlib','exact_source_safe_CI',
 'semantic_panel_fixtures','native_containment_fit','closure_archive_exact_restore','independent_admission')
CAPS=dict(inputs=2,roles_per_input=7,concurrency=1,processes_per_job=4,
 child_memory_bytes=2*1024**3,job_memory_bytes=4*1024**3,
 user_cpu_seconds_per_role=120,wall_seconds_per_role=180,closure_seconds_per_role=30,
 input_bytes_per_role=64*1024**2,output_bytes_per_role=128*1024**2,
 archive_bytes_total=4*1024**3,archive_expanded_bytes_total=4*1024**3,
 files_per_role=32,archive_files_total=512,json_depth=64,json_nodes=2000000,
 process_births_total=56,geneses_per_input=32,dispatches_per_genesis=4096)


def validate(plan):
    fields={'schema','status','source_gate_sha256','source_pins','dose_slots','roles','panels','caps',
            'external_proofs','execution_authorized','scientific_admission','retry_policy'}
    if type(plan) is not dict or set(plan)!=fields or plan['schema']!='ORA-EKA1-NATIVE-QUALIFICATION-PLAN-v1':
        raise ValueError('Exact preparation schema')
    if plan['status']!='PREPARATION_ONLY_NOT_REGISTERED' or plan['source_gate_sha256']!=GATE_SHA:
        raise ValueError('Accepted source gate binding')
    if plan['execution_authorized'] is not False or plan['scientific_admission'] is not False:
        raise ValueError('Preparation cannot grant authority')
    if plan['dose_slots']!=[1,8] or any(type(x) is not int for x in plan['dose_slots']):
        raise ValueError('Both dose slots, no selected seeds')
    if plan['roles']!=list(ROLES) or plan['panels']!=list(PANELS):
        raise ValueError('Complete role graph and required panels')
    if type(plan['caps']) is not dict or set(plan['caps'])!=set(CAPS):
        raise ValueError('Complete resource dimensions')
    if any(type(plan['caps'][k]) is not int or plan['caps'][k]!=v for k,v in CAPS.items()):
        raise ValueError('Frozen positive integer caps; no bool or extensions')
    if (type(plan['external_proofs']) is not dict or set(plan['external_proofs'])!=set(PROOFS)
        or any(v is not None for v in plan['external_proofs'].values())):
        raise ValueError('No self-issued original/native authority; external proofs unassigned')
    if plan['retry_policy']!='NO_RETRY_NO_REPLACEMENT_RETAIN_PARTIAL_FAILURE':
        raise ValueError('Closed-attempt preservation')
    pins=plan['source_pins']
    if type(pins) is not dict or len(pins)!=9 or any(type(v) is not str or len(v)!=64 or any(c not in '0123456789abcdef' for c in v) for v in pins.values()):
        raise ValueError('Nine exact accepted source hashes')
    roles=CAPS['inputs']*CAPS['roles_per_input']
    return dict(schema='ORA-EKA1-QUALIFICATION-PREPARATION-CHECK-v1',preparation_valid=True,
        maximum_native_roles=roles,total_user_cpu_seconds=roles*CAPS['user_cpu_seconds_per_role'],
        sequential_wall_including_closure_seconds=roles*(CAPS['wall_seconds_per_role']+CAPS['closure_seconds_per_role']),
        total_input_bytes=roles*CAPS['input_bytes_per_role'],total_output_bytes=roles*CAPS['output_bytes_per_role'],
        maximum_geneses=CAPS['inputs']*CAPS['geneses_per_input'],
        maximum_dispatches=CAPS['inputs']*CAPS['geneses_per_input']*CAPS['dispatches_per_genesis'],
        missing_external_proofs=list(PROOFS),actual_original_status='NOT_CREATED_OR_ASSIGNED_BY_THIS_PLAN',
        resource_fit_qualified=False,actual_original_authenticated=False,actual_prestate_authenticated=False,
        actual_paid_continuation_authenticated=False,native_execution_authorized=False,scientific_admission=False)


def inspect(root=ROOT):
    gate_raw=(root/GATE).read_bytes()
    if hashlib.sha256(gate_raw).hexdigest()!=GATE_SHA:raise ValueError('Prior gate changed')
    gate=json.loads(gate_raw)
    plan=json.loads((root/'data/eka1-native-authentication-qualification-plan-20261026.json').read_text())
    result=validate(plan)
    if plan['source_pins']!=gate['source_pins']:raise ValueError('Source inventory changed')
    for name,digest in plan['source_pins'].items():
        if hashlib.sha256((root/name).read_bytes()).hexdigest()!=digest:raise ValueError('Source bytes changed: '+name)
    return result


if __name__=='__main__':print(json.dumps(inspect(),indent=2))
