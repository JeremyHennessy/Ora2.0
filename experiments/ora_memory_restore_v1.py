"""Explicit snapshot restore with external cursor reconciliation; never automatic.

Only idle complete snapshots at the operator's known producer high-water mark.
Corrupt primary is retained. Healthy primary and active owners are never replaced.
"""
import argparse
from contextlib import closing,ExitStack
import hashlib
import json
import msvcrt
import os
from pathlib import Path
import re
import sqlite3
import time

CAP=4*1024**2


def plain(path):
    if path.is_symlink() or getattr(path.lstat(),'st_file_attributes',0)&0x400 or path.stat().st_nlink!=1:
        raise ValueError('Plain unshared snapshot/target files required')


def inspect(path):
    with closing(sqlite3.connect(path.resolve().as_uri()+'?mode=ro',uri=True,timeout=.2)) as db:
        deadline=time.monotonic()+2
        db.set_progress_handler(lambda: int(time.monotonic()>deadline),1000)
        if db.execute('PRAGMA integrity_check').fetchone()!=('ok',): raise ValueError('Snapshot integrity failed')
        return (db.execute('SELECT submitted FROM meta').fetchone()[0],
                db.execute("SELECT count(*) FROM tasks WHERE state!='done'").fetchone()[0])


def restore(directory,snapshot,expected_sha256,expected_cursor):
    if type(expected_cursor) is not int or not 0<=expected_cursor<2**63:
        raise ValueError('Explicit known external submission cursor required')
    if type(expected_sha256) is not str or not re.fullmatch('[a-f0-9]{64}',expected_sha256):
        raise ValueError('Exact reviewed snapshot digest required')
    root=Path(directory).resolve(); source=Path(snapshot).resolve(); primary=root/'memory.sqlite3'
    if source==primary: raise ValueError('Snapshot must be separate from primary')
    plain(source)
    with source.open('rb') as stream: raw=stream.read(CAP+1)
    if len(raw)>CAP or hashlib.sha256(raw).hexdigest()!=expected_sha256:
        raise ValueError('Snapshot digest/cap mismatch')
    with ExitStack() as stack:
        for name in ('supervisor.lock','owner.lock','mailbox.lock'):
            path=root/name
            if path.exists(): plain(path)
            handle=stack.enter_context(path.open('a+b')); handle.seek(0)
            msvcrt.locking(handle.fileno(),msvcrt.LK_NBLCK,1)
        for base in (source,primary):
            for suffix in ('-journal','-wal','-shm'):
                if Path(str(base)+suffix).exists():
                    raise ValueError('SQLite sidecar present; preserve and reconcile the whole interrupted transaction first')
        cursor,pending=inspect(source)
        if cursor!=expected_cursor or pending:
            raise ValueError('Snapshot is not a complete checkpoint at the known producer cursor')
        inbox=root/'inbox.json'
        if inbox.exists():
            plain(inbox)
            with inbox.open('rb') as stream: data=stream.read(65537)
            if len(data)>65536: raise ValueError('Oversized producer mailbox')
            value=json.loads(data)
            if type(value) is not list or any(type(x) is not dict or type(x.get('sequence')) is not int for x in value):
                raise ValueError('Cannot reconcile producer mailbox')
            if any(x['sequence']>expected_cursor for x in value):
                raise ValueError('Producer mailbox is newer than snapshot')
        if primary.exists():
            plain(primary)
            if primary.stat().st_size>CAP: raise ValueError('Oversized corrupt primary requires explicit separate preservation')
            try: inspect(primary)
            except (sqlite3.DatabaseError,ValueError): pass
            else: raise ValueError('Healthy primary must not be rolled back')
        temporary=root/'memory.restore.next'
        if temporary.exists():
            plain(temporary)
            if temporary.read_bytes()!=raw: raise ValueError('Different interrupted restoration requires review')
        else:
            with temporary.open('xb') as stream:
                stream.write(raw); stream.flush(); os.fsync(stream.fileno())
        if inspect(temporary)!=(expected_cursor,0): raise ValueError('Restoration copy failed verification')
        preserved=root/'memory.corrupt.sqlite3'
        if primary.exists():
            if preserved.exists(): raise ValueError('Prior corrupt primary already retained; archive it explicitly')
            os.replace(primary,preserved)
        os.replace(temporary,primary)
        return dict(schema='ORA-EXPLICIT-MEMORY-RESTORE-v1',cursor=expected_cursor,sha256=expected_sha256,
                    previous_primary_retained=preserved.exists(),automatic=False)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('directory',type=Path); parser.add_argument('snapshot',type=Path)
    parser.add_argument('sha256'); parser.add_argument('known_producer_cursor',type=int)
    args=parser.parse_args()
    print(json.dumps(restore(args.directory,args.snapshot,args.sha256,args.known_producer_cursor)))
