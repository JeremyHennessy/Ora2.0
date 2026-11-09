"""Fixed campaign scope. This module contains no execution entry."""
import hashlib
import json
from pathlib import Path

TOKEN = 'AL02-NATURAL-B-PANEL-20261109-v1'
ROOT = Path('D:/OraLab')
CHECKOUT = ROOT/'src/Ora2.0-al02-first-depletion-20261109'
DESTINATION = ROOT/'reports/al02-natural-b-campaign-attempts-20261109'
ARTIFACTS = ROOT/'reports/ora-al02-natural-b-panel-20261109'
CONTEXTS_SHA256 = '065149a3c3aa278c9dbc14527a8f54e354602e6ebcd3a87360cf20fa6e377804'
BINDING_SHA256 = 'c1711e6b33ad9784bf408cc92345998758ef9f4c590d680290aba30da5ef4e0b'
PACKAGE_SHA256 = '50d0d3995e2b9358db4a79b02c6e00f439604012fdf55360c65012b05edef06b'
AUTHORIZATION_SHA256 = None
OWNER = 'hennessydesktop\\hennessy'
LIMITS = dict(cpu_seconds=5, wall_seconds=10, memory_bytes=134217728, processes=3)
STOP = ROOT/'automation/ora-codex/STOP'


def read_pinned(path, expected):
    with path.open('rb') as stream:
        raw = stream.read(131073)
    if len(raw) > 131072 or hashlib.sha256(raw).hexdigest() != expected:
        raise ValueError(f'Campaign artifact identity differs: {path.name}')
    return json.loads(raw)


def inventory():
    rows = read_pinned(ARTIFACTS/'contexts.json', CONTEXTS_SHA256)
    if len(rows) != 128:
        raise ValueError('Campaign requires 128 contexts')
    seen = {8195177122164069225}
    for index, row in enumerate(rows):
        digest = hashlib.sha256(row['context'].encode('ascii')).hexdigest()
        seed = int(digest[:16],16)
        if (row['index'] != index or row['attempt'] != f'attempt-{index:03d}'
                or row['seed'] != seed or row['context_sha256'] != digest or seed in seen):
            raise ValueError('Campaign context mapping differs')
        seen.add(seed)
    return rows


def binding():
    b = read_pinned(ARTIFACTS/'campaign-binding.json', BINDING_SHA256)
    p = read_pinned(ARTIFACTS/'campaign-package.json', PACKAGE_SHA256)
    if (b['schema'] != 'al02-campaign-binding-v1' or p['schema'] != 'al02-campaign-package-v1'
            or b['scientific_authorization'] is not False or p['scientific_authorization'] is not False
            or p['binding_sha256'] != BINDING_SHA256
            or b['contexts_sha256'] != CONTEXTS_SHA256 or b['limits'] != LIMITS
            or b['destination'] != str(DESTINATION) or b['checkout'] != str(CHECKOUT)):
        raise ValueError('Campaign binding scope differs')
    return b


def admitted(directory, cwd, command, owner, context, limits, pins):
    if STOP.exists():
        raise ValueError('STOP present')
    pilot = directory.parent == PILOT_DESTINATION
    b = pilot_binding() if pilot else binding()
    root = PILOT_DESTINATION if pilot else DESTINATION
    rows = inventory()[:8] if pilot else inventory()
    candidates = [row for row in rows if root/row['attempt'] == directory]
    if len(candidates) != 1:
        raise ValueError('Campaign destination differs')
    row = candidates[0]
    expected = [b['python'], '-I', '-S', '-B', b['worker'],
                str(directory/'00-pending.json'), TOKEN]
    if (cwd != CHECKOUT or owner != OWNER or context != row['context_sha256']
            or limits != LIMITS or list(command) != expected
            or not b['pins'].items() <= pins.items()):
        raise ValueError('Campaign admission scope differs')
    authority_pin = PILOT_AUTHORIZATION_SHA256 if pilot else AUTHORIZATION_SHA256
    if authority_pin is None:
        raise ValueError('Campaign scientific authorization absent')
    if pilot:
        authority = read_pinned(root/'pilot-authority.json',authority_pin)
        if authority != dict(schema='al02-supervised-eight-one-claim-per-index-v1',owner=OWNER,
                             pilot_binding_sha256=PILOT_BINDING_SHA256):
            raise ValueError('Pilot authority scope differs')
        return dict(authorization_sha256=authority_pin,binding_sha256=BINDING_SHA256,
                    package_sha256=PACKAGE_SHA256,contexts_sha256=CONTEXTS_SHA256,
                    pilot_binding_sha256=PILOT_BINDING_SHA256,context_index=row['index'],seed=row['seed'])
    authority = read_pinned(DESTINATION/'campaign-authority.json', AUTHORIZATION_SHA256)
    if authority != dict(schema='al02-campaign-one-claim-per-index-v1', owner=OWNER,
                         binding_sha256=BINDING_SHA256, package_sha256=PACKAGE_SHA256,
                         contexts_sha256=CONTEXTS_SHA256):
        raise ValueError('Campaign authority scope differs')
    return dict(authorization_sha256=AUTHORIZATION_SHA256, binding_sha256=BINDING_SHA256,
                package_sha256=PACKAGE_SHA256, contexts_sha256=CONTEXTS_SHA256,
                context_index=row['index'], seed=row['seed'])


PILOT_DESTINATION = ROOT/'reports/al02-supervised-eight-attempts-20261109'
PILOT_BINDING_SHA256 = 'c12a44cd19ba01f5b84b4f2467835797b09c645a39b1209aeb1aa086a1e292c5'
PILOT_AUTHORIZATION_SHA256 = None


def pilot_binding():
    base = binding()
    pilot = read_pinned(ARTIFACTS/'supervised-eight-binding.json', PILOT_BINDING_SHA256)
    expected = dict(schema='al02-supervised-eight-v1', scientific_authorization=False,
                    campaign_binding_sha256=BINDING_SHA256, campaign_package_sha256=PACKAGE_SHA256,
                    contexts_sha256=CONTEXTS_SHA256, destination=str(PILOT_DESTINATION),
                    indices=list(range(8)), policy='verified-custody-then-batch-review',
                    budget=dict(base['budget'],pairs=8,instructions=9600,cpu_seconds=40,
                                job_wall_seconds=80,archive_bytes=67108864))
    if pilot != expected:
        raise ValueError('Supervised pilot binding differs')
    return dict(base, destination=str(PILOT_DESTINATION),budget=pilot['budget'])
