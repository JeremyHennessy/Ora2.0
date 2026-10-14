"""Prepared Pressure71-v2 arithmetic only; no history or admission authority.

Caller owes independent full-history/COPY/birth/control authentication. Supplied
frames and booleans cannot prove a scientific result. No VM, sampler or policy.
"""
from fractions import Fraction
from experiments.digital_functional69_contract import contrast, integer

VERSION = 'DIGITAL-PRESSURE-SELECTION-71-v2'


def schedule_counts(original_roles=104):
    integer(original_roles, 1)
    return dict(endpoint_records=4 * original_roles,
                native_calls=4 * original_roles + 2,
                original_restored_comparison_pairs=2 * original_roles,
                precharged_record_mib=2 * original_roles * (64 + 8))


def cohort(frame):
    """Exact generation3/4 paid census; truth remains external, not in a flag."""
    assert type(frame) is dict
    for key in ('root', 'early_total', 'early_lineage', 'late_total', 'late_lineage'):
        integer(frame[key], 0, 4096)
    assert frame['early_lineage'] <= frame['early_total']
    assert frame['late_lineage'] <= frame['late_total']
    eligible = frame['early_total'] >= 2 and frame['late_total'] >= 2
    growth = None if not eligible else (
        Fraction(frame['late_lineage'], frame['late_total']) -
        Fraction(frame['early_lineage'], frame['early_total']))
    return eligible, growth, frame['early_lineage'] + frame['late_lineage']


def prepared_selection(parent, parent_control, child, child_control,
                       parent_changed, child_source_changed, edge, sham, control):
    """Fixture reachability; ALL returned results deny scientific acceptance."""
    assert type(parent_changed) is bool and type(child_source_changed) is bool
    assert type(edge) is dict and type(edge['present']) is bool
    missing = not edge['present']
    if not missing:
        assert edge['root_generation'] == 2 and type(edge['root_generation']) is int
        assert edge['child_generation'] == 3 and type(edge['child_generation']) is int
        integer(edge['root'], 1); integer(edge['child'], 1)
        integer(edge['child_parent'], 1); integer(edge['root_tick'], 1, 4096)
        integer(edge['child_tick'], 1, 4096)
        assert edge['child_parent'] == edge['root'] and edge['child'] != edge['root']
        assert edge['child_tick'] > edge['root_tick']
        assert sham['root'] == control['root'] == edge['root']
    p = contrast(parent, parent_control, parent_changed)
    c = contrast(child, child_control, child_source_changed)
    functional = (not missing and p['new_strategy'] and c['new_strategy'] and
                  child['births'] > 0 and child['food'] > 0)
    eligible_a, a, births_a = cohort(sham)
    eligible_b, b, births_b = cohort(control)
    opportunity = not missing and eligible_a and eligible_b and sham['late_lineage'] >= 2
    selected = (functional and opportunity and a > 0 and a > b and births_a > births_b)
    rational = lambda x: None if x is None else [x.numerator, x.denominator]
    return dict(version=VERSION, fixture_functional_candidate=bool(functional),
                fixture_selection_candidate=bool(selected), cohort_opportunity=opportunity,
                sham_growth=rational(a), control_growth=rational(b),
                descendant_birth_difference=births_a - births_b,
                missing=missing, scientific_acceptance=False, stage_credit=False,
                requires_independent_full_history=True)
