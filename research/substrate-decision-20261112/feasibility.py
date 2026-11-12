"""Authored scalar engineering fixtures only. No VM, World, reproduction or search."""
import itertools
import json


def bit(value):
    if type(value) is not int or value not in (0, 1):
        raise ValueError('Expected one exact binary integer')
    return value


def nand(a, b):
    return 1 - bit(a) * bit(b)


def authored_response(cue, probe, gap, erase=False):
    """Hand-authored mathematical witness; forbidden as a scientific founder."""
    bit(cue)
    bit(probe)
    if type(gap) is not int or not 0 <= gap <= 31:
        raise ValueError('Engineering fixture delay outside bound')
    remembered = cue
    for _ in range(gap):
        pass  # declared charged delay, no evolving state or simulation
    if erase:
        remembered = 0
    q = nand(remembered, probe)
    t = nand(remembered, q)
    u = nand(probe, q)
    output = nand(t, u)
    # one cue acquisition, gap charges, one probe, four NANDs, one output
    return output, gap + 7


def qualify():
    truth = []
    for gap in range(32):
        correct = erased_correct = 0
        for x, y in itertools.product((0, 1), repeat=2):
            actual, charged = authored_response(x, y, gap)
            erased, _ = authored_response(x, y, gap, erase=True)
            assert actual == (x + y) % 2  # independent parity definition
            assert charged == gap + 7
            correct += actual == (x + y) % 2
            erased_correct += erased == (x + y) % 2
        assert correct == 4 and erased_correct == 2
        truth.append({'gap': gap, 'correct_of_four': correct,
                      'erased_correct_of_four': erased_correct,
                      'scalar_charge': gap + 7})
    memoryless = []
    for f0, f1 in itertools.product((0, 1), repeat=2):
        count = sum((f0, f1)[y] == (x + y) % 2
                    for x, y in itertools.product((0, 1), repeat=2))
        assert count == 2
        memoryless.append({'f0': f0, 'f1': f1, 'correct_of_four': count})
    for args in [(True, 0, 1), (2, 0, 1), (0, -1, 1), (0, 0, 32),
                 (0, 0, -1), (0, 0, 1.5)]:
        try:
            authored_response(*args)
        except ValueError:
            continue
        raise AssertionError('Malformed fixture accepted')
    return {'classification': 'AUTHORED NON-SCIENTIFIC SCALAR PROOF',
            'worlds': 0, 'populations': 0, 'evolutionary_searches': 0,
            'scientific_attempts': 0, 'memoryless_maps': memoryless,
            'truth_tables': truth,
            'limit': 'Not a runtime, viable mutation, scheduling or fitness proof'}


if __name__ == '__main__':
    print(json.dumps(qualify(), indent=2, sort_keys=True))
