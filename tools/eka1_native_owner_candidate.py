"""Partially integrated owner/physical-ledger candidate. Native execution HELD.

No launcher, World imports, admission flag, callback or arbitrary command API.
Checks below enforce the preparation path only. They are not a security boundary
against hostile Python, another process, cached code or a substituted OS owner.
"""
import ctypes
from ctypes import wintypes
import hashlib
import json
import os
from pathlib import Path
import stat
import threading
import time

ROOT = Path(__file__).resolve().parents[1]
LEDGER_SHA256 = '735c7fbd9564e04e715e8125df315eba47e36a8dc66c3d1a24dc23ef7c33b73d'
ROLES = ('owner', 'original_producer', 'selection_replay', 'true',
         'identity_sham', 'xor1', 'independent_verifier')
_active = None
_consumed = set()
_lifetime_used = False
_mutex = threading.RLock()


class NativeQualificationRequired(RuntimeError):
    pass


def current_birth():
    """Read only the current Windows process birth; start no process."""
    if os.name != 'nt':
        raise OSError('Windows owner birth required; no portable fallback')
    kernel = ctypes.WinDLL('kernel32', use_last_error=True)
    kernel.GetCurrentProcess.argtypes = []
    kernel.GetCurrentProcess.restype = wintypes.HANDLE
    kernel.GetProcessTimes.argtypes = [wintypes.HANDLE] + [ctypes.POINTER(wintypes.FILETIME)]*4
    kernel.GetProcessTimes.restype = wintypes.BOOL
    fields = [wintypes.FILETIME() for unused in range(4)]
    if not kernel.GetProcessTimes(kernel.GetCurrentProcess(), *[ctypes.byref(v) for v in fields]):
        raise ctypes.WinError(ctypes.get_last_error())
    return (os.getpid(), (fields[0].dwHighDateTime << 32) | fields[0].dwLowDateTime)


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'),
                      ensure_ascii=True, allow_nan=False).encode('ascii')


def ledger_class():
    path = ROOT/'tools/eka1_cumulative_reservations.py'
    if path.is_symlink() or hashlib.sha256(path.read_bytes()).hexdigest() != LEDGER_SHA256:
        raise ValueError('Reviewed ledger source differs')
    from tools import eka1_cumulative_reservations as source
    if Path(source.__file__).resolve() != path.resolve():
        raise ValueError('Ledger module origin differs')
    return source.Reservations


