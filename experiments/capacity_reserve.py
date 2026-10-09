"""CAPACITY-01 authored full-cost capacity assay; no natural-world installation."""
import argparse
import copy
import hashlib
import itertools
from pathlib import Path
from experiments import paid_dissociation as prior

ROOT = Path(__file__).resolve().parents[1]
MODES = prior.MODES
FILES = prior.FILES + ('docs/CAPACITY-01-PROTOCOL.md', 'experiments/capacity_reserve.py', 'experiments/capacity_reserve_audit.py')
encode = prior.encode
digest = prior.digest

def configs():
    for p in (4, 5, 6):
        for n in (2, 3, 4):
            for word in itertools.product('01', repeat=n):
                for budget, food, mode in itertools.product((0, 32), ('0', '1'), MODES):
                    yield dict(payer_size=p, word=''.join(word), budget=budget, food_bit=food, mode=mode)

def formation(size):
    actions = [(0, 0), (2, 0)]
    for atom in range(1, size): actions += [(0, atom), (3, atom), (0, atom)]
    return actions + [(4, 0)]

def select(s, c, op, atom, phase):
    size = c['payer_size']
    chains = sorted(s['chains'], key=lambda k: (-len(s['chains'][k]['atoms']), k))
    products = sorted([k for k, v in s['history'].items() if v['kind'] == 'product' and v['origin'] == 'assembly'], key=lambda k: s['history'][k]['born'])
    foundations = [k for k in products if set(s['history'][k]['atoms']) == set(f'M{i}' for i in range(size))]
    actor = foundations[0] if foundations else None
    target = set(f'M{i}' for i in range(size, size + len(c['word'])))
    if phase == 'post' and op == 5 and atom == size:
        matches = [k for k in products if target.issubset(s['history'][k]['atoms'])]
        actor = matches[-1] if matches else None
    food = sorted(s['food'], key=lambda a: int(a[1:]))[0] if s['food'] else 'F0'
    return dict(op=op, atom=f'M{atom}', food=food, chain=chains[0] if chains else None, actor=actor)

def initial(c):
    s, _ = prior.base.initial(0, 'active')
    for a in s['atoms']: s['atoms'][a]['bit'] = c['food_bit'] if a[0] == 'F' else '0'
    for i, bit in enumerate(c['word'], c['payer_size']): s['atoms'][f'M{i}']['bit'] = bit
    s['recycles'] = {f'M{i}': [] for i in range(24)}
    preparation = []; chain = digest(s)
    if c['mode'] == 'supplied':
        for i, (op, atom) in enumerate(formation(c['payer_size'])):
            t = i - 128; q = select(s, c, op, atom, 'preparation'); before = digest(s)
            result = prior.step(s, c, t, q)
            e = dict(tick=t, request=q, before=before, after=digest(s), previous=chain, result=result)
            e['sha256'] = digest(e); chain = e['sha256']; preparation.append(e)
    s['reserve_work'].extend(s['bank'][c['budget']:]); s['bank'] = s['bank'][:c['budget']]
    return s, preparation

def schedule(c):
    p = c['payer_size']; pre = [] if c['mode'] == 'supplied' else formation(p)
    pre += [(0, p), (2, p)]
    for a in range(p + 1, p + len(c['word'])): pre += [(0, a), (3, a)]
    post = [(5, 0)] * (p - 2) + [(6, p)]
    for a in range(p, p + len(c['word'])):
        post += [(5, 0), (5, 0), (0, a), (2 if a == p else 3, a)]
        if a != p: post += [(5, 0), (5, 0), (0, a)]
    post += [(4, p), (5, p)]
    return [(t, op, a, 'pre') for t, (op, a) in enumerate(pre)] + [(128 + t, op, a, 'post') for t, (op, a) in enumerate(post)]

def simulate(c):
    s, preparation = initial(c); start = copy.deepcopy(s); chain = digest(s); events = []
    for t, op, a, phase in schedule(c):
        q = select(s, c, op, a, phase); before = digest(s); result = prior.step(s, c, t, q)
        e = dict(tick=t, request=q, before=before, after=digest(s), previous=chain, result=result)
        e['sha256'] = digest(e); chain = e['sha256']; events.append(e)
    return dict(config=c, preparation=preparation, initial=start, events=events, terminal=s)

