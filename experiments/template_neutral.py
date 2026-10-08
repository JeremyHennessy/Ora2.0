"""Frozen TEMPLATE-02 monomer-only neutral opportunity pilot."""
import argparse
import copy
import hashlib
import json
from pathlib import Path
import random

ARMS = ('active', 'fixed', 'ghost', 'untemplated', 'shared')
ROOT = Path(__file__).resolve().parents[1]
FILES = ('docs/TEMPLATE-02-PROTOCOL.md', 'experiments/template_neutral.py', 'experiments/template_neutral_audit.py')


def encode(v):
    return json.dumps(v, sort_keys=True, separators=(',', ':'))


def digest(v):
    return hashlib.sha256(encode(v).encode()).hexdigest()


def birth(bits, atoms, tokens, tick, origin, parents=(), producer=None, own=False, matches=False, template=None):
    return dict(bits=bits, atoms=list(atoms), tokens=list(tokens), born_tick=tick, origin=origin,
                parents=list(parents), producer=producer, own_funded=own, sequence_match=matches, template_parent=template)


def genesis(seed, work, mode):
    rng = random.Random(seed)
    s = dict(atoms={}, objects={}, ready=[], nutrients={}, waste={}, history={}, bank=[], heat=0)
    for i in range(96):
        aid = f'a{i:03d}'
        bit = str(rng.randrange(2))
        origin = 'genesis_object' if i < 32 else 'genesis_ready' if i < 64 else 'genesis_nutrient'
        s['atoms'][aid] = dict(bit=bit, origin=origin, reclaims=[])
        if i < 32:
            oid = 'g'+str(i)
            tokens = [dict(unit=f'w{oid}:{j}', origin='genesis', actor=oid, nutrient=None, tick=-1) for j in range(work)]
            if mode == 'shared':
                s['bank'].extend(tokens)
                tokens = []
            obj = birth(bit, [aid], tokens, -1, 'genesis')
            s['objects'][oid] = obj
            s['history'][oid] = copy.deepcopy(obj)
        elif i < 64:
            s['ready'].append(aid)
        else:
            s['nutrients'][aid] = aid
    draws = [[rng.randrange(8), *[rng.randrange(65536) for _ in range(4)]] for _ in range(128)]
    return s, draws


