"""Reproduce the inactive V2 artifacts without modifying V1."""
import hashlib
import json
import sys
from pathlib import Path

def sha(raw):
    return hashlib.sha256(raw).hexdigest()

def encode(value):
    return (json.dumps(value, indent=2, sort_keys=True) + '\n').encode('ascii')

v1 = Path('D:/OraLab/drafts/ora-al02-production-installation')
old = (v1/'installed-binding-v1.json').read_bytes()
if sha(old) != '4da179bad479aadaec04d96483a6032bb33187593abc0ed45cd1493f0ed1a7fb':
    raise ValueError('Unexpected V1 binding')
b = json.loads(old)
pins = dict(b['installed_file_pins'])
for path, expected in pins.items():
    if sha(Path(path).read_bytes()) != expected:
        raise ValueError(f'Unexpected production bytes: {path}')
source = Path(__file__).resolve().parents[1]
changes = {}
for name in ('al02_one_pair_consent.py', 'al02_one_pair_custody.py'):
    relative = Path('experiments') / name
    target = str(Path(b['proposed_cwd']) / relative)
    changes[target] = dict(before=sha(Path(target).read_bytes()),
                           after=sha((source/relative).read_bytes()))
    if name.endswith('_custody.py'):
        pins[target] = changes[target]['after']
inventory = encode(pins)
base = 'a5b1cb72775314340d87b9b868c9b7232b00c78f'
binding = encode(dict(b, schema='ora.al02.installed-binding.v2', candidate_commit=base,
                      installed_file_pins=pins, source_inventory_sha256=sha(inventory),
                      engineering_status='Inactive V2 proposal'))
package = encode(dict(schema='AL02-INACTIVE-HUMAN-RELEASE-PACKAGE-v2', candidate=base,
                      production_head=b['production_git_head'], seed=str(b['seed']),
                      attempt=b['attempt'], scientific_authorization=False,
                      artifact_sha256={'installed-binding-v2.json':sha(binding),
                                       'source-pins-v2.json':sha(inventory)}))
files = {'source-pins-v2.json':inventory, 'installed-binding-v2.json':binding,
         'human-release-package-v2.json':package}
files['installation-verification-v2.json'] = encode(dict(
    scientific_authorization=False, replacements=changes,
    artifact_sha256={k:sha(v) for k,v in files.items()},
    dependency_order=['runtime excluding consent','inventory','binding','package',
                      'consent','external verification'],
    rollback='Restore byte-exact backups of both replacements and preserve any attempt claim.'))
out = Path(sys.argv[1])
out.mkdir(exist_ok=True)
for name, raw in files.items():
    path = out / name
    if path.exists():
        if path.read_bytes() != raw:
            raise ValueError(f'Refusing changed artifact: {path}')
    else:
        with path.open('xb') as stream:
            stream.write(raw)
print(sha(binding), sha(package))
