"""Read-only contract diagnostics, separate from scientific acceptance.

No world execution, law modification, prices, sample selection or life claims.
The missing-role probes intentionally supply a prepared funded bank to isolate
apparatus guards; this is not a reachable natural history.
"""
import json

ROLES = ('C', 'H', 'F', 'S', 'L')


def fabrication_targets():
    from experiments.photofactory import Fixture
    result = {}
    for target in ROLES:
        f = Fixture('candidate', 1, True)
        f.epoch = 0
        f.bills.append(dict(formation=0, upkeep=0, release=0, work=0))
        f.photons[0] = f.emit('feed', [], [('p', 100)], engine=0)
        for role in ROLES:
            if role != target:
                f.form(0, role, 'photo')
                f.upkeep(0, role)
        # Deliberate prepared charge, even with capture apparatus absent.
        f.banks[0] = f.emit('capture', f.take(0, 4), [('c', 2), ('h', 2)], engine=0)
        try:
            f.form(0, target, 'fabricate')
        except ValueError as error:
            result[target] = dict(enabled=False, reason=str(error))
        else:
            result[target] = dict(enabled=True, reason=None)
    return result


def check_target_claim(claimed, observed):
    """Return unsupported targets, never convert guard checks into admission."""
    if len(claimed) != len(set(claimed)) or set(claimed) - set(observed):
        raise ValueError('Claimed roles must be unique observed targets')
    return sorted(role for role in claimed if not observed[role]['enabled'])


def fresh_token_opportunity(touched):
    """Necessary support for MAINTAIN's *first-use* post-loss endpoint.

    A positive count is not sufficient: retained function, accessibility, costs,
    and the full future trajectory must also satisfy the frozen endpoint.
    """
    if not isinstance(touched, (list, tuple)) or any(type(v) is not bool for v in touched):
        raise ValueError('Explicit boolean token ancestry required')
    remaining = sum(not value for value in touched)
    return dict(untouched=remaining, fresh_endpoint_possible=remaining > 0,
                sufficient_for_success=False)


def positive_endpoint_witness(record, evaluator):
    """Require the same evaluator as worlds; do not accept a separate score."""
    score = evaluator(record)
    if type(score) is not dict or type(score.get('success')) is not bool:
        raise ValueError('Evaluator must return an explicit boolean success')
    if not score['success']:
        raise ValueError('Prepared positive witness does not reach the endpoint')
    return score


def report():
    from experiments.association_channel import fixtures
    from experiments.association_channel_audit import audit_fixture
    targets = fabrication_targets()
    return dict(
        schema='code-reachability-preflight-v1', scientific_admission=False,
        natural_worlds=0, scope='Prepared guard diagnostics only',
        fabrication=dict(targets=targets,
            original_any_role_claim_unsupported=check_target_claim(ROLES, targets),
            corrected_SL_claim_unsupported=check_target_claim(('S', 'L'), targets)),
        association=audit_fixture(fixtures()),
        exhausted_first_use_endpoint=fresh_token_opportunity([True] * 10),
        limitations=['No full converter, maintenance or founder-free result',
                     'Zero fixture work is not a general impossibility theorem',
                     'Ancestry support is necessary, not sufficient',
                     'Frozen historical laws are unchanged'])


if __name__ == '__main__':
    print(json.dumps(report(), sort_keys=True, indent=2))
