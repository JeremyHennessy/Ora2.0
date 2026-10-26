"""Frozen authored-learner assay. No VM, population, native archives or models."""
import argparse
import hashlib
import itertools
import json
import os
from pathlib import Path
import random

SCALE = 64
HORIZON = 384


def digest(value):
    return hashlib.sha256(json.dumps(value, separators=(',', ':'), sort_keys=True).encode()).hexdigest()


def environment(seed, period):
    rng = random.Random(seed)
    rows = []
    for t in range(HORIZON):
        if t % period == 0:
            mapping = [rng.randrange(4) for _ in range(4)]
        cue = rng.randrange(4)
        rows.append([cue, mapping[cue], rng.random()])
    return rows


def spec(name, kind, **kw):
    return dict(name=name, kind=kind, **kw)


def candidates():
    return [spec(f'counter{b}-drop{d}', 'counter', width=b, drop=d)
            for b in (1, 2, 3) for d in (1, 2)]


def references():
    result = [spec(f'constant{a}', 'constant', action=a) for a in range(4)]
    result += [spec('fixed'+''.join(map(str, m)), 'fixed', mapping=m)
               for m in itertools.product(range(4), repeat=4)]
    result += [spec('global-wsls', 'global'), spec('context-wsls', 'wsls'),
               spec('context-last-success', 'last'), spec('context-estimator', 'estimator')]
    return result


def allocation(policy, delay):
    kind = policy['kind']
    state = {'constant': 0, 'fixed': 0, 'global': 2, 'wsls': 8,
             'last': 8, 'counter': 16*policy.get('width', 0), 'estimator': 288}[kind]
    learning = kind not in ('constant', 'fixed')
    bits = state + ((delay+1)*5 if learning else 0)
    program = {'constant': 1, 'fixed': 12, 'global': 8, 'wsls': 8,
               'last': 8, 'counter': 12, 'estimator': 16}[kind]
    return bits, program, learning


def life(policy, rows, delay, intervention='true', retain=False):
    kind = policy['kind']
    bits, program, learning = allocation(policy, delay)
    energy, heat, food = 128*SCALE, 0, 0
    costs = dict(formation=0, storage=0, sensing=0, feedback=0, update=0, arithmetic=0, action=0)
    trace, pending = [], {}
    maximum = (1 << policy.get('width', 1))-1
    scores = [[maximum]*4 for _ in range(4)]
    last = [0]*4
    successes, counts = [[0]*4 for _ in range(4)], [[0]*4 for _ in range(4)]
    alive, reason, attempts, hits, delivered, completed = True, None, 0, 0, 0, 0

    def pay(label, amount):
        nonlocal energy, alive, reason
        # Record only a payable debit. Exhaustion preserves residual energy.
        if energy <= amount:
            alive, reason = False, label
            return False
        energy -= amount
        costs[label] += amount
        return True

    pay('formation', (bits+program)*SCALE)
    for t, (cue, target, u) in enumerate(rows):
        if not alive:
            break
        before, due_food, cost_before, heat_before = energy, 0, sum(costs.values()), heat
        action, hit = -1, -1
        if pay('storage', bits):
            due = pending.pop(t, None)
            if due is not None:
                oldcue, oldaction, outcome = due
                if not learning or pay('feedback', SCALE):
                    due_food = outcome*8*SCALE
                    food += due_food
                    delivered += outcome
                    energy += due_food
                    heat += max(0, energy-512*SCALE)
                    energy = min(energy, 512*SCALE)
                    if learning and pay('update', (2 if kind == 'estimator' else 1)*SCALE):
                        observed = 0 if intervention == 'clamp' else outcome
                        c = (oldcue+1) % 4 if intervention == 'miscredit' else oldcue
                        if kind == 'counter':
                            scores[c][oldaction] = min(maximum, scores[c][oldaction]+1) if observed else max(0, scores[c][oldaction]-policy['drop'])
                        elif kind in ('global', 'wsls'):
                            index = 0 if kind == 'global' else c
                            last[index] = oldaction if observed else (oldaction+1) % 4
                        elif kind == 'last':
                            if observed:
                                last[c] = oldaction
                        else:
                            counts[c][oldaction] += 1
                            successes[c][oldaction] += observed
            if alive:
                if intervention == 'erase':
                    scores = [[maximum]*4 for _ in range(4)]
                if kind == 'constant':
                    action = policy['action']
                elif pay('sensing', SCALE):
                    if kind == 'fixed':
                        action = policy['mapping'][cue]
                    elif kind == 'counter':
                        action = max(range(4), key=lambda a: scores[cue][a])
                    elif kind in ('global', 'wsls', 'last'):
                        action = last[0 if kind == 'global' else cue]
                    elif pay('arithmetic', 2*SCALE):
                        # Rational comparison; no floating precision in policy decisions.
                        action = 0
                        for a in range(1, 4):
                            left = (successes[cue][a]+1)*(counts[cue][action]+1)
                            right = (successes[cue][action]+1)*(counts[cue][a]+1)
                            if left > right:
                                action = a
                if alive and pay('action', SCALE):
                    hit = int(u < (0.8 if action == target else 1/15))
                    pending[t+delay] = (cue, action, hit)
                    attempts += 1
                    hits += hit
                    completed += 1
        trace.append([t, before, energy, sum(costs.values())-cost_before,
                      due_food, heat-heat_before, cue, action, hit, int(alive)])
    assert energy == 128*SCALE - sum(costs.values()) + food - heat
    result = dict(policy=policy['name'], intervention=intervention, alive=alive,
                  death_reason=reason, attempts=attempts, successful_attempts=hits,
                  delivered_successes=delivered, unresolved=len(pending),
                  allocated_bits=bits, costs=costs, delivered_food=food, overflow_heat=heat,
                  remaining_energy=energy, score=energy if alive else 0,
                  trace_sha256=digest(trace), completed=completed)
    if retain:
        result['trace'] = trace
    return result


