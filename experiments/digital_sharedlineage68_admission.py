"""Pure admission predicates. Prepared summaries are not executed evidence."""
from experiments.digital_sharedlineage68_interpret import ANCESTOR_WORDS,h
from experiments.digital_sharedlineage68_transition import validate_provenance
PRIMARY=tuple(range(69000,69004));UNSEEN=tuple(range(69200,69204));SEEDS=PRIMARY+UNSEEN

def ordinary_gate(summary,software=False):
    assert type(software) is bool
    assert summary['verified'] is True and type(summary['seed']) is int
    assert summary['seed'] in ((1,2) if software else SEEDS)
    assert summary['mode']=='faithful' and summary['inheritance_mode']=='parent_copy'
    assert summary['route']=='ancestor' and summary['formation_cost']==43
    assert summary['genesis_program_hash']==h(ANCESTOR_WORDS) and summary['fuel_mode']=='renewed'
    t=summary['turnover']
    for value in (summary['births'],t['post_founder_instructions'],t['maximum_generation'],
                  t['post_founder_paid_personal_births'],t['post_founder_renewed_food'],t['living_descendants']):
        assert type(value) is int and value>=0
    assert t['founder_expiry_tick'] is None or (type(t['founder_expiry_tick']) is int and 1<=t['founder_expiry_tick']<=4096)
    assert type(t['paid_personal_chains']) is list
    # Exact existing64 whole-paid lifecycle predicates; membership is prospective68.
    return (t['founder_expiry_tick'] is not None and t['post_founder_instructions']>=128
            and summary['births']>=12 and t['maximum_generation']>=3
            and t['post_founder_paid_personal_births']>0 and t['post_founder_renewed_food']>0
            and bool(t['paid_personal_chains']) and t['living_descendants']>=1)

def ordinary_admission(original,restored):
    assert type(original) is list and type(restored) is list
    assert len(original)==len(restored)==8
    all_gates=[]
    for export in (original,restored):
        seen=set()
        for summary in export:
            assert summary['seed'] not in seen;seen.add(summary['seed'])
            all_gates.append(ordinary_gate(summary))
        assert seen==set(SEEDS)
    # Evaluate every reference at both exports before aggregating success.
    return all(all_gates)

def require_durable_admission(receipt,expected_source,expected_configuration):
    validate_provenance(dict(source_sha256=expected_source,configuration_sha256=expected_configuration))
    assert type(receipt) is dict and receipt['source_sha256']==expected_source
    assert receipt['configuration_sha256']==expected_configuration
    assert type(receipt['references']) is int and receipt['references']==16
    assert type(receipt['treatment_worlds']) is int and receipt['treatment_worlds']==0
    assert receipt['original_restored_equal'] is True and receipt['all_paid_gates'] is True
    return True
