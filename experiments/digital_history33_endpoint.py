"""Prospective summary predicate, after independent full-history verification.

This module neither runs a World nor authenticates its input. Prepared summaries
are evaluator fixtures only. A scientific caller must verify complete VM traces,
source ancestry, resource accounting and opportunity origins before extraction.
"""
import json

VERSION = 'DIGITAL-HISTORY-33-ENDPOINT-v1'
MODES = ('intact', 'retained_disabled', 'own_disrupted')
REFERENCES = tuple(f'affine{i}' for i in range(8)) + ('alternating', 'fixed0', 'fixed1')
FRESH_SEEDS = tuple(range(33100, 33108))
RESERVED_SEEDS = tuple(range(33200, 33208))


def validate(m):
    """Refuse inconsistent/bool-valued bills; absence is never zero-cost success."""
    for k in ('formation', 'food', 'fresh', 'own_origins', 'terminal_tick'):
        if type(m[k]) is not int:
            raise ValueError(k)
    if not (19 <= m['formation'] <= 112 and (m['formation']-16) % 3 == 0
            and 0 <= m['fresh'] <= 16 and m['fresh'] <= m['food'] <= 32
            and 0 <= m['own_origins'] <= 512 and 1 <= m['terminal_tick'] <= 512):
        raise ValueError('range')
    for k in ('completed', 'survived64', 'delivered_own', 'both_own_outcomes'):
        if type(m[k]) is not bool:
            raise ValueError(k)
    if m['completed']:
        t = m['completion_tick']
        if (type(t) is not int or not 64 <= t <= m['terminal_tick']
                or type(m['paid_work']) is not int
                or m['paid_work'] != m['formation'] + t
                or m['food'] != 32 or m['fresh'] != 16 or not m['survived64']):
            raise ValueError('complete bill')
    elif m['completion_tick'] is not None or m['paid_work'] is not None or m['food'] == 32:
        raise ValueError('incomplete bill')
    if not m['delivered_own'] and m['both_own_outcomes']:
        # Native availability in disrupted controls is a separate input channel.
        raise ValueError('native availability presented as delivered own history')


def compare(arms, references):
    """One genotype/one common exogenous seed; no selection or pooled inference.

    All controls must finish the same 32-local/16-fresh task. Resource stock,
    costs and exogenous targets must be matched upstream; actual trajectories
    are outcomes, not forced copies. A refusal is not general impossibility.
    """
    if set(arms) != set(MODES) or set(references) != set(REFERENCES):
        raise ValueError('complete cell required')
    for m in list(arms.values()) + list(references.values()):
        validate(m)
    if arms['own_disrupted']['delivered_own']:
        raise ValueError('disrupted history labelled own')
    if len({m['formation'] for m in arms.values()}) != 1:
        raise ValueError('candidate formation mismatch')
    reasons = []
    intact = arms['intact']
    if not all(m['completed'] for m in arms.values()):
        reasons.append('incomplete_candidate_or_control_exposure')
    if not (intact['delivered_own'] and intact['both_own_outcomes']
            and intact['own_origins'] >= 16):
        reasons.append('insufficient_personal_opportunity_before_completion')
    # Required ordinary references certify viable exploration. Failed fixed
    # ports stay reported, but do not create an infinite comparison advantage.
    if not all(references[r]['completed'] for r in ('affine3', 'alternating')):
        reasons.append('ordinary_reference_failure')
    completed_refs = [m for m in references.values() if m['completed']]
    if all(m['completed'] for m in arms.values()) and completed_refs:
        comparators = [arms[m] for m in MODES[1:]] + completed_refs
        if not all(intact['completion_tick'] < m['completion_tick']
                   and intact['paid_work'] < m['paid_work'] for m in comparators):
            reasons.append('no_strict_latency_and_paid_work_advantage')
    return dict(qualified=not reasons, reasons=reasons,
                incomplete_references=[r for r in REFERENCES if not references[r]['completed']],
                classification='prepared_predicate_or_scoped_retained_history_advantage',
                learning=False, stage_credit=False)


def contract():
    return dict(version=VERSION, candidates=list(range(56)), references=list(REFERENCES),
                controls=list(MODES), future_fresh_seeds=list(FRESH_SEEDS),
                reserved_unopened_seeds=list(RESERVED_SEEDS),
                candidate_cells=448, future_histories=1608, horizon=512,
                all_eight_cells_required_per_genotype=True,
                performance_selection=False, world_histories_executed=0,
                future_execution_requires_reviewed_registration=True,
                learning=False, stage_credit=False)


if __name__ == '__main__':
    print(json.dumps(contract(), sort_keys=True, separators=(',', ':')))
