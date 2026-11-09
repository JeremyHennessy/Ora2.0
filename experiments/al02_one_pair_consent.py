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


def _read_pinned_record(path, expected):
    with path.open('rb') as stream:
        raw = stream.read(128 * 1024 + 1)
    if len(raw) > 128 * 1024 or hashlib.sha256(raw).hexdigest() != expected:
        raise ValueError(f'Candidate artifact identity differs: {path.name}')
    return json.loads(raw)


def _require_candidate(pins, command, relay_argv):
    binding = _read_pinned_record(RELEASE_DRAFT / 'installed-binding-v1.json',
                                  CANDIDATE_BINDING)
    package = _read_pinned_record(RELEASE_DRAFT / 'human-release-package-v1.json',
                                  CANDIDATE_PACKAGE)
    if (binding['schema'] != 'ora.al02.installed-binding.v1'
            or package['schema'] != 'AL02-INACTIVE-HUMAN-RELEASE-PACKAGE-v1'
            or package['artifact_sha256']['installed-binding-v1.json'] != CANDIDATE_BINDING
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
    if CANDIDATE_AUTHORIZATION_SHA256 is None:
        raise ValueError('Candidate scientific authorization absent')
    record = _read_pinned_record(BINDING.parent / 'candidate-scientific-authorization.json',
                                 CANDIDATE_AUTHORIZATION_SHA256)
    expected = dict(schema='AL02-CANDIDATE-ONE-ATTEMPT-v1', worker_sha256=CANDIDATE_WORKER,
                    binding_sha256=CANDIDATE_BINDING, package_sha256=CANDIDATE_PACKAGE,
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


