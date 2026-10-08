"""Authored TEMPLATE-01 feasibility, never a natural-emergence sample."""
import argparse
import copy
import hashlib
import itertools
import json
from pathlib import Path

MODES = ('active', 'ghost', 'untemplated', 'shared')
ROOT = Path(__file__).resolve().parents[1]
FILES = ('docs/TEMPLATE-01-PROTOCOL.md', 'experiments/template_feasibility.py',
         'experiments/template_feasibility_audit.py')


def encode(v):
    return json.dumps(v, sort_keys=True, separators=(',', ':'))


def sha(v):
    return hashlib.sha256(encode(v).encode()).hexdigest()


def fixture(bits, work=2, mode='active'):
    n = len(bits)
    s = dict(atoms={}, ready=[], waste=[], nutrients={}, objects={}, history={}, heat=0,
             bank=work if mode == 'shared' else 0, next_id=1)
    for i, bit in enumerate(bits + '0' * (2*n) + '1' * (2*n)):
        s['atoms'][f'a{i:03d}'] = dict(bit=bit, origin='external_genesis')
    ids = list(s['atoms'])
    s['ready'] = ids[n:]
    parent = dict(bits=bits, atoms=ids[:n], work=0 if mode == 'shared' else work,
                  template_parent=None, born=0)
    s['objects']['p0'] = copy.deepcopy(parent)
    s['history']['p0'] = {k: v for k, v in parent.items() if k != 'work'}
    for i in range(8*n+8):
        aid = f'f{i:03d}'
        s['atoms'][aid] = dict(bit=str(1-int(bits[-1])), origin='external_nutrient')
        s['nutrients'][aid] = aid
    return s


def step(old, mode, action, tick):
    s = copy.deepcopy(old)
    kind, owner = action['action'], action['owner']
    obj = s['objects'].get(owner)
    result = dict(outcome='unavailable', charged=0, heat=0, returned=0, endowment=0,
                  product=None, consumed=[], template_parent=None)
    if obj is None:
        return s, result
    def balance():
        return s['bank'] if mode == 'shared' else obj['work']
    def debit(amount, heat):
        if mode == 'shared':
            s['bank'] -= amount
        else:
            obj['work'] -= amount
        s['heat'] += heat
        result['charged'] += amount
        result['heat'] += heat
    if kind == 'contact':
        charge = min(2, balance())
        debit(charge, charge)
        aid = action.get('nutrient')
        result['outcome'] = 'spent' if charge else 'starved'
        if charge == 2 and aid in s['nutrients'] and len(obj['bits']) >= 2 and obj['bits'][-1] != s['atoms'][aid]['bit']:
            del s['nutrients'][aid]
            s['waste'].append(aid)
            if mode == 'shared':
                s['bank'] += 3
            else:
                obj['work'] += 3
            s['heat'] += 5
            result.update(outcome='converted', returned=3, heat=charge+5, consumed=[aid])
    elif kind == 'copy':
        n = len(obj['bits'])
        price = 3*n+1
        available = sorted(s['ready'])
        selected = []
        for bit in obj['bits']:
            candidates = available if mode == 'untemplated' else [a for a in available if s['atoms'][a]['bit'] == bit]
            if not candidates:
                break
            atom = candidates[0]
            selected.append(atom)
            available.remove(atom)
        if len(selected) != n or balance() < price:
            return s, result
        if mode == 'ghost':
            debit(price, price)
            result['outcome'] = 'paid_ghost'
        else:
            debit(price, 2*n)
            oid = 'p'+str(s['next_id'])
            s['next_id'] += 1
            parent = None if mode == 'untemplated' else owner
            child = dict(bits=''.join(s['atoms'][a]['bit'] for a in selected), atoms=selected,
                         work=0 if mode == 'shared' else 2, template_parent=parent, born=tick)
            s['objects'][oid] = child
            s['history'][oid] = {k: copy.deepcopy(v) for k, v in child.items() if k != 'work'}
            if mode == 'shared':
                s['bank'] += 2  # Explicit endowment routes to the common bank.
            for aid in selected:
                s['ready'].remove(aid)
            result.update(outcome='copied', product=oid, consumed=selected, template_parent=parent, endowment=2)
    elif kind == 'decay':
        del s['objects'][owner]
        s['waste'].extend(obj['atoms'])
        heat = len(obj['bits'])-1+obj['work']
        s['heat'] += heat
        result.update(outcome='decayed', heat=heat, consumed=obj['atoms'])
    elif kind == 'reclaim':
        aid = action.get('atom')
        if aid in s['waste'] and balance() >= 1:
            debit(1, 1)
            s['waste'].remove(aid)
            s['ready'].append(aid)
            result.update(outcome='reclaimed', consumed=[aid])
    else:
        raise ValueError('Unknown action')
    return s, result


