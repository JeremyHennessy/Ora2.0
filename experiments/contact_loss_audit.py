"""Independent CONTACT-01 interpreter; imports neither experimental worker."""
import argparse
from copy import deepcopy
import hashlib
import itertools
import json
from pathlib import Path
from experiments import precursor_coupling_audit as core

ROOT = Path(__file__).resolve().parents[1]
FILES = ('docs/CONTACT-01-PROTOCOL.md', 'docs/CONTACT-01-COUNT-ADDENDUM.md', 'experiments/contact_loss.py',
         'experiments/contact_loss_audit.py', 'docs/ENERGY-02-PROTOCOL.md',
         'experiments/precursor_coupling.py', 'experiments/precursor_coupling_audit.py')


def orders(bits):
    words = sorted(set(''.join(bits[i] for i in ids) for ids in itertools.permutations(range(len(bits)))))
    return [list(min(ids for ids in itertools.permutations(range(len(bits))) if ''.join(bits[i] for i in ids) == word)) for word in words]


def panel():
    for n in range(2, 5):
        for pattern in itertools.product('01', repeat=n):
            bits = ''.join(pattern)
            for ids in orders(bits):
                for mode in ('coupled', 'uncoupled', 'ghost', 'untemplated'):
                    for source in ('producer', 'external'):
                        for price in ('free', 'paid'):
                            for food in ('compatible', 'mixed'):
                                for loss in (0, 1):
                                    for founder in ('present', 'removed'):
                                        yield dict(kind='contact', bits=bits, candidate=bits, budget=n, fuel=n*2,
                                                   phases=1, mode=mode, source=source, order=ids,
                                                   contacts=price, food=food, loss=loss, founder=founder)


def schedule(c):
    n, program = len(c['bits']), []
    for i in range(n):
        program += [['harvest', 'C', f'F0.{i*2}', None], ['harvest', 'C', f'F0.{i*2+1}', None],
                    ['activate', 'C', f'M0.{c["order"][i]}', f'A0.{i}']]
    program.append(['loss', None, None, None])
    for _ in range(n):
        for index in c['order']:
            program += [['recognize', 'C', f'M0.{index}', None], ['ligate', 'C', None, None]]
    return program+[['release', 'C', 'D0', None], ['probe', 'D0', 'P0', None]]


def genesis(c):
    s = core.genesis(c)
    old_balance = core.balance(s)
    if c['food'] == 'mixed':
        for i in range(1, len(c['bits'])*2, 2):
            s['atoms'][f'F0.{i}']['bit'] = c['bits'][-1]
    if c['founder'] == 'removed':
        supplied = s['objects']['C']
        s['environment']['protected_founder_work'] = list(supplied['work'])
        s['heat'] = supplied['supplied_bonds']
        for aid in supplied['atoms']:
            s['ready'].append(aid)
        del s['objects']['C']
        del s['channels']['C']
    # Food-profile changes alter bit composition deliberately, never energy total.
    core.need(core.balance(s)[1] == old_balance[1], 'Genesis energy subsidy')
    return s


def advance(old, c, tick, req):
    act, who, target, donor = req
    if act == 'loss':
        s = deepcopy(old)
        lost = []
        if c['loss'] == 1:
            for i in range(len(c['bits'])):
                units = s['activation'][f'M0.{i}']
                if len(units):
                    lost.append(units[0])
                    del units[0]
        s['heat'] += len(lost)
        result = dict(outcome='loss_round', spent=[], returned=[], endowed=[], overflow=[],
                      bond=None, heat=len(lost), product=None, producer_funded=False, matching=None,
                      failed_contact=False, failed_debit=[], lost_activation=lost)
        return s, result
    s, result = core.advance(old, c, tick, req)
    result['failed_contact'], result['failed_debit'], result['lost_activation'] = False, [], []
    if act not in ('harvest', 'probe', 'activate') or result['outcome'] in ('captured', 'activated'):
        return s, result
    food = donor if act == 'activate' else target
    environment = act == 'activate' and c['source'] == 'external'
    parent = s['objects'].get(who)
    available = food in s['food'] and (parent is not None or environment)
    if act == 'activate':
        available = available and target in s['ready'] and len(s['activation'][target]) == 0
    if available:
        result['failed_contact'] = True
        if result['outcome'] == 'unavailable':
            result['outcome'] = 'nonmatching_contact'
        if c['contacts'] == 'paid':
            account = s['environment']['0'] if environment else parent['work']
            for _ in range(min(2, len(account))):
                uid = account.pop(0)
                result['spent'].append(uid)
                result['failed_debit'].append(uid)
                result['heat'] += 1
                s['heat'] += 1
    return s, result


