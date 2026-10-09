"""RECYCLE-01 finite unscreened paid recycling; no runtime installation."""
import copy
import argparse
from collections import Counter
import hashlib
from pathlib import Path
from experiments import paid_dissociation as cut
from experiments import renewal_opportunity as diagnosis

ROOT = Path(__file__).resolve().parents[1]
MODES = ('candidate', 'irreversible', 'cut_ghost', 'product_ghost', 'association_off',
         'supplied', 'food_withdrawn', 'external', 'no_initial_work')
FILES = tuple(dict.fromkeys(cut.FILES + diagnosis.FILES + ('docs/CAPACITY-01-PROTOCOL.md',
              'docs/RECYCLE-01-PROTOCOL.md', 'experiments/recycling_unscreened.py',
              'experiments/recycling_unscreened_audit.py')))

def configs(): return [dict(seed=seed, mode=m) for seed in range(42000, 42032) for m in MODES]

def select(s, draw):
    chains = sorted(s['chains']); products = sorted(s['products'])
    return dict(op=draw[0], atom=f'M{draw[1]%24}', food=f'F{draw[2]%64}',
                chain=chains[draw[3] % len(chains)] if chains else None,
                actor=products[draw[4] % len(products)] if products else None)

def initial(c):
    s, rng = cut.base.initial(c['seed'], 'active')
    s['recycles'] = {f'M{i}': [] for i in range(24)}
    preparation = []; chain = cut.digest(s)
    if c['mode'] == 'supplied':
        actions = [(0, 0), (2, 0)]
        for atom in range(1, 6): actions.extend(((0, atom), (3, atom), (0, atom)))
        actions.append((4, 0))
        for i, (op, atom) in enumerate(actions):
            chains = sorted(s['chains'], key=lambda key: (-len(s['chains'][key]['atoms']), key))
            q = dict(op=op, atom=f'M{atom}', food=min(s['food'], key=lambda a: int(a[1:])), chain=chains[0] if chains else None, actor=None)
            before = cut.digest(s); result = cut.step(s, c, i - 128, q)
            e = dict(tick=i-128, request=q, before=before, after=cut.digest(s), previous=chain, result=result)
            e['sha256'] = cut.digest(e); chain = e['sha256']; preparation.append(e)
    if c['mode'] == 'no_initial_work': s['reserve_work'].extend(s['bank']); s['bank'] = []
    return s, rng, preparation

def measure(s, c, tick):
    row = diagnosis.measure(s, cut.mode(c), tick)
    row.update(large_payers=sum(len(p['atoms']) >= 5 for p in s['products'].values()),
               recycled_free_atoms=sum(bool(s['recycles'][a]) and s['history'][s['recycles'][a][-1]]['returned'] for a in s['free']))
    pairs = reserve = 0
    if tick >= 128 and c['mode'] not in ('irreversible', 'external'):
        for ch in s['chains'].values():
            n = len(ch['atoms'])
            if n < 2: continue
            for p in s['products'].values():
                if len(p['work']) >= n + 1 and all(s['units'][u]['origin'] == 'capture' for u in p['work'][:n+1]):
                    pairs += 1; reserve += int(len(p['work']) >= n + 3)
    row.update(capture_cut_pairs=pairs, capture_cut_reserve_pairs=reserve)
    return row

def classification(s, tick, result):
    out = result['outcome']; kind = 'other'
    if out == 'charged': kind = 'capture_paid_charge' if all(s['units'][u]['origin'] == 'capture' for u in result['spent']) else 'other_funded_charge'
    elif out == 'started': kind = 'clean_start' if diagnosis.clean(s, result['spent']) else 'contaminated_start'
    elif out in ('extended', 'released'):
        value = s['history'][f'C{tick}' if out == 'extended' else result['product']]
        kind = ('clean_' if diagnosis.clean(s, value['debits']) else 'contaminated_') + ('extension' if out == 'extended' else 'release')
    elif out == 'captured': kind = 'assembled_capture' if s['history'][result['actor']]['born'] >= 0 else 'supplied_capture'
    elif out in ('cut', 'inert_cut'):
        value = s['history'][result['product']]
        paid = tick >= 128 and all(s['units'][u]['origin'] == 'capture' for u in value['work_debits'])
        kind = ('capture_paid_' if paid else 'other_funded_') + ('cut' if out == 'cut' else 'inert_cut')
    return kind

def simulate(c):
    s, rng, preparation = initial(c); start = copy.deepcopy(s); initial_rng = rng.getstate(); chain = cut.digest(s); events = []
    for t in range(256):
        draw = [rng.randrange(7)] + [rng.randrange(65536) for _ in range(5)]
        q = select(s, draw); before = cut.digest(s); opportunities = measure(s, c, t)
        result = cut.step(s, c, t, q)
        e = dict(tick=t, draw=draw, request=q, before=before, after=cut.digest(s), previous=chain,
                 result=result, opportunities=opportunities, selected=classification(s, t, result))
        e['sha256'] = cut.digest(e); chain = e['sha256']; events.append(e)
    return dict(config=c, preparation=preparation, initial=start, rng_initial=initial_rng,
                events=events, terminal=s, rng_terminal=rng.getstate(), noise_cursor=1536)

