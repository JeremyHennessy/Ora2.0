"""Independent TEMPLATE-01 interpreter and authored-case audit; no worker import."""
import argparse
import copy
import hashlib
import itertools
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FILES = ('docs/TEMPLATE-01-PROTOCOL.md', 'experiments/template_feasibility.py',
         'experiments/template_feasibility_audit.py')


def canonical(v):
    return json.dumps(v, sort_keys=True, separators=(',', ':'))


def digest(v):
    return hashlib.sha256(canonical(v).encode()).hexdigest()


def unique(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError('Duplicate JSON key')
        result[key] = value
    return result


def ledger(s):
    ids = s['ready'] + s['waste'] + list(s['nutrients'])
    work, bonds = s['bank'], 0
    if type(work) is not int or work < 0 or type(s['heat']) is not int or s['heat'] < 0:
        raise ValueError('Invalid energy')
    for o in s['objects'].values():
        if type(o['work']) is not int or o['work'] < 0 or o['bits'] != ''.join(s['atoms'][a]['bit'] for a in o['atoms']):
            raise ValueError('Object energy or sequence')
        ids += o['atoms']
        work += o['work']
        bonds += len(o['atoms'])-1
    if len(ids) != len(set(ids)) or set(ids) != set(s['atoms']):
        raise ValueError('Lost/duplicated/invented atom')
    if any(a['bit'] not in ('0', '1') for a in s['atoms'].values()):
        raise ValueError('Invalid bit')
    return (sum(s['atoms'][a]['bit'] == '0' for a in ids), sum(s['atoms'][a]['bit'] == '1' for a in ids),
            work+s['heat']+bonds+8*len(s['nutrients']))


def initial(bits, work=2, mode='active'):
    n = len(bits)
    atoms = {f'a{i:03d}': dict(bit=b, origin='external_genesis') for i, b in enumerate(bits+'0'*(2*n)+'1'*(2*n))}
    ready = list(atoms)[n:]
    birth = dict(bits=bits, atoms=list(atoms)[:n], template_parent=None, born=0)
    obj = {**copy.deepcopy(birth), 'work': 0 if mode == 'shared' else work}
    food = {}
    for i in range(8*n+8):
        aid = f'f{i:03d}'
        atoms[aid] = dict(bit=str(1-int(bits[-1])), origin='external_nutrient')
        food[aid] = aid
    return dict(atoms=atoms, ready=ready, waste=[], nutrients=food, objects={'p0': obj},
                history={'p0': birth}, heat=0, bank=work if mode == 'shared' else 0, next_id=1)


def transition(old, mode, request, tick):
    s = copy.deepcopy(old)
    oid = request['owner']
    result = dict(outcome='unavailable', charged=0, heat=0, returned=0, endowment=0,
                  product=None, consumed=[], template_parent=None)
    if oid not in old['objects']:
        return s, result
    original = old['objects'][oid]
    account = old['bank'] if mode == 'shared' else original['work']
    kind = request['action']
    charge, released, returned = 0, 0, 0
    if kind == 'contact':
        charge = min(2, account)
        released = charge
        result['outcome'] = 'spent' if charge else 'starved'
        aid = request.get('nutrient')
        if charge == 2 and aid in old['nutrients'] and len(original['atoms']) > 1 and int(original['bits'][-1])+int(old['atoms'][aid]['bit']) == 1:
            s['nutrients'].pop(aid)
            s['waste'].append(aid)
            returned, released = 3, 7
            result.update(outcome='converted', consumed=[aid])
    elif kind == 'copy':
        n = len(original['atoms'])
        remaining = sorted(old['ready'])
        selected = []
        for bit in original['bits']:
            match = next((a for a in remaining if mode == 'untemplated' or old['atoms'][a]['bit'] == bit), None)
            if match is None:
                break
            remaining.remove(match)
            selected.append(match)
        if len(selected) == n and account >= 3*n+1:
            charge = 3*n+1
            if mode == 'ghost':
                released = charge
                result['outcome'] = 'paid_ghost'
            else:
                released = 2*n
                product = f"p{old['next_id']}"
                if product in old['history']:
                    raise ValueError('Reused object ID')
                parent = None if mode == 'untemplated' else oid
                birth = dict(bits=''.join(old['atoms'][a]['bit'] for a in selected), atoms=selected, template_parent=parent, born=tick)
                s['history'][product] = copy.deepcopy(birth)
                s['objects'][product] = {**birth, 'work': 0 if mode == 'shared' else 2}
                s['next_id'] += 1
                s['ready'] = [a for a in old['ready'] if a not in selected]
                if mode == 'shared':
                    s['bank'] += 2
                result.update(outcome='copied', product=product, consumed=selected, template_parent=parent, endowment=2)
    elif kind == 'decay':
        s['objects'].pop(oid)
        s['waste'] += original['atoms']
        released = len(original['atoms'])-1+original['work']
        result.update(outcome='decayed', consumed=original['atoms'])
    elif kind == 'reclaim':
        aid = request.get('atom')
        if aid in old['waste'] and account >= 1:
            s['waste'].remove(aid)
            s['ready'].append(aid)
            charge, released = 1, 1
            result.update(outcome='reclaimed', consumed=[aid])
    else:
        raise ValueError('Unknown action')
    if mode == 'shared':
        s['bank'] += returned-charge
    elif kind != 'decay':
        s['objects'][oid]['work'] += returned-charge
    s['heat'] += released
    result.update(charged=charge, heat=released, returned=returned)
    return s, result


def expected_specs():
    for n in (2, 3, 4):
        for letters in itertools.product('01', repeat=n):
            bits = ''.join(letters)
            contacts = lambda owner, start: [dict(action='contact', owner=owner, nutrient=f'f{i:03d}') for i in range(start, start+3*n-1)]
            for mode in ('active', 'ghost', 'untemplated', 'shared'):
                actions = contacts('p0', 0)+[dict(action='copy', owner='p0')]+contacts('p1', 3*n-1)+[dict(action='copy', owner='p1')]
                yield bits, mode, 'generations', initial(bits, mode=mode), actions
            for work in (3*n, 3*n+1, 3*n+2):
                yield bits, 'active', 'copy-budget-'+str(work), initial(bits, work), [dict(action='copy', owner='p0')]
            for work in (0, 1):
                yield bits, 'active', 'contact-budget-'+str(work), initial(bits, work), [dict(action='contact', owner='p0', nutrient='f000')]
            for label, ready_count in (('missing-feed', 0), ('insufficient-feed', n-1)):
                s = initial(bits, 3*n+1)
                s['waste'] = s['ready'][ready_count:]
                s['ready'] = s['ready'][:ready_count]
                yield bits, 'active', label, s, [dict(action='copy', owner='p0')]
            s = initial(bits, 3*n+1)
            for a in s['ready']:
                s['atoms'][a]['bit'] = str(1-int(bits[0]))
            yield bits, 'active', 'wrong-feed', s, [dict(action='copy', owner='p0')]
            s = initial(bits)
            s['atoms']['f000']['bit'] = bits[-1]
            yield bits, 'active', 'nonmatching-food', s, [dict(action='contact', owner='p0', nutrient='f000')]
            s = initial(bits, 4*n+3)
            actions = [dict(action='copy', owner='p0'), dict(action='decay', owner='p1')]
            after, result = transition(s, 'active', actions[0], 1)
            recovered = result['consumed']
            actions += [dict(action='reclaim', owner='p0', atom=a) for a in recovered]
            actions += contacts('p0', 0)+[dict(action='copy', owner='p0')]
            yield bits, 'active', 'regeneration', s, actions


def verify(record, spec):
    bits, mode, label, s, actions = spec
    if set(record) != {'bits', 'mode', 'label', 'initial', 'events', 'terminal'} or canonical([record['bits'], record['mode'], record['label'], record['initial']]) != canonical([bits, mode, label, s]):
        raise ValueError('Authored case identity/initial mismatch')
    if len(record['events']) != len(actions):
        raise ValueError('Missing/extra events')
    budget = ledger(s)
    for tick, (request, event) in enumerate(zip(actions, record['events']), 1):
        before = digest(s)
        s, result = transition(s, mode, request, tick)
        if ledger(s) != budget:
            raise ValueError('Material/energy violation')
        expected = dict(tick=tick, action=request, result=result, before=before, after=digest(s))
        if canonical(event) != canonical(expected):
            raise ValueError('Forged action/cost/state')
    if canonical(record['terminal']) != canonical(s):
        raise ValueError('Forged terminal/provenance')
    if label == 'generations' and mode == 'active':
        if set(s['objects']) != {'p0', 'p1', 'p2'} or any(o['bits'] != bits for o in s['objects'].values()) or s['history']['p1']['template_parent'] != 'p0' or s['history']['p2']['template_parent'] != 'p1':
            raise ValueError('Two paid matching generations failed')
    if label == 'regeneration':
        if s['history']['p1']['atoms'] != s['history']['p2']['atoms'] or 'p1' in s['objects']:
            raise ValueError('Paid regeneration failed')


def audit(output, revision):
    if not isinstance(revision, str) or len(revision) != 40 or any(c not in '0123456789abcdef' for c in revision):
        raise ValueError('Exact source revision required')
    output = Path(output)
    with (output/'records.jsonl').open('rb') as stream:
        raw = stream.read(32*1024*1024+1)
    if len(raw) > 32*1024*1024 or not raw.endswith(b'\n'):
        raise ValueError('Bounded complete evidence required')
    records = [json.loads(line, object_pairs_hook=unique) for line in raw.splitlines()]
    specs = list(expected_specs())
    if len(records) != len(specs):
        raise ValueError('All authored denominators required')
    for record, spec in zip(records, specs):
        verify(record, spec)
    expected = dict(schema='template01-feasibility-v1', revision=revision, authored=True, natural_worlds=0,
                    records=len(specs), records_sha256=hashlib.sha256(raw).hexdigest(),
                    source_sha256={p: hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in FILES})
    if canonical(json.loads((output/'manifest.json').read_bytes(), object_pairs_hook=unique)) != canonical(expected):
        raise ValueError('Source/manifest mismatch')
    modes = {}
    for mode in ('active', 'ghost', 'untemplated', 'shared'):
        rows = [r for r in records if r['label'] == 'generations' and r['mode'] == mode]
        modes[mode] = dict(starting_templates=len(rows), first_products=sum('p1' in r['terminal']['objects'] for r in rows),
                           second_products=sum('p2' in r['terminal']['objects'] for r in rows),
                           first_sequence_matches=sum(r['terminal']['objects'].get('p1', {}).get('bits') == r['bits'] for r in rows),
                           second_sequence_matches=sum(r['terminal']['objects'].get('p2', {}).get('bits') == r['bits'] for r in rows),
                           nutrient_conversions=sum(e['result']['outcome'] == 'converted' for r in rows for e in r['events']))
    return dict(verified_revision=revision, authored_cases=len(records), independent_natural_initializations=0,
                active_templates=28, modes=modes, conservation_verified=True, feasibility_passed=True,
                reserved_samples_executed=False, claim='Installed mechanism feasible in authored schedules; no naturally realized reproduction or evolution')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input-dir', required=True)
    parser.add_argument('--source-revision', required=True)
    args = parser.parse_args()
    print(json.dumps(audit(args.input_dir, args.source_revision), sort_keys=True, indent=2))
