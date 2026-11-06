"""Arithmetic verification of retained data only; does not execute policies."""
import argparse
import hashlib
import json
from pathlib import Path


def digest(value):
    return hashlib.sha256(json.dumps(value, separators=(',', ':'), sort_keys=True).encode()).hexdigest()


def verify(path):
    r = json.loads(path.read_text(encoding='utf-8'))
    assert not r['scientific_population'] and not r['evolution_demonstrated'] and r['births'] == 0
    dev = r['development']
    totals = {k: sum(x['score'] for x in v) for k, v in dev.items()}
    assert totals == r['selection']['development_totals']
    assert r['selection_sha256'] == digest(r['selection'])
    best_candidate = min((k for k in totals if k.startswith('counter')), key=lambda k: (-totals[k], k))
    best_ref = min((k for k in totals if not k.startswith('counter')), key=lambda k: (-totals[k], k))
    assert best_candidate == r['selection']['candidate']['name']
    assert best_ref == r['selection']['reference']['name']
    assert set(w['seed'] for w in r['development_worlds']) == set(range(1000, 1016))
    assert set(w['seed'] for w in r['validation_worlds']) == set(range(9000, 9032))
    lives, traced, events = 0, 0, 0
    for records in list(dev.values())+list(r['validation'].values())+list(r['causal_arms'].values()):
        for x in records:
            lives += 1
            assert x['remaining_energy'] == 8192-sum(x['costs'].values())+x['delivered_food']-x['overflow_heat']
            assert x['score'] == (x['remaining_energy'] if x['alive'] else 0)
            assert x['delivered_food'] == x['delivered_successes']*512
            assert x['delivered_successes'] <= x['successful_attempts'] <= x['attempts'] <= 384
            if 'trace' in x:
                traced += 1
                tr = x['trace']
                assert digest(tr) == x['trace_sha256']
                prev = 8192-x['costs']['formation']
                for i, e in enumerate(tr):
                    assert e[0] == i and e[1] == prev
                    assert e[2] == e[1]-e[3]+e[4]-e[5]
                    prev = e[2]
                assert prev == x['remaining_energy']
                assert sum(e[3] for e in tr) == sum(x['costs'].values())-x['costs']['formation']
                assert sum(e[4] for e in tr) == x['delivered_food']
                assert sum(e[5] for e in tr) == x['overflow_heat']
                assert sum(e[8] >= 0 for e in tr) == x['attempts']
                events += len(tr)
    own = r['causal_arms']['true']
    ref = r['validation'][best_ref]
    differences = [a['score']-b['score'] for a, b in zip(own, ref)]
    gaps = {a: sum(x['score'] for x in own)-sum(x['score'] for x in v)
            for a, v in r['causal_arms'].items() if a != 'true'}
    primary = dict(passed=sum(differences) > 0 and sum(x > 0 for x in differences) >= 24 and all(x > 0 for x in gaps.values()),
                   paired_score_differences=differences, positive_worlds=sum(x > 0 for x in differences),
                   mean_energy_difference=sum(differences)/32/64, ablation_total_gaps=gaps)
    assert primary == r['primary']
    return dict(status='RETAINED_ARITHMETIC_PASS_NOT_POLICY_REPLAY', lives=lives,
                traced_lives=traced, traced_events=events, primary=primary,
                result_sha256=hashlib.sha256(path.read_bytes()).hexdigest())


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('path', type=Path)
    args = parser.parse_args()
    print(json.dumps(verify(args.path), indent=2))