def worlds(validation=False):
    seeds = range(9000, 9032) if validation else range(1000, 1016)
    periods = (80, 128) if validation else (64, 96)
    return [dict(seed=s, period=periods[i % 2], rows=environment(s, periods[i % 2]))
            for i, s in enumerate(seeds)]


def evaluate(policy, bank, delay, intervention='true', retain=False):
    return [dict(seed=w['seed'], **life(policy, w['rows'], delay, intervention, retain)) for w in bank]


def choose(policies, records):
    return min(policies, key=lambda p: (-sum(r['score'] for r in records[p['name']]), p['name']))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    development = worlds()
    candidate_policies, reference_policies = candidates(), references()
    dev = {p['name']: evaluate(p, development, 2) for p in candidate_policies+reference_policies}
    selected = choose(candidate_policies, dev)
    fixed = choose([p for p in reference_policies if p['kind'] == 'fixed'], dev)
    deployed_refs = [p for p in reference_policies if p['kind'] != 'fixed']+[fixed]
    strongest = choose(deployed_refs, dev)
    # Durable exclusive selection receipt precedes construction of held-out data.
    selection = dict(candidate=selected, fixed=fixed, reference=strongest,
                     development_totals={k: sum(r['score'] for r in v) for k, v in dev.items()})
    selection_hash = digest(selection)
    with args.output.with_name('selection.json').open('x', encoding='utf-8') as target:
        json.dump(dict(selection=selection, sha256=selection_hash), target, sort_keys=True)
        target.flush()
        os.fsync(target.fileno())
    validation = worlds(True)
    val = {p['name']: evaluate(p, validation, 3) for p in reference_policies}
    arms = {arm: evaluate(selected, validation, 3, arm, retain=True)
            for arm in ('true', 'clamp', 'erase', 'miscredit')}
    own = arms['true']
    ref = val[strongest['name']]
    differences = [a['score']-b['score'] for a, b in zip(own, ref)]
    ablation_gaps = {arm: sum(r['score'] for r in own)-sum(r['score'] for r in records)
                     for arm, records in arms.items() if arm != 'true'}
    passed = sum(differences) > 0 and sum(x > 0 for x in differences) >= 24 and all(x > 0 for x in ablation_gaps.values())
    result = dict(schema='noisy-credit-v1', scientific_population=False, births=0,
                  evolution_demonstrated=False, scale=SCALE, initial_energy=128*SCALE,
                  protocol_sha256=hashlib.sha256(Path(__file__).with_name('PROTOCOL.md').read_bytes()).hexdigest(),
                  source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                  selection=selection, selection_sha256=selection_hash,
                  development_worlds=development, development=dev, validation_worlds=validation,
                  validation=val, causal_arms=arms,
                  primary=dict(passed=passed, paired_score_differences=differences,
                               positive_worlds=sum(x > 0 for x in differences),
                               mean_energy_difference=sum(differences)/32/SCALE,
                               ablation_total_gaps=ablation_gaps))
    with args.output.open('x', encoding='utf-8') as target:
        json.dump(result, target, separators=(',', ':'))


if __name__ == '__main__':
    main()