def step(old, mode, tick, draw):
    s = copy.deepcopy(old)
    action, left, right, feed, food = draw
    pool = sorted(s['objects'])
    owner = pool[left % len(pool)] if pool else None
    alternatives = [p for p in pool if p != owner]
    partner = alternatives[right % len(alternatives)] if alternatives else None
    obj = s['objects'].get(owner)
    ready = sorted(s['ready'])
    if ready:
        ready = ready[feed % len(ready):]+ready[:feed % len(ready)]
    selected = []
    if obj and len(obj['bits']) >= 2:
        for bit in obj['bits']:
            possible = ready if mode == 'untemplated' else [a for a in ready if
                (int(s['atoms'][a]['bit']) == int(bit) if mode == 'fixed' else s['atoms'][a]['bit'] == bit)]
            if not possible:
                break
            aid = possible[0]
            selected.append(aid)
            ready.remove(aid)
    foods, wastes = sorted(s['nutrients']), sorted(s['waste'])
    nid = foods[food % len(foods)] if foods else None
    wid = wastes[feed % len(wastes)] if wastes else None
    account = s['bank'] if mode == 'shared' else obj['tokens'] if obj else []
    structural = bool(obj and len(obj['bits']) >= 2 and len(selected) == len(obj['bits']))
    price = 3*len(obj['bits'])+1 if obj else 0
    match = bool(obj and nid and len(obj['bits']) >= 2 and obj['bits'][-1] != s['atoms'][nid]['bit'])
    if mode == 'fixed' and obj and nid:
        match = len(obj['bits']) > 1 and int(obj['bits'][-1])+int(s['atoms'][nid]['bit']) == 1
    ligatable = bool(partner and len(obj['bits'])+len(s['objects'][partner]['bits']) <= 4)
    ligwork = len(s['bank']) if mode == 'shared' else len(obj['tokens'])+len(s['objects'][partner]['tokens']) if partner else 0
    opp = dict(ligation_structural=action < 2 and ligatable, ligation_funded=action < 2 and ligatable and ligwork >= 2,
               copy_structural=action == 2 and structural, copy_funded=action == 2 and structural and len(account) >= price,
               contact_binding=action == 3 and match, contact_funded=action == 3 and match and len(account) >= 2,
               reclaim_structural=action == 5 and wid is not None and owner is not None,
               reclaim_funded=action == 5 and wid is not None and owner is not None and len(account) >= 1,
               any_polymer_copy_work=any(len(o['bits']) >= 2 and (len(s['bank']) if mode == 'shared' else len(o['tokens'])) >= 3*len(o['bits'])+1 for o in s['objects'].values()))
    result = dict(outcome='unavailable', targets=[], product=None, spent=[], returned=[], endowed=[], carried=[], discarded=[],
                  charged=0, heat=0, own_funded=False, sequence_match=False)
    def pay(n, heat):
        spent = account[:n]
        del account[:n]
        s['heat'] += heat
        result.update(spent=spent, charged=n, heat=heat)
        return spent
    if action < 2:
        result['targets'] = [p for p in (owner, partner) if p is not None]
        if opp['ligation_funded']:
            other = s['objects'][partner]
            if mode != 'shared':
                account = obj['tokens']+other['tokens']
            pay(2, 1)
            oid = 'o'+str(tick)
            tokens = [] if mode == 'shared' else account
            product = birth(obj['bits']+other['bits'], obj['atoms']+other['atoms'], tokens, tick, 'ligation', (owner, partner))
            del s['objects'][owner], s['objects'][partner]
            s['objects'][oid] = product
            s['history'][oid] = copy.deepcopy(product)
            result.update(outcome='ligated', product=oid, carried=copy.deepcopy(tokens))
    elif action == 2:
        result['targets'] = [] if owner is None else [owner]
        if opp['copy_funded']:
            n = len(obj['bits'])
            spent = pay(price, price if mode == 'ghost' else 2*n)
            own = all(t['origin'] == 'nutrient' and t['actor'] == owner for t in spent)
            result['own_funded'] = own
            if mode == 'ghost':
                result['outcome'] = 'paid_ghost'
            else:
                oid = 'o'+str(tick)
                bits = ''.join(s['atoms'][a]['bit'] for a in selected)
                endowment = spent[-2:]
                product = birth(bits, selected, [] if mode == 'shared' else endowment, tick, 'copy',
                                producer=owner, own=own, matches=bits == obj['bits'], template=None if mode == 'untemplated' else owner)
                if mode == 'shared':
                    s['bank'].extend(endowment)
                for aid in selected:
                    s['ready'].remove(aid)
                s['objects'][oid] = product
                s['history'][oid] = copy.deepcopy(product)
                result.update(outcome='copied', product=oid, endowed=endowment, sequence_match=bits == obj['bits'])
    elif action == 3:
        result['targets'] = [p for p in (owner, nid) if p is not None]
        if owner is not None:
            count = min(2, len(account))
            pay(count, count)
            result['outcome'] = 'spent' if count else 'starved'
            if count == 2 and match:
                del s['nutrients'][nid]
                s['waste'][nid] = dict(retired_id=None, retired_tick=tick)
                tokens = [dict(unit=f'wn{nid}:{j}', origin='nutrient', actor=owner, nutrient=nid, tick=tick) for j in range(3)]
                account.extend(tokens)
                s['heat'] += 5
                result.update(outcome='converted', returned=tokens, heat=7)
    elif action == 4:
        result['targets'] = [] if owner is None else [owner]
        if obj is not None:
            del s['objects'][owner]
            for aid in obj['atoms']:
                s['waste'][aid] = dict(retired_id=owner, retired_tick=tick)
            heat = len(obj['bits'])-1+len(obj['tokens'])
            s['heat'] += heat
            result.update(outcome='decayed', heat=heat, discarded=obj['tokens'])
    elif action == 5:
        result['targets'] = [p for p in (owner, wid) if p is not None]
        if opp['reclaim_funded']:
            pay(1, 1)
            former = s['waste'].pop(wid)
            s['atoms'][wid]['reclaims'].append(dict(actor=owner, tick=tick, retired_id=former['retired_id']))
            s['ready'].append(wid)
            result['outcome'] = 'reclaimed'
    else:
        result['outcome'] = 'idle'
    return s, opp, result


