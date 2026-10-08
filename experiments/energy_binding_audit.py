"""Independent ENERGY-01 interpreter and read-only source-bound audit."""
import argparse
from collections import Counter
import copy
from fractions import Fraction
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FILES = ('docs/ENERGY-01-PROTOCOL.md', 'experiments/energy_binding.py', 'experiments/energy_binding_audit.py')
MODES = ('selective', 'nonspecific', 'yoked', 'ghost')


def canonical(v):
    return json.dumps(v, sort_keys=True, separators=(',', ':'))


def sha(v):
    return hashlib.sha256(canonical(v).encode()).hexdigest()


def unique(pairs):
    d = {}
    for k, v in pairs:
        if k in d:
            raise ValueError('Duplicate key')
        d[k] = v
    return d


def genesis(c):
    bodies = ['B'+str(i) for i in range(len(c['bits']))]
    nutrients = ['N'+str(i) for i in range(len(c['foods']))]
    atoms = {}
    for i, aid in enumerate(bodies):
        atoms[aid] = {'bit': c['bits'][i], 'origin': 'supplied_body'}
    for i, aid in enumerate(nutrients):
        atoms[aid] = {'bit': str(c['foods'][i]), 'origin': 'supplied_food'}
    tokens = [{'unit': 'G'+str(i), 'origin': 'genesis', 'actor': 'C', 'nutrient': None, 'tick': -1} for i in range(c['work'])]
    return {'bits': c['bits'], 'body': bodies, 'live': True, 'atoms': atoms, 'food': nutrients, 'bound': None,
            'ready': [], 'waste': [], 'tokens': tokens, 'capacity': c['capacity'], 'storage': c['storage'], 'heat': 0,
            'history': {'birth': {'actor': 'C', 'body': list(bodies), 'tokens': copy.deepcopy(tokens)}, 'captures': [], 'reclaims': []}}


def ledger(s):
    owners = (s['body'] if s['live'] else [])+s['food']+([] if s['bound'] is None else [s['bound']])+s['ready']+s['waste']
    if len(set(owners)) != len(owners) or set(owners) != set(s['atoms']):
        raise ValueError('Unique material ownership')
    if len({w['unit'] for w in s['tokens']}) != len(s['tokens']) or s['capacity'] is not None and len(s['tokens']) > s['capacity']:
        raise ValueError('Unique work ownership/capacity')
    if not s['live'] and s['storage'] == 'local' and s['tokens'] or type(s['heat']) is not int or s['heat'] < 0:
        raise ValueError('Unaccounted retained work/heat')
    for token in s['tokens']:
        if set(token) != {'unit', 'origin', 'actor', 'nutrient', 'tick'} or token['actor'] != 'C' or token['origin'] not in ('genesis', 'capture'):
            raise ValueError('Work provenance')
    bits = tuple(sorted(Counter(s['atoms'][a]['bit'] for a in owners).items()))
    potential = 8*(len(s['food'])+int(s['bound'] is not None))
    total = len(s['tokens'])+s['heat']+potential+(len(s['body'])-1 if s['live'] else 0)+int(s['bound'] is not None)
    return bits, total


