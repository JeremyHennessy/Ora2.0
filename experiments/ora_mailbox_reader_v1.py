"""Arbitrate a bounded inbox read against the existing producer lock.

A busy reader is a skipped poll, not a task retry. Publishers remain nonblocking
and fail before building a publication intent when this reader owns the lock.
"""
from contextlib import contextmanager
import os
from pathlib import Path

@contextmanager
def open_reader(path):
    path=Path(path);lock=path.parent/'mailbox.lock'
    if lock.exists() and (lock.is_symlink() or lock.stat().st_nlink!=1):
        raise ValueError('Mailbox lock must be a plain local file')
    with lock.open('a+b') as owner:
        owner.seek(0)
        if os.name=='nt':
            import msvcrt
            try: msvcrt.locking(owner.fileno(),msvcrt.LK_NBLCK,1)
            except OSError:
                yield None
                return
        else:
            import fcntl
            try: fcntl.flock(owner,fcntl.LOCK_EX|fcntl.LOCK_NB)
            except BlockingIOError:
                yield None
                return
        with path.open('rb') as stream:
            yield stream