class NativeOwnerCandidate:
    """Own one fresh ledger and immutable prospective assignment/request set.

    The owner label and request hashes are consistency bindings, not grants.
    Original registry, physical custody and native guardian are still absent.
    Every execution entry consumes its reservation then terminally refuses.
    """
    def __init__(self, ledger_path, *, owner_birth, assignment_id, request_hashes):
        global _active, _lifetime_used
        self._started = time.monotonic()
        self._deadline = self._started + 2940
        self._closed = False
        self._failed = None
        self._cleanup_errors = []
        self._fd = None
        self._ledger = None
        self._role = None
        if (type(owner_birth) is not tuple or len(owner_birth) != 2 or
                any(type(v) is not int or v <= 0 for v in owner_birth) or
                owner_birth != current_birth()):
            raise ValueError('Exact current owner process birth required')
        if type(assignment_id) is not str or not 0 < len(assignment_id) <= 128:
            raise ValueError('Prospective assignment label required')
        keys = {(d, r) for d in (1, 8) for r in ROLES}
        if (type(request_hashes) is not dict or
                any(type(k) is not tuple or len(k) != 2 or type(k[0]) is not int or
                    k[0] not in (1, 8) or type(k[1]) is not str or k[1] not in ROLES
                    for k in request_hashes) or set(request_hashes) != keys or
                any(type(v) is not str or len(v) != 64 or
                    any(c not in '0123456789abcdef' for c in v) for v in request_hashes.values())):
            raise ValueError('Exact fourteen prospectively fixed request hashes')
        self._birth = owner_birth
        self._assignment = assignment_id
        self._requests = tuple(sorted(request_hashes.items()))
        self._path = Path(ledger_path).absolute()
        for path in (self._path, *self._path.parents):
            if path.exists() and (path.is_symlink() or getattr(path.lstat(), 'st_file_attributes', 0) & 0x400):
                raise ValueError('Ledger ancestry reparse/link refused')
        with _mutex:
            if _lifetime_used or _active is not None or assignment_id in _consumed:
                raise ValueError('One process-local owner/lifetime; no replacement')
            _lifetime_used = True
            _consumed.add(assignment_id)  # A failed open never refunds identity.
            try:
                self._fd = os.open(self._path, os.O_CREAT | os.O_EXCL | os.O_RDWR | os.O_BINARY, 0o600)
                info = os.fstat(self._fd)
                self._physical = (info.st_dev, info.st_ino)
                self._ledger = ledger_class()(self._fd)
                _active = self
                self._check()
            except BaseException as exc:
                self._fail(exc)
                raise

    def _fail(self, exc):
        # Later refusal/cleanup must not replace the originating failure.
        if self._failed is None:
            self._failed = type(exc).__name__ + ': ' + str(exc)
        try:
            self.close()
        except BaseException as cleanup:
            # close() retains each cleanup cause itself. This fallback covers
            # a failure before that retention; there is never a cleanup retry.
            if not self._cleanup_errors:
                self._cleanup_errors.append(type(cleanup).__name__ + ': ' + str(cleanup))

    def _check(self):
        if self._closed or self._failed is not None or _active is not self:
            raise RuntimeError('Owner closed/incomplete; no retry')
        if current_birth() != self._birth:
            raise RuntimeError('Owner process birth differs')
        now = time.monotonic()
        if now >= self._deadline or (self._role is not None and now >= self._role_deadline):
            raise TimeoutError('Original enclosing/role deadline reached')
        for path in (self._path, *self._path.parents):
            info = path.lstat()
            if path.is_symlink() or getattr(info, 'st_file_attributes', 0) & 0x400:
                raise OSError('Ledger ancestry reparse/link refused')
        fd = os.fstat(self._fd); named = self._path.lstat()
        if (not stat.S_ISREG(fd.st_mode) or not stat.S_ISREG(named.st_mode) or
                getattr(named, 'st_file_attributes', 0) & 0x400 or named.st_nlink != 1 or
                fd.st_nlink != 1 or (fd.st_dev, fd.st_ino) != self._physical or
                (named.st_dev, named.st_ino) != self._physical or
                fd.st_size != self._ledger._bytes or named.st_size != fd.st_size or
                os.lseek(self._fd, 0, os.SEEK_CUR) != self._ledger._bytes):
            raise OSError('Canonical physical ledger identity/extent/offset differs')

    @property
    def ledger(self):
        with _mutex:
            try:
                self._check()
                return self._ledger
            except BaseException as exc:
                self._fail(exc)
                raise

    def _enter(self, dose, role, request):
        entered = time.monotonic()
        self._check()
        if (type(dose) is not int or dose not in (1, 8) or
                type(role) is not str or role not in ROLES or self._role is not None):
            raise ValueError('One fixed role at a time; no retry')
        if hashlib.sha256(canonical(request)).hexdigest() != dict(self._requests)[dose, role]:
            raise ValueError('Prospectively fixed request differs')
        self._role = (dose, role)
        self._role_deadline = min(self._deadline - 30, entered + 180)
        self._ledger.role(dose, ROLES.index(role))
        self._check()

    def _held(self):
        raise NativeQualificationRequired('NOT_READY: original registry/grant, physical/native guardian custody and resource/archive fit absent')

    def launch_role(self, *, assignment_id, dose, role, request):
        """Burn an attempted launch reservation; no native launcher exists."""
        with _mutex:
            try:
                if assignment_id != self._assignment:
                    raise ValueError('Assignment differs')
                self._enter(dose, role, request)
                self._ledger.process_birth(dose, ROLES.index(role))
                self._check()
                self._held()
            except BaseException as exc:
                self._fail(exc)
                raise

    def replay(self, ledger, *, assignment_id, dose, role, request, genesis_index):
        """Mandatory canonical-ledger precharge, then held BEFORE World import."""
        with _mutex:
            try:
                if ledger is not self._ledger or assignment_id != self._assignment:
                    raise ValueError('Alternate ledger/assignment refused')
                if role not in ('selection_replay', 'true', 'identity_sham', 'xor1'):
                    raise ValueError('Not a fixed World-producing role')
                if request['configuration']['dose'] != dose:
                    raise ValueError('Request dose differs')
                if role == 'selection_replay':
                    bound_assignment = request['assignment_id']
                    stop_tick = request['assigned_stop_tick']
                    if type(stop_tick) is not int or stop_tick != 4096:
                        raise ValueError('Full selection horizon required')
                else:
                    bound_assignment = request['binding']['original_world_id']
                    stop_tick = request['stop_tick']
                    if request['arm'] != role:
                        raise ValueError('Request arm differs')
                if bound_assignment != self._assignment:
                    raise ValueError('Request assignment differs')
                self._enter(dose, role, request)
                self._ledger.genesis(dose, genesis_index)
                self._ledger.dispatches(dose, genesis_index, stop_tick)
                self._check()
                self._held()
            except BaseException as exc:
                self._fail(exc)
                raise

    def close(self):
        global _active
        with _mutex:
            if not self._closed:
                self._closed = True
                first_cleanup = None
                try:
                    if self._ledger is not None:
                        self._ledger.close()
                except BaseException as exc:
                    first_cleanup = exc
                    self._cleanup_errors.append(type(exc).__name__ + ': ' + str(exc))
                try:
                    if self._fd is not None:
                        os.close(self._fd)
                        self._fd = None
                except BaseException as exc:
                    if first_cleanup is None:
                        first_cleanup = exc
                    self._cleanup_errors.append(type(exc).__name__ + ': ' + str(exc))
                    # Keep the failed descriptor number for custody. Logical
                    # closed means no further work; physical closure UNKNOWN.
                finally:
                    if _active is self:
                        _active = None
                if first_cleanup is not None:
                    raise first_cleanup