def advance(old, mode, tick, request):
    s = copy.deepcopy(old)
    action, target = request
    r = {'outcome': 'unavailable', 'spent': [], 'returned': [], 'stored': [], 'overflow': [], 'discarded': [], 'charged': 0, 'heat': 0, 'reclaimer': None}
    account = s['tokens']
    def debit(count):
        used = min(count, len(account))
        for _ in range(used):
            r['spent'].append(account.pop(0))
        r['charged'] += used
        return used
    def dissipate(amount):
        r['heat'] += amount
        s['heat'] += amount
    if action == 'recognize':
        if s['live'] and s['bound'] is None and target in s['food']:
            if not debit(1):
                r['outcome'] = 'starved'
            elif mode == 'nonspecific' or int(s['bits'][-1])+int(s['atoms'][target]['bit']) == 1:
                s['bound'] = target
                s['food'].remove(target)
                r['outcome'] = 'bound'
            else:
                dissipate(1+debit(1) if mode == 'yoked' else 1)
                r['outcome'] = 'rejected'
    elif action == 'process':
        if s['live'] and s['bound'] is not None:
            nutrient = s['bound']
            if not debit(1):
                r['outcome'] = 'bound_starved'
            else:
                s['bound'] = None
                complementary = int(s['bits'][-1])+int(s['atoms'][nutrient]['bit']) == 1
                if not complementary:
                    s['food'].append(nutrient)
                    dissipate(2)
                    r['outcome'] = 'processed_rejection'
                else:
                    s['waste'].append(nutrient)
                    if mode == 'ghost':
                        dissipate(10)
                        r['outcome'] = 'ghost_consumed'
                    else:
                        r['outcome'] = 'captured'
                        for i in range(3):
                            unit = {'unit': f'{nutrient}:{tick}:{i}', 'origin': 'capture', 'actor': 'C', 'nutrient': nutrient, 'tick': tick}
                            r['returned'].append(unit)
                            if s['capacity'] is None or len(account) < s['capacity']:
                                account.append(unit)
                                r['stored'].append(unit)
                            else:
                                r['overflow'].append(unit)
                        dissipate(7+len(r['overflow']))
                        s['history']['captures'].append({'nutrient': nutrient, 'tick': tick, 'actor': 'C', 'returned': list(r['returned']), 'stored': list(r['stored']), 'overflow': list(r['overflow'])})
    elif action == 'release':
        if s['bound'] is not None:
            s['food'].append(s['bound'])
            s['bound'] = None
            dissipate(1)
            r['outcome'] = 'released'
    elif action == 'decay':
        if s['live']:
            dissipate(len(s['body'])-1)
            s['waste'] += s['body']
            s['live'] = False
            if s['bound'] is not None:
                s['food'].append(s['bound'])
                s['bound'] = None
                dissipate(1)
            if s['storage'] == 'local':
                r['discarded'] = list(account)
                dissipate(len(account))
                account.clear()
            r['outcome'] = 'decayed'
    elif action == 'reclaim':
        if target in s['waste'] and (s['live'] or s['storage'] == 'protected'):
            if not debit(1):
                r['outcome'] = 'starved'
            else:
                s['waste'].remove(target)
                s['ready'].append(target)
                dissipate(1)
                r['outcome'] = 'reclaimed'
                r['reclaimer'] = 'C' if s['live'] else 'engine_bank'
                s['history']['reclaims'].append({'atom': target, 'tick': tick, 'actor': r['reclaimer']})
    return s, r


def enumerate_cases():
    for n in range(2, 5):
        for number in range(2**n):
            bits = format(number, f'0{n}b')
            def c(kind, work, foods, mode, cap, store):
                return dict(kind=kind, bits=bits, work=work, foods=foods, mode=mode, capacity=cap, storage=store)
            for w in range(n+1):
                for food in (0, 1):
                    for mode in MODES:
                        for cap in (n, None):
                            yield c('single', w, [food], mode, cap, 'local'), [['recognize', 'N0'], ['process', None]]
            for mode in MODES:
                for cap in (n, None):
                    requests = []
                    for i in range(4):
                        requests.extend([['recognize', 'N'+str(i)], ['process', None], ['release', None]])
                    yield c('balanced', 2, [0, 1, 0, 1], mode, cap, 'local'), requests
            for w in range(n+1):
                for mode in ('selective', 'ghost'):
                    for cap in (n, None):
                        for store in ('local', 'protected'):
                            for stage in ('before', 'after'):
                                requests = [['recognize', 'N0']]
                                requests.extend([['decay', None], ['process', None], ['release', None]] if stage == 'before' else [['process', None], ['decay', None]])
                                requests.extend([['reclaim', 'B'+str(i)] for i in range(n)])
                                requests.append(['reclaim', 'N0'])
                                yield c('retention-'+stage, w, [int(bits[-1]) ^ 1], mode, cap, store), requests


