"""Source-only reservation ledger; no launcher, World, grant or resume authority.

The future sole native owner must reserve BEFORE each effect and authenticate
actual births/steps separately. This ledger alone cannot enforce external calls.
Each attempted reservation consumes its allowance even if the later effect fails.
Interrupted writes poison this instance; retained bytes must never be overwritten.
"""
import hashlib
import json
import os
import threading


def _integer(value, lo, hi):
    if type(value) is not int or not lo <= value <= hi:
        raise ValueError('Exact bounded integer required')
    return value


class Reservations:
    """One fresh file, one owning instance, no recovery/refund/retry API.

    The enclosing owner supplies a new exclusive plain-file descriptor and owns
    physical ancestry/custody and total file/output reservations. No file path,
    serialized ledger or caller-supplied count can restore this object.
    """

    def __init__(self, fd):
        # Duplicate ownership: caller may close its original descriptor.
        self._fd = os.dup(fd)
        try:
            import stat
            info = os.fstat(self._fd)
            if not stat.S_ISREG(info.st_mode) or info.st_size or info.st_nlink != 1:
                raise ValueError('Fresh unlinked-from-other-names empty plain file required')
            if os.lseek(self._fd, 0, os.SEEK_CUR) != 0:
                raise ValueError('Fresh file offset required')
        except BaseException:
            os.close(self._fd)
            raise
        self._mutex = threading.Lock()
        self._poison = None
        self._closed = False
        self._sequence = 0
        self._previous = '0' * 64
        self._roles = set()
        self._births = 0
        self._genesis = {1: {}, 8: {}}
        self._bytes = 0
        self._identity = (info.st_dev, info.st_ino)

    def _append(self, event):
        if self._closed or self._poison is not None:
            raise RuntimeError('Closed or incomplete ledger; no retry')
        row = dict(sequence=self._sequence, previous_sha256=self._previous,
                   reservation=event, execution_authenticated=False)
        raw = (json.dumps(row, sort_keys=True, separators=(',', ':')) + '\n').encode('ascii')
        # <=14 roles +56 births +64 genesis +262144 dispatches; 256 bytes/row
        # and an independent 80MiB ledger ceiling fit neither an output grant
        # nor union automatically. The future manifest must explicitly charge it.
        if len(raw) > 256 or self._bytes + len(raw) > 80 * 1024**2:
            self._poison = 'ledger output ceiling'
            raise RuntimeError(self._poison)
        try:
            info = os.fstat(self._fd)
            if ((info.st_dev, info.st_ino) != self._identity or
                    info.st_size != self._bytes or info.st_nlink != 1 or
                    os.lseek(self._fd, 0, os.SEEK_CUR) != self._bytes):
                raise OSError('Ledger identity/extent/offset changed')
            # Short write is a terminal custody failure, never a retry loop.
            if os.write(self._fd, raw) != len(raw):
                raise OSError('Short ledger write; retained partial is INCOMPLETE')
            os.fsync(self._fd)
        except BaseException as exc:
            self._poison = type(exc).__name__ + ': ' + str(exc)
            raise
        self._previous = hashlib.sha256(raw).hexdigest()
        self._sequence += 1
        self._bytes += len(raw)

    def role(self, dose, role_index):
        with self._mutex:
            _integer(dose, 1, 8)
            if dose not in self._genesis:
                raise ValueError('Both fixed dose slots only')
            _integer(role_index, 0, 6)
            key = (dose, role_index)
            if key in self._roles:
                raise ValueError('Role already consumed; no replacement')
            self._append(dict(kind='role', dose=dose, index=role_index))
            self._roles.add(key)

    def process_birth(self, dose, role_index):
        with self._mutex:
            _integer(dose, 1, 8)
            _integer(role_index, 0, 6)
            if (dose, role_index) not in self._roles or self._births >= 56:
                raise ValueError('Unreserved role or cumulative process ceiling')
            self._append(dict(kind='process_birth', dose=dose, role=role_index,
                              index=self._births))
            self._births += 1

    def genesis(self, dose, index):
        with self._mutex:
            _integer(dose, 1, 8)
            _integer(index, 0, 31)
            if dose not in self._genesis or not any(d == dose for d, _ in self._roles):
                raise ValueError('Unreserved dose role')
            if index in self._genesis[dose]:
                raise ValueError('Genesis already consumed')
            self._append(dict(kind='genesis', dose=dose, index=index))
            self._genesis[dose][index] = 0

    def dispatch(self, dose, index):
        self.dispatches(dose, index, 1)

    def dispatches(self, dose, index, count):
        """Reserve a bounded block before opaque restore; unused credit burns."""
        with self._mutex:
            _integer(dose, 1, 8)
            _integer(index, 0, 31)
            _integer(count, 1, 4096)
            if dose not in self._genesis or index not in self._genesis[dose]:
                raise ValueError('Unreserved genesis')
            used = self._genesis[dose][index]
            if used + count > 4096:
                raise ValueError('Per-genesis dispatch ceiling')
            self._append(dict(kind='dispatch', dose=dose, genesis=index,
                              index=used, count=count))
            self._genesis[dose][index] = used + count

    def close(self):
        """Close custody only; no execution, EOF or archive completeness claim."""
        with self._mutex:
            if not self._closed:
                self._closed = True
                os.close(self._fd)
