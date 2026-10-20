"""Scripted VM-free C stand-in; not a scientific role implementation."""
import hashlib
import json
from pathlib import Path
import sys

raw=Path(sys.argv[2]).read_bytes()
assert len(raw)==int(sys.argv[3]) and hashlib.sha256(raw).hexdigest()==sys.argv[4]
request=json.loads(raw)
assert request['fixture'] is True
print(json.dumps(dict(ordinal=request['ordinal'],fixture=True)),flush=True)
raise SystemExit(78 if request['ordinal'] in (16,18,20) else 0)
