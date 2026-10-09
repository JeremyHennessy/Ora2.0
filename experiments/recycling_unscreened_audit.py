"""Independent RECYCLE-01 finite-noise, manufacture and recycling interpreter."""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
from experiments import paid_dissociation_audit as cut
from experiments import renewal_opportunity_audit as diagnosis

ROOT = Path(__file__).resolve().parents[1]
MODES = ('candidate', 'irreversible', 'cut_ghost', 'product_ghost', 'association_off',
         'supplied', 'food_withdrawn', 'external', 'no_initial_work')
FILES = tuple(dict.fromkeys(cut.FILES + diagnosis.FILES + ('docs/CAPACITY-01-PROTOCOL.md',
              'docs/RECYCLE-01-PROTOCOL.md', 'experiments/recycling_unscreened.py',
              'experiments/recycling_unscreened_audit.py')))

def configurations(): return [dict(seed=i, mode=m) for i in range(42000, 42032) for m in MODES]

def request(s, draw):
    cs = sorted(s['chains']); ps = sorted(s['products'])
    return dict(op=draw[0], atom=f'M{draw[1] % 24}', food=f'F{draw[2] % 64}',
                chain=cs[draw[3] % len(cs)] if cs else None,
                actor=ps[draw[4] % len(ps)] if ps else None)

def genesis(c):
    s, rng = cut.old.genesis(dict(seed=c['seed'], mode='active'))
    s['recycles'] = {f'M{i}': [] for i in range(24)}
    cut.validate(s); prep = []; chain = cut.old.digest(s)
    if c['mode'] == 'supplied':
        actions = [(0, 0), (2, 0)]
        for atom in range(1, 6): actions += [(0, atom), (3, atom), (0, atom)]
        actions += [(4, 0)]
        for i, (op, atom) in enumerate(actions):
            cid = min(s['chains'], key=lambda k: (-len(s['chains'][k]['atoms']), k)) if s['chains'] else None
            food = min(s['food'], key=lambda a: int(a[1:]))
            q = dict(op=op, atom=f'M{atom}', food=food, chain=cid, actor=None)
            before = cut.old.digest(s); result = cut.transition(s, c, i - 128, q); cut.validate(s)
            event = dict(tick=i-128, request=q, before=before, after=cut.old.digest(s), previous=chain, result=result)
            event['sha256'] = cut.old.digest(event); chain = event['sha256']; prep.append(event)
    if c['mode'] == 'no_initial_work': s['reserve_work'] += s['bank']; s['bank'] = []
    cut.validate(s); return s, rng, prep

def opportunities(s, c, tick):
    row = diagnosis.opportunities(s, cut.lawmode(c), tick)
    row['large_payers'] = sum(len(p['atoms']) >= 5 for p in s['products'].values())
    row['recycled_free_atoms'] = sum(bool(s['recycles'][a]) and s['history'][s['recycles'][a][-1]]['returned'] for a in s['free'])
    pairs = reserve = 0
    if tick >= 128 and c['mode'] not in ('irreversible', 'external'):
        for ch in s['chains'].values():
            n = len(ch['atoms'])
            if n < 2: continue
            for p in s['products'].values():
                eligible = len(p['work']) >= n + 1 and all(s['units'][u]['origin'] == 'capture' for u in p['work'][:n+1])
                pairs += int(eligible); reserve += int(eligible and len(p['work']) >= n + 3)
    row.update(capture_cut_pairs=pairs, capture_cut_reserve_pairs=reserve)
    return row

def selected(s, tick, result):
    out = result['outcome']; kind = 'other'
    if out == 'charged': kind = 'capture_paid_charge' if all(s['units'][u]['origin'] == 'capture' for u in result['spent']) else 'other_funded_charge'
    elif out == 'started': kind = 'clean_start' if all(diagnosis.paid(s, u) for u in result['spent']) else 'contaminated_start'
    elif out in ('extended', 'released'):
        value = s['history'][f'C{tick}' if out == 'extended' else result['product']]
        clean = all(diagnosis.paid(s, u) for u in value['debits'])
        kind = ('clean_' if clean else 'contaminated_') + ('extension' if out == 'extended' else 'release')
    elif out == 'captured': kind = 'assembled_capture' if s['history'][result['actor']]['born'] >= 0 else 'supplied_capture'
    elif out in ('cut', 'inert_cut'):
        v = s['history'][result['product']]
        private = tick >= 128 and all(s['units'][u]['origin'] == 'capture' for u in v['work_debits'])
        kind = ('capture_paid_' if private else 'other_funded_') + ('cut' if out == 'cut' else 'inert_cut')
    return kind

