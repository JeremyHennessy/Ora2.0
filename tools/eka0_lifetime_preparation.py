"""Review-only contract validation and literal genotype predicates; no launcher."""
import argparse
import json
from pathlib import Path

REQUIRED_GATES = {
    'exact_source_and_raw_custody', 'actual_reachable_information_contrast',
    'paid_lifetime_resource_and_strong_control_qualification',
    'nonlethal_information_lesion_and_sham', 'viable_mutation_path_and_origin_review',
    'sampling_effect_and_reserved_bank_registration', 'independent_scientific_admission',
    'native_cpu_memory_storage_deadline_and_custody',
    'exclusive_world_owner_and_execution_authority',
    'separate_authored_reference_founder_permission_if_proposed',
}
FOUNDER = [[4,1,1],[6,0,0],[5,0,1],[6,0,0],[10,0,0],[12,0,0],[13,1,0],[13,1,0],[7,0,1]]
ARMS = {'feedback', 'blind_alternator', 'fixed0', 'fixed1', 'nursery_aware_blind'}


def validate(plan):
    assert plan['schema'] == 'ORA-EKA0-LIFETIME-PREPARATION-v1'
    assert plan['status'] == 'DRAFT_NOT_REGISTERED'
    assert plan['execution_ready'] is False and plan['worlds_authorized'] == 0
    assert plan['scientific_founder'] == FOUNDER
    programs = plan['authored_reference_programs']
    assert set(programs) == ARMS
    for name, p in programs.items():
        assert len(p) == 9 and all(len(t) == 3 for t in p)
        assert all(type(w) is int and 0 <= w < 32 for t in p for w in t)
        if name != 'feedback':
            assert not any(t[0] in (1,2,3,9) for t in p), 'Blind control reads food/private experience or rewrites code'
    assert programs['fixed0'][0] == [4,0,0] and programs['fixed1'][0] == [4,0,1]
    assert programs['nursery_aware_blind'][3] == [11,0,6]
    f = plan['food_matching']
    assert f['basis'] == 'EXOGENOUS_SOURCE_RULES_AND_STARTING_BUDGETS'
    assert f['initial_physical_stock_by_site'] == [32,16,16,0]
    assert (f['site0_locked_stock'], f['unlock_global_tick'], f['offers_per_site'],
            f['offer_period_global_dispatches'], f['site_capacity']) == (16,64,4,64,32)
    assert (f['initial_energy'], f['energy_cap'], f['code_words'], f['state_units'],
            f['total_material_units'], f['configured_population_cap']) == (12,64,27,16,512,32)
    for key in ('equal_realized_meals', 'meal_count_stopping', 'posthoc_matching_fixed_port', 'survivor_only_analysis'):
        assert f[key] is False, key
    e = plan['estimand']
    assert e['unit'] == 'WHOLE_PAIRED_WORLD_LINEAGE'
    assert e['denominator'] == 'ALL_ASSIGNED_INITIAL_FOUNDERS'
    assert (e['horizon_global_dispatches'], e['own_turn_expiry']) == (4096,256)
    assert e['no_composite_posthoc_score'] is True
    assert plan['causal_controls']['food_feedback_lesion_and_paid_sham'] == 'REQUIRED_NOT_IMPLEMENTED_OR_ADMITTED'
    assert set(plan['required_gates']) == REQUIRED_GATES and len(plan['required_gates']) == len(REQUIRED_GATES)
    assert plan['gate_status'] == 'ALL_SCIENTIFIC_EXECUTION_GATES_HELD'
    assert all(plan['closed_path_review']['budget'][k] == 0 for k in ('worlds','vm_steps','new_seed_queries','model_calls'))
    return dict(preparation_schema_valid=True, reference_words=27, mature_material=43,
                scientific_execution_ready=False, admission_granted=False,
                required_gates_held=sorted(REQUIRED_GATES), scope='Static preparation only; no execution method exists.')


def genotype_mask(words, founder, target):
    """Membership in one FIXED ten-edit subcube, never genotype selection."""
    assert len(words) == len(founder) == len(target) == 27
    mask = bit = 0
    for value, old, new in zip(words, founder, target):
        if old == new:
            if value != old:
                return None
        else:
            if value == new:
                mask |= 1 << bit
            elif value != old:
                return None
            bit += 1
    assert bit == 10
    return mask


def strict_transition(parent_birth, copied, child, changed_since_birth, founder, target):
    old = genotype_mask(parent_birth, founder, target)
    new = genotype_mask(child, founder, target)
    if changed_since_birth:
        return 'parent_code_changed'
    if copied != parent_birth:
        return 'copied_source_differs_from_birth'
    if old is None or new is None:
        return 'outside_subcube'
    if old == new:
        return 'faithful'
    diff = old ^ new
    return 'one_added_intended_edit' if (new | old) == new and diff.bit_count() == 1 else 'multiedit_or_reversion'


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--plan', type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(validate(json.loads(args.plan.read_text(encoding='utf-8'))), indent=2))