def summarize(records, revision):
    totals = {}
    for item in records:
        c = item['config']
        key = '/'.join([c['kind'], c['mode'], 'uncapped' if c['capacity'] is None else 'finite', c['storage']])
        row = totals.setdefault(key, dict(cases=0, captures=0, bound_starvations=0, ghost_consumptions=0, overflow=0, charged=0, reclaimed=0, external_reclaims=0, terminal_work=0))
        row['cases'] += 1
        row['terminal_work'] += len(item['terminal']['tokens'])
        for e in item['events']:
            result = e['result']
            for name, outcome in [('captures', 'captured'), ('bound_starvations', 'bound_starved'), ('ghost_consumptions', 'ghost_consumed'), ('reclaimed', 'reclaimed')]:
                row[name] += int(result['outcome'] == outcome)
            row['overflow'] += len(result['overflow'])
            row['charged'] += len(result['spent'])
            row['external_reclaims'] += int(result['reclaimer'] == 'engine_bank')
    drift = []
    for mode in MODES:
        deltas = []
        for bit in (1, 0):
            c = dict(bits='00', work=2, foods=[bit], capacity=None, storage='local')
            s = genesis(c)
            for tick, request in enumerate([['recognize', 'N0'], ['process', None]]):
                s, _ = advance(s, mode, tick, request)
            deltas.append(len(s['tokens'])-2)
        for fraction in [Fraction(0), Fraction(1, 4), Fraction(1, 2), Fraction(3, 4), Fraction(1)]:
            drift.append(dict(mode=mode, matching_fraction=str(fraction), uncapped_funded_drift=str(fraction*deltas[0]+(1-fraction)*deltas[1])))
    return dict(schema='energy01-summary-v1', revision=revision, source_sha256={p: hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in FILES},
        authored_cases=len(records), events=sum(len(r['events']) for r in records), independent_natural_worlds=0, totals=totals, analytic_drift=drift,
        capacity_bounds=[dict(length=n, capacity=n, unchanged_copy_debit=3*n+1, sufficient=n >= 3*n+1) for n in (2, 3, 4)],
        decision='capture_feasibility_only_no_reproduction_pilot', no_emergence_claim=True)


def audit(output, revision):
    if not isinstance(revision, str) or len(revision) != 40 or any(c not in '0123456789abcdef' for c in revision):
        raise ValueError('Exact revision required')
    output = Path(output)
    with (output/'records.jsonl').open('rb') as stream:
        raw = stream.read(128*1024*1024+1)
    if len(raw) > 128*1024*1024 or not raw.endswith(b'\n'):
        raise ValueError('Bounded complete records')
    records = [json.loads(line, object_pairs_hook=unique) for line in raw.splitlines()]
    expected = list(enumerate_cases())
    if len(records) != 4192 or len(records) != len(expected):
        raise ValueError('All authored cases required')
    for record, (config, requests) in zip(records, expected):
        if set(record) != {'config', 'initial', 'events', 'terminal'} or canonical(record['config']) != canonical(config) or len(record['events']) != len(requests):
            raise ValueError('Case/configuration/denominator')
        s = genesis(config)
        if canonical(s) != canonical(record['initial']):
            raise ValueError('Supplied founder/source mismatch')
        total, chain = ledger(s), sha(s)
        for tick, request in enumerate(requests):
            before = sha(s)
            s, result = advance(s, config['mode'], tick, request)
            if ledger(s) != total:
                raise ValueError('Material/work/heat/binding conservation')
            event = dict(tick=tick, request=request, before=before, after=sha(s), previous=chain, result=result)
            event['sha256'] = sha(event)
            if canonical(record['events'][tick]) != canonical(event):
                raise ValueError('Binding/capture/cost/root/overflow divergence')
            chain = event['sha256']
        if canonical(s) != canonical(record['terminal']):
            raise ValueError('Terminal provenance divergence')
    summary = summarize(records, revision)
    summary['records_sha256'] = hashlib.sha256(raw).hexdigest()
    if canonical(json.loads((output/'summary.json').read_bytes(), object_pairs_hook=unique)) != canonical(summary):
        raise ValueError('Summary/source/drift/decision divergence')
    return dict(verified_revision=revision, authored_cases=4192, events=summary['events'], independent_natural_worlds=0,
                conservation_and_unique_provenance=True, capacity_and_exact_drift_verified=True,
                records_sha256=summary['records_sha256'], decision=summary['decision'], no_emergence_claim=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input-dir', required=True)
    parser.add_argument('--source-revision', required=True)
    args = parser.parse_args()
    print(json.dumps(audit(args.input_dir, args.source_revision), sort_keys=True, indent=2))
