"""Independent CAPACITY-01 manufacture/renewal interpreter; no worker imports."""
import argparse
import copy
import hashlib
import itertools
import json
from pathlib import Path
from experiments import paid_dissociation_audit as prior

ROOT = Path(__file__).resolve().parents[1]
MODES = ('candidate', 'irreversible', 'cut_ghost', 'product_ghost',
         'association_off', 'supplied', 'food_withdrawn', 'external')
FILES = prior.FILES + ('docs/CAPACITY-01-PROTOCOL.md',
                     'experiments/capacity_reserve.py',
                     'experiments/capacity_reserve_audit.py')

def configurations():
    return [dict(payer_size=p, word=''.join(bits), budget=b, food_bit=f, mode=m)
            for p in (4, 5, 6) for n in (2, 3, 4)
            for bits in itertools.product('01', repeat=n)
            for b in (0, 32) for f in ('0', '1') for m in MODES]

def formation(p):
    sequence = [(0, 0), (2, 0)]
    for i in range(1, p): sequence.extend(((0, i), (3, i), (0, i)))
    sequence.append((4, 0))
    return sequence

def request(s, c, op, atom, phase):
    size = c['payer_size']
    chain = min(s['chains'], key=lambda k: (-len(s['chains'][k]['atoms']), k)) if s['chains'] else None
    products = sorted((k for k, v in s['history'].items()
                       if v['kind'] == 'product' and v['origin'] == 'assembly'),
                      key=lambda k: s['history'][k]['born'])
    body = {f'M{i}' for i in range(size)}
    founders = [k for k in products if set(s['history'][k]['atoms']) == body]
    payer = founders[0] if founders else None
    if phase == 'post' and op == 5 and atom == size:
        target = {f'M{i}' for i in range(size, size + len(c['word']))}
        available = [k for k in products if target <= set(s['history'][k]['atoms'])]
        payer = available[-1] if available else None
    food = min(s['food'], key=lambda k: int(k[1:])) if s['food'] else 'F0'
    return dict(op=op, atom=f'M{atom}', food=food, chain=chain, actor=payer)

def genesis(c):
    s, _ = prior.old.genesis(dict(seed=0, mode='active'))
    for aid in s['atoms']: s['atoms'][aid]['bit'] = c['food_bit'] if aid[0] == 'F' else '0'
    for i, bit in enumerate(c['word'], c['payer_size']): s['atoms'][f'M{i}']['bit'] = bit
    s['recycles'] = {f'M{i}': [] for i in range(24)}
    prior.validate(s)
    preparation = []
    chain = prior.old.digest(s)
    if c['mode'] == 'supplied':
        for i, (op, atom) in enumerate(formation(c['payer_size'])):
            tick = i - 128
            q = request(s, c, op, atom, 'preparation')
            before = prior.old.digest(s)
            result = prior.transition(s, c, tick, q)
            prior.validate(s)
            event = dict(tick=tick, request=q, before=before, after=prior.old.digest(s), previous=chain, result=result)
            event['sha256'] = prior.old.digest(event)
            chain = event['sha256']; preparation.append(event)
    s['reserve_work'].extend(s['bank'][c['budget']:]); s['bank'] = s['bank'][:c['budget']]
    prior.validate(s)
    return s, preparation

def program(c):
    p = c['payer_size']
    early = [] if c['mode'] == 'supplied' else formation(p)
    early.extend(((0, p), (2, p)))
    for i in range(p + 1, p + len(c['word'])): early.extend(((0, i), (3, i)))
    later = [(5, 0)] * (p - 2) + [(6, p)]
    for i in range(p, p + len(c['word'])):
        later.extend(((5, 0), (5, 0), (0, i), (2 if i == p else 3, i)))
        if i > p: later.extend(((5, 0), (5, 0), (0, i)))
    later.extend(((4, p), (5, p)))
    actions = [(i, op, a, 'pre') for i, (op, a) in enumerate(early)]
    actions.extend((128 + i, op, a, 'post') for i, (op, a) in enumerate(later))
    assert len(actions) + (len(formation(p)) if c['mode'] == 'supplied' else 0) <= 80
    assert actions[-1][0] < 256
    return actions

