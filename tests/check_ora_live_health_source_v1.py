"""Source-byte/AST check only;no World/runtime imports or old-suite replays."""
from pathlib import Path
import ast,hashlib,json,subprocess
root=Path(__file__).resolve().parents[1]
pins=json.loads((root/'data/ora-live-health-inherited-source-pins-v1.json').read_text())
for name,expected in pins.items():
    assert hashlib.sha256((root/name).read_bytes()).hexdigest()==expected,name
for name in ['experiments/ora_live_task_bounds_v1.py','experiments/ora_runtime_health_review_v8.py']:
    raw=(root/name).read_bytes();ast.parse(raw);pins[name]=hashlib.sha256(raw).hexdigest()
print(json.dumps(dict(head_sha=subprocess.check_output(['git','rev-parse','HEAD'],cwd=root,text=True).strip(),
    source_hashes=pins,worlds=0,model_calls=0,live_store_access=False),sort_keys=True))
