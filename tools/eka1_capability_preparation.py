"""Source/contract checks and necessary resource ceilings. Not a launcher/scorer.

No VM imports, seed queries, organism execution, diagnostic execution or new
population. Even a valid draft remains NOT_READY; bounds are not feasibility.
"""
import argparse
import ast
from fractions import Fraction
import hashlib
import json
from pathlib import Path

FOUNDER = [[4,1,1],[6,0,0],[5,0,1],[6,0,0],[10,0,0],[12,0,0],[13,1,0],[13,1,0],[7,0,1]]
GATES = {
    'ordinary_founder_and_unchanged_discovery_source': 'SOURCE_CHECK_REQUIRED',
    'new_functional_question_not_pressure71_rerun': 'INDEPENDENT_REVIEW_REQUIRED',
    'resource_and_lifetime_affordability': 'UNKNOWN',
    'nonlethal_paid_causal_information_assay': 'BLOCKED_UNIMPLEMENTED',
    'mutation_exposure_reproduction_selection_opportunity': 'UNKNOWN',
    'sampling_power_reserved_conditions': 'BLOCKED_UNASSIGNED',
    'native_resource_custody_owner': 'BLOCKED_UNQUALIFIED',
    'independent_scientific_and_execution_admission': 'BLOCKED_NOT_ADMITTED',
}


def validate(plan):
    assert plan['schema'] == 'ORA-EKA1-CAPABILITY-PROPOSAL-v1'
    assert plan['status'] == 'NOT_READY_NOT_REGISTERED'
    assert plan['execution_ready'] is False and plan['worlds_authorized'] == 0
    assert plan['ordinary_founder'] == FOUNDER and plan['authored_genotype_insertion'] is False
    assert plan['exact_target_genome'] is None and plan['genome_distance_acceptance'] is False
    d = plan['discovery']
    assert d['founder_policy'] == 'ORDINARY_UNSELECTED_FOUNDER_ONLY' and d['law_changes'] is False
    assert d['mutation_doses'] == [1,8] and d['best_dose_selection'] is False
    assert d['unit'] == 'WHOLE_DISCOVERY_WORLD'
    assert d['origin_sampling'] == 'FIRST_MUTATED_PAID_BIRTH_PER_WORLD_NO_REPLACEMENT'
    assert d['offspring_sampling'] == 'FIRST_PAID_LITERAL_FAITHFUL_CHILD_OF_SELECTED_ORIGIN_NO_REPLACEMENT'
    assert d['all_births_deaths_retained'] and d['no_survivor_or_high_score_selection']
    r = plan['resource_matching']
    assert r['basis'] == 'EXOGENOUS_RULES_STARTING_STATE_AND_BUDGETS'
    assert r['equal_realized_meals'] is False and r['meal_count_stopping'] is False
    assert r['stock'] == [32,16,16,0]
    assert [r[k] for k in ('site0_locked_stock','unlock_global_tick','offer_period_global_dispatches',
                           'offers_per_site','capacity_per_site')] == [16,64,64,4,32]
    assert [r[k] for k in ('code_words','state_units','material_units','configured_population_cap',
                           'initial_organism_energy','packet_energy','energy_cap','global_horizon','own_turn_expiry')] == [27,16,512,32,12,20,64,4096,256]
    f = plan['functional_claim']
    assert f['genotype_independent'] and not f['opcode_presence_is_acceptance']
    assert f['no_posthoc_composite_score'] and not f['novel_algorithm_or_general_intelligence_claim']
    assert f['mandatory_economic_nulls'] == ['predeclared_balanced_fixed_port_allocation', 'same27_blind_alternator', 'same27_nursery_aware_blind']
    x = plan['diagnostics']
    assert x['status'] == 'UNIMPLEMENTED_UNQUALIFIED_NOT_ADMITTED'
    assert x['causal_states'] == ['intact','paid_sham','information_use_lesion']
    assert len(x['panels']) == 3 and len(x['reference_roles']) == len(set(x['reference_roles'])) == 5
    assert x['max_proposed_forks_per_discovery_world'] == 3*3+5 == 14
    assert all(value is None for key,value in plan['registration'].items() if key != 'reason')
    assert plan['gates'] == GATES
    return dict(draft_valid=True, scientific_execution_ready=False, worlds_authorized=0,
                warning='Valid metadata does not implement or qualify a causal assay or admission.')


