"""Parse the complete local Python dependency closure without importing Ora."""
import ast
import hashlib
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]


def inspect():
    todo = list((ROOT / 'experiments').glob('digital_pilot74*.py'))
    seen = {}
    missing = []
    while todo:
        path = todo.pop()
        relative = path.relative_to(ROOT).as_posix()
        if relative in seen:
            continue
        raw = path.read_bytes()
        tree = ast.parse(raw, filename=relative)
        compile(tree, relative, 'exec')  # Compile only; never execute.
        seen[relative] = hashlib.sha256(raw).hexdigest()
        modules = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                modules.update(x.name for x in node.names if x.name.startswith('experiments.'))
            elif isinstance(node, ast.ImportFrom):
                if node.module == 'experiments':
                    modules.update('experiments.' + x.name for x in node.names)
                elif node.module and node.module.startswith('experiments.'):
                    modules.add(node.module)
        for name in modules:
            candidate = ROOT / (name.replace('.', '/') + '.py')
            if candidate.exists():
                todo.append(candidate)
            elif (ROOT / name.replace('.', '/') / '__init__.py').exists():
                todo.append(ROOT / name.replace('.', '/') / '__init__.py')
            else:
                missing.append(dict(source=relative, module=name))
    assert not missing, missing
    # Exact byte identity for changed launcher/native/tests, not merely AST parity.
    names = ['experiments/digital_pilot74_guardian_v1.py',
             'experiments/native/pilot74_guardian_failure_fixture_v1.c',
             'tests/test_digital_pilot74_launch_contract.py']
    tracked = subprocess.check_output(['git', 'ls-files'], cwd=ROOT, text=True).splitlines()
    for name in names:
        if name in tracked:
            blob = subprocess.check_output(['git', 'show', 'HEAD:' + name], cwd=ROOT)
            assert blob == (ROOT / name).read_bytes(), 'Commit/checkout byte mismatch: ' + name
    return dict(schema='PILOT74-STATIC-SOURCE-CLOSURE-v1', files=seen,
                parsed_modules=len(seen), missing=missing, execution=False,
                limitation='Static import graph only; dynamic role/runtime union and physical resource gates remain separate.')


if __name__ == '__main__':
    print(json.dumps(inspect(), indent=2))
