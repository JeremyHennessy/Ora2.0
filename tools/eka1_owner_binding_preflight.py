"""Offline prospective consistency only. No imports of replay or native code.

No identity here authenticates a producer, OS handle, assignment or grant.
Actual canonical-ledger consumption/process hooks remain unimplemented.
"""
import hashlib
import json
from pathlib import Path

FROZEN_PLAN = 'data/eka1-native-authentication-qualification-plan-20261026.json'
FROZEN_PLAN_SHA256 = '8b7d8b296d0479d11675c637a69f0cb889a67c833ac7aad6a09772ad4a095eb8'
EXTRA_SOURCES = {'tools/eka1_cumulative_reservations.py',
                 'tools/eka1_owner_binding_preflight.py'}
REVIEWED_REVISIONS = {
    'experiments/digital_eka1_selection_replay_v1.py':
        '557824ce51b2d10aeebcc888bc912feae7ebdb6c6060de8f227962146c765505',
    'experiments/digital_eka1_derived_reconstruction_v1.py':
        'f98e36f925b6472fc310b4afccd17208b6d9945474f31d9e907d15ef82270683',
    'tools/eka1_cumulative_reservations.py':
        '735c7fbd9564e04e715e8125df315eba47e36a8dc66c3d1a24dc23ef7c33b73d'}


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'),
                                    allow_nan=False).encode('ascii')).hexdigest()


def validate(plan, *, expected_owner, frozen):
    """Check a supplied prospective role binding; never return READY."""
    fields = {'schema', 'status', 'binding', 'roles', 'caps', 'source_pins',
              'external_proofs', 'execution_authorized', 'scientific_admission'}
    if type(plan) is not dict or set(plan) != fields:
        raise ValueError('Exact source-only owner binding schema')
    if (plan['schema'] != 'ORA-EKA1-OWNER-BINDING-PREFLIGHT-v1' or
            plan['status'] != 'PROSPECTIVE_UNASSIGNED_NOT_READY' or
            plan['execution_authorized'] is not False or
            plan['scientific_admission'] is not False):
        raise ValueError('No execution or admission authority')
    if type(expected_owner) is not str or not 0 < len(expected_owner) <= 128:
        raise ValueError('External expected owner label required')
    binding = plan['binding']
    if (type(binding) is not dict or set(binding) !=
            {'owner_id', 'assignment_registry_sha256', 'original_owner_grant_sha256',
             'ledger_file_identity'} or binding['owner_id'] != expected_owner):
        raise ValueError('One prospective owner binding')
    if any(binding[k] is not None for k in binding if k != 'owner_id'):
        raise ValueError('Unassigned proof/physical ledger cannot be self-issued')
    expected = [{'dose': d, 'role_index': i, 'binding_sha256': digest(binding),
                 'ledger_file_identity': None}
                for d in (1, 8) for i in range(7)]
    if type(plan['roles']) is not list or digest(plan['roles']) != digest(expected):
        raise ValueError('All14 roles share one binding/ledger across both doses')
    caps = plan['caps']
    if (type(caps) is not dict or set(caps) != set(frozen['caps']) or
            any(type(caps[k]) is not int or caps[k] != v
                for k, v in frozen['caps'].items())):
        raise ValueError('Frozen global caps; no per-role multiplication')
    proofs = plan['external_proofs']
    if (type(proofs) is not dict or set(proofs) != set(frozen['external_proofs']) or
            any(v is not None for v in proofs.values())):
        raise ValueError('All external authentication proofs remain unassigned')
    pins = plan['source_pins']
    if (type(pins) is not dict or set(pins) != set(frozen['source_pins']) | EXTRA_SOURCES or
            any(type(v) is not str or len(v) != 64 or
                any(c not in '0123456789abcdef' for c in v) for v in pins.values())):
        raise ValueError('Complete revised11-source closure required')
    fixed = dict(frozen['source_pins'])
    fixed.update(REVIEWED_REVISIONS)
    if any(pins[name] != pin for name, pin in fixed.items()):
        raise ValueError('Unchanged laws and reviewed wrapper/ledger pins required')
    return dict(schema='ORA-EKA1-OWNER-BINDING-RESULT-v1', consistency_valid=True,
                status='NOT_READY', maximum_roles=14, maximum_process_births=56,
                maximum_geneses=64, maximum_dispatches=262144,
                actual_ledger_bound=False, process_birth_hooks_integrated=False,
                executed_code_authenticated=False, resource_fit_qualified=False,
                actual_original_authenticated=False, native_execution_authorized=False,
                scientific_admission=False)


def inspect(plan, *, root, expected_owner):
    """Inspect bounded raw source files only; not old gate reacceptance."""
    root = Path(root)
    frozen_path = root/FROZEN_PLAN
    if frozen_path.is_symlink():
        raise ValueError('Frozen preparation path is a link')
    raw = frozen_path.read_bytes()
    if hashlib.sha256(raw).hexdigest() != FROZEN_PLAN_SHA256:
        raise ValueError('Historical preparation bytes changed')
    result = validate(plan, expected_owner=expected_owner, frozen=json.loads(raw))
    for name, pin in plan['source_pins'].items():
        path = root/name
        if any(p.is_symlink() for p in (root, path.parent, path)):
            raise ValueError('Source/import-root link')
        if path.stat().st_size > 1024**2:
            raise ValueError('Source extent')
        if hashlib.sha256(path.read_bytes()).hexdigest() != pin:
            raise ValueError('Revised source bytes differ: '+name)
    # No new initializer may silently join the tools namespace closure.
    if (root/'tools/__init__.py').exists():
        raise ValueError('Unreviewed tools package initializer')
    result['raw_source_files_checked'] = len(plan['source_pins'])
    result['namespace_and_loaded_code_custody'] = 'UNQUALIFIED'
    return result
