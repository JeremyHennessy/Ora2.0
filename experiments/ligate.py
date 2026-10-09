"""LIGATE-01 finite activated-chain chemistry, no controller or supplied founder."""
import argparse, copy, hashlib, json
from pathlib import Path

ARMS = ('candidate', 'inert', 'shuffled', 'constitutive')

def encode(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':')).encode()

def sequence(atoms):
    return ''.join(str(a // 16) for a in atoms)

def target(atoms):
    return hashlib.sha256(('LIGATE-01|' + sequence(atoms)).encode('ascii')).digest()[0] % 2

def draw(w):
    x = w['rng']; x ^= (x << 13) & 0xffffffff; x ^= x >> 17; x ^= (x << 5) & 0xffffffff
    w['rng'] = x & 0xffffffff
    return w['rng']

def new(seed, arm):
    if seed not in (*range(75000, 75032), 75999) or arm not in ARMS:
        raise ValueError('Unregistered sample')
    return dict(seed=seed, arm=arm, rng=seed, step=0, photons=256, heat=0,
                removed=0, objects=[dict(id=i, atoms=[i], alive=True, active=False,
                charge=None, parents=[], born=0, route='genesis') for i in range(32)],
                productive=[], opportunity=False, observation=None,
                stats=dict(activation=0, basal=0, catalytic=0, ligation=0, cleavage=0,
                           cross=0, reused=0, post_withdrawal=0), depleted_at=None)

def check(w):
    live = [o for o in w['objects'] if o['alive']]
    atoms = [a for o in live for a in o['atoms']]
    if sorted(atoms) != list(range(32)):
        raise ValueError('Material ownership')
    bound = sum(len(o['atoms']) - 1 + 2 * o['active'] for o in live)
    if w['photons'] + w['heat'] + w['removed'] + bound != 256 or min(w['photons'], w['heat'], w['removed']) < 0:
        raise ValueError('Energy residual/borrowing')
    for i, o in enumerate(w['objects']):
        if o['id'] != i or not 1 <= len(o['atoms']) <= 4 or len(set(o['atoms'])) != len(o['atoms']):
            raise ValueError('Identity/chain')
        if o['active'] and len(o['atoms']) != 1:
            raise ValueError('Activation substrate')
        if any(p >= i or p < 0 for p in o['parents']):
            raise ValueError('Parent chronology')

def create(w, atoms, parents, t, route):
    o = dict(id=len(w['objects']), atoms=atoms, alive=True, active=False,
             charge=None, parents=parents, born=t, route=route)
    w['objects'].append(o)
    return o

def observe(w):
    live = [o for o in w['objects'] if o['alive'] and o['id'] in w['productive']]
    kinds = sorted({sequence(o['atoms']) for o in live})
    w['observation'] = dict(live_productive_sequences=kinds, cross=w['stats']['cross'])
    w['opportunity'] = len(kinds) >= 2 and w['stats']['cross'] >= 4

def tick(w, t, d):
    event = None
    if t == 1024:
        observe(w)
    if t == 1536:
        w['removed'] += w['photons']; w['photons'] = 0
    live = [o for o in w['objects'] if o['alive']]
    a, b, c = (live[d[i] % len(live)] for i in (1, 2, 3))
    byte = d[4] % 256
    channel = d[0] % 3
    if channel == 0 and len(a['atoms']) == 1 and not a['active'] and w['photons'] >= 3:
        compatible = c['id'] != a['id'] and len(c['atoms']) >= 2 and target(c['atoms']) == a['atoms'][0] // 16
        if w['arm'] == 'shuffled':
            compatible = c['id'] != a['id'] and len(c['atoms']) >= 2 and target(c['atoms']) != a['atoms'][0] // 16
        if w['arm'] == 'inert':
            compatible = False
        threshold = 64 if compatible or w['arm'] == 'constitutive' else 8
        if byte < threshold:
            donor = c['id'] if compatible and byte >= 8 and w['arm'] != 'constitutive' else None
            a['active'] = True; a['charge'] = dict(donor=donor, step=t)
            w['photons'] -= 3; w['heat'] += 1; w['stats']['activation'] += 1
            w['stats']['catalytic' if donor is not None else 'basal'] += 1
            event = ['activate', a['id'], donor]
    elif channel == 1 and a['id'] != b['id'] and a['active'] != b['active'] and len(a['atoms']) + len(b['atoms']) <= 4 and byte < 128:
        active, other = (a, b) if a['active'] else (b, a)
        atoms = active['atoms'] + other['atoms'] if d[5] % 2 == 0 else other['atoms'] + active['atoms']
        o = create(w, atoms, [active['id'], other['id']], t, 'ligation')
        o['funding'] = copy.deepcopy(active['charge'])
        a['alive'] = b['alive'] = False; w['heat'] += 1; w['stats']['ligation'] += 1
        if t >= 1536: w['stats']['post_withdrawal'] += 1
        if any(x['route'] == 'cleavage' for x in (a, b)): w['stats']['reused'] += 1
        donor = o['funding']['donor']
        if donor is not None and sequence(w['objects'][donor]['atoms']) != sequence(atoms):
            w['stats']['cross'] += 1
            if donor not in w['productive']: w['productive'].append(donor); w['productive'].sort()
        event = ['ligate', o['id'], active['id'], other['id'], donor]
    elif channel == 2 and len(a['atoms']) >= 2 and not a['active'] and byte < 8:
        cut = 1 + d[5] % (len(a['atoms']) - 1)
        left = create(w, a['atoms'][:cut], [a['id']], t, 'cleavage')
        right = create(w, a['atoms'][cut:], [a['id']], t, 'cleavage')
        a['alive'] = False; w['heat'] += 1; w['stats']['cleavage'] += 1
        event = ['cleave', a['id'], left['id'], right['id'], cut]
    if w['depleted_at'] is None and w['photons'] < 3:
        w['depleted_at'] = t
    w['step'] = t; check(w)
    return event

def run(seed, arm, revision):
    w = new(seed, arm)
    rows = [encode(dict(schema='ligate01', revision=revision, seed=seed, arm=arm)) + b'\n']
    for t in range(1, 2049):
        d = [draw(w) for _ in range(6)]; event = tick(w, t, d)
        rows.append(encode(dict(step=t, draws=d, event=event, state=hashlib.sha256(encode(w)).hexdigest())) + b'\n')
    return b''.join(rows), w

def main():
    p = argparse.ArgumentParser(); p.add_argument('--output', required=True); p.add_argument('--revision', required=True)
    p.add_argument('--start', type=int, default=75000); p.add_argument('--count', type=int, default=32)
    args = p.parse_args()
    from .evidence_budget import Budget
    b = Budget(args.output, dict(raw=128*1024**2, archive=64*1024**2, restore=128*1024**2, failure=8*1024**2), 328*1024**2)
    try:
        for seed in range(args.start, args.start + args.count):
            for arm in ARMS:
                rows, w = run(seed, arm, args.revision)
                with b.create('raw', f'{seed}-{arm}.jsonl') as f: f.write(rows)
                with b.create('raw', f'{seed}-{arm}-final.json') as f: f.write(encode(w))
    finally:
        with b.create('failure', 'budget.json', 1024**2) as f:
            f.write(encode(copy.deepcopy(b.snapshot())))

if __name__ == '__main__': main()
