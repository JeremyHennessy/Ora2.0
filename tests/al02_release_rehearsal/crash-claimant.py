import json, os, sys, time
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path.cwd()))
from experiments import al02_one_pair as pair, al02_one_pair_consent as consent
from experiments import al02_one_pair_custody as custody

config = json.loads(Path(sys.argv[1]).read_bytes())
scope = config['scope']
for name in ('WORKTREE', 'ATTEMPT', 'WORKER', 'STOP', 'BINDING', 'V2_DRAFT'):
    scope[name] = Path(scope[name])
root = Path(sys.argv[1]).parent
assert scope['ATTEMPT'].parent == root
assert scope['STOP'].parent == root
assert scope['CONSENT'] == 'ORA-PHASE6-INERT'
assert scope['WORKER'].name == 'inert-worker.py'
(root / f'ready-{sys.argv[2]}').touch()
deadline = time.monotonic() + 10
while not (root / 'go').exists():
    if time.monotonic() > deadline:
        raise TimeoutError('Race start barrier')
    time.sleep(.01)
real_mkdir = Path.mkdir
def claim_boundary(path, *args, **kwargs):
    if path == scope['ATTEMPT'] and sys.argv[2] == 'before':
        os._exit(41)
    result = real_mkdir(path, *args, **kwargs)
    if path == scope['ATTEMPT'] and sys.argv[2] == 'after':
        os._exit(42)
    return result
with patch.object(Path, 'mkdir', claim_boundary), patch.multiple(consent, **scope), patch.multiple(pair, SEED=42, CONTEXT_SHA256=scope['CONTEXT']):
    try:
        result = custody.transaction(scope['ATTEMPT'], command=config['command'],
            cwd=scope['WORKTREE'], pins=config['pins'], expected_account=consent.OWNER,
            context=scope['CONTEXT'], referee=pair.verify, consent=scope['CONSENT'])
    except FileExistsError:
        print('claim lost')
    else:
        assert result['contrast'] == 3
        print('claim won')
