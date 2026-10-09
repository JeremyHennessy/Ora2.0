"""CONTACT-01 finite authored contact challenges; no natural-world generator."""
import argparse
import copy
import hashlib
import itertools
import json
from pathlib import Path
from experiments import precursor_coupling as core

ROOT = Path(__file__).resolve().parents[1]
FILES = ('docs/CONTACT-01-PROTOCOL.md', 'docs/CONTACT-01-COUNT-ADDENDUM.md', 'experiments/contact_loss.py',
         'experiments/contact_loss_audit.py', 'docs/ENERGY-02-PROTOCOL.md',
         'experiments/precursor_coupling.py', 'experiments/precursor_coupling_audit.py')


def orders(bits):
    representatives = {}
    for indices in itertools.permutations(range(len(bits))):
        word = ''.join(bits[i] for i in indices)
        representatives.setdefault(word, list(indices))
    return [representatives[word] for word in sorted(representatives)]


def configs():
    for n in (2, 3, 4):
        for pattern in itertools.product('01', repeat=n):
            bits = ''.join(pattern)
            for order in orders(bits):
                for mode, source, contacts, food, loss, founder in itertools.product(
                        core.MODES, ('producer', 'external'), ('free', 'paid'),
                        ('compatible', 'mixed'), (0, 1), ('present', 'removed')):
                    yield dict(kind='contact', bits=bits, candidate=bits, budget=n, fuel=2*n,
                               phases=1, mode=mode, source=source, order=order, contacts=contacts,
                               food=food, loss=loss, founder=founder)


def requests(c):
    n = len(c['bits'])
    for i, index in enumerate(c['order']):
        yield ['harvest', 'C', f'F0.{2*i}', None]
        yield ['harvest', 'C', f'F0.{2*i+1}', None]
        yield ['activate', 'C', f'M0.{index}', f'A0.{i}']
    yield ['loss', None, None, None]
    for _ in range(n):
        for index in c['order']:
            yield ['recognize', 'C', f'M0.{index}', None]
            yield ['ligate', 'C', None, None]
    yield ['release', 'C', 'D0', None]
    yield ['probe', 'D0', 'P0', None]


def initial(c):
    s = core.initial(c)
    if c['food'] == 'mixed':
        for i in range(len(c['bits'])):
            s['atoms'][f'F0.{2*i+1}']['bit'] = c['bits'][-1]
    if c['founder'] == 'removed':
        founder = s['objects'].pop('C')
        s['ready'].extend(founder['atoms'])
        s['heat'] += founder['supplied_bonds']
        s['environment']['protected_founder_work'] = founder['work']
        s['channels'].pop('C')
    return s


def step(old, c, tick, request):
    action, actor, target, donor = request
    if action == 'loss':
        s = copy.deepcopy(old)
        result = dict(outcome='loss_round', spent=[], returned=[], endowed=[], overflow=[],
                      bond=None, heat=0, product=None, producer_funded=False, matching=None)
        lost = []
        if c['loss']:
            for index in range(len(c['bits'])):
                potential = s['activation'][f'M0.{index}']
                if potential:
                    lost.append(potential.pop(0))
        s['heat'] += len(lost)
        result['heat'] = len(lost)
        result.update(failed_contact=False, failed_debit=[], lost_activation=lost)
        return s, result
    s, result = core.step(old, c, tick, request)
    result.update(failed_contact=False, failed_debit=[], lost_activation=[])
    if action in ('harvest', 'probe', 'activate') and result['outcome'] not in ('captured', 'activated'):
        food = donor if action == 'activate' else target
        external = action == 'activate' and c['source'] == 'external'
        obj = s['objects'].get(actor)
        possible = food in s['food'] and (external or obj is not None)
        if action == 'activate':
            possible = possible and target in s['ready'] and not s['activation'][target]
        if possible:
            result['failed_contact'] = True
            if result['outcome'] == 'unavailable':
                result['outcome'] = 'nonmatching_contact'
            if c['contacts'] == 'paid':
                pool = s['environment']['0'] if external else obj['work']
                used = pool[:2]
                del pool[:2]
                result['spent'].extend(used)
                result['failed_debit'] = used
                result['heat'] += len(used)
                s['heat'] += len(used)
    return s, result


def simulate(c):
    s = initial(c)
    genesis = copy.deepcopy(s)
    chain, events = core.digest(s), []
    for tick, request in enumerate(requests(c)):
        before = core.digest(s)
        s, result = step(s, c, tick, request)
        event = dict(tick=tick, request=request, before=before, after=core.digest(s), previous=chain, result=result)
        event['sha256'] = core.digest(event)
        chain = event['sha256']
        events.append(event)
    return dict(config=c, initial=genesis, events=events, terminal=s)


def counts(record):
    result = core.counts(record)
    result.update(failed_food_contacts=sum(e['result']['failed_contact'] for e in record['events']),
                  failed_work_lost=sum(len(e['result']['failed_debit']) for e in record['events']),
                  activation_units_lost=sum(len(e['result']['lost_activation']) for e in record['events']))
    return result


def key(c):
    word = ''.join(c['bits'][i] for i in c['order'])
    return '/'.join(map(str, (len(c['bits']), c['mode'], c['source'], c['contacts'],
                              c['food'], c['loss'], c['founder'], 'ordered' if word == c['bits'] else 'reordered')))


def challenged(c):
    return (c['mode'] == 'coupled' and c['source'] == 'producer' and c['contacts'] == 'paid'
            and c['food'] == 'mixed' and c['loss'] == 1 and c['founder'] == 'present')


def source_hashes():
    return {p: hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in FILES}


def run(output, revision):
    if len(revision) != 40 or any(ch not in '0123456789abcdef' for ch in revision):
        raise ValueError('Exact source revision required')
    output = Path(output)
    output.mkdir(parents=True, exist_ok=False)
    groups, checksum, cases, events, robust = {}, hashlib.sha256(), 0, 0, 0
    with (output/'records.jsonl').open('wb') as stream:
        for config in configs():
            record = simulate(config)
            raw = (core.encode(record)+'\n').encode()
            stream.write(raw)
            checksum.update(raw)
            stats = counts(record)
            row = groups.setdefault(key(config), {k: 0 for k in stats})
            for k, v in stats.items():
                row[k] += v
            if challenged(config):
                robust += stats['producer_funded_functional']
            cases += 1
            events += len(record['events'])
    summary = dict(schema='contact01-summary-v1', revision=revision, source_sha256=source_hashes(),
                   records_sha256=checksum.hexdigest(), authored_cases=cases, events=events, groups=groups,
                   robust_producer_funded_matching_functional=robust,
                   decision='possibility_survives_registered_challenge' if robust else 'fragile_under_registered_combined_challenge',
                   natural_worlds=0, reserved_samples_executed=False, founder_ablation_is_not_origin_test=True,
                   no_emergence_claim=True)
    (output/'summary.json').write_bytes((core.encode(summary)+'\n').encode())


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output-dir', required=True)
    parser.add_argument('--source-revision', required=True)
    args = parser.parse_args()
    run(args.output_dir, args.source_revision)
