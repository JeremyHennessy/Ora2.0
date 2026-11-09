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