def metrics(r):
    s = r['terminal']; births = {k: v for k, v in s['history'].items() if v['kind'] == 'product' and v['born'] >= 0}
    cuts = [v for v in s['history'].values() if v['kind'] == 'dismantled']
    used = set(); wholly = set(); partial = set(); paid = set(); fresh = set(); clean = set()
    for key, p in births.items():
        if p['born'] < 128: continue
        last = []
        for a in p['atoms']:
            previous = [s['history'][k] for k in s['recycles'][a] if s['history'][k]['born'] < p['born']]
            last.append(previous[-1] if previous else None)
        recycled = sum(v is not None and v['returned'] for v in last)
        if recycled: used.add(key)
        if recycled == len(p['atoms']): wholly.add(key)
        if 0 < recycled < len(p['atoms']): partial.add(key)
        if p['fully_capture_funded']:
            clean.add(key)
            if not any(last): fresh.add(key)
            if recycled == len(p['atoms']) and all(v['born'] >= 128 and all(s['units'][u]['origin'] == 'capture' for u in v['work_debits']) for v in last): paid.add(key)
    captures = [e for e in r['events'] if e['result']['outcome'] == 'captured']
    post = [e for e in captures if e['tick'] >= 128]
    probes = lambda ids: sum(e['result']['actor'] in ids for e in post)
    totals = dict(worlds=1, assemblies=len(births), assembled_captures=sum(e['result']['actor'] in births for e in captures),
                  supplied_captures=sum(e['result']['actor'] not in births for e in captures), post_withdrawal_captures=probes(births),
                  fully_capture_funded_births=len(clean), fully_capture_funded_probes=probes(clean),
                  recycled_releases=len(used), partial_recycled_releases=len(partial), fully_recycled_releases=len(wholly),
                  capture_paid_recycled_releases=len(paid), capture_paid_recycled_probes=probes(paid),
                  capture_paid_fresh_releases=len(fresh), capture_paid_fresh_probes=probes(fresh),
                  cuts=sum(v['returned'] for v in cuts), inert_cuts=sum(not v['returned'] for v in cuts),
                  cut_work=sum(len(v['work_debits']) for v in cuts), cut_bond_heat=sum(len(v['bond_debits']) for v in cuts),
                  cut_charge_heat=sum(len(v['charge_debits']) for v in cuts), recycled_atoms=sum(bool(ids) for ids in s['recycles'].values()),
                  remaining_food=len(s['food']), waste=len(s['waste']), final_heat=s['heat'], unused_external=len(s['bank']))
    sums = Counter(); nonzero = Counter(); selected = Counter()
    for e in r['events']:
        if e['tick'] >= 128:
            sums.update(e['opportunities']); nonzero.update(k for k, v in e['opportunities'].items() if v)
        selected[('post/' if e['tick'] >= 128 else 'pre/') + e['selected']] += 1
    return dict(totals=totals, post_opportunity_sums=dict(sums), post_nonzero_steps=dict(nonzero), selected=dict(selected))

def aggregate(records):
    rows = {}
    for r in records:
        row = rows.setdefault(r['config']['mode'], dict(worlds=0, totals={}, post_opportunity_sums={}, post_nonzero_steps={}, selected={}, worlds_with={}))
        m = metrics(r); row['worlds'] += 1
        for group in ('totals', 'post_opportunity_sums', 'post_nonzero_steps', 'selected'):
            for key, value in m[group].items(): row[group][key] = row[group].get(key, 0) + value
        for key in ('large_payers', 'capture_cut_pairs', 'capture_cut_reserve_pairs', 'clean_starts', 'clean_extensions', 'clean_releases'):
            row['worlds_with'][key] = row['worlds_with'].get(key, 0) + int(m['post_opportunity_sums'].get(key, 0) > 0)
        for key in ('capture_paid_recycled_probes', 'capture_paid_recycled_releases', 'assembled_captures', 'fully_capture_funded_births'):
            row['worlds_with'][key] = row['worlds_with'].get(key, 0) + int(m['totals'][key] > 0)
    return rows

def run(output, revision):
    if len(revision) != 40 or any(x not in '0123456789abcdef' for x in revision): raise ValueError('Exact revision')
    output = Path(output); output.mkdir(parents=True, exist_ok=False); records = []; h = hashlib.sha256()
    with (output / 'records.jsonl').open('wb') as f:
        for c in configs():
            r = simulate(c); data = (cut.encode(r) + '\n').encode(); f.write(data); h.update(data); records.append(r)
    summary = dict(schema='recycle01-summary-v1', revision=revision, sources={f: hashlib.sha256((ROOT / f).read_bytes()).hexdigest() for f in FILES},
                   records_sha256=h.hexdigest(), worlds=288, events=73728, preparation_events=576,
                   independent_seed_blocks=32, reserved_samples_executed=False, totals=aggregate(records))
    (output / 'summary.json').write_bytes((cut.encode(summary) + '\n').encode()); return summary

if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__); p.add_argument('--output-dir', required=True); p.add_argument('--source-revision', required=True)
    a = p.parse_args(); run(a.output_dir, a.source_revision)
