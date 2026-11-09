"""Consent boundary for the single AL02 lower-assurance attempt."""

import hashlib
import json
from pathlib import Path

TIER = 'LOW_ASSURANCE_EXPLORATORY'
CONSENT = 'JeremyHennessy/Ora2.0#328:6740691539'
CONTEXT = '71bb1e2c35ff536900807c5c0ee86d30c13722b85291a8e8f086c0c62dc934b8'
SEED = 8195177122164069225
OWNER = 'hennessydesktop\\hennessy'
LIMITS = dict(memory_bytes=134217728, cpu_seconds=5, processes=3, wall_seconds=10)
ROOT = Path('D:/OraLab')
WORKTREE = ROOT / 'src/Ora2.0-al02-first-depletion-20261109'
ATTEMPT = ROOT / 'reports/al02-first-depletion-exploratory-20261109/attempt-6740691539'
WORKER = WORKTREE / 'experiments/al02_one_pair_worker.py'
STOP = ROOT / 'automation/ora-codex/STOP'
APPROVED_WORKER_SHA256 = '7ba6d4ee9a5b4072ad7f7cb09afdcc610689b55aa6829e1d45bd90f1d779a824'
BINDING = ATTEMPT.parent / 'one-pair-production-binding.json'
BINDING_SHA256 = '18c144b6f89a62c39cf97630d9577604074b48ad54519bdd2813589cdba3f0ef'


def check_scope(directory, cwd, command, owner, context, limits):
    """The consent can bind only one worker shape, context and evidence destination."""
    if (Path(directory) != ATTEMPT or Path(cwd) != WORKTREE or owner != OWNER
            or context != CONTEXT or limits != LIMITS or len(command) != 7
            or tuple(command[1:]) != ('-I', '-S', '-B', str(WORKER),
                                      str(ATTEMPT / '00-pending.json'), CONSENT)):
        raise ValueError('Outside explicit AL02 lower-assurance consent scope')
    if STOP.exists():
        raise ValueError('STOP present')


def check_manifest(raw, digest, *, command, owner, context, limits):
    if hashlib.sha256(raw).hexdigest() != digest:
        raise ValueError('Pending manifest digest mismatch')
    data = json.loads(raw)
    expected = dict(command=list(command), owner=owner, context=context, limits=limits,
                    consent=CONSENT, evidence_tier=TIER)
    if any(data.get(key) != value for key, value in expected.items()):
        raise ValueError('Pending manifest does not bind the approved scope')


def require_bound_worker(pins, command, relay_argv):
    # A caller-provided hash is not approval of a newly supplied worker.
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
V2_BINDING = '913ed1226fed8a0ac67085ce876e9e7f717a2b1edd1d32f32f6e0775bf72d3f9'
V2_PACKAGE = '9f86091f636aeace97dac957b36d5284e3845e026531f5f5388854105483fa6a'
V2_AUTHORIZATION_SHA256 = None


def _read_pinned_record(path, expected):
    with path.open('rb') as stream:
        raw = stream.read(128 * 1024 + 1)
    if len(raw) > 128 * 1024 or hashlib.sha256(raw).hexdigest() != expected:
        raise ValueError(f'Candidate artifact identity differs: {path.name}')
    return json.loads(raw)


def _require_candidate(pins, command, relay_argv):
    custody_path = str(WORKTREE / 'experiments/al02_one_pair_custody.py')
    version = 2 if pins.get(custody_path) == V2_CUSTODY else 1
    if version == 2:
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
    check_scope(ATTEMPT, WORKTREE, command, OWNER, CONTEXT, LIMITS)
    if (binding['proposed_command'] != list(command)
            or binding['proposed_relay_argv'] != relay_argv
            or binding['context_sha256'] != CONTEXT
            or type(binding['seed']) is not int or binding['seed'] != SEED
            or package['seed'] != str(SEED)
            or binding['limits'] != LIMITS
            or binding['candidate_worker_sha256'] != CANDIDATE_WORKER
            or binding['attempt'] != str(ATTEMPT)
            or package['attempt'] != str(ATTEMPT)
            or not binding['installed_file_pins'].items() <= pins.items()):
        raise ValueError('Candidate command, context, resource limits or required closure differs')
    # Identity records are inactive. No caller can supply the authorization pin.
    if version == 2:
        inventory_name = 'source-pins-v2.json'
        inventory = _read_pinned_record(root / inventory_name,
                                        package['artifact_sha256'][inventory_name])
        if (inventory != binding['installed_file_pins']
                or binding['source_inventory_sha256'] != package['artifact_sha256'][inventory_name]
                or inventory.get(custody_path) != V2_CUSTODY):
            raise ValueError('V2 inventory differs')
    if authority_pin is None:
        raise ValueError('Candidate scientific authorization absent')
    authority_name = ('candidate-scientific-authorization.json' if version == 1
                      else 'candidate-scientific-authorization-v2.json')
    record = _read_pinned_record(BINDING.parent / authority_name, authority_pin)
    expected = dict(schema=f'AL02-CANDIDATE-ONE-ATTEMPT-v{version}', worker_sha256=CANDIDATE_WORKER,
                    binding_sha256=binding_pin, package_sha256=package_pin,
                    seed=str(SEED), attempt=str(ATTEMPT), owner=OWNER)
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

