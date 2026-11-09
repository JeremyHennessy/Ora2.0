import json,hashlib,sys
from pathlib import Path
r=Path(sys.argv[1])
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
b=json.loads((r/'campaign-binding.json').read_bytes())
p=dict(schema='al02-supervised-eight-v1',scientific_authorization=False,
       campaign_binding_sha256=sha(r/'campaign-binding.json'),campaign_package_sha256=sha(r/'campaign-package.json'),
       contexts_sha256=sha(r/'contexts.json'),
       destination=str(Path('D:/OraLab/reports/al02-supervised-eight-attempts-20261109')),
       indices=list(range(8)),policy='verified-custody-then-batch-review',
       budget=dict(b['budget'],pairs=8,instructions=9600,cpu_seconds=40,job_wall_seconds=80,archive_bytes=67108864))
raw=(json.dumps(p,sort_keys=True,indent=2)+'\n').encode()
with (r/'supervised-eight-binding.json').open('xb') as f:f.write(raw)
print(hashlib.sha256(raw).hexdigest())