def resource_bounds(plan):
    """Loose necessary ceilings for ordinary discovery laws, never forecasts."""
    r = plan['resource_matching']
    D = r['global_horizon']
    offers = (D // r['offer_period_global_dispatches']) * r['offers_per_site'] * 4
    accessible = r['initial_organism_energy'] + (sum(r['stock']) + offers) * r['packet_energy']
    # Founder constructor reserve is not organism-available input. Child12 is
    # transferred parent energy, not an additional source at each birth.
    extra_heat_per_birth = r['code_words'] + 18
    births = (accessible - D) // extra_heat_per_birth
    W = 3 * D
    mutation = []
    H = 2**64
    for dose in (1,8):
        cycles, rem = divmod(H,100)
        p = Fraction(cycles*dose+min(rem,dose),H)
        cycles31, rem31 = divmod(H,3100)
        delta = [cycles31*dose+max(0,min(dose,rem31-100*k)) for k in range(31)]
        assert sum(delta) == p*H
        mutation.append(dict(dose=dose, uniform_hash_assumption_only=True,
                             expected_mutated_words_ceiling=float(W*p),
                             expected_COPY_mutated_information_opcode_words_ceiling=float(D*4*Fraction(max(delta),H)),
                             unchanged_complete27word_copy_probability_under_independence=float((1-p)**27),
                             useful_paid_origin_lower_bound=0,
                             warning='COPY mutation only, not all SELFWRITE-generated behaviour. Hypothetical hash uniformity is not viable variants, sampling power or new seed odds.'))
    return dict(discovery_global_dispatch_ceiling=D, own_turn_expiry=r['own_turn_expiry'],
                maximum_renewal_offers=offers, maximum_organism_accessible_energy=accessible,
                constructor_energy_credited_as_organism_input=0,
                simultaneous_mature_material_ceiling=r['material_units']//(r['code_words']+r['state_units']),
                completed_birth_energy_ceiling_at_full_4096_dispatch_horizon=births,
                birth_bound_formula='D +45B <=12+20*(64+16*floor(D/64)); full-horizon D=4096 only, no attainable-birth or survival claim.',
                paid_copy_word_ceiling=W, hypothetical_mutation_supply=mutation,
                proposed_scientific_starts_per_discovery_world=1+plan['diagnostics']['max_proposed_forks_per_discovery_world'],
                proposed_dispatch_ceiling_including_all_diagnostic_roles=D*(1+plan['diagnostics']['max_proposed_forks_per_discovery_world']),
                role_bound_limit='Schematic only if future admitted diagnostic roles obey the same horizon; law-changing controls remain unqualified. N, native wall/CPU/RAM/log/storage and total assay costs unassigned.',
                resource_affordability_qualified=False, mutation_opportunity_qualified=False)


def review(root):
    path = root/'data/eka1-capability-proposal-20261023.json'
    raw = path.read_bytes()
    plan = json.loads(raw)
    validity = validate(plan)
    for name, expected in plan['source_sha256'].items():
        assert hashlib.sha256((root/name).read_bytes()).hexdigest() == expected
    mobile = ast.parse((root/'experiments/digital_mobile54.py').read_text(encoding='utf-8'))
    literal = next(node.value for node in mobile.body if isinstance(node,ast.Assign)
                   and any(isinstance(t,ast.Name) and t.id == 'PROGRAM' for t in node.targets))
    assert ast.literal_eval(literal) == plan['ordinary_founder']
    return dict(schema='ORA-EKA1-CAPABILITY-PREPARATION-REVIEW-v1',
                plan_sha256=hashlib.sha256(raw).hexdigest(), source_pins=plan['source_sha256'],
                validation=validity, resource_bounds=resource_bounds(plan),
                source_mechanism_check='Exact unchanged Windows discovery source and ordinary founder verified; no World instantiated.',
                gates=plan['gates'], scientific_execution_ready=False,
                preparation_decision='PROPOSAL_ONLY', execution_decision='NO_GO', substrate_feasibility='UNKNOWN',
                new_worlds=0, new_vm_steps=0, new_seed_queries=0, external_model_calls=0)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--root', type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(review(args.root.resolve()), indent=2, sort_keys=True))
