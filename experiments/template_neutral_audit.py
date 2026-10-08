"""Independent material/work-provenance replay; imports no neutral worker."""
import argparse
import copy
import hashlib
import itertools
import json
from pathlib import Path
import random

ROOT = Path(__file__).resolve().parents[1]
ARMS = ('active', 'fixed', 'ghost', 'untemplated', 'shared')
FILES = ('docs/TEMPLATE-02-PROTOCOL.md', 'experiments/template_neutral.py', 'experiments/template_neutral_audit.py')


def canonical(v):
    return json.dumps(v, sort_keys=True, separators=(',', ':'))


def sha(v):
    return hashlib.sha256(canonical(v).encode()).hexdigest()


def unique(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError('Duplicate JSON key')
        result[key] = value
    return result


def born(bits, atoms, tokens, tick, origin, parents=(), producer=None, own=False, matches=False, template=None):
    return dict(bits=bits, atoms=list(atoms), tokens=list(tokens), born_tick=tick, origin=origin, parents=list(parents),
                producer=producer, own_funded=own, sequence_match=matches, template_parent=template)


def regenerate(seed, budget, mode):
    generator = random.Random(seed)
    values = [str(generator.randrange(2)) for _ in range(96)]
    atoms = {f'a{i:03d}': dict(bit=bit, origin=('genesis_object' if i < 32 else 'genesis_ready' if i < 64 else 'genesis_nutrient'), reclaims=[])
             for i, bit in enumerate(values)}
    objects, bank = {}, []
    for i in range(32):
        oid = f'g{i}'
        work = [dict(unit=f'w{oid}:{j}', origin='genesis', actor=oid, nutrient=None, tick=-1) for j in range(budget)]
        objects[oid] = born(values[i], [f'a{i:03d}'], [] if mode == 'shared' else work, -1, 'genesis')
        if mode == 'shared':
            bank += work
    state = dict(atoms=atoms, objects=objects, ready=[f'a{i:03d}' for i in range(32, 64)],
                 nutrients={f'a{i:03d}': f'a{i:03d}' for i in range(64, 96)}, waste={}, history=copy.deepcopy(objects), bank=bank, heat=0)
    draws = [[generator.randrange(bound) for bound in (8, 65536, 65536, 65536, 65536)] for _ in range(128)]
    return state, draws


def ledger(s):
    if type(s['heat']) is not int or s['heat'] < 0:
        raise ValueError('Invalid heat')
    atoms = s['ready']+list(s['waste'])+list(s['nutrients'])
    units, bonds = list(s['bank']), 0
    for o in s['objects'].values():
        if not 1 <= len(o['bits']) <= 4 or o['bits'] != ''.join(s['atoms'][a]['bit'] for a in o['atoms']):
            raise ValueError('Object bits/material')
        atoms += o['atoms']
        units += o['tokens']
        bonds += len(o['bits'])-1
    if len(atoms) != 96 or len(set(atoms)) != 96 or set(atoms) != set(s['atoms']):
        raise ValueError('Duplicated/lost/invented material')
    if len({t['unit'] for t in units}) != len(units):
        raise ValueError('Work unit has duplicate ownership')
    if any(t['origin'] not in ('genesis', 'nutrient') for t in units):
        raise ValueError('Invalid work root')
    return (*[sum(s['atoms'][a]['bit'] == bit for a in atoms) for bit in ('0', '1')],
            len(units)+s['heat']+bonds+8*len(s['nutrients']))


def transition(old, mode, tick, draw):
    s = copy.deepcopy(old)
    act, selection, partner_selection, material_selection, food_selection = draw
    ids = sorted(old['objects'])
    oid = ids[selection % len(ids)] if ids else None
    remaining = [k for k in ids if k != oid]
    other_id = remaining[partner_selection % len(remaining)] if remaining else None
    obj = old['objects'].get(oid)
    ready = sorted(old['ready'])
    offset = material_selection % len(ready) if ready else 0
    candidates = ready[offset:]+ready[:offset]
    feed = []
    if obj and len(obj['atoms']) > 1:
        for bit in obj['bits']:
            atom = next((a for a in candidates if mode == 'untemplated' or int(old['atoms'][a]['bit']) == int(bit)), None)
            if atom is None:
                break
            feed.append(atom)
            candidates.remove(atom)
    nutrients, waste = sorted(old['nutrients']), sorted(old['waste'])
    food = nutrients[food_selection % len(nutrients)] if nutrients else None
    discarded_atom = waste[material_selection % len(waste)] if waste else None
    available = old['bank'] if mode == 'shared' else obj['tokens'] if obj else []
    structural = bool(obj and len(obj['atoms']) > 1 and len(feed) == len(obj['atoms']))
    price = 3*len(obj['atoms'])+1 if obj else 0
    binding = bool(obj and food and len(obj['atoms']) > 1 and int(obj['bits'][-1])+int(old['atoms'][food]['bit']) == 1)
    ligation = bool(other_id and len(obj['atoms'])+len(old['objects'][other_id]['atoms']) <= 4)
    combined = old['bank'] if mode == 'shared' else obj['tokens']+old['objects'][other_id]['tokens'] if other_id else []
    opportunities = dict(ligation_structural=act < 2 and ligation, ligation_funded=act < 2 and ligation and len(combined) >= 2,
                         copy_structural=act == 2 and structural, copy_funded=act == 2 and structural and len(available) >= price,
                         contact_binding=act == 3 and binding, contact_funded=act == 3 and binding and len(available) >= 2,
                         reclaim_structural=act == 5 and discarded_atom is not None and oid is not None,
                         reclaim_funded=act == 5 and discarded_atom is not None and oid is not None and len(available) >= 1,
                         any_polymer_copy_work=any(len(o['atoms']) > 1 and (len(old['bank']) if mode == 'shared' else len(o['tokens'])) >= 3*len(o['atoms'])+1 for o in old['objects'].values()))
    result = dict(outcome='unavailable', targets=[], product=None, spent=[], returned=[], endowed=[], carried=[], discarded=[],
                  charged=0, heat=0, own_funded=False, sequence_match=False)
    account = s['bank'] if mode == 'shared' else s['objects'][oid]['tokens'] if oid else []
    cost, released, credit, new_birth = 0, 0, [], None
    if act < 2:
        result['targets'] = [k for k in (oid, other_id) if k is not None]
        if opportunities['ligation_funded']:
            cost, released = 2, 1
            spent = combined[:2]
            carried = [] if mode == 'shared' else copy.deepcopy(combined[2:])
            other = old['objects'][other_id]
            new_birth = born(obj['bits']+other['bits'], obj['atoms']+other['atoms'], carried, tick, 'ligation', (oid, other_id))
            s['objects'].pop(oid)
            s['objects'].pop(other_id)
            if mode != 'shared':
                account = list(combined)
            result.update(outcome='ligated', spent=spent, carried=carried)
    elif act == 2:
        result['targets'] = [] if oid is None else [oid]
        if opportunities['copy_funded']:
            cost = price
            own = all(t['origin'] == 'nutrient' and t['actor'] == oid for t in available[:price])
            result['own_funded'] = own
            if mode == 'ghost':
                released = price
                result['outcome'] = 'paid_ghost'
            else:
                released = 2*len(obj['atoms'])
                bits = ''.join(old['atoms'][a]['bit'] for a in feed)
                endowment = copy.deepcopy(available[price-2:price])
                result.update(outcome='copied', endowed=endowment, sequence_match=bits == obj['bits'])
                new_birth = born(bits, feed, [] if mode == 'shared' else endowment, tick, 'copy', producer=oid,
                                 own=own, matches=bits == obj['bits'], template=None if mode == 'untemplated' else oid)
                s['ready'] = [a for a in old['ready'] if a not in feed]
                if mode == 'shared':
                    credit += endowment
    elif act == 3:
        result['targets'] = [k for k in (oid, food) if k is not None]
        if oid is not None:
            cost = min(2, len(available))
            released = cost
            result['outcome'] = 'spent' if cost else 'starved'
            if cost == 2 and binding:
                s['nutrients'].pop(food)
                s['waste'][food] = dict(retired_id=None, retired_tick=tick)
                credit = [dict(unit=f'wn{food}:{j}', origin='nutrient', actor=oid, nutrient=food, tick=tick) for j in range(3)]
                released = 7
                result.update(outcome='converted', returned=copy.deepcopy(credit))
    elif act == 4:
        result['targets'] = [] if oid is None else [oid]
        if obj is not None:
            s['objects'].pop(oid)
            for a in obj['atoms']:
                s['waste'][a] = dict(retired_id=oid, retired_tick=tick)
            released = len(obj['atoms'])-1+len(obj['tokens'])
            result.update(outcome='decayed', discarded=copy.deepcopy(obj['tokens']))
    elif act == 5:
        result['targets'] = [k for k in (oid, discarded_atom) if k is not None]
        if opportunities['reclaim_funded']:
            cost, released = 1, 1
            former = s['waste'].pop(discarded_atom)
            s['atoms'][discarded_atom]['reclaims'].append(dict(actor=oid, tick=tick, retired_id=former['retired_id']))
            s['ready'].append(discarded_atom)
            result['outcome'] = 'reclaimed'
    else:
        result['outcome'] = 'idle'
    if cost:
        result['spent'] = copy.deepcopy(account[:cost])
        del account[:cost]
    account.extend(credit)
    s['heat'] += released
    result.update(charged=cost, heat=released)
    if new_birth is not None:
        product = 'o'+str(tick)
        if product in old['history']:
            raise ValueError('Reused identity')
        s['objects'][product] = new_birth
        s['history'][product] = copy.deepcopy(new_birth)
        result['product'] = product
    return s, opportunities, result


def measure(initial, events, terminal):
    rows = [e['result'] for e in events]
    captures = {}
    for e in events:
        if e['result']['outcome'] == 'converted':
            captures.setdefault(e['result']['targets'][0], []).append(e['tick'])
    copy_functioned = {k for k in captures if terminal['history'][k]['origin'] == 'copy'}
    primary = {k for k in copy_functioned if terminal['history'][k]['own_funded'] and terminal['history'][k]['sequence_match']}
    renewed = set()
    for k in primary:
        h = terminal['history'][k]
        parent = terminal['history'][h['producer']]
        if parent['origin'] == 'copy' and parent['own_funded'] and parent['sequence_match'] and any(t < h['born_tick'] for t in captures.get(h['producer'], [])):
            renewed.add(k)
    return dict(ligations=sum(r['outcome'] == 'ligated' for r in rows), copies=sum(r['outcome'] == 'copied' for r in rows),
                own_funded_copies=sum(r['outcome'] == 'copied' and r['own_funded'] for r in rows),
                matching_copies=sum(r['outcome'] == 'copied' and r['sequence_match'] for r in rows),
                primary_children=len(primary), primary_conversion_events=sum(len(captures[k]) for k in primary), renewed_children=len(renewed),
                functional_copy_children=len(copy_functioned), conversions=sum(len(v) for v in captures.values()),
                paid_ghosts=sum(r['outcome'] == 'paid_ghost' for r in rows), decays=sum(r['outcome'] == 'decayed' for r in rows),
                reclaims=sum(r['outcome'] == 'reclaimed' for r in rows), charged=sum(r['charged'] for r in rows), returned=sum(len(r['returned']) for r in rows),
                endowed=sum(len(r['endowed']) for r in rows), starved_contacts=sum(r['outcome'] == 'starved' for r in rows),
                partial_contacts=sum(r['outcome'] == 'spent' and r['charged'] == 1 for r in rows),
                missing_food_contacts=sum(e['draw'][0] == 3 and not set(e['result']['targets']).intersection(initial['nutrients']) for e in events),
                unavailable=sum(r['outcome'] == 'unavailable' for r in rows),
                opportunities={k: sum(e['opportunities'][k] for e in events) for k in events[0]['opportunities']},
                terminal_work=len(terminal['bank'])+sum(len(o['tokens']) for o in terminal['objects'].values()), terminal_heat=terminal['heat'],
                terminal_bonds=sum(len(o['atoms'])-1 for o in terminal['objects'].values()), remaining_food=len(terminal['nutrients']),
                ready_atoms=len(terminal['ready']), waste_atoms=len(terminal['waste']))


def verify_record(record, seed, budget):
    if set(record) != {'seed', 'work_per_monomer', 'draws', 'arms'} or canonical([record['seed'], record['work_per_monomer']]) != canonical([seed, budget]) or len(record['arms']) != 5:
        raise ValueError('Seed/budget/arm identity')
    for mode, arm in zip(ARMS, record['arms']):
        state, draws = regenerate(seed, budget, mode)
        if set(arm) != {'mode', 'initial', 'events', 'terminal', 'statistics'} or arm['mode'] != mode or canonical(arm['initial']) != canonical(state) or canonical(record['draws']) != canonical(draws) or len(arm['events']) != 128:
            raise ValueError('Founder/request/denominator mismatch')
        total, chain = ledger(state), sha(state)
        for tick, draw in enumerate(draws):
            before = sha(state)
            state, opp, result = transition(state, mode, tick, draw)
            if ledger(state) != total:
                raise ValueError('Material/energy/work ownership divergence')
            event = dict(tick=tick, draw=draw, before=before, after=sha(state), previous=chain, opportunities=opp, result=result)
            event['sha256'] = sha(event)
            if canonical(arm['events'][tick]) != canonical(event):
                raise ValueError(f'Transition/cost/work provenance mismatch {seed}/{budget}/{mode}/{tick}')
            chain = event['sha256']
        if canonical(arm['terminal']) != canonical(state) or canonical(arm['statistics']) != canonical(measure(arm['initial'], arm['events'], state)):
            raise ValueError('Terminal/endpoint/statistics forgery')
    if canonical({k: v for k, v in record['arms'][0].items() if k != 'mode'}) != canonical({k: v for k, v in record['arms'][1].items() if k != 'mode'}):
        raise ValueError('Fixed law equality failed')


def summarize(records, revision):
    regimes = {}
    for work in (2, 0):
        panel = [r for r in records if r['work_per_monomer'] == work]
        totals = {}
        for index, mode in enumerate(ARMS):
            rows = [r['arms'][index]['statistics'] for r in panel]
            totals[mode] = {k: sum(row[k] for row in rows) for k, v in rows[0].items() if type(v) is int}
            totals[mode]['primary_worlds'] = sum(row['primary_children'] > 0 for row in rows)
            totals[mode]['copy_funding_worlds'] = sum(row['opportunities']['any_polymer_copy_work'] > 0 for row in rows)
            totals[mode]['opportunities'] = {k: sum(row['opportunities'][k] for row in rows) for k in rows[0]['opportunities']}
        contrasts = [dict(seed=r['seed'], difference=r['arms'][0]['statistics']['primary_children']-r['arms'][3]['statistics']['primary_children']) for r in panel]
        regimes[str(work)] = dict(arms=totals, active_vs_untemplated=contrasts)
    eligible = regimes['2']['arms']['active']['primary_worlds'] >= 4 and sum(c['difference'] > 0 for c in regimes['2']['active_vs_untemplated']) >= 4 and sum(c['difference'] for c in regimes['2']['active_vs_untemplated']) > 0
    return dict(schema='template02-summary-v1', revision=revision, source_sha256={p: hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in FILES},
                independent_initializations=16, paired_settings=32, correlated_histories=160, events=20480, regimes=regimes,
                admission_passed=eligible, decision='propose_separate_causal_protocol' if eligible else 'close_negative_neutral_pilot')


def audit(output, revision):
    if not isinstance(revision, str) or len(revision) != 40 or any(c not in '0123456789abcdef' for c in revision):
        raise ValueError('Exact revision required')
    output = Path(output)
    with (output/'records.jsonl').open('rb') as stream:
        raw = stream.read(64*1024*1024+1)
    if len(raw) > 64*1024*1024 or not raw.endswith(b'\n'):
        raise ValueError('Bounded complete records required')
    records = [json.loads(line, object_pairs_hook=unique) for line in raw.splitlines()]
    if len(records) != 32:
        raise ValueError('All starting world denominators required')
    for record, (seed, budget) in zip(records, itertools.product(range(128, 144), (2, 0))):
        verify_record(record, seed, budget)
    expected = summarize(records, revision)
    expected['records_sha256'] = hashlib.sha256(raw).hexdigest()
    if canonical(json.loads((output/'summary.json').read_bytes(), object_pairs_hook=unique)) != canonical(expected):
        raise ValueError('Source/summary mismatch')
    return dict(verified_revision=revision, verified_initializations=16, settings=32, histories=160, events=20480,
                exact_fixed_matches=32, conservation_and_work_provenance=True, admission_passed=expected['admission_passed'],
                records_sha256=expected['records_sha256'], no_evolution_claim=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input-dir', required=True)
    parser.add_argument('--source-revision', required=True)
    args = parser.parse_args()
    print(json.dumps(audit(args.input_dir, args.source_revision), sort_keys=True, indent=2))
