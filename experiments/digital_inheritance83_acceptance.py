"""Independent frozen complete-denominator arithmetic; no World/target imports.

The custody controller must bind each metric receipt to its native job, full
literal proof and exact producer replay BEFORE invoking this interpreter. This
module cannot establish those external facts and never grants execution admission.
"""
from collections import Counter
from fractions import Fraction
from math import comb

PRIMARY = tuple(range(1008900, 1008908))
UNSEEN = tuple(range(1009100, 1009108))
ARMS = ('variation', 'no_variation', 'inheritance_disabled',
        'model_disabled', 'history_misbound')


def integer(value, minimum=0):
    assert type(value) is int and value >= minimum, 'invalid integer'
    return value


def ratio(value):
    return dict(numerator=value.numerator, denominator=value.denominator)


def paired_sign(differences):
    """Zero differences remain in the cohort, outside the nonzero sign trial."""
    assert len(differences) == 16
    wins = sum(d > 0 for d in differences)
    losses = sum(d < 0 for d in differences)
    n = wins + losses
    p = Fraction(sum(comb(n, k) for k in range(wins, n + 1)), 2 ** n)
    return dict(cohort=16, wins=wins, losses=losses, ties=16-n,
                nonzero=n, p=ratio(p), passes=p <= Fraction(1, 60))


def validate_metric(m, seed, arm):
    assert type(m) is dict and m['seed'] == seed and m['mode'] == arm
    assert m['finite_horizon'] == 16384
    integer(m['R']); assert type(m['S_numerator']) is int
    integer(m['S_denominator'], 1); integer(m['gate0_episodes'])
    assert m['S_denominator'] == max(1, m['gate0_episodes'])
    assert len(m['episodes']) == m['gate0_episodes']
    assert len(m['functional_children']) == len(set(m['functional_children'])) == m['R']
    assert len(m['changed_functional_children']) == len(set(m['changed_functional_children']))
    assert set(m['changed_functional_children']) <= set(m['functional_children'])
    counts = {str(q): 0 for q in (2, 4, 8)}
    score = 0
    sessions = set(); headers = set(); children = set()
    for e in m['episodes']:
        key = (integer(e['actor']), integer(e['session']))
        assert key not in sessions; sessions.add(key)
        q = e['proposed']; assert q is None or type(q) is int and q in (2, 4, 8)
        if q is not None: counts[str(q)] += 1
        f = e['child_fitness']; assert type(f) is int and f in (0, 1)
        child = e['paid_child']; header = e['header_write_id']
        if header is not None:
            integer(header); assert header not in headers; headers.add(header)
        if child is None:
            assert f == 0
        else:
            integer(child, 1); assert child not in children; children.add(child)
            assert header is not None and q is not None
            assert f == int(child in m['functional_children'])
        z = 3 * (int(q == 8) - int(q == 2)) * f
        assert e['score'] == z
        score += z
    assert m['proposal_counts'] == counts
    assert m['accepted_uniform_proposals'] == sum(counts.values())
    assert m['S_numerator'] == score
    # Keep real energy/cost reporting independent of the finite fitness endpoint.
    for field in ('captured', 'paid_actor_cost', 'living_energy', 'births', 'deaths', 'paid_dispatches'):
        integer(m[field])
    assert m['R'] <= m['births'] and m['paid_dispatches'] <= 16384
    assert 112 + m['captured'] - m['paid_actor_cost'] == m['living_energy']
    assert m['retained_operating_surplus'] == m['captured'] - m['paid_actor_cost']
    assert m['physics_validator'] is False and m['new_worlds'] == 0
    assert m['selection_accepted'] is False
    for field, width in (('actual_offered_packets', 3), ('actual_served_opportunities', 3)):
        assert type(m[field]) is list and all(type(x) is list and len(x) == width for x in m[field])


def common_opportunities(arms):
    """Multiset intersections, retaining actual cue/lineage and admission loss."""
    offered = [Counter((x[0], x[1]) for x in m['actual_offered_packets']) for m in arms]
    admitted = [Counter((x[0], x[1]) for x in m['actual_offered_packets'] if x[2] == 'admitted') for m in arms]
    served = [Counter((x[0], x[1], tuple(x[2])) for x in m['actual_served_opportunities']) for m in arms]
    def overlap(values):
        result = values[0].copy()
        for value in values[1:]: result &= value
        return sum(result.values())
    return dict(common_offered_packet_cue=overlap(offered),
                common_admitted_packet_cue=overlap(admitted),
                common_served_packet_cue_lineage=overlap(served),
                offered_by_arm=[sum(v.values()) for v in offered],
                admitted_by_arm=[sum(v.values()) for v in admitted],
                served_by_arm=[sum(v.values()) for v in served])


