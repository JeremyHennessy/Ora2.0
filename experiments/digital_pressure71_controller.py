"""Finite parent flow, with custody/native IO supplied by a reviewed adapter.

No VM, sampler, filesystem or process launcher here. Prepared callback success is
reachability only. Full source/native/grant qualification and paid literal replay
are separate obligations; this flow cannot authorize scientific execution.
"""
from experiments.digital_pressure71_admission import (
    VERSION, SEEDS, digest, hash_string, ordinary_admission, require_durable_admission)
from experiments.digital_pressure71_runplan import EXPORTS, roles, schedule
from experiments.digital_functional69_contract import integer
from experiments.digital_pressure71_measure import family_comparison, panel


def spec(value, cap):
    assert type(value) is dict and set(value) == {'path', 'sha256', 'extent'}
    assert type(value['path']) is str and value['path']
    hash_string(value['sha256']); integer(value['extent'], 1, cap)
    return value


def proof_binding(value, role, provenance):
    assert value['verified'] is True and value['stage_credit'] is False
    assert value['provenance'] == provenance
    assert type(value['seed'] if role['kind'] == 'fork' else value['summary']['seed']) is int
    if role['kind'] == 'population':
        s = value['summary']
        assert s['verified'] is True and s['software_only'] is False
        assert type(s['horizon']) is int and s['horizon'] == 4096
        for key in ('seed', 'dose', 'mode', 'inheritance_mode'):
            assert s[key] == role[key] and type(s[key]) is type(role[key])
    else:
        assert value['seed'] == role['seed'] and value['slot_kind'] == role['slot_kind']
        assert value['role'] == role['fork_role']
        assert type(value['null']) is bool
        if not value['null']:
            s = value['summary']
            assert s['verified'] is True and s['software_only'] is False
            for key, expected in (('seed', role['seed']), ('dose', role['dose']), ('horizon', 4096)):
                assert type(s[key]) is int and s[key] == expected
    hash_string(value['natural_history_hash'])


def drive(io, provenance):
    """One pass, no retries. Adapter must validate custody before returning values.

    io owns: source_check, precharge, prepared, endpoint, persist_admission,
    read_admission, record and failed. All must be bounded/locked by the caller.
    endpoint(export,role,endpoint,input_spec,admission_spec) returns spec,value;
    raw value is unused and may be None. A proof must hash to its file spec.
    """
    assert type(provenance) is dict and set(provenance) == {'source_sha256', 'configuration_sha256'}
    for value in provenance.values(): hash_string(value)
    plan = roles(); raw = {}; proofs = {}; proof_specs = {}; calls = 0; treatment_calls = 0
    admission_spec = None; admission = None
    try:
        io.source_check()
        # Adapter owes actual sealed files and accounting, not a returned boolean.
        io.precharge(schedule(), 14976 * 1024**2)
        for export in EXPORTS:
            calls += 1; io.prepared(export); io.source_check()

        def endpoint_pair(export, role):
            nonlocal calls, treatment_calls
            name = role['name']; treatment = role['kind'] == 'fork' or role.get('mode') == 'mutating'
            input_spec = raw[(export, role['natural_role'])] if role['kind'] == 'fork' else None
            for endpoint in ('raw', 'proof'):
                io.source_check()
                if treatment:
                    assert admission_spec is not None
                    durable = io.read_admission(admission_spec)
                    assert durable == admission and digest(durable) == admission_spec['sha256']
                    require_durable_admission(durable, provenance['source_sha256'], provenance['configuration_sha256'])
                calls += 1
                if treatment: treatment_calls += 1
                artifact, value = io.endpoint(export, dict(role), endpoint, input_spec, admission_spec)
                artifact = dict(spec(artifact, (64 if endpoint == 'raw' else 8) * 1024**2))
                if endpoint == 'raw':
                    input_spec = artifact; raw[(export, name)] = artifact
                else:
                    proof_binding(value, role, provenance)
                    if role['kind'] == 'fork':
                        assert value['natural_history_hash'] == proofs[(export, role['natural_role'])]['natural_history_hash']
                    assert digest(value) == artifact['sha256']
                    proofs[(export, name)] = value; proof_specs[(export, name)] = artifact
                io.source_check()

        for role in plan[:8]:
            for export in EXPORTS: endpoint_pair(export, role)
        assert calls == 34 and treatment_calls == 0
        references = {e: [proofs[(e, r['name'])]['summary'] for r in plan[:8]] for e in EXPORTS}
        paid = ordinary_admission(references['original'], references['restored'])
        equal = all(raw[('original', r['name'])]['sha256'] == raw[('restored', r['name'])]['sha256'] and
                    proofs[('original', r['name'])] == proofs[('restored', r['name'])] and
                    proof_specs[('original', r['name'])]['sha256'] == proof_specs[('restored', r['name'])]['sha256'] for r in plan[:8])
        rows = [dict(export=e, seed=r['seed'], dose=r['dose'], raw_sha256=raw[(e, r['name'])]['sha256'],
                     proof_sha256=proof_specs[(e, r['name'])]['sha256']) for r in plan[:8] for e in EXPORTS]
        admission = dict(version=VERSION, **provenance, references=16, treatment_worlds=0,
                         original_restored_equal=equal, all_paid_gates=paid, native_children=calls,
                         raw_proof_pairs=16, reference_receipts=rows, reference_bundle_sha256=digest(rows))
        io.record('ordinary-gates', dict(references=references, admission=admission))
        # Preserve negative admission, then stop BEFORE any treatment callback.
        admission_spec = dict(spec(io.persist_admission(admission), 1024**2))
        assert digest(admission) == admission_spec['sha256'] and io.read_admission(admission_spec) == admission
        require_durable_admission(admission, provenance['source_sha256'], provenance['configuration_sha256'])
        for role in plan[8:]:
            for export in EXPORTS: endpoint_pair(export, role)
        assert calls == 418 and treatment_calls == 384
        assert len(raw) == len(proofs) == len(proof_specs) == 208
        for role in plan:
            key_a = ('original', role['name']); key_b = ('restored', role['name'])
            assert raw[key_a]['sha256'] == raw[key_b]['sha256']
            assert proofs[key_a] == proofs[key_b] and proof_specs[key_a]['sha256'] == proof_specs[key_b]['sha256']
        families = []; populations = []
        for seed in SEEDS:
            for dose in (1, 8):
                natural = proofs[('original', f'{seed}-mutating-parent_copy-d{dose}')]
                populations.append(natural); s = natural['summary']
                context = dict(seed=seed, dose=dose, horizon=s['horizon'], software_only=s['software_only'],
                               natural_history_hash=natural['natural_history_hash'], birth_edges=s['birth_edges'])
                family = [proofs[('original', f'{seed}-{kind}-{role}-d{dose}')] for kind, role in
                          (('parent', 'sham'), ('parent', 'ancestor_value_control'),
                           ('child', 'sham'), ('child', 'inherited_source_control'))]
                families.append(family_comparison(*family, provenance, context))
        comparison = panel(families, populations, provenance)
        io.record('comparison', dict(families=families, panel=comparison))
        io.source_check()
        return dict(native_calls=calls, treatment_calls=treatment_calls, raw_proof_pairs=208,
                    admission=admission, comparison=comparison, scientific_acceptance=False,
                    stage_credit=False, requires_qualified_native_custody=True)
    except BaseException as error:
        io.failed(dict(error=repr(error), attempted_native_calls=calls, attempted_treatment_calls=treatment_calls,
                       recorded_raw=len(raw), recorded_proofs=len(proofs), scientific_acceptance=False, stage_credit=False))
        raise
