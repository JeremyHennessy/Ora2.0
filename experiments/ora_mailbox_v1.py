"""Single-slot producer arbitration for operator and automatic task sources."""
from contextlib import closing
import json
import msvcrt
import os
from pathlib import Path
import sqlite3


class Busy(RuntimeError): pass


def publish(directory, build):
    root=Path(directory)
    lock=root/'mailbox.lock'
    if lock.exists() and (lock.is_symlink() or lock.stat().st_nlink!=1):
        raise ValueError('Mailbox lock must be a plain local file')
    with lock.open('a+b') as owner:
        owner.seek(0)
        try: msvcrt.locking(owner.fileno(),msvcrt.LK_NBLCK,1)
        except OSError as error: raise Busy('Another producer owns mailbox') from error
        if not (root/'memory.sqlite3').exists(): raise Busy('Service not ready')
        with closing(sqlite3.connect(root/'memory.sqlite3',timeout=.1)) as db:
            row=db.execute('SELECT submitted FROM meta').fetchone()
            if row is None: raise Busy('Service cursor not initialized')
            last=row[0]
        inbox=root/'inbox.json'
        if inbox.exists():
            with inbox.open('rb') as stream: previous=stream.read(65537)
            if len(previous)>65536: raise ValueError('Oversized existing mailbox; operator repair required')
            old=json.loads(previous)
            if type(old) is not list or not old or any(type(x) is not dict or type(x.get('sequence')) is not int for x in old):
                raise ValueError('Invalid existing mailbox; operator repair required')
            if max(x['sequence'] for x in old)>last:
                raise Busy('Unconsumed task cannot be overwritten')
        sequence=last+1
        task=build(sequence)
        if type(task) is not dict or set(task)!={'sequence','kind','key','value'} or task['sequence']!=sequence:
            raise ValueError('Producer must use next sequence')
        raw=json.dumps([task],ensure_ascii=True,allow_nan=False).encode('ascii')
        if len(raw)>65536: raise ValueError('Task exceeds mailbox cap')
        temporary=root/'mailbox.next'
        # Fixed temporary is owned under this producer lock; never scan/delete queues.
        if temporary.exists():
            if temporary.is_symlink() or temporary.stat().st_nlink!=1: raise ValueError('Invalid mailbox temporary')
            temporary.unlink()
        with temporary.open('xb') as stream:
            stream.write(raw); stream.flush(); os.fsync(stream.fileno())
        os.replace(temporary,inbox)
        return sequence
