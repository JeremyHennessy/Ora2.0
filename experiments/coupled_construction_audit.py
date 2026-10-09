"""Separate COUPLE-01 interpreter and full DFS closure; no producer import."""
import argparse
import json
from pathlib import Path


def following(x, topology, mode):
    phase, light, fa, fb, ra, rb, wa, wb, ca, cb = x
    if phase and ca and cb:
        return []
    if not phase and ca and cb:
        return [('damage', (1, 0 if mode == 'withdrawal' else light, fa, fb, 0, 0, 2, 2, 0, 0))]
    result = []
    # Independently implement each stoichiometric vector, in reverse material order.
    for j in (1, 0):
        if light > 2:
            rules = [(f'basal-{j}', 1)]
            if mode == 'background':
                rules.append((f'background-{j}', 2))
            elif mode != 'inert':
                for i in (1, 0):
                    if (ca, cb)[i] == 1 and (topology >> (i*2+j)) & 1:
                        rules.append((f'catalytic-{i}-{j}', 2))
            for name, yield_fuel in rules:
                result.append((name, (phase, light-3, fa+(yield_fuel if j == 0 else 0),
                                     fb+(yield_fuel if j == 1 else 0), ra, rb, wa, wb, ca, cb)))
        fuel = (fa, fb)[j]
        if (ra, rb)[j] == 2 and fuel > 2:
            result.append((f'manufacture-{j}',
                           (phase, light, fa-(3 if j == 0 else 0), fb-(3 if j == 1 else 0),
                            0 if j == 0 else ra, 0 if j == 1 else rb, wa, wb,
                            1 if j == 0 else ca, 1 if j == 1 else cb)))
        if mode != 'no-recycling' and (wa, wb)[j] == 2 and fuel > 0:
            result.append((f'recycle-{j}',
                           (phase, light, fa-(1 if j == 0 else 0), fb-(1 if j == 1 else 0),
                            2 if j == 0 else ra, 2 if j == 1 else rb,
                            0 if j == 0 else wa, 0 if j == 1 else wb, ca, cb)))
    return result


def closure(mask, energy, arm):
    start = (0, energy, 0, 0, 2, 2, 0, 0, 0, 0)
    found = {start}
    pending = [start]
    edges = 0
    success = False
    while pending:
        x = pending.pop()
        success |= bool(x[0] == 1 and x[-2:] == (1, 1))
        for _, y in following(x, mask, arm):
            edges += 1
            if y not in found:
                if len(found) >= 200000:
                    raise ValueError('State ceiling')
                found.add(y)
                pending.append(y)
    return success, len(found), edges


def interpret(w, case):
    x = (0, case['photons'], 0, 0, 2, 2, 0, 0, 0, 0)
    objects, history, current = [], [[], []], [None, None]
    heat = removed = 0
    rows = w['rows']
    if rows[0] != dict(state=list(x), heat=0, removed=0, current=current, objects=[]):
        raise ValueError('Genesis mismatch')
    actions = []
    for row in rows[1:]:
        action = row['action']
        actions.append(action)
        options = dict(following(x, case['mask'], case['arm']))
        if action not in options:
            raise ValueError('Illegal or unfunded action')
        if action == 'damage':
            if any(v is None for v in current):
                raise ValueError('Missing damage subject')
            heat += 2
            removed += x[1] if case['arm'] == 'withdrawal' else 0
            current = [None, None]
        elif action.startswith('manufacture-'):
            j = int(action[-1])
            new_id = len(objects)
            objects.append(dict(id=new_id, kind=j, atoms=[2*j, 2*j+1],
                                previous_objects=history[j].copy()))
            history[j].append(new_id)
            current[j] = new_id
            heat += 2
        elif action.startswith('basal-'):
            heat += 2
        else:
            heat += 1
        x = options[action]
        if any(type(v) is not int or v < 0 for v in x):
            raise ValueError('Invalid inventory')
        for j in (0, 1):
            if x[4+j]+x[6+j]+2*x[8+j] != 2:
                raise ValueError('Material conservation')
        if x[1]+x[2]+x[3]+x[8]+x[9]+heat+removed != case['photons']:
            raise ValueError('Energy conservation')
        expected = dict(action=action, state=list(x), heat=heat, removed=removed,
                        current=current, objects=objects)
        if row != expected:
            raise ValueError('State, payment, identity or atom provenance mismatch')
    if actions != case['actions'] or not (x[0] == 1 and x[8:] == (1, 1)):
        raise ValueError('Endpoint/path mismatch')
    if len(objects) != 4 or set(current) & {0, 1}:
        raise ValueError('Old object reused as reconstruction')


def audit(data, revision):
    arms = ('network', 'inert', 'background', 'withdrawal', 'no-recycling')
    expected = {(m, p, a) for m in range(16) for p in range(0, 37, 3) for a in arms}
    actual = [(c['mask'], c['photons'], c['arm']) for c in data['cases']]
    if len(actual) != 1040 or set(actual) != expected or data['source_revision'] != revision:
        raise ValueError('Scope, duplicates or source mismatch')
    if data['schema'] != 'couple01-feasibility-v1' or data['continuous'] is not False or data['scope'] != 'exhaustive authored reachability, NOT natural dynamics':
        raise ValueError('Scope claim mismatch')
    states = edges = 0
    cases = {}
    for c in data['cases']:
        success, n, e = closure(c['mask'], c['photons'], c['arm'])
        if (success, n, e) != (c['feasible'], c['states'], c['edges']):
            raise ValueError('Independent reachability mismatch')
        if success and (c['photons'] < 14 or c['arm'] == 'no-recycling'):
            raise ValueError('Accounting falsifier')
        if not success and c['actions']:
            raise ValueError('Infeasible case claims actions')
        states += n
        edges += e
        cases[c['mask'], c['photons'], c['arm']] = c
    minima = []
    witness_keys = set()
    for m in range(16):
        values = {}
        for a in arms:
            eligible = [p for p in range(0, 37, 3) if cases[m, p, a]['feasible']]
            values[a] = min(eligible) if eligible else None
            if eligible:
                witness_keys.add((m, min(eligible), a))
        minima.append(dict(mask=m, reciprocal=bool(m & 2 and m & 4),
                           diagonal_only=not bool(m & 6), minimum=values))
    if data['minima'] != minima or (states, edges) != (data['total_states'], data['total_edges']):
        raise ValueError('Census summary mismatch')
    actual_witnesses = []
    for w in data['witnesses']:
        k = (w['case']['mask'], w['case']['photons'], w['case']['arm'])
        actual_witnesses.append(k)
        interpret(w, cases[k])
    if len(actual_witnesses) != len(witness_keys) or set(actual_witnesses) != witness_keys:
        raise ValueError('Missing/duplicate minimal witness')
    return dict(verified=True, cases=1040, states=states, edges=edges,
                object_witnesses=len(witness_keys), minima=minima,
                natural_worlds=0, autonomous_self_maintenance=False)


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--input', required=True)
    p.add_argument('--revision', required=True)
    args = p.parse_args()
    try:
        print(json.dumps(audit(json.loads(Path(args.input).read_bytes()), args.revision), sort_keys=True))
    except (ValueError, KeyError, TypeError) as error:
        p.exit(2, str(error)+'\n')