def verify_record(record, c):
    core.need(record['config'] == c, 'Registered configuration')
    s = genesis(c)
    core.need(record['initial'] == s, 'Genesis source, founder or food profile')
    conserved, chain = core.balance(s), core.sha(s)
    program = schedule(c)
    core.need(len(record['events']) == len(program), 'Complete contact history')
    for tick, (req, event) in enumerate(zip(program, record['events'])):
        before = core.sha(s)
        s, result = advance(s, c, tick, req)
        core.need(core.balance(s) == conserved, 'Mass/energy/ownership')
        predicted = dict(tick=tick, request=req, before=before, after=core.sha(s), previous=chain, result=result)
        predicted['sha256'] = core.sha(predicted)
        core.need(event == predicted, 'Semantic contact, loss, ancestry or event chain')
        chain = predicted['sha256']
    core.need(record['terminal'] == s, 'Terminal semantic state')
    born = [e['result'] for e in record['events'] if e['result']['product']]
    function = {e['request'][1] for e in record['events'] if e['request'][0] == 'probe' and e['result']['outcome'] == 'captured'}
    funded = {oid for oid in ('D0',) if oid in s['history'] and s['history'][oid]['origin'] == 'construction' and s['history'][oid]['matching'] and s['history'][oid]['producer_funded']}
    return dict(cases=1, constructions=sum(e['outcome'] == 'constructed' for e in born),
                ghosts=sum(e['outcome'] == 'ghost_constructed' for e in born),
                matching=sum(e['matching'] is True for e in born), probe_functions=len(function),
                matching_functional=sum(oid in function and s['history'][oid]['matching'] for oid in ('D0',) if oid in s['history']),
                producer_funded_functional=len(function & funded), renewed_functional=0,
                second_functional=0, second_producer_funded_functional=0,
                mismatches=sum(e['result']['outcome'] == 'mismatch' for e in record['events']),
                starved=sum(e['result']['outcome'] == 'starved' for e in record['events']),
                overflow=sum(len(e['result']['overflow']) for e in record['events']),
                external_activation=sum(cap['actor'].startswith('environment') and cap['carrier'] is not None for cap in s['captures']),
                terminal_heat=s['heat'], failed_food_contacts=sum(e['result']['failed_contact'] for e in record['events']),
                failed_work_lost=sum(len(e['result']['failed_debit']) for e in record['events']),
                activation_units_lost=sum(len(e['result']['lost_activation']) for e in record['events']))


def audit(directory, revision):
    core.need(len(revision) == 40 and all(c in '0123456789abcdef' for c in revision), 'Exact source revision')
    directory = Path(directory)
    summary = json.loads((directory/'summary.json').read_bytes(), object_pairs_hook=core.unique)
    groups, checksum, count, events, robust = {}, hashlib.sha256(), 0, 0, 0
    with (directory/'records.jsonl').open('rb') as stream:
        for c in panel():
            line = stream.readline()
            core.need(line, 'Missing registered case')
            checksum.update(line)
            record = json.loads(line, object_pairs_hook=core.unique)
            stats = verify_record(record, c)
            word = ''.join(c['bits'][i] for i in c['order'])
            label = '/'.join(map(str, (len(c['bits']), c['mode'], c['source'], c['contacts'], c['food'], c['loss'], c['founder'],
                                       'ordered' if word == c['bits'] else 'reordered')))
            row = groups.setdefault(label, {k: 0 for k in stats})
            for k, v in stats.items():
                row[k] += v
            if c['mode'] == 'coupled' and c['source'] == 'producer' and c['contacts'] == 'paid' and c['food'] == 'mixed' and c['loss'] == 1 and c['founder'] == 'present':
                robust += stats['producer_funded_functional']
            count += 1
            events += len(record['events'])
        core.need(not stream.read(1), 'Extra records')
    expected = dict(schema='contact01-summary-v1', revision=revision,
                    source_sha256={p: hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in FILES},
                    records_sha256=checksum.hexdigest(), authored_cases=count, events=events, groups=groups,
                    robust_producer_funded_matching_functional=robust,
                    decision='possibility_survives_registered_challenge' if robust else 'fragile_under_registered_combined_challenge',
                    natural_worlds=0, reserved_samples_executed=False, founder_ablation_is_not_origin_test=True, no_emergence_claim=True)
    core.need(summary == expected and count == 12288 and events == 510976, 'Complete independently reconstructed summary/source')
    return dict(schema='contact01-audit-v1', revision=revision, authored_cases=count, events=events,
                conservation_and_provenance=True, independent_full_event_replay=True, failed_contact_and_loss_prices_verified=True,
                robust_producer_funded_matching_functional=robust, records_sha256=checksum.hexdigest(),
                natural_worlds=0, founder_ablation_is_not_origin_test=True, no_emergence_claim=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input-dir', required=True)
    parser.add_argument('--source-revision', required=True)
    args = parser.parse_args()
    print(json.dumps(audit(args.input_dir, args.source_revision), sort_keys=True))
