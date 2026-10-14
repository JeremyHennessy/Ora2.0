"""Prospectively registered fresh rapid-revision cognition experiment.

New seed banks, separate results and no alteration to COGNITION01 closed panel.
Uses only COGNITION01's frozen environment/draw helpers, never its historic trials.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from experiments import digital_cognition01 as previous

VERSION = 'DIGITAL-COGNITION02-v1'
ARMS = ('quick_memory', 'historic_memory', 'memory_disabled', 'misbound_history',
        'latest_reactive', 'fixed', 'constant0', 'constant1')
PRIMARY = tuple(range(78400, 78408))
UNSEEN = tuple(range(78600, 78608))


class Policy:
    """No access to environment seed, target, global tick, epoch or future outcome."""
    def __init__(self, arm, fixed_ports):
        assert arm in ARMS and len(fixed_ports) == 8
        self.arm = arm
        self.fixed_ports = tuple(fixed_ports)
        self.weights = [0] * 8
        self.latest = None

    def choose(self, site, tie, explore, noise):
        assert type(site) is int and 0 <= site < 8
        if self.arm in ('quick_memory', 'historic_memory', 'misbound_history'):
            weight = self.weights[site]
            port = 1 if weight > 0 else 0 if weight < 0 else tie
        elif self.arm == 'latest_reactive':
            port = tie if self.latest is None else self.latest[0] if self.latest[1] else 1 - self.latest[0]
        elif self.arm == 'fixed':
            port = self.fixed_ports[site]
        elif self.arm == 'constant0':
            port = 0
        elif self.arm == 'constant1':
            port = 1
        else:
            port = tie
        return noise if explore else port

    def learn(self, site, port, feedback):
        if self.arm in ('quick_memory', 'historic_memory', 'misbound_history'):
            dest = (site + 1) % 8 if self.arm == 'misbound_history' else site
            bound = 12 if self.arm == 'historic_memory' else 2
            delta = 2 * (1 if port else -1) * (1 if feedback else -1)
            self.weights[dest] = max(-bound, min(bound, self.weights[dest] + delta))
        self.latest = (port, feedback)


def run_trial(seed, arm):
    if type(seed) is not int or seed not in PRIMARY + UNSEEN or arm not in ARMS:
        raise ValueError('nonregistered seed or arm')
    # Unlike closed01, only the fixed arm receives seed-derived assignments.
    fixed = [previous.bit('COGNITION01-fixed', seed, j) for j in range(8)] if arm == 'fixed' else [0] * 8
    policy = Policy(arm, fixed)
    energy, heat, successes, death = 64, 0, 0, None
    rows = []
    for tick in range(256):
        site = tick % 8
        target = previous.target_port(seed, site, tick)
        tie, explore, noise = previous.event_random(seed, tick)
        was_energy = energy
        old_weights = policy.weights[:]
        old_latest = policy.latest
        if death is not None or energy < 3:
            if death is None:
                death = tick
                heat += energy
                energy = 0
            heat += 12
            row = dict(tick=tick, site=site, target=target, tie=tie, explore=explore,
                       noise=noise, port=None, feedback=None, before=was_energy,
                       energy=energy, heat=heat, cost=0, collected=0,
                       packet_wasted=12, memory_before=old_weights, memory_after=policy.weights[:],
                       latest_before=old_latest, latest_after=policy.latest, expired=True)
        else:
            attempted = policy.choose(site, tie, explore, noise)
            energy -= 3
            heat += 3
            success = int(attempted == target)
            gained = min(12, 64 - energy) if success else 0
            heat += 12 - gained
            energy += gained
            successes += success
            policy.learn(site, attempted, success)
            if energy == 0:
                death = tick + 1
            row = dict(tick=tick, site=site, target=target, tie=tie, explore=explore,
                       noise=noise, port=attempted, feedback=success, before=was_energy,
                       energy=energy, heat=heat, cost=3, collected=gained,
                       packet_wasted=12 - gained, memory_before=old_weights,
                       memory_after=policy.weights[:], latest_before=old_latest,
                       latest_after=policy.latest, expired=(energy == 0))
        assert energy + heat == 64 + 12 * (tick + 1)
        rows.append(row)
    result = dict(version=VERSION, seed=seed, arm=arm, events=rows,
                  summary=dict(successes=successes, final_energy=energy, heat=heat,
                               died_at=death, alive_through_end=death is None,
                               paid_instructions=sum(x['cost'] for x in rows),
                               acquired_energy=sum(x['collected'] for x in rows),
                               packet_energy_offered=12 * 256,
                               source='researcher-authored generic rapid-revision plasticity'))
    result['sha256'] = previous.digest(result)
    return result


def run_panel():
    trials = {(seed, arm): run_trial(seed, arm) for seed in PRIMARY + UNSEEN for arm in ARMS}
    summaries = []
    for seed in PRIMARY + UNSEEN:
        rows = {arm: trials[seed, arm] for arm in ARMS}
        scores = {arm: rows[arm]['summary']['successes'] for arm in ARMS}
        competing = ('historic_memory', 'memory_disabled', 'misbound_history', 'latest_reactive', 'fixed')
        margins = {arm: scores['quick_memory'] - scores[arm] for arm in competing}
        alive = rows['quick_memory']['summary']['alive_through_end']
        summaries.append(dict(seed=seed, bank='primary' if seed in PRIMARY else 'unseen',
                              scores=scores, margins=margins,
                              quick_alive=alive, qualifying=alive and all(x >= 20 for x in margins.values()),
                              deaths={arm: rows[arm]['summary']['died_at'] for arm in ARMS},
                              hashes={arm: rows[arm]['sha256'] for arm in ARMS}))
    bank = {name: sum(s['qualifying'] for s in summaries if s['bank'] == name)
            for name in ('primary', 'unseen')}
    return trials, dict(version=VERSION, banks=bank, registered_pass=all(v >= 6 for v in bank.values()),
                        rows=summaries, supplied_learning_mechanism=True, evolved=False)


def main():
    args = argparse.ArgumentParser()
    args.add_argument('--output', type=Path, required=True)
    path = args.parse_args().output
    if path.exists():
        raise SystemExit('refuse overwriting prior evidence')
    trials, summary = run_panel()
    from experiments.digital_cognition02_referee import audit_panel
    proof = audit_panel(trials)
    assert summary['banks'] == proof['banks'] and summary['registered_pass'] == proof['registered_pass']
    payload = dict(version=VERSION, summary=summary, referee=proof,
                   full=[trials[seed, arm] for seed in PRIMARY + UNSEEN for arm in ARMS])
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('x', encoding='utf-8', newline='\n') as f:
        json.dump(payload, f, sort_keys=True, separators=(',', ':'), ensure_ascii=True)
        f.write('\n')
    print(previous.canonical(dict(result=summary['banks'], passed=summary['registered_pass'],
                                  referee=proof['verified'], sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
                                  output=str(path))))


if __name__ == '__main__':
    main()
