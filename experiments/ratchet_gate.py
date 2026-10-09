"""RATCHET-01 controlled reversible work ledger; no natural-world sampling."""
import argparse
from collections import deque
import hashlib
import itertools
import json
from math import comb

ARMS = ('candidate', 'uncoupled', 'isotropic', 'equilibrium')
ENERGY = (0, 1, 0)
START = (16, 0, 10, 0)  # remaining fuel, conformation, work, replacement phase


def packed(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':')).encode()


def heat(state):
    fuel, conformation, work, _ = state
    return 144 - 6 * fuel - ENERGY[conformation] - work - 2


def edges(state, arm):
    fuel, q, work, phase = state
    pairs = ((0, 1), (1, 2), (2, 0), (0, 1), (2, 1))
    for channel, (left, right) in enumerate(pairs):
        if channel in (0, 4) and (arm == 'equilibrium' or (channel == 4 and arm != 'isotropic')):
            continue
        for direction in (1, -1):
            before, after = (left, right) if direction == 1 else (right, left)
            independent = arm == 'uncoupled' and channel == 2
            if not independent and q != before:
                continue
            n = fuel - direction if channel in (0, 4) else fuel
            load = work + direction if channel == 2 else work
            nxt = (n, q if independent else after, load, phase)
            if 0 <= n <= 16 and load >= 0 and heat(nxt) >= 0:
                yield (channel, direction), nxt
    if phase == 0 and work >= 7:
        yield (5, 1), (fuel, 0, work - 7, 1)


def rate(state, action, nxt, arm, barriers):
    channel, direction = action
    if channel == 5:
        raise ValueError('Operator action is not a thermal rate')
    chemical = channel in (0, 4)
    numerator = (state[0] if direction == 1 else 16 - state[0]) if chemical else 16
    barrier = barriers[0 if chemical else 2 if channel == 2 else 1]
    barrier += int(chemical and arm == 'isotropic')
    exponent = barrier + max(0, heat(state) - heat(nxt))
    return numerator, exponent  # probability = numerator / (160 * 2**exponent)


def endpoint(state):
    return state[3] == 1 and state[2] > 16 and heat(state) >= 32


def witness(arm, path):
    state = START
    atoms = [0, 1, 2]
    objects = [dict(id=0, atoms=atoms, parent=None, construction_work=6, alive=True)]
    tokens = [dict(id=i, state='F', transformations=[]) for i in range(16)]
    snapshots = [list(state) + [heat(state)]]
    events = []
    for action in path:
        matches = [nxt for proposal, nxt in edges(state, arm) if list(proposal) == action]
        if len(matches) != 1:
            raise ValueError('Illegal witness action')
        nxt = matches[0]
        channel, direction = action
        token = None
        if channel in (0, 4):
            before, after = ('F', 'W') if direction == 1 else ('W', 'F')
            token = next(x for x in tokens if x['state'] == before)
            token['state'] = after
            token['transformations'].append(dict(event=len(events), machine=objects[-1]['id'], route=action))
        if channel == 5:
            objects[-1]['alive'] = False
            objects.append(dict(id=1, atoms=atoms, parent=0, construction_work=6, destruction_work=1, alive=True))
        events.append(dict(action=action, token=None if token is None else token['id'], machine=objects[-1]['id']))
        state = nxt
        snapshots.append(list(state) + [heat(state)])
    return dict(path=path, snapshots=snapshots, events=events, objects=objects, tokens=tokens,
                total_energy=144, structural_atoms=atoms, initial_work=16, initial_heat=32,
                startup_work=6, replacement_work=7 if state[3] else 0, endpoint=endpoint(state))


def enumerate_arm(arm):
    pending = deque([START])
    parents = {START: None}
    count = physical = 0
    first = None
    signatures = set()
    while pending:
        state = pending.popleft()
        if endpoint(state) and first is None:
            first = state
        for action, nxt in edges(state, arm):
            count += 1
            if count > 2000000:
                raise ValueError('Registered edge cap exceeded')
            if action[0] != 5:
                physical += 1
                # Rates depend on F, channel, direction and heat difference only.
                signatures.add((state[0], action[0], action[1], heat(nxt)-heat(state)))
            if nxt not in parents:
                parents[nxt] = (state, action)
                pending.append(nxt)
                if len(parents) > 60000:
                    raise ValueError('Registered state cap exceeded')
    checks = 0
    for fuel, channel, direction, dh in sorted(signatures):
        chemical = channel in (0, 4)
        other_fuel = fuel - direction if chemical else fuel
        a = (fuel if direction == 1 else 16-fuel) if chemical else 16
        reverse = (other_fuel if direction == -1 else 16-other_fuel) if chemical else 16
        for b0, b1, b2 in itertools.product(range(4), repeat=3):
            barrier = (b0 if chemical else b2 if channel == 2 else b1) + int(chemical and arm == 'isotropic')
            x, y = barrier + max(0, -dh), barrier + max(0, dh)
            # Cancel common positive 2**H before integer cross-multiplication.
            lhs = comb(16, fuel) * a * 2**(y + max(0, -dh))
            rhs = comb(16, other_fuel) * reverse * 2**(x + max(0, dh))
            if lhs != rhs or a > 160 * 2**x:
                raise ValueError('Channel detailed balance/rate failed')
            checks += 1
    path = []
    cursor = first
    while cursor is not None and parents[cursor] is not None:
        previous, action = parents[cursor]
        path.append(list(action))
        cursor = previous
    path.reverse()
    return dict(arm=arm, states=len(parents), edges=count, physical_edges=physical,
                state_sha256=hashlib.sha256(packed(sorted(parents))).hexdigest(),
                endpoint_states=sum(endpoint(s) for s in parents),
                rate_signatures=len(signatures), barrier_checks=checks,
                witness=None if first is None else witness(arm, path))


def certificate():
    cycle = [[0, 1], [1, 1], [2, 1]]
    return witness('candidate', cycle * 7 + [[5, 1]] + cycle * 7)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--revision', required=True)
    args = parser.parse_args()
    result = dict(schema='ratchet01-feasibility', source_revision=args.revision,
                  natural_worlds=0, barrier_laws=64, records=[enumerate_arm(a) for a in ARMS],
                  forward_cycle_certificate=certificate())
    print(json.dumps(result, sort_keys=True))


if __name__ == '__main__':
    main()
