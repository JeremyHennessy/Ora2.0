"""Offline post-READ delta adapter. No World import, loader, step or grant.

Input is a supplied truthful post-READ state without event history. Authentic
pre-READ replay and paid transition remain external qualification requirements.
Returned states are derived diagnostic data, never authentic original history.
"""
import hashlib
import json

SOURCE = 'cf22e109878bae6ac6b22e0563c8593f1c93e8ac03296a9ed9cd0cd43e1400de'
FIELDS = {'schema', 'source_sha256', 'original_world_id', 'actor', 'decoded',
          'original_state_sha256', 'original_read_receipt_sha256', 'branch_ids'}
ARMS = ('true', 'identity_sham', 'xor1')


def canonical(value):
    stack = [value]
    nodes = 0
    while stack:
        x = stack.pop(); nodes += 1
        if nodes > 100000:
            raise ValueError('offline node cap')
        if type(x) is dict:
            if any(type(k) is not str for k in x):
                raise ValueError('string JSON keys required')
            stack.extend(x.values())
        elif type(x) is list:
            stack.extend(x)
        elif x is not None and type(x) not in (str, int, bool):
            raise ValueError('plain finite JSON required')
    try:
        raw = json.dumps(value, sort_keys=True, separators=(',', ':'),
                         ensure_ascii=True, allow_nan=False).encode('ascii')
    except (RecursionError, ValueError) as exc:
        raise ValueError('invalid JSON tree') from exc
    if len(raw) > 2 * 1024**2:
        raise ValueError('offline byte cap')
    return raw


def digest(value):
    return hashlib.sha256(canonical(value)).hexdigest()


def sha(value):
    if type(value) is not str or len(value) != 64 or any(c not in '0123456789abcdef' for c in value):
        raise ValueError('exact SHA256 required')


def context(original, binding):
    if type(binding) is not dict or set(binding) != FIELDS:
        raise ValueError('exact binding fields required')
    if binding['schema'] != 'ORA-EKA1-OFFLINE-READ-BINDING-v1' or binding['source_sha256'] != SOURCE:
        raise ValueError('source or schema mismatch')
    sha(binding['original_state_sha256']); sha(binding['original_read_receipt_sha256'])
    if digest(original) != binding['original_state_sha256']:
        raise ValueError('original checkpoint bytes changed')
    if not isinstance(original, dict) or 'events' in original:
        raise ValueError('history-free state frame required; preserve original events separately')
    for key in ['original_world_id', 'actor']:
        if type(binding[key]) is not str or not binding[key] or len(binding[key]) > 128:
            raise ValueError('explicit bounded identity required')
    ids = binding['branch_ids']
    if (type(ids) is not dict or set(ids) != set(ARMS)
            or any(type(v) is not str or not v or len(v) > 128 for v in ids.values())
            or len(set(ids.values())) != 3 or binding['original_world_id'] in ids.values()):
        raise ValueError('three distinct proposed branch labels required')
    decoded = binding['decoded']
    if (type(decoded) is not list or len(decoded) != 3
            or any(type(x) is not int or not 0 <= x < 32 for x in decoded)
            or decoded[0] != 1):
        raise ValueError('feedback READ required')
    try:
        actor = original['entities'][binding['actor']]
        code, pc = actor['code'], actor['pc']
        reg, feedback = actor['registers'], actor['feedback']
        if (type(code) is not list or len(code) != 27
                or any(type(cell) is not list or len(cell) != 2
                       or any(type(v) is not int for v in cell)
                       or not 0 <= cell[0] < 32 for cell in code)
                or type(pc) is not int or not 0 <= pc < 9
                or type(reg) is not list or len(reg) != 2
                or any(type(v) is not int or not 0 <= v < 16 for v in reg)
                or type(feedback) is not int or feedback not in (0, 1)):
            raise ValueError('invalid local READ state')
        slot = (pc - 1) % 9
        if [cell[0] for cell in code[3*slot:3*slot+3]] != decoded:
            raise ValueError('decoded READ does not match preceding source slot')
        dest = decoded[1] % 2
        if reg[dest] != feedback:
            raise ValueError('baseline must contain truthful READ result')
    except (KeyError, TypeError) as exc:
        raise ValueError('missing checkpoint context') from exc
    return dest, feedback


def adapt(original, binding, arm):
    """Derive one destination delta in JSON only; does not execute the READ."""
    dest, feedback = context(original, binding)
    if arm not in ARMS:
        raise ValueError('unknown role')
    derived = json.loads(canonical(original))  # break Python container aliases
    value = feedback ^ int(arm == 'xor1')
    derived['entities'][binding['actor']]['registers'][dest] = value
    receipt = {'schema': 'ORA-EKA1-OFFLINE-DERIVED-READ-v1',
               'binding_sha256': digest(binding), 'original_state_sha256': digest(original),
               'derived_state_sha256': digest(derived), 'arm': arm,
               'actor': binding['actor'], 'destination': dest,
               'derived_branch_id': binding['branch_ids'][arm],
               'original_feedback': feedback, 'delivered_value': value,
               'structural_delta_checked': True,
               'authentic_original_history_verified': False,
               'ordinary_read_charge_verified': False,
               'derived_checkpoint_authority_granted': False,
               'execution_identity_verified': False,
               'execution_authorized': False}
    return derived, receipt


def verify(original, derived, binding, arm, receipt):
    expected, expected_receipt = adapt(original, binding, arm)
    if canonical(derived) != canonical(expected) or canonical(receipt) != canonical(expected_receipt):
        raise ValueError('undeclared delta or forged derived receipt')
    return expected_receipt
