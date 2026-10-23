"""Read-only AST qualification; never import a World or query a seed."""
import ast
import hashlib
import json
from pathlib import Path

PINS = {
    'digital_pressure71_population.py': 'cf22e109878bae6ac6b22e0563c8593f1c93e8ac03296a9ed9cd0cd43e1400de',
    'digital_sharedlineage68_population.py': '624e861387ceac70e4c2413ed852228db08f6b1ebd774e442732650ae2103609',
}


def inspect_source(raw):
    tree = ast.parse(raw.decode('utf-8'))
    worlds = [n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == 'World']
    if len(worlds) != 1:
        raise ValueError('ambiguous World source')
    methods = {n.name: n for n in worlds[0].body if isinstance(n, ast.FunctionDef)}
    step = methods['step']
    channels = {}
    for n in ast.walk(step):
        if (isinstance(n, ast.Subscript) and isinstance(n.value, ast.Name)
                and n.value.id == 'e' and isinstance(n.slice, ast.Constant)
                and isinstance(n.slice.value, str)):
            channels.setdefault(n.slice.value, set()).add(type(n.ctx).__name__)
    restore = methods.get('restore')
    replay = False
    equality = False
    if restore:
        replay = any(isinstance(n, ast.While) and any(
            isinstance(c, ast.Call) and isinstance(c.func, ast.Attribute)
            and c.func.attr == 'step' for c in ast.walk(n)) for n in ast.walk(restore))
        equality = any(isinstance(n, ast.Assert) and isinstance(n.test, ast.Compare)
            and ast.unparse(n.test) == 'h(world.snapshot()) == h(state)'
            for n in ast.walk(restore))
    return {'channels': {k: sorted(v) for k, v in sorted(channels.items())},
            'restore_defined_here': restore is not None,
            'restore_replays_steps': replay, 'restore_requires_exact_history': equality}


def audit(root):
    result = {}
    for name, expected in PINS.items():
        raw = (Path(root) / 'experiments' / name).read_bytes()
        actual = hashlib.sha256(raw).hexdigest()
        if actual != expected:
            raise ValueError('source identity changed: ' + name)
        result[name] = {'sha256': actual, **inspect_source(raw)}
    base = result['digital_sharedlineage68_population.py']
    if not (base['restore_replays_steps'] and base['restore_requires_exact_history']):
        raise ValueError('restore premise no longer supported')
    required = {'memory', 'registers', 'feedback', 'code', 'pc', 'pos', 'inbox'}
    if not required.issubset(base['channels']):
        raise ValueError('channel premise no longer supported')
    return {'schema': 'ORA-EKA1-CAUSAL-SOURCE-AUDIT-v1', 'source_findings': result,
            'source_audit': 'PASS', 'causal_assay_qualified': False,
            'decision': 'NO_GO_FOR_CAUSAL_EXECUTION', 'worlds_authorized': 0,
            'vm_steps_executed': 0, 'new_seed_queries': 0,
            'limits': ['AST presence is not proof of information use or functional learning.',
                       'Memory-only erasure is neither complete nor certified nonlethal.',
                       'Exact-history restore does not provide an intervention API.',
                       'No intervention pricing, causal effect or nonlethality is verified.']}


if __name__ == '__main__':
    print(json.dumps(audit(Path(__file__).resolve().parents[1]), indent=2))
