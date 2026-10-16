"""Source-only portable AST binding; no experiment module execution."""
import ast,hashlib,json
from pathlib import Path
root=Path(__file__).resolve().parents[1]
receipt=json.loads((root/'docs/context90-source-qualification.json').read_bytes())
for relative,expected in receipt['semantic_ast'].items():
 p=root/relative
 actual=hashlib.sha256(ast.dump(ast.parse(p.read_bytes()),include_attributes=False).encode()).hexdigest()
 if actual!=expected:raise RuntimeError('Unqualified semantic source: '+relative)
print('Exact qualified semantics bound; only new layout check admitted. No World/task execution.')
