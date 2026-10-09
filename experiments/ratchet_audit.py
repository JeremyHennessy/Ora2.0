"""Independent RATCHET-01 DFS interpreter and exact rational-rate audit."""
import argparse
from fractions import Fraction
import hashlib
import itertools
import json
from math import comb
from pathlib import Path


def energy_heat(s):
    return 142 - 6*s[0] - s[2] - int(s[1] == 1)


def proposals(s, arm):
    f, q, load, replaced = s
    table = {0:(0,1), 1:(1,2), 2:(2,0), 3:(0,1), 4:(2,1)}
    out = []
    for c, pair in table.items():
        if c in (0,4) and (arm == 'equilibrium' or c == 4 and arm != 'isotropic'):
            continue
        for d in (-1,1):
            start, end = pair if d == 1 else pair[::-1]
            independent = c == 2 and arm == 'uncoupled'
            if q != start and not independent:
                continue
            target = (f-d if c in (0,4) else f, q if independent else end,
                      load+d if c == 2 else load, replaced)
            if target[0] in range(17) and target[2] >= 0 and energy_heat(target) >= 0:
                out.append(((c,d),target))
    if not replaced and load >= 7:
        out.append(((5,1),(f,0,load-7,1)))
    return out


def qualifies(s):
    return s[3] == 1 and s[2] >= 17 and energy_heat(s) >= 32


def inspect_witness(value, arm):
    s = (16,0,10,0)
    states = [list(s)+[energy_heat(s)]]
    objects = [dict(id=0, atoms=[0,1,2], parent=None, construction_work=6, alive=True)]
    tokens = [dict(id=i, state='F', transformations=[]) for i in range(16)]
    events = []
    for i, action in enumerate(value['path']):
        alternatives = dict(proposals(s,arm))
        if tuple(action) not in alternatives:
            raise ValueError('Impossible witness')
        new = alternatives[tuple(action)]
        c,d = action
        identity = None
        if c in (0,4):
            old, fresh = ('F','W') if d > 0 else ('W','F')
            identity = min(t['id'] for t in tokens if t['state'] == old)
            tokens[identity]['state'] = fresh
            tokens[identity]['transformations'].append(dict(event=i,machine=objects[-1]['id'],route=action))
        if c == 5:
            objects[0]['alive'] = False
            objects.append(dict(id=1, atoms=[0,1,2], parent=0, construction_work=6, destruction_work=1, alive=True))
        events.append(dict(action=action,token=identity,machine=objects[-1]['id']))
        s = new
        states.append(list(s)+[energy_heat(s)])
    expected = dict(path=value['path'],snapshots=states,events=events,objects=objects,tokens=tokens,
                    total_energy=144,structural_atoms=[0,1,2],initial_work=16,initial_heat=32,
                    startup_work=6,replacement_work=7 if s[3] else 0,endpoint=qualifies(s))
    if value != expected or not qualifies(s):
        raise ValueError('Ledger/identity/endpoint witness mismatch')
    return s


def graph(arm):
    start = (16,0,10,0)
    pending = [start]
    seen = {start}
    edges = physical = 0
    signatures = set()
    while pending:
        s = pending.pop()
        for action, t in proposals(s,arm):
            edges += 1
            c,d = action
            if c < 5:
                physical += 1
                if ((c,-d),s) not in proposals(t,arm):
                    raise ValueError('Missing physical reverse')
                signatures.add((s[0],c,d,energy_heat(t)-energy_heat(s)))
            if t not in seen:
                seen.add(t)
                pending.append(t)
            if len(seen) > 60000 or edges > 2000000:
                raise ValueError('Exhaustive enumeration cap')
    checked = 0
    for f,c,d,dh in signatures:
        chemical = c in (0,4)
        nf = f-d if chemical else f
        forward = f if d == 1 else 16-f
        backward = 16-nf if d == 1 else nf
        if not chemical:
            forward = backward = 16
        for barriers in itertools.product(range(4),repeat=3):
            b = barriers[0 if chemical else 2 if c == 2 else 1]
            if chemical and arm == 'isotropic':
                b += 1
            p = Fraction(forward,160*2**(b+max(0,-dh)))
            reverse = Fraction(backward,160*2**(b+max(0,dh)))
            ratio = Fraction(comb(16,nf),comb(16,f)) * (Fraction(2**dh) if dh >= 0 else Fraction(1,2**(-dh)))
            if not 0 < p <= Fraction(1,10) or p/reverse != ratio:
                raise ValueError('Thermodynamic ratio/probability')
            checked += 1
    canonical = json.dumps(sorted(seen),sort_keys=True,separators=(',',':')).encode()
    return dict(states=len(seen),edges=edges,physical_edges=physical,
                state_sha256=hashlib.sha256(canonical).hexdigest(),endpoint_states=sum(qualifies(s) for s in seen),
                rate_signatures=len(signatures),barrier_checks=checked)


def audit(value, revision):
    if value['schema'] != 'ratchet01-feasibility' or value['source_revision'] != revision or value['natural_worlds'] != 0 or value['barrier_laws'] != 64:
        raise ValueError('Frozen header')
    arms = ('candidate','uncoupled','isotropic','equilibrium')
    if [r['arm'] for r in value['records']] != list(arms):
        raise ValueError('Missing/duplicate arm')
    rows = []
    for r in value['records']:
        arm = r['arm']
        expected = graph(arm)
        if any(r[k] != v for k,v in expected.items()):
            raise ValueError('Complete graph/rate digest mismatch')
        if expected['endpoint_states']:
            inspect_witness(r['witness'],arm)
        elif r['witness'] is not None:
            raise ValueError('Invented witness')
        rows.append(dict(arm=arm,**expected))
    certificate = value['forward_cycle_certificate']
    if certificate['path'] != [[0,1],[1,1],[2,1]]*7+[[5,1]]+[[0,1],[1,1],[2,1]]*7:
        raise ValueError('Registered cycle certificate')
    if inspect_witness(certificate,'candidate') != (2,0,17,1) or certificate['snapshots'][-1][-1] != 113:
        raise ValueError('Whole-cost cycle certificate')
    gate = all(r['endpoint_states'] > 0 for r in rows[:3]) and rows[3]['endpoint_states'] == 0
    return dict(verified=True,source_revision=revision,records=rows,feasibility_pass=gate,
                natural_worlds=0,autonomous_self_maintenance=False,kinetic_superiority_tested=False,
                certificate_final=certificate['snapshots'][-1],
                decision='CONTROLLED WORK FEASIBLE; kinetics and founder-free origin untested' if gate else 'STOP: feasibility/control gate failed')


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--input',required=True)
    p.add_argument('--revision',required=True)
    a = p.parse_args()
    try:
        print(json.dumps(audit(json.loads(Path(a.input).read_bytes()),a.revision),sort_keys=True))
    except (ValueError,KeyError,IndexError,TypeError) as e:
        print(json.dumps(dict(verified=False,error=str(e))))
        raise SystemExit(2)


if __name__ == '__main__':
    main()
