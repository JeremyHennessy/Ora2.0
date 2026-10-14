"""Frozen coherent scaffold with blind update atoms; no environment imports."""
import hashlib
import json
from experiments.digital_experience75_source import references as old_references

VERSION = 'DIGITAL-COGNITIVE76-SOURCE-v1'
OPS = (0, 1, 2, 3, 4, 5, 6, 7, 8, 18, 19, 20, 21)
UPDATE_OPS = (4, 5, 18, 21)
PREFIX = [[4,1,1], [6,0,0], [5,0,1], [6,0,0], [18,0,0]]
REFERENCES = tuple(old_references()) + ('fixed_cognitive',)

def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':')).encode()).hexdigest()

def compile_atoms(atoms):
    if type(atoms) is not list or len(atoms) != 2 or any(
        type(t) is not list or len(t) != 3 or any(type(v) is not int for v in t)
        or t[0] not in UPDATE_OPS or t[1] != 0 or not 0 <= t[2] < 32 for t in atoms
    ):
        raise ValueError('Two typed prediction-register update atoms required')
    return [t[:] for t in PREFIX] + [
        [0,1,0], [19,0,1], [6,0,0], [1,0,0], [8,0,12],
        [7,0,5], [18,0,0], [19,0,1], [21,0,0], [6,0,0],
        [19,0,1], *[t[:] for t in atoms], [20,1,0], [7,0,5],
    ]

def candidate(sample):
    if type(sample) is not int or not 0 <= sample < 16:
        raise ValueError('Frozen founder id required')
    atoms = []; draws = []
    for slot in range(2):
        values = {}
        for field in ('opcode', 'operand'):
            certificate = digest(['cognitive76-source',76,sample,slot,field])
            draw = int(certificate[:16],16)
            value = UPDATE_OPS[draw % 4] if field == 'opcode' else draw % 32
            values[field] = value
            draws.append(dict(slot=slot, field=field, sha256=certificate,
                              low64_decimal=str(draw), value=value))
        atoms.append([values['opcode'],0,values['operand']])
    code = compile_atoms(atoms)
    return dict(sample_id=sample, program=code, program_sha256=digest(code),
                draws=draws, parent=None, founder='researcher supplied coherent grammar',
                performance_selection=False, resampling=False)

def references():
    result = {name: code + [[18,0,0] for _ in range(6)]
              for name, code in old_references().items()}
    result['fixed_cognitive'] = compile_atoms([[18,0,0],[18,0,0]])
    return result

def programmes():
    return {**{f'candidate{i}':candidate(i)['program'] for i in range(16)}, **references()}

def manifest():
    return dict(version=VERSION, candidates=[candidate(i) for i in range(16)],
                references=references(), assembly_words=76, performance_selection=False,
                targets_queried=0, worlds=0, stage_credit=False)
