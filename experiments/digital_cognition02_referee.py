"""Second independent decision/resource interpreter; never imports producer module."""
import hashlib
import json

MODES = ('quick_memory', 'historic_memory', 'memory_disabled', 'misbound_history',
         'latest_reactive', 'fixed', 'constant0', 'constant1')
SEEDS = tuple(range(78400, 78408)) + tuple(range(78600, 78608))


def sha(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=True).encode()).hexdigest()


def rnd(*parts):
    return int(sha(list(parts))[:16], 16)


def audit_trial(obj):
    assert set(obj) == {'version', 'seed', 'arm', 'events', 'summary', 'sha256'}
    assert obj['version'] == 'DIGITAL-COGNITION02-v1'
    seed, arm = obj['seed'], obj['arm']
    assert type(seed) is int and seed in SEEDS and arm in MODES and len(obj['events']) == 256
    weight, prev, energy, heat, good, death, charged, intake = [0] * 8, None, 64, 0, 0, None, 0, 0
    for tick, row in enumerate(obj['events']):
        site = tick % 8
        target = rnd('COGNITION01-target', seed, site) % 2 ^ int(tick >= 128)
        tie = rnd('COGNITION01-tie', seed, tick) % 2
        explore = rnd('COGNITION01-explore', seed, tick) % 16 == 0
        noise = rnd('COGNITION01-noise', seed, tick) % 2
        was, before, last = energy, weight[:], prev
        if death is not None or energy < 3:
            if death is None:
                death = tick
                heat += energy
                energy = 0
            heat += 12
            expected = dict(tick=tick, site=site, target=target, tie=tie, explore=explore,
                            noise=noise, port=None, feedback=None, before=was,
                            energy=energy, heat=heat, cost=0, collected=0,
                            packet_wasted=12, memory_before=before, memory_after=weight[:],
                            latest_before=last, latest_after=prev, expired=True)
        else:
            if arm in ('quick_memory', 'historic_memory', 'misbound_history'):
                val = weight[site]
                port = 1 if val > 0 else 0 if val < 0 else tie
            elif arm == 'latest_reactive':
                port = tie if prev is None else prev[0] if prev[1] else 1 - prev[0]
            elif arm == 'fixed':
                port = rnd('COGNITION01-fixed', seed, site) % 2
            else:
                port = 0 if arm == 'constant0' else 1 if arm == 'constant1' else tie
            port = noise if explore else port
            feedback = int(port == target)
            energy -= 3
            heat += 3
            acquired = min(12, 64 - energy) if feedback else 0
            heat += 12 - acquired
            energy += acquired
            good += feedback
            charged += 3
            intake += acquired
            if arm in ('quick_memory', 'historic_memory', 'misbound_history'):
                dest = (site + 1) % 8 if arm == 'misbound_history' else site
                bound = 12 if arm == 'historic_memory' else 2
                difference = 2 * (1 if port else -1) * (1 if feedback else -1)
                weight[dest] = max(-bound, min(bound, weight[dest] + difference))
            prev = (port, feedback)
            if energy == 0:
                death = tick + 1
            expected = dict(tick=tick, site=site, target=target, tie=tie, explore=explore,
                            noise=noise, port=port, feedback=feedback, before=was,
                            energy=energy, heat=heat, cost=3, collected=acquired,
                            packet_wasted=12 - acquired, memory_before=before,
                            memory_after=weight[:], latest_before=last, latest_after=prev,
                            expired=energy == 0)
        assert json.loads(json.dumps(row)) == json.loads(json.dumps(expected)), (seed, arm, tick)
        assert energy + heat == 64 + 12 * (tick + 1)
    summary = dict(successes=good, final_energy=energy, heat=heat, died_at=death,
                   alive_through_end=death is None, paid_instructions=charged,
                   acquired_energy=intake, packet_energy_offered=12 * 256,
                   source='researcher-authored generic rapid-revision plasticity')
    assert obj['summary'] == summary
    assert obj['sha256'] == sha({key: value for key, value in obj.items() if key != 'sha256'})
    return dict(seed=seed, arm=arm, successes=good, charges=charged, died_at=death,
                forensic_sha256=sha(obj))


def audit_panel(trials):
    assert set(trials) == {(seed, arm) for seed in SEEDS for arm in MODES}
    proofs = [audit_trial(trials[seed, arm]) for seed in SEEDS for arm in MODES]
    bank = {'primary': 0, 'unseen': 0}
    for seed in SEEDS:
        a = {arm: trials[seed, arm]['summary'] for arm in MODES}
        score = a['quick_memory']['successes']
        qualifies = a['quick_memory']['alive_through_end'] and all(
            score - a[alt]['successes'] >= 20 for alt in
            ('historic_memory', 'memory_disabled', 'misbound_history', 'latest_reactive', 'fixed'))
        bank['primary' if seed in SEEDS[:8] else 'unseen'] += int(qualifies)
    return dict(verified=True, banks=bank, registered_pass=all(x >= 6 for x in bank.values()),
                trials=len(proofs), opportunities=256 * len(proofs),
                total_acquisitions=sum(x['successes'] for x in proofs),
                total_cost=sum(x['charges'] for x in proofs),
                proof_sha256=sha(proofs))
