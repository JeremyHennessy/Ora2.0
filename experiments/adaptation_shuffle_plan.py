"""Design-only past-reference permutations; no actor or memory edit is executed."""
import hashlib
import json

FIELDS = {'id', 'event_step', 'observed_step', 'cue', 'action', 'outcome'}
LIMIT = 4096


def natural(value, maximum=None):
    if type(value) is not int or value < 0 or (maximum is not None and value > maximum):
        raise ValueError('Expected bounded nonnegative integer')
    return value


def source_digest(records):
    return hashlib.sha256(json.dumps(records, sort_keys=True, separators=(',', ':'),
                                    ensure_ascii=True).encode('ascii')).hexdigest()


def validate(records):
    if type(records) is not list or len(records) > LIMIT:
        raise ValueError('Bounded source list required')
    names = set()
    previous = -1
    for record in records:
        if type(record) is not dict or set(record) != FIELDS:
            raise ValueError('Exact evaluator-record schema required')
        for field in ('id', 'cue', 'action', 'outcome'):
            if type(record[field]) is not str or not 1 <= len(record[field]) <= 128:
                raise ValueError('Bounded string required')
        if record['id'] in names:
            raise ValueError('Duplicate source identity')
        names.add(record['id'])
        event = natural(record['event_step'])
        if event < previous:
            raise ValueError('World chronology changed')
        previous = event
        observed = record['observed_step']
        if observed is not None and natural(observed) < event:
            raise ValueError('Observation precedes its event')


def indices(count, seed):
    """SHA256 counter draws and unbiased Fisher-Yates, including fixed points."""
    permutation = list(range(count))
    counter = 0
    prefix = b'ora-adaptation-reference-plan-v1\0' + seed.to_bytes(8, 'big')
    for end in range(count - 1, 0, -1):
        size = end + 1
        ceiling = 2**64 - (2**64 % size)
        while True:
            draw = int.from_bytes(hashlib.sha256(prefix + counter.to_bytes(8, 'big')).digest()[:8], 'big')
            counter += 1
            if draw < ceiling:
                break
        index = draw % size
        permutation[end], permutation[index] = permutation[index], permutation[end]
    return permutation


def plan(records, kind, cutoff, window, seed):
    """Only evaluator references are returned. This is not an actor-input adapter."""
    validate(records)
    natural(cutoff)
    if natural(window, LIMIT) == 0:
        raise ValueError('Positive observation window required')
    natural(seed, 2**64 - 1)
    if kind not in ('order', 'association') or type(kind) is not str:
        raise ValueError('Unknown intervention kind')
    eligible = sorted((r for r in records if r['observed_step'] is not None
                       and r['observed_step'] < cutoff), key=lambda r: (r['observed_step'], r['id']))[-window:]
    names = [r['id'] for r in eligible]
    donors = [names[i] for i in indices(len(names), seed)]
    return dict(schema='adaptation-reference-plan-v1', kind=kind, cutoff=cutoff,
                window=window, seed=seed, source_sha256=source_digest(records),
                eligible_ids=names, donor_ids=donors,
                planned_reference_reads=len(names), planned_reference_writes=len(names),
                physical_cost='UNKNOWN', design_only=True)
