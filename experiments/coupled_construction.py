"""COUPLE-01 finite possibility oracle. Never a natural-world controller."""
import argparse
from collections import deque
import json
from pathlib import Path

ARMS = ('network', 'inert', 'background', 'withdrawal', 'no-recycling')
# phase, photons, fuelA, fuelB, rawA, rawB, wasteA, wasteB, componentA, componentB


def initial(photons):
    return (0, photons, 0, 0, 2, 2, 0, 0, 0, 0)


def goal(s):
    return s[0] == 1 and s[8:] == (1, 1)


def successors(s, mask, arm):
    if goal(s):
        return []
    if s[0] == 0 and s[8:] == (1, 1):
        q = list(s)
        q[0] = 1
        q[6:10] = [2, 2, 0, 0]
        if arm == 'withdrawal':
            q[1] = 0
        return [('damage', tuple(q))]
    out = []
    for j in range(2):
        if s[1] >= 3:
            q = list(s)
            q[1] -= 3
            q[2+j] += 1
            out.append((f'basal-{j}', tuple(q)))
            if arm == 'background':
                q = list(s)
                q[1] -= 3
                q[2+j] += 2
                out.append((f'background-{j}', tuple(q)))
            elif arm != 'inert':
                for i in range(2):
                    if s[8+i] and mask & (1 << (2*i+j)):
                        q = list(s)
                        q[1] -= 3
                        q[2+j] += 2
                        out.append((f'catalytic-{i}-{j}', tuple(q)))
        if s[4+j] == 2 and s[2+j] >= 3:
            q = list(s)
            q[4+j] = 0
            q[2+j] -= 3
            q[8+j] = 1
            out.append((f'manufacture-{j}', tuple(q)))
        if arm != 'no-recycling' and s[6+j] == 2 and s[2+j] >= 1:
            q = list(s)
            q[6+j] = 0
            q[4+j] = 2
            q[2+j] -= 1
            out.append((f'recycle-{j}', tuple(q)))
    return out


def enumerate_case(mask, photons, arm):
    if mask not in range(16) or photons not in range(0, 37, 3) or arm not in ARMS:
        raise ValueError('Unregistered case')
    start = initial(photons)
    seen = {start: None}
    queue = deque([start])
    edges = 0
    target = None
    while queue:
        state = queue.popleft()
        if goal(state) and target is None:
            target = state
        for action, child in successors(state, mask, arm):
            edges += 1
            if child not in seen:
                if len(seen) >= 200000:
                    raise ValueError('Registered per-case state bound reached')
                seen[child] = (state, action)
                queue.append(child)
    path = []
    cursor = target
    while cursor is not None and seen[cursor] is not None:
        parent, action = seen[cursor]
        path.append(action)
        cursor = parent
    return dict(mask=mask, photons=photons, arm=arm, feasible=target is not None,
                states=len(seen), edges=edges, actions=list(reversed(path)))


def witness(case):
    """Object-level provenance for the deterministic shortest oracle witness."""
    state = initial(case['photons'])
    heat = removed = 0
    objects = []
    current = [None, None]
    histories = [[], []]
    rows = [dict(state=state, heat=0, removed=0, current=current.copy(), objects=[])]
    for action in case['actions']:
        choices = dict(successors(state, case['mask'], case['arm']))
        nxt = choices[action]
        if action == 'damage':
            heat += 2
            if case['arm'] == 'withdrawal':
                removed += state[1]
            current = [None, None]
        elif action.startswith('manufacture'):
            j = int(action[-1])
            identity = len(objects)
            objects.append(dict(id=identity, kind=j, atoms=[2*j, 2*j+1],
                                previous_objects=histories[j].copy()))
            histories[j].append(identity)
            current[j] = identity
            heat += 2
        elif action.startswith('recycle'):
            heat += 1
        elif action.startswith('basal'):
            heat += 2
        else:
            heat += 1
        state = nxt
        if state[1] + sum(state[2:4]) + sum(state[8:10]) + heat + removed != case['photons']:
            raise ValueError('Energy mismatch')
        rows.append(dict(action=action, state=state, heat=heat, removed=removed,
                         current=current.copy(), objects=[dict(x) for x in objects]))
    return rows


def census(revision):
    cases = [enumerate_case(m, p, a) for m in range(16)
             for p in range(0, 37, 3) for a in ARMS]
    witnesses = []
    # Preserve every minimal-energy feasible mask/arm, never select world seeds.
    minima = []
    for mask in range(16):
        entry = dict(mask=mask, reciprocal=bool(mask & 2 and mask & 4),
                     diagonal_only=not bool(mask & 6), minimum={})
        for arm in ARMS:
            matches = [c for c in cases if c['mask'] == mask and c['arm'] == arm and c['feasible']]
            entry['minimum'][arm] = matches[0]['photons'] if matches else None
            if matches:
                witnesses.append(dict(case={k: matches[0][k] for k in ('mask', 'photons', 'arm')},
                                      rows=witness(matches[0])))
        minima.append(entry)
    for c in cases:
        if c['feasible'] and (c['arm'] == 'no-recycling' or c['photons'] < 14):
            raise ValueError('Registered accounting falsifier')
    return dict(schema='couple01-feasibility-v1', source_revision=revision,
                scope='exhaustive authored reachability, NOT natural dynamics',
                cases=cases, minima=minima, witnesses=witnesses,
                total_states=sum(c['states'] for c in cases),
                total_edges=sum(c['edges'] for c in cases), continuous=False)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--revision', required=True)
    parser.add_argument('--output', required=True)
    args = parser.parse_args()
    data = json.dumps(census(args.revision), sort_keys=True, separators=(',', ':')).encode()
    # The acceptance wrapper precharges this file; this module only emits stdout.
    if args.output != 'stdout':
        raise ValueError('Guarded wrapper must capture stdout; direct writes prohibited')
    print(data.decode())
