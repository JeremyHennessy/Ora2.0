"""Consent boundary for the single AL02 lower-assurance attempt."""

import hashlib
import json
from pathlib import Path

TIER = 'LOW_ASSURANCE_EXPLORATORY'
CONSENT = 'JeremyHennessy/Ora2.0#328:6740691539'
SUCCESSOR = 'AL02-SUCCESSOR-20261109-v3'
CONTEXT = '71bb1e2c35ff536900807c5c0ee86d30c13722b85291a8e8f086c0c62dc934b8'
SEED = 8195177122164069225
OWNER = 'hennessydesktop\\hennessy'
LIMITS = dict(memory_bytes=134217728, cpu_seconds=5, processes=3, wall_seconds=10)
ROOT = Path('D:/OraLab')
WORKTREE = ROOT / 'src/Ora2.0-al02-first-depletion-20261109'
ATTEMPT = ROOT / 'reports/al02-first-depletion-exploratory-20261109/attempt-6740691539'
SUCCESSOR_ATTEMPT = ROOT / 'reports/al02-first-depletion-successor-20261109/attempt-v3'
WORKER = WORKTREE / 'experiments/al02_one_pair_worker.py'
STOP = ROOT / 'automation/ora-codex/STOP'
APPROVED_WORKER_SHA256 = '7ba6d4ee9a5b4072ad7f7cb09afdcc610689b55aa6829e1d45bd90f1d779a824'
BINDING = ATTEMPT.parent / 'one-pair-production-binding.json'
BINDING_SHA256 = '18c144b6f89a62c39cf97630d9577604074b48ad54519bdd2813589cdba3f0ef'


def check_scope(directory, cwd, command, owner, context, limits):
    """The consent can bind only one worker shape, context and evidence destination."""
    release = command[-1] if command else None
    target = SUCCESSOR_ATTEMPT if release == SUCCESSOR else ATTEMPT
    if (release not in (CONSENT, SUCCESSOR) or Path(directory) != target or Path(cwd) != WORKTREE or owner != OWNER
            or context != CONTEXT or limits != LIMITS or len(command) != 7
            or tuple(command[1:]) != ('-I', '-S', '-B', str(WORKER),
                                      str(target / '00-pending.json'), release)):
        raise ValueError('Outside explicit AL02 lower-assurance consent scope')
    if STOP.exists():
        raise ValueError('STOP present')


def check_manifest(raw, digest, *, command, owner, context, limits):
    if hashlib.sha256(raw).hexdigest() != digest:
        raise ValueError('Pending manifest digest mismatch')
    data = json.loads(raw)
    expected = dict(command=list(command), owner=owner, context=context, limits=limits,
                    consent=command[-1], evidence_tier=TIER)
    if any(data.get(key) != value for key, value in expected.items()):
        raise ValueError('Pending manifest does not bind the approved scope')


def require_bound_worker(pins, command, relay_argv):
    # A caller-provided hash is not approval of a newly supplied worker.
    if command and command[-1] == SUCCESSOR:
        return _require_candidate(pins, command, relay_argv, successor=True)
    if APPROVED_WORKER_SHA256 is None:
        raise ValueError('No reviewed scientific worker with a pinned import closure')
    if pins.get(str(WORKER)) == CANDIDATE_WORKER:
        return _require_candidate(pins, command, relay_argv)
    if pins.get(str(WORKER)) != APPROVED_WORKER_SHA256:
        raise ValueError('Scientific worker pin differs from approved worker')
    with BINDING.open('rb') as stream:
        raw = stream.read(128 * 1024 + 1)
    if len(raw) > 128 * 1024 or hashlib.sha256(raw).hexdigest() != BINDING_SHA256:
        raise ValueError('Production binding manifest differs')
    binding = json.loads(raw)
    if (binding['command'] != list(command) or binding['relay_argv'] != relay_argv
            or binding['context'] != CONTEXT or binding['seed'] != SEED
            or not binding['pins'].items() <= pins.items()):
        raise ValueError('Production argv, context or required closure differs')


CANDIDATE_WORKER = 'c7671dd28f8a87a60145d6c310df62b4799a1a4a60132781fb323bb2f415cf35'
CANDIDATE_BINDING = '4da179bad479aadaec04d96483a6032bb33187593abc0ed45cd1493f0ed1a7fb'
CANDIDATE_PACKAGE = '9f01cd5355961fa769efd38fc5cb956fb0abbdfa59cf6423169c4cc5e7843208'
RELEASE_DRAFT = ROOT / 'drafts/ora-al02-production-installation'
CANDIDATE_AUTHORIZATION_SHA256 = None
V2_DRAFT = ROOT / 'drafts/ora-al02-release-v2'
V2_CUSTODY = '5c092df6e0bd0b8c61f2bf6556a30b3cfa7780cbaf0cd1f47b54861a9834bf47'
V2_BINDING = 'dbf11f4ba6dfecdbc205d392176e186b9072d682d2de229a20f025e5639a3327'
V2_PACKAGE = '380087f218147745a1e06bd51f47dfe841255415126a5d156b483654d700104e'
V2_AUTHORIZATION_SHA256 = None
V3_DRAFT = ROOT / 'drafts/ora-al02-release-v3'
V3_WORKER = 'dc4b8e19cb7b9869e313c86fd163d94223b7e43487d044b2c1db81e1b3761fc9'
V3_CUSTODY = '6c0c52ae86ed5b946b8839a06982249b0030f6e583c12380b2b391afad1ec400'
V3_BINDING = '633856cddad0c24182f4ced25cf608d34359c77e9cbb019752e2b342b7571b11'
V3_PACKAGE = 'fd7a6bbaa7f9e7b436261993642fd27aac293783e586a53e3dbfc4c17562719e'
V3_AUTHORIZATION_SHA256 = None


