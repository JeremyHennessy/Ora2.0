"""Generate immutable inactive continuation records without replacing any bytes."""
from hashlib import sha256
import json
from pathlib import Path
import sys
from experiments import al02_campaign_admission as gate

def encode(data):
    return (json.dumps(data,sort_keys=True,indent=2)+'\n').encode('ascii')

def build(root):
    binding=encode(gate.continuation_spec())
    package=encode(dict(schema='al02-supervised-continuation-package-v1',
        scientific_authorization=False,binding_sha256=sha256(binding).hexdigest(),
        contexts_sha256=gate.CONTEXTS_SHA256))
    for name,raw in [('continuation-binding.json',binding),('continuation-package.json',package)]:
        path=root/name
        if path.exists():
            if path.read_bytes()!=raw:
                raise ValueError(f'Refusing to replace {name}')
        else:
            with path.open('xb') as stream:stream.write(raw)
    return sha256(binding).hexdigest(),sha256(package).hexdigest()

if __name__=='__main__':
    print(*build(Path(sys.argv[1])))
