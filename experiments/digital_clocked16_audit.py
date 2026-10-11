"""Separate fixed-program derivation plus frozen full independent law interpreter."""
import json
from experiments.digital_contingency15_audit import audit as interpret

def expected_program():
    # Explicit table independent of the producer's program builder.
    return [[4,1,1], [6,0,0], [5,0,1], [6,0,0], [5,0,1], [6,0,0],
            [5,0,1], [6,0,0], [5,0,1], [6,0,0], [5,0,1], [6,0,0],
            [5,0,1], [6,0,0], [2,0,1], [5,0,1], [3,1,0], [8,0,19],
            [7,0,1], [6,0,0], [5,0,1], [18,0,0], [18,0,0], [18,0,0],
            [18,0,0], [18,0,0], [18,0,0], [18,0,0], [18,0,0], [18,0,0],
            [18,0,0], [7,0,19]]

def audit(row):
    assert type(row['seed']) is int and row['seed'] in (26490,26491)
    assert row['route'] in ('clocked','witness','alternating','fixed0','fixed1')
    if row['route'] == 'clocked':
        assert row['genesis_program'] == expected_program()
    result = interpret(row)
    if row['route'] == 'clocked':
        acts = [e for e in row['final']['events'] if e['decoded'][0] == 6]
        expected = [2,4,6,8,10,12,14,20,22,24,26,28,30,32]
        expected += list(range(37,513,13))
        assert [e['tick'] for e in acts] == [t for t in expected if t <= result['ticks']]
        assert all(e['decoded'][0] not in (0,1,9,10,12,13,14,15,16)
                   for e in row['final']['events'])
        assert result['formation_cost'] == 112
    return result

if __name__ == '__main__':
    import sys
    with open(sys.argv[1], encoding='utf-8') as stream:
        print(json.dumps([audit(row) for row in json.load(stream)],sort_keys=True))
