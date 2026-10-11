"""Supplied NON-learning clock; immutable Contingency15 law, fresh fixtures only."""
import base64
import json
import zlib
from experiments import digital_contingency15 as law

SEEDS = (26490, 26491)
ROUTES = ('clocked', 'witness', 'alternating', 'fixed0', 'fixed1')

def program():
    warm = []
    for index in range(7):
        warm.append([6, 0, 0])
        if index < 6:
            warm.append([5, 0, 1])
    return ([[4, 1, 1]] + warm +
            [[2, 0, 1], [5, 0, 1], [3, 1, 0], [8, 0, 19], [7, 0, 1],
             [6, 0, 0], [5, 0, 1]] + [[18, 0, 0] for _ in range(10)] +
            [[7, 0, 19]])

def history(seed, route):
    assert type(seed) is int and seed in SEEDS and route in ROUTES
    assert 'clocked' not in law.PROGRAMS
    law.PROGRAMS['clocked'] = program()
    try:
        return law.history(seed, route)
    finally:
        del law.PROGRAMS['clocked']

if __name__ == '__main__':
    import sys
    raw = json.dumps([history(int(sys.argv[1]), sys.argv[2])],
                     sort_keys=True, separators=(',', ':')).encode()
    print(base64.b64encode(zlib.compress(raw)).decode('ascii'))
