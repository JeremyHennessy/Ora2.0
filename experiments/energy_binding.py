"""ENERGY-01 authored paid binding/storage feasibility; no natural worlds."""
import argparse
import copy
from fractions import Fraction
import hashlib
import itertools
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FILES = ('docs/ENERGY-01-PROTOCOL.md', 'experiments/energy_binding.py', 'experiments/energy_binding_audit.py')
MODES = ('selective', 'nonspecific', 'yoked', 'ghost')


def canonical(v):
    return json.dumps(v, sort_keys=True, separators=(',', ':'))


def digest(v):
    return hashlib.sha256(canonical(v).encode()).hexdigest()


def initial(bits, work, foods, capacity, storage):
    atoms = {f'B{i}': dict(bit=b, origin='supplied_body') for i, b in enumerate(bits)}
    atoms.update({f'N{i}': dict(bit=str(b), origin='supplied_food') for i, b in enumerate(foods)})
    tokens = [dict(unit=f'G{i}', origin='genesis', actor='C', nutrient=None, tick=-1) for i in range(work)]
    return dict(bits=bits, body=[f'B{i}' for i in range(len(bits))], live=True, atoms=atoms,
                food=[f'N{i}' for i in range(len(foods))], bound=None, ready=[], waste=[], tokens=tokens,
                capacity=capacity, storage=storage, heat=0,
                history=dict(birth=dict(actor='C', body=[f'B{i}' for i in range(len(bits))], tokens=copy.deepcopy(tokens)), captures=[], reclaims=[]))


def transition(old, mode, tick, request):
    s = copy.deepcopy(old)
    action, target = request
    r = dict(outcome='unavailable', spent=[], returned=[], stored=[], overflow=[], discarded=[], charged=0, heat=0, reclaimer=None)
    def spend(n):
        taken = s['tokens'][:n]
        del s['tokens'][:n]
        r['spent'].extend(taken)
        r['charged'] += len(taken)
        return len(taken)
    def heat(n):
        s['heat'] += n
        r['heat'] += n
    if action == 'recognize' and s['live'] and s['bound'] is None and target in s['food']:
        if spend(1):
            match = s['bits'][-1] != s['atoms'][target]['bit']
            if match or mode == 'nonspecific':
                s['food'].remove(target)
                s['bound'] = target
                r['outcome'] = 'bound'
            else:
                heat(1)
                if mode == 'yoked':
                    heat(spend(1))
                r['outcome'] = 'rejected'
        else:
            r['outcome'] = 'starved'
    elif action == 'process' and s['live'] and s['bound'] is not None:
        if spend(1):
            nutrient = s['bound']
            s['bound'] = None
            if s['bits'][-1] != s['atoms'][nutrient]['bit']:
                s['waste'].append(nutrient)
                if mode == 'ghost':
                    heat(10)
                    r['outcome'] = 'ghost_consumed'
                else:
                    made = [dict(unit=f'{nutrient}:{tick}:{i}', origin='capture', actor='C', nutrient=nutrient, tick=tick) for i in range(3)]
                    slots = 3 if s['capacity'] is None else max(0, s['capacity']-len(s['tokens']))
                    stored, overflow = made[:slots], made[slots:]
                    s['tokens'].extend(stored)
                    heat(7+len(overflow))
                    s['history']['captures'].append(dict(nutrient=nutrient, tick=tick, actor='C', returned=made, stored=stored, overflow=overflow))
                    r.update(outcome='captured', returned=made, stored=stored, overflow=overflow)
            else:
                s['food'].append(nutrient)
                heat(2)
                r['outcome'] = 'processed_rejection'
        else:
            r['outcome'] = 'bound_starved'
    elif action == 'release' and s['bound'] is not None:
        s['food'].append(s['bound'])
        s['bound'] = None
        heat(1)
        r['outcome'] = 'released'
    elif action == 'decay' and s['live']:
        s['live'] = False
        s['waste'].extend(s['body'])
        heat(len(s['body'])-1)
        if s['bound'] is not None:
            s['food'].append(s['bound'])
            s['bound'] = None
            heat(1)
        if s['storage'] == 'local':
            r['discarded'] = list(s['tokens'])
            heat(len(s['tokens']))
            s['tokens'] = []
        r['outcome'] = 'decayed'
    elif action == 'reclaim' and target in s['waste'] and (s['live'] or s['storage'] == 'protected'):
        if spend(1):
            heat(1)
            s['waste'].remove(target)
            s['ready'].append(target)
            actor = 'C' if s['live'] else 'engine_bank'
            s['history']['reclaims'].append(dict(atom=target, tick=tick, actor=actor))
            r.update(outcome='reclaimed', reclaimer=actor)
        else:
            r['outcome'] = 'starved'
    return s, r


