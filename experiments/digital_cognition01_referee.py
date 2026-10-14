"""Independent literal referee for COGNITION01; imports NO producer or Policy.

Replays the disclosed environment, paid energy, alternative policies, timing,
feedback and signed memory update entirely from each original event transcript.
"""
from __future__ import annotations

import hashlib
import json

MODES = ('intact', 'memory_disabled', 'misbound_history',
         'latest_reactive', 'fixed', 'constant0', 'constant1')
SEEDS = tuple(range(78000, 78008)) + tuple(range(78200, 78208))
DURATION = 256


def fingerprint(o):
    return hashlib.sha256(json.dumps(o, sort_keys=True, separators=(',', ':'), ensure_ascii=True).encode()).hexdigest()


def draw(*parts):
    return int(fingerprint(list(parts))[:16], 16)


def audit_trial(trial):
    assert set(trial) == {'version', 'seed', 'arm', 'events', 'summary', 'sha256'}
    assert trial['version'] == 'DIGITAL-COGNITION01-v1'
    seed, arm = trial['seed'], trial['arm']
    assert type(seed) is int and seed in SEEDS and arm in MODES
    assert type(trial['events']) is list and len(trial['events']) == DURATION
    energy, heat, rewards, death_tick, charges, gained = 64, 0, 0, None, 0, 0
    learned = [0] * 8
    recent = None
    for t, raw in enumerate(trial['events']):
        location = t % 8
        hidden = (draw('COGNITION01-target', seed, location) % 2) ^ int(t >= 128)
        tie = draw('COGNITION01-tie', seed, t) % 2
        noise = draw('COGNITION01-noise', seed, t) % 2
        explore = draw('COGNITION01-explore', seed, t) % 16 == 0
        original_energy = energy
        old_memory = learned[:]
        old_recent = recent
        if death_tick is not None or energy < 3:
            if death_tick is None:
                death_tick = t
                heat += energy
                energy = 0
            heat += 12
            candidate = dict(tick=t, site=location, target=hidden, tie=tie, explore=explore,
                             noise=noise, port=None, feedback=None, before=original_energy,
                             energy=energy, heat=heat, cost=0, collected=0, packet_wasted=12,
                             memory_before=old_memory, memory_after=learned[:],
                             latest_before=old_recent, latest_after=recent, expired=True)
        else:
            if arm in ('intact', 'misbound_history'):
                direction = learned[location]
                chosen = 1 if direction > 0 else 0 if direction < 0 else tie
            elif arm == 'latest_reactive':
                chosen = tie if recent is None else recent[0] if recent[1] else 1 - recent[0]
            elif arm == 'fixed':
                chosen = draw('COGNITION01-fixed', seed, location) % 2
            elif arm == 'constant0':
                chosen = 0
            elif arm == 'constant1':
                chosen = 1
            else:
                chosen = tie
            chosen = noise if explore else chosen
            truth = int(chosen == hidden)
            energy -= 3
            heat += 3
            awarded = min(12, 64 - energy) if truth else 0
            heat += 12 - awarded
            energy += awarded
            rewards += truth
            charges += 3
            gained += awarded
            if arm in ('intact', 'misbound_history'):
                key = location if arm == 'intact' else (location + 1) % 8
                change = 2 * (1 if chosen else -1) * (1 if truth else -1)
                learned[key] = max(-12, min(12, learned[key] + change))
            recent = (chosen, truth)
            if energy == 0:
                death_tick = t + 1
            candidate = dict(tick=t, site=location, target=hidden, tie=tie, explore=explore,
                             noise=noise, port=chosen, feedback=truth, before=original_energy,
                             energy=energy, heat=heat, cost=3, collected=awarded,
                             packet_wasted=12 - awarded, memory_before=old_memory,
                             memory_after=learned[:], latest_before=old_recent,
                             latest_after=recent, expired=(energy == 0))
        # JSON serialisation changes tuples to arrays; ensure exact round-trip.
        assert json.loads(json.dumps(raw)) == json.loads(json.dumps(candidate)), f'event mismatch: {seed}/{arm}/tick {t}'
        assert energy + heat == 64 + 12 * (t + 1), 'energy conservation'
    expected = dict(successes=rewards, final_energy=energy, heat=heat,
                    died_at=death_tick, alive_through_end=(death_tick is None),
                    paid_instructions=charges, acquired_energy=gained,
                    packet_energy_offered=12 * DURATION,
                    source='researcher-authored generic plasticity')
    assert trial['summary'] == expected, f'wrong summary: {seed}/{arm}'
    assert trial['sha256'] == fingerprint({k: v for k, v in trial.items() if k != 'sha256'})
    return dict(seed=seed, arm=arm, successes=rewards, died_at=death_tick,
                charge=charges, gained=gained, audit_sha256=fingerprint(trial))


def audit_panel(trials):
    assert type(trials) is dict
    assert set(trials) == {(s, m) for s in SEEDS for m in MODES}
    rows = [audit_trial(trials[(seed, arm)]) for seed in SEEDS for arm in MODES]
    paired = {}
    for seed in SEEDS:
        scores = {arm: trials[(seed, arm)]['summary']['successes'] for arm in MODES}
        alive = trials[(seed, 'intact')]['summary']['alive_through_end']
        paired[seed] = bool(alive and all(scores['intact'] - scores[base] >= 20
                         for base in ('memory_disabled', 'misbound_history', 'latest_reactive', 'fixed')))
    banks = dict(primary=sum(paired[s] for s in SEEDS[:8]), unseen=sum(paired[s] for s in SEEDS[8:]))
    return dict(verified=True, trials=len(rows), opportunities=len(rows) * DURATION,
                actual_acquisitions=sum(r['successes'] for r in rows),
                total_paid_instructions=sum(r['charge'] for r in rows),
                banks=banks, registered_pass=all(v >= 6 for v in banks.values()),
                panel_audit_sha256=fingerprint(rows))
