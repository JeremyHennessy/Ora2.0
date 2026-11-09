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
                referee, admission_check):
    """Persist one attempt at a fixed directory; admission_check must fail closed."""
    directory = Path(directory)
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
    if any(path not in pins for path in required):
        raise ValueError('Required source or interpreter pin missing')

    def preflight():
        if account() != expected_account or shutil.disk_usage(parent).free < FREE_MIN:
            raise ValueError('Account or free-space admission failed')
        for path, expected in pins.items():
            if digest(path) != expected:
                raise ValueError(f'Identity mismatch: {path}')

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

    preflight()
    directory.mkdir()
    released = False
    pending = record('00-pending.json', dict(
        context=context, command=command, cwd=str(cwd), pins=pins, python_version=sys.version,
        owner=expected_account, owner_pid=os.getpid(), limits=vars(transport.LIMITS),
        archive_max=ARCHIVE_MAX, free_min=FREE_MIN, stdout_max=transport.OUTPUT_LIMIT,
        process_births_expected=2, environment_sha256=hashlib.sha256(json.dumps(
            environment, sort_keys=True).encode()).hexdigest()))
    try:
        with (directory / 'raw.bin').open('xb', buffering=0) as raw:
            def before_go(executable, script, process, usage):
                nonlocal released
                preflight()
                if (executable != python or str(script) != bootstrap or process.poll() is not None
                        or usage['flags'] != transport.FLAGS or usage['started_processes'] != 1
                        or usage['active_before_close'] != 1
                        or usage['configured_memory_bytes'] != transport.LIMITS.memory_bytes
                        or usage['configured_processes'] != transport.LIMITS.processes
                        or usage['configured_cpu_ticks'] != 50_000_000):
                    raise ValueError('Pre-go executable or Job readback differs')
                if admission_check() is not True:
                    raise ValueError('Admission did not affirm release')
                preflight()
                if sum(p.stat().st_size for p in directory.iterdir()) + transport.OUTPUT_LIMIT + 65536 > ARCHIVE_MAX:
                    raise ValueError('Insufficient bounded archive headroom')
                verified = record('01-verified.json', dict(
                    pending_sha256=pending, bootstrap_pid=process.pid, usage=usage))
                record('02-release-intent.json', dict(verified_sha256=verified))
                released = True

            def capture(chunk):
                if raw.write(chunk) != len(chunk):
                    raise OSError('Short raw evidence write')

            _, receipt = transport.run(command, cwd, before_go=before_go,
                                       capture=capture, environment=environment)
            os.fsync(raw.fileno())
        raw_path = directory / 'raw.bin'
        raw_sha = digest(raw_path)
        record('03-transport.json', dict(raw_sha256=raw_sha, receipt=receipt))
        if not released or not receipt['accepted']:
            raise ValueError('Transport rejected')
        with pinned_path(raw_path).open('rb') as stream:
            data = stream.read(transport.OUTPUT_LIMIT + 1)
        if len(data) != receipt['retained_bytes'] or hashlib.sha256(data).hexdigest() != raw_sha:
            raise ValueError('Preserved raw evidence mismatch')
        result = referee(data)
        record('04-terminal.json', dict(raw_sha256=raw_sha, result=result))
        return result
    except BaseException as exc:
        raw_path = directory / 'raw.bin'
        record('99-failed.json', dict(release_intent=released, error_type=type(exc).__name__,
                                      error=str(exc)[:2048],
                                      raw_sha256=digest(raw_path) if raw_path.exists() else None))
        raise
