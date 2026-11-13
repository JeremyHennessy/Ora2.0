"""Finite optimistic accounting bound, not organism or population execution.

New authored boundary assumptions: event6 blind genotype0; energy8 initially;
atomic paid probes; death at resulting energy0; free instantaneous copying at
any operation boundary, including horizon. No competition, material/time limit,
decoder overhead or formation debit on parent. These relaxations favor copying.
"""
import argparse
from functools import lru_cache
import hashlib
from itertools import product
import json
from pathlib import Path

PROTOCOL = dict(schema='ORA-EVENT6-BLIND-FUNDING-UPPERBOUND-v1', startup=8,
                copy_fee=22, reward=8, code_bits=6, attempts=1,
                cases={'development': [3, [0, 1]], 'reused_validation': [4, [2, 3]]},
                controller_executions=0, population_executions=0,
                copy_placement='clairvoyant, instantaneous, any boundary including horizon',
                payment='require pre-energy >= cost; atomically debit then reward; death if resulting zero',
                ecology='independent uniform fresh binary strings only; no competition',
                scope='conditional upper bound for event6 blind genotype0 only')


def upper(operations, energy=8, fee=22):
    """Return maximum possible copies over a fixed finite paid operation ledger."""
    @lru_cache(None)
    def solve(i, e):
        if e == 0:
            return 0
        best = 1 + solve(i, e-fee) if e >= fee else 0
        if i < len(operations):
            cost, gain = operations[i]
            if e >= cost:
                best = max(best, solve(i+1, e-cost+gain))
        return best
    return solve(0, energy)


def ledger(targets, delay):
    operations = []
    for target in targets:
        operations += [(1, 0), (2, 0)] + [(1, 0)]*delay
        operations += [(1, 8 if target == 0 else 0)]*2
    return tuple(operations)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    result = {'protocol': PROTOCOL, 'source_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
              'cases': [], 'summary': {}}
    for name, (length, delays) in PROTOCOL['cases'].items():
        values = []
        for targets in product((0, 1), repeat=length):
            for delay in delays:
                operations = ledger(targets, delay)
                count = upper(operations)
                values.append(count)
                result['cases'].append(dict(split=name, targets=targets, delay=delay,
                    operations=operations, maximum_copies=count))
        total, n = sum(values), len(values)
        result['summary'][name] = dict(cases=n, total_maximum_copies=total,
            R_upper_numerator=total, R_upper_denominator=n,
            zero_copy_cases=values.count(0), maximum=max(values),
            conditional_descendants_upper_fraction=[total, n-total] if total < n else None)
    with args.output.open('x', encoding='utf-8') as out:
        json.dump(result, out, indent=2)


if __name__ == '__main__':
    main()
