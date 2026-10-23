"""Prospective external caller. No CLI, scheduler, registrar or launch on import.

The separately reviewed original owner supplies admission_check. This module
cannot authenticate reviewer origin or issue an expiring original-owner grant.
An incomplete started directory is terminal UNKNOWN, never a resumable attempt.
"""
import hashlib
import json
import os
import stat
import sys
from pathlib import Path

SLOT_BYTES = 1024 * 1024
SCHEMA = 'PILOT74-DURABLE-CALLER-v1'


def encode(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'),
                      ensure_ascii=True, allow_nan=False).encode('ascii')


def plain(path, directory=False):
    info = path.lstat()
    if stat.S_ISLNK(info.st_mode) or getattr(info, 'st_file_attributes', 0) & 0x400:
        raise ValueError('Reparse/symlink evidence path refused')
    if directory:
        if not stat.S_ISDIR(info.st_mode):
            raise ValueError('Plain directory required')
    elif not stat.S_ISREG(info.st_mode) or info.st_nlink != 1:
        raise ValueError('Single-link plain evidence file required')
    return info.st_dev, info.st_ino


def ancestors(path):
    return [(parent, plain(parent, True)) for parent in path.parents]


def recheck(rows):
    for path, identity in rows:
        if plain(path, True) != identity:
            raise ValueError('Evidence ancestor changed')


def safe_error(error):
    try:
        return repr(error)
    except BaseException:
        return '<exception formatting unavailable>'


def diagnostic(error):
    """Bounded stack/chain inventory; incompleteness is explicit, never a pass."""
    rows = []
    seen = set()
    current = error
    while current is not None and id(current) not in seen and len(rows) < 4:
        seen.add(id(current))
        frames = []
        tb = current.__traceback__
        while tb is not None and len(frames) < 32:
            frames.append(dict(file=tb.tb_frame.f_code.co_filename,
                               function=tb.tb_frame.f_code.co_name, line=tb.tb_lineno))
            tb = tb.tb_next
        notes = list(getattr(current, '__notes__', []))
        rows.append(dict(type=type(current).__module__ + '.' + type(current).__qualname__,
            representation=safe_error(current), frames=frames,
            frames_complete=tb is None, notes=notes[:16], notes_complete=len(notes) <= 16,
            suppress_context=bool(current.__suppress_context__)))
        current = current.__cause__ if current.__cause__ is not None else current.__context__
    return dict(exceptions=rows, chain_complete=current is None,
                complete=current is None and all(r['frames_complete'] and r['notes_complete'] for r in rows))


