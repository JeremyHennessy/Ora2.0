"""One-use AL02 evidence custody. A hash journal is not an owner signature."""
import ctypes
import hashlib
import json
import os
from pathlib import Path
import shutil
import stat
import sys

from experiments import al02_one_pair_job as transport
from experiments.al02_one_pair import verify as candidate_referee

ARCHIVE_MAX = 8 * 1024 * 1024
FREE_MIN = 32 * 1024 * 1024


def pinned_path(path):
    path = Path(path)
    if not path.is_absolute():
        raise ValueError('Pin paths must be absolute')
    for part in (path, *path.parents):
        if part.lstat().st_file_attributes & stat.FILE_ATTRIBUTE_REPARSE_POINT:
            raise ValueError(f'Reparse point: {part}')
    return path


def digest(path):
    with pinned_path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def account():
    name = ctypes.create_unicode_buffer(1024)
    size = ctypes.c_ulong(len(name))
    if not ctypes.windll.secur32.GetUserNameExW(2, name, ctypes.byref(size)):
        raise OSError('Cannot resolve effective Windows account')
    return name.value.casefold()


def transaction(directory, *, command, cwd, pins, expected_account, context,
                referee, admission_check=None, consent=None):
    """Persist one attempt at a fixed directory; admission_check must fail closed."""
    from experiments import al02_one_pair_consent as limited

    directory = Path(directory)
    if consent is None:
        if not callable(admission_check):
            raise ValueError('Strict admission check required')
    elif consent not in (limited.CONSENT, limited.SUCCESSOR) or admission_check is not None:
        raise ValueError('Unrecognized or mixed admission authority')
    else:
        limited.check_scope(directory, cwd, command, expected_account, context,
                            vars(transport.LIMITS))
    cwd = pinned_path(cwd)
    parent = pinned_path(directory.parent)
    command = tuple(command)
    pins = dict(pins)
    environment = dict(os.environ)
    if len(command) < 5:
        raise ValueError('Explicit worker script required')
    python = str(pinned_path(getattr(sys, '_base_executable', sys.executable)))
    bootstrap = str(pinned_path(Path(transport.__file__).with_name('process_limits.py')))
    worker = str(pinned_path(command[4]))
    if command[:5] != (python, '-I', '-S', '-B', worker):
        raise ValueError('Unexpected worker interpreter or startup arguments')
    required = (python, bootstrap, worker, str(Path(__file__).resolve()),
                str(Path(transport.__file__).resolve()))
    if consent is not None:
        required += (str(Path(limited.__file__).resolve()),)
    if any(path not in pins for path in required):
        raise ValueError('Required source or interpreter pin missing')

    def preflight():
        identities = None
        if consent is not None:
            if consent != limited.SUCCESSOR:
                pinned_path(limited.BINDING)
            identities = limited.require_bound_worker(
                pins, command, transport.relay_argv(python, command))
            if identities is not None:
                source = str(Path(__file__).with_name('al02_one_pair.py').resolve())
                if (referee is not candidate_referee
                        or candidate_referee.__code__.co_filename != source
                        or source not in pins):
                    raise ValueError('Candidate referee identity differs')
                identities = dict(identities, referee_entry='experiments.al02_one_pair.verify',
                                  referee_sha256=pins[source])
        if account() != expected_account or shutil.disk_usage(parent).free < FREE_MIN:
            raise ValueError('Account or free-space admission failed')
        for path, expected in pins.items():
            if digest(path) != expected:
                raise ValueError(f'Identity mismatch: {path}')
        return identities

    def record(name, value):
        raw = json.dumps(value, sort_keys=True, separators=(',', ':'),
                         allow_nan=False).encode('utf-8')
        used = sum(p.stat().st_size for p in directory.iterdir())
        if used + len(raw) > ARCHIVE_MAX:
            raise ValueError('Archive ceiling exceeded')
        with (directory / name).open('xb') as stream:
            stream.write(raw)
            stream.flush()
            os.fsync(stream.fileno())
        return hashlib.sha256(raw).hexdigest()

    def partial_receipt():
        path = directory / 'partial.jsonl'
        try:
            size = pinned_path(path).stat().st_size
            if size > transport.OUTPUT_LIMIT:
                return dict(bytes=size, error='Invalid partial-history extent')
            return dict(bytes=size, sha256=digest(path))
        except FileNotFoundError:
            return None
        except (OSError, ValueError) as exc:
            return dict(error=str(exc)[:512])

    identities = preflight()
    chain = {'release_identities': identities} if identities is not None else {}
    receipts = {}

    def verify_receipts():
        for name, expected in receipts.items():
            if digest(directory / name) != expected:
                raise ValueError(f'Candidate receipt identity differs: {name}')

    def recheck():
        if preflight() != identities:
            raise ValueError('Candidate release identities changed')
        verify_receipts()

    directory.mkdir()
    released = False
    try:
        pending = record('00-pending.json', dict(
            context=context, consent=consent, evidence_tier=limited.TIER if consent else None,
            command=command, cwd=str(cwd), pins=pins, python_version=sys.version,
            relay_argv=transport.relay_argv(python, command) if consent else None,
            owner=expected_account, owner_pid=os.getpid(), limits=vars(transport.LIMITS),
            archive_max=ARCHIVE_MAX, free_min=FREE_MIN, stdout_max=transport.OUTPUT_LIMIT,
            process_births_expected=2, environment_sha256=hashlib.sha256(json.dumps(
                environment, sort_keys=True).encode()).hexdigest(), **chain))
        if chain:
            receipts['00-pending.json'] = pending
        with (directory / 'raw.bin').open('xb', buffering=0) as raw:
            def before_go(executable, script, process, usage):
                nonlocal released
                recheck()
                expected_script = tuple(transport.relay_argv(python, command)) if consent else bootstrap
                actual_script = script if consent else str(script)
                if (executable != python or actual_script != expected_script or process.poll() is not None
                        or usage['flags'] != transport.FLAGS or usage['started_processes'] != 1
                        or usage['active_before_close'] != 1
                        or usage['configured_memory_bytes'] != transport.LIMITS.memory_bytes
                        or usage['configured_processes'] != transport.LIMITS.processes
                        or usage['configured_cpu_ticks'] != 50_000_000):
                    raise ValueError('Pre-go executable or Job readback differs')
                if consent is None:
                    if admission_check() is not True:
                        raise ValueError('Admission did not affirm release')
                else:
                    limited.check_scope(directory, cwd, command, expected_account,
                                        context, vars(transport.LIMITS))
                    with pinned_path(directory / '00-pending.json').open('rb') as manifest:
                        limited.check_manifest(manifest.read(ARCHIVE_MAX + 1), pending,
                                               command=command, owner=expected_account,
                                               context=context, limits=vars(transport.LIMITS))
                recheck()
                if sum(p.stat().st_size for p in directory.iterdir()) + transport.OUTPUT_LIMIT * (2 if consent else 1) + 65536 > ARCHIVE_MAX:
                    raise ValueError('Insufficient bounded archive headroom')
                verified = record('01-verified.json', dict(
                    pending_sha256=pending, bootstrap_pid=process.pid, usage=usage, **chain))
                intent = record('02-release-intent.json', dict(verified_sha256=verified, **chain))
                if chain:
                    receipts.update({'01-verified.json': verified, '02-release-intent.json': intent})
                    recheck()
                if consent is not None:
                    limited.check_scope(directory, cwd, command, expected_account,
                                        context, vars(transport.LIMITS))
                released = True
                return intent

            def capture(chunk):
                if raw.write(chunk) != len(chunk):
                    raise OSError('Short raw evidence write')

            _, receipt = transport.run(command, cwd, before_go=before_go,
                                       capture=capture, environment=environment,
                                       relay=consent is not None)
            os.fsync(raw.fileno())
        raw_path = directory / 'raw.bin'
        raw_sha = digest(raw_path)
        partial = partial_receipt()
        transport_sha = record('03-transport.json', dict(
            raw_sha256=raw_sha, receipt=receipt, partial=partial, **chain))
        if chain:
            receipts['03-transport.json'] = transport_sha
        if consent and (not partial or not partial.get('bytes') or partial.get('error')):
            raise ValueError('Missing or invalid partial-history journal')
        if not released or not receipt['accepted']:
            raise ValueError('Transport rejected')
        with pinned_path(raw_path).open('rb') as stream:
            data = stream.read(transport.OUTPUT_LIMIT + 1)
        if len(data) != receipt['retained_bytes'] or hashlib.sha256(data).hexdigest() != raw_sha:
            raise ValueError('Preserved raw evidence mismatch')
        if consent:
            payload = json.loads(data)
            prefix = json.loads(payload['checkpoint'])['state']['events']
            expected = [dict(phase='prefix', event=event) for event in prefix]
            for role in ('accessible', 'sequestered'):
                expected.extend(dict(phase=role, event=event)
                                for event in payload['branches'][role]['events'])
            with pinned_path(directory / 'partial.jsonl').open('rb') as stream:
                journal = stream.read(transport.OUTPUT_LIMIT + 1)
            expected_bytes = b''.join(json.dumps(row, sort_keys=True, separators=(',', ':'),
                                                ensure_ascii=True, allow_nan=False).encode('ascii') + b'\n'
                                      for row in expected)
            if (len(journal) != partial['bytes'] or hashlib.sha256(journal).hexdigest() != partial['sha256']
                    or journal != expected_bytes):
                raise ValueError('Partial-history journal does not match raw result')
        if chain:
            recheck()
        result = referee(data)
        if chain:
            verify_receipts()
        record('04-terminal.json', dict(raw_sha256=raw_sha, result=result, **chain,
                                        **({'receipt_sha256': receipts} if chain else {})))
        return result
    except BaseException as exc:
        raw_path = directory / 'raw.bin'
        raw_error = None
        try:
            raw_sha = digest(raw_path) if raw_path.exists() else None
        except (OSError, ValueError) as raw_exc:
            raw_sha = None
            raw_error = str(raw_exc)[:512]
        try:
            record('99-failed.json', dict(release_intent=released, error_type=type(exc).__name__,
                                          error=str(exc)[:2048], partial=partial_receipt(),
                                          raw_sha256=raw_sha, raw_error=raw_error, **chain,
                                          **({'receipt_sha256': receipts} if chain else {})))
        except Exception as receipt_error:
            exc.add_note(f'Attempt remains claimed; failure receipt unavailable: {receipt_error}')
        raise
