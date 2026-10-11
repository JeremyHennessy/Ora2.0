"""Separate design-plan interpreter. Does not import the producer or any actor."""
from collections import Counter
from hashlib import sha256
import json


def unique(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError('Duplicate JSON key')
        result[key] = value
    return result


def audit(records, proposed):
    keys = {'schema', 'kind', 'cutoff', 'window', 'seed', 'source_sha256',
            'eligible_ids', 'donor_ids', 'planned_reference_reads',
            'planned_reference_writes', 'physical_cost', 'design_only'}
    if type(proposed) is not dict or set(proposed) != keys:
        raise ValueError('Unexpected plan fields')
    if (proposed['schema'] != 'adaptation-reference-plan-v1'
            or type(proposed['schema']) is not str or proposed['design_only'] is not True
            or proposed['physical_cost'] != 'UNKNOWN' or type(proposed['physical_cost']) is not str
            or type(proposed['kind']) is not str or proposed['kind'] not in ('order', 'association')):
        raise ValueError('Scope or cost claim changed')
    for key, lower, upper in [('cutoff', 0, None), ('window', 1, 4096), ('seed', 0, 2**64-1),
                              ('planned_reference_reads', 0, 4096), ('planned_reference_writes', 0, 4096)]:
        value = proposed[key]
        if type(value) is not int or value < lower or (upper is not None and value > upper):
            raise ValueError('Invalid integer field')
    if type(records) is not list or len(records) > 4096:
        raise ValueError('Source bound')
    by_id = {}
    time = -1
    for r in records:
        if type(r) is not dict or set(r) != {'id', 'event_step', 'observed_step', 'cue', 'action', 'outcome'}:
            raise ValueError('Source schema')
        if any(type(r[k]) is not str or not 1 <= len(r[k]) <= 128 for k in ('id', 'cue', 'action', 'outcome')):
            raise ValueError('Source strings')
        if r['id'] in by_id or type(r['event_step']) is not int or r['event_step'] < time or r['event_step'] < 0:
            raise ValueError('Source chronology or identity')
        seen = r['observed_step']
        if seen is not None and (type(seen) is not int or seen < r['event_step']):
            raise ValueError('Source observation')
        time = r['event_step']
        by_id[r['id']] = r
    digest = sha256(json.dumps(records, sort_keys=True, separators=(',', ':'), ensure_ascii=True).encode('ascii')).hexdigest()
    if type(proposed['source_sha256']) is not str or proposed['source_sha256'] != digest:
        raise ValueError('World source changed')
    past = [r['id'] for r in sorted(records, key=lambda r: (r['observed_step'] if r['observed_step'] is not None else -1, r['id']))
            if r['observed_step'] is not None and r['observed_step'] < proposed['cutoff']][-proposed['window']:]
    order = list(past)
    position = len(order) - 1
    serial = 0
    while position > 0:
        modulus = position + 1
        maximum = (2**64 // modulus) * modulus
        while True:
            material = (b'ora-adaptation-reference-plan-v1\0' + proposed['seed'].to_bytes(8, 'big')
                        + serial.to_bytes(8, 'big'))
            value = int(sha256(material).hexdigest()[:16], 16)
            serial += 1
            if value < maximum:
                break
        partner = value % modulus
        order[position], order[partner] = order[partner], order[position]
        position -= 1
    if (type(proposed['eligible_ids']) is not list or type(proposed['donor_ids']) is not list
            or proposed['eligible_ids'] != past or proposed['donor_ids'] != order
            or proposed['planned_reference_reads'] != len(past) or proposed['planned_reference_writes'] != len(past)):
        raise ValueError('Invalid donor or operation plan')
    original_pairs = Counter((by_id[n]['cue'], by_id[n]['action'], by_id[n]['outcome']) for n in past)
    if proposed['kind'] == 'order':
        altered = Counter((by_id[n]['cue'], by_id[n]['action'], by_id[n]['outcome']) for n in order)
    else:
        altered = Counter((by_id[n]['cue'], by_id[n]['action'], by_id[d]['outcome']) for n, d in zip(past, order))
    return dict(verified=True, design_only=True, observations=len(past),
                fixed_points=sum(a == b for a, b in zip(past, order)),
                association_multiset_preserved=original_pairs == altered,
                new_worlds=0, physical_cost='UNKNOWN', controller_activated=False)