def metrics(r):
    s = r['terminal']; births = {k: v for k, v in s['history'].items() if v['kind'] == 'product' and v['born'] >= 0}
    cuts = [v for v in s['history'].values() if v['kind'] == 'dismantled']
    any_recycled = set(); wholly = set(); qualified = set(); fresh = set(); clean_products = set(); partial = set()
    for key, p in births.items():
        if p['born'] < 128: continue
        latest = []
        for atom in p['atoms']:
            previous = [s['history'][k] for k in s['recycles'][atom] if s['history'][k]['born'] < p['born']]
            latest.append(previous[-1] if previous else None)
        used = sum(v is not None and v['returned'] for v in latest)
        if used: any_recycled.add(key)
        if 0 < used < len(p['atoms']): partial.add(key)
        if used == len(p['atoms']): wholly.add(key)
        if p['fully_capture_funded']:
            clean_products.add(key)
            if not any(latest): fresh.add(key)
            if used == len(p['atoms']) and all(v['born'] >= 128 and all(s['units'][u]['origin'] == 'capture' for u in v['work_debits']) for v in latest): qualified.add(key)
    captures = [e for e in r['events'] if e['result']['outcome'] == 'captured']
    post = [e for e in captures if e['tick'] >= 128]
    probes = lambda keys: sum(e['result']['actor'] in keys for e in post)
    row = dict(worlds=1, assemblies=len(births), assembled_captures=sum(e['result']['actor'] in births for e in captures),
               supplied_captures=sum(e['result']['actor'] not in births for e in captures), post_withdrawal_captures=probes(births),
               fully_capture_funded_births=len(clean_products), fully_capture_funded_probes=probes(clean_products),
               recycled_releases=len(any_recycled), partial_recycled_releases=len(partial), fully_recycled_releases=len(wholly),
               capture_paid_recycled_releases=len(qualified), capture_paid_recycled_probes=probes(qualified),
               capture_paid_fresh_releases=len(fresh), capture_paid_fresh_probes=probes(fresh),
               cuts=sum(v['returned'] for v in cuts), inert_cuts=sum(not v['returned'] for v in cuts),
               cut_work=sum(len(v['work_debits']) for v in cuts), cut_bond_heat=sum(len(v['bond_debits']) for v in cuts),
               cut_charge_heat=sum(len(v['charge_debits']) for v in cuts), recycled_atoms=sum(bool(x) for x in s['recycles'].values()),
               remaining_food=len(s['food']), waste=len(s['waste']), final_heat=s['heat'], unused_external=len(s['bank']))
    sums = Counter(); nonzero = Counter(); outcomes = Counter()
    for e in r['events']:
        if e['tick'] >= 128:
            sums.update(e['opportunities']); nonzero.update(k for k, v in e['opportunities'].items() if v)
        outcomes[('post/' if e['tick'] >= 128 else 'pre/') + e['selected']] += 1
    return dict(totals=row, post_opportunity_sums=dict(sums), post_nonzero_steps=dict(nonzero), selected=dict(outcomes))

def aggregate(records):
    rows = {}
    for r in records:
        m = metrics(r); row = rows.setdefault(r['config']['mode'], dict(worlds=0, totals={}, post_opportunity_sums={}, post_nonzero_steps={}, selected={}, worlds_with={}))
        row['worlds'] += 1
        for group in ('totals', 'post_opportunity_sums', 'post_nonzero_steps', 'selected'):
            for k, v in m[group].items(): row[group][k] = row[group].get(k, 0) + v
        for key in ('large_payers', 'capture_cut_pairs', 'capture_cut_reserve_pairs', 'clean_starts', 'clean_extensions', 'clean_releases'):
            row['worlds_with'][key] = row['worlds_with'].get(key, 0) + int(m['post_opportunity_sums'].get(key, 0) > 0)
        for key in ('capture_paid_recycled_probes', 'capture_paid_recycled_releases', 'assembled_captures', 'fully_capture_funded_births'):
            row['worlds_with'][key] = row['worlds_with'].get(key, 0) + int(m['totals'][key] > 0)
    return rows