def interpret(receipts):
    """Sixteen per-seed receipts, each containing all five original-cell metrics."""
    assert type(receipts) is list and len(receipts) == 16, 'incomplete seed denominator'
    by_seed = {}
    for receipt in receipts:
        seed = receipt['seed']
        assert type(seed) is int and seed in PRIMARY + UNSEEN and seed not in by_seed
        rows = receipt['metrics']
        assert type(rows) is list and len(rows) == 5, 'incomplete arm denominator'
        by_arm = {}
        for m in rows:
            arm = m['mode']; assert arm in ARMS and arm not in by_arm
            validate_metric(m, seed, arm); by_arm[arm] = m
        assert set(by_arm) == set(ARMS)
        by_seed[seed] = by_arm
    assert set(by_seed) == set(PRIMARY + UNSEEN)
    differences = {name: [] for name in ('R_no_variation', 'R_inheritance_disabled', 'S_inheritance_disabled')}
    banks = {}; opportunities = {}; equal_map_diagnostics = {}
    for label, seeds in (('primary', PRIMARY), ('unseen', UNSEEN)):
        totals = {name: Fraction(0) for name in differences}
        diagnostics = {arm: 0 for arm in ARMS[3:]}
        proposals = {str(q): 0 for q in (2, 4, 8)}
        changed = 0; completed = 0; retained = {arm: 0 for arm in ARMS}
        for seed in seeds:
            rows = by_seed[seed]; v = rows['variation']
            contrasts = dict(R_no_variation=Fraction(v['R']-rows['no_variation']['R']),
                             R_inheritance_disabled=Fraction(v['R']-rows['inheritance_disabled']['R']),
                             S_inheritance_disabled=Fraction(v['S_numerator'], v['S_denominator'])-
                             Fraction(rows['inheritance_disabled']['S_numerator'], rows['inheritance_disabled']['S_denominator']))
            for name, value in contrasts.items():
                differences[name].append(value); totals[name] += value
            for arm in diagnostics: diagnostics[arm] += v['R']-rows[arm]['R']
            for q in proposals: proposals[q] += v['proposal_counts'][q]
            completed += v['accepted_uniform_proposals']; changed += len(v['changed_functional_children'])
            for arm in ARMS: retained[arm] += rows[arm]['retained_operating_surplus']
            opportunities[str(seed)] = common_opportunities([rows[a] for a in ARMS])
            if seed in (seeds[0], seeds[1]):
                equal_map_diagnostics[str(seed)] = dict(
                    variation_R=v['R'], misbound_R=rows['history_misbound']['R'],
                    equal_R=v['R'] == rows['history_misbound']['R'])
        criteria = dict(proposals=completed >= 8 and all(n >= 1 for n in proposals.values()),
                        changed_functional_children=changed >= 2,
                        positive_fitness_and_proposal_contrasts=all(x > 0 for x in totals.values()),
                        actual_model_diagnostics=all(x > 0 for x in diagnostics.values()))
        banks[label] = dict(criteria=criteria, completed_uniform_proposals=completed,
                            proposal_counts=proposals, changed_functional_children=changed,
                            contrasts={k: ratio(v) for k, v in totals.items()},
                            model_R_contrasts=diagnostics, retained_operating_surplus=retained)
    signs = {name: paired_sign(values) for name, values in differences.items()}
    passed = all(all(b['criteria'].values()) for b in banks.values()) and all(s['passes'] for s in signs.values())
    return dict(complete_original_cells=80, independent_seed_count=16, banks=banks,
                paired_sign_tests=signs, registered_numeric_criteria_met=passed,
                actual_common_opportunities=opportunities, equal_map_diagnostics=equal_map_diagnostics,
                new_own_history_learning_attribution=False,
                attribution_scope='Requires separately reviewed actual channel/feedback traces; no new attribution from endpoint arithmetic alone',
                scientific_acceptance_requires_external_custody=True,
                scope='Only inherited capacity under supplied architecture; no invented algorithm, sustained evolution or general intelligence',
                new_worlds=0, target_queries=0, execution_admission=False)