def metrics(r):
    s = r['terminal']; p = r['config']['payer_size']; target = {f'M{i}' for i in range(p, p + len(r['config']['word']))}
    cuts = {k: v for k, v in s['history'].items() if v['kind'] == 'dismantled'}
    products = {k: v for k, v in s['history'].items() if v['kind'] == 'product' and v['origin'] == 'assembly' and set(v['atoms']) == target}
    reused = set(); renewed = set(); fresh = set()
    for k, v in products.items():
        previous = [x for x in cuts.values() if x['returned'] and set(x['atoms']) == target and x['born'] < v['born']]
        if previous: reused.add(k)
        if v['fully_capture_funded'] and previous and all(s['units'][u]['origin'] == 'capture' for x in previous for u in x['work_debits']): renewed.add(k)
        if v['fully_capture_funded'] and all(not s['recycles'][a] for a in target): fresh.add(k)
    probes = {e['result']['actor'] for e in r['events'] if e['tick'] >= 128 and e['result']['outcome'] == 'captured'}
    payers = [v for v in s['history'].values() if v['kind'] == 'product' and set(v['atoms']) == {f'M{i}' for i in range(p)}]
    charges = [e for e in r['preparation'] + r['events'] if e['tick'] < 128 and e['request']['op'] < 2
               and int(e['request']['atom'][1:]) < p and e['result']['outcome'] == 'charged']
    return dict(cases=1, cuts=sum(v['returned'] for v in cuts.values()), inert_cuts=sum(not v['returned'] for v in cuts.values()),
                cut_work=sum(len(v['work_debits']) for v in cuts.values()), cut_bond_heat=sum(len(v['bond_debits']) for v in cuts.values()),
                cut_charge_heat=sum(len(v['charge_debits']) for v in cuts.values()), reused_release=int(bool(reused)),
                fully_capture_paid_release=int(bool(renewed)), fully_capture_paid_probe=int(bool(renewed & probes)),
                capture_paid_fresh_release=int(bool(fresh)), capture_paid_fresh_probe=int(bool(fresh & probes)),
                target_probe=int(bool(set(products) & probes)), payer_releases=len(payers),
                payer_external_work=sum(len(e['result']['spent']) for e in charges), payer_food=len(charges),
                payer_formation_debits=sum(len(v['debits']) for v in payers), final_heat=s['heat'], remaining_food=len(s['food']),
                waste=len(s['waste']), events=len(r['events']), preparation_events=len(r['preparation']))

def aggregate(records):
    totals = {}
    for r in records:
        c = r['config']; key = f"{c['mode']}/{c['payer_size']}/{len(c['word'])}/{c['budget']}/{c['food_bit']}"
        row = totals.setdefault(key, {})
        for k, v in metrics(r).items(): row[k] = row.get(k, 0) + v
    return totals

def run(output, revision):
    if len(revision) != 40 or any(x not in '0123456789abcdef' for x in revision): raise ValueError('Exact revision')
    output = Path(output); output.mkdir(parents=True, exist_ok=False); records = []; h = hashlib.sha256()
    with (output / 'records.jsonl').open('wb') as f:
        for c in configs():
            r = simulate(c); raw = (encode(r) + '\n').encode(); f.write(raw); h.update(raw); records.append(r)
    summary = dict(schema='capacity01-summary-v1', revision=revision, sources={f: hashlib.sha256((ROOT / f).read_bytes()).hexdigest() for f in FILES},
                   records_sha256=h.hexdigest(), cases=2688, events=sum(len(r['events']) for r in records),
                   preparation_events=sum(len(r['preparation']) for r in records), authored_feasibility_only=True, natural_worlds=0, totals=aggregate(records))
    (output / 'summary.json').write_bytes((encode(summary) + '\n').encode()); return summary

if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__); p.add_argument('--output-dir', required=True); p.add_argument('--source-revision', required=True)
    a = p.parse_args(); run(a.output_dir, a.source_revision)