def recipes():
    for n in (2, 3, 4):
        for pattern in itertools.product('01', repeat=n):
            bits = ''.join(pattern)
            for work in range(n+1):
                for bit, mode, capacity in itertools.product((0, 1), MODES, (n, None)):
                    yield dict(kind='single', bits=bits, work=work, foods=[bit], mode=mode, capacity=capacity, storage='local'), [('recognize', 'N0'), ('process', None)]
            for mode, capacity in itertools.product(MODES, (n, None)):
                requests = [r for i in range(4) for r in (('recognize', f'N{i}'), ('process', None), ('release', None))]
                yield dict(kind='balanced', bits=bits, work=2, foods=[0, 1, 0, 1], mode=mode, capacity=capacity, storage='local'), requests
            for work, mode, capacity, storage, stage in itertools.product(range(n+1), ('selective', 'ghost'), (n, None), ('local', 'protected'), ('before', 'after')):
                requests = [('recognize', 'N0'), ('decay', None), ('process', None), ('release', None)] if stage == 'before' else [('recognize', 'N0'), ('process', None), ('decay', None)]
                requests += [('reclaim', f'B{i}') for i in range(n)]+[('reclaim', 'N0')]
                yield dict(kind='retention-'+stage, bits=bits, work=work, foods=[1-int(bits[-1])], mode=mode, capacity=capacity, storage=storage), requests


def simulate(config, requests):
    s = initial(config['bits'], config['work'], config['foods'], config['capacity'], config['storage'])
    genesis = copy.deepcopy(s)
    events = []
    chain = digest(s)
    for tick, request in enumerate(requests):
        before = digest(s)
        s, result = transition(s, config['mode'], tick, request)
        e = dict(tick=tick, request=list(request), before=before, after=digest(s), previous=chain, result=result)
        e['sha256'] = digest(e)
        chain = e['sha256']
        events.append(e)
    return dict(config=config, initial=genesis, events=events, terminal=s)


def summarize(records, revision):
    totals = {}
    for record in records:
        c = record['config']
        key = '/'.join((c['kind'], c['mode'], 'finite' if c['capacity'] is not None else 'uncapped', c['storage']))
        row = totals.setdefault(key, dict(cases=0, captures=0, bound_starvations=0, ghost_consumptions=0, overflow=0, charged=0, reclaimed=0, external_reclaims=0, terminal_work=0))
        row['cases'] += 1
        row['terminal_work'] += len(record['terminal']['tokens'])
        for e in record['events']:
            r = e['result']
            row['captures'] += r['outcome'] == 'captured'
            row['bound_starvations'] += r['outcome'] == 'bound_starved'
            row['ghost_consumptions'] += r['outcome'] == 'ghost_consumed'
            row['overflow'] += len(r['overflow'])
            row['charged'] += r['charged']
            row['reclaimed'] += r['outcome'] == 'reclaimed'
            row['external_reclaims'] += r['reclaimer'] == 'engine_bank'
    drift = []
    for mode in MODES:
        for p in map(Fraction, ('0', '1/4', '1/2', '3/4', '1')):
            d = 2*p-1 if mode == 'selective' else 3*p-2 if mode in ('nonspecific', 'yoked') else -1-p
            drift.append(dict(mode=mode, matching_fraction=str(p), uncapped_funded_drift=str(d)))
    return dict(schema='energy01-summary-v1', revision=revision, source_sha256={p: hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in FILES},
                authored_cases=len(records), events=sum(len(r['events']) for r in records), independent_natural_worlds=0,
                totals=totals, analytic_drift=drift, capacity_bounds=[dict(length=n, capacity=n, unchanged_copy_debit=3*n+1, sufficient=False) for n in (2, 3, 4)],
                decision='capture_feasibility_only_no_reproduction_pilot', no_emergence_claim=True)


def run(output, revision):
    if len(revision) != 40 or any(c not in '0123456789abcdef' for c in revision):
        raise ValueError('Exact revision required')
    output = Path(output)
    output.mkdir(parents=True, exist_ok=False)
    records = [simulate(c, requests) for c, requests in recipes()]
    raw = ''.join(canonical(r)+'\n' for r in records).encode()
    (output/'records.jsonl').write_bytes(raw)
    result = summarize(records, revision)
    result['records_sha256'] = hashlib.sha256(raw).hexdigest()
    (output/'summary.json').write_bytes((canonical(result)+'\n').encode())


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output-dir', required=True)
    parser.add_argument('--source-revision', required=True)
    args = parser.parse_args()
    run(args.output_dir, args.source_revision)