class Attempt:
    """Exclusive one-shot reservation in an externally selected evidence parent.

    No deletion, overwrite of previous attempts, retry or recovery is provided.
    File fsync/readback proves local file retention, not power-loss recovery.
    """
    def __init__(self, root, registration_sha256):
        if (type(registration_sha256) is not str or len(registration_sha256) != 64
                or any(c not in '0123456789abcdef' for c in registration_sha256)):
            raise ValueError('Exact registration SHA256 required')
        self.root = Path(root)
        if not self.root.is_absolute():
            raise ValueError('Absolute new evidence path required')
        self.parents = ancestors(self.root)
        self.root.mkdir()  # existing or partial attempt is never reused
        self.identity = plain(self.root, True)
        self.registration_sha256 = registration_sha256
        self.handles = {}
        self.finished = False
        self.cleanup_errors = []
        try:
            # Both handles remain open, so pathname replacement is detected.
            for name in ('started', 'terminal'):
                path = self.root / (name + '.slot')
                handle = path.open('x+b', buffering=0)
                self.handles[name] = (path, handle, plain(path))
                # Actual bounded allocation, not a sparse/truncate reservation.
                if handle.write(b'\0' * SLOT_BYTES) != SLOT_BYTES:
                    raise OSError('Short evidence reservation')
                handle.flush()
                os.fsync(handle.fileno())
            self.write('started', dict(schema=SCHEMA, status='STARTED',
                registration_sha256=registration_sha256,
                closure_observed=False, publication_accepted=False,
                live_attachment=False, retry_permitted=False))
        except BaseException:
            self.close()
            raise

    def write(self, name, value):
        raw = encode(value)
        packet = len(raw).to_bytes(8, 'little') + hashlib.sha256(raw).digest() + raw
        if len(packet) > SLOT_BYTES:
            raise ValueError('Full receipt exceeds reserved slot; no truncation')
        recheck(self.parents)
        if plain(self.root, True) != self.identity:
            raise ValueError('Evidence directory changed')
        path, handle, identity = self.handles[name]
        opened = os.fstat(handle.fileno())
        if plain(path) != identity or (opened.st_dev, opened.st_ino) != identity:
            raise ValueError('Evidence file identity changed')
        handle.seek(0)
        if handle.write(packet) != len(packet):
            raise OSError('Short receipt write')
        handle.flush()
        os.fsync(handle.fileno())
        handle.seek(0)
        if handle.read(len(packet)) != packet:
            raise OSError('Receipt readback mismatch')
        recheck(self.parents)
        opened = os.fstat(handle.fileno())
        if (plain(self.root, True) != self.identity or plain(path) != identity
                or (opened.st_dev, opened.st_ino) != identity or opened.st_size != SLOT_BYTES
                or path.stat().st_size != SLOT_BYTES):
            raise ValueError('Evidence identity/size changed after retention')

    def run(self, spec, expected, admission_check):
        """Trusted original-owner API only; admission callback creates no grant.

        Must validate actual live original-owner identity, lock, expiry, exact
        source/native/reviewer pins and all admission gates immediately here.
        Synthetic callbacks are only valid in synthetic tests, never admission.
        """
        if self.finished or expected != self.registration_sha256 or spec.get('sha256') != expected:
            raise ValueError('One attempt for one exact registration only')
        self.finished = True  # failures and partial receipts cannot be retried
        try:
            if admission_check(spec, expected) is not True:
                raise ValueError('External original-owner admission refused')
            from experiments.digital_pilot74_guardian_v1 import launch_guardian
            result = launch_guardian(spec, expected)
        except BaseException as first:
            try:
                self.write('terminal', dict(schema=SCHEMA, status='FAILED',
                    registration_sha256=expected, first_exception=safe_error(first),
                    diagnostic=diagnostic(first),
                    guardian=getattr(first, 'guardian_failure_evidence', None),
                    closure_observed=False, publication_accepted=False,
                    live_attachment=False, retry_permitted=False))
            except BaseException as retention:
                try:
                    first.add_note('Durable terminal receipt unavailable; STARTED remains UNKNOWN: ' + safe_error(retention))
                except BaseException:
                    pass
            raise
        else:
            # A failed success-receipt write is not retried or overwritten.
            # STARTED plus the partial terminal remains explicit UNKNOWN.
            self.write('terminal', dict(schema=SCHEMA, status='RETURNED',
                registration_sha256=expected, guardian=result,
                publication_accepted=False, live_attachment=False,
                retry_permitted=False))
            return result
        finally:
            self.close()
            if self.cleanup_errors:
                active = sys.exception()
                detail = 'External evidence handle cleanup UNKNOWN: ' + repr(self.cleanup_errors)
                if active is None:
                    raise OSError(detail)
                try:
                    active.add_note(detail)
                except BaseException:
                    pass

    def close(self):
        for unused_path, handle, unused_identity in self.handles.values():
            try:
                handle.close()
            except BaseException as error:
                self.cleanup_errors.append(safe_error(error))


def read_slot(path):
    """Read-only diagnostic; a missing/partial slot is never accepted as closed."""
    path = Path(path)
    parents = ancestors(path)
    identity = plain(path)
    with path.open('rb') as handle:
        info = os.fstat(handle.fileno())
        if (info.st_dev, info.st_ino) != identity or info.st_size != SLOT_BYTES:
            raise ValueError('Receipt slot identity/size mismatch')
        header = handle.read(40)
        size = int.from_bytes(header[:8], 'little')
        if len(header) != 40 or not 0 < size <= SLOT_BYTES - 40:
            raise ValueError('No complete receipt')
        raw = handle.read(size)
        opened = os.fstat(handle.fileno())
        recheck(parents)
        if (plain(path) != identity or (opened.st_dev, opened.st_ino) != identity
                or opened.st_size != SLOT_BYTES or path.stat().st_size != SLOT_BYTES):
            raise ValueError('Receipt identity/size changed during read')
    if len(raw) != size or hashlib.sha256(raw).digest() != header[8:]:
        raise ValueError('Receipt checksum mismatch')
    value = json.loads(raw)
    if encode(value) != raw:
        raise ValueError('Noncanonical receipt')
    return value