def metrics(r):
    s = r['terminal']; c = r['config']; p = c['payer_size']
    target = {f'M{i}' for i in range(p, p + len(c['word']))}
    cuts = [v for v in s['history'].values() if v['kind'] == 'dismantled']
    products = {k: v for k, v in s['history'].items() if v['kind'] == 'product'
                and v['origin'] == 'assembly' and set(v['atoms']) == target}
    renewed = set(); reused = set(); fresh = set()
    for k, v in products.items():
        earlier = [cut for cut in cuts if cut['returned'] and set(cut['atoms']) == target and cut['born'] < v['born']]
        if earlier: reused.add(k)
        if v['fully_capture_funded']:
            if earlier and all(s['units'][u]['origin'] == 'capture' for cut in earlier for u in cut['work_debits']): renewed.add(k)
            if not any(s['recycles'][a] for a in target): fresh.add(k)
    probes = {e['result']['actor'] for e in r['events'] if e['tick'] >= 128 and e['result']['outcome'] == 'captured'}
    foundation = [v for v in s['history'].values() if v['kind'] == 'product'
                  and set(v['atoms']) == {f'M{i}' for i in range(p)}]
    charges = [e for e in r['preparation'] + r['events'] if e['tick'] < 128
               and e['request']['op'] < 2 and int(e['request']['atom'][1:]) < p
               and e['result']['outcome'] == 'charged']
    return dict(cases=1, cuts=sum(v['returned'] for v in cuts), inert_cuts=sum(not v['returned'] for v in cuts),
                cut_work=sum(len(v['work_debits']) for v in cuts), cut_bond_heat=sum(len(v['bond_debits']) for v in cuts),
                cut_charge_heat=sum(len(v['charge_debits']) for v in cuts), reused_release=int(bool(reused)),
                fully_capture_paid_release=int(bool(renewed)), fully_capture_paid_probe=int(bool(renewed & probes)),
                capture_paid_fresh_release=int(bool(fresh)), capture_paid_fresh_probe=int(bool(fresh & probes)),
                target_probe=int(bool(set(products) & probes)), payer_releases=len(foundation),
                payer_external_work=sum(len(e['result']['spent']) for e in charges), payer_food=len(charges),
                payer_formation_debits=sum(len(v['debits']) for v in foundation), final_heat=s['heat'],
                remaining_food=len(s['food']), waste=len(s['waste']), events=len(r['events']), preparation_events=len(r['preparation']))

def aggregate(records):
    totals = {}
    for r in records:
        c = r['config']; key = f"{c['mode']}/{c['payer_size']}/{len(c['word'])}/{c['budget']}/{c['food_bit']}"
        row = totals.setdefault(key, {})
        for k, v in metrics(r).items(): row[k] = row.get(k, 0) + v
    return totals

def verify_record(r, c):
    canonical = prior.old.canonical; digest = prior.old.digest
    if canonical(r['config']) != canonical(c): raise ValueError('Frozen capacity configuration')
    s, preparation = genesis(c)
    if canonical(r['preparation']) != canonical(preparation) or canonical(r['initial']) != canonical(s): raise ValueError('Manufacture/genesis')
    chain = digest(s)
    actions = program(c)
    if len(r['events']) != len(actions): raise ValueError('Frozen request count')
    for event, (tick, op, atom, phase) in zip(r['events'], actions):
        q = request(s, c, op, atom, phase); before = digest(s)
        result = prior.transition(s, c, tick, q); prior.validate(s)
        expected = dict(tick=tick, request=q, before=before, after=digest(s), previous=chain, result=result)
        expected['sha256'] = digest(expected)
        if canonical(event) != canonical(expected): raise ValueError('Capacity/ledger/provenance divergence')
        chain = expected['sha256']
    if canonical(r['terminal']) != canonical(s): raise ValueError('Terminal capacity/renewal')
    result = metrics(r)
    if c['payer_size'] < len(c['word']) + 3 and result['fully_capture_paid_probe']: raise ValueError('Necessary reserve bound violated')
    return result

def inspect(output, revision):
    output = Path(output); configs = configurations(); records = []; h = hashlib.sha256()
    for i, raw in enumerate((output / 'records.jsonl').open('rb')):
        if i >= len(configs) or not raw.endswith(b'\n'): raise ValueError('Panel size/LF')
        h.update(raw); record = prior.old.decode(raw); verify_record(record, configs[i]); records.append(record)
    if len(records) != 2688: raise ValueError('Complete 2688 cases')
    expected = dict(schema='capacity01-summary-v1', revision=revision,
                    sources={f: hashlib.sha256((ROOT / f).read_bytes()).hexdigest() for f in FILES},
                    records_sha256=h.hexdigest(), cases=2688, events=sum(len(r['events']) for r in records),
                    preparation_events=sum(len(r['preparation']) for r in records),
                    authored_feasibility_only=True, natural_worlds=0, totals=aggregate(records))
    if prior.old.canonical(prior.old.decode((output / 'summary.json').read_bytes())) != prior.old.canonical(expected): raise ValueError('Summary/source/denominator')
    return dict(schema='capacity01-audit-v1', cases=2688, events=expected['events'], preparation_events=expected['preparation_events'],
                zero_material_energy_residual=True, exact_semantic_replay=True, full_manufacture_recycling_provenance_verified=True,
                authored_feasibility_only=True, natural_worlds=0, totals=expected['totals'], autonomous_origin_demonstrated=False)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input-dir', required=True); parser.add_argument('--source-revision', required=True)
    args = parser.parse_args()
    try: print(json.dumps(inspect(args.input_dir, args.source_revision), indent=2, sort_keys=True))
    except (ValueError, OSError, KeyError, TypeError) as e: parser.exit(2, f'Rejected CAPACITY-01: {e}\n')