def verify_record(r, c):
    canonical = cut.old.canonical; digest = cut.old.digest
    if canonical(r['config']) != canonical(c): raise ValueError('Frozen fresh configuration')
    s, rng, prep = genesis(c)
    if canonical(r['initial']) != canonical(s) or canonical(r['preparation']) != canonical(prep): raise ValueError('Genesis/manufacture')
    if canonical(r['rng_initial']) != canonical(rng.getstate()) or len(r['events']) != 256: raise ValueError('Initial RNG/horizon')
    chain = digest(s)
    for tick, event in enumerate(r['events']):
        draw = [rng.randrange(7)] + [rng.randrange(65536) for _ in range(5)]
        q = request(s, draw); before = digest(s); observation = opportunities(s, c, tick)
        result = cut.transition(s, c, tick, q); cut.validate(s)
        expected = dict(tick=tick, draw=draw, request=q, before=before, after=digest(s), previous=chain,
                        result=result, opportunities=observation, selected=selected(s, tick, result))
        expected['sha256'] = digest(expected)
        if canonical(event) != canonical(expected): raise ValueError('Noise/reaction/opportunity/provenance')
        chain = expected['sha256']
    if canonical(r['terminal']) != canonical(s) or canonical(r['rng_terminal']) != canonical(rng.getstate()) or type(r['noise_cursor']) is not int or r['noise_cursor'] != 1536: raise ValueError('Terminal/RNG/cursor')
    return metrics(r)

def inspect(output, revision):
    output = Path(output); records = []; configs = configurations(); h = hashlib.sha256()
    with (output / 'records.jsonl').open('rb') as f:
        for i, raw in enumerate(f):
            if i >= len(configs) or not raw.endswith(b'\n'): raise ValueError('Panel size/LF')
            h.update(raw); r = cut.old.decode(raw); verify_record(r, configs[i]); records.append(r)
    if len(records) != 288: raise ValueError('Complete 288 worlds')
    expected = dict(schema='recycle01-summary-v1', revision=revision,
                    sources={f: hashlib.sha256((ROOT / f).read_bytes()).hexdigest() for f in FILES},
                    records_sha256=h.hexdigest(), worlds=288, events=73728, preparation_events=576,
                    independent_seed_blocks=32, reserved_samples_executed=False, totals=aggregate(records))
    if cut.old.canonical(cut.old.decode((output / 'summary.json').read_bytes())) != cut.old.canonical(expected): raise ValueError('Summary/source/denominator')
    for mode in ('cut_ghost', 'product_ghost', 'association_off', 'no_initial_work'):
        if expected['totals'][mode]['totals']['capture_paid_recycled_probes']: raise ValueError('Primary null violation')
    if any(e['tick'] >= 128 and e['result']['outcome'] == 'captured' for r in records if r['config']['mode'] == 'food_withdrawn' for e in r['events']): raise ValueError('Food withdrawal violation')
    candidate = expected['totals']['candidate']['worlds_with']['capture_paid_recycled_probes']
    return dict(schema='recycle01-audit-v1', worlds=288, events=73728, preparation_events=576, independent_seed_blocks=32,
                zero_material_energy_residual=True, exact_semantic_noise_opportunity_replay=True, complete_rng_cursor_verified=True,
                totals=expected['totals'], repeatable_candidate_realization=candidate >= 2,
                autonomous_origin_demonstrated=False, reproduction_demonstrated=False)

if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__); p.add_argument('--input-dir', required=True); p.add_argument('--source-revision', required=True)
    a = p.parse_args()
    try: print(json.dumps(inspect(a.input_dir, a.source_revision), indent=2, sort_keys=True))
    except (ValueError, OSError, KeyError, TypeError) as e: p.exit(2, f'Rejected RECYCLE-01: {e}\n')