def schedule(bits):
    count = 3*len(bits)-1
    return ([dict(action='contact', owner='p0', nutrient=f'f{i:03d}') for i in range(count)] +
            [dict(action='copy', owner='p0')] +
            [dict(action='contact', owner='p1', nutrient=f'f{i+count:03d}') for i in range(count)] +
            [dict(action='copy', owner='p1')])


def run_case(bits, mode, label, initial, actions):
    s = copy.deepcopy(initial)
    events = []
    for tick, action in enumerate(actions, 1):
        before = sha(s)
        s, result = step(s, mode, action, tick)
        events.append(dict(tick=tick, action=action, result=result, before=before, after=sha(s)))
    return dict(bits=bits, mode=mode, label=label, initial=initial, events=events, terminal=s)


def cases():
    for n in range(2, 5):
        for chars in itertools.product('01', repeat=n):
            bits = ''.join(chars)
            for mode in MODES:
                yield run_case(bits, mode, 'generations', fixture(bits, mode=mode), schedule(bits))
            for work in (3*n, 3*n+1, 3*n+2):
                yield run_case(bits, 'active', 'copy-budget-'+str(work), fixture(bits, work), [dict(action='copy', owner='p0')])
            for work in (0, 1):
                yield run_case(bits, 'active', 'contact-budget-'+str(work), fixture(bits, work), [dict(action='contact', owner='p0', nutrient='f000')])
            bad = fixture(bits, 3*n+1)
            bad['ready'] = []
            bad['waste'] = [a for a in bad['atoms'] if a.startswith('a')][n:]
            yield run_case(bits, 'active', 'missing-feed', bad, [dict(action='copy', owner='p0')])
            wrong = fixture(bits, 3*n+1)
            wrong['ready'] = wrong['ready'][:n-1]
            wrong['waste'] = [a for a in wrong['atoms'] if a.startswith('a')][n:][n-1:]
            yield run_case(bits, 'active', 'insufficient-feed', wrong, [dict(action='copy', owner='p0')])
            wrong_bits = fixture(bits, 3*n+1)
            for aid in wrong_bits['ready']:
                wrong_bits['atoms'][aid]['bit'] = str(1-int(bits[0]))
            yield run_case(bits, 'active', 'wrong-feed', wrong_bits, [dict(action='copy', owner='p0')])
            mismatch = fixture(bits)
            mismatch['atoms']['f000']['bit'] = bits[-1]
            yield run_case(bits, 'active', 'nonmatching-food', mismatch, [dict(action='contact', owner='p0', nutrient='f000')])
            initial = fixture(bits, 4*n+3)
            prefix = [dict(action='copy', owner='p0'), dict(action='decay', owner='p1')]
            temporary = run_case(bits, 'active', 'temporary', initial, prefix)['terminal']
            # Regenerated IDs are reused as material, never as object IDs.
            recycled = temporary['history']['p1']['atoms']
            actions = prefix + [dict(action='reclaim', owner='p0', atom=a) for a in recycled]
            actions += [dict(action='contact', owner='p0', nutrient=f'f{i:03d}') for i in range(3*n-1)]
            actions += [dict(action='copy', owner='p0')]
            yield run_case(bits, 'active', 'regeneration', initial, actions)


def run(output, revision):
    if len(revision) != 40 or any(c not in '0123456789abcdef' for c in revision):
        raise ValueError('Exact revision required')
    output = Path(output)
    output.mkdir(parents=True, exist_ok=False)
    records = list(cases())
    raw = (''.join(encode(r)+'\n' for r in records)).encode()
    (output/'records.jsonl').write_bytes(raw)
    manifest = dict(schema='template01-feasibility-v1', revision=revision, authored=True,
                    natural_worlds=0, records=len(records), records_sha256=hashlib.sha256(raw).hexdigest(),
                    source_sha256={p: hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in FILES})
    (output/'manifest.json').write_bytes((encode(manifest)+'\n').encode())


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output-dir', required=True)
    parser.add_argument('--source-revision', required=True)
    args = parser.parse_args()
    run(args.output_dir, args.source_revision)
