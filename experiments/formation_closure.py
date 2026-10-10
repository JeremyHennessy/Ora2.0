"""Necessary structural formation preflight. No costed law or world dynamics."""
import itertools
import json
import sys


def closure(routes, initial):
    if (type(initial) is not int or not 0 <= initial < 8 or
            len(routes) != 3 or any(type(x) is not int or not 0 <= x < 8
                                    for x in routes)):
        raise ValueError("Three strict integer masks in0..7 required")
    available = initial
    while True:
        following = available
        for role, prerequisites in enumerate(routes):
            if prerequisites & available == prerequisites:
                following |= 1 << role
        if following == available:
            return available
        available = following


def census():
    rows = []
    for routes in itertools.product(range(8), repeat=3):
        for initial in range(8):
            final = closure(routes, initial)
            rows.append(dict(routes=list(routes), initial=initial,
                             closure=final, all_roles=final == 7))
    return dict(schema="formation-closure01-v1", cases=rows,
                costs="UNKNOWN", energy_admission=False, natural_worlds=0)


if __name__ == "__main__":
    json.dump(census(), sys.stdout, sort_keys=True, separators=(",", ":"))
    sys.stdout.write("\n")
