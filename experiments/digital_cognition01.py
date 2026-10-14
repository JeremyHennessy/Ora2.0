"""COGNITION01: isolated, preregistered, capability-first synthetic memory assay.

The policy sees site/its own feedback and exogenous tie/noise bits only.
It never receives the hidden reward port, trial seed, tick, or epoch.
This is an authored generic plastic learner, not evolved intelligence or Ora's VM.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

VERSION = 'DIGITAL-COGNITION01-v1'
SITES = 8
HORIZON = 256
INITIAL_ENERGY = 64
ENERGY_CAP = 64
PACKET_ENERGY = 12
ACT_COST = 3
RATE = 2
WEIGHT_BOUND = 12
ARMS = ('intact', 'memory_disabled', 'misbound_history',
        'latest_reactive', 'fixed', 'constant0', 'constant1')
PRIMARY = tuple(range(78000, 78008))
UNSEEN = tuple(range(78200, 78208))


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=True)


def digest(value):
    return hashlib.sha256(canonical(value).encode('ascii')).hexdigest()


def bit(*parts):
    return int(digest(list(parts))[:16], 16) % 2


def event_random(seed, tick):
    """Bounded exogenous randomness, not a feature exposed to the policy."""
    return (bit('COGNITION01-tie', seed, tick),
            int(digest(['COGNITION01-explore', seed, tick])[:16], 16) % 16 == 0,
            bit('COGNITION01-noise', seed, tick))


def target_port(seed, site, tick):
    """Forensic environment ONLY. Never called from Policy."""
    return bit('COGNITION01-target', seed, site) ^ int(tick >= HORIZON // 2)


class Policy:
    def __init__(self, arm, fixed_ports):
        if arm not in ARMS or len(fixed_ports) != SITES:
            raise ValueError('invalid arm or fixed-port inventory')
        if any(type(port) is not int or port not in (0, 1) for port in fixed_ports):
            raise ValueError('invalid fixed port')
        self.arm = arm
        self.fixed_ports = tuple(fixed_ports)
        self.weights = [0] * SITES
        self.latest = None

    def choose(self, site, tie, explore, noise):
        if type(site) is not int or not 0 <= site < SITES:
            raise ValueError('invalid sensed site')
        if any(type(x) is not int or x not in (0, 1) for x in (tie, noise)) or type(explore) is not bool:
            raise ValueError('invalid independent draw')
        if self.arm in ('intact', 'misbound_history'):
            weight = self.weights[site]
            port = (1 if weight > 0 else 0 if weight < 0 else tie)
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

    def learn(self, site, chosen_port, feedback):
        if type(feedback) is not int or feedback not in (0, 1):
            raise ValueError('not personally observable feedback')
        if self.arm in ('intact', 'misbound_history'):
            slot = site if self.arm == 'intact' else (site + 1) % SITES
            direction = (1 if chosen_port else -1) * (1 if feedback else -1)
            self.weights[slot] = max(-WEIGHT_BOUND, min(WEIGHT_BOUND, self.weights[slot] + RATE * direction))
        self.latest = (chosen_port, feedback)


def run_trial(seed, arm):
    if type(seed) is not int or seed not in PRIMARY + UNSEEN or arm not in ARMS:
        raise ValueError('not in the frozen bank')
    # Only fixed comparator receives the random static per-site assignment.
    ports = [bit('COGNITION01-fixed', seed, site) for site in range(SITES)]
    policy = Policy(arm, ports)
    energy, heat, successes, dead_at = INITIAL_ENERGY, 0, 0, None
    events = []
    for tick in range(HORIZON):
        site = tick % SITES
        target = target_port(seed, site, tick)
        tie, explore, noise = event_random(seed, tick)
        before = energy
        memory_before = policy.weights[:]
        latest_before = policy.latest
        if dead_at is not None or energy < ACT_COST:
            if dead_at is None:
                dead_at = tick
                heat += energy
                energy = 0
            heat += PACKET_ENERGY
            record = dict(tick=tick, site=site, target=target, tie=tie, explore=explore,
                          noise=noise, port=None, feedback=None, before=before,
                          energy=energy, heat=heat, cost=0, collected=0,
                          packet_wasted=PACKET_ENERGY, memory_before=memory_before,
                          memory_after=policy.weights[:], latest_before=latest_before,
                          latest_after=policy.latest, expired=True)
        else:
            port = policy.choose(site, tie, explore, noise)
            energy -= ACT_COST
            heat += ACT_COST
            feedback = int(port == target)
            collected = min(PACKET_ENERGY, ENERGY_CAP - energy) if feedback else 0
            wasted = PACKET_ENERGY - collected
            heat += wasted
            energy += collected
            successes += feedback
            policy.learn(site, port, feedback)
            if energy == 0:
                dead_at = tick + 1
            record = dict(tick=tick, site=site, target=target, tie=tie, explore=explore,
                          noise=noise, port=port, feedback=feedback, before=before,
                          energy=energy, heat=heat, cost=ACT_COST, collected=collected,
                          packet_wasted=wasted, memory_before=memory_before,
                          memory_after=policy.weights[:], latest_before=latest_before,
                          latest_after=policy.latest, expired=(energy == 0))
        assert energy + heat == INITIAL_ENERGY + PACKET_ENERGY * (tick + 1)
        events.append(record)
    assert len(events) == HORIZON
    result = dict(version=VERSION, seed=seed, arm=arm, events=events,
                  summary=dict(successes=successes, final_energy=energy,
                               heat=heat, died_at=dead_at,
                               alive_through_end=dead_at is None,
                               paid_instructions=sum(e['cost'] for e in events),
                               acquired_energy=sum(e['collected'] for e in events),
                               packet_energy_offered=PACKET_ENERGY * HORIZON,
                               source='researcher-authored generic plasticity'))
    result['sha256'] = digest({k: v for k, v in result.items() if k != 'sha256'})
    return result


def summarize_panel(trials):
    paired = []
    for seed in PRIMARY + UNSEEN:
        arms = {arm: trials[(seed, arm)] for arm in ARMS}
        score = {name: row['summary']['successes'] for name, row in arms.items()}
        intact = arms['intact']['summary']
        margins = {arm: score['intact'] - score[arm]
                   for arm in ('memory_disabled', 'misbound_history', 'latest_reactive', 'fixed')}
        win = intact['alive_through_end'] and all(v >= 20 for v in margins.values())
        paired.append(dict(seed=seed, bank='primary' if seed in PRIMARY else 'unseen',
                           scores=score, margins=margins, intact_alive=intact['alive_through_end'],
                           qualifying=win,
                           trial_sha256={arm: arms[arm]['sha256'] for arm in ARMS},
                           deaths={arm: arms[arm]['summary']['died_at'] for arm in ARMS}))
    counts = {name: sum(row['qualifying'] for row in paired if row['bank'] == name)
              for name in ('primary', 'unseen')}
    return dict(version=VERSION, banks=counts, registered_pass=all(n >= 6 for n in counts.values()),
                rows=paired, disclaimed='supplied plastic mechanism; no emergent evolution or intelligence')


def run_panel():
    trials = {(seed, arm): run_trial(seed, arm) for seed in PRIMARY + UNSEEN for arm in ARMS}
    return trials, summarize_panel(trials)


def main():
    parser = argparse.ArgumentParser(description='Cognition01 bounded, standalone, no-network assay')
    parser.add_argument('--output', type=Path, required=True, help='Complete immutable-style evidence JSON path')
    args = parser.parse_args()
    if args.output.exists():
        parser.error('refuse overwriting any evidence output')
    trials, summary = run_panel()
    from experiments.digital_cognition01_referee import audit_panel
    audit = audit_panel(trials)
    if not audit['verified']:
        raise SystemExit('independent referee rejected panel')
    body = dict(protocol=VERSION, summary=summary, referee=audit,
                full=[trials[(seed, arm)] for seed in PRIMARY + UNSEEN for arm in ARMS])
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open('x', encoding='utf-8', newline='\n') as handle:
        json.dump(body, handle, sort_keys=True, separators=(',', ':'), ensure_ascii=True)
        handle.write('\n')
    print(canonical(dict(path=str(args.output), counts=summary['banks'],
                         registered_pass=summary['registered_pass'],
                         full_sha256=hashlib.sha256(args.output.read_bytes()).hexdigest(),
                         referee=audit['verified'])))


if __name__ == '__main__':
    main()