def statistics(initial, events, terminal):
    results = [e['result'] for e in events]
    functioned, first, primary, renewed = set(), {}, set(), set()
    for e in events:
        r = e['result']
        if r['outcome'] != 'converted':
            continue
        oid = r['targets'][0]
        first.setdefault(oid, e['tick'])
        h = terminal['history'][oid]
        if h['origin'] != 'copy':
            continue
        functioned.add(oid)
        if h['own_funded'] and h['sequence_match']:
            primary.add(oid)
            parent = terminal['history'][h['producer']]
            if parent['origin'] == 'copy' and parent['own_funded'] and parent['sequence_match'] and first.get(h['producer'], 999) < h['born_tick']:
                renewed.add(oid)
    return dict(ligations=sum(r['outcome'] == 'ligated' for r in results), copies=sum(r['outcome'] == 'copied' for r in results),
                own_funded_copies=sum(r['outcome'] == 'copied' and r['own_funded'] for r in results),
                matching_copies=sum(r['outcome'] == 'copied' and r['sequence_match'] for r in results),
                primary_children=len(primary), primary_conversion_events=sum(r['outcome'] == 'converted' and r['targets'][0] in primary for r in results),
                renewed_children=len(renewed), functional_copy_children=len(functioned), conversions=sum(r['outcome'] == 'converted' for r in results),
                paid_ghosts=sum(r['outcome'] == 'paid_ghost' for r in results), decays=sum(r['outcome'] == 'decayed' for r in results),
                reclaims=sum(r['outcome'] == 'reclaimed' for r in results), charged=sum(r['charged'] for r in results),
                returned=sum(len(r['returned']) for r in results), endowed=sum(len(r['endowed']) for r in results),
                starved_contacts=sum(r['outcome'] == 'starved' for r in results), partial_contacts=sum(r['outcome'] == 'spent' and r['charged'] == 1 for r in results),
                missing_food_contacts=sum(e['draw'][0] == 3 and not any(a in initial['nutrients'] for a in e['result']['targets']) for e in events),
                unavailable=sum(r['outcome'] == 'unavailable' for r in results),
                opportunities={k: sum(e['opportunities'][k] for e in events) for k in events[0]['opportunities']},
                terminal_work=len(terminal['bank'])+sum(len(o['tokens']) for o in terminal['objects'].values()),
                terminal_heat=terminal['heat'], terminal_bonds=sum(len(o['bits'])-1 for o in terminal['objects'].values()),
                remaining_food=len(terminal['nutrients']), ready_atoms=len(terminal['ready']), waste_atoms=len(terminal['waste']))


def simulate(seed, work):
    arms = []
    all_draws = None
    for mode in ARMS:
        initial, draws = genesis(seed, work, mode)
        state, chain, events = initial, digest(initial), []
        for tick, draw in enumerate(draws):
            before = digest(state)
            state, opp, result = step(state, mode, tick, draw)
            event = dict(tick=tick, draw=draw, before=before, after=digest(state), previous=chain, opportunities=opp, result=result)
            event['sha256'] = digest(event)
            chain = event['sha256']
            events.append(event)
        arms.append(dict(mode=mode, initial=initial, events=events, terminal=state, statistics=statistics(initial, events, state)))
        all_draws = draws
    return dict(seed=seed, work_per_monomer=work, draws=all_draws, arms=arms)


def summary(records, revision):
    regimes = {}
    for work in (2, 0):
        panel = [r for r in records if r['work_per_monomer'] == work]
        totals = {}
        for mode in ARMS:
            rows = [next(a['statistics'] for a in r['arms'] if a['mode'] == mode) for r in panel]
            totals[mode] = {k: sum(row[k] for row in rows) for k, v in rows[0].items() if type(v) is int}
            totals[mode]['primary_worlds'] = sum(row['primary_children'] > 0 for row in rows)
            totals[mode]['copy_funding_worlds'] = sum(row['opportunities']['any_polymer_copy_work'] > 0 for row in rows)
            totals[mode]['opportunities'] = {k: sum(row['opportunities'][k] for row in rows) for k in rows[0]['opportunities']}
        contrasts = [dict(seed=r['seed'], difference=r['arms'][0]['statistics']['primary_children']-r['arms'][3]['statistics']['primary_children']) for r in panel]
        regimes[str(work)] = dict(arms=totals, active_vs_untemplated=contrasts)
    admitted = regimes['2']['arms']['active']['primary_worlds'] >= 4 and sum(c['difference'] > 0 for c in regimes['2']['active_vs_untemplated']) >= 4 and sum(c['difference'] for c in regimes['2']['active_vs_untemplated']) > 0
    return dict(schema='template02-summary-v1', revision=revision, source_sha256={p: hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in FILES},
                independent_initializations=16, paired_settings=32, correlated_histories=160, events=20480, regimes=regimes,
                admission_passed=admitted, decision='propose_separate_causal_protocol' if admitted else 'close_negative_neutral_pilot')


def run(output, revision):
    if len(revision) != 40 or any(c not in '0123456789abcdef' for c in revision):
        raise ValueError('Exact revision required')
    output = Path(output)
    output.mkdir(parents=True, exist_ok=False)
    records = [simulate(seed, work) for seed in range(128, 144) for work in (2, 0)]
    raw = (''.join(encode(r)+'\n' for r in records)).encode()
    (output/'records.jsonl').write_bytes(raw)
    result = summary(records, revision)
    result['records_sha256'] = hashlib.sha256(raw).hexdigest()
    (output/'summary.json').write_bytes((encode(result)+'\n').encode())


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output-dir', required=True)
    parser.add_argument('--source-revision', required=True)
    args = parser.parse_args()
    run(args.output_dir, args.source_revision)
