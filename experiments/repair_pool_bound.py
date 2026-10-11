"""Optimistic sharing bound versus attainable pre-loss local reserves."""
from fractions import Fraction
import itertools
import json
import sys


def case(stock, repair, gain, transfer):
    if any(type(x) is not int or x <= 0 for x in (stock, repair, gain, transfer)):
        raise ValueError('Positive integer work quantities required')
    covered = min(4, stock // repair)
    q = Fraction(covered, 4)
    frontier = (1-q)*gain-transfer
    witness = [repair if i < covered else 0 for i in range(4)]
    return dict(stock=stock, repair=repair, gain=gain, transfer=transfer,
                covered_losses=covered, allocation=witness,
                independent_output=[(stock+q*gain).numerator,
                                    (stock+q*gain).denominator],
                pool_output_before_extra_cost=stock+gain-transfer,
                extra_cost_frontier=[frontier.numerator, frontier.denominator],
                pool_funded=stock >= repair+transfer,
                positive_frontier=frontier > 0)


def census():
    return dict(schema='repair-pool01-v1',
                cases=[case(*x) for x in itertools.product(
                    range(1,13), range(1,13), range(1,5), range(1,4))],
                common_cost='UNKNOWN', extra_apparatus_cost='UNKNOWN',
                mechanism_admitted=False, natural_worlds=0)


if __name__ == '__main__':
    json.dump(census(), sys.stdout, sort_keys=True, separators=(',', ':'))
    sys.stdout.write('\n')
