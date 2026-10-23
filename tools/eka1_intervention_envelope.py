"""Offline delta checker for synthetic fixtures. Not a World loader or admission gate.

No history authentication, replay, intervention, pricing or execution is provided.
All input objects remain untouched; a passing envelope never qualifies learning.
"""
import hashlib
import json


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'),
                                    allow_nan=False).encode()).hexdigest()


def validate_delta(before, after, *, actor, cell, value, arm):
    """Check exactly one private-cell delta; all other JSON state must be equal.

    String actor keys are the canonical JSON representation, not a runtime API.
    This checks data structure custody only, not valid source history or biology.
    """
    if type(actor) is not str or type(cell) is not int or not 0 <= cell < 8:
        raise ValueError('invalid address')
    if type(value) is not int or not 0 <= value < 16:
        raise ValueError('invalid replacement')
    if arm not in ('intact', 'sham', 'single_cell_lesion'):
        raise ValueError('unknown arm')
    try:
        memory = before['entities'][actor]['memory']
    except (TypeError, KeyError) as exc:
        raise ValueError('missing actor memory') from exc
    if (type(memory) is not list or len(memory) != 8
            or any(type(v) is not int or not 0 <= v < 16 for v in memory)):
        raise ValueError('invalid memory shape')
    old = memory[cell]
    if (arm == 'single_cell_lesion') != (old != value):
        raise ValueError('lesion must change value; intact/sham must preserve it')
    # JSON has no shared-container aliases. Break Python aliases before applying
    # the declared delta so a second actor cannot change through the same list.
    expected = json.loads(json.dumps(before, allow_nan=False))
    expected['entities'][actor]['memory'][cell] = value
    # Hash canonical JSON as well as equality: bool/int substitutions must fail.
    if expected != after or digest(expected) != digest(after):
        raise ValueError('undeclared collateral delta')
    return {'schema': 'ORA-EKA1-OFFLINE-DELTA-v1', 'arm': arm,
            'before_sha256': digest(before), 'after_sha256': digest(after),
            'actor': actor, 'cell': cell, 'old': old, 'replacement': value,
            'structural_delta_valid': True, 'history_authenticated': False,
            'pricing_qualified': False, 'nonlethality_qualified': False,
            'causal_assay_qualified': False, 'execution_authorized': False}