def _read_pinned_record(path, expected):
    with path.open('rb') as stream:
        raw = stream.read(128 * 1024 + 1)
    if len(raw) > 128 * 1024 or hashlib.sha256(raw).hexdigest() != expected:
        raise ValueError(f'Candidate artifact identity differs: {path.name}')
    return json.loads(raw)


def _require_candidate(pins, command, relay_argv, *, successor=False):
    custody_path = str(WORKTREE / 'experiments/al02_one_pair_custody.py')
    version = 3 if successor else (2 if pins.get(custody_path) == V2_CUSTODY else 1)
    target = SUCCESSOR_ATTEMPT if successor else ATTEMPT
    worker_pin = V3_WORKER if successor else CANDIDATE_WORKER
    if version == 3:
        root, binding_pin, package_pin, authority_pin = (
            V3_DRAFT, V3_BINDING, V3_PACKAGE, V3_AUTHORIZATION_SHA256)
    elif version == 2:
        root, binding_pin, package_pin, authority_pin = (
            V2_DRAFT, V2_BINDING, V2_PACKAGE, V2_AUTHORIZATION_SHA256)
    else:
        root, binding_pin, package_pin, authority_pin = (
            RELEASE_DRAFT, CANDIDATE_BINDING, CANDIDATE_PACKAGE, CANDIDATE_AUTHORIZATION_SHA256)
    binding_name = f'installed-binding-v{version}.json'
    binding = _read_pinned_record(root / binding_name, binding_pin)
    package = _read_pinned_record(root / f'human-release-package-v{version}.json', package_pin)
    if (binding['schema'] != f'ora.al02.installed-binding.v{version}'
            or package['schema'] != f'AL02-INACTIVE-HUMAN-RELEASE-PACKAGE-v{version}'
            or package['artifact_sha256'][binding_name] != binding_pin
            or package['candidate'] != binding['candidate_commit']
            or package['production_head'] != binding['production_git_head']
            or package['scientific_authorization'] is not False
            or binding['scientific_authorization'] is not False
            or binding['consent_active_for_candidate'] is not False):
        raise ValueError('Candidate package and binding differ')
    check_scope(target, WORKTREE, command, OWNER, CONTEXT, LIMITS)
    if (binding['proposed_command'] != list(command)
            or binding['proposed_relay_argv'] != relay_argv
            or binding['context_sha256'] != CONTEXT
            or type(binding['seed']) is not int or binding['seed'] != SEED
            or package['seed'] != str(SEED)
            or binding['limits'] != LIMITS
            or binding['candidate_worker_sha256'] != worker_pin
            or pins.get(str(WORKER)) != worker_pin
            or binding['attempt'] != str(target)
            or package['attempt'] != str(target)
            or not binding['installed_file_pins'].items() <= pins.items()):
        raise ValueError('Candidate command, context, resource limits or required closure differs')
    # Identity records are inactive. No caller can supply the authorization pin.
    if version in (2, 3):
        inventory_name = f'source-pins-v{version}.json'
        custody_pin = V3_CUSTODY if successor else V2_CUSTODY
        inventory = _read_pinned_record(root / inventory_name,
                                        package['artifact_sha256'][inventory_name])
        if (inventory != binding['installed_file_pins']
                or binding['source_inventory_sha256'] != package['artifact_sha256'][inventory_name]
                or inventory.get(custody_path) != custody_pin):
            raise ValueError('V2 inventory differs')
    if authority_pin is None:
        raise ValueError('Candidate scientific authorization absent')
    authority_name = ('candidate-scientific-authorization.json' if version == 1
                      else f'candidate-scientific-authorization-v{version}.json')
    record = _read_pinned_record(target.parent / authority_name if successor else
                                 BINDING.parent / authority_name, authority_pin)
    expected = dict(schema=f'AL02-CANDIDATE-ONE-ATTEMPT-v{version}', worker_sha256=worker_pin,
                    binding_sha256=binding_pin, package_sha256=package_pin,
                    seed=str(SEED), attempt=str(target), owner=OWNER)
    if record != expected:
        raise ValueError('Candidate scientific authorization scope differs')

    # Custody checks actual bytes and atomically claims ATTEMPT after this check.
    # It repeats admission after that claim, so existence alone cannot fail here.
    import subprocess
    head = subprocess.check_output(['git', '-C', str(WORKTREE), 'rev-parse', 'HEAD'],
                                   text=True, timeout=2).strip()
    if head != binding['production_git_head']:
        raise ValueError('Candidate production HEAD differs')
    return dict(authorization_sha256=authority_pin,
                binding_sha256=binding_pin, package_sha256=package_pin)
